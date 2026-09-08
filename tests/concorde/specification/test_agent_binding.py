"""P2: every launch binds an Agent definition and derives effective authority from it (A1, A4).

Reproduces the R-066 design-review probe (a narrowed implementation Agent's declared writes must
narrow effective write authority, never widen it) and exercises the new Agent-binding wiring:
describe-policy descriptions expose the bound Agent/Harness identity, the executor receives the
Agent's effective loop timeout, and a cancelled/limit-exhausted executor outcome is distinguishable
on both the wire (`execution_cancelled`/`execution_limit`) and the recorded change status.
"""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from concorde.host import capability_host
from concorde.host.agent_executor import CapabilityExecutionError
from concorde.host.agent_model import resolve_agent
from concorde.host.capability_service import CapabilityHost, run_capability
from concorde.host.capability_host import Invocation
from concorde.host.change_worktree import read_change
from concorde.host.harness import HARNESSES, SPEC_CAPSULE
from concorde.host.typed_data import typed
from .support import CONFIGURATION, PACKAGE, ModelProcessDouble, project


class AgentBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.task = {"target_id": "service.transfer", "task": "Implement the pure transfer contract"}

    def run_op(self, name, data=None, *, double=None, mode="execute"):
        self.host = CapabilityHost(self.root, PACKAGE, executor=double.executor if double else None,
            allow_primary_worktree=True, mode=mode, routed_target=(data or self.task)["target_id"])
        return run_capability(name, CONFIGURATION, typed(name + "-request", data or self.task),
                             host_context=self.host)

    def change(self, double):
        result = self.run_op("concorde-plan", double=double)
        self.assertEqual("succeeded", result["status"], result)
        return {**self.task, "change_id": result["output"]["data"]["change_id"]}

    # --- R-066: a declared-writes-narrowed implementation Agent must never receive write authority ---

    def test_narrowed_implementation_agent_write_authority_is_never_widened(self):
        from concorde.host.build import load_role_prompt as real_load

        def narrowed_prompt(package_root, role_name):
            prompt = real_load(package_root, role_name)
            return replace(prompt, effects=replace(prompt.effects, writes=()))

        with patch.object(capability_host, "load_role_prompt", side_effect=narrowed_prompt):
            result = self.run_op("concorde-implement", mode="describe-policy")
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("permission_denied", result["errors"][0]["code"], result)

    def test_readonly_investigation_path_has_empty_write_paths(self):
        host = CapabilityHost(self.root, PACKAGE, mode="describe-policy", allow_primary_worktree=True)
        Invocation("concorde-implement", CONFIGURATION, self.task, host).stage(
            "concorde-implement", readonly=True)
        policy = next(item for item in host.descriptions if item["phase"] == "implementation")
        self.assertEqual([], policy["write_paths"])

    # --- describe-policy descriptions expose the bound Agent/Harness identity ---

    def test_describe_policy_descriptions_expose_agent_and_harness_identity(self):
        result = self.run_op("concorde-dev-loop", mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertTrue(self.host.descriptions)
        for policy in self.host.descriptions:
            self.assertTrue(policy["agent"].startswith("concorde-"), policy)
            self.assertIn(policy["harness"], HARNESSES)
            self.assertRegex(policy["agent_binding_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(policy["instructions_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertGreater(policy["loop_timeout_seconds"], 0)

    def test_description_agent_binding_digest_matches_resolve_agent(self):
        host = CapabilityHost(self.root, PACKAGE, mode="describe-policy", allow_primary_worktree=True)
        Invocation("concorde-context-solve", CONFIGURATION, self.task, host).stage("concorde-context-solve")
        policy = host.descriptions[0]
        expected = resolve_agent(PACKAGE, "context_assessor")
        self.assertEqual(expected.digest, policy["agent_binding_digest"])
        self.assertEqual(expected.instructions_digest, policy["instructions_digest"])
        self.assertEqual("concorde-context-assessor", policy["agent"])
        self.assertEqual("spec-capsule", policy["harness"])
        self.assertEqual(expected.effective_loop.timeout_seconds, policy["loop_timeout_seconds"])

    # --- the executor receives the bound Agent's effective loop timeout ---

    def test_executor_receives_the_agents_effective_loop_timeout(self):
        double = ModelProcessDouble()
        self.addCleanup(double.runtime_directory.cleanup)
        self.run_op("concorde-plan", double=double)
        planner_calls = [call for call in double.calls if call["stage"] == "plan"]
        self.assertTrue(planner_calls)
        self.assertEqual(SPEC_CAPSULE.loop.timeout_seconds, planner_calls[-1]["timeout"])

    # --- executor cancellation/limit-exhaustion outcomes surface as distinct wire codes and change status ---

    def _fail_implementation(self, double, outcome, message):
        real = double.executor

        def failing(launch):
            if launch.stage == "implementation":
                raise CapabilityExecutionError(message, None, outcome=outcome)
            return real(launch)

        double.executor = failing

    def test_execution_limit_outcome_maps_to_execution_limit_and_records_change_status(self):
        double = ModelProcessDouble()
        self.addCleanup(double.runtime_directory.cleanup)
        task = self.change(double)
        result = self.run_op("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        self._fail_implementation(double, "limit_exhausted",
            "codex process exceeded the Harness loop limit of 10s")
        result = self.run_op("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_limit", result["errors"][0]["code"], result)
        self.assertEqual("limit_exhausted", read_change(self.root)["status"])

    def test_execution_cancelled_outcome_maps_to_execution_cancelled_and_records_change_status(self):
        double = ModelProcessDouble()
        self.addCleanup(double.runtime_directory.cleanup)
        task = self.change(double)
        result = self.run_op("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        self._fail_implementation(double, "cancelled", "agent process cancelled")
        result = self.run_op("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_cancelled", result["errors"][0]["code"], result)
        self.assertEqual("cancelled", read_change(self.root)["status"])

    def test_dev_loop_composition_records_child_limit_status_on_the_change(self):
        double = ModelProcessDouble()
        self.addCleanup(double.runtime_directory.cleanup)
        self._fail_implementation(double, "limit_exhausted",
            "codex process exceeded the Harness loop limit of 10s")
        result = self.run_op("concorde-dev-loop", double=double)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("child_blocked", result["errors"][0]["code"], result)
        self.assertEqual("limit_exhausted", read_change(self.root)["status"])


if __name__ == "__main__":
    unittest.main()
