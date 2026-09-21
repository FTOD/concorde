"""Local executable surfaces; collaborator doubles never stand for native enforcement."""

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from concorde.harness.host import OperationHost
from concorde.review import review
from concorde.spec.verification import verifies


class GraphSurfaceTests(TestCase):
    @verifies("scenario.harness.graph-execution")
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
                        state = {"targets": {}, field: {"owner": deepcopy(old)}}
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
                                "_code_scope_identity",
                                return_value="fixture-parent-scope",
                            ),
                            patch.object(
                                review,
                                "spec_consumers",
                                return_value={"peer"} if remaining else set(),
                            ),
                            patch.object(
                                __import__(
                                    "tests.concorde.support.legacy_review",
                                    fromlist=["review"],
                                ),
                                "review",
                                side_effect=reviewed,
                            ),
                            patch.object(
                                review,
                                "code_review_peers",
                                return_value=(peer,) if remaining else (),
                            ),
                            patch(
                                "concorde.review.review.Invocation",
                                side_effect=lambda *args, peer=peer: SimpleNamespace(
                                    target=peer
                                ),
                            ),
                        ):
                            result = __import__(
                                "tests.concorde.support.legacy_review",
                                fromlist=["legacy_issue_review_scope"],
                            ).legacy_issue_review_scope(run, mode)
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
                                    **(
                                        {"scope_digest": "fixture-parent-scope"}
                                        if mode == "code"
                                        else {}
                                    ),
                                },
                                records["peer"],
                            )

    @verifies("scenario.harness.graph-execution")
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
                            "component_revisions": {"peer": {}} if coordinated else {},
                            "tasks": [
                                {
                                    "target_id": "peer",
                                    "description": "Review peer",
                                    "acceptance": "Peer contract",
                                }
                            ]
                            if coordinated
                            else [],
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
                    patch.object(
                        __import__(
                            "tests.concorde.support.legacy_review", fromlist=["review"]
                        ),
                        "review",
                        side_effect=reviewed,
                    ),
                    patch(
                        "concorde.review.review.Invocation",
                        side_effect=lambda *args, peer=peer: SimpleNamespace(
                            target=peer
                        ),
                    ),
                ):
                    result = __import__(
                        "tests.concorde.support.legacy_review",
                        fromlist=["legacy_issue_review_scope"],
                    ).legacy_issue_review_scope(run, "code")
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
        "scenario.harness.graph-execution",
        "scenario.harness.graph-bounds",
        "scenario.harness.graph-inspection",
    )
    def test_scoped_review_stops_after_first_unsuccessful_result(self):
        from tests.concorde.support.legacy_graphs import batch_graph

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
                patch.object(
                    __import__(
                        "tests.concorde.support.legacy_review", fromlist=["review"]
                    ),
                    "review",
                    side_effect=reviewed,
                ),
                patch("concorde.review.review.Invocation", side_effect=child),
                patch.object(
                    batch_graph,
                    "build_batch_graph",
                    side_effect=self.instrument(
                        batch_graph.build_batch_graph, visited, drawings
                    ),
                ),
            ):
                result = __import__(
                    "tests.concorde.support.legacy_review",
                    fromlist=["legacy_issue_review_scope"],
                ).legacy_issue_review_scope(run, "code")
            self.assertEqual("failed", result["data"]["outcome"])
            self.assertEqual(stop + 1, len(calls))
            self.assert_path(drawings[0], visited)
