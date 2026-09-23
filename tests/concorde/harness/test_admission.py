"""Admission of capability requests: relay from the primary, typed refusal, targets and builds."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from concorde.distribution.build import write_build
from concorde.harness import change_worktree
from concorde.harness.change_worktree import (
    ensure_change,
    git,
    git_value,
    read_change,
)
from concorde.harness.host import OperationHost
from concorde.harness.host import OperationHost as RealHost
from concorde.operations.dispatch import run_operation
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE, project
from tests.concorde.support.worktree_project import WorktreeProject

LAUNCHER = REPOSITORY_ROOT / "scripts/run-operation.py"
TARGET = {"target_id": "service.transfer", "task": "Implement the transfer contract"}


def _run(argv, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LAUNCHER), *argv],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
    )


class PrimaryRelayTests(WorktreeProject, unittest.TestCase):
    """Requests started in the primary worktree: relay, opt-in and refusal."""

    @verifies("scenario.admission.relay-missing-change")
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

    @verifies("scenario.admission.primary-opt-in-outside-primary")
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
                try:
                    json.loads(line)
                except ValueError:
                    self.fail(f"stderr line is not JSON: {line!r}")


class SourceRelayTests(unittest.TestCase):
    """Relaying from a primary into a candidate whose tree carries the Concorde sources."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.primary = Path(self.temp.name) / "not-named-primary"
        self.primary.mkdir()
        git(self.primary, "init", "-q", "-b", "trunk")
        git(self.primary, "config", "user.name", "Test")
        git(self.primary, "config", "user.email", "test@example.invalid")
        (self.primary / "file").write_text("base")
        git(self.primary, "add", ".")
        git(self.primary, "commit", "-qm", "base")
        self.candidate = Path(self.temp.name) / "candidate"
        git(self.primary, "worktree", "add", "-b", "task", str(self.candidate))

    @verifies("scenario.admission.source-primary-refused")
    def test_source_primary_cannot_relay_a_mutation_by_change_id(self):
        from concorde.harness.host import OperationHost
        from concorde.harness.relay import bind_worktree

        state = ensure_change(
            self.candidate, task={"task": "maintenance"}, mode="maintenance"
        )
        (self.primary / "concorde.json").write_text("{}")
        with self.assertRaises(SpecError) as error:
            bind_worktree(
                OperationHost(self.primary, self.primary),
                True,
                {"change_id": state["change_id"]},
            )
        self.assertEqual("fresh_session_required", error.exception.code)
        host, workspace = bind_worktree(
            OperationHost(self.candidate, self.candidate),
            True,
            {"change_id": state["change_id"]},
        )
        self.assertEqual(str(self.candidate), workspace["path"])
        self.assertNotIn("relay", workspace)

    @verifies("scenario.admission.relay")
    def test_source_carrying_relay_checks_existing_build_without_rebuilding(self):
        from concorde.harness.host import OperationHost
        from concorde.harness.relay import relay_operation
        from concorde.spec.repository import SpecError

        state = ensure_change(
            self.candidate, task={"task": "maintenance"}, mode="maintenance"
        )
        (self.candidate / "concorde.json").write_text("{}")
        (self.candidate / "src/concorde").mkdir(parents=True)
        relaying = OperationHost(
            self.primary,
            self.primary,
            relay_target={
                "path": str(self.candidate),
                "change_id": state["change_id"],
                "mutates": False,
            },
        )
        # A source candidate is checked like any other: its change status must name the
        # requested change and path before anything is verified or launched. Git keeps running
        # for real; only the candidate's launcher is replaced.
        real_popen = subprocess.Popen
        launched = []

        def launcher(argv, *args, **kwargs):
            if argv[-1] != "concorde-main":
                return real_popen(argv, *args, **kwargs)
            launched.append((argv, kwargs))
            process = MagicMock()
            process.communicate.return_value = (
                '{"type_id":"concorde-operation-result"}',
                "diagnostics",
            )
            return process

        mismatched = OperationHost(
            self.primary,
            self.primary,
            relay_target={
                "path": str(self.candidate),
                "change_id": "change.other",
                "mutates": False,
            },
        )
        with (
            patch("concorde.harness.admission.verify_build") as verify,
            patch("subprocess.Popen", side_effect=launcher),
        ):
            with self.assertRaises(SpecError) as mismatch:
                relay_operation(mismatched, "concorde-main", {}, self.candidate)
            self.assertEqual("workspace_mismatch", mismatch.exception.code)
            verify.assert_not_called()
        with (
            patch(
                "concorde.harness.admission.verify_build",
                side_effect=SpecError("stale", "stale_build"),
            ) as verify,
            patch("subprocess.Popen", side_effect=launcher),
        ):
            with self.assertRaises(SpecError):
                relay_operation(relaying, "concorde-main", {}, self.candidate)
            verify.assert_called_once_with(self.candidate)
        self.assertEqual([], launched)
        (self.candidate / ".venv/bin").mkdir(parents=True)
        (self.candidate / ".venv/bin/python").write_text("fixture interpreter")
        (self.candidate / "scripts").mkdir()
        (self.candidate / "scripts/run-operation.py").write_text("fixture launcher")
        with (
            patch("concorde.harness.admission.verify_build") as verify,
            patch("subprocess.Popen", side_effect=launcher),
        ):
            result, diagnostics = relay_operation(
                relaying, "concorde-main", {}, self.candidate
            )
            verify.assert_called_once_with(self.candidate)
        [(argv, kwargs)] = launched
        self.assertEqual("concorde-main", argv[-1])
        self.assertEqual(str(self.candidate / ".venv/bin/python"), argv[0])
        self.assertNotIn("PYTHONPATH", kwargs["env"])
        self.assertNotIn("PYTHONHOME", kwargs["env"])
        self.assertEqual("diagnostics", diagnostics)


