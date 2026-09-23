"""Real Git regressions for worktree ownership, awareness, recovery and primary delivery."""

import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from concorde.harness import change_worktree, worktree_delivery
from concorde.operations.dispatch import run_operation
from concorde.harness.change_worktree import (
    GUIDANCE_START,
    git,
    git_value,
    read_change,
)
from tests.concorde.support.environment import child_environment
from concorde.harness.host import OperationHost
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    project,
)


class WorktreeLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.primary = self.directory / "primary"
        self.primary.mkdir()
        project(self.primary)
        (self.primary / "AGENTS.md").write_text(
            "# Existing project policy\nKeep project conventions.\n"
        )
        (self.primary / "shared.txt").write_text("base\n")
        git(self.primary, "init", "-q", "-b", "integration")
        git(self.primary, "config", "user.name", "Concorde Test")
        git(self.primary, "config", "user.email", "concorde-test@example.invalid")
        self.commit(self.primary, "Fixture")
        self.change = self.directory / "change"
        git(self.primary, "worktree", "add", "-b", "candidate", str(self.change))
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the transfer contract",
        }

    def state_file(self):
        return next(
            (self.primary / ".concorde/status").glob("change.*.json"),
            self.primary / ".concorde/status/missing.json",
        )

    def commit(self, root, message):
        git(root, "add", "-A")
        git(root, "commit", "-qm", message)
        return git_value(root, "rev-parse", "HEAD")

    def call_operation(self, root, name, data, *, host=None, mode="execute"):
        host = host or OperationHost(root, PACKAGE, mode=mode)
        return run_operation(
            name, CONFIGURATION, typed(name + "-request", data), host_context=host
        )

    def ready_delivery(self):
        """A directly validated candidate for tests focused on Git delivery transactions."""
        (self.change / "app/transfer.py").write_text(
            "def transfer(balance, amount):\n"
            '    if amount <= 0 or amount > balance: raise ValueError("invalid transfer")\n'
            "    return balance - amount\n"
        )
        result = self.call_operation(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        return read_change(self.change, required=True)["change_id"]

    @verifies("scenario.worktrees.guidance-appended")
    def test_new_guidance_preserves_existing_client_content_bytes_and_modes(self):
        agents = self.change / "AGENTS.md"
        agents.write_bytes(b"# User policy\r\nKeep these bytes.\r\n")
        agents.chmod(0o751)
        claude = self.change / "CLAUDE.md"
        # Even a guidance-looking block outside the saved ownership map is user content.
        original = (
            b"# User-owned client file\r\n"
            + (GUIDANCE_START + "User text\n" + change_worktree.GUIDANCE_END).encode()
        )
        claude.write_bytes(original)
        claude.chmod(0o740)
        before = agents.read_bytes()
        state = change_worktree.ensure_change(self.change, task=self.task)
        self.assertEqual({"AGENTS.md": {"created": False}}, state["guidance"])
        self.assertEqual(
            before,
            change_worktree.strip_guidance(agents.read_bytes().decode()).encode(),
        )
        self.assertEqual(0o751, agents.stat().st_mode & 0o777)
        self.assertEqual(original, claude.read_bytes())
        self.assertEqual(0o740, claude.stat().st_mode & 0o777)
        tree = change_worktree.snapshot_tree(self.change)
        self.assertEqual(original, self.tree_bytes(tree, "CLAUDE.md"))
        self.assertEqual(before, self.tree_bytes(tree, "AGENTS.md"))
        self.assertTrue(
            git_value(self.change, "ls-tree", tree, "AGENTS.md").startswith("100755 ")
        )

    def tree_bytes(self, tree, path):
        return subprocess.run(
            ["git", "-C", str(self.change), "show", f"{tree}:{path}"],
            capture_output=True,
            check=True,
        ).stdout

    @verifies("scenario.worktrees.guidance-appended")
    def test_new_guidance_creates_only_agents_and_excludes_its_empty_shell(self):
        (self.change / "AGENTS.md").unlink()
        state = change_worktree.ensure_change(self.change, task=self.task)
        self.assertEqual({"AGENTS.md": {"created": True}}, state["guidance"])
        self.assertTrue((self.change / "AGENTS.md").exists())
        self.assertFalse((self.change / "CLAUDE.md").exists())
        tree = change_worktree.snapshot_tree(self.change)
        self.assertEqual(
            "", git_value(self.change, "ls-tree", tree, "AGENTS.md", "CLAUDE.md")
        )

    @verifies("scenario.worktrees.guidance-appended")
    def test_ambiguous_guidance_blocks_snapshot_without_mutation(self):
        change_worktree.ensure_change(self.change, task=self.task)
        agents = self.change / "AGENTS.md"
        block = (
            GUIDANCE_START + "Owned guidance\n" + change_worktree.GUIDANCE_END
        ).encode()
        agents.write_bytes(block + block)
        saved = self.state_file().read_bytes()
        index = git_value(self.change, "write-tree")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            change_worktree.snapshot_tree(self.change)
        self.assertEqual(block + block, agents.read_bytes())
        self.assertEqual(saved, self.state_file().read_bytes())
        self.assertEqual(index, git_value(self.change, "write-tree"))

    @verifies("scenario.worktrees.guidance-appended")
    def test_guidance_and_initial_state_rollback_together(self):
        agents = self.change / "AGENTS.md"
        agents.write_bytes(b"# Existing policy\r\nKeep original newlines.\r\n")
        agents.chmod(0o751)
        before = agents.read_bytes()
        with patch.object(
            change_worktree,
            "write_status",
            side_effect=OSError("fixture state transaction failure"),
        ):
            result = self.call_operation(
                self.change,
                "concorde-context-solve",
                {"target_id": "scope.bank", "task": "Explain transfer"},
            )
        self.assertNotEqual("succeeded", result["status"], result)
        self.assertEqual(before, agents.read_bytes())
        self.assertEqual(0o751, agents.stat().st_mode & 0o777)
        self.assertFalse((self.change / "CLAUDE.md").exists())
        self.assertFalse(self.state_file().exists())

    def relay_in_process(self):
        """A trusted relay running the candidate in this process."""
        self.relayed = []

        def relay(host, operation, invocation, candidate):
            inner = OperationHost(candidate, PACKAGE, mode=invocation["mode"])
            result = run_operation(
                operation, CONFIGURATION, invocation["input"], host_context=inner
            )
            self.relayed.append(
                {
                    "operation": operation,
                    "invocation": invocation,
                    "candidate": candidate,
                    "result": result,
                }
            )
            return result, ""

        return relay

    def primary_host(self, relay):
        return OperationHost(self.primary, PACKAGE, relay=relay)

    def remove_candidate(self, created):
        git(self.primary, "worktree", "remove", "--force", str(created))
        created.parent.rmdir()

    @verifies("scenario.admission.relay")
    def test_primary_mutation_with_an_unknown_change_id_is_refused(self):
        result = self.call_operation(
            self.primary,
            "concorde-plan",
            {**self.task, "change_id": "change.unknown"},
            host=self.primary_host(self.relay_in_process()),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("missing_change", result["errors"][0]["code"], result)
        self.assertEqual([], self.relayed)

    @verifies("scenario.validation.without-change")
    def test_validation_from_the_primary_needs_an_existing_change(self):
        worktrees = git_value(self.primary, "worktree", "list", "--porcelain")
        for request in (self.task, {**self.task, "change_id": "change.unknown"}):
            for mode in ("execute", "describe-policy"):
                with self.subTest(request=request, mode=mode):
                    result = self.call_operation(
                        self.primary,
                        "concorde-validate",
                        request,
                        host=OperationHost(
                            self.primary,
                            PACKAGE,
                            mode=mode,
                            relay=self.relay_in_process(),
                        ),
                    )
                    self.assertEqual("blocked", result["status"], result)
                    self.assertEqual(
                        "missing_change", result["errors"][0]["code"], result
                    )
                    self.assertEqual([], self.relayed)
        self.assertFalse((self.primary / ".concorde/status").exists())
        self.assertEqual(
            worktrees, git_value(self.primary, "worktree", "list", "--porcelain")
        )

    def configure_request(self, **extra):
        selection = typed(
            "concorde-operation-configuration",
            {"model": "openai-codex/gpt-6-astra", "thinking": "high"},
        )
        return selection, {"configuration": selection, **extra}

    def stored_configuration(self, root):
        value = json.loads((root / ".concorde/config.json").read_text())
        return value["operation_configuration"]

    @verifies("scenario.admission.primary-opt-in")
    def test_configure_applies_in_primary_only_on_explicit_opt_in(self):
        selection, request = self.configure_request(run_in_primary=True)
        result = self.call_operation(
            self.primary,
            "concorde-configure",
            request,
            host=self.primary_host(self.relay_in_process()),
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertIsNone(result["workspace"], result)
        self.assertEqual([], self.relayed)
        self.assertEqual(selection, self.stored_configuration(self.primary))
        self.assertFalse((self.primary / ".concorde/status").exists())
        self.assertEqual(
            [str(self.change.resolve())],
            [
                item["path"]
                for item in change_worktree.refresh_registry(
                    self.primary, persist=False
                )["worktrees"]
            ],
        )

    @verifies(
        "scenario.admission.primary-opt-in",
        "scenario.admission.relay",
        "scenario.admission.run-record",
    )
    def test_configure_without_opt_in_is_relayed_into_a_candidate(self):
        selection, request = self.configure_request()
        result = self.call_operation(
            self.primary,
            "concorde-configure",
            request,
            host=self.primary_host(self.relay_in_process()),
        )
        [relayed] = self.relayed
        created = relayed["candidate"]
        self.addCleanup(self.remove_candidate, created)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(str(created), result["workspace"]["path"], result)
        self.assertEqual(selection, self.stored_configuration(created))
        self.assertEqual(CONFIGURATION, self.stored_configuration(self.primary))
        # The envelope is the candidate's own; the relaying run record links to its run.
        self.assertEqual(relayed["result"], result)
        records = {
            path.parent.name: json.loads(path.read_text())
            for path in (self.primary / ".concorde/runs").glob("*/run.json")
        }
        self.assertEqual(result, records[result["invocation_id"]]["result"])
        [relaying] = [
            record
            for record in records.values()
            if record["relayed_run_id"] == result["invocation_id"]
        ]
        self.assertEqual(3, relaying["schema_version"])
        self.assertNotEqual(result["invocation_id"], relaying["run_id"])
        self.assertEqual(result, relaying["result"])

    @verifies("scenario.admission.primary-opt-in")
    def test_primary_opt_in_is_refused_elsewhere_and_by_other_capabilities(self):
        _, request = self.configure_request(run_in_primary=True)
        result = self.call_operation(self.change, "concorde-configure", request)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("workspace_mismatch", result["errors"][0]["code"], result)
        self.assertEqual(CONFIGURATION, self.stored_configuration(self.change))
        result = run_operation(
            "concorde-plan",
            CONFIGURATION,
            {
                "type_id": "concorde-plan-request",
                "schema_version": 1,
                "data": {**self.task, "run_in_primary": True},
            },
            host_context=self.primary_host(self.relay_in_process()),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(
            ("invalid_field", "/data/run_in_primary"),
            (result["errors"][0]["code"], result["errors"][0]["field"]),
        )
        self.assertEqual([], self.relayed)
        self.assertFalse((self.primary / ".concorde/status").exists())

    @verifies("scenario.worktrees.owner-conflict")
    def test_owner_binding_missing_fields_returns_structured_error(self):
        from concorde.spec.repository import SpecError

        change_worktree.ensure_change(self.change, task=self.task)
        for field in ("target_id", "task"):
            task = dict(self.task)
            del task[field]
            with self.subTest(field=field), self.assertRaises(SpecError) as caught:
                change_worktree.bind_owner(self.change, task)
            self.assertEqual("invalid_input", caught.exception.code)
            self.assertEqual(field, caught.exception.field)
        self.assertIsNone(read_change(self.change, required=True)["target_id"])

    @verifies("scenario.admission.relay")
    def test_primary_relay_is_one_json_response_on_the_paired_cli(self):
        """The default relay runs the candidate's launcher in a subprocess; configure needs no agent."""
        operation = "concorde-configure"
        selection, request = self.configure_request()
        invocation = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": operation,
            "mode": "execute",
            "configuration": CONFIGURATION,
            "input": typed(operation + "-request", request),
        }
        process = subprocess.run(
            [sys.executable, str(PACKAGE / "scripts/run-operation.py"), operation],
            cwd=self.primary,
            input=json.dumps(invocation),
            text=True,
            capture_output=True,
            env=child_environment(),
        )
        result = json.loads(process.stdout)
        self.assertIsNotNone(result["workspace"], result)
        created = Path(result["workspace"]["path"])
        self.addCleanup(self.remove_candidate, created)
        self.assertNotEqual(self.primary, created)
        self.assertTrue(created.is_dir(), created)
        self.assertEqual(str(self.primary), result["workspace"]["primary_worktree"])
        state = read_change(created, required=True)
        self.assertEqual(state["change_id"], result["workspace"]["change_id"])
        # The declared default task is the change's recorded task.
        self.assertEqual("Configure the project's operation settings", state["task"])
        self.assertIn(result["status"], {"succeeded", "blocked", "failed"}, result)
        self.assertEqual(
            0 if result["status"] == "succeeded" else 3,
            process.returncode,
            process.stderr,
        )
        # Whatever the candidate's launcher wrote to stderr is forwarded as it was: JSON lines.
        for line in process.stderr.splitlines():
            if line.strip():
                json.loads(line)

    def declare_pending_files(self):
        """Declare two files the plan intends to create, before any of them exists."""
        path = self.change / "specs/transfer/module.md.json"
        metadata = json.loads(path.read_text())
        realizations = [
            item for item in metadata["defines"] if item["type"] == "realization"
        ]
        realizations[0].update(
            entries=["app/rounding.py", "app/transfer.py"], pending=["app/rounding.py"]
        )
        realizations[1].update(
            entries=["checks/rounding_check.py", "checks/transfer_check.py"],
            pending=["checks/rounding_check.py"],
        )
        path.write_text(json.dumps(metadata, indent=2) + "\n")

    @verifies(
        "scenario.validation.pending-confirmed",
        "scenario.delivery.pending-confirmed",
    )
    def test_created_pending_files_are_confirmed_and_the_rest_stay_pending(self):
        self.declare_pending_files()
        (self.change / "app/rounding.py").write_text(
            "def round_half_up(value):\n    return value\n"
        )
        # A pending entry whose file exists fails CHK.binds.pending-subset, so the host confirms
        # it in the candidate before validating; delivery then has nothing left to confirm.
        change_id = self.ready_delivery()
        realizations = [
            item
            for item in json.loads(
                (self.change / "specs/transfer/module.md.json").read_text()
            )["defines"]
            if item["type"] == "realization"
        ]
        self.assertEqual([], realizations[0]["pending"])
        self.assertEqual(["checks/rounding_check.py"], realizations[1]["pending"])
        result = self.call_operation(
            self.change,
            "concorde-deliver",
            {"change_id": change_id, "keep_worktree": True},
        )
        self.assertEqual("succeeded", result["status"], result)
        answer = result["output"]["data"]["answer"]
        self.assertIn("checks/rounding_check.py", answer)
        receipt = json.loads(
            (self.primary / f".concorde/status/{change_id}.json").read_text()
        )["delivery"]
        self.assertEqual([], receipt["confirmed_files"])
        self.assertEqual(["checks/rounding_check.py"], receipt["still_pending"])
        self.assertEqual(
            "success", validate_repository(self.change, package_root=PACKAGE).status
        )

    def test_delivery_refuses_a_declared_file_that_was_never_created_or_marked(self):
        self.declare_pending_files()
        path = self.change / "specs/transfer/module.md.json"
        metadata = json.loads(path.read_text())
        next(item for item in metadata["defines"] if item["type"] == "realization").pop(
            "pending"
        )
        path.write_text(json.dumps(metadata, indent=2) + "\n")
        report = validate_repository(self.change, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        self.assertIn(
            "CHK.binds.exists", {finding.rule_id for finding in report.findings}
        )

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-primary",
    )
    def test_primary_merge_requires_separate_delivery_and_primary_session(self):
        change_id = self.ready_delivery()
        request = {"change_id": change_id, "merge_primary": True}
        result = self.call_operation(self.change, "concorde-deliver", request)
        self.assertEqual(
            "primary_session_required", result["errors"][0]["code"], result
        )
        result = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("delivery_required", result["errors"][0]["code"], result)
        staged = self.call_operation(
            self.change,
            "concorde-deliver",
            {"change_id": change_id, "keep_worktree": True},
        )
        self.assertEqual("succeeded", staged["status"], staged)
        result = self.call_operation(self.change, "concorde-deliver", request)
        self.assertEqual(
            "primary_session_required", result["errors"][0]["code"], result
        )
        redirected = OperationHost(self.primary, PACKAGE, session_root=self.change)
        result = self.call_operation(
            self.primary, "concorde-deliver", request, host=redirected
        )
        self.assertEqual(
            "primary_session_required", result["errors"][0]["code"], result
        )
        merged = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", merged["status"], merged)
        head = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(
            worktree_delivery,
            "_verify_merged_tree",
            side_effect=AssertionError("duplicate merge checks"),
        ):
            again = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(head, git_value(self.primary, "rev-parse", "HEAD"))

    @verifies("scenario.delivery.branch", "scenario.delivery.retry")
    def test_explicit_retention_survives_interrupted_initial_cleanup(self):
        change_id = self.ready_delivery()
        before = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(
            worktree_delivery, "_cleanup", side_effect=OSError("interrupted cleanup")
        ):
            result = self.call_operation(
                self.change,
                "concorde-deliver",
                {"change_id": change_id, "keep_worktree": True},
            )
        self.assertEqual("failed", result["status"], result)
        again = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        self.assertIn("retained", again["output"]["data"]["answer"])
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    @verifies("scenario.delivery.branch", "scenario.delivery.retry")
    def test_cleanup_retry_persists_a_changed_retention_choice_before_cleanup(self):
        change_id = self.ready_delivery()
        with patch.object(
            worktree_delivery, "_cleanup", side_effect=OSError("interrupted cleanup")
        ):
            result = self.call_operation(
                self.change, "concorde-deliver", {"change_id": change_id}
            )
            self.assertEqual("failed", result["status"], result)
            result = self.call_operation(
                self.primary,
                "concorde-deliver",
                {"change_id": change_id, "keep_worktree": True},
            )
        self.assertEqual("failed", result["status"], result)
        again = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        removed = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "keep_worktree": False},
        )
        self.assertEqual("succeeded", removed["status"], removed)
        self.assertFalse(self.change.exists())

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-primary",
    )
    def test_independent_deliveries_do_not_update_each_other_or_primary(self):
        before = git_value(self.primary, "rev-parse", "HEAD")
        first_id = self.ready_delivery()
        first = self.call_operation(
            self.change, "concorde-deliver", {"change_id": first_id}
        )
        self.assertEqual("succeeded", first["status"], first)
        first_branch = "concorde/delivered/" + first_id
        first_head = git_value(self.primary, "rev-parse", first_branch)
        self.change = self.directory / "second-change"
        git(self.primary, "worktree", "add", "-b", "second-candidate", str(self.change))
        second_id = self.ready_delivery()
        second = self.call_operation(
            self.change, "concorde-deliver", {"change_id": second_id}
        )
        self.assertEqual("succeeded", second["status"], second)
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(first_head, git_value(self.primary, "rev-parse", first_branch))
        self.assertTrue(
            git_value(self.primary, "rev-parse", "concorde/delivered/" + second_id)
        )
        start = threading.Barrier(2)
        checking = threading.Lock()
        verify = worktree_delivery._verify_merged_tree

        def checked(*args, **kwargs):
            self.assertTrue(
                checking.acquire(blocking=False), "overlapping primary merge checks"
            )
            try:
                return verify(*args, **kwargs)
            finally:
                checking.release()

        def promote(change_id):
            start.wait(timeout=10)
            return run_operation(
                "concorde-deliver",
                CONFIGURATION,
                typed(
                    "concorde-deliver-request",
                    {"change_id": change_id, "merge_primary": True},
                ),
                host_context=OperationHost(self.primary, PACKAGE),
            )

        with (
            patch.object(worktree_delivery, "_verify_merged_tree", side_effect=checked),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            results = list(pool.map(promote, (first_id, second_id)))
        for merged in results:
            self.assertEqual("succeeded", merged["status"], merged)
        for change_id in (first_id, second_id):
            branch = "concorde/delivered/" + change_id
            self.assertEqual(
                0,
                git(
                    self.primary,
                    "merge-base",
                    "--is-ancestor",
                    branch,
                    "HEAD",
                    check=False,
                ).returncode,
            )

    @verifies("scenario.delivery.branch", "scenario.delivery.conflict")
    def test_primary_merge_checks_latest_integration_and_preserves_delivery_on_failure(
        self,
    ):
        change_id = self.ready_delivery()
        staged = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", staged["status"], staged)
        path = self.primary / "checks/transfer_check.py"
        path.write_text(path.read_text() + "\nassert transfer(100, 20) == 40\n")
        advanced = self.commit(self.primary, "Changed acceptance after delivery")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("failed_merge_checks", result["errors"][0]["code"], result)
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue(
            git_value(self.primary, "rev-parse", "concorde/delivered/" + change_id)
        )

    @verifies("scenario.delivery.branch", "scenario.delivery.conflict")
    def test_final_merge_conflict_preserves_primary_and_delivered_branch(self):
        (self.change / "shared.txt").write_text("candidate\n")
        change_id = self.ready_delivery()
        staged = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", staged["status"], staged)
        (self.primary / "shared.txt").write_text("primary\n")
        before = self.commit(self.primary, "Conflicting change after delivery")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("merge_conflict", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(
            "candidate",
            git_value(
                self.primary, "show", "concorde/delivered/" + change_id + ":shared.txt"
            ),
        )
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))

    def test_delivery_does_not_overwrite_an_existing_branch(self):
        change_id = self.ready_delivery()
        branch = "concorde/delivered/" + change_id
        git(self.primary, "branch", branch)
        before = git_value(self.primary, "rev-parse", branch)
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("stale_delivery", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", branch))
        self.assertTrue(self.change.exists())

    @verifies("scenario.admission.describe-policy")
    def test_primary_merge_preview_after_source_removal_is_read_only(self):
        change_id = self.ready_delivery()
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", result["status"], result)
        path = self.primary / result["output"]["data"]["artifacts"][0]["path"]
        receipt = path.read_bytes()
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
            mode="describe-policy",
        )
        self.assertEqual("described", result["status"], result)
        self.assertEqual(receipt, path.read_bytes())
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    def test_changed_delivery_ref_blocks_final_merge(self):
        change_id = self.ready_delivery()
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", result["status"], result)
        branch = "concorde/delivered/" + change_id
        git(self.primary, "update-ref", "refs/heads/" + branch, "HEAD")
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("stale_delivery", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-primary",
        "scenario.delivery.retry",
    )
    def test_primary_merge_recovers_receipt_after_update_without_merging_again(self):
        change_id = self.ready_delivery()
        staged = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", staged["status"], staged)
        write = worktree_delivery._write_json

        def interrupted(root, relative, receipt):
            if (receipt.get("primary_merge") or {}).get("status") == "merged":
                raise OSError("interrupted after primary ref update")
            return write(root, relative, receipt)

        request = {"change_id": change_id, "merge_primary": True}
        with patch.object(worktree_delivery, "_write_json", side_effect=interrupted):
            result = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("failed", result["status"], result)
        merged = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(
            worktree_delivery,
            "_verify_merged_tree",
            side_effect=AssertionError("duplicate checks"),
        ):
            again = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(merged, git_value(self.primary, "rev-parse", "HEAD"))
        receipt = json.loads(
            (self.primary / again["output"]["data"]["artifacts"][0]["path"]).read_text()
        )["delivery"]
        self.assertEqual("merged", receipt["primary_merge"]["status"])
        self.assertTrue(
            list((self.primary / ".concorde/runs").glob("*/delivery/staging"))
        )
        self.assertTrue(
            list((self.primary / ".concorde/runs").glob("*/delivery/primary"))
        )
        self.assertFalse((self.primary / ".concorde/deliveries").exists())

    @verifies(
        "scenario.validation.ready",
        "scenario.delivery.branch",
        "scenario.concorde.validate-record",
    )
    def test_directly_authored_candidate_can_be_validated_and_delivered_without_a_plan(
        self,
    ):
        path = self.change / "app/transfer.py"
        path.write_text(
            'def transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n'
        )
        spec = self.change / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nClarified directly in the candidate.\n")
        result = self.call_operation(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.change, required=True)
        self.assertEqual({}, state["targets"])
        self.assertTrue(state["validation"]["checks"])
        result = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": state["change_id"]}
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertIn(
            "Clarified directly",
            git_value(
                self.primary,
                "show",
                "concorde/delivered/"
                + state["change_id"]
                + ":specs/transfer/module.md",
            ),
        )
        self.assertFalse(self.change.exists())

    def test_self_hosted_integration_builds_its_exact_checkout_before_validation(self):
        from concorde.distribution.build import verify_fresh

        fixture_report = validate_repository(self.primary, package_root=PACKAGE)
        self.assertEqual(fixture_report.status, "success")
        for directory in (
            "prompts",
            "agents",
            "operations",
            "protocol",
            "scripts",
            "src",
            "pi",
        ):
            shutil.copytree(
                PACKAGE / directory,
                self.primary / directory,
                ignore=shutil.ignore_patterns("__pycache__", "node_modules"),
            )
        (self.primary / "concorde.json").write_text("{}")
        (self.primary / "app/transfer.py").write_text(
            "def transfer(balance, amount):\n"
            '    if amount <= 0 or amount > balance: raise ValueError("invalid transfer")\n'
            "    return balance - amount\n"
        )
        with (self.primary / ".gitignore").open("a") as stream:
            stream.write("\ngenerated/\n.agents/\n.claude/\n.pi/\n")
        commit = self.commit(self.primary, "Self-hosted integration fixture")
        tree = git_value(self.primary, "rev-parse", "HEAD^{tree}")
        verified = []

        def inspect(root, **kwargs):
            self.assertNotEqual(root, self.primary)
            self.assertEqual(git_value(root, "rev-parse", "HEAD^{tree}"), tree)
            verify_fresh(root)
            self.assertTrue(
                (root / "generated/session/pi/concorde-session.ts").is_file()
            )
            for retired in (
                "skills",
                ".agents/skills",
                ".claude/skills",
                ".pi/extensions/concorde-session.ts",
            ):
                self.assertFalse((root / retired).exists(), retired)
            self.assertEqual(
                (PACKAGE / "prompts/operation-guidance/concorde-plan.md").read_bytes(),
                (root / "prompts/operation-guidance/concorde-plan.md").read_bytes(),
            )
            verified.append(root)
            return fixture_report

        with (
            patch.object(worktree_delivery, "validate_repository", side_effect=inspect),
            patch.object(
                worktree_delivery.subprocess, "run", wraps=subprocess.run
            ) as launched,
        ):
            checks = worktree_delivery._verify_merged_tree(
                OperationHost(self.primary, PACKAGE),
                commit,
                tree,
                "change.integration-build",
            )
        self.assertEqual(len(verified), 1)
        expected = [sys.executable, str(verified[0] / "scripts/concorde.py"), "build"]
        self.assertTrue(
            any(call.args[0] == expected for call in launched.call_args_list)
        )
        self.assertFalse(verified[0].exists())
        self.assertTrue(checks)
        self.assertTrue(all(check["status"] == "passed" for check in checks))
        self.assertFalse((self.primary / "generated").exists())


if __name__ == "__main__":
    unittest.main()
