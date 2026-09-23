"""Review's typed values and its provider section of the change status.

The reviewer input and stage context, the reviewer's answer and the public review result are
registered with Spec tooling when this module is loaded, and the ``review`` provider section is
declared with Candidate worktrees: the accepted review intents, the required review kinds, the
latest review per Module and kind, and the shared Spec and implementation review records.
"""

from __future__ import annotations

from ..harness.change_worktree import declare_section, put_section, section
from ..issues.shapes import REVIEW_ISSUE
from ..spec.typed_data import DIGEST, PATH, STRING, array, obj, register, typed_schema

NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}
REVISION = obj(
    {
        "spec_digest": DIGEST,
        "implementation_digest": {"anyOf": [DIGEST, {"type": "null"}]},
        "baseline": NULLABLE_ID,
        "head": NULLABLE_ID,
    }
)
REVIEW_INPUT = obj(
    {
        "review_mode": {"enum": ["spec", "code"]},
        "input_digest": DIGEST,
        "revision": REVISION,
        "changes": array(obj({"path": PATH, "patch": {"type": "string"}})),
    }
)
REVIEW_STAGE_CONTEXT = obj(
    {
        "snapshot": typed_schema("concorde-context-snapshot"),
        "review": typed_schema("concorde-review-input"),
    }
)
_STAGE_FIELDS = {
    "context_id": DIGEST,
    "input_digest": DIGEST,
    "review_mode": {"enum": ["spec", "code"]},
    "status": {"enum": ["no_findings", "findings", "incomplete"]},
    "representative_tasks": array(STRING, unique=True),
    "issues": array(REVIEW_ISSUE),
    "answer": STRING,
}
REVIEW_STAGE_RESULT = obj(_STAGE_FIELDS)
# contract.review.result: context_id is null only for an incomplete result without an admitted
# reviewer context.
REVIEW_RESULT = obj(
    {
        **_STAGE_FIELDS,
        "context_id": {"anyOf": [DIGEST, {"type": "null"}]},
        "target_id": STRING,
        "focus_id": NULLABLE_ID,
        "revision": REVISION,
        "semantic_completeness": {"const": "not_proven"},
    }
)

register("concorde-review-input", 1, REVIEW_INPUT)
register("concorde-review-stage-context", 5, REVIEW_STAGE_CONTEXT)
register("concorde-review-stage-result", 2, REVIEW_STAGE_RESULT)
register("concorde-review-result", 3, REVIEW_RESULT)

# The review section. Each map is keyed by Module identity.
_MAP = {"type": "object", "additionalProperties": {}}
REVIEW_RECORDS = obj(
    {
        "intents": _MAP,
        "requirements": _MAP,
        "reviews": _MAP,
        "shared_spec_reviews": _MAP,
        "shared_implementation_reviews": _MAP,
    }
)
SECTION = "review"
SECTION_TYPE = "concorde-review-records"
register(SECTION_TYPE, 1, REVIEW_RECORDS)
declare_section(SECTION, SECTION_TYPE)


def review_records(change: dict) -> dict:
    """The mutable review section of ``change``, created empty when absent."""
    return section(change, SECTION) or put_section(
        change, SECTION, {name: {} for name in REVIEW_RECORDS["properties"]}
    )


def recorded(change: dict | None, name: str) -> dict:
    """One map of the review section of ``change``; empty when nothing is recorded."""
    return (section(change, SECTION) or {}).get(name, {})
