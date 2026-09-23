"""Closed shapes of Issue observations, provenance, records and the Issue typed values.

Issues owns these shapes and registers its typed values with Spec tooling when this module is
loaded; worker tool schemas and the persistent store use the same declarations.
"""

from __future__ import annotations

from ..spec.typed_data import DIGEST, PATH, STRING, array, obj, register

ISSUE_ID = {**STRING, "pattern": r"I-[0-9a-f]{32}"}
NULLABLE_STRING = {"anyOf": [STRING, {"type": "null"}]}
GAP_KINDS = ("implementation-spec-mismatch", "spec-conflict", "missing-contract")
EVIDENCE = obj({"path": PATH, "description": STRING})
REPORT = obj(
    {
        "report_key": STRING,
        "type": {"enum": ["bug", "gap", "limitation"]},
        "subtype": {"anyOf": [{"enum": list(GAP_KINDS)}, {"type": "null"}]},
        "title": STRING,
        "description": STRING,
        "impact": STRING,
        "basis": STRING,
        "owner_target_id": NULLABLE_STRING,
        "evidence": array(EVIDENCE),
        "issue_id": ISSUE_ID,
        "expected_revision": DIGEST,
    },
    ("issue_id", "expected_revision"),
)
PROVENANCE = obj(
    {
        "invocation_id": STRING,
        "agent": STRING,
        "operation": STRING,
        "phase": STRING,
        "target_id": STRING,
        "context_id": DIGEST,
        "change_id": NULLABLE_STRING,
        "head": NULLABLE_STRING,
    }
)
RECEIPT = obj({"issue_id": ISSUE_ID, "report_id": DIGEST, "path": PATH})
# Task-local judgments reference one immutable observation; they are not another problem record.
BLOCKER = obj({**RECEIPT["properties"], "blocked_step": STRING})
REVIEW_ISSUE = obj(
    {
        **RECEIPT["properties"],
        "severity": {"enum": ["blocking", "advisory"]},
        "affected_task": STRING,
    }
)
OBSERVATION = obj(
    {"id": DIGEST, "created_at": STRING, "report": REPORT, "source": PROVENANCE}
)
DISPOSITION = obj(
    {
        "reason": {"enum": ["resolved", "duplicate", "not-actionable", "reopened"]},
        "note": STRING,
        "evidence": {**array(STRING, unique=True), "minItems": 1},
        "duplicate_of": {"anyOf": [ISSUE_ID, {"type": "null"}]},
        "actor": STRING,
        "created_at": STRING,
    }
)
RECORD = obj(
    {
        "schema_version": {"type": "integer", "const": 2},
        "id": ISSUE_ID,
        "status": {"enum": ["open", "closed"]},
        "reports": {**array(OBSERVATION), "minItems": 1},
        "dispositions": array(DISPOSITION),
    }
)

SELECTION = obj(
    {
        "issue_id": STRING,
        "revision": DIGEST,
        "problem": STRING,
        "type": {"enum": ["bug", "gap", "limitation"]},
        "feedback": {"type": "string"},
        "verification": {"type": "string"},
        "duplicates": array(
            obj({"issue_id": STRING, "revision": DIGEST, "problem": STRING})
        ),
    }
)
CONTEXT = obj(
    {
        "observations": array(
            obj(
                {
                    "receipt": RECEIPT,
                    "description": STRING,
                    "impact": STRING,
                    "basis": STRING,
                }
            )
        )
    }
)

register("concorde-issue-report", 1, REPORT)
register("concorde-issue-receipt", 1, RECEIPT)
register("concorde-issue-selection", 1, SELECTION)
register("concorde-issue-context", 1, CONTEXT)
