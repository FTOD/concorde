"""The manual merge record: a merge into the primary branch made with ordinary Git.

Delivery only observes such a merge; recording it never performs, authorizes or undoes one.
The project CLI's ``status --change-id <id> --manual-merge <commit> --cleanup <outcome>``
reaches this service from the primary worktree.
"""

from __future__ import annotations

from pathlib import Path

from ..harness.change_worktree import (
    git,
    git_value,
    read_change,
    repository_lock,
    snapshot_tree,
    workspace_identity,
    worktree_incarnation,
)
from ..harness.status_store import primary_root, read_status, write_status
from ..spec.repository import SpecError
from .records import delivery_records, manual_merge


def record_manual_merge(
    root: Path, change_id: str, *, commit: str | None, cleanup: str
) -> dict:
    """Record observed ordinary-Git integration, never perform or authorize a merge.

    ``commit=None`` updates only the cleanup outcome of an already recorded manual
    merge, reverifying that recorded commit; it cannot invent merge evidence.
    """
    with repository_lock(root):
        primary = primary_root(root)
        if root.resolve() != primary:
            raise SpecError(
                "a manual merge is recorded from the primary worktree",
                "primary_session_required",
            )
        state = read_status(root, change_id)
        if state is None:
            raise SpecError("unknown task", "unknown_change")
        prior = manual_merge(state) or {}
        if commit is None:
            commit = prior.get("commit")
            if not commit:
                raise SpecError(
                    "cleanup outcome requires a recorded or observed manual merge",
                    "stale_evidence",
                )
        resolved = git_value(primary, "rev-parse", "--verify", commit + "^{commit}")
        if git(
            primary, "merge-base", "--is-ancestor", resolved, "HEAD", check=False
        ).returncode:
            raise SpecError(
                "merge commit is not integrated in primary HEAD", "stale_evidence"
            )
        candidate = Path(state["path"])
        candidate_commit = prior.get("candidate_commit")
        if candidate.exists():
            source_primary, current = workspace_identity(candidate)
            owner = read_change(candidate)
            if (
                current is None
                or source_primary is None
                or source_primary["path"] != str(primary)
                or not state.get("git_worktree_id")
                or state["git_worktree_id"] != worktree_incarnation(candidate)
                or (owner is not None and owner["change_id"] != change_id)
                or (owner is None and not candidate_commit)
            ):
                raise SpecError(
                    "present source does not belong to the selected task incarnation",
                    "workspace_mismatch",
                )
        if not candidate.exists() and not candidate_commit:
            raise SpecError(
                "record verified manual integration before removing its candidate",
                "stale_evidence",
            )
        if (
            candidate_commit
            and git(
                primary,
                "merge-base",
                "--is-ancestor",
                candidate_commit,
                resolved,
                check=False,
            ).returncode
        ):
            raise SpecError(
                "recorded candidate is not integrated in the observed merge",
                "stale_evidence",
            )
        if candidate.exists() and candidate != primary:
            head = git_value(candidate, "rev-parse", "HEAD")
            candidate_commit = head
            if git(
                primary, "merge-base", "--is-ancestor", head, resolved, check=False
            ).returncode:
                raise SpecError(
                    "candidate commit is not part of the observed merge",
                    "stale_evidence",
                )
            if snapshot_tree(candidate, state) != git_value(
                candidate, "rev-parse", "HEAD^{tree}"
            ):
                raise SpecError(
                    "candidate has uncommitted deliverable input", "stale_evidence"
                )
        if cleanup not in {"pending", "retained", "removed"}:
            raise SpecError("invalid cleanup outcome", "invalid_input")
        if cleanup == "removed" and Path(state["path"]).exists():
            raise SpecError("candidate still exists", "stale_evidence")
        delivery_records(state)["manual_merge"] = {
            "commit": resolved,
            "candidate_commit": candidate_commit or resolved,
            "method": "ordinary-git",
        }
        state.update(
            cleanup={"status": "not_needed" if candidate == primary else cleanup},
            outcome="merged",
            status="merged",
            phase="complete",
        )
        write_status(root, state)
        return state
