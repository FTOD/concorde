"""Issue solving's provider section of the change status.

Loading this module declares the ``issue-solving`` section with Candidate worktrees. It holds one
solve state per selected Issue, including the closing journal while a close is unfinished.
"""

from __future__ import annotations

from ..harness.change_worktree import declare_section, put_section, section
from ..spec.typed_data import obj, register

ISSUE_SOLVING_RECORDS = obj(
    {
        "solutions": {
            "type": "object",
            "additionalProperties": {"type": "object", "additionalProperties": {}},
        }
    }
)
SECTION = "issue-solving"
SECTION_TYPE = "concorde-issue-solving-records"
register(SECTION_TYPE, 1, ISSUE_SOLVING_RECORDS)
declare_section(SECTION, SECTION_TYPE)


def solutions(change: dict | None) -> dict:
    """The solve states of ``change`` by Issue identity; empty when nothing was solved."""
    return (section(change, SECTION) or {}).get("solutions", {})


def store_solution(change: dict, issue_id: str, solution: dict) -> None:
    """Place the solve state of ``issue_id`` into ``change``; the caller writes the status."""
    records = section(change, SECTION) or put_section(
        change, SECTION, {"solutions": {}}
    )
    records["solutions"][issue_id] = solution
