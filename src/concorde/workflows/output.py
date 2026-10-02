"""The step output convention: what a run's output declares for a workflow.

Any Operation or execution command may give its output a top-level ``workflow`` object with its
decision points, decisions, deviations and notes, whether it blocks the procedure, and the ``data``
a workflow script reads. Workflows reads nothing else of a run's output, so it knows no Operation
or command by name; ``declared`` reads the object, ``step_output`` builds one for a producer.
"""

from __future__ import annotations

from ..kernel.refusal import KernelError
from ..kernel.schema import validate

ITEM_ID = {"type": "string", "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"}
TEXT = {"type": "string", "minLength": 1}
TEXTS = {"type": "array", "items": TEXT}
MODULE_ID = {
    "type": "string",
    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$",
}


def obj(properties: dict, required) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(required),
        "properties": properties,
    }


DECISION_POINT = obj(
    {
        "id": ITEM_ID,
        "kind": {"enum": ["decision", "question"]},
        "question": TEXT,
        "options": TEXTS,
        "recommendation": TEXT,
        "module": MODULE_ID,
    },
    ["id", "kind", "question", "options", "recommendation"],
)
DECISION = obj(
    {
        "id": ITEM_ID,
        "question": TEXT,
        "options": TEXTS,
        "decision": TEXT,
        "reason": TEXT,
        "decided_by": {"enum": ["worker", "main-agent", "developer"]},
        "module": MODULE_ID,
    },
    ["id", "question", "decision", "reason", "decided_by"],
)
DEVIATION = obj(
    {
        "subject": TEXT,
        "intended": TEXT,
        "observed": TEXT,
        "point": ITEM_ID,
        "module": MODULE_ID,
    },
    ["subject", "intended", "observed"],
)
NOTE = obj(
    {
        "kind": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "text": TEXT,
        "data": {"type": "object"},
    },
    ["kind", "text", "data"],
)
BLOCKING = obj(
    {"code": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}, "detail": TEXT},
    ["code", "detail"],
)
ANSWER = obj(
    {
        "id": ITEM_ID,
        "question": TEXT,
        "answer": TEXT,
        "answered_by": {"enum": ["main-agent", "developer"]},
    },
    ["id", "question", "answer", "answered_by"],
)
# contract.workflows.step-output, version 1
STEP_OUTPUT_SCHEMA: dict = {
    **obj(
        {
            "decision_points": {"type": "array", "items": DECISION_POINT},
            "decisions": {"type": "array", "items": DECISION},
            "deviations": {"type": "array", "items": DEVIATION},
            "notes": {"type": "array", "items": NOTE},
            "blocking": {"anyOf": [{"type": "null"}, BLOCKING]},
            "data": {"type": "object"},
        },
        ["decision_points", "decisions", "deviations", "notes", "blocking", "data"],
    ),
    "$defs": {"answer": ANSWER},
}

NOTHING = {
    "decision_points": [],
    "decisions": [],
    "deviations": [],
    "notes": [],
    "blocking": None,
    "data": {},
}


class StepOutputError(ValueError):
    """A run's ``workflow`` object that breaks the step output convention."""


def step_output(
    *,
    decision_points=(),
    decisions=(),
    deviations=(),
    notes=(),
    blocking: dict | None = None,
    data: dict | None = None,
) -> dict:
    """A ``workflow`` object for a run's output, checked against the convention."""
    value = {
        "decision_points": list(decision_points),
        "decisions": list(decisions),
        "deviations": list(deviations),
        "notes": list(notes),
        "blocking": blocking,
        "data": dict(data or {}),
    }
    validate(value, STEP_OUTPUT_SCHEMA)
    return value


def declared(output) -> dict:
    """What a run's output declares for a workflow: its ``workflow`` object, or nothing declared
    when the output has none. ``StepOutputError`` when the object breaks the convention."""
    if not isinstance(output, dict) or "workflow" not in output:
        return dict(NOTHING)
    value = output["workflow"]
    try:
        validate(value, STEP_OUTPUT_SCHEMA)
    except KernelError as error:
        raise StepOutputError(
            f"the run's output declares a workflow object that breaks "
            f"contract.workflows.step-output: {error}"
        ) from None
    return value


def pending(value: dict, settled=frozenset()) -> list[dict]:
    """The declared decision points that no answer settled."""
    return [item for item in value["decision_points"] if item["id"] not in settled]


__all__ = [
    "STEP_OUTPUT_SCHEMA",
    "StepOutputError",
    "declared",
    "pending",
    "step_output",
]
