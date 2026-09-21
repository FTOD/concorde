"""Dispatch the caller-selected Operation and deterministically checked Module."""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import replace

from ..harness.change_worktree import bind_owner, read_change
from ..harness.invocation import Invocation
from ..harness.relay import relay_operation
from ..implementation.implement import implement
from ..planning.plan import context_solve, plan, plan_nodes
from ..planning.tasks import tasks
from ..spec.contracts import MODEL_STAGES, REVIEW_OPERATIONS
from ..spec.project import project_nodes, project_operation
from ..spec.repository import SpecError, SpecRepository
from ..validation.validate import validate


def dispatch_graph_nodes(operation, configuration, task, host):
    """Bind declared provider entries; never infer a target or author a Spec."""
    run = None

    def bound_run():
        if run is None:
            raise SpecError("operation requires an admitted target", "invalid_context")
        return run

    def select_operation(state):
        if host.relay_target is not None:
            route = "relay"
        elif operation == "concorde-deliver":
            route = "deliver"
        elif operation in {"concorde-init", "concorde-configure"}:
            route = "project"
        else:
            route = "prepare_target"
        return {"route": route}

    def bind_target(state):
        nonlocal run, host
        if not task.get("target_id"):
            raise SpecError("select an explicit target_id", "invalid_input")
        SpecRepository(host.project_root, host.package_root).select(
            task["target_id"], task.get("focus_id")
        )
        readonly = operation in {"concorde-context-solve", *REVIEW_OPERATIONS}
        readonly = readonly or (
            operation == "concorde-issues"
            and (task["action"] != "solve" or task.get("_issue_closed"))
        )
        change = read_change(host.project_root)
        if change and change.get("target_id") not in {None, task["target_id"]}:
            from ..implementation.implement import component_intent
            from ..harness.revisions import target_revision

            repository = SpecRepository(host.project_root, host.package_root)
            admitted = False
            for owner_id, record in change["targets"].items():
                owner = repository.select(owner_id)
                allowed = {
                    *owner.uses,
                    *(child.id for child in repository.children(owner)),
                }
                selected = [
                    item
                    for item in record.get("tasks", [])
                    if item["target_id"] == task["target_id"]
                ]
                if (
                    task["target_id"] in allowed
                    and record.get("plan")
                    and record.get("spec_digest") == target_revision(repository, owner)
                    and selected
                    and task["task"] == component_intent(selected)
                    and task.get("constraints", []) == record.get("constraints", [])
                    and task.get("focus_id") is None
                ):
                    admitted = True
                    break
            if admitted:
                host = replace(host, coordinated=True)
        if host.mode == "execute" and not readonly:
            bind_owner(host.project_root, task, coordinated=host.coordinated)
        run = Invocation(operation, configuration, task, host)
        route = (
            "review"
            if operation in REVIEW_OPERATIONS
            else "describe_policy"
            if host.mode == "describe-policy"
            else {
                "concorde-issues": "issues",
                "concorde-plan": "plan",
                "concorde-tasks": "tasks",
                "concorde-implement": "implement",
                "concorde-validate": "validate",
                "concorde-context-solve": "context_solve",
            }[operation]
        )
        return {"route": route}

    def describe_policy():
        if operation == "concorde-context-solve" and host.executor is None:
            if host.native_assessment is not None:
                return host.native_assessment(bound_run())
            from ..harness.native_context import assessment_context

            assessment_context(bound_run())
            return bound_run().response(
                "described",
                "Native context-assessor: prompt-level read-only policy; no model launched. Use the Pi preparation boundary for the exact context index and native call.",
            )
        if operation == "concorde-issues" and (
            task["action"] != "solve" or task.get("_issue_closed")
        ):
            return bound_run().response(
                "described", "Host bookkeeping only; no worker is launched."
            )
        if operation in MODEL_STAGES:
            bound_run().stage(operation)
        return bound_run().response("described")

    def deliver():
        from ..harness.worktree_delivery import deliver

        return deliver(host, configuration, task)

    def project():
        if host.mode == "describe-policy":
            raise SpecError("project proposals provide the preview", "use_proposal")
        return project_operation(operation, configuration, task, host)

    def review():
        from ..review.review import review_scope

        return review_scope(bound_run(), REVIEW_OPERATIONS[operation])

    def relay(state):
        target = host.relay_target
        assert target is not None
        runner = host.relay or relay_operation
        envelope, diagnostics = runner(
            host, operation, target["invocation"], Path(target["path"])
        )
        if diagnostics:
            sys.stderr.write(diagnostics.rstrip("\n") + "\n")
            sys.stderr.flush()
        return {"relayed": envelope}

    entries = {
        "deliver": deliver,
        "project": project,
        "review": review,
        "describe_policy": describe_policy,
        "plan": lambda: plan(bound_run()),
        "tasks": lambda: tasks(bound_run()),
        "implement": lambda: implement(bound_run()),
        "validate": lambda: validate(bound_run(), task.get("run_checks", True)),
        "context_solve": lambda: context_solve(bound_run(), operation),
    }
    subgraphs = {}

    def subgraph(name, child, state):
        if name not in subgraphs:
            if name == "prepare_target":
                subgraphs[name] = {"bind_target": bind_target}
            elif name == "project":
                subgraphs[name] = project_nodes(operation, configuration, task, host)
            elif name == "plan":
                subgraphs[name] = plan_nodes(bound_run())
            elif name == "issues":
                from ..issues.graph import issue_nodes

                subgraphs[name] = issue_nodes(bound_run())
        return subgraphs[name][child](state)

    from .dispatch_graph import SUBGRAPH_NODES

    return {
        "select_operation": select_operation,
        "relay": relay,
        **{
            name: (lambda state, entry=entry: {"output": entry()})
            for name, entry in entries.items()
        },
        **{
            name + "/" + child: (
                lambda state, name=name, child=child: subgraph(name, child, state)
            )
            for name, children in SUBGRAPH_NODES.items()
            for child in children
        },
    }
