"""Every launch binds a worker definition and derives effective authority from it (A1, A4).

A narrowed implementation worker's declared writes must narrow effective write authority, never
widen it; describe-policy descriptions expose the bound worker and its model selection; the Pi
worker receives its selected model, thinking level and timeout; and a cancelled or limit-exhausted
executor outcome is distinguishable on the wire (`execution_cancelled`/`execution_limit`) and in the
recorded change status.
"""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from concorde.harness import invocation
from concorde.harness.invocation import Invocation
from concorde.harness.host import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.change_worktree import read_change
from concorde.harness.pi_worker import WorkerExecutionError
from concorde.harness.worker_executor import OperationExecutionError
from concorde.harness.worker_profile import resolve_worker, worker_profile
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    ModelProcessDouble,
    project,
)
from tests.concorde.support.operation_json import configure


class AgentBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the pure transfer contract",
        }

    def call_operation(
        self,
        name,
        data=None,
        *,
        double=None,
        mode="execute",
        configuration=CONFIGURATION,
    ):
        self.host = OperationHost(
            self.root,
            PACKAGE,
            executor=double.executor if double else None,
            allow_primary_worktree=True,
            mode=mode,
            routed_target=(data or self.task)["target_id"],
        )
        return run_operation(
            name,
            configuration,
            typed(name + "-request", data or self.task),
            host_context=self.host,
        )

    def change(self, double):
        result = self.call_operation("concorde-plan", double=double)
        self.assertEqual("succeeded", result["status"], result)
        return {**self.task, "change_id": result["output"]["data"]["change_id"]}

    @verifies("scenario.harness.permission-compile")
    def test_narrowed_implementation_worker_write_authority_is_never_widened(self):
        real_load = invocation.load_model_instructions

        def narrowed(package_root, name):
            prompt = real_load(package_root, name)
            return replace(prompt, effects=replace(prompt.effects, writes=()))

        with patch.object(invocation, "load_model_instructions", side_effect=narrowed):
            result = self.call_operation("concorde-implement", mode="describe-policy")
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("permission_denied", result["errors"][0]["code"], result)

    @verifies("scenario.harness.permission-compile")
    def test_issue_solver_is_spec_only_with_empty_write_paths(self):
        host = OperationHost(
            self.root, PACKAGE, mode="describe-policy", allow_primary_worktree=True
        )
        Invocation("concorde-issues", CONFIGURATION, self.task, host).stage(
            "concorde-issues"
        )
        policy = next(
            item for item in host.descriptions if item["phase"] == "issue-solve"
        )
        self.assertEqual("concorde-issue-solver", policy["agent"])
        self.assertEqual("capsule", policy["workspace"])
        self.assertEqual([], policy["write_paths"])
        self.assertFalse(any(path.startswith("app/") for path in policy["read_paths"]))

    @verifies("scenario.harness.worker-selection")
    def test_describe_policy_descriptions_expose_the_worker_and_its_selection(self):
        result = self.call_operation("concorde-dev-loop", mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertTrue(self.host.descriptions)
        for policy in self.host.descriptions:
            agent = worker_profile(policy["agent"])
            self.assertEqual(agent.workspace, policy["workspace"])
            self.assertEqual(list(agent.tools), policy["tools"])
            self.assertEqual(
                [child.name for child in agent.children], policy["children"]
            )
            self.assertRegex(policy["agent_binding_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(policy["profile_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(policy["instructions_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(
                ("openai-codex/gpt-6-astra", "medium", agent.timeout_seconds),
                (policy["model"], policy["thinking"], policy["timeout_seconds"]),
            )

    @verifies("scenario.harness.agent-bind")
    def test_description_agent_binding_digest_matches_resolve_agent(self):
        host = OperationHost(
            self.root, PACKAGE, mode="describe-policy", allow_primary_worktree=True
        )
        Invocation("concorde-context-solve", CONFIGURATION, self.task, host).stage(
            "concorde-context-solve"
        )
        policy = host.descriptions[0]
        expected = resolve_worker(PACKAGE, "context_assessor")
        self.assertEqual(expected.digest, policy["agent_binding_digest"])
        self.assertEqual(expected.instructions_digest, policy["instructions_digest"])
        self.assertEqual(expected.profile_digest, policy["profile_digest"])
        self.assertEqual("concorde-context-assessor", policy["agent"])
        self.assertEqual("capsule", policy["workspace"])
        self.assertEqual(expected.timeout_seconds, policy["timeout_seconds"])

    @verifies("scenario.harness.agent-bind", "scenario.harness.worker-selection")
    def test_the_pi_worker_receives_the_profile_timeout_by_default(self):
        double = ModelProcessDouble()
        self.call_operation("concorde-plan", double=double)
        planner_calls = [call for call in double.calls if call["stage"] == "plan"]
        self.assertTrue(planner_calls)
        self.assertEqual(
            worker_profile("planner").timeout_seconds, planner_calls[-1]["timeout"]
        )

    @verifies("scenario.harness.worker-selection")
    def test_each_worker_and_child_launches_on_its_own_configured_selection(self):
        selection = typed(
            "concorde-operation-configuration",
            {
                "model": "openai-codex/gpt-6-astra",
                "thinking": "medium",
                "workers": {
                    "context_assessor": {
                        "model": "anthropic/claude-sonnet-5",
                        "timeout_seconds": 600,
                    },
                    "planner": {"thinking": "high"},
                    "planner/scout": {
                        "model": "openai-codex/gpt-5.6-sol",
                        "thinking": "low",
                    },
                },
            },
        )
        configure(self.root, selection)
        double = ModelProcessDouble()
        result = self.call_operation(
            "concorde-plan", double=double, configuration=selection
        )
        self.assertEqual("succeeded", result["status"], result)
        launches = {call["agent"]: call["launch"] for call in double.calls}
        assessor, planner = launches["context_assessor"], launches["planner"]
        self.assertEqual(
            ("anthropic/claude-sonnet-5", "medium", 600),
            (assessor.model, assessor.thinking, assessor.timeout_seconds),
        )
        self.assertEqual(
            (
                "openai-codex/gpt-6-astra",
                "high",
                worker_profile("planner").timeout_seconds,
            ),
            (planner.model, planner.thinking, planner.timeout_seconds),
        )
        scout = next(child for child in planner.children if child.name == "scout")
        self.assertTrue(
            scout.definition.startswith(
                "---\nmodel: openai-codex/gpt-5.6-sol\nthinking: low\n"
            )
        )

    def _fail_implementation(self, double, outcome, message):
        real = double.executor

        def failing(invocation, **options):
            if invocation.stage == "implementation":
                raise OperationExecutionError(message, outcome=outcome)
            return real(invocation, **options)

        double.executor = failing

    @verifies("scenario.harness.execute-failure")
    def test_execution_limit_outcome_maps_to_execution_limit_and_records_change_status(
        self,
    ):
        double = ModelProcessDouble()
        task = self.change(double)
        result = self.call_operation("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        self._fail_implementation(
            double, "limit_exhausted", "the worker ran past its 10s timeout"
        )
        result = self.call_operation("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_limit", result["errors"][0]["code"], result)
        self.assertEqual(
            "limit_exhausted", read_change(self.root, required=True)["status"]
        )

    @verifies("scenario.harness.execute-failure")
    def test_execution_cancelled_outcome_maps_to_execution_cancelled_and_records_change_status(
        self,
    ):
        double = ModelProcessDouble()
        task = self.change(double)
        result = self.call_operation("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        self._fail_implementation(double, "cancelled", "worker cancelled")
        result = self.call_operation("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_cancelled", result["errors"][0]["code"], result)
        self.assertEqual("cancelled", read_change(self.root, required=True)["status"])

    @verifies("scenario.implementation.failed-execution")
    def test_authorized_edits_survive_a_failed_execution_and_the_retry_re_admits_the_same_artifacts(
        self,
    ):
        double = ModelProcessDouble()
        task = self.change(double)
        result = self.call_operation("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        code = self.root / "app/transfer.py"
        planned = code.read_bytes()

        def fail_after_the_authorized_write(stage, snapshot, data, cwd):
            # The double has already written the worker's authorized code edit when it reaches here.
            if stage == "implementation":
                raise WorkerExecutionError(
                    "the worker ran past its 10s timeout", outcome="limit_exhausted"
                )

        double.callback = fail_after_the_authorized_write
        result = self.call_operation("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_limit", result["errors"][0]["code"], result)
        self.assertNotEqual(planned, code.read_bytes())
        self.assertIn(b"raise ValueError", code.read_bytes())
        change = read_change(self.root, required=True)
        self.assertEqual("limit_exhausted", change["status"])
        recorded = change["targets"]["service.transfer"]
        self.assertEqual(
            ("tasks", None, [False]),
            (
                recorded["phase"],
                recorded["implementation_digest"],
                [item["complete"] for item in recorded["tasks"]],
            ),
        )
        self.assertNotIn("concorde-implement", recorded["completed_operations"])
        retry = ModelProcessDouble()
        result = self.call_operation("concorde-implement", task, double=retry)
        self.assertEqual("succeeded", result["status"], result)
        first, second = (
            next(call for call in calls if call["stage"] == "implementation")
            for calls in (double.calls, retry.calls)
        )
        self.assertEqual(
            first["snapshot"]["stage_inputs"], second["snapshot"]["stage_inputs"]
        )
        self.assertEqual(first["launch"].write_paths, second["launch"].write_paths)
        # A fresh invocation with its own frozen context file and no other added grant.
        self.assertNotEqual(
            first["snapshot"]["context_id"], second["snapshot"]["context_id"]
        )
        granted = [
            [
                path
                for path in sorted(call["launch"].read_paths)
                if not path.startswith(".concorde/runs/")
            ]
            for call in (first, second)
        ]
        self.assertEqual(granted[0], granted[1])

    @verifies("scenario.harness.execute-failure")
    def test_dev_loop_composition_records_child_limit_status_on_the_change(self):
        double = ModelProcessDouble()
        self._fail_implementation(
            double, "limit_exhausted", "the worker ran past its 10s timeout"
        )
        result = self.call_operation("concorde-dev-loop", double=double)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("child_blocked", result["errors"][0]["code"], result)
        self.assertEqual(
            "limit_exhausted", read_change(self.root, required=True)["status"]
        )


if __name__ == "__main__":
    unittest.main()
