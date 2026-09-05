from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.operation_data import OperationDataError, decode, typed, validate_typed, verify_artifacts
from concorde.capabilities.operation_service import OperationHost, run_operation
from concorde.lifecycle.delivery import apply_delivery, materialize_delivery_proposal, propose_delivery
from tests.concorde.support.feature_workspace import create_feature_file, write_complete_attempt, write_selection
from tests.concorde.support.operation_json import CONFIGURATION, ScriptedAgent, configure, investigation_result
from tests.concorde.support.reflection_triage import create_triage_project, initialize_git, git, write_plan
from tests.concorde.support.feature_workspace import reflection_entry, write_reflection_collection

FEATURE = "specs/example/features/001-deliver.md"
ATTEMPT = ".concorde/attempts/feature.example.deliver"


class OperationJSONIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        create_feature_file(self.root)
        write_selection(self.root, FEATURE)
        configure(self.root)

    def task(self, operation="concorde-plan"):
        return typed(operation + "-context", {"feature_path": FEATURE, "request": "Implement the fixture change", "constraints": []})

    def author(self, capability, runtime_input, root):
        if capability == "concorde-plan-author":
            attempt = root / ATTEMPT
            attempt.mkdir(parents=True, exist_ok=True)
            (attempt / "plan.md").write_text("# Plan\n\nImplement the fixture change.\n")
            (attempt / "tasks.md").write_text("# Tasks\n\n- [ ] T001 Implement fixture change\n")

    def host(self, agent=None, *, mode="execute"):
        return OperationHost(self.root, REPOSITORY_ROOT, mode=mode,
                             executor=agent.executor if agent else None,
                             allow_primary_worktree=True)

    def test_plan_passes_typed_context_and_returns_verified_artifact_refs(self):
        agent = ScriptedAgent(self.author)
        host = self.host(agent)
        result = run_operation("concorde-plan", CONFIGURATION, self.task(), host_context=host)
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual([call["capability"] for call in agent.calls], ["concorde-plan-context", "concorde-plan-author"])
        author = agent.calls[1]["input"]
        self.assertEqual(author["type_id"], "concorde-plan-author-context")
        self.assertEqual(author["data"]["task"], self.task())
        self.assertEqual(author["data"]["planning_context"]["data"]["feature_id"], "feature.example.deliver")
        self.assertEqual(result["output"]["type_id"], "concorde-plan-result")
        self.assertEqual(len(host.evidence), 2)
        verify_artifacts(self.root, result["output"])

    def test_old_completion_cannot_be_replayed_into_a_new_invocation(self):
        from dataclasses import replace

        agent = ScriptedAgent()
        receipts = []
        def capture(specification):
            result = agent.executor(specification)
            receipts.append(result)
            return result
        first = run_operation("concorde-plan", CONFIGURATION, self.task(),
                              host_context=replace(self.host(), executor=capture))
        self.assertEqual(first["status"], "blocked")  # No author artifacts, so the checkout stays unchanged.
        second = run_operation("concorde-plan", CONFIGURATION, self.task(),
                               host_context=replace(self.host(), executor=lambda specification: receipts[0]))
        self.assertEqual(second["status"], "failed", second)
        self.assertNotEqual(first["invocation_id"], second["invocation_id"])
        self.assertIn("current launch", second["errors"][0]["message"])

    def test_missing_author_artifacts_and_failed_completion_stop_success(self):
        for agent in (ScriptedAgent(), ScriptedAgent(self.author, failure="concorde-plan-context")):
            with self.subTest(failure=agent.failure):
                result = run_operation("concorde-plan", CONFIGURATION, self.task(), host_context=self.host(agent))
                self.assertIn(result["status"], {"failed", "blocked"}, result)
                self.assertIsNone(result["output"])
                self.assertTrue(result["errors"])
                if agent.failure:
                    self.assertEqual(len(agent.calls), 1)

    def test_wrong_types_versions_fields_and_configuration_reject_before_launch(self):
        cases = []
        for patch in ({"schema_version": 2}, {"schema_version": True}, {"type_id": "concorde-standard-dev-loop-context"}, {"extra": 1}):
            cases.append({**self.task(), **patch})
        for patch in ({"feature_path": "../outside.md"}, {"integration": "codex"}, {"request": ""}, {"constraints": [False]}):
            value = self.task()
            value["data"].update(patch)
            cases.append(value)
        for value in cases:
            agent = ScriptedAgent(self.author)
            result = run_operation("concorde-plan", CONFIGURATION, value, host_context=self.host(agent))
            self.assertEqual(result["status"], "blocked", result)
            self.assertEqual(agent.calls, [])
        agent = ScriptedAgent(self.author)
        changed = typed("concorde-operation-configuration", {"integration": "codex", "enforcement": "native"})
        result = run_operation("concorde-plan", changed, self.task(), host_context=self.host(agent))
        self.assertEqual(result["errors"][0]["code"], "configuration_mismatch")
        self.assertEqual(agent.calls, [])

    def test_source_change_during_context_blocks_author(self):
        def change(capability, value, root):
            if capability == "concorde-plan-context":
                with (root / FEATURE).open("a") as stream:
                    stream.write("\nUnexpected source change.\n")
        agent = ScriptedAgent(change)
        result = run_operation("concorde-plan", CONFIGURATION, self.task(), host_context=self.host(agent))
        self.assertEqual(result["errors"][0]["code"], "stale_reference", result)
        self.assertEqual(len(agent.calls), 1)

    def test_standard_loop_requires_an_existing_feature_before_launch(self):
        agent = ScriptedAgent()
        task = typed("concorde-standard-dev-loop-context", {
            "feature_path": "specs/example/features/002-planned.md",
            "request": "Create a new feature",
            "constraints": [],
        })

        result = run_operation(
            "concorde-standard-dev-loop",
            CONFIGURATION,
            task,
            host_context=self.host(agent, mode="describe-policy"),
        )

        self.assertEqual(result["status"], "blocked", result)
        self.assertEqual(result["errors"][0]["code"], "workspace_mismatch")
        self.assertEqual(result["errors"][0]["field"], "/input/data/feature_path")
        self.assertEqual(agent.calls, [])

    def test_standard_loop_runs_real_nested_graph_and_delivery_tools(self):
        def perform(capability, value, root):
            self.author(capability, value, root)
            if capability == "concorde-tasks":
                with (root / ATTEMPT / "tasks.md").open("a") as stream:
                    stream.write("- [ ] T002 Verify fixture change\n")
            if capability == "concorde-implement":
                write_complete_attempt(root / FEATURE, ("T001", "T002"))
            if capability == "concorde-deliver":
                proposed = materialize_delivery_proposal(root, propose_delivery(root, "feature.example.deliver"))
                self.assertEqual(proposed.status, "eligible", proposed.findings)
                applied = apply_delivery(root, proposed.result["proposal_path"])
                self.assertEqual(applied.status, "delivered", applied.findings)
        agent = ScriptedAgent(perform)
        host = self.host(agent)
        result = run_operation("concorde-standard-dev-loop", CONFIGURATION,
                               self.task("concorde-standard-dev-loop"), host_context=host)
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual([call["capability"] for call in agent.calls], [
            "concorde-specify", "concorde-plan-context", "concorde-plan-author", "concorde-tasks",
            "concorde-implement", "concorde-validate", "concorde-deliver"])
        self.assertFalse((self.root / ATTEMPT).exists())
        self.assertEqual(result["output"]["data"]["completed_capabilities"][1], "concorde-plan")
        tasks = next(call["input"] for call in agent.calls if call["capability"] == "concorde-tasks")
        self.assertEqual(tasks["data"]["feature_id"], "feature.example.deliver")
        self.assertEqual({Path(item["path"]).name for item in tasks["data"]["artifacts"]}, {"plan.md", "tasks.md"})
        self.assertEqual(len(host.evidence), 7)
        child = [item.completion for item in host.evidence if item.capability.startswith("concorde-plan-")]
        self.assertEqual(len({item.invocation_id for item in child}), 1)
        self.assertNotEqual(child[0].invocation_id, result["invocation_id"])
        self.assertNotEqual(child[0].launch_digest, child[1].launch_digest)

    def test_json_process_boundary_and_duplicate_key_rejection(self):
        script = REPOSITORY_ROOT / "operations/concorde-plan/operation.py"
        invocation = {"type_id": "concorde-operation-invocation", "schema_version": 1,
                      "operation_id": "concorde-plan", "mode": "describe-policy",
                      "configuration": CONFIGURATION, "input": self.task()}
        completed = subprocess.run([sys.executable, str(script)], cwd=self.root, input=json.dumps(invocation),
                                   capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "described")
        self.assertIsNone(result["output"])
        self.assertEqual(len(json.loads(completed.stderr)["policies"]), 2)
        malformed = subprocess.run([sys.executable, str(script)], cwd=self.root,
                                   input='{"mode":"execute","mode":"describe-policy"}',
                                   capture_output=True, text=True, check=False)
        self.assertEqual(malformed.returncode, 3)
        self.assertEqual(json.loads(malformed.stdout)["errors"][0]["code"], "invalid_json")

    def test_configuration_snapshot_is_inherited_after_project_settings_change(self):
        def perform(capability, value, root):
            self.author(capability, value, root)
            if capability == "concorde-plan-context":
                configure(root, typed("concorde-operation-configuration", {"integration": "codex", "enforcement": "native"}))
        agent = ScriptedAgent(perform)
        result = run_operation("concorde-plan", CONFIGURATION, self.task(), host_context=self.host(agent))
        self.assertEqual(result["status"], "succeeded", result)
        self.assertTrue(all(call["configuration"] == CONFIGURATION for call in agent.calls))
        self.assertEqual(self.host().configuration["data"]["integration"], "codex")

    def test_triage_status_selection_and_close_use_real_reflection_tools(self):
        create_triage_project(self.root, entry_count=2)
        configure(self.root)
        agent = ScriptedAgent()
        result = run_operation("concorde-reflections-triage", CONFIGURATION,
                               typed("concorde-reflections-triage-context", {"action": "status", "reflection_ids": []}),
                               host_context=self.host(agent))
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual(set(result["output"]["data"]["reflection_ids"]), {"R-001", "R-002"})
        self.assertEqual(agent.calls, [])
        write_reflection_collection(self.root, [reflection_entry("R-001", status="dismissed", Note="Maintainer dismissed the fixture"), reflection_entry("R-002")])
        closed = run_operation("concorde-reflections-triage", CONFIGURATION,
                               typed("concorde-reflections-triage-context", {"action": "close", "reflection_ids": ["R-001"]}),
                               host_context=self.host(agent))
        self.assertEqual(closed["status"], "succeeded", closed)
        self.assertEqual(closed["output"]["data"]["dispositions"], [{"reflection_id": "R-001", "outcome": "closed"}])
        self.assertTrue((self.root / ".concorde/reflections/pending/R-002.md").is_file())

    def test_triage_plan_route_maps_task_fields_and_rejects_mixed_selection(self):
        create_triage_project(self.root, entry_count=1)
        configure(self.root)
        initialize_git(self.root)
        def perform(capability, value, root):
            self.author(capability, value, root)
            if capability == "concorde-implement":
                write_complete_attempt(root / FEATURE)
        agent = ScriptedAgent(perform)
        task = typed("concorde-reflections-triage-context", {
            "action": "implement", "route": "plan", "reflection_ids": ["R-001"],
            "feature_path": FEATURE, "request": "Fix the selected reflection", "constraints": ["Keep scope local"],
        })
        result = run_operation("concorde-reflections-triage", CONFIGURATION, task, host_context=self.host(agent))
        self.assertEqual(result["status"], "succeeded", result)
        plan = next(call for call in agent.calls if call["capability"] == "concorde-plan-context")
        self.assertEqual(plan["input"]["type_id"], "concorde-plan-context")
        self.assertEqual(set(plan["input"]["data"]), {"feature_path", "request", "constraints", "source_artifacts"})
        self.assertEqual({item["id"] for item in plan["input"]["data"]["source_artifacts"]}, {"reflection:R-001", "reflection-plan:R-001"})
        self.assertEqual(plan["input"]["data"]["constraints"], ["Keep scope local"])
        self.assertEqual(result["output"]["data"]["reflection_ids"], ["R-001"])
        invalid = copy.deepcopy(task)
        invalid["data"]["reflection_ids"] = ["R-999"]
        other_agent = ScriptedAgent(perform)
        failed = run_operation("concorde-reflections-triage", CONFIGURATION, invalid, host_context=self.host(other_agent))
        self.assertEqual(failed["status"], "blocked", failed)
        self.assertEqual(other_agent.calls, [])

    def test_investigation_persists_verified_result_and_preserves_user_comments(self):
        create_triage_project(self.root, entry_count=1)
        write_reflection_collection(self.root, [reflection_entry("R-001", **{"User Comments": "Preserve this maintainer comment."})])
        configure(self.root)
        head = initialize_git(self.root)
        agent = ScriptedAgent()
        task = typed("concorde-reflections-triage-context", {
            "action": "investigate", "reflection_ids": ["R-001"], "feature_path": FEATURE, "request": "Investigate this record",
        })
        result = run_operation("concorde-reflections-triage", CONFIGURATION, task, host_context=self.host(agent))
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual(result["output"]["data"]["dispositions"], [{"reflection_id": "R-001", "outcome": "planned"}])
        document = (self.root / ".concorde/reflections/planned/R-001.md").read_text()
        self.assertIn("triage: complete", document)
        self.assertIn("Preserve this maintainer comment.", document)
        self.assertIn("status: open", document)
        plan = (self.root / ".concorde/reflections/plans/R-001.md").read_text()
        self.assertIn(head, plan)
        self.assertIn("## Verification", plan)

    def test_fast_loop_receives_resolution_refs_and_honors_plan_approval(self):
        create_triage_project(self.root, entry_count=1)
        configure(self.root)
        settings = self.root / ".concorde/reflections/config.json"
        config = json.loads(settings.read_text())
        settings.write_text(json.dumps({**config, "require_approval": True}))
        initialize_git(self.root)
        task = typed("concorde-reflections-triage-context", {
            "action": "implement", "route": "fast-loop", "reflection_ids": ["R-001"],
            "feature_path": FEATURE, "request": "Apply the bounded reflected fix",
        })
        blocked_agent = ScriptedAgent()
        blocked = run_operation("concorde-reflections-triage", CONFIGURATION, task, host_context=self.host(blocked_agent))
        self.assertEqual(blocked["status"], "blocked", blocked)
        self.assertIn("explicit approval", blocked["errors"][0]["message"])
        self.assertEqual(len(blocked_agent.calls), 1)
        approval = subprocess.run([sys.executable, str(REPOSITORY_ROOT / "scripts/reflections_queue.py"),
                                   "--root", str(self.root), "--allow-primary-worktree", "--set", "R-001", "status=approved"],
                                  capture_output=True, text=True)
        self.assertEqual(approval.returncode, 0, approval.stderr)
        def perform(capability, value, root):
            if capability == "concorde-fast-loop":
                self.assertEqual({item["id"] for item in value["data"]["source_artifacts"]},
                                 {"reflection:R-001", "reflection-plan:R-001"})
                (root / "src/example.py").write_text("VALUE = 2\n")
        agent = ScriptedAgent(perform)
        result = run_operation("concorde-reflections-triage", CONFIGURATION, task, host_context=self.host(agent))
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual([call["capability"] for call in agent.calls],
                         ["concorde-analyze", "concorde-fast-loop", "concorde-validate"])
        self.assertIn('status: implemented', (self.root / ".concorde/reflections/plans/R-001.md").read_text())
        self.assertFalse((self.root / ATTEMPT).exists())

    def test_merge_validates_integrated_commit_and_removes_only_selected_small_record(self):
        create_triage_project(self.root, entry_count=2)
        configure(self.root)
        head = initialize_git(self.root)
        write_plan(self.root, "R-001", status="merged", commit=head)
        task = typed("concorde-reflections-triage-context", {
            "action": "merge", "reflection_ids": ["R-001"], "feature_path": FEATURE,
            "request": "Clean up the verified integrated fix",
        })
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "record completed integration")
        agent = ScriptedAgent()
        result = run_operation("concorde-reflections-triage", CONFIGURATION, task, host_context=self.host(agent))
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual([call["capability"] for call in agent.calls], ["concorde-validate"])
        self.assertEqual(result["output"]["data"]["dispositions"], [{"reflection_id": "R-001", "outcome": "merged"}])
        self.assertFalse((self.root / ".concorde/reflections/plans/R-001.md").exists())
        self.assertTrue((self.root / ".concorde/reflections/pending/R-002.md").exists())

    def test_cross_feature_selection_and_supporting_refs_reject_before_launch(self):
        from concorde.capabilities.operation_data import artifact

        create_triage_project(self.root, entry_count=2)
        write_reflection_collection(self.root, [reflection_entry("R-001"),
                                               reflection_entry("R-002", feature="feature.example.other")])
        configure(self.root)
        for operation, task in (
            ("concorde-reflections-triage", typed("concorde-reflections-triage-context", {
                "action": "investigate", "reflection_ids": ["R-001", "R-002"],
                "feature_path": FEATURE, "request": "Investigate selected records"})),
            ("concorde-plan", typed("concorde-plan-context", {
                "feature_path": FEATURE, "request": "Plan the selected change",
                "source_artifacts": [artifact(self.root, "reflection:R-002", ".concorde/reflections/pending/R-002.md")]})),
        ):
            agent = ScriptedAgent()
            result = run_operation(operation, CONFIGURATION, task, host_context=self.host(agent))
            self.assertEqual(result["status"], "blocked", result)
            self.assertEqual(result["errors"][0]["code"], "workspace_mismatch")
            self.assertEqual(agent.calls, [])

    def test_investigation_failure_gates_stop_every_implementation_stage(self):
        scenarios = [
            {"observed_state": "not-reproduced", "route": "dismiss", "human_intervention": "required"},
            {"human_intervention": "required"},
            {"verified_commit": "0" * 40},
        ]
        for override in scenarios:
            with self.subTest(override=override), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                create_triage_project(root, entry_count=1)
                configure(root)
                initialize_git(root)
                def respond(capability, value, project):
                    if capability == "concorde-analyze":
                        report = investigation_result(value)
                        report["data"]["findings"][0].update(override)
                        return report
                    self.fail("a downstream capability ran after a rejected investigation")
                agent = ScriptedAgent(respond)
                task = typed("concorde-reflections-triage-context", {
                    "action": "implement", "route": "plan", "reflection_ids": ["R-001"],
                    "feature_path": FEATURE, "request": "Fix only a reproduced problem",
                })
                host = OperationHost(root, REPOSITORY_ROOT, executor=agent.executor, allow_primary_worktree=True)
                result = run_operation("concorde-reflections-triage", CONFIGURATION, task, host_context=host)
                self.assertEqual(result["status"], "blocked", result)
                self.assertEqual([call["capability"] for call in agent.calls], ["concorde-analyze"])
                self.assertFalse((root / ATTEMPT).exists())
                if "verified_commit" in override:
                    self.assertTrue((root / ".concorde/reflections/pending/R-001.md").is_file())
                    self.assertFalse((root / ".concorde/reflections/plans/R-001.md").exists())
                else:
                    self.assertTrue((root / ".concorde/reflections/needs-comments/R-001.md").is_file())


if __name__ == "__main__":
    unittest.main()
