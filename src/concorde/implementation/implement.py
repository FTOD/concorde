"""Implementation of an accepted task list, or coordination of participating components."""

from __future__ import annotations

from dataclasses import replace

from ..dev_loop.loop import loop
from ..harness.change_worktree import (
    progress,
    read_change,
    save_change,
    save_target_state,
    target_state,
)
from ..harness.invocation import Invocation
from ..harness.revisions import (
    implementation_digest,
    target_revision,
    unconfirmed_files,
)
from ..review.review import require_spec_review
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import decode, typed, validate_typed, verify_artifacts
from ..spec.validation import validate_repository
from ..validation.validate import verify_completion


def component_intent(tasks: list[dict]) -> str:
    return "\n\n".join(
        task["description"] + "\nAcceptance: " + task["acceptance"] for task in tasks
    )


def implement(run) -> dict:
    require_spec_review(run)
    pending = run.pending_gaps("implementation")
    if pending:
        return run.response(
            "spec_incomplete",
            "Resolve the prerequisite task gaps before implementation.",
            blockers=pending,
        )
    if not run.work_directory:
        raise SpecError(
            "implementation requires a managed change and authored tasks",
            "missing_change",
        )
    state = target_state(run.repository.root, run.target.id, run.task.get("focus_id"))
    run.check_state(state)
    if not state["tasks"]:
        raise SpecError("implementation requires tasks", "missing_tasks")
    if state.get("coordination") or any(
        task["target_id"] != run.target.id for task in state["tasks"]
    ):
        return implement_scope(run, state)
    if (
        validate_repository(
            run.repository.root, package_root=run.host.package_root
        ).status
        != "success"
    ):
        raise SpecError(
            "reconcile all shared contracts before implementation",
            "incompatible_contracts",
        )
    if not run.host.coordinated:
        progress(
            run.repository.root,
            phase="implementation",
            status="active",
            invalidate=True,
        )
    inputs = (
        typed(
            "concorde-implementation-task",
            {"plan": state["plan"], "tasks": state["tasks"]},
        ),
    )
    repair_review = state.get("repair_review")
    if repair_review:
        verify_artifacts(run.repository.root, repair_review)
        review_value = validate_typed(
            decode(read_file(run.repository.root, repair_review["path"]).decode()),
            "concorde-review-result",
        )
        inputs = (*inputs, review_value)
    result = run.stage("concorde-implement", inputs=inputs, defer_gap_resolution=True)
    if result["outcome"] not in {"completed", "sufficient"}:
        return run.response(
            result["outcome"], result["answer"], blockers=result["blockers"]
        )
    if run.host.mode == "describe-policy":
        return run.response("described")
    returned = result["tasks"]
    expected = [{**task, "complete": True} for task in state["tasks"]]
    if returned != expected:
        raise SpecError(
            "implementation must report every exact task complete",
            "incomplete_tasks",
        )
    missing = unconfirmed_files(run.repository, run.target)
    if missing:
        raise SpecError(
            "implementation did not materialize required listed files: "
            + ", ".join(missing),
            "incomplete_tasks",
        )
    state["tasks"] = returned
    state["implementation_digest"] = implementation_digest(run.repository, run.target)
    state["checks"] = []
    state.pop("repair_review", None)
    state.update(phase="implementation", status="completed")
    save_target_state(run.repository.root, state)
    change = read_change(run.repository.root)
    if change is not None and run.target.id in change.get("graph", {}):
        # Keep the graph's own baseline in sync with every real implementation, so the next
        # loop() invocation's reset check only fires for an out-of-band (human) code edit.
        change["graph"][run.target.id]["last_implementation_digest"] = state[
            "implementation_digest"
        ]
        save_change(run.repository.root, change)
    run.record_gaps("implementation", [])
    return run.response(answer=result["answer"])


