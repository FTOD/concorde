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

from .. import errors
from ..execution.runs import load_result, run_state
from ..spec.schema import validate
from . import store
from .step import (
    NAME,
    STEP_SCHEMA,
    answered,
    decision_points,
    lost_link,
    workflow_link,
)
from .store import WorkflowError, Workspace

RUN = STEP_SCHEMA["properties"]["run_id"]["anyOf"][0]
KEY = STEP_SCHEMA["properties"]["key"]
MODULE_ID = {
    "type": "string",
    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$",
}
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
# contract.workflows.result, version 7
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
            "decisions": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": RUN,
                        "id": {"type": "string", "pattern": "^d\\.[a-z0-9-]+$"},
                        "module": MODULE_ID,
                        "question": S,
                        "options": {"type": "array", "minItems": 2, "items": S},
                        "chosen": S,
                        "reason": S,
                        "decided_by": {"enum": ["worker", "main-agent", "developer"]},
                    }
                ),
            },
            "open_questions": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": RUN,
                        "id": {"type": "string", "pattern": "^q\\.[a-z0-9-]+$"},
                        "module": MODULE_ID,
                        "subject": S,
                        "observed": S,
                        "evidence": {"type": "array", "minItems": 1, "items": S},
                        "why_uncertain": S,
                        "options": {"type": "array", "minItems": 1, "items": S},
                        "recommendation": S,
                    }
                ),
            },
            "deviations": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": RUN,
                        "module": MODULE_ID,
                        "question": {"type": "string", "pattern": "^q\\.[a-z0-9-]+$"},
                        "intended": S,
                        "observed": S,
                    }
                ),
            },
            "reviews": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": RUN,
                        "verdict": {
                            "enum": ["accepted", "changes_required", "incomplete"]
                        },
                        "modules": {"type": "array", "items": {"type": "object"}},
                    }
                ),
            },
            "proposed_checks": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": RUN,
                        "id": {
                            "type": "string",
                            "pattern": "^check\\.[a-z0-9-]+(?:\\.[a-z0-9-]+)*$",
                        },
                        "module": MODULE_ID,
                        "argv": {"type": "array", "minItems": 1, "items": S},
                        "env": {"type": "object", "additionalProperties": S},
                        "when": {"enum": ["always", "readiness"]},
                        "timeout_seconds": {"type": "integer", "minimum": 1},
                        "inputs": {"type": "array", "items": S},
                        "reason": S,
                    },
                    required=[
                        "step",
                        "run_id",
                        "id",
                        "module",
                        "argv",
                        "timeout_seconds",
                        "inputs",
                        "reason",
                    ],
                ),
            },
            "pending": {
                "type": "array",
                "items": obj(
                    {
                        "step": KEY,
                        "run_id": RUN,
                        "kind": {"enum": ["decision", "open_question"]},
                        "id": {"type": "string", "pattern": "^[dq]\\.[a-z0-9-]+$"},
                        "module": MODULE_ID,
                        "question": S,
                        "options": {"type": "array", "items": S},
                        "recommendation": S,
                    }
                ),
            },
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
# The procedure's last step: a workflow whose last current step is this and ok is done.
LAST_STEP = {"brownfield": "delivery"}


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Row:
    """One recorded step with what its saved result says."""

    def __init__(self, space: Workspace, step: dict, workflow: str):
        self.step = step
        self.key = step["key"]
        self.name = step["name"]
        self.run_id = step["run_id"]
        self.settled = answered(step.get("answers"))
        state = run_state(space.store, self.run_id)
        # One read decides: a result that appears after run_state is read on the next report.
        self.result = (
            load_result(space.store, self.run_id) if state == "finished" else None
        )
        if state == "finished" and self.result is None:
            state = "running"
        self.status = self.result["status"] if self.result is not None else state
        self.output = (self.result or {}).get("output") or {}
        self.error = (self.result or {}).get("error") or step.get("error")
        if self.status == "lost":
            self.error = lost_link(space, workflow, self.key, self.name, self.run_id)
        elif self.status == "running":
            self.error = workflow_link(
                workflow,
                space.name,
                "step_running",
                f"the {self.name} run {self.run_id} of step {self.key} is still running",
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


def pending_points(workflow: str, row: Row) -> list[dict]:
    points = []
    for item in row.output.get("open_questions") or []:
        if item["id"] in row.settled:
            continue
        points.append(
            {
                "step": row.key,
                "run_id": row.run_id,
                "kind": "open_question",
                "id": item["id"],
                "module": item["module"],
                "question": f"{item['subject']}: {item['observed']}",
                "options": item["options"],
                "recommendation": item["recommendation"],
            }
        )
    if row.name == "survey":
        for item in row.output.get("decisions") or []:
            if item["decided_by"] == "worker" and item["id"] not in row.settled:
                points.append(
                    {
                        "step": row.key,
                        "run_id": row.run_id,
                        "kind": "decision",
                        "id": item["id"],
                        "module": item["module"],
                        "question": item["question"],
                        "options": item["options"],
                        "recommendation": f"the worker chose {item['chosen']!r}: "
                        f"{item['reason']}",
                    }
                )
    return points


def build(space: Workspace, lost: list[str] = ()) -> dict:
    """The workflow result of a workspace, from its workflow record and its runs' results."""
    record = store.load(space)
    if record is None:
        raise WorkflowError(
            "no_workflow",
            f"workspace {space.name} ran no workflow step; there is nothing to report",
        )
    workflow = record["workflow"]
    steps = record["steps"]
    mode = steps[-1]["mode"] if steps else "no-ask"
    rows = [Row(space, step, workflow) for step in steps if not step["superseded"]]
    superseded = [
        Row(space, step, workflow).value() for step in steps if step["superseded"]
    ]
    keys = {row.key for row in rows}
    extra = [
        lost_row(workflow, space.name, key)
        for key in lost
        if key not in keys
        and store.base_key(key) not in {store.base_key(k) for k in keys}
    ]
    decisions, questions, deviations, reviews, checks, problems = [], [], [], [], [], []
    for row in rows:
        where = {"step": row.key, "run_id": row.run_id}
        if row.status in ("ok", "blocked", "failed") and row.result is not None:
            decisions += [
                {**where, **item} for item in row.output.get("decisions") or []
            ]
            questions += [
                {**where, **item} for item in row.output.get("open_questions") or []
            ]
            deviations += [
                {**where, **item} for item in row.output.get("deviations") or []
            ]
            if row.name == "spec_review" and row.output.get("verdict"):
                reviews.append(
                    {
                        **where,
                        "verdict": row.output["verdict"],
                        "modules": row.output.get("modules") or [],
                    }
                )
            if row.name == "survey":
                checks += [{**where, **item} for item in row.output.get("checks") or []]
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
    last = rows[-1] if rows else None
    pending: list[dict] = []
    stop = None
    if any(row.status == "running" for row in rows):
        status, code, reason = "running", "step_running", "exhausted"
        stop = [row for row in rows if row.status == "running"]
    elif extra:
        status, code, reason = "failed", "step_lost", "environment"
    elif last is None:
        status, code, reason = "failed", "incomplete", "capability"
    elif last.status in ("failed", "lost", "refused"):
        status, code, reason = (
            "failed",
            {
                "failed": "step_failed",
                "lost": "step_lost",
                "refused": "step_refused",
            }[last.status],
            "decision",
        )
        stop = [last]
    elif last.status == "blocked":
        status, code, reason = "blocked", "step_blocked", "decision"
        stop = [last]
    elif mode == "interactive" and decision_points(
        last.name, last.output, last.settled
    ):
        status, code, reason = "awaiting_decision", "awaiting_decision", "decision"
        pending = pending_points(workflow, last)
    elif last.name == LAST_STEP.get(workflow, "delivery"):
        status, code, reason = "ok", None, None
    else:
        status, code, reason = "failed", "incomplete", "capability"
    summary = summarize(
        workflow, space.name, status, rows, decisions, questions, problems, checks
    )
    error = None
    if status != "ok":
        causes = [row.error for row in (stop or []) if row.error] + [
            item["error"] for item in extra
        ]
        detail = {
            "running": "the workflow is still running a step",
            "failed": "the workflow stopped at a step that failed, was refused or was lost",
            "blocked": "the workflow stopped at a blocked step",
            "awaiting_decision": f"the workflow stopped for {len(pending)} decision point(s) "
            "to be settled above the task",
        }[status]
        if code == "incomplete":
            detail = (
                "the workflow's steps end after "
                + (f"step {last.key} ({last.name})" if last else "no step")
                + f" without reaching its last step, {LAST_STEP.get(workflow, 'delivery')}"
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
                "capability": "the workflow's record does not show the procedure reaching its "
                "end, and it cannot run the missing steps from a report",
                "exhausted": "the report was taken before the procedure ended",
            }[reason],
            evidence=[
                errors.evidence(
                    "pending",
                    f"{point['step']} {point['id']}",
                    point["question"],
                )
                for point in pending
            ],
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
        "decisions": decisions,
        "open_questions": questions,
        "deviations": deviations,
        "reviews": reviews,
        "proposed_checks": checks,
        "pending": pending,
        "problems": problems,
        "error": error,
        "reported_at": now(),
    }


