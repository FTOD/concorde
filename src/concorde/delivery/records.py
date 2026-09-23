"""Delivery's provider section of the change status.

Loading this module declares the ``delivery`` section with Candidate worktrees. It holds the
delivery receipt, which records publication, cleanup and the primary merge, and the manual merge
record of a merge the developer made with ordinary Git.
"""

from __future__ import annotations

from ..harness.change_worktree import declare_section, put_section, section
from ..spec.typed_data import obj, register

_RECORD = {"anyOf": [{"type": "object", "additionalProperties": {}}, {"type": "null"}]}
DELIVERY_RECORDS = obj({"receipt": _RECORD, "manual_merge": _RECORD})
SECTION = "delivery"
SECTION_TYPE = "concorde-delivery-records"
register(SECTION_TYPE, 1, DELIVERY_RECORDS)
declare_section(SECTION, SECTION_TYPE)


def delivery_records(change: dict) -> dict:
    """The mutable delivery section of ``change``, created empty when absent."""
    return section(change, SECTION) or put_section(
        change, SECTION, {"receipt": None, "manual_merge": None}
    )


def receipt(change: dict | None) -> dict | None:
    """The delivery receipt of ``change``, or None before delivery."""
    return (section(change, SECTION) or {}).get("receipt")


def manual_merge(change: dict | None) -> dict | None:
    """The manual merge record of ``change``, or None."""
    return (section(change, SECTION) or {}).get("manual_merge")
