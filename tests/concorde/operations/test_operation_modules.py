"""One executable Operation inventory, one USES relation, and State-based nodes."""

from __future__ import annotations

import importlib
import unittest
from unittest.mock import patch

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from concorde.harness.operation_node import OperationNode
from concorde.harness.operation_state import OperationRuntimeContext, StateContract
from concorde.harness.worker_profile import WorkerProfile
from concorde.spec.contracts import (
    COMPOSITE_OPERATIONS,
    DETERMINISTIC_OPERATIONS,
    INTERNAL_OPERATIONS,
    OPERATION_NAMES,
    PUBLIC_OPERATIONS,
    contracts,
    dependencies,
    load_operation_inventory,
    schemas,
)
from concorde.spec.typed_data import TypedDataError, typed
from concorde.spec.verification import verifies

operations = load_operation_inventory()


def _modules():
    return {
        name: importlib.import_module(f"operations.{name}")
        for name in operations.OPERATIONS
    }


class OperationModuleContractTests(unittest.TestCase):
    @verifies("scenario.harness.operation-state")
    def test_one_inventory_includes_model_code_and_composed_nodes(self):
        modules = _modules()
        self.assertEqual(18, len(modules))
        self.assertEqual(
            set(OPERATION_NAMES), {m.EXTERNAL_NAME for m in modules.values()}
        )
        self.assertEqual(len(operations.OPERATIONS), len(set(operations.OPERATIONS)))
        self.assertEqual(
            7, sum(isinstance(m.PROFILE, WorkerProfile) for m in modules.values())
        )
        self.assertEqual(7, len(operations.AGENTS))
        for name, module in modules.items():
            self.assertEqual(module.EXTERNAL_NAME, operations.external_name(name))
            self.assertIn(module.KIND, {"agent", "agent-entry", "workflow", "host"})
            if module.PROFILE:
                self.assertEqual(module.KIND, "agent")
                self.assertFalse(hasattr(module, "run"))
                self.assertFalse(hasattr(module, "STATE"))
                node = OperationNode(name)
                self.assertEqual(
                    {"__start__", "terminal_agent", "__end__"},
                    set(node.graph().get_graph().nodes),
                )
            else:
                self.assertIsInstance(module.STATE, StateContract)
                self.assertTrue(callable(module.run))

    def test_properties_and_transport_contracts_are_independent(self):
        exported = schemas()
        for module in _modules().values():
            name = module.EXTERNAL_NAME
            self.assertIs(type(module.PUBLIC), bool)
            self.assertIs(type(module.DETERMINISTIC), bool)
            self.assertIn(module.CONTEXT_SELECTION, {"bound", "none"})
            self.assertEqual(module.PUBLIC, name in PUBLIC_OPERATIONS)
            self.assertEqual(not module.PUBLIC, name in INTERNAL_OPERATIONS)
            self.assertEqual(module.DETERMINISTIC, name in DETERMINISTIC_OPERATIONS)
            if hasattr(module, "REQUEST"):
                self.assertEqual(module.REQUEST, exported[f"{name}-request"])
                self.assertEqual(module.RESPONSE, exported[f"{name}-response"])
                self.assertIsNone(module.STATE.output_type)
            else:
                self.assertNotIn(name, contracts())
                self.assertIsNotNone(module.PROFILE)
        self.assertEqual(11, len(contracts()))
        self.assertEqual(11, len(PUBLIC_OPERATIONS))
        self.assertEqual(
            set(PUBLIC_OPERATIONS),
            {m.EXTERNAL_NAME for m in _modules().values() if m.PUBLIC},
        )
        self.assertTrue(
            {
                "concorde-main",
                "concorde-dev-loop",
                "concorde-specify-loop",
                "concorde-specify",
            }.isdisjoint(OPERATION_NAMES)
        )

    def test_review_entries_have_fixed_authority_and_no_legacy_selector(self):
        modules = _modules()
        self.assertNotIn("review", modules)
        self.assertNotIn("concorde-review", contracts())
        self.assertNotIn("concorde-review-request", schemas())
        self.assertNotIn("concorde-review-response", schemas())
        for kind in ("spec", "code"):
            with self.subTest(kind=kind):
                operation = f"concorde-{kind}-review"
                module = modules[f"{kind}_review"]
                self.assertEqual((f"{kind}_reviewer",), module.USES)
                self.assertEqual({"target_id", "task"}, set(module.REQUEST["required"]))
                self.assertNotIn("review_mode", module.REQUEST["properties"])
                typed(
                    operation + "-request",
                    {"target_id": "module.example", "task": "Inspect"},
                )
                with self.assertRaises(TypedDataError):
                    typed(
                        operation + "-request",
                        {
                            "target_id": "module.example",
                            "task": "Inspect",
                            "review_mode": kind,
                        },
                    )

    def test_uses_is_the_only_dependency_relation_and_is_acyclic(self):
        modules = _modules()
        self.assertEqual(("context_assessor", "planner"), modules["plan"].USES)
        self.assertNotIn("specify", modules)
        self.assertEqual(
            set(COMPOSITE_OPERATIONS),
            {m.EXTERNAL_NAME for m in modules.values() if m.USES},
        )
        for module in modules.values():
            self.assertEqual(
                dependencies(module.EXTERNAL_NAME),
                tuple(operations.external_name(n) for n in module.USES),
            )
        visited = set()

        def visit(name, chain):
            self.assertNotIn(name, chain)
            self.assertIn(name, modules)
            if name in visited:
                return
            for child in modules[name].USES:
                visit(child, (*chain, name))
            visited.add(name)

        for name in modules:
            visit(name, ())

    @verifies("scenario.harness.operation-state")
    def test_model_subgraph_projects_parent_state_and_preserves_unrelated_channels(
        self,
    ):
        from tests.concorde.harness.test_operation_node import _stage_context

        node = OperationNode("planner")
        seen = []

        def launcher(value):
            seen.append(value)
            return {
                "context_id": value["data"]["snapshot"]["data"]["context_id"],
                "outcome": "completed",
                "answer": "Planned",
                "blockers": [],
                "documents": [],
                "plan": "The plan",
                "tasks": [],
            }

        from typing import TypedDict, cast

        class ParentState(TypedDict, total=False):
            snapshot: dict
            change_id: str | None
            expected_artifacts: list[str]
            plan: str
            private_parent_channel: str

        graph = StateGraph(ParentState, context_schema=OperationRuntimeContext)
        graph.add_node("plan", node.graph())
        graph.add_edge(START, "plan")
        graph.add_edge("plan", END)
        data = _stage_context()["data"]
        result = graph.compile().invoke(
            cast(ParentState, {**data, "private_parent_channel": "not admitted"}),
            context=OperationRuntimeContext(launcher=launcher),
        )
        self.assertEqual("The plan", result["plan"])
        self.assertEqual("not admitted", result["private_parent_channel"])
        self.assertEqual([typed(node.input_type, data)], seen)
        with self.assertRaises(RuntimeError):
            node.graph().invoke(data)  # State cannot supply the trusted launcher.

    @verifies("scenario.harness.operation-state")
    def test_arbitrary_compatibility_names_do_not_register_operations(self):
        from concorde.distribution.build import BuildError

        with self.assertRaises(BuildError):
            OperationNode("normalize_plan")

    @verifies("scenario.harness.operation-state")
    def test_agent_has_no_retired_model_operation_alias(self):
        planner = _modules()["planner"]
        self.assertEqual(planner.KIND, "agent")
        self.assertFalse(hasattr(planner, "run"))
        self.assertFalse(hasattr(planner, "STATE"))

    @verifies("scenario.harness.operation-result-state")
    def test_host_state_node_preserves_failure_envelope_and_runtime_context(self):
        from operations import validate

        envelope = {
            "status": "blocked",
            "output": None,
            "errors": [{"code": "fixture"}],
        }
        host = object()
        # None is an admitted request to resolve initialized project configuration on the host.
        context = OperationRuntimeContext(host=host, configuration=None)
        with patch(
            "concorde.harness.admission.run_operation",
            return_value=envelope,
        ) as run:
            result = validate.run(
                {"target_id": "module.fixture", "task": "Check"},
                Runtime(context=context),
            )
        self.assertEqual({"result": envelope}, result)
        self.assertEqual("concorde-validate", run.call_args.args[0])
        self.assertIs(host, run.call_args.kwargs["host_context"])
        with self.assertRaises(RuntimeError):
            validate.run({"task": "Check"}, Runtime(context=None))

    @verifies("scenario.harness.operation-result-state")
    def test_wire_adapter_rejects_wrong_identity_before_state_projection(self):
        from concorde.harness.admission import run_host_node

        called = []
        with self.assertRaises(TypedDataError):
            run_host_node(
                lambda *args: called.append(args),
                None,
                {},
                typed(
                    "concorde-implement-request",
                    {"target_id": "module.x", "task": "Do"},
                ),
                "concorde-plan",
            )
        self.assertEqual([], called)


