"""Validation's provider section of the change status.

Loading this module declares the ``validation`` section with Candidate worktrees. It holds the
validated deliverable tree of a ready change and the evidence of a direct candidate, which has no
planned progress entry to hold it. A planned Module's evidence lives in its progress entry, which
Validation updates through Planning.
"""

from __future__ import annotations

from ..harness.change_worktree import declare_section, put_section, section
from ..planning.records import targets
from ..spec.typed_data import STRING, obj, register

VALIDATION_RECORDS = obj(
    {
        "validated_tree": {"anyOf": [STRING, {"type": "null"}]},
        "evidence": {
            "anyOf": [
                {"type": "object", "additionalProperties": {}},
                {"type": "null"},
            ]
        },
    }
)
SECTION = "validation"
SECTION_TYPE = "concorde-validation-records"
register(SECTION_TYPE, 1, VALIDATION_RECORDS)
declare_section(SECTION, SECTION_TYPE)


def validation_records(change: dict) -> dict:
    """The mutable validation section of ``change``, created empty when absent."""
    return section(change, SECTION) or put_section(
        change, SECTION, {"validated_tree": None, "evidence": None}
    )


def validated_tree(change: dict | None) -> str | None:
    """The deliverable tree the change was last validated ready for, or None."""
    return (section(change, SECTION) or {}).get("validated_tree")


def direct_evidence(change: dict | None) -> dict | None:
    """The recorded validation evidence of a direct candidate, or None."""
    return (section(change, SECTION) or {}).get("evidence")


def recorded_evidence(change: dict) -> dict | None:
    """The evidence a completion check of the change's own Module reads: the owner's planned
    progress entry, or a direct candidate's validation evidence."""
    return targets(change).get(change.get("target_id")) or direct_evidence(change)


def planned_work(change: dict) -> dict:
    """The change's recorded Module work, by Module, as Planning keeps it."""
    return targets(change)
