"""Real Git regressions for worktree ownership, awareness, recovery and primary delivery."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.capabilities.change_worktree import (
    GUIDANCE_START, REGISTRY_PATH, STATE_PATH, git, git_value, read_change,
)
from concorde.capabilities.operation_data import typed
from concorde.capabilities.operation_service import OperationHost, run_operation
from concorde.capabilities import worktree_delivery
from concorde.capabilities import change_worktree
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
        host = host or OperationHost(root, PACKAGE, executor=double.executor, mode=mode)
        return run_operation(name, CONFIGURATION, typed(name + "-request", data), host_context=host)

    def ready(self, callback=None, task=None):
        result = self.run_op(self.change, "concorde-standard-dev-loop", task or self.task, callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        state = read_change(self.change, required=True)
        self.assertEqual("ready", state["status"])
        self.assertFalse((self.change / ".concorde/attempts").exists())
        return state["change_id"]

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
        result = self.run_op(self.primary, "concorde-standard-dev-loop", self.task)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("worktree_handoff_required", result["errors"][0]["code"])
        self.assertEqual([], self.last_double.calls)
        created = Path(result["workspace"]["path"])
        try:
            self.assertTrue((created / STATE_PATH).exists())
            self.assertEqual("created", read_change(created)["phase"])
            self.assertEqual("def transfer(balance, amount):\n    return balance\n",
                             (self.primary / "app/transfer.py").read_text())
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
        before_primary = (self.primary / "specs/send-money.md").read_bytes()
        def contract(role, peer, value_type, example):
            return "\n```concorde-contract\n" + json.dumps({"id": "contract.fixture.sync", "version": 1,
                "role": role, "peer": peer, "schema": {"type": value_type},
                "semantics": "The coordinated value has the agreed representation.", "example": example}) + "\n```\n"
        consumer = self.change / "specs/send-money.md"
        provider = self.change / "specs/ledger-api.md"
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
        result = self.run_op(self.change, "concorde-standard-dev-loop", task, partial)
        self.assertEqual("blocked", result["status"], result)
        state = read_change(self.change, required=True)
        records = state["targets"]["scope.bank"]["coordination"]
        self.assertEqual("completed", records["service.transfer"]["spec_status"])
        self.assertEqual("blocked", records["module.ledger"]["spec_status"])
        self.assertEqual("spec_reconciliation", state["phase"])
        self.assertEqual("spec_incomplete", state["outcome"])
        self.assertIn("Clarified candidate promise", (self.change / "specs/send-money.md").read_text())
        self.assertEqual(before_primary, (self.primary / "specs/send-money.md").read_bytes())
        self.assertEqual("invalid", validate_repository(self.change, package_root=PACKAGE).status)
        self.assertFalse(any(c["stage"] == "implementation" for c in self.last_double.calls))
        def finish_provider(stage, snapshot, data, cwd):
            if stage == "specify" and snapshot["target_id"] == "module.ledger":
                document = snapshot["target_spec"][0]
                replacement = document["content"].replace('"type": "integer"', '"type": "string"').replace('"example": 7', '"example": "new"')
                data["documents"] = [{"path": document["path"], "content": replacement}]
        result = self.run_op(self.change, "concorde-standard-dev-loop", task, finish_provider)
        self.assertEqual("succeeded", result["status"], result)
        authors = [c["snapshot"]["target_id"] for c in self.last_double.calls if c["stage"] == "specify"]
        self.assertEqual(["module.ledger"], authors)
        self.assertEqual(state["change_id"], read_change(self.change)["change_id"])
        self.assertTrue(self.change.exists())

    def test_secondary_redirected_and_nested_delivery_sessions_are_rejected(self):
        change_id = self.ready()
        old_head = git_value(self.primary, "rev-parse", "HEAD")
        hosts = [OperationHost(self.change, PACKAGE),
                 OperationHost(self.change, PACKAGE, allow_primary_worktree=True),
                 OperationHost(self.primary, PACKAGE, session_root=self.change),
                 OperationHost(self.primary, PACKAGE, depth=1)]
        for host in hosts:
            with self.subTest(root=host.project_root, origin=host.session_root, depth=host.depth):
                result = self.run_op(host.project_root, "concorde-deliver", {"change_id": change_id}, host=host)
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("primary_session_required", result["errors"][0]["code"])
                self.assertIn(str(self.primary), result["errors"][0]["message"])
        self.assertEqual(old_head, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue(self.change.exists())

    def test_secondary_owned_runtime_cannot_deliver_after_changing_cwd(self):
        change_id = self.ready()
        secondary_package = self.change / ".concorde/framework"
        secondary_package.mkdir()
        host = OperationHost(self.primary, secondary_package)
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id}, host=host)
        self.assertEqual("primary_session_required", result["errors"][0]["code"], result)
        self.assertTrue(self.change.exists())

    def test_paired_cli_rejects_secondary_and_delivers_from_primary(self):
        change_id = self.ready()
        invocation = {"type_id": "concorde-operation-invocation", "schema_version": 2,
            "operation_id": "concorde-deliver", "mode": "execute", "configuration": None,
            "input": typed("concorde-deliver-request", {"change_id": change_id})}
        command = [sys.executable, str(PACKAGE / "operations/concorde-deliver/operation.py")]
        secondary = subprocess.run(command, input=json.dumps(invocation), capture_output=True,
                                   text=True, cwd=self.change)
        self.assertEqual(3, secondary.returncode, secondary.stdout + secondary.stderr)
        self.assertEqual("primary_session_required", json.loads(secondary.stdout)["errors"][0]["code"])
        primary = subprocess.run(command, input=json.dumps(invocation), capture_output=True,
                                 text=True, cwd=self.primary)
        self.assertEqual(0, primary.returncode, primary.stdout + primary.stderr)
        self.assertEqual("delivered", json.loads(primary.stdout)["output"]["data"]["outcome"])
        self.assertFalse(self.change.exists())

    def test_primary_delivery_merges_non_main_branch_and_removes_only_transient_guidance(self):
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
        self.assertEqual(original + "\nA deliberately authored convention.\n", (self.primary / "AGENTS.md").read_text())
        self.assertFalse((self.primary / "CLAUDE.md").exists())
        self.assertFalse((self.primary / STATE_PATH).exists())
        self.assertEqual([], json.loads((self.primary / REGISTRY_PATH).read_text())["worktrees"])
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))
        tracked = git_value(self.primary, "ls-tree", "-r", "--name-only", "HEAD")
        self.assertNotIn(STATE_PATH, tracked)
        self.assertNotIn(REGISTRY_PATH, tracked)
        self.assertNotIn(".concorde/work/", tracked)
        self.assertNotIn(".concorde/runs/", tracked)
        receipt = json.loads((self.primary / result["output"]["data"]["artifacts"][0]["path"]).read_text())
        self.assertEqual("integration", receipt["target_branch"])
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
        spec = self.change / "specs/send-money.md"
        spec.write_text(spec.read_text() + "\nClarified directly in the candidate.\n")
        result = self.run_op(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.change, required=True)
        self.assertEqual({}, state["targets"])
        self.assertTrue(state["validation"]["checks"])
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": state["change_id"]})
        self.assertEqual("succeeded", result["status"], result)
        self.assertIn("Clarified directly", (self.primary / "specs/send-money.md").read_text())
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
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("dirty_primary", result["errors"][0]["code"], result)
        self.assertEqual("Primary user work\n", (self.primary / "local.txt").read_text())
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue(self.change.exists())

    def test_primary_can_advance_before_a_clean_verified_merge(self):
        change_id = self.ready()
        (self.primary / "another.txt").write_text("Accepted independent change\n")
        advanced = self.commit(self.primary, "Independent accepted change")
        result = self.run_op(self.primary, "concorde-deliver", {"change_id": change_id})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("Accepted independent change\n", (self.primary / "another.txt").read_text())
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD^1"))

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
