"""``concorde workflow report``: the workflow result, built only from what the runs recorded.

The steps come from the workspace's workflow record; each step's status, output and error come
from its saved run result. A value a step agent relayed is never read, so the chains the developer
finally reads are the runs' own, with the workflow's link on top. The report is saved next to the
workflow record with a Markdown rendering, which the task level may copy into its decision log.
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime

from ..kernel import errors
from ..execution.runs import load_result, run_state
from ..kernel.schema import validate
from . import catalog, store
from .output import (
    MODULE_ID,
    DECISION,
    DECISION_POINT,
    DEVIATION,
    NOTE,
    declared,
    pending,
)
from .step import (
    NAME,
    STEP_SCHEMA,
    answered,
    busy,
    lost_link,
    unstarted_link,
    workflow_link,
)
from .store import WorkflowError, Workspace

RUN = STEP_SCHEMA["properties"]["run_id"]["anyOf"][0]
KEY = STEP_SCHEMA["properties"]["key"]
S = {"type": "string", "minLength": 1}


def obj(properties: dict, required=None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties if required is None else required),
        "properties": properties,
    }


STEP_ROW = obj(
    {
        "key": KEY,
        "name": NAME,
        "modules": {"type": "array", "items": MODULE_ID},
        "run_id": {"anyOf": [RUN, {"type": "null"}]},
        "status": {"enum": ["ok", "blocked", "failed", "running", "lost", "refused"]},
        "summary": {"anyOf": [S, {"type": "null"}]},
    }
)


def located(item: dict) -> dict:
    """A declared item of the step output convention with the step and run that declared it."""
    return {
        **item,
        "required": ["step", "run_id", *item["required"]],
        "properties": {"step": KEY, "run_id": RUN, **item["properties"]},
    }


# contract.workflows.result, version 9
RESULT_SCHEMA: dict = {
    "$defs": copy.deepcopy(errors.DEFS),
    **obj(
        {
            "workflow": S,
            "workspace": S,
            "mode": {"enum": ["interactive", "no-ask"]},
            "status": {
                "enum": ["ok", "awaiting_decision", "blocked", "failed", "running"]
            },
            "summary": S,
            "steps": {"type": "array", "items": STEP_ROW},
            "superseded": {"type": "array", "items": STEP_ROW},
            "decisions": {"type": "array", "items": located(DECISION)},
            "decision_points": {"type": "array", "items": located(DECISION_POINT)},
            "deviations": {"type": "array", "items": located(DEVIATION)},
            "notes": {"type": "array", "items": located(NOTE)},
            "pending": {"type": "array", "items": located(DECISION_POINT)},
            "problems": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": {"anyOf": [RUN, {"type": "null"}]},
                        "status": {
                            "enum": ["blocked", "failed", "running", "lost", "refused"]
                        },
                        "error": {"$ref": "#/$defs/error"},
                    }
                ),
            },
            "error": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/error"}]},
            "reported_at": {
                "type": "string",
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",
            },
        }
    ),
}


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Row:
    """One recorded step with what its saved result says."""

    def __init__(
        self, space: Workspace, step: dict, workflow: str, superseded: bool = False
    ):
        self.step = step
        self.key = step["key"]
        self.name = step["name"]
        self.run_id = step["run_id"]
        self.settled = answered(step.get("answers"))
        # A step still starting has no run in its node yet (``report`` adopted every run found
        # there): it is running while a run of the workspace may still enter it, and lost
        # otherwise, for its run never started.
        unstarted = store.starting(step)
        if unstarted:
            state = "running" if not superseded and busy(space) else "lost"
        else:
            state = run_state(space.store, self.run_id)
        # One read decides: a result that appears after run_state is read on the next report.
        self.result = (
            load_result(space.store, self.run_id) if state == "finished" else None
        )
        if state == "finished" and self.result is None:
            state = "running"
        self.status = self.result["status"] if self.result is not None else state
        # What the run declared under the step output convention; nothing until it finished, and
        # never read for a superseded step, which contributes nothing but its summary row.
        self.declared = (
            None if superseded else declared((self.result or {}).get("output"))
        )
        self.error = (self.result or {}).get("error") or step.get("error")
        if self.status == "lost":
            self.error = (
                unstarted_link(space, workflow, self.key, self.name)
                if unstarted
                else lost_link(space, workflow, self.key, self.name, self.run_id)
            )
        elif self.status == "running":
            self.error = workflow_link(
                workflow,
                space.name,
                "step_running",
                f"step {self.key} ({self.name}) is starting: its run has not entered the "
                "step's node yet"
                if unstarted
                else f"the {self.name} run {self.run_id} of step {self.key} is still running",
                reason="exhausted",
                explanation="the report was taken before the step finished",
                options=["report again once the run has finished"],
            )

    def value(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "modules": list((self.result or {}).get("modules") or []),
            "run_id": self.run_id,
            "status": self.status,
            "summary": (self.result or {}).get("summary"),
        }


def lost_row(workflow: str, workspace: str, key: str) -> dict:
    return {
        "key": key,
        "name": "unknown",
        "modules": [],
        "run_id": None,
        "status": "lost",
        "summary": None,
        "error": workflow_link(
            workflow,
            workspace,
            "step_lost",
            f"the script reported step {key} without a recorded run: its step agent returned "
            "nothing, or the workflow record refused the step, in which case the script's own "
            "result carries that refusal",
            reason="environment",
            explanation="nothing was recorded for the step, so the workflow cannot tell what "
            "its agent did",
            options=[
                "run the step's command yourself to see why it failed",
                "start the workflow again",
            ],
        ),
    }


def build(
    space: Workspace,
    lost: list[str] = (),
    workflow: str | None = None,
    mode: str | None = None,
) -> dict:
    """The workflow result of a workspace, from its workflow record and its runs' results.

    ``workflow`` and ``mode`` name the script's workflow and mode: a workspace whose first step was
    lost before anything was recorded has no record, and its result is built from them and the
    lost keys alone."""
    record = store.load(space)
    if record is None:
        if not (lost and workflow):
            raise WorkflowError(
                "no_workflow",
                f"workspace {space.name} ran no workflow step; there is nothing to report"
                + (
                    ", and a lost step is reported without a record only when --workflow "
                    "names its workflow"
                    if lost
                    else ""
                ),
            )
        record = {"workflow": workflow, "steps": []}
    elif workflow is not None and workflow != record["workflow"]:
        raise WorkflowError(
            "workflow_conflict",
            f"workspace {space.name} runs the workflow {record['workflow']}, not {workflow}",
        )
    workflow = record["workflow"]
    steps = record["steps"]
    mode = steps[-1]["mode"] if steps else mode or "no-ask"
    rows = [Row(space, step, workflow) for step in steps if not step["superseded"]]
    superseded = [
        Row(space, step, workflow, superseded=True).value()
        for step in steps
        if step["superseded"]
    ]
    keys = {row.key for row in rows}
    extra = [
        lost_row(workflow, space.name, key)
        for key in lost
        if key not in keys
        and store.base_key(key) not in {store.base_key(k) for k in keys}
    ]
    items = {"decisions": [], "decision_points": [], "deviations": [], "notes": []}
    problems = []
    for row in rows:
        where = {"step": row.key, "run_id": row.run_id}
        for field, found in items.items():
            found += [{**where, **item} for item in row.declared[field]]
        if row.status != "ok":
            problems.append(
                {
                    "step": row.key,
                    "run_id": row.run_id,
                    "status": row.status,
                    "error": row.error,
                }
            )
    for item in extra:
        problems.append(
            {
                "step": item["key"],
                "run_id": None,
                "status": "lost",
                "error": item["error"],
            }
        )
    # The procedure's last step, which the part that owns the workflow named when it registered
    # it; a workflow no installed part registered has none, so it can never be ok.
    try:
        last_step = catalog.get(workflow).last_step
    except catalog.WorkflowError:
        last_step = None
    last = rows[-1] if rows else None
    pending_points: list[dict] = []
    stop = None
    evidence = []
    if any(row.status == "running" for row in rows):
        status, code, reason = "running", "step_running", "exhausted"
        stop = [row for row in rows if row.status == "running"]
    elif extra:
        status, code, reason = "failed", "step_lost", "environment"
    elif last is None:
        status, code, reason = "failed", "incomplete", "capability"
    elif last.status in ("failed", "lost", "refused"):
        # The reasons of the error table: a failed step's handling is decided above the
        # workflow, a lost one ended outside it, a refused one needs its command line corrected.
        status, (code, reason) = (
            "failed",
            {
                "failed": ("step_failed", "decision"),
                "lost": ("step_lost", "environment"),
                "refused": ("step_refused", "input"),
            }[last.status],
        )
        stop = [last]
    elif last.status == "blocked":
        status, code, reason = "blocked", "step_blocked", "decision"
        stop = [last]
    elif last.declared["blocking"] is not None:
        status, code, reason = "blocked", "step_blocked", "decision"
        blocking = last.declared["blocking"]
        evidence = [
            errors.evidence(
                "blocking", f"{last.key} {blocking['code']}", blocking["detail"]
            )
        ]
    elif mode == "interactive" and pending(last.declared, last.settled):
        status, code, reason = "awaiting_decision", "awaiting_decision", "decision"
        where = {"step": last.key, "run_id": last.run_id}
        pending_points = [
            {**where, **item} for item in pending(last.declared, last.settled)
        ]
        evidence = [
            errors.evidence(
                "pending", f"{point['step']} {point['id']}", point["question"]
            )
            for point in pending_points
        ]
    elif last_step is not None and store.base_key(last.key) == last_step:
        status, code, reason = "ok", None, None
    else:
        status, code, reason = "failed", "incomplete", "capability"
    summary = summarize(workflow, space.name, status, rows, items, problems)
    error = None
    if status != "ok":
        causes = [row.error for row in (stop or []) if row.error] + [
            item["error"] for item in extra
        ]
        detail = {
            "running": "the workflow is still running a step",
            "failed": "the workflow stopped at a step that failed, was refused or was lost",
            "blocked": "the workflow stopped at a blocked step",
            "awaiting_decision": f"the workflow stopped for {len(pending_points)} decision "
            "point(s) to be settled above the task",
        }[status]
        if code == "incomplete":
            detail = (
                "the workflow's steps end after "
                + (f"step {last.key} ({last.name})" if last else "no step")
                + (
                    f" without reaching its last step, {last_step}"
                    if last_step is not None
                    else f", and no installed part registers the workflow {workflow}, "
                    "so it has no last step to reach"
                )
            )
        error = workflow_link(
            workflow,
            space.name,
            code,
            f"{detail}: {summary}",
            reason=reason,
            explanation={
                "decision": "whether to answer, repair, retry or give up is decided above the "
                "workflow, by the task level or those it escalates to",
                "environment": "a step ended without a result the workflow could read",
                "input": "the step's run could not start, and only its workflow script or "
                "arguments, corrected above the workflow, can change that",
                "capability": "the workflow's record does not show the procedure reaching its "
                "end, and it cannot run the missing steps from a report",
                "exhausted": "the report was taken before the procedure ended",
            }[reason],
            evidence=evidence,
            options={
                "awaiting_decision": [
                    (
                        "have every pending point settled above the task, by the main agent "
                        "where its authority covers it and otherwise by the developer, and start "
                        "the workflow again with the answers keyed by step"
                    )
                ],
            }.get(
                status,
                [
                    (
                        "read the cause, repair or answer, and start the workflow again with "
                        "retry for the failed step"
                    )
                ],
            ),
            causes=causes,
        )
    return {
        "workflow": workflow,
        "workspace": space.name,
        "mode": mode,
        "status": status,
        "summary": summary,
        "steps": [row.value() for row in rows]
        + [{k: v for k, v in item.items() if k != "error"} for item in extra],
        "superseded": superseded,
        **items,
        "pending": pending_points,
        "problems": problems,
        "error": error,
        "reported_at": now(),
    }


def summarize(workflow, workspace, status, rows, declared, problems) -> str:
    ran = ", ".join(f"{row.key} {row.status}" for row in rows) or "no step"
    return (
        f"workflow {workflow} of workspace {workspace} is {status} after {ran}; "
        f"{len(problems)} problem(s), {len(declared['decisions'])} decision(s), "
        f"{len(declared['decision_points'])} decision point(s), "
        f"{len(declared['deviations'])} deviation(s), {len(declared['notes'])} note(s)"
    )


def rendered(result: dict) -> str:
    """The result as a Markdown section, for the task level's decision log."""
    lines = [
        (
            f"\n## Workflow {result['workflow']} report: {result['status']}, "
            f"{result['reported_at']}\n\n{result['summary']}\n"
        )
    ]
    if result["decisions"]:
        lines.append("\nDecisions:\n\n")
        lines += [
            f"- {d['id']} ({d['step']}, {d['decided_by']}): {d['question']} Decided "
            f"{d['decision']!r}: {d['reason']}\n"
            for d in result["decisions"]
        ]
    if result["decision_points"]:
        lines.append("\nDecision points:\n\n")
        lines += [
            f"- {p['id']} ({p['step']}, {p['kind']}"
            + (f", {p['module']}" if p.get("module") else "")
            + f"): {p['question']} Options: {'; '.join(p['options']) or '(none)'}. "
            f"Recommendation: {p['recommendation']}\n"
            for p in result["decision_points"]
        ]
    if result["deviations"]:
        lines.append("\nDeviations:\n\n")
        lines += [
            f"- {d['subject']} ({d['step']}"
            + (f", {d['module']}" if d.get("module") else "")
            + f"): intended {d['intended']}; observed {d['observed']}\n"
            for d in result["deviations"]
        ]
    if result["notes"]:
        lines.append("\nNotes:\n\n")
        lines += [
            f"- {n['kind']} ({n['step']}): {n['text']}\n" for n in result["notes"]
        ]
    for problem in result["problems"]:
        lines.append(
            f"\nProblem at {problem['step']} ({problem['status']}):\n\n"
            f"{errors.render(problem['error'])}\n"
        )
    if result["error"]:
        lines.append(
            f"\n```json\n{json.dumps(result['error'], indent=2, ensure_ascii=False)}\n```\n"
        )
    return "".join(lines)


def report(
    space: Workspace,
    lost: list[str] = (),
    workflow: str | None = None,
    mode: str | None = None,
) -> dict:
    """Build, check and save the workflow result of a workspace with its rendering, holding its
    workflow lock; ``WorkspaceRetired`` when the workspace was retired meanwhile.

    Every step still starting whose run entered its node gets that run, and every step whose run
    ended by now has its node ended with it, before the result is built."""
    with store.step_lock(space):
        record = store.load(space)
        for step in (record or {}).get("steps", []):
            if store.starting(step):
                store.adopt(space, step)
            if step["run_id"]:
                state = run_state(space.store, step["run_id"])
                lost_now = (
                    lost_link(
                        space,
                        record["workflow"],
                        step["key"],
                        step["name"],
                        step["run_id"],
                    )
                    if state == "lost"
                    else None
                )
                store.end_step(
                    space,
                    step,
                    state,
                    load_result(space.store, step["run_id"]),
                    lost_now,
                )
        result = build(space, lost, workflow, mode)
        validate(result, RESULT_SCHEMA)
        store.record_report(space, result, rendered(result))
    return result


__all__ = ["RESULT_SCHEMA", "build", "report"]
