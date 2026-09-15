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

from concorde.development import capability_host
from concorde.development.capability_host import Invocation
from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.harness.agent_model import agent_definition, resolve_agent
from concorde.harness.change_worktree import read_change
from concorde.harness.worker_executor import CapabilityExecutionError
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble, project
from tests.concorde.support.capability_json import configure


class AgentBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.task = {"target_id": "service.transfer", "task": "Implement the pure transfer contract"}

    def call_capability(self, name, data=None, *, double=None, mode="execute", configuration=CONFIGURATION):
        self.host = CapabilityHost(self.root, PACKAGE, executor=double.executor if double else None,
            allow_primary_worktree=True, mode=mode, routed_target=(data or self.task)["target_id"])
        return run_capability(name, configuration, typed(name + "-request", data or self.task),
                             host_context=self.host)

    def change(self, double):
        result = self.call_capability("concorde-plan", double=double)
        self.assertEqual("succeeded", result["status"], result)
        return {**self.task, "change_id": result["output"]["data"]["change_id"]}

    @verifies("scenario.harness.permission-compile")
    def test_narrowed_implementation_worker_write_authority_is_never_widened(self):
        real_load = capability_host.load_agent

        def narrowed(package_root, name):
            prompt = real_load(package_root, name)
            return replace(prompt, effects=replace(prompt.effects, writes=()))

        with patch.object(capability_host, "load_agent", side_effect=narrowed):
            result = self.call_capability("concorde-implement", mode="describe-policy")
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("permission_denied", result["errors"][0]["code"], result)

    @verifies("scenario.harness.permission-compile")
    def test_readonly_investigation_path_has_empty_write_paths(self):
        host = CapabilityHost(self.root, PACKAGE, mode="describe-policy", allow_primary_worktree=True)
        Invocation("concorde-implement", CONFIGURATION, self.task, host).stage(
            "concorde-implement", mode="investigation", readonly=True)
        policy = next(item for item in host.descriptions if item["phase"] == "implementation")
        self.assertEqual("concorde-investigator", policy["agent"])
        self.assertEqual([], policy["write_paths"])

    @verifies("scenario.harness.worker-selection")
    def test_describe_policy_descriptions_expose_the_worker_and_its_selection(self):
        result = self.call_capability("concorde-dev-loop", mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertTrue(self.host.descriptions)
        for policy in self.host.descriptions:
            agent = agent_definition(policy["agent"])
            self.assertEqual(agent.workspace, policy["workspace"])
            self.assertEqual(list(agent.tools), policy["tools"])
            self.assertEqual([child.name for child in agent.children], policy["children"])
            self.assertRegex(policy["agent_binding_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(policy["profile_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(policy["instructions_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(("openai-codex/gpt-6-astra", "medium", agent.timeout_seconds),
                             (policy["model"], policy["thinking"], policy["timeout_seconds"]))

    @verifies("scenario.harness.agent-bind")
    def test_description_agent_binding_digest_matches_resolve_agent(self):
        host = CapabilityHost(self.root, PACKAGE, mode="describe-policy", allow_primary_worktree=True)
        Invocation("concorde-context-solve", CONFIGURATION, self.task, host).stage("concorde-context-solve")
        policy = host.descriptions[0]
        expected = resolve_agent(PACKAGE, "context_assessor")
        self.assertEqual(expected.digest, policy["agent_binding_digest"])
        self.assertEqual(expected.instructions_digest, policy["instructions_digest"])
        self.assertEqual(expected.profile_digest, policy["profile_digest"])
        self.assertEqual("concorde-context-assessor", policy["agent"])
        self.assertEqual("capsule", policy["workspace"])
        self.assertEqual(expected.timeout_seconds, policy["timeout_seconds"])

    @verifies("scenario.harness.agent-bind", "scenario.harness.worker-selection")
    def test_the_pi_worker_receives_the_profile_timeout_by_default(self):
        double = ModelProcessDouble()
        self.call_capability("concorde-plan", double=double)
        planner_calls = [call for call in double.calls if call["stage"] == "plan"]
        self.assertTrue(planner_calls)
        self.assertEqual(agent_definition("planner").timeout_seconds, planner_calls[-1]["timeout"])

    @verifies("scenario.harness.worker-selection")
    def test_each_worker_and_child_launches_on_its_own_configured_selection(self):
        selection = typed("concorde-capability-configuration", {
            "model": "openai-codex/gpt-6-astra", "thinking": "medium", "workers": {
                "context_assessor": {"model": "anthropic/claude-sonnet-5", "timeout_seconds": 600},
                "planner": {"thinking": "high"},
                "planner/scout": {"model": "openai-codex/gpt-5.6-sol", "thinking": "low"}}})
        configure(self.root, selection)
        double = ModelProcessDouble()
        result = self.call_capability("concorde-plan", double=double, configuration=selection)
        self.assertEqual("succeeded", result["status"], result)
        launches = {call["agent"]: call["launch"] for call in double.calls}
        assessor, planner = launches["context_assessor"], launches["planner"]
        self.assertEqual(("anthropic/claude-sonnet-5", "medium", 600),
                         (assessor.model, assessor.thinking, assessor.timeout_seconds))
        self.assertEqual(("openai-codex/gpt-6-astra", "high", agent_definition("planner").timeout_seconds),
                         (planner.model, planner.thinking, planner.timeout_seconds))
        scout = next(child for child in planner.children if child.name == "scout")
        self.assertTrue(scout.definition.startswith("---\nmodel: openai-codex/gpt-5.6-sol\nthinking: low\n"))

    def _fail_implementation(self, double, outcome, message):
        real = double.executor

        def failing(invocation, **options):
            if invocation.stage == "implementation":
                raise CapabilityExecutionError(message, outcome=outcome)
            return real(invocation, **options)

        double.executor = failing

    @verifies("scenario.harness.execute-failure")
    def test_execution_limit_outcome_maps_to_execution_limit_and_records_change_status(self):
        double = ModelProcessDouble()
        task = self.change(double)
        result = self.call_capability("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        self._fail_implementation(double, "limit_exhausted", "the worker ran past its 10s timeout")
        result = self.call_capability("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_limit", result["errors"][0]["code"], result)
        self.assertEqual("limit_exhausted", read_change(self.root)["status"])

    @verifies("scenario.harness.execute-failure")
    def test_execution_cancelled_outcome_maps_to_execution_cancelled_and_records_change_status(self):
        double = ModelProcessDouble()
        task = self.change(double)
        result = self.call_capability("concorde-tasks", task, double=double)
        self.assertEqual("succeeded", result["status"], result)
        self._fail_implementation(double, "cancelled", "worker cancelled")
        result = self.call_capability("concorde-implement", task, double=double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_cancelled", result["errors"][0]["code"], result)
        self.assertEqual("cancelled", read_change(self.root)["status"])

    @verifies("scenario.harness.execute-failure")
    def test_dev_loop_composition_records_child_limit_status_on_the_change(self):
        double = ModelProcessDouble()
        self._fail_implementation(double, "limit_exhausted", "the worker ran past its 10s timeout")
        result = self.call_capability("concorde-dev-loop", double=double)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("child_blocked", result["errors"][0]["code"], result)
        self.assertEqual("limit_exhausted", read_change(self.root)["status"])


if __name__ == "__main__":
    unittest.main()
