"""Planning's typed values and its provider section of the change status.

Loading this module registers Planning's typed values with Spec tooling and declares the
``planning`` provider section with Candidate worktrees. The section holds one progress entry per
Module worked on in the change (its plan, tasks, checks and revisions) and the pending-gap
history; no other Module writes it except through the functions below.
"""

from __future__ import annotations

import copy
from pathlib import Path

from ..harness.change_worktree import (
    declare_section,
    put_section,
    read_change,
    repository_lock,
    save_change,
    section,
)
from ..harness.native_result import TASK_ITEM
from ..spec.repository import SpecError, identifier
from ..spec.typed_data import DIGEST, STRING, array, obj, register

PLAN_ARTIFACT = obj({"plan": STRING})
TASK_IDENTITY_CONSTRAINTS = obj({"reserved_task_ids": array(STRING, unique=True)})
# contract.planning.implementation-task
IMPLEMENTATION_TASK = obj({"plan": STRING, "tasks": array(TASK_ITEM)})
TASK_SCOPE_FEEDBACK = obj(
    {"tasks_digest": DIGEST, "reason": {"const": "implementation_boundary"}}
)
# The planning section: progress entries by Module and the pending-gap history.
_RECORD = {"type": "object", "additionalProperties": {}}
PLANNING_RECORDS = obj(
    {
        "targets": {"type": "object", "additionalProperties": _RECORD},
        "gaps": array(_RECORD),
    }
)
SECTION = "planning"
SECTION_TYPE = "concorde-planning-records"

register("concorde-plan-artifact", 1, PLAN_ARTIFACT)
register("concorde-task-identity-constraints", 1, TASK_IDENTITY_CONSTRAINTS)
register("concorde-implementation-task", 1, IMPLEMENTATION_TASK)
register("concorde-task-scope-feedback", 1, TASK_SCOPE_FEEDBACK)
register(SECTION_TYPE, 1, PLANNING_RECORDS)
declare_section(SECTION, SECTION_TYPE)


def planning_records(change: dict) -> dict:
    """The mutable planning section of ``change``, created empty when absent."""
    return section(change, SECTION) or put_section(
        change, SECTION, {"targets": {}, "gaps": []}
    )


def targets(change: dict | None) -> dict:
    """The progress entries of ``change`` by Module; empty without planned work."""
    return (section(change, SECTION) or {}).get("targets", {})


def gap_history(change: dict | None) -> list[dict]:
    """Every pending gap recorded in ``change``, open or resolved."""
    return (section(change, SECTION) or {}).get("gaps", [])


def target_owner(change: dict) -> dict:
    """Non-reusable ownership, captured when a target is first constructed."""
    return {
        "change_id": change["change_id"],
        "git_worktree_id": change.get("git_worktree_id"),
    }


def verify_target_owner(change: dict, target: dict) -> None:
    # Never fill a missing binding from a fresh read: that would launder stale work.
    if target.get("owner") != target_owner(change):
        raise SpecError(
            "target belongs to another task or worktree incarnation, or lacks ownership",
            "workspace_mismatch",
        )


def target_state(
    root: Path, target_id: str, focus_id: str | None, *, create: bool = False
) -> dict:
    """A copy of the progress entry of ``target_id``, or a new one when ``create``."""
    change = read_change(root, required=True)
    existing = targets(change).get(target_id)
    if existing is not None:
        verify_target_owner(change, existing)
        if existing.get("focus_id") != focus_id:
            raise SpecError(
                "target work belongs to a different focus", "incompatible_handoff"
            )
        return copy.deepcopy(existing)
    if not create:
        raise SpecError(
            "this operation requires an authored target plan", "missing_plan"
        )
    return {
        "schema_version": 2,
        "target_id": target_id,
        "focus_id": focus_id,
        "owner": target_owner(change),
        "plan": "",
        "tasks": [],
        "checks": [],
        "spec_digest": None,
        "implementation_digest": None,
        "completed_operations": [],
        "phase": "plan",
        "status": "active",
    }


def save_target_state(root: Path, value: dict) -> None:
    """Replace one progress entry if it is unchanged since it was read (``stale_status``)."""
    with repository_lock(root):
        change = read_change(root, required=True)
        identifier(value["target_id"])
        verify_target_owner(change, value)
        entries = planning_records(change)["targets"]
        previous = entries.get(value["target_id"], {})
        if value.get("revision", 0) != previous.get("revision", 0):
            raise SpecError(
                "target progress changed; reread before updating", "stale_status"
            )
        updated = copy.deepcopy(value)
        updated["revision"] = previous.get("revision", 0) + (
            {**updated, "revision": previous.get("revision", 0)} != previous
        )
        entries[value["target_id"]] = updated
        save_change(root, change)
        value["revision"] = updated["revision"]