class LauncherAdmissionTests(unittest.TestCase):
    """Requests read by `scripts/run-operation.py` in this checkout."""

    @verifies("scenario.admission.typed-reject")
    def test_invalid_payload_retains_the_admitted_mode_without_execution(self):
        for mode in ("execute", "describe-policy"):
            with self.subTest(mode=mode):
                value = {
                    "type_id": "concorde-operation-invocation",
                    "schema_version": 3,
                    "operation_id": "concorde-context-solve",
                    "mode": mode,
                    "configuration": None,
                    "input": {
                        "type_id": "concorde-context-solve-request",
                        "schema_version": 1,
                        "data": {
                            "target_id": "module.harness",
                            "task": "Assess",
                            "unknown": True,
                        },
                    },
                }
                process = _run(["concorde-context-solve"], json.dumps(value))
                result = json.loads(process.stdout)
                self.assertEqual(3, process.returncode)
                self.assertEqual(mode, result["mode"])
                self.assertEqual("blocked", result["status"])
                self.assertEqual("invalid_field", result["errors"][0]["code"])
                self.assertIsNone(result["output"])
                self.assertIsNone(result["workspace"])

    @verifies("scenario.admission.describe-policy")
    def test_public_review_launcher_previews_scoped_code_authority(self):
        invocation = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-code-review",
            "mode": "describe-policy",
            "configuration": None,
            "input": {
                "type_id": "concorde-code-review-request",
                "schema_version": 2,
                "data": {
                    "task": "Review the operation dispatch",
                    "target_id": "module.operations",
                },
            },
        }
        process = _run(
            ["--native-context", "prepare"],
            json.dumps({"invocation": invocation, "session_id": "policy-preview"}),
        )
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)
        value = json.loads(process.stdout)
        self.assertEqual("described", value["state"])
        self.assertNotIn("call", value)
        self.assertNotIn("workflow", value)
        self.assertIn("module.operations", value["result"]["output"]["data"]["answer"])
        self.assertEqual(
            "concorde-code-review-response", value["result"]["output"]["type_id"]
        )


