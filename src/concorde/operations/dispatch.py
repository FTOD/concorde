"""Operation dispatch: the admitted operation selects its entry leaf or its bound Module."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from ..dev_loop.loop import loop, loop_nodes
from ..harness.change_worktree import bind_owner, read_change, resume_owner
from ..harness.invocation import Invocation
from ..harness.relay import relay_operation
from ..implementation.implement import implement
from ..planning.plan import context_solve, plan, plan_nodes
from ..planning.tasks import tasks
from ..query_routing.main import MainInvocation
from ..spec.contracts import (
    DISCOVERY_OPERATIONS,
    MAIN_OPERATION,
    MODEL_STAGES,
    REVIEW_OPERATIONS,
)
from ..spec.project import project_nodes, project_operation
from ..spec.repository import SpecError, SpecRepository
from ..spec_authoring.author import author
from ..topology.application import (
    apply_topology,
    prepare_topology,
    topology_apply_nodes,
    topology_nodes,
)
from ..topology.design import run_topology_design, topology_response
from ..validation.validate import validate


def dispatch_graph_nodes(operation, configuration, task, host):
    """Trusted node bindings of the dispatch Graph for one admitted operation.

    Each leaf is the entry of one provider's Operation; the provider owns what it does once
    dispatched here, and every target-bound leaf receives the invocation bound by target admission.
    """
    from langgraph.graph import END

    run = None

    def bound_run() -> Invocation:
        if run is None:
            raise SpecError(
                "operation stage requires an admitted target", "invalid_context"
            )
        return run

    target_discovery = None
    target_discovery_nodes = {}

    def select_operation(state):
        if host.relay_target is not None:
            route = "relay"
        elif operation == "concorde-deliver":
            route = "deliver"
        elif operation in {"concorde-init", "concorde-configure"}:
            route = "project"
        elif operation == MAIN_OPERATION:
            route = {
                "ask": "answer",
                "design-topology": "design_topology",
                "accept-topology": "prepare_topology",
                "apply-topology": "apply_topology",
            }[task["action"]]
        else:
            route = "prepare_target"
        return {"route": route}

    def initialize_target(state):
        nonlocal task, host, target_discovery, target_discovery_nodes
        if (
            operation in DISCOVERY_OPERATIONS
            and host.routed_target is not None
            and task.get("target_id") != host.routed_target
        ):
            raise SpecError(
                "child target differs from the host's discovery route",
                "incompatible_handoff",
            )
        if operation in DISCOVERY_OPERATIONS:
            if host.routed_target is None and (
                task.get("change_id")
                or operation in {"concorde-dev-loop", "concorde-specify-loop"}
            ):
                change = read_change(host.project_root)
                if change is not None:
                    task = resume_owner(change, task)
                    if change["target_id"] is not None:
                        try:
                            SpecRepository(host.project_root, host.package_root).select(
                                change["target_id"], change["focus_id"]
                            )
                        except SpecError as error:
                            if error.code not in {"unknown_target", "invalid_focus"}:
                                raise
                            raise SpecError(
                                "recorded owner no longer resolves: " + str(error),
                                "invalid_worktree_state",
                            ) from error
                        host = replace(host, routed_target=change["target_id"])
            if host.routed_target is None:
                target_discovery = MainInvocation(operation, configuration, task, host)
                target_discovery_nodes = target_discovery.discovery_nodes()
                return {
                    "route": "discover",
                    "occurrence": 0,
                    "routes": [],
                    "decision": None,
                }
        return {"route": "bind_target"}

    def bind_target(state):
        nonlocal task, host, run
        main_completed: tuple[str, ...] = ()
        if target_discovery is not None:
            route, blocked = target_discovery.select_discovered(
                state["routes"], state["decision"]
            )
            if blocked is not None:
                return {"output": blocked, "route": END}
            if route is None:
                raise SpecError(
                    "discovery did not select an owner", "invalid_completion"
                )
            task = {
                **task,
                "target_id": route["target_id"],
                "task": route["task"],
                "constraints": route["constraints"],
            }
            if route["focus_id"] is not None:
                task["focus_id"] = route["focus_id"]
            else:
                task.pop("focus_id", None)
            host = replace(host, routed_target=route["target_id"])
            main_completed = tuple(target_discovery.completed)
        readonly = operation in {
            "concorde-main",
            "concorde-context-solve",
            *REVIEW_OPERATIONS,
        }
        readonly = readonly or (
            operation == "concorde-issues"
            and (task["action"] != "solve" or task.get("_issue_closed"))
        )
        if host.mode == "execute" and not readonly:
            SpecRepository(host.project_root, host.package_root).select(
                task["target_id"], task.get("focus_id")
            )
            bind_owner(host.project_root, task, coordinated=host.coordinated)
        run = Invocation(operation, configuration, task, host)
        bound_run().completed.extend(main_completed)
        route = (
            "review"
            if operation in REVIEW_OPERATIONS
            else (
                "describe_policy"
                if host.mode == "describe-policy"
                else {
                    "concorde-issues": "issues",
                    "concorde-specify": "specify",
                    "concorde-plan": "plan",
                    "concorde-tasks": "tasks",
                    "concorde-implement": "implement",
                    "concorde-validate": "validate",
                    "concorde-dev-loop": "development_loop",
                    "concorde-specify-loop": "specify_loop",
                }.get(operation, "context_solve")
            )
        )
        return {"route": route}

    target_nodes = {
        "initialize_target": initialize_target,
        "bind_target": bind_target,
        **{
            name: (lambda state, name=name: target_discovery_nodes[name](state))
            for name in ("decide", "expand_context", "bind_routes", "finish")
        },
    }

    def describe_policy():
        if operation == "concorde-issues" and (
            task["action"] != "solve" or task.get("_issue_closed")
        ):
            return bound_run().response(
                "described",
                "This Issue operation uses host bookkeeping only; no worker or candidate is launched.",
            )
        stages = [operation] if operation in MODEL_STAGES else []
        describe_reviews = False
        if operation == "concorde-dev-loop":
            describe_reviews = task.get("run_reviews", True)
            stages = ["concorde-context-solve", "concorde-plan", "concorde-tasks"]
            if bound_run().target.files:
                stages.append("concorde-implement")
            if task.get("specify", True):
                stages.insert(0, "concorde-specify")
        if operation == "concorde-specify-loop":
            if task.get("specify", True):
                bound_run().stage("concorde-specify")
            if task.get("run_reviews", True):
                from ..review.review import review

                review(bound_run(), "spec")
            return bound_run().response("described")
        for stage in stages:
            if stage == "concorde-context-solve" and describe_reviews:
                from ..review.review import review

                review(bound_run(), "spec")
            bound_run().stage(stage)
        if describe_reviews and bound_run().target.files:
            from ..review.review import review

            review(bound_run(), "code")
        return bound_run().response("described")

    def deliver():
        from ..harness.worktree_delivery import deliver

        return deliver(host, configuration, task)

    def project():
        if host.mode == "describe-policy":
            raise SpecError(
                "project proposals are the deterministic preview for this operation",
                "use_proposal",
            )
        return project_operation(operation, configuration, task, host)

    def review():
        from ..review.review import review_scope

        return review_scope(bound_run(), REVIEW_OPERATIONS[operation])

    def issues():
        from ..issues.graph import build_issue_graph, issue_nodes

        return build_issue_graph(issue_nodes(bound_run()).__getitem__).invoke(
            {}, {"recursion_limit": 64}
        )["output"]

    def relay():
        """Run this invocation in the prepared candidate worktree and adopt its result."""
        target = host.relay_target
        assert target is not None, "relay requires a prepared candidate"
        runner = host.relay or relay_operation
        envelope, diagnostics = runner(
            host, operation, target["invocation"], Path(target["path"])
        )
        if diagnostics:
            # The candidate's policies and usage lines reach the caller unchanged.
            sys.stderr.write(diagnostics.rstrip("\n") + "\n")
            sys.stderr.flush()
        return envelope

    operations = {
        "deliver": deliver,
        "project": project,
        "answer": lambda: MainInvocation(
            operation, configuration, task, host
        ).run_answer(),
        "design_topology": lambda: run_topology_design(
            MainInvocation(operation, configuration, task, host)
        ),
        "prepare_topology": lambda: prepare_topology(
            configuration, task["topology_proposal"], host
        ),
        "apply_topology": lambda: apply_topology(task["application"], host),
        "review": review,
        "describe_policy": describe_policy,
        "issues": issues,
        "specify": lambda: author(bound_run(), operation),
        "plan": lambda: plan(bound_run()),
        "tasks": lambda: tasks(bound_run()),
        "implement": lambda: implement(bound_run()),
        "validate": lambda: validate(bound_run(), task.get("run_checks", True)),
        "development_loop": lambda: loop(bound_run()),
        "context_solve": lambda: context_solve(bound_run(), operation),
    }
    nodes: dict[str, Callable] = {
        name: (lambda state, operation=operation: {"output": operation()})
        for name, operation in operations.items()
    }
    nodes["relay"] = lambda state: {"relayed": relay()}
    subgraphs = {}

    def subgraph(name, child, state):
        if name not in subgraphs:
            if name == "prepare_target":
                subgraphs[name] = target_nodes
            elif name in {"answer", "design_topology"}:
                main = MainInvocation(operation, configuration, task, host)
                response = (
                    main.answer_response
                    if name == "answer"
                    else lambda decision, main=main: topology_response(main, decision)
                )
                subgraphs[name] = {
                    **main.discovery_nodes(),
                    "respond": lambda state: {"output": response(state["decision"])},
                }
            elif name == "prepare_topology":
                subgraphs[name] = topology_nodes(
                    configuration, task["topology_proposal"], host
                )
            elif name == "apply_topology":
                subgraphs[name] = topology_apply_nodes(task["application"], host)
            elif name == "project":
                subgraphs[name] = project_nodes(operation, configuration, task, host)
            elif name == "plan":
                subgraphs[name] = plan_nodes(bound_run())
            elif name == "specify_loop":
                from ..specify_loop.specify_graph import specify_nodes

                subgraphs[name] = specify_nodes(bound_run())
            elif name == "development_loop":
                subgraphs[name] = loop_nodes(bound_run())
            elif name == "issues":
                from ..issues.graph import issue_nodes

                subgraphs[name] = issue_nodes(bound_run())
        return subgraphs[name][child](state)

    from .dispatch_graph import SUBGRAPH_NODES

    return {
        "select_operation": select_operation,
        **nodes,
        **{
            name + "/" + child: (
                lambda state, name=name, child=child: subgraph(name, child, state)
            )
            for name, children in SUBGRAPH_NODES.items()
            for child in children
        },
    }
