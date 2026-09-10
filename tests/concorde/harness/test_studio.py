"""Studio uses the real host and process enforcement with deterministic model responses."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from langgraph.checkpoint.memory import InMemorySaver
from concorde.spec.typed_data import typed
from concorde.spec.contracts import SKILL_NAMES, STAGE_CAPABILITIES
from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.harness.studio import build_studio_graph
from concorde.spec.verification import verifies
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble, project


def invocation(capability="concorde-reflections-triage", mode="execute", data=None):
    return {"type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": capability, "mode": mode, "configuration": None,
            "input": {"type_id": capability + "-request", "schema_version": 1, "data":
                      data if data is not None else {"target_id": "service.transfer", "task": "Explain transfer",
                          **({"action": "status", "reflection_ids": []} if capability == "concorde-reflections-triage" else {})}}}


def stable(value):
    # Host runs intentionally allocate different invocation/capsule identities.
    value = copy.deepcopy(value)
    value.pop("invocation_id", None)
    return value


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project(self.root)
        self.double = ModelProcessDouble()
        self.addCleanup(self.double.runtime_directory.cleanup)

    def graph(self, capability="concorde-reflections-triage", executor=None):
        return build_studio_graph(capability, self.root, PACKAGE,
                                  executor=executor or self.double.executor)

    def test_inventory_and_all_entries_execute_the_shared_boundary(self):
        manifest = json.loads((PACKAGE / "generated/langgraph.json").read_text())
        self.assertEqual(set(SKILL_NAMES), set(manifest["graphs"]))
        self.assertEqual(7, len(manifest["graphs"]))
        for capability in SKILL_NAMES:
            with self.subTest(capability=capability):
                value = invocation(capability, data={"unrecognized": True})
                actual = self.graph(capability).invoke({"invocation": value})
                expected = run_capability(capability, None, value["input"],
                                         host_context=CapabilityHost(self.root, PACKAGE))
                self.assertEqual(stable(expected), stable(actual["result"]))
                self.assertEqual("blocked", actual["result"]["status"])
        self.assertEqual([], self.double.calls)

    def test_real_context_execution_matches_local_json(self):
        value = invocation()
        actual = self.graph().invoke({"invocation": value})
        expected = run_capability(value["capability_id"], None, value["input"],
                                 host_context=CapabilityHost(self.root, PACKAGE))
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        self.assertEqual(stable(expected), stable(actual["result"]))
        self.assertEqual(["capability_started", "capability_finished"],
                         [event["event"] for event in actual["events"]])

    def test_streamed_agent_stages_use_native_executor_and_fresh_invocations(self):
        graph = self.graph("concorde-main")
        value = invocation("concorde-main", data={"task": "Explain transfer"})
        chunks = list(graph.stream({"invocation": value}, stream_mode=["custom", "updates"]))
        custom = [data for mode, data in chunks if mode == "custom"]
        actual = [data["concorde-main"] for mode, data in chunks
                  if mode == "updates" and "concorde-main" in data][0]
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        self.assertEqual(custom, actual["events"])
        started = [e for e in custom if e["event"] == "agent_started"]
        self.assertEqual(["route", "route"], [e["stage"] for e in started])
        self.assertEqual(2, len({e["invocation_id"] for e in started}))
        self.assertTrue(all(p["read_paths"] == ["context.json"] for p in actual["policies"]))
        second = graph.invoke({"invocation": value})
        self.assertEqual(len(actual["events"]), len(second["events"]))
        self.assertNotEqual(actual["result"]["invocation_id"], second["result"]["invocation_id"])

    def test_describe_policy_does_not_start_agents(self):
        actual = self.graph("concorde-dev-loop").invoke(
            {"invocation": invocation("concorde-dev-loop", "describe-policy")})
        self.assertEqual("described", actual["result"]["status"], actual)
        self.assertTrue(actual["policies"])
        self.assertEqual([], self.double.calls)
        self.assertFalse(any(e["event"].startswith("agent_") for e in actual["events"]))

    def test_reused_thread_clears_results_and_rechecks_resume_workspace(self):
        graph = self.graph()
        graph.checkpointer = InMemorySaver()
        config = {"configurable": {"thread_id": "repeat"}}
        first = graph.invoke({"invocation": invocation()}, config)
        rejected = graph.invoke({"invocation": {}, "expected_workspace": None}, config)
        self.assertEqual("blocked", rejected["result"]["status"])
        self.assertEqual([], rejected["events"])
        self.assertIsNone(rejected["result"]["output"])
        graph.invoke({"invocation": invocation()}, config, interrupt_before=["concorde-reflections-triage"])
        graph.update_state(config, {"expected_workspace": {"project_root": "/other", "package_root": str(PACKAGE)}})
        resumed = graph.invoke(None, config)
        self.assertEqual("workspace_mismatch", resumed["result"]["errors"][0]["code"])
        self.assertNotEqual(first["result"]["invocation_id"], resumed["result"]["invocation_id"])

    def test_cross_workspace_and_invalid_envelope_never_construct_execution_host(self):
        graph = self.graph()
        cases = [
            {"invocation": invocation(), "expected_workspace": {"project_root": "/other", "package_root": str(PACKAGE)}},
            {"invocation": invocation(), "expected_workspace": {"project_root": str(self.root), "package_root": "/other"}},
            {"invocation": {}},
            {"invocation": {**invocation(), "schema_version": True}},
            {"invocation": {**invocation(), "permissions": "all"}},
            {"invocation": invocation("concorde-plan")},
            {"invocation": {**invocation(), "input": "x" * (1024 * 1024)}},
        ]
        with patch("concorde.harness.studio.CapabilityHost") as host:
            for value in cases:
                with self.subTest(value=str(value)[:160]):
                    actual = graph.invoke(value)
                    self.assertEqual("blocked", actual["result"]["status"])
                    self.assertEqual([], actual["events"])
            host.assert_not_called()

    def test_utf8_input_limit_matches_cli_without_ascii_escape_expansion(self):
        value = invocation("concorde-main", data={"task": "测" * 180000})
        self.assertLess(len(json.dumps(value, ensure_ascii=False).encode()), 1024 * 1024)
        graph = self.graph("concorde-main")
        state = graph.invoke({"invocation": value}, interrupt_before=["concorde-main"])
        self.assertIsNone(state["result"])
        self.assertEqual([], self.double.calls)

    def test_configuration_and_agent_completion_cannot_bypass_authority(self):
        value = invocation("concorde-main", data={"task": "Explain transfer"})
        value["configuration"] = typed("concorde-capability-configuration",
                                      {"integration": "codex", "enforcement": "native"})
        actual = self.graph("concorde-main").invoke({"invocation": value})
        self.assertEqual("configuration_mismatch", actual["result"]["errors"][0]["code"])
        self.assertEqual([], self.double.calls)
        value["configuration"] = None
        actual = self.graph("concorde-main", Mock(return_value={})).invoke({"invocation": value})
        self.assertEqual("invalid_completion", actual["result"]["errors"][0]["code"])

    def test_agent_failure_is_a_failed_result_with_final_event(self):
        actual = self.graph("concorde-main", Mock(side_effect=RuntimeError("process broke"))).invoke(
            {"invocation": invocation("concorde-main", data={"task": "Explain transfer"})})
        self.assertEqual("failed", actual["result"]["status"])
        self.assertEqual("execution_failed", actual["result"]["errors"][0]["code"])
        self.assertEqual(["capability_started", "agent_started", "agent_failed", "capability_finished"],
                         [e["event"] for e in actual["events"]])

    def test_observer_failure_does_not_change_operation_result(self):
        value = invocation()
        result = run_capability("concorde-reflections-triage", None, value["input"], host_context=CapabilityHost(
            self.root, PACKAGE, observer=Mock(side_effect=RuntimeError("disconnected"))))
        self.assertEqual("succeeded", result["status"])

    @verifies("scenario.harness.recursive-delegate")
    def test_loop_emits_child_operations_and_deterministic_phases(self):
        from tests.concorde.harness.test_worktree_lifecycle import WorktreeLifecycleTests
        fixture = WorktreeLifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        actual = build_studio_graph("concorde-dev-loop", fixture.change, PACKAGE,
                                   executor=self.double.executor).invoke({"invocation": invocation(
            "concorde-dev-loop", data={**fixture.task, "specify": False, "run_reviews": False})})
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        stages = [e["stage"] for e in actual["events"] if e["event"] == "stage_finished"]
        self.assertIn("validate", stages)
        self.assertEqual("ready", stages[-1])
        self.assertTrue(any(e["event"] == "capability_started" and e["depth"] == 2
                            for e in actual["events"]))
        self.assertTrue(any(e.get("stage") == "implementation" and e["event"] == "agent_finished"
                            for e in actual["events"]))

    def test_source_studio_delivery_retains_its_worktree(self):
        from tests.concorde.harness.test_worktree_lifecycle import WorktreeLifecycleTests
        fixture = WorktreeLifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        change_id = fixture.ready()
        result = build_studio_graph("concorde-deliver", fixture.change, PACKAGE,
                                    executor=self.double.executor).invoke({"invocation": invocation(
            "concorde-deliver", data={"change_id": change_id, "keep_worktree": True})})
        self.assertEqual("succeeded", result["result"]["status"], result)
        self.assertIn("retained", result["result"]["output"]["data"]["answer"])
        self.assertTrue(fixture.change.exists())
        self.assertEqual([], self.double.calls)

    def test_internal_stages_cannot_be_published_as_direct_studio_entries(self):
        for capability in STAGE_CAPABILITIES:
            with self.subTest(capability=capability), self.assertRaisesRegex(ValueError, "public capability"):
                build_studio_graph(capability, self.root, PACKAGE)

    def test_symlink_root_is_rejected(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(Exception, "symlinks"):
            build_studio_graph("concorde-reflections-triage", alias, PACKAGE)
