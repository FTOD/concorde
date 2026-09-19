"""Local executable surfaces; collaborator doubles never stand for native enforcement."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import TestCase
from unittest.mock import Mock, patch

from concorde.query_routing import discovery_graph
from concorde.review import review
from concorde.implementation.coordination_graph import (
    build_coordination_graph,
    build_stabilization_graph,
)
from concorde.query_routing.main import MainInvocation
from concorde.harness.host import OperationHost
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class GraphSurfaceTests(TestCase):
    @verifies("scenario.development.graph-execution")
    def test_review_membership_retirement_preserves_unvisited_applicable_receipts(self):
        from copy import deepcopy

        for mode in ("code", "spec"):
            for remaining in (False, True):
                for interrupted in (False, True):
                    with self.subTest(
                        mode=mode, remaining=remaining, interrupted=interrupted
                    ):
                        owner = SimpleNamespace(id="owner", uses=(), files=("code.py",))
                        peer = SimpleNamespace(id="peer", files=("code.py",))
                        members = [owner, peer] if remaining else [owner]
                        repository = SimpleNamespace(
                            root=Path("."),
                            covering_modules=lambda _, members=members: members,
                            children=lambda _: [],
                            select=lambda name, peer=peer: peer,
                        )
                        host = OperationHost(Path("."), Path("."), mode="execute")
                        run = SimpleNamespace(
                            repository=repository,
                            target=owner,
                            host=host,
                            task={"task": "Review"},
                            configuration={},
                            change_id=None,
                            completed=[],
                        )
                        run.response = lambda outcome, answer, **data: {
                            "data": {"outcome": outcome, **data}
                        }
                        field = (
                            "shared_spec_reviews"
                            if mode == "spec"
                            else "shared_implementation_reviews"
                        )
                        old = {
                            name: {
                                "artifact": {"id": name, "path": name + ".json"},
                                "task": "old",
                                "constraints": [],
                            }
                            for name in ("peer", "removed")
                        }
                        state = {field: {"owner": deepcopy(old)}}
                        calls = []

                        def reviewed(
                            child,
                            selected_mode,
                            calls=calls,
                            interrupted=interrupted,
                            mode=mode,
                        ):
                            key = child.target.id
                            calls.append(key)
                            return {
                                "data": {
                                    "outcome": "failed" if interrupted else "completed",
                                    "answer": "review",
                                    "blockers": [],
                                    "completed_operations": [],
                                    "artifacts": [
                                        {
                                            "id": f"review.{key}.{mode}",
                                            "path": key + "-new.json",
                                        }
                                    ],
                                    "reviews": [{"data": {"target_id": key}}],
                                }
                            }

                        with (
                            patch.object(review, "read_change", return_value=state),
                            patch.object(review, "save_change") as save,
                            patch.object(
                                review,
                                "spec_consumers",
                                return_value={"peer"} if remaining else set(),
                            ),
                            patch.object(review, "review", side_effect=reviewed),
                            patch(
                                "concorde.review.review.Invocation",
                                side_effect=lambda *args, peer=peer: SimpleNamespace(
                                    target=peer
                                ),
                            ),
                        ):
                            result = review.review_scope(run, mode)
                        records = save.call_args.args[1][field]["owner"]
                        self.assertEqual({"peer"} if remaining else set(), set(records))
                        self.assertEqual(
                            ["owner", "peer"]
                            if remaining and not interrupted
                            else ["owner"],
                            calls,
                        )
                        self.assertEqual(
                            "failed" if interrupted else "completed",
                            result["data"]["outcome"],
                        )
                        if remaining:
                            self.assertEqual(
                                old["peer"]
                                if interrupted
                                else {
                                    "artifact": {
                                        "id": f"review.peer.{mode}",
                                        "path": "peer-new.json",
                                    },
                                    "task": (
                                        "Review this Module's reliance on the changed canonical Spec. Review"
                                        if mode == "spec"
                                        else "Check this Module's own contract against the shared implementation change. Review"
                                    ),
                                    "constraints": [],
                                },
                                records["peer"],
                            )

    @verifies("scenario.development.graph-execution")
    def test_code_owner_is_reviewed_with_and_without_recorded_components(self):
        for coordinated in (False, True):
            with self.subTest(coordinated=coordinated):
                owner = SimpleNamespace(id="owner", uses=("peer",), files=("owner.py",))
                peer = SimpleNamespace(id="peer", files=("peer.py",))
                repository = SimpleNamespace(
                    root=Path("."),
                    covering_modules=lambda _, owner=owner: [owner],
                    children=lambda _: [],
                    select=lambda _, peer=peer: peer,
                )
                run = SimpleNamespace(
                    repository=repository,
                    target=owner,
                    host=OperationHost(Path("."), Path("."), mode="describe-policy"),
                    task={"task": "Review owner"},
                    configuration={},
                    change_id=None,
                    completed=[],
                )
                run.response = lambda outcome, answer, **data: {
                    "data": {"outcome": outcome, **data}
                }
                state = {
                    "targets": {
                        "owner": {
                            "coordination": {"peer": {"task": "Review peer"}}
                            if coordinated
                            else {}
                        }
                    }
                }
                calls = []

                def reviewed(child, mode, calls=calls):
                    calls.append((child.target.id, mode))
                    return {
                        "data": {
                            "outcome": "completed",
                            "answer": "Reviewed",
                            "blockers": [],
                            "artifacts": [],
                            "reviews": [],
                            "completed_operations": [],
                        }
                    }

                with (
                    patch.object(review, "read_change", return_value=state),
                    patch.object(review, "spec_consumers", return_value=set()),
                    patch.object(review, "review", side_effect=reviewed),
                    patch(
                        "concorde.review.review.Invocation",
                        side_effect=lambda *args, peer=peer: SimpleNamespace(
                            target=peer
                        ),
                    ),
                ):
                    result = review.review_scope(run, "code")
                self.assertEqual("completed", result["data"]["outcome"])
                self.assertEqual(
                    [("owner", "code"), ("peer", "code")]
                    if coordinated
                    else [("owner", "code")],
                    calls,
                )

    def instrument(self, build, visited, drawings):
        def factory(nodes, **options):
            def node(name):
                execute = nodes(name)

                def record(state):
                    visited.append(name)
                    return execute(state)

                return record

            graph = build(node, **options)
            drawing = graph.get_graph().to_json()
            self.assertEqual(drawing, graph.get_graph().to_json())
            self.assertEqual([], visited)
            self.assertIs(graph.checkpointer, False)
            drawings.append(drawing)
            return graph

        return factory

    def assert_path(self, drawing, visited):
        edges = {(edge["source"], edge["target"]) for edge in drawing["edges"]}
        path = ["__start__", *visited, "__end__"]
        self.assertTrue(
            all(pair in edges for pair in zip(path, path[1:], strict=False))
        )

    @verifies(
        "scenario.development.graph-execution",
        "scenario.development.graph-bounds",
        "scenario.harness.graph-inspection",
    )
    def test_fresh_discovery_uses_inspected_factory_and_preserves_intent(self):
        for operation in ("concorde-review", "concorde-dev-loop"):
            for terminal in ("routed", "failed"):
                with self.subTest(operation=operation, terminal=terminal):
                    run: Any = MainInvocation.__new__(MainInvocation)
                    run.operation = operation
                    run.repository = SimpleNamespace(
                        targets={
                            str(i): SimpleNamespace(kind="module") for i in range(40)
                        },
                        select=lambda name, focus=None: SimpleNamespace(
                            kind="module", id=name
                        ),
                    )
                    run.host = SimpleNamespace(mode="execute")
                    run.task = {
                        "task": "Original intent",
                        "constraints": ["Keep scope"],
                    }
                    run.completed, run.discovered = [], ["entry"]
                    run.stage_context_text = lambda _: " ".join(
                        "module." + str(i) for i in range(35)
                    )
                    run.stage = Mock(
                        side_effect=lambda phase, occurrence, terminal=terminal: (
                            {
                                "outcome": "expand",
                                "expand_targets": ["module." + str(occurrence)],
                            }
                            if occurrence < 35
                            else {
                                "outcome": terminal,
                                "answer": "Stopped",
                                "routes": [
                                    {"target_id": "module.34", "focus_id": None}
                                ],
                            }
                        )
                    )
                    visited, drawings = [], []
                    with patch.object(
                        discovery_graph,
                        "build_discovery_graph",
                        side_effect=self.instrument(
                            discovery_graph.build_discovery_graph, visited, drawings
                        ),
                    ):
                        routes, decision = run.discover_routes()
                    self.assertEqual(36, run.stage.call_count)
                    self.assert_path(drawings[0], visited)
                    if terminal == "routed":
                        self.assertEqual("Original intent", routes[0]["task"])
                        self.assertEqual(["Keep scope"], routes[0]["constraints"])
                        self.assertIsNone(decision)
                    else:
                        self.assertEqual([], routes)
                        self.assertEqual("failed", decision["outcome"])

    @verifies(
        "scenario.development.graph-bounds", "scenario.development.discovery-limit"
    )
    def test_discovery_domain_limit_does_not_restart(self):
        run: Any = MainInvocation.__new__(MainInvocation)
        run.repository = SimpleNamespace(
            targets={"entry": SimpleNamespace(kind="module")}
        )
        run.stage = Mock()
        with self.assertRaises(SpecError) as caught:
            run.discovery_nodes()["decide"]({"occurrence": 2})
        self.assertEqual("context_limit", caught.exception.code)
        run.stage.assert_not_called()

    @verifies(
        "scenario.development.graph-execution", "scenario.harness.graph-inspection"
    )
    def test_coordination_variants_stop_before_dependent_nodes(self):
        names = [
            "reconcile_specs",
            "validate_specs",
            "implement_components",
            "implement_local",
            "finalize_components",
            "record_completion",
        ]
        for stop in [None, *names[:-1]]:
            visited, drawings = [], []

            def node(name, stop=stop):
                return lambda state: {
                    "output": {"outcome": "failed"} if name == stop else None
                }

            graph = self.instrument(build_coordination_graph, visited, drawings)(node)
            graph.invoke({})
            self.assertEqual(
                names if stop is None else names[: names.index(stop) + 1], visited
            )
            self.assert_path(drawings[0], visited)

    @verifies("scenario.development.graph-bounds", "scenario.harness.graph-inspection")
    def test_stabilization_repeats_without_leaking_state(self):
        for _ in range(2):
            visited, drawings, rounds = [], [], []

            def node(name, rounds=rounds):
                def execute(state):
                    if name == "snapshot":
                        rounds.append(len(rounds))
                    return {
                        "route": "__end__" if len(rounds) == 30 else "snapshot",
                        "output": None,
                    }

                return execute

            graph = self.instrument(build_stabilization_graph, visited, drawings)(node)
            graph.invoke({}, {"recursion_limit": 93})
            self.assertEqual(30, len(rounds))
            self.assert_path(drawings[0], visited)

    @verifies(
        "scenario.development.graph-execution",
        "scenario.development.graph-bounds",
        "scenario.harness.graph-inspection",
    )
    def test_scoped_review_stops_after_first_unsuccessful_result(self):
        from concorde.harness import batch_graph

        for stop in (0, 37):
            target = SimpleNamespace(id="owner", uses=(), files=("code.py",))
            peers = [
                SimpleNamespace(id="peer." + str(i), files=("code.py",))
                for i in range(40)
            ]
            repository = SimpleNamespace(
                root=Path("."),
                covering_modules=lambda _, target=target, peers=peers: [target, *peers],
                children=lambda _: [],
                select=lambda name, peers=peers: next(p for p in peers if p.id == name),
            )
            host = OperationHost(Path("."), Path("."), mode="describe-policy")
            run = SimpleNamespace(
                repository=repository,
                target=target,
                host=host,
                task={"task": "Review"},
                configuration={},
                change_id=None,
                completed=[],
            )
            run.response = lambda outcome, answer, **data: {
                "data": {"outcome": outcome, **data}
            }
            calls, visited, drawings = [], [], []

            def reviewed(child, mode, calls=calls, stop=stop):
                calls.append(child.target.id)
                return {
                    "data": {
                        "outcome": "failed" if len(calls) - 1 == stop else "completed",
                        "answer": "review",
                        "blockers": [],
                        "artifacts": [],
                        "reviews": [],
                        "completed_operations": [],
                    }
                }

            def child(
                operation, configuration, task, child_host, repository=repository
            ):
                return SimpleNamespace(target=repository.select(task["target_id"]))

            with (
                patch.object(review, "read_change", return_value=None),
                patch.object(review, "spec_consumers", return_value=set()),
                patch.object(review, "code_review_peers", return_value=tuple(peers)),
                patch.object(review, "review", side_effect=reviewed),
                patch("concorde.review.review.Invocation", side_effect=child),
                patch.object(
                    batch_graph,
                    "build_batch_graph",
                    side_effect=self.instrument(
                        batch_graph.build_batch_graph, visited, drawings
                    ),
                ),
            ):
                result = review.review_scope(run, "code")
            self.assertEqual("failed", result["data"]["outcome"])
            self.assertEqual(stop + 1, len(calls))
            self.assert_path(drawings[0], visited)