def summarize(
    workflow, workspace, status, rows, decisions, questions, problems, checks
) -> str:
    ran = ", ".join(f"{row.key} {row.status}" for row in rows) or "no step"
    return (
        f"workflow {workflow} of workspace {workspace} is {status} after {ran}; "
        f"{len(problems)} problem(s), {len(decisions)} decision(s), "
        f"{len(questions)} open question(s), {len(checks)} proposed check(s)"
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
            f"- {d['id']} ({d['step']}, {d['decided_by']}): {d['question']} Chose "
            f"{d['chosen']!r}: {d['reason']}\n"
            for d in result["decisions"]
        ]
    if result["open_questions"]:
        lines.append("\nOpen questions, written as no promise:\n\n")
        lines += [
            f"- {q['id']} ({q['module']}): {q['subject']}. Observed: {q['observed']} "
            f"Uncertain because {q['why_uncertain']} Recommendation: {q['recommendation']}\n"
            for q in result["open_questions"]
        ]
    if result["deviations"]:
        lines.append("\nDeviations between stated intent and code:\n\n")
        lines += [
            f"- {d['question']} ({d['module']}): intended {d['intended']}; observed "
            f"{d['observed']}\n"
            for d in result["deviations"]
        ]
    for review in result["reviews"]:
        lines.append(f"\nSpec review {review['run_id']}: {review['verdict']}\n")
    if result["proposed_checks"]:
        lines.append("\nProposed checks, not configured:\n\n")
        lines += [
            f"- {c['id']} for {c['module']}: `{' '.join(c['argv'])}` ({c['reason']})\n"
            for c in result["proposed_checks"]
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


def report(space: Workspace, lost: list[str] = ()) -> dict:
    """Build, check and save the workflow result of a workspace with its rendering."""
    result = build(space, lost)
    validate(result, RESULT_SCHEMA)
    store.record_report(space, result, rendered(result))
    return result


__all__ = ["RESULT_SCHEMA", "build", "report"]
