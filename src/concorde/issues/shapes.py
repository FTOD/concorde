"""Closed shapes of Issue reports, provenance, records and the Issue typed values.

Issues owns these shapes and registers its typed values with Spec tooling when this module is
loaded; the store and the bookkeeping command use the same declarations.
"""

from __future__ import annotations

from ..spec.typed_data import DIGEST, PATH, STRING, array, obj, register

ISSUE_ID = {**STRING, "pattern": r"^I-[0-9a-f]{32}$"}
NULLABLE_STRING = {"anyOf": [STRING, {"type": "null"}]}
GAP_KINDS = ("implementation-spec-mismatch", "spec-conflict", "missing-contract")
# Who may handle a problem without the level above, weakest first: a suggestion (advisory), an
# obvious fix AI makes alone, a preferred fix AI makes and reports, a decision the level above takes.
TIERS = ("suggestion", "obvious-fix", "preferred-fix", "decision-needed")
# The tiers that block: every tier but a suggestion.
BLOCKING = TIERS[1:]
# How much a problem matters, most severe first; orthogonal to its tier.
SEVERITIES = ("critical", "high", "medium", "low")
EVIDENCE = obj({"path": PATH, "description": STRING})
# Where a report was observed when that is another project than the one recording it: evidence
# paths are then relative to that project.
ORIGIN = obj(
    {
        "project": {**STRING, "pattern": r"^/.*"},
        "head": NULLABLE_STRING,
        "concorde_commit": NULLABLE_STRING,
        "task": NULLABLE_STRING,
    }
)
REPORT_FIELDS = {
    "report_key": STRING,
    "tier": {"enum": list(TIERS)},
    "severity": {"enum": list(SEVERITIES)},
    "type": {"enum": ["bug", "gap", "limitation"]},
    "subtype": {"anyOf": [{"enum": list(GAP_KINDS)}, {"type": "null"}]},
    "title": STRING,
    "description": STRING,
    "impact": STRING,
    "basis": STRING,
    "owner_target_id": NULLABLE_STRING,
    "evidence": array(EVIDENCE),
    "origin": ORIGIN,
    # An error link of the Framework's error contract, checked against it by the store.
    "error_chain": {"type": "object", "additionalProperties": {}},
    "issue_id": ISSUE_ID,
    "expected_revision": DIGEST,
}
OPTIONAL = ("origin", "error_chain", "issue_id", "expected_revision")
# What a caller submits: every report carries its tier and its severity.
REPORT = obj(REPORT_FIELDS, OPTIONAL)
# A report as a record stores it: records of schema version 2, written before tiers, hold reports
# without either, and records of version 3, written before severities, reports without a
# severity, which the store never rewrites; version 4 requires both of every report.
STORED_REPORT = obj(REPORT_FIELDS, ("tier", "severity", *OPTIONAL))
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
OBSERVATION = obj(
    {"id": DIGEST, "created_at": STRING, "report": STORED_REPORT, "source": PROVENANCE}
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
# The version of the records the store creates.
RECORD_VERSION = 4
# The first record version whose reports carry their tier.
TIERED_VERSION = 3
RECORD = obj(
    {
        "schema_version": {"enum": [2, TIERED_VERSION, RECORD_VERSION]},
        "id": ISSUE_ID,
        "status": {"enum": ["open", "closed"]},
        "reports": {**array(OBSERVATION), "minItems": 1},
        "dispositions": array(DISPOSITION),
    }
)

register("concorde-issue-report", 3, REPORT)
register("concorde-issue-receipt", 2, RECEIPT)