def implement_scope(run, state: dict) -> dict:
    """Retain resumable component drafts inside this one candidate worktree."""
    grouped = {}
    review_artifacts = []
    for task in state["tasks"]:
        component = run.repository.select(task["target_id"])
        allowed = {
            run.target.id,
            *run.target.uses,
            *(child.id for child in run.repository.children(run.target)),
        }
        if component.id not in allowed:
            raise SpecError(
                "coordinated task must name a declared dependency or direct submodule",
                "permission_denied",
            )
        grouped.setdefault(component.id, []).append(task)
    local_tasks = grouped.pop(run.target.id, [])
    component_tasks = {
        target_id: component_intent(tasks) for target_id, tasks in grouped.items()
    }
    coordination = state.setdefault("coordination", {})
    # Local repair tasks do not erase already completed participating work. Its final
    # contract evidence must still be refreshed if the repair changes a shared implementation.
    for target_id, record in coordination.items():
        component_tasks.setdefault(target_id, record["task"])
    for target_id, task_text in component_tasks.items():
        record = coordination.setdefault(
            target_id,
            {
                "task": task_text,
                "spec_status": "pending",
                "implementation_status": "pending",
                "spec_digest": None,
                "implementation_digest": None,
                "blockers": [],
                "outcome": None,
            },
        )
        if record["task"] != task_text:
            raise SpecError(
                "component intent changed; replan this worktree change",
                "stale_context",
            )
    progress(
        run.repository.root,
        phase="spec_reconciliation",
        status="active",
        invalidate=True,
    )
    state.update(phase="spec_reconciliation", status="active")
    save_target_state(run.repository.root, state)

    def blocked(result, target_id, phase):
        record = coordination[target_id]
        record[phase + "_status"] = "blocked"
        child = result["output"]["data"] if result["output"] else None
        record["outcome"] = child["outcome"] if child else "failed"
        record["blockers"] = child["blockers"] if child else []
        state["status"] = "blocked"
        save_target_state(run.repository.root, state)
        progress(
            run.repository.root,
            status="blocked",
            outcome=record["outcome"],
            blockers=record["blockers"],
        )
        if child:
            return run.response(
                child["outcome"],
                "Component " + target_id + ": " + child["answer"],
                blockers=child["blockers"],
                artifacts=child["artifacts"],
            )
        raise SpecError(
            "component " + phase + " blocked: " + target_id, "child_blocked"
        )

    from ..harness.admission import run_operation
    from ..harness.batch_graph import run_batch_graph
    from .coordination_graph import build_coordination_graph

    def reconcile_specs(_graph_state):
        def reconcile_component(item):
            target_id, task_text = item
            component = run.repository.select(target_id)
            record = coordination[target_id]
            revision = target_revision(run.repository, component)
            if (
                record["spec_status"] == "completed"
                and record["spec_digest"] == revision
            ):
                return None
            record.update(
                spec_status="running",
                implementation_status="pending",
                blockers=[],
                outcome=None,
            )
            save_target_state(run.repository.root, state)
            payload = {
                "target_id": target_id,
                "task": task_text,
                "change_id": run.change_id,
                "constraints": run.task.get("constraints", []),
            }
            child_host = replace(
                run.host,
                routed_target=target_id,
                coordinated=True,
                defer_component_checks=True,
                finalize_components=False,
            )
            result = run_operation(
                "concorde-specify",
                run.configuration,
                typed("concorde-specify-request", payload),
                host_context=child_host,
            )
            if result["status"] != "succeeded":
                return blocked(result, target_id, "spec")
            run.repository = SpecRepository(
                run.host.project_root, run.host.package_root
            )
            record.update(
                spec_status="completed",
                outcome="completed",
                spec_digest=target_revision(
                    run.repository, run.repository.select(target_id)
                ),
            )
            save_target_state(run.repository.root, state)

        from ..harness.batch_graph import run_batch_graph

        failure = run_batch_graph(
            component_tasks.items(),
            reconcile_component,
            name="component_spec_graph",
            item_node="author_module",
        )
        if failure is not None:
            return {"output": failure}

        return {"output": None}

    def validate_specs(_graph_state):
        # Transitional consumer/provider disagreement is allowed until every
        # participating author has completed. It must not prevent resuming a draft.
        progress(run.repository.root, phase="spec_validation", status="active")
        if (
            validate_repository(
                run.repository.root, package_root=run.host.package_root
            ).status
            != "success"
        ):
            state.update(phase="spec_validation", status="blocked")
            save_target_state(run.repository.root, state)
            progress(
                run.repository.root,
                status="blocked",
                outcome="incompatible_contracts",
            )
            raise SpecError(
                "reconcile all consumer/provider contracts before implementation",
                "incompatible_contracts",
            )
        progress(run.repository.root, phase="implementation", status="active")
        state.update(phase="implementation", status="active")
        return {"output": None}

    def implement_components(_graph_state):
        def implement_component(item):
            target_id, task_text = item
            component = run.repository.select(target_id)
            record = coordination[target_id]
            payload = {
                "target_id": target_id,
                "task": task_text,
                "change_id": run.change_id,
                "constraints": run.task.get("constraints", []),
            }
            child_host = replace(
                run.host,
                routed_target=target_id,
                coordinated=True,
                defer_component_checks=True,
                finalize_components=False,
            )
            from ..review.review import require_reviews

            require_reviews(
                Invocation(
                    "concorde-spec-review", run.configuration, payload, child_host
                ),
                bool(
                    read_change(run.repository.root, required=True)
                    .get("review_requirements", {})
                    .get(run.target.id, {})
                    .get("spec")
                ),
            )
            if record["implementation_status"] == "completed" and record[
                "implementation_digest"
            ] == implementation_digest(run.repository, component):
                try:
                    verify_completion(
                        Invocation(
                            "concorde-validate", run.configuration, payload, child_host
                        )
                    )
                    review_artifacts.extend(
                        item["artifact"]
                        for item in read_change(run.repository.root, required=True)
                        .get("reviews", {})
                        .get(target_id, {})
                        .values()
                    )
                    return None
                except SpecError:
                    pass
            record.update(implementation_status="running", blockers=[], outcome=None)
            save_target_state(run.repository.root, state)
            result = run_operation(
                "concorde-dev-loop",
                run.configuration,
                typed(
                    "concorde-dev-loop-request",
                    {
                        **payload,
                        "specify": False,
                        "run_reviews": bool(
                            read_change(run.repository.root, required=True)
                            .get("review_requirements", {})
                            .get(run.target.id, {})
                            .get("spec")
                        ),
                    },
                ),
                host_context=child_host,
            )
            if result["status"] != "succeeded":
                return blocked(result, target_id, "implementation")
            review_artifacts.extend(
                item
                for item in result["output"]["data"]["artifacts"]
                if item["id"].startswith("review.")
            )
            run.repository = SpecRepository(
                run.host.project_root, run.host.package_root
            )
            record.update(
                implementation_status="completed",
                outcome="completed",
                implementation_digest=implementation_digest(
                    run.repository, run.repository.select(target_id)
                ),
            )
            save_target_state(run.repository.root, state)

        failure = run_batch_graph(
            component_tasks.items(),
            implement_component,
            name="component_implementation_graph",
            item_node="develop_module",
        )
        if failure is not None:
            return {"output": failure}
        return {"output": None}

    def implement_local(_graph_state):
        if local_tasks:
            # A composite may also own coordination code. Do not recursively start a dev-loop
            # for this same target or replace its enclosing plan with one local subtask.
            current_local = implementation_digest(run.repository, run.target)
            expected_local = [{**task, "complete": True} for task in local_tasks]
            if (
                state.get("local_implementation_digest") != current_local
                or state.get("local_completed_tasks") != expected_local
            ):
                inputs = (
                    typed(
                        "concorde-implementation-task",
                        {"plan": state["plan"], "tasks": local_tasks},
                    ),
                )
                result = run.stage(
                    "concorde-implement", inputs=inputs, defer_gap_resolution=True
                )
                if result["outcome"] not in {"completed", "sufficient"}:
                    state.update(phase="implementation", status="blocked")
                    save_target_state(run.repository.root, state)
                    return {
                        "output": run.response(
                            result["outcome"],
                            result["answer"],
                            blockers=result["blockers"],
                        )
                    }
                if result["tasks"] != expected_local:
                    raise SpecError(
                        "local coordination code did not complete its exact tasks",
                        "incomplete_tasks",
                    )
                if unconfirmed_files(run.repository, run.target):
                    raise SpecError(
                        "local implementation did not materialize its listed files",
                        "incomplete_tasks",
                    )
                state["local_completed_tasks"] = expected_local
                state["local_implementation_digest"] = implementation_digest(
                    run.repository, run.target
                )
                save_target_state(run.repository.root, state)
        return {"output": None}

    def finalize_components(_graph_state):
        # All coordinated writers finish before any consumer's final code checks. A nested
        # coordinator leaves explicit drafts; the outer coordinator finalizes the whole tree.
        if not run.host.defer_component_checks:
            finalized = set()

            def finalize(target_id, task_text):
                if target_id in finalized:
                    return None
                finalized.add(target_id)
                run.repository = SpecRepository(
                    run.host.project_root, run.host.package_root
                )
                component = run.repository.select(target_id)
                component_state = target_state(run.repository.root, target_id, None)
                nested = component_state.get("coordination", {})
                failure = run_batch_graph(
                    nested.items(),
                    lambda item: finalize(item[0], item[1]["task"]),
                    name="nested_finalization_graph",
                    item_node="finalize_module",
                )
                if failure is not None:
                    return failure
                run.repository = SpecRepository(
                    run.host.project_root, run.host.package_root
                )
                component = run.repository.select(target_id)
                component_state = target_state(run.repository.root, target_id, None)
                component_state["component_revisions"] = {
                    key: {
                        "spec": target_revision(
                            run.repository, run.repository.select(key)
                        ),
                        "implementation": implementation_digest(
                            run.repository, run.repository.select(key)
                        ),
                    }
                    for key in nested
                }
                component_state.update(
                    implementation_digest=implementation_digest(
                        run.repository, component
                    ),
                    checks=[],
                    phase="validate",
                    status="active",
                )
                save_target_state(run.repository.root, component_state)
                payload = {
                    "target_id": target_id,
                    "task": task_text,
                    "change_id": run.change_id,
                    "constraints": run.task.get("constraints", []),
                }
                child_host = replace(
                    run.host,
                    routed_target=target_id,
                    coordinated=True,
                    defer_ready=True,
                    defer_component_checks=False,
                    finalize_components=True,
                )
                change = read_change(run.repository.root, required=True)
                enabled = bool(
                    change.get("review_requirements", {}).get(target_id, {}).get("spec")
                )
                child = Invocation(
                    "concorde-dev-loop",
                    run.configuration,
                    {**payload, "specify": False, "run_reviews": enabled},
                    child_host,
                )
                verified = loop(child)["data"]
                if verified["outcome"] not in {"completed", "ready"}:
                    return verified
                review_artifacts.extend(verified["artifacts"])
                return None

            def participating_ids():
                change = read_change(run.repository.root, required=True)
                selected = {run.target.id}

                def visit(target_id):
                    if target_id in selected:
                        return
                    selected.add(target_id)
                    for nested_id in (
                        change["targets"].get(target_id, {}).get("coordination", {})
                    ):
                        visit(nested_id)

                for target_id in component_tasks:
                    visit(target_id)
                return selected

            def candidate_implementation():
                run.repository = SpecRepository(
                    run.host.project_root, run.host.package_root
                )
                return digest(
                    [
                        (
                            key,
                            implementation_digest(
                                run.repository, run.repository.select(key)
                            ),
                        )
                        for key in sorted(participating_ids())
                    ]
                )

            # Local repair remains bounded by each Module's loop. A later repair can stale
            # an earlier consumer; rerun final verification until the shared candidate is stable.
            from langgraph.graph import END

            from .coordination_graph import build_stabilization_graph

            remaining = 1 + 2 * len(participating_ids())
            before_finalization = None

            def snapshot(_graph_state):
                nonlocal remaining, before_finalization
                if remaining == 0:
                    raise SpecError(
                        "shared implementation repairs did not converge to one verified candidate",
                        "incompatible_contracts",
                    )
                remaining -= 1
                before_finalization = candidate_implementation()
                finalized.clear()
                return {}

            def verify_component(item):
                target_id, task_text = item
                failure = finalize(target_id, task_text)
                if failure is not None:
                    state.update(phase="validate", status="blocked")
                    save_target_state(run.repository.root, state)
                    return run.response(
                        failure["outcome"],
                        failure["answer"],
                        blockers=failure.get("blockers", []),
                        checks=failure.get("checks", []),
                        artifacts=failure.get("artifacts", []),
                    )
                coordination[target_id]["implementation_digest"] = (
                    implementation_digest(
                        run.repository, run.repository.select(target_id)
                    )
                )

            def verify_components(_graph_state):
                return {
                    "output": run_batch_graph(
                        component_tasks.items(),
                        verify_component,
                        name="component_finalization_graph",
                        item_node="finalize_module",
                    )
                }

            def check_stability(_graph_state):
                return {
                    "route": END
                    if candidate_implementation() == before_finalization
                    else "snapshot"
                }

            nodes = {
                "snapshot": snapshot,
                "verify_components": verify_components,
                "check_stability": check_stability,
            }
            failure = (
                build_stabilization_graph(nodes.__getitem__)
                .invoke({}, {"recursion_limit": 3 * remaining + 3})
                .get("output")
            )
            if failure is not None:
                return {"output": failure}
        return {"output": None}

    def record_completion(_graph_state):
        state["component_revisions"] = {
            target_id: {
                "spec": target_revision(
                    run.repository, run.repository.select(target_id)
                ),
                "implementation": implementation_digest(
                    run.repository, run.repository.select(target_id)
                ),
            }
            for target_id in component_tasks
        }
        state["tasks"] = [{**task, "complete": True} for task in state["tasks"]]
        state["implementation_digest"] = implementation_digest(
            run.repository, run.target
        )
        state.update(phase="implementation", status="completed")
        save_target_state(run.repository.root, state)
        return {
            "output": run.response(
                answer="Participating components completed in the candidate worktree.",
                artifacts=list(
                    {
                        reference["id"]: reference for reference in review_artifacts
                    }.values()
                ),
            )
        }

    nodes = {
        "reconcile_specs": reconcile_specs,
        "validate_specs": validate_specs,
        "implement_components": implement_components,
        "implement_local": implement_local,
        "finalize_components": finalize_components,
        "record_completion": record_completion,
    }
    return build_coordination_graph(nodes.__getitem__).invoke({})["output"]
