"""Studio uses the real host and process enforcement with deterministic model responses."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from langgraph.checkpoint.memory import InMemorySaver

from concorde.harness.admission import run_operation
from concorde.spec.contracts import INTERNAL_OPERATIONS, PUBLIC_OPERATIONS
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from concorde.spec.wire_shapes import type_version
from tests.concorde.spec.support import (
    CONFIGURATION as CONFIGURATION,
)
from tests.concorde.spec.support import (
    PACKAGE,
    ModelProcessDouble,
    project,
)
from tests.concorde.support.legacy_graphs.studio import build_studio_graph
from tests.concorde.support.native_planning import OperationHost

EXPECTED_PUBLIC = (
    "concorde-context-solve",
    "concorde-plan",
    "concorde-tasks",
    "concorde-implement",
    "concorde-issues",
    "concorde-init",
    "concorde-configure",
    "concorde-validate",
    "concorde-deliver",
    "concorde-spec-review",
    "concorde-code-review",
)


def assert_public_inventory(case, names):
    names = list(names)
    case.assertEqual(11, len(names))
    case.assertEqual(len(names), len(set(names)))
    case.assertEqual(set(EXPECTED_PUBLIC), set(names))


class PublicInventoryTests(unittest.TestCase):
    # This tests the assertion helper itself, without inspecting an executable Graph.
    def test_inventory_assertion_rejects_missing_extra_and_duplicate_entries(self):
        assert_public_inventory(self, EXPECTED_PUBLIC)
        for names in (
            EXPECTED_PUBLIC[:-1],
            EXPECTED_PUBLIC + ("concorde-main",),
            EXPECTED_PUBLIC + (EXPECTED_PUBLIC[0],),
            EXPECTED_PUBLIC[:-1] + (EXPECTED_PUBLIC[0],),
            EXPECTED_PUBLIC[:-1] + ("concorde-main",),
        ):
            with self.subTest(names=names), self.assertRaises(AssertionError):
                assert_public_inventory(self, names)


def invocation(operation="concorde-issues", mode="execute", data=None):
    return {
        "type_id": "concorde-operation-invocation",
        "schema_version": 3,
        "operation_id": operation,
        "mode": mode,
        "configuration": None,
        "input": {
            "type_id": operation + "-request",
            "schema_version": type_version(operation + "-request"),
            "data": data
            if data is not None
            else {
                "target_id": "service.transfer",
                "task": "Explain transfer",
                **({"action": "list"} if operation == "concorde-issues" else {}),
            },
        },
    }


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

    def graph(self, operation="concorde-issues", executor=None):
        return build_studio_graph(
            operation, self.root, PACKAGE, executor=executor or self.double.executor
        )

    # Every supplied request is invalid, so this does not verify operation execution.
    @verifies("scenario.harness.graph-inspection")
    def test_inventory_and_all_entries_reject_invalid_input_at_the_shared_boundary(
        self,
    ):
        manifest = json.loads((PACKAGE / "generated/langgraph.json").read_text())
        assert_public_inventory(self, PUBLIC_OPERATIONS)
        self.assertEqual({"terminal-agent-operation"}, set(manifest["graphs"]))
        for operation in EXPECTED_PUBLIC:
            with self.subTest(operation=operation):
                value = invocation(operation, data={"unrecognized": True})
                graph = self.graph(operation)
                self.assertIn("invocation", graph.get_input_jsonschema()["properties"])
                actual = graph.invoke({"invocation": value})
                expected = run_operation(
                    operation,
                    None,
                    value["input"],
                    host_context=OperationHost(self.root, PACKAGE),
                )
                self.assertEqual(stable(expected), stable(actual["result"]))
                self.assertEqual("blocked", actual["result"]["status"])
        self.assertEqual([], self.double.calls)

    @verifies("scenario.harness.graph-inspection")
    def test_every_public_entry_enforces_envelope_configuration_and_workspace(self):
        for operation in EXPECTED_PUBLIC:
            graph = self.graph(operation)
            value = invocation(operation)
            cases = [
                (
                    {"invocation": {**value, "schema_version": 2}},
                    "unsupported_version",
                    [],
                ),
                (
                    {
                        "invocation": {
                            **value,
                            "configuration": {"integration": "codex"},
                        }
                    },
                    "unknown_type",
                    ["operation_started", "operation_finished"],
                ),
                (
                    {
                        "invocation": value,
                        "expected_workspace": {
                            "project_root": "/other",
                            "package_root": str(PACKAGE),
                        },
                    },
                    "workspace_mismatch",
                    [],
                ),
            ]
            # Configuration is admitted by the real Host after the envelope check.
            for supplied, error_code, events in cases:
                with self.subTest(operation=operation, supplied=supplied):
                    result = graph.invoke(supplied)
                    self.assertEqual("blocked", result["result"]["status"])
                    self.assertIsNone(result["result"]["output"])
                    self.assertEqual(error_code, result["result"]["errors"][0]["code"])
                    self.assertEqual(
                        events, [event["event"] for event in result["events"]]
                    )
        self.assertEqual([], self.double.calls)

    @verifies("scenario.harness.execute-operation")
    def test_real_context_execution_matches_local_json(self):
        value = invocation()
        actual = self.graph().invoke({"invocation": value})
        expected = run_operation(
            value["operation_id"],
            None,
            value["input"],
            host_context=OperationHost(self.root, PACKAGE),
        )
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        self.assertEqual(
            value["operation_id"] + "-response", actual["result"]["output"]["type_id"]
        )
        self.assertEqual(stable(expected), stable(actual["result"]))
        self.assertEqual(
            ["operation_started", "operation_finished"],
            [event["event"] for event in actual["events"]],
        )

    def test_streamed_agent_stages_use_native_executor_and_fresh_invocations(self):
        graph = self.graph("concorde-context-solve")
        value = invocation(
            "concorde-context-solve",
            data={"target_id": "service.transfer", "task": "Explain transfer"},
        )
        from typing import Any

        chunks: list[Any] = list(
            graph.stream({"invocation": value}, stream_mode=["custom", "updates"])
        )
        custom = [data for mode, data in chunks if mode == "custom"]
        actual = [
            data["concorde-context-solve"]
            for mode, data in chunks
            if mode == "updates" and "concorde-context-solve" in data
        ][0]
        self.assertEqual("succeeded", actual["result"]["status"], actual)
        self.assertEqual(custom, actual["events"])
        started = [e for e in custom if e["event"] == "agent_started"]
        self.assertEqual(["context-solve"], [e["stage"] for e in started])
        self.assertEqual(1, len({e["invocation_id"] for e in started}))
        self.assertTrue(
            all(
                "context.json" in p["read_paths"]
                and all(
                    path == "context.json"
                    or path.startswith(("specs/", ".concorde/protocol/"))
                    for path in p["read_paths"]
                )
                for p in actual["policies"]
            )
        )
        second = graph.invoke({"invocation": value})
        self.assertEqual(len(actual["events"]), len(second["events"]))
        self.assertNotEqual(
            actual["result"]["invocation_id"], second["result"]["invocation_id"]
        )

    def test_describe_policy_does_not_start_agents(self):
        actual = self.graph("concorde-plan").invoke(
            {"invocation": invocation("concorde-plan", "describe-policy")}
        )
        self.assertEqual("described", actual["result"]["status"], actual)
        self.assertTrue(actual["policies"])
        self.assertEqual([], self.double.calls)
        self.assertFalse(any(e["event"].startswith("agent_") for e in actual["events"]))

    def test_reused_thread_clears_results_and_rechecks_resume_workspace(self):
        graph = self.graph()
        graph.checkpointer = InMemorySaver()
        from langchain_core.runnables import RunnableConfig

        config: RunnableConfig = {"configurable": {"thread_id": "repeat"}}
        first = graph.invoke({"invocation": invocation()}, config)
        rejected = graph.invoke({"invocation": {}, "expected_workspace": None}, config)
        self.assertEqual("blocked", rejected["result"]["status"])
        self.assertEqual([], rejected["events"])
        self.assertIsNone(rejected["result"]["output"])
        graph.invoke(
            {"invocation": invocation()}, config, interrupt_before=["concorde-issues"]
        )
        graph.update_state(
            config,
            {
                "expected_workspace": {
                    "project_root": "/other",
                    "package_root": str(PACKAGE),
                }
            },
        )
        resumed = graph.invoke(None, config)
        self.assertEqual("workspace_mismatch", resumed["result"]["errors"][0]["code"])
        self.assertNotEqual(
            first["result"]["invocation_id"], resumed["result"]["invocation_id"]
        )

    def test_cross_workspace_and_invalid_envelope_never_construct_execution_host(self):
        graph = self.graph()
        cases = [
            {
                "invocation": invocation(),
                "expected_workspace": {
                    "project_root": "/other",
                    "package_root": str(PACKAGE),
                },
            },
            {
                "invocation": invocation(),
                "expected_workspace": {
                    "project_root": str(self.root),
                    "package_root": "/other",
                },
            },
            {"invocation": {}},
            {"invocation": {**invocation(), "schema_version": True}},
            {"invocation": {**invocation(), "permissions": "all"}},
            {"invocation": invocation("concorde-plan")},
            {"invocation": {**invocation(), "input": "x" * (1024 * 1024)}},
        ]
        with patch("tests.concorde.support.legacy_graphs.studio.OperationHost") as host:
            for value in cases:
                with self.subTest(value=str(value)[:160]):
                    actual = graph.invoke(value)
                    self.assertEqual("blocked", actual["result"]["status"])
                    self.assertEqual([], actual["events"])
            host.assert_not_called()

    def test_utf8_input_limit_matches_cli_without_ascii_escape_expansion(self):
        value = invocation(
            "concorde-context-solve",
            data={"target_id": "service.transfer", "task": "测" * 180000},
        )
        self.assertLess(
            len(json.dumps(value, ensure_ascii=False).encode()), 1024 * 1024
        )
        graph = self.graph("concorde-context-solve")
        state = graph.invoke(
            {"invocation": value}, interrupt_before=["concorde-context-solve"]
        )
        self.assertIsNone(state["result"])
        self.assertEqual([], self.double.calls)

    def test_configuration_and_agent_completion_cannot_bypass_authority(self):
        value = invocation(
            "concorde-context-solve",
            data={"target_id": "service.transfer", "task": "Explain transfer"},
        )
        value["configuration"] = typed(
            "concorde-operation-configuration",
            {"model": "openai-codex/gpt-6-astra", "thinking": "high"},
        )
        actual = self.graph("concorde-context-solve").invoke({"invocation": value})
        self.assertEqual(
            "configuration_mismatch", actual["result"]["errors"][0]["code"]
        )
        self.assertEqual([], self.double.calls)
        value["configuration"] = None
        actual = self.graph("concorde-context-solve", Mock(return_value={})).invoke(
            {"invocation": value}
        )
        self.assertEqual("invalid_completion", actual["result"]["errors"][0]["code"])

    def test_agent_failure_is_a_failed_result_with_final_event(self):
        actual = self.graph(
            "concorde-context-solve", Mock(side_effect=RuntimeError("process broke"))
        ).invoke(
            {
                "invocation": invocation(
                    "concorde-context-solve",
                    data={"target_id": "service.transfer", "task": "Explain transfer"},
                )
            }
        )
        self.assertEqual("failed", actual["result"]["status"])
        self.assertEqual("execution_failed", actual["result"]["errors"][0]["code"])
        self.assertEqual(
            [
                "operation_started",
                "agent_started",
                "agent_failed",
                "operation_finished",
            ],
            [e["event"] for e in actual["events"]],
        )

    def test_observer_failure_does_not_change_operation_result(self):
        value = invocation()
        result = run_operation(
            "concorde-issues",
            None,
            value["input"],
            host_context=OperationHost(
                self.root,
                PACKAGE,
                observer=Mock(side_effect=RuntimeError("disconnected")),
            ),
        )
        self.assertEqual("succeeded", result["status"])

    def test_source_studio_delivery_retains_its_worktree(self):
        from tests.concorde.harness.test_worktree_lifecycle import (
            WorktreeLifecycleTests,
        )

        fixture = WorktreeLifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        change_id = fixture.ready()
        result = build_studio_graph(
            "concorde-deliver", fixture.change, PACKAGE, executor=self.double.executor
        ).invoke(
            {
                "invocation": invocation(
                    "concorde-deliver",
                    data={"change_id": change_id, "keep_worktree": True},
                )
            }
        )
        self.assertEqual("succeeded", result["result"]["status"], result)
        self.assertIn("retained", result["result"]["output"]["data"]["answer"])
        self.assertTrue(fixture.change.exists())
        self.assertEqual([], self.double.calls)

    def test_internal_stages_cannot_be_published_as_direct_studio_entries(self):
        for operation in INTERNAL_OPERATIONS:
            with (
                self.subTest(operation=operation),
                self.assertRaisesRegex(ValueError, "public operation"),
            ):
                build_studio_graph(operation, self.root, PACKAGE)

    def test_symlink_root_is_rejected(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(Exception, "symlinks"):
            build_studio_graph("concorde-issues", alias, PACKAGE)