class TargetAdmissionTests(unittest.TestCase):
    """Module-bound requests whose target or focus does not resolve."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name)
        self.primary = directory / "primary"
        self.primary.mkdir()
        project(self.primary)
        git(self.primary, "init", "-q", "-b", "integration")
        git(self.primary, "config", "user.name", "Concorde Test")
        git(self.primary, "config", "user.email", "concorde-test@example.invalid")
        git(self.primary, "add", "-A")
        git(self.primary, "commit", "-qm", "Fixture")
        self.change = directory / "change"
        git(self.primary, "worktree", "add", "-q", "-b", "candidate", str(self.change))

    def call(self, root, name, data, host):
        return run_operation(
            name, CONFIGURATION, typed(name + "-request", data), host_context=host
        )

    def snapshot(self):
        """Candidate bindings, worktrees and project files outside run diagnostics."""
        files = {
            path.relative_to(root): path.read_bytes()
            for root in (self.primary, self.change)
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and ".concorde/runs" not in path.as_posix()
        }
        return files, git_value(self.primary, "worktree", "list", "--porcelain")

    @verifies("scenario.admission.unknown-target", "scenario.admission.invalid-focus")
    def test_unresolved_target_or_focus_binds_nothing_and_starts_no_worker(self):
        before = self.snapshot()
        requests = (
            {**TARGET, "target_id": "module.unknown"},
            {**TARGET, "focus_id": "scenario.ledger.read"},
        )
        for root in (self.primary, self.change):
            for name in (
                "concorde-context-solve",
                "concorde-plan",
                "concorde-validate",
            ):
                for data, code in zip(requests, ("unknown_target", "invalid_focus")):
                    with self.subTest(root=root.name, operation=name, code=code):
                        host = RealHost(root, PACKAGE)
                        result = self.call(root, name, data, host)
                        self.assertEqual("blocked", result["status"], result)
                        self.assertEqual(code, result["errors"][0]["code"], result)
                        self.assertIsNone(result["output"])
                        self.assertEqual(before, self.snapshot())


class StaleBuildAdmissionTests(unittest.TestCase):
    """A model-backed request against a package whose sources changed since its build."""

    @verifies("scenario.admission.stale-build")
    def test_a_stale_build_refuses_a_model_backed_request_before_it_runs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for directory in ("agents", "prompts", "protocol", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            shutil.copytree(
                REPOSITORY_ROOT / "src/concorde/spec",
                root / "src/concorde/spec",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            # This isolated render fixture does not accept a consumer Protocol binding.
            (root / "protocol/manifest.json").unlink()

            def contents():
                return {
                    p.relative_to(root).as_posix(): p.read_bytes()
                    for p in root.rglob("*")
                    if p.is_file()
                }

            def invoke_model_backed_operation():
                # The fixture is this invocation's package root: a top-level model-backed
                # operation verifies the fixture build before admitting anything else.
                host = OperationHost(root, root, mode="describe-policy")
                return run_operation(
                    "concorde-spec-review",
                    None,
                    typed(
                        "concorde-spec-review-request",
                        {"target_id": "module.fixture", "task": "Review"},
                    ),
                    host_context=host,
                )

            write_build(root)
            admitted = invoke_model_backed_operation()
            self.assertNotEqual(
                "stale_build", (admitted["errors"] or [{}])[0].get("code"), admitted
            )
            helper = root / "src/concorde/spec/typed_data.py"
            helper.write_text(
                helper.read_text() + "\n# Fixture schema source change.\n"
            )
            before = contents()
            refused = invoke_model_backed_operation()
            self.assertEqual("blocked", refused["status"], refused)
            self.assertEqual("stale_build", refused["errors"][0]["code"], refused)
            self.assertIsNone(refused["output"])
            self.assertEqual(before, contents())


if __name__ == "__main__":
    unittest.main()