class InProcessCompositionTests(unittest.TestCase):
    def test_unregistered_identity_is_refused_before_dynamic_import(self):
        from concorde.harness.host import resolve_child_operation
        from concorde.spec.repository import SpecError

        for parent, child in (
            ("concorde-main", "concorde-ghost"),
            ("concorde-ghost", "concorde-ghost"),
            ("concorde-ghost", "concorde-planner"),
        ):
            with patch("concorde.harness.host.importlib.import_module") as load:
                with self.assertRaises(SpecError) as failure:
                    resolve_child_operation(parent, child)
                self.assertEqual("unknown_operation", failure.exception.code)
                load.assert_not_called()

    def test_resolution_exactly_matches_uses_for_every_pair_including_model_nodes(self):
        from concorde.harness.host import resolve_child_operation
        from concorde.spec.repository import SpecError

        modules = _modules()
        for name, parent in modules.items():
            for child_name, child in modules.items():
                if name == child_name or child_name in parent.USES:
                    self.assertIs(
                        child,
                        resolve_child_operation(
                            parent.EXTERNAL_NAME, child.EXTERNAL_NAME
                        ),
                    )
                else:
                    with self.assertRaises(SpecError) as failure:
                        resolve_child_operation(
                            parent.EXTERNAL_NAME, child.EXTERNAL_NAME
                        )
                    self.assertEqual("undeclared_operation", failure.exception.code)


if __name__ == "__main__":
    unittest.main()
