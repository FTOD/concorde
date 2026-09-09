"""Real Git regressions for worktree ownership, awareness, recovery and primary delivery."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.host.change_worktree import (
    GUIDANCE_START, REGISTRY_PATH, STATE_PATH, git, git_value, read_change,
)
from concorde.host.typed_data import typed
from concorde.host.capability_service import CapabilityHost, run_capability
from concorde.host import worktree_delivery
from concorde.host import change_worktree
from concorde.specification.validation import validate_repository
from .support import CONFIGURATION, PACKAGE, ModelProcessDouble, project


class WorktreeLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.primary = self.directory / "primary"
        self.primary.mkdir()
        project(self.primary)
        (self.primary / "AGENTS.md").write_text("# Existing project policy\nKeep project conventions.\n")
        (self.primary / "shared.txt").write_text("base\n")
        git(self.primary, "init", "-q", "-b", "integration")
        git(self.primary, "config", "user.name", "Concorde Test")
        git(self.primary, "config", "user.email", "concorde-test@example.invalid")
        self.commit(self.primary, "Fixture")
        self.change = self.directory / "change"
        git(self.primary, "worktree", "add", "-b", "candidate", str(self.change))
        self.task = {"target_id": "service.transfer", "task": "Implement the transfer contract"}

    def commit(self, root, message):
        git(root, "add", "-A")
        git(root, "commit", "-qm", message)
        return git_value(root, "rev-parse", "HEAD")

    def run_op(self, root, name, data, callback=None, *, host=None, mode="execute"):
        double = ModelProcessDouble(callback)
        self.addCleanup(double.runtime_directory.cleanup)
        self.last_double = double
        host = host or CapabilityHost(root, PACKAGE, executor=double.executor, mode=mode)
        return run_capability(name, CONFIGURATION, typed(name + "-request", data), host_context=host)

    def ready(self, callback=None, task=None):
        result = self.run_op(self.change, "concorde-dev-loop", task or self.task, callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        state = read_change(self.change, required=True)
        self.assertEqual("ready", state["status"])
        self.assertFalse((self.change / ".concorde/attempts").exists())
        return state["change_id"]

    def ready_delivery(self):
        """A directly validated candidate for tests focused on Git delivery transactions."""
        (self.change / "app/transfer.py").write_text(
            'def transfer(balance, amount):\n'
            '    if amount <= 0 or amount > balance: raise ValueError("invalid transfer")\n'
            '    return balance - amount\n')
        result = self.run_op(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        return read_change(self.change, required=True)["change_id"]

    def test_main_sees_primary_inventory_and_secondary_draft_identity(self):
        result = self.run_op(self.change, "concorde-main", {"task": "Explain transfer"})
        self.assertEqual("succeeded", result["status"], result)
        observed = self.last_double.calls[0]["snapshot"]["workspace"]
        self.assertEqual("change", observed["kind"])
        self.assertEqual(str(self.primary), observed["primary_worktree"])
        self.assertEqual("integration", observed["primary_branch"])
        self.assertIsNotNone(observed["change_id"])
        state = read_change(self.change, required=True)
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.change / name).read_text()
            self.assertIn("initial working directory", text)
            self.assertIn(str(self.primary), text)
            self.assertEqual(1, text.count(GUIDANCE_START))
        unmanaged = self.directory / "unmanaged"
        git(self.primary, "worktree", "add", "-b", "another-change", str(unmanaged))
        result = self.run_op(self.primary, "concorde-main", {"task": "Explain transfer"})
        self.assertEqual("succeeded", result["status"], result)
        workspace = self.last_double.calls[0]["snapshot"]["workspace"]
        self.assertEqual("primary", workspace["kind"])
        self.assertEqual({"candidate", "another-change"}, {x["branch"] for x in workspace["active_worktrees"]})
        managed = next(x for x in workspace["active_worktrees"] if x["branch"] == "candidate")
        self.assertEqual(state["change_id"], managed["change_id"])
        stored = json.loads((self.primary / REGISTRY_PATH).read_text())
        self.assertEqual(workspace["active_worktrees"], stored["worktrees"])
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))

    def test_failed_delivery_preserves_visible_unresolved_task_gaps(self):
        def missing(stage, snapshot, data, cwd):
            if stage == "plan":
                data.update(outcome="spec_incomplete", gaps=[{
                    "question": "Who owns transfer admission?", "blocked_step": "Plan admission",
                    "needed_contract": "Transfer admission owner"}])
        blocked = self.run_op(self.change, "concorde-plan", self.task, missing)
        self.assertEqual("blocked", blocked["status"], blocked)
        before = read_change(self.change, required=True)
        rejected = self.run_op(self.primary, "concorde-deliver", {"change_id": before["change_id"]})
        self.assertEqual("blocked", rejected["status"], rejected)
        after = read_change(self.change, required=True)
        self.assertEqual(before["gap_history"], after["gap_history"])
        self.assertEqual(before["gaps"], after["gaps"])
        self.assertTrue(after["gaps"])

    def test_main_answers_workspace_metadata_without_target_reader(self):
        def status(stage, snapshot, data, cwd):
            if stage == "route":
                data.update(outcome="completed", answer="One change is in progress on candidate.",
                            routes=[], expand_targets=[])
        result = self.run_op(self.primary, "concorde-main", {"task": "What work is in progress?"}, status)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(["route"], [x["stage"] for x in self.last_double.calls])

    def test_guidance_and_initial_state_rollback_together(self):
        before = (self.change / "AGENTS.md").read_bytes()
        apply = change_worktree.apply_files
        def fail_state(root, changes, allowed, **kwargs):
            if any(item["path"] == STATE_PATH for item in changes):
                def reject():
                    raise OSError("fixture state transaction failure")
                return apply(root, changes, allowed, verify=reject)
            return apply(root, changes, allowed, **kwargs)
        with patch.object(change_worktree, "apply_files", side_effect=fail_state):
            result = self.run_op(self.change, "concorde-main", {"task": "Explain transfer"})
        self.assertNotEqual("succeeded", result["status"], result)
        self.assertEqual(before, (self.change / "AGENTS.md").read_bytes())
        self.assertFalse((self.change / "CLAUDE.md").exists())
        self.assertFalse((self.change / STATE_PATH).exists())

    def test_primary_mutation_creates_handoff_without_running_an_agent(self):
        result = self.run_op(self.primary, "concorde-dev-loop", self.task)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("worktree_handoff_required", result["errors"][0]["code"])
        self.assertEqual([], self.last_double.calls)
        created = Path(result["workspace"]["path"])
        message = result["errors"][0]["message"]
        self.assertIn("```text", message)
        for fact in (str(created), result["workspace"]["branch"], result["workspace"]["change_id"],
                     self.task["task"], str(created / STATE_PATH), "have not run", "No task agent",
                     '"temporary": true'):
            self.assertIn(fact, message)
        self.assertEqual(result, json.loads(json.dumps(result)))
        try:
            self.assertTrue((created / STATE_PATH).exists())
            self.assertEqual("created", read_change(created)["phase"])
            self.assertEqual("def transfer(balance, amount):\n    return balance\n",
                             (self.primary / "app/transfer.py").read_text())
        finally:
            git(self.primary, "worktree", "remove", "--force", str(created))
            created.parent.rmdir()

    def test_handoff_remains_one_json_response_on_the_paired_cli(self):
        operation = "concorde-dev-loop"
        task = {**self.task, "constraints": ["保留用户原文；不合并、不 push"]}
        invocation = {"type_id": "concorde-capability-invocation", "schema_version": 3,
                      "capability_id": operation, "mode": "execute", "configuration": CONFIGURATION,
                      "input": typed(operation + "-request", task)}
        process = subprocess.run([sys.executable, str(PACKAGE / "scripts/run-capability.py"), operation],
                                 cwd=self.primary, input=json.dumps(invocation), text=True,
                                 capture_output=True, env={**os.environ, "CONCORDE_STUDIO_URL": ""})
        result = json.loads(process.stdout)
        created = Path(result["workspace"]["path"])
        try:
            self.assertEqual(3, process.returncode, process.stderr)
            self.assertEqual("", process.stderr)
            self.assertEqual("worktree_handoff_required", result["errors"][0]["code"])
            message = result["errors"][0]["message"]
            self.assertIn("```text", message)
            self.assertIn(task["constraints"][0], message)
            self.assertIn(str(created / STATE_PATH), message)
            self.assertEqual("created", read_change(created)["phase"])
        finally:
            git(self.primary, "worktree", "remove", "--force", str(created))
            created.parent.rmdir()

    def test_second_top_level_task_cannot_share_the_same_change_worktree(self):
        self.ready()
        result = self.run_op(self.change, "concorde-plan",
                             {"target_id": "module.ledger", "task": "Implement an unrelated ledger change"})
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("incompatible_handoff", result["errors"][0]["code"])
        self.assertEqual("ready", read_change(self.change)["status"])

    def test_partial_spec_reconciliation_is_explicit_and_resumes_completed_authors(self):
        before_primary = (self.primary / "specs/transfer/module.md").read_bytes()
        def contract(role, peer, value_type, example):
            return "\n```concorde-contract\n" + json.dumps({"id": "contract.fixture.sync", "version": 1,
                "role": role, "peer": peer, "schema": {"type": value_type},
                "semantics": "The coordinated value has the agreed representation.", "example": example}) + "\n```\n"
        consumer = self.change / "specs/transfer/module.md"
        provider = self.change / "specs/ledger/module.md"
        consumer.write_text(consumer.read_text() + contract("required", "module.ledger", "integer", 7))
        provider.write_text(provider.read_text() + contract("provided", "service.transfer", "integer", 7))
        task = {"target_id": "scope.bank", "task": "Coordinate transfer and ledger changes"}
        def partial(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"].append({"id": "task.ledger", "target_id": "module.ledger",
                    "description": "Implement the ledger API", "acceptance": "Read a known balance", "complete": False})
            if stage == "specify" and snapshot["target_id"] == "service.transfer":
                document = snapshot["target_spec"][0]
                replacement = document["content"].replace('"type": "integer"', '"type": "string"').replace('"example": 7', '"example": "new"')
                data["documents"] = [{"path": document["path"], "content": replacement + "\nClarified candidate promise.\n"}]
            if stage == "specify" and snapshot["target_id"] == "module.ledger":
                data.update(outcome="spec_incomplete", gaps=[{"question": "Which account is known?",
                    "blocked_step": "Author the ledger view", "needed_contract": "Known account identity"}])
        result = self.run_op(self.change, "concorde-dev-loop", task, partial)
        self.assertEqual("blocked", result["status"], result)
        state = read_change(self.change, required=True)
        records = state["targets"]["scope.bank"]["coordination"]
        self.assertEqual("completed", records["service.transfer"]["spec_status"])
        self.assertEqual("blocked", records["module.ledger"]["spec_status"])
        self.assertEqual("spec_reconciliation", state["phase"])
        self.assertEqual("spec_incomplete", state["outcome"])
        self.assertIn("Clarified candidate promise", (self.change / "specs/transfer/module.md").read_text())
        self.assertEqual(before_primary, (self.primary / "specs/transfer/module.md").read_bytes())
        self.assertEqual("invalid", validate_repository(self.change, package_root=PACKAGE).status)
        self.assertFalse(any(c["stage"] == "implementation" for c in self.last_double.calls))
        def finish_provider(stage, snapshot, data, cwd):
            if stage == "specify" and snapshot["target_id"] == "module.ledger":
                document = snapshot["target_spec"][0]
                replacement = document["content"].replace('"type": "integer"', '"type": "string"').replace('"example": 7', '"example": "new"')
                data["documents"] = [{"path": document["path"], "content": replacement}]
        result = self.run_op(self.change, "concorde-dev-loop", task, finish_provider)
        self.assertEqual("succeeded", result["status"], result)
        authors = [c["snapshot"]["target_id"] for c in self.last_double.calls if c["stage"] == "specify"]
        self.assertEqual(["module.ledger"], authors)
        self.assertEqual(state["change_id"], read_change(self.change)["change_id"])
        self.assertTrue(self.change.exists())

    def test_source_delivery_removes_active_worktree_and_retry_does_not_republish(self):
        change_id = self.ready()
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        self.assertFalse(self.change.exists())
        branch = "concorde/delivered/" + change_id
        delivered = git_value(self.primary, "rev-parse", branch)
        with patch.object(worktree_delivery, "_verify_merged_tree", side_effect=AssertionError("duplicate checks")):
            again = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(delivered, git_value(self.primary, "rev-parse", branch))
        self.assertIn(branch, again["output"]["data"]["answer"])

    def test_primary_merge_requires_separate_delivery_and_primary_session(self):
        change_id = self.ready_delivery()
        request = {"change_id": change_id, "merge_primary": True}
        result = self.run_op(self.change, "concorde-deliver", request)
        self.assertEqual("primary_session_required", result["errors"][0]["code"], result)
        result = self.run_op(self.primary, "concorde-deliver", request)
        self.assertEqual("delivery_required", result["errors"][0]["code"], result)
        staged = self.run_op(self.change, "concorde-deliver", {"change_id": change_id, "keep_worktree": True})
        self.assertEqual("succeeded", staged["status"], staged)
        result = self.run_op(self.change, "concorde-deliver", request)
        self.assertEqual("primary_session_required", result["errors"][0]["code"], result)
        redirected = CapabilityHost(self.primary, PACKAGE, session_root=self.change)
        result = self.run_op(self.primary, "concorde-deliver", request, host=redirected)
        self.assertEqual("primary_session_required", result["errors"][0]["code"], result)
        merged = self.run_op(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", merged["status"], merged)
        head = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(worktree_delivery, "_verify_merged_tree", side_effect=AssertionError("duplicate merge checks")):
            again = self.run_op(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(head, git_value(self.primary, "rev-parse", "HEAD"))

    def test_explicit_retention_survives_interrupted_initial_cleanup(self):
        change_id = self.ready_delivery()
        before = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(worktree_delivery, "_cleanup", side_effect=OSError("interrupted cleanup")):
            result = self.run_op(self.change, "concorde-deliver",
                                 {"change_id": change_id, "keep_worktree": True})
        self.assertEqual("failed", result["status"], result)
        again = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        self.assertIn("retained", again["output"]["data"]["answer"])
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    def test_cleanup_retry_persists_a_changed_retention_choice_before_cleanup(self):
        change_id = self.ready_delivery()
        with patch.object(worktree_delivery, "_cleanup", side_effect=OSError("interrupted cleanup")):
            result = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
            self.assertEqual("failed", result["status"], result)
            result = self.run_op(self.primary, "concorde-deliver",
                                 {"change_id": change_id, "keep_worktree": True})
        self.assertEqual("failed", result["status"], result)
        again = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        removed = self.run_op(self.primary, "concorde-deliver",
                              {"change_id": change_id, "keep_worktree": False})
        self.assertEqual("succeeded", removed["status"], removed)
        self.assertFalse(self.change.exists())

    def test_independent_deliveries_do_not_update_each_other_or_primary(self):
        before = git_value(self.primary, "rev-parse", "HEAD")
        first_id = self.ready_delivery()
        first = self.run_op(self.change, "concorde-deliver", {"change_id": first_id})
        self.assertEqual("succeeded", first["status"], first)
        first_branch = "concorde/delivered/" + first_id
        first_head = git_value(self.primary, "rev-parse", first_branch)
        self.change = self.directory / "second-change"
        git(self.primary, "worktree", "add", "-b", "second-candidate", str(self.change))
        second_id = self.ready_delivery()
        second = self.run_op(self.change, "concorde-deliver", {"change_id": second_id})
        self.assertEqual("succeeded", second["status"], second)
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(first_head, git_value(self.primary, "rev-parse", first_branch))
        self.assertTrue(git_value(self.primary, "rev-parse", "concorde/delivered/" + second_id))
        start = threading.Barrier(2)
        checking = threading.Lock()
        verify = worktree_delivery._verify_merged_tree
        def checked(*args, **kwargs):
            self.assertTrue(checking.acquire(blocking=False), "overlapping primary merge checks")
            try:
                return verify(*args, **kwargs)
            finally:
                checking.release()
        def promote(change_id):
            start.wait(timeout=10)
            return run_capability("concorde-deliver", CONFIGURATION,
                typed("concorde-deliver-request", {"change_id": change_id, "merge_primary": True}),
                host_context=CapabilityHost(self.primary, PACKAGE))
        with patch.object(worktree_delivery, "_verify_merged_tree", side_effect=checked):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(promote, (first_id, second_id)))
        for merged in results:
            self.assertEqual("succeeded", merged["status"], merged)
        for change_id in (first_id, second_id):
            branch = "concorde/delivered/" + change_id
            self.assertEqual(0, git(self.primary, "merge-base", "--is-ancestor", branch, "HEAD", check=False).returncode)

    def test_legacy_delivery_receipt_does_not_claim_primary_was_unchanged(self):
        change_id = self.ready_delivery()
        self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        merged = self.run_op(self.primary, "concorde-deliver",
                             {"change_id": change_id, "merge_primary": True})
        self.assertEqual("succeeded", merged["status"], merged)
        path = self.primary / merged["output"]["data"]["artifacts"][0]["path"]
        receipt = json.loads(path.read_text())
        receipt["target_branch"] = receipt.pop("primary_branch")
        receipt.pop("primary_merge")
        path.write_text(json.dumps(receipt))
        before = git_value(self.primary, "rev-parse", "HEAD")
        again = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", again["status"], again)
        self.assertIn("into integration", again["output"]["data"]["answer"])
        self.assertNotIn("primary branch is unchanged", again["output"]["data"]["answer"])
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    def test_primary_merge_checks_latest_integration_and_preserves_delivery_on_failure(self):
        change_id = self.ready_delivery()
        staged = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", staged["status"], staged)
        path = self.primary / "checks/transfer_check.py"
        path.write_text(path.read_text() + '\nassert transfer(100, 20) == 40\n')
        advanced = self.commit(self.primary, "Changed acceptance after delivery")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id, "merge_primary": True})
        self.assertEqual("failed_merge_checks", result["errors"][0]["code"], result)
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue(git_value(self.primary, "rev-parse", "concorde/delivered/" + change_id))

    def test_final_merge_conflict_preserves_primary_and_delivered_branch(self):
        (self.change / "shared.txt").write_text("candidate\n")
        change_id = self.ready_delivery()
        staged = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", staged["status"], staged)
        (self.primary / "shared.txt").write_text("primary\n")
        before = self.commit(self.primary, "Conflicting change after delivery")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id, "merge_primary": True})
        self.assertEqual("merge_conflict", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual("candidate", git_value(self.primary, "show", "concorde/delivered/" + change_id + ":shared.txt"))
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))

    def test_delivery_does_not_overwrite_an_existing_branch(self):
        change_id = self.ready_delivery()
        branch = "concorde/delivered/" + change_id
        git(self.primary, "branch", branch)
        before = git_value(self.primary, "rev-parse", branch)
        result = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("stale_delivery", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", branch))
        self.assertTrue(self.change.exists())

    def test_primary_merge_preview_after_source_removal_is_read_only(self):
        change_id = self.ready_delivery()
        result = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        path = self.primary / result["output"]["data"]["artifacts"][0]["path"]
        receipt = path.read_bytes()
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id, "merge_primary": True},
                             mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertEqual(receipt, path.read_bytes())
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    def test_changed_delivery_ref_blocks_final_merge(self):
        change_id = self.ready_delivery()
        result = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        branch = "concorde/delivered/" + change_id
        git(self.primary, "update-ref", "refs/heads/" + branch, "HEAD")
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id, "merge_primary": True})
        self.assertEqual("stale_delivery", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    def test_primary_merge_recovers_receipt_after_update_without_merging_again(self):
        change_id = self.ready_delivery()
        staged = self.run_op(self.change, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", staged["status"], staged)
        write = worktree_delivery._write_json
        def interrupted(root, relative, receipt):
            if (receipt.get("primary_merge") or {}).get("status") == "merged":
                raise OSError("interrupted after primary ref update")
            return write(root, relative, receipt)
        request = {"change_id": change_id, "merge_primary": True}
        with patch.object(worktree_delivery, "_write_json", side_effect=interrupted):
            result = self.run_op(self.primary, "concorde-deliver", request)
        self.assertEqual("failed", result["status"], result)
        merged = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(worktree_delivery, "_verify_merged_tree", side_effect=AssertionError("duplicate checks")):
            again = self.run_op(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(merged, git_value(self.primary, "rev-parse", "HEAD"))
        receipt = json.loads((self.primary / again["output"]["data"]["artifacts"][0]["path"]).read_text())
        self.assertEqual("merged", receipt["primary_merge"]["status"])
        self.assertTrue((self.primary / ".concorde/deliveries" / change_id / "staging").is_dir())
        self.assertTrue((self.primary / ".concorde/deliveries" / change_id / "primary").is_dir())

    def test_third_worktree_redirected_runtime_and_nested_delivery_are_rejected(self):
        change_id = self.ready()
        third = self.directory / "third"
        git(self.primary, "worktree", "add", "-b", "unrelated", str(third))
        third_package = third / ".concorde/framework"
        third_package.mkdir(parents=True, exist_ok=True)
        old_head = git_value(self.primary, "rev-parse", "HEAD")
        hosts = [CapabilityHost(third, PACKAGE),
                 CapabilityHost(self.primary, PACKAGE, session_root=third),
                 CapabilityHost(self.primary, third_package),
                 CapabilityHost(self.primary, PACKAGE, depth=1)]
        for host in hosts:
            with self.subTest(root=host.project_root, origin=host.session_root, depth=host.depth):
                result = self.run_op(host.project_root, "concorde-deliver", {"change_id": change_id}, host=host)
                self.assertEqual("delivery_session_required", result["errors"][0]["code"], result)
        self.assertEqual(old_head, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue(self.change.exists())

    def test_primary_delivery_can_explicitly_retain_source(self):
        change_id = self.ready()
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id, "keep_worktree": True})
        self.assertEqual("succeeded", result["status"], result)
        self.assertTrue(self.change.exists())
        self.assertEqual("delivered", read_change(self.change)["status"])

    def test_paired_cli_delivers_from_source_and_primary_can_clean_up(self):
        change_id = self.ready()
        invocation = {"type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": "concorde-deliver", "mode": "execute", "configuration": None,
            "input": typed("concorde-deliver-request", {"change_id": change_id})}
        command = [sys.executable, str(PACKAGE / "scripts/run-capability.py"), "concorde-deliver"]
        secondary = subprocess.run(command, input=json.dumps(invocation), capture_output=True,
                                   text=True, cwd=self.change)
        self.assertEqual(0, secondary.returncode, secondary.stdout + secondary.stderr)
        self.assertEqual("delivered", json.loads(secondary.stdout)["output"]["data"]["outcome"])
        self.assertFalse(self.change.exists())
        invocation["input"]["data"]["merge_primary"] = True
        primary = subprocess.run(command, input=json.dumps(invocation), capture_output=True,
                                 text=True, cwd=self.primary)
        self.assertEqual(0, primary.returncode, primary.stdout + primary.stderr)
        self.assertEqual("delivered", json.loads(primary.stdout)["output"]["data"]["outcome"])
        self.assertFalse(self.change.exists())

    def test_primary_delivery_stages_separate_branch_and_removes_only_transient_guidance(self):
        original = (self.primary / "AGENTS.md").read_text()
        self.run_op(self.change, "concorde-main", {"task": "Explain transfer"})
        path = self.change / "AGENTS.md"
        path.write_text(path.read_text() + "\nA deliberately authored convention.\n")
        change_id = self.ready()
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("delivered", result["output"]["data"]["outcome"])
        self.assertEqual("integration", git_value(self.primary, "branch", "--show-current"))
        self.assertFalse(self.change.exists())
        self.assertEqual(original, (self.primary / "AGENTS.md").read_text())
        delivered_branch = "concorde/delivered/" + change_id
        self.assertEqual(original + "\nA deliberately authored convention.\n",
                         git(self.primary, "show", delivered_branch + ":AGENTS.md").stdout)
        self.assertFalse((self.primary / "CLAUDE.md").exists())
        self.assertFalse((self.primary / STATE_PATH).exists())
        self.assertEqual([], json.loads((self.primary / REGISTRY_PATH).read_text())["worktrees"])
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))
        tracked = git_value(self.primary, "ls-tree", "-r", "--name-only", delivered_branch)
        self.assertNotIn(STATE_PATH, tracked)
        self.assertNotIn(REGISTRY_PATH, tracked)
        self.assertNotIn(".concorde/work/", tracked)
        self.assertNotIn(".concorde/runs/", tracked)
        receipt = json.loads((self.primary / result["output"]["data"]["artifacts"][0]["path"]).read_text())
        self.assertEqual(delivered_branch, receipt["target_branch"])
        self.assertEqual("integration", receipt["primary_branch"])
        self.assertIsNone(receipt["primary_merge"])
        self.assertEqual("delivered", receipt["status"])
        self.assertTrue(all(c["status"] == "passed" for c in receipt["checks"]))

    def test_delivery_preview_does_not_merge_or_change_state(self):
        change_id = self.ready()
        primary_head = git_value(self.primary, "rev-parse", "HEAD")
        source_head = git_value(self.change, "rev-parse", "HEAD")
        before = (self.change / STATE_PATH).read_bytes()
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id}, mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertEqual(primary_head, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(source_head, git_value(self.change, "rev-parse", "HEAD"))
        self.assertEqual(before, (self.change / STATE_PATH).read_bytes())
        self.assertEqual([], self.last_double.calls)

    def test_directly_authored_candidate_can_be_validated_and_delivered_without_a_plan(self):
        path = self.change / "app/transfer.py"
        path.write_text('def transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n')
        spec = self.change / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nClarified directly in the candidate.\n")
        result = self.run_op(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.change, required=True)
        self.assertEqual({}, state["targets"])
        self.assertTrue(state["validation"]["checks"])
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": state["change_id"]})
        self.assertEqual("succeeded", result["status"], result)
        self.assertIn("Clarified directly", git_value(self.primary, "show",
            "concorde/delivered/" + state["change_id"] + ":specs/transfer/module.md"))
        self.assertFalse(self.change.exists())

    def test_validation_does_not_bypass_an_unfinished_authored_plan(self):
        result = self.run_op(self.change, "concorde-plan", self.task)
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.change)
        result = self.run_op(self.change, "concorde-validate", {**self.task, "change_id": state["change_id"]})
        self.assertNotEqual("ready", result["output"]["data"]["outcome"])
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": state["change_id"]})
        self.assertEqual("incomplete_change", result["errors"][0]["code"], result)

    def test_stale_candidate_and_dirty_primary_are_preserved(self):
        change_id = self.ready()
        (self.change / "late.txt").write_text("Unverified candidate work\n")
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("stale_evidence", result["errors"][0]["code"], result)
        self.assertTrue((self.change / "late.txt").exists())
        (self.change / "late.txt").unlink()
        (self.primary / "local.txt").write_text("Primary user work\n")
        (self.primary / "shared.txt").write_text("Staged primary work\n")
        git(self.primary, "add", "shared.txt")
        index_before = git_value(self.primary, "diff", "--cached", "--binary")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id, "merge_primary": True})
        self.assertEqual("dirty_primary", result["errors"][0]["code"], result)
        self.assertEqual("Primary user work\n", (self.primary / "local.txt").read_text())
        self.assertEqual("Staged primary work\n", (self.primary / "shared.txt").read_text())
        self.assertEqual(index_before, git_value(self.primary, "diff", "--cached", "--binary"))
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertFalse(self.change.exists())

    def test_primary_can_advance_before_a_clean_verified_merge(self):
        change_id = self.ready()
        (self.primary / "another.txt").write_text("Accepted independent change\n")
        advanced = self.commit(self.primary, "Independent accepted change")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("Accepted independent change\n", (self.primary / "another.txt").read_text())
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "concorde/delivered/" + change_id + "^1"))

    def test_merge_conflict_does_not_change_primary_or_discard_candidate(self):
        (self.change / "shared.txt").write_text("candidate\n")
        change_id = self.ready()
        (self.primary / "shared.txt").write_text("accepted\n")
        advanced = self.commit(self.primary, "Conflicting accepted change")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("merge_conflict", result["errors"][0]["code"], result)
        self.assertEqual("blocked", read_change(self.change)["status"])
        self.assertEqual("merge_conflict", read_change(self.change)["outcome"])
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual("candidate\n", (self.change / "shared.txt").read_text())

    def test_self_hosted_integration_builds_its_exact_checkout_before_validation(self):
        from concorde.host.build import verify_fresh
        fixture_report=validate_repository(self.primary,package_root=PACKAGE)
        self.assertEqual(fixture_report.status,'success')
        for directory in ('prompts','skills','agents','protocol'):
            shutil.copytree(PACKAGE/directory,self.primary/directory)
        (self.primary/'concorde.json').write_text('{}')
        (self.primary/'app/transfer.py').write_text(
            'def transfer(balance, amount):\n'
            '    if amount <= 0 or amount > balance: raise ValueError("invalid transfer")\n'
            '    return balance - amount\n')
        with (self.primary/'.gitignore').open('a') as stream:
            stream.write('\ngenerated/\n.agents/\n.claude/\n')
        commit=self.commit(self.primary,'Self-hosted integration fixture')
        tree=git_value(self.primary,'rev-parse','HEAD^{tree}')
        verified=[]
        def inspect(root,**kwargs):
            self.assertNotEqual(root,self.primary)
            self.assertEqual(git_value(root,'rev-parse','HEAD^{tree}'),tree)
            verify_fresh(root)
            verified.append(root)
            return fixture_report
        with patch.object(worktree_delivery,'validate_repository',side_effect=inspect):
            checks=worktree_delivery._verify_merged_tree(
                CapabilityHost(self.primary,PACKAGE),commit,tree,'change.integration-build')
        self.assertEqual(len(verified),1)
        self.assertFalse(verified[0].exists())
        self.assertTrue(checks)
        self.assertTrue(all(check['status']=='passed' for check in checks))
        self.assertFalse((self.primary/'generated').exists())

    def test_actual_integration_checks_run_after_primary_advances(self):
        change_id = self.ready()
        path = self.primary / "checks/transfer_check.py"
        path.write_text(path.read_text() + '\nassert transfer(100, 20) == 40\n')
        advanced = self.commit(self.primary, "Changed acceptance")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("failed_merge_checks", result["errors"][0]["code"], result)
        self.assertEqual("failed_merge_checks", read_change(self.change)["outcome"])
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue((self.change / STATE_PATH).exists())

    def test_cleanup_failure_resumes_without_a_second_merge_or_check_run(self):
        change_id = self.ready()
        actual_git = worktree_delivery.git
        def fail_cleanup(root, *args, **kwargs):
            if args == ("worktree", "remove", "--force", str(self.change)):
                return subprocess.CompletedProcess(args, 1, "", "fixture cleanup failure")
            return actual_git(root, *args, **kwargs)
        with patch.object(worktree_delivery, "git", side_effect=fail_cleanup):
            result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("cleanup_pending", read_change(self.change)["status"])
        merged = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(worktree_delivery, "_verify_merged_tree", side_effect=AssertionError("duplicate verification")):
            result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
            self.assertEqual("succeeded", result["status"], result)
            repeated = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
            self.assertEqual("succeeded", repeated["status"], repeated)
        self.assertEqual(merged, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertFalse(self.change.exists())

    def test_cleanup_can_finish_after_files_were_removed_but_git_registration_remains(self):
        change_id = self.ready()
        actual_git = worktree_delivery.git
        def remove_files_then_fail(root, *args, **kwargs):
            if args == ("worktree", "remove", "--force", str(self.change)):
                shutil.rmtree(self.change)
                return subprocess.CompletedProcess(args, 1, "", "fixture metadata cleanup failure")
            return actual_git(root, *args, **kwargs)
        with patch.object(worktree_delivery, "git", side_effect=remove_files_then_fail):
            result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("failed", result["status"], result)
        merged = git_value(self.primary, "rev-parse", "HEAD")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(merged, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertNotIn(str(self.change), git_value(self.primary, "worktree", "list", "--porcelain"))


if __name__ == "__main__":
    unittest.main()
