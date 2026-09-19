"""Task authoring: implementation acceptance tasks derived from the accepted plan."""

from __future__ import annotations

import copy

from ..harness.change_worktree import (
    STATE_PATH,
    progress,
    read_change,
    save_change,
    save_target_state,
    target_state,
)
from ..harness.revisions import target_revision
from ..implementation.implement import component_intent
from ..review.review import require_spec_review
from ..spec.repository import SpecError, digest, read_file
from ..spec.typed_data import (
    artifact,
    canonical,
    decode,
    typed,
    validate_typed,
    verify_artifacts,
)


def tasks(run) -> dict:
    require_spec_review(run)
    if not run.work_directory:
        raise SpecError("task authoring requires a managed change", "missing_change")
    if not run.host.coordinated:
        progress(run.repository.root, phase="tasks", status="active", invalidate=True)
    state = target_state(run.repository.root, run.target.id, run.task.get("focus_id"))
    scope_repair = run.task.get("repair_task_scope")
    run.check_state(state, allow_stale_spec=bool(scope_repair))
    if not state["plan"]:
        raise SpecError("tasks require an authored plan", "missing_plan")
    change = read_change(run.repository.root, required=True)
    repair = change.get("graph", {}).get(run.target.id, {}).get("repair")
    if scope_repair and (
        not state["tasks"]
        or scope_repair["tasks_digest"] != digest(canonical(state["tasks"]).encode())
        or all(task["complete"] for task in state["tasks"])
        or repair is not None
    ):
        raise SpecError(
            "task scope repair requires the exact current incomplete task list and no pending review repair",
            "incompatible_handoff",
        )
    reserved_ids = {
        t["id"] for entry in state.get("task_history", []) for t in entry["tasks"]
    }
    if scope_repair or repair is not None:
        reserved_ids.update(t["id"] for t in state["tasks"])
    inputs = (
        typed("concorde-plan-artifact", {"plan": state["plan"]}),
        typed(
            "concorde-task-identity-constraints",
            {"reserved_task_ids": sorted(reserved_ids)},
        ),
    )
    if scope_repair:
        inputs = (
            *inputs,
            typed(
                "concorde-implementation-task",
                {"plan": state["plan"], "tasks": state["tasks"]},
            ),
            typed(
                "concorde-task-scope-feedback",
                {**scope_repair, "reason": "implementation_boundary"},
            ),
        )
    if repair is not None:
        verify_artifacts(run.repository.root, repair["artifact"])
        review_value = validate_typed(
            decode(read_file(run.repository.root, repair["artifact"]["path"]).decode()),
            "concorde-review-result",
        )
        review_data = review_value["data"]
        if (
            review_data["review_mode"] != "code"
            or review_data["target_id"] != run.target.id
            or review_data["status"] != "findings"
        ):
            raise SpecError(
                "repair review artifact does not match this target's blocking code-review findings",
                "incompatible_handoff",
            )
        inputs = (
            *inputs,
            typed(
                "concorde-implementation-task",
                {"plan": state["plan"], "tasks": state["tasks"]},
            ),
            review_value,
        )
    result = run.stage("concorde-tasks", inputs=inputs, defer_gap_resolution=True)
    if result["outcome"] not in {"completed", "sufficient"}:
        return run.response(
            result["outcome"], result["answer"], blockers=result["blockers"]
        )
    if run.host.mode == "describe-policy":
        return run.response("described")
    tasks = result["tasks"]
    collisions = sorted({t["id"] for t in tasks} & reserved_ids)
    if collisions:
        raise SpecError(
            "task IDs are reserved by retained task history or the list being replaced: "
            + ", ".join(collisions),
            "invalid_completion",
        )
    if (
        not tasks
        or len({t["id"] for t in tasks}) != len(tasks)
        or any(t["complete"] for t in tasks)
    ):
        raise SpecError(
            "tasks must be nonempty, uniquely identified and initially incomplete",
            "invalid_completion",
        )
    for task in tasks:
        run.repository.select(task["target_id"])
        if task["target_id"] not in {
            run.target.id,
            *run.target.uses,
            *(child.id for child in run.repository.children(run.target)),
        }:
            raise SpecError(
                "Module tasks may target only this Module, its declared dependencies or direct submodules",
                "permission_denied",
            )
    prior_coordination = None
    if scope_repair and state.get("coordination"):
        old_targets = {
            task["target_id"]
            for task in state["tasks"]
            if task["target_id"] != run.target.id
        }
        grouped = {}
        for task in tasks:
            if task["target_id"] != run.target.id:
                grouped.setdefault(task["target_id"], []).append(task)
        if set(grouped) != old_targets:
            raise SpecError(
                "task scope repair must preserve component routing",
                "incompatible_handoff",
            )
        replacements = {
            key: component_intent(items)
            for key, items in grouped.items()
            if key in state["coordination"]
            and component_intent(items) != state["coordination"][key]["task"]
        }
        for key in replacements:
            record = state["coordination"][key]
            owners = set()
            pending = [(key, record["task"])]
            while pending:
                owner, intent = pending.pop()
                if (owner, intent) in owners:
                    continue
                owners.add((owner, intent))
                component = change["targets"].get(owner, {})
                if component.get("task") == intent:
                    for child, nested in component.get("coordination", {}).items():
                        declarations = [
                            item
                            for item in component.get("tasks", [])
                            if item["target_id"] == child
                        ]
                        if declarations and nested["task"] != component_intent(
                            declarations
                        ):
                            raise SpecError(
                                "component coordination differs from its accepted task list",
                                "incompatible_handoff",
                            )
                        pending.append((child, nested["task"]))
            history = [
                item
                for item in change.get("issue_blockers", [])
                if item["target_id"] in {owner for owner, _ in owners}
                and item["scope_id"] == "module:" + item["target_id"]
            ]
            # Match immutable observations, not duplicated free text or a previous task label.
            unresolved_cache = any(
                not any(
                    item["status"] == "resolved"
                    and item["blocker"]["issue_id"] == blocker.get("issue_id")
                    and item["blocker"]["report_id"] == blocker.get("report_id")
                    for item in history
                )
                for blocker in record.get("blockers", [])
            )
            if unresolved_cache or any(item["status"] == "open" for item in history):
                raise SpecError(
                    "resolve the component's contract gaps before repairing its task boundary",
                    "spec_incomplete",
                )
        prior_coordination = copy.deepcopy(state["coordination"])
        for key, intent in replacements.items():
            # Keep current Spec bytes and unaffected participants. The changed
            # child intent makes its ordinary loop re-review and replan; no
            # child task or completion evidence is rewritten here.
            state["coordination"][key].update(
                task=intent,
                implementation_status="pending",
                implementation_digest=None,
                outcome=None,
            )
        state.pop("component_revisions", None)
    if repair is not None:
        state.setdefault("task_history", []).append(
            {
                "iteration": repair["iteration"],
                "tasks": state["tasks"],
                "implementation_digest": state.get("implementation_digest"),
            }
        )
        state["repair_review"] = repair["artifact"]
    if scope_repair:
        state.setdefault("task_history", []).append(
            {
                "reason": "implementation_boundary",
                "tasks_digest": scope_repair["tasks_digest"],
                "tasks": state["tasks"],
                "implementation_digest": state.get("implementation_digest"),
                "spec_digest": state["spec_digest"],
            }
        )
        if prior_coordination is not None:
            state["task_history"][-1]["coordination"] = prior_coordination
        state["spec_digest"] = target_revision(run.repository, run.target)
    state.update(
        tasks=tasks,
        checks=[],
        implementation_digest=None,
        phase="tasks",
        status="active",
    )
    save_target_state(run.repository.root, state)
    if repair is not None:
        change = read_change(run.repository.root, required=True)
        change["graph"][run.target.id]["repair"] = None
        save_change(run.repository.root, change)
    run.record_gaps("tasks", [])
    return run.response(
        answer=result["answer"],
        artifacts=[artifact(run.repository.root, "change", STATE_PATH)],
    )
