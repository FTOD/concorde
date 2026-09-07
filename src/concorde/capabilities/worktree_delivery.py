"""Deliver an exact candidate from either participating worktree session."""
from __future__ import annotations

import copy
import tempfile
from dataclasses import replace
from pathlib import Path

from .change_worktree import (DELIVERIES_PATH, _inventory, _write_json,
    git, git_value, list_worktrees, read_change, repository_lock, save_change,
    snapshot_tree, workspace_identity)
from .operation_data import artifact, checked_path, decode, typed
from ..specification.repository import SpecError, SpecRepository, identifier, read_file
from ..specification.validation import validate_repository


def require_delivery_session(host, change_id: str) -> dict:
    """Admit only the selected source or destination, preserving session provenance."""
    primary, current = workspace_identity(host.project_root)
    if primary is None or current is None:
        raise SpecError("delivery requires linked Git worktrees", "delivery_session_required")
    root = Path(primary["path"])
    inventory = _inventory(root, persist=False)
    selected = [item for item in inventory["worktrees"] if item["change_id"] == change_id]
    if len(selected) == 1:
        source = Path(selected[0]["path"])
    else:
        receipt_path = _receipt_path(change_id)
        if selected or not checked_path(root, receipt_path).exists():
            raise SpecError("delivery requires one registered change or delivery receipt", "unknown_change")
        receipt = decode(read_file(root, receipt_path).decode())
        if receipt.get("schema_version") != 1 or receipt.get("change_id") != change_id:
            raise SpecError("delivery receipt has an invalid identity", "invalid_delivery")
        source = Path(receipt["source_worktree"])
    participants = {root, source}
    package_checkout = git(host.package_root, "rev-parse", "--show-toplevel", check=False)
    package_common = git(host.package_root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False)
    primary_common = git_value(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    unrelated_entry = (package_checkout.returncode == 0 and package_common.returncode == 0
        and package_common.stdout.strip() == primary_common
        and Path(package_checkout.stdout.strip()).resolve() not in participants)
    if (host.project_root not in participants or host.session_root not in participants
            or host.depth > 1 or unrelated_entry):
        raise SpecError("delivery session must belong to its selected source or destination worktree; "
                        "third-worktree and nested delivery are not authorized", "delivery_session_required")
    if not primary["branch"]:
        raise SpecError("the destination worktree must have an attached delivery branch", "detached_primary")
    return primary


def _receipt_path(change_id: str) -> str:
    identifier(change_id)
    return f"{DELIVERIES_PATH}/{change_id}.json"


def _is_ancestor(root: Path, before: str, after: str) -> bool:
    return git(root, "merge-base", "--is-ancestor", before, after, check=False).returncode == 0


def _primary_clean(root: Path) -> None:
    if git_value(root, "status", "--porcelain", "--untracked-files=all"):
        raise SpecError("primary worktree has local changes; delivery must preserve them", "dirty_primary")


def _commit(root: Path, tree: str, parents: tuple[str, ...], message: str) -> str:
    arguments = ["commit-tree", tree]
    for parent in parents:
        arguments.extend(("-p", parent))
    return git(root, *arguments, input=message.rstrip() + "\n").stdout.strip()


def _verify_merged_tree(host, commit: str, tree: str, change_id: str) -> list[dict]:
    """Run deterministic checks against the actual integration result, without agents."""
    from .scoped_operations import _check

    with tempfile.TemporaryDirectory(prefix="concorde-delivery-check-") as directory:
        root = Path(directory) / "project"
        git(host.project_root, "worktree", "add", "--detach", str(root), commit)
        try:
            report = validate_repository(root, package_root=host.package_root)
            if report.status != "success":
                raise SpecError("the merged candidate failed Spec validation", "invalid_merge")
            repository = SpecRepository(root, host.package_root)
            checks = []
            for target in repository.targets.values():
                if target.checks:
                    results = _check(repository, target, host.invocation_id)
                    checks.extend(results)
                    for result in results:
                        relative = f".concorde/runs/{host.invocation_id}/{result['check_id']}.log"
                        destination = checked_path(host.project_root,
                            f"{DELIVERIES_PATH}/{change_id}/{result['check_id']}.log")
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(read_file(root, relative))
            if any(item["status"] != "passed" for item in checks):
                raise SpecError("the merged candidate failed configured checks", "failed_merge_checks")
            if snapshot_tree(root) != tree:
                raise SpecError("validation changed the merged candidate", "stale_evidence")
            return checks
        finally:
            git(host.project_root, "worktree", "remove", "--force", str(root))


def _cleanup(host, receipt: dict, *, keep_worktree: bool = False) -> bool:
    """Retry only cleanup after a successful merge; never merge a second time."""
    root = host.project_root
    relative = _receipt_path(receipt["change_id"])
    accepted = "refs/heads/" + receipt["target_branch"]
    if not _is_ancestor(root, receipt["merged_commit"], accepted):
        raise SpecError("the recorded delivery is no longer on its target branch", "stale_delivery")
    source = Path(receipt["source_worktree"])
    current = next((item for item in list_worktrees(root) if item["path"] == str(source)), None)
    if current is not None:
        if current["branch"] != receipt["source_branch"] or current["head"] != receipt["candidate_commit"]:
            raise SpecError("delivered worktree branch changed before cleanup", "stale_delivery")
        if source.exists():
            state = read_change(source, required=True)
            if state["change_id"] != receipt["change_id"] or snapshot_tree(source, state) != receipt["candidate_tree"]:
                raise SpecError("delivered worktree has new candidate changes; retain it for inspection", "stale_delivery")
            if keep_worktree or host.session_root == source:
                state.update(phase="delivered", status="delivered", outcome="delivered")
                save_change(source, state, publish=False, locked=True)
                receipt.update(status="delivered", cleanup_error=None, retained_worktree=True)
                _write_json(root, relative, receipt)
                _inventory(root, persist=True)
                return True
            state.update(phase="cleanup", status="cleanup_pending", outcome="delivered")
            save_change(source, state, publish=False, locked=True)
        removal = git(root, "worktree", "remove", "--force", str(source), check=False)
        if removal.returncode:
            receipt.update(status="cleanup_pending", cleanup_error=removal.stderr.strip())
            _write_json(root, relative, receipt)
            _inventory(root, persist=True)
            return False
    elif source.exists():
        raise SpecError("delivered path is no longer the registered worktree; retain it", "stale_delivery")
    receipt.update(status="delivered", cleanup_error=None, retained_worktree=False)
    _write_json(root, relative, receipt)
    _inventory(root, persist=True)
    return True


def deliver(host, configuration: dict, task: dict) -> dict:
    primary = require_delivery_session(host, task["change_id"])
    host = replace(host, project_root=Path(primary["path"]))
    try:
        return _deliver(host, configuration, task)
    except Exception as error:
        if host.mode == "execute":
            try:
                _remember_failure(host, task["change_id"], error)
            except (ValueError, OSError) as persistence_error:
                raise SpecError(str(error) + "; could not persist delivery status: " + str(persistence_error),
                                "state_persistence_failed") from error
        raise


def _remember_failure(host, change_id: str, error: Exception) -> None:
    with repository_lock(host.project_root):
        inventory = _inventory(host.project_root, persist=False)
        selected = [item for item in inventory["worktrees"] if item["change_id"] == change_id]
        if len(selected) != 1:
            return
        source = Path(selected[0]["path"])
        state = read_change(source, required=True)
        receipt_path = _receipt_path(change_id)
        receipt = (decode(read_file(host.project_root, receipt_path).decode())
                   if checked_path(host.project_root, receipt_path).exists() else None)
        merged = receipt is not None and _is_ancestor(host.project_root, receipt["merged_commit"],
                                                      "refs/heads/" + receipt["target_branch"])
        state.update(phase="cleanup" if merged else "deliver", status="cleanup_pending" if merged else "blocked",
                     outcome=getattr(error, "code", "failed"))
        save_change(source, state, locked=True)
        if merged:
            receipt.update(status="cleanup_pending", cleanup_error=str(error))
            _write_json(host.project_root, receipt_path, receipt)


def _deliver(host, configuration: dict, task: dict) -> dict:
    from .scoped_operations import Invocation

    primary = require_delivery_session(host, task["change_id"])
    change_id = task["change_id"]
    relative = _receipt_path(change_id)
    root = host.project_root
    if host.mode == "describe-policy":
        inventory = _inventory(root, persist=False)
        selected = [item for item in inventory["worktrees"] if item["change_id"] == change_id]
        if len(selected) != 1:
            raise SpecError("delivery preview requires one registered live change", "unknown_change")
        state = read_change(Path(selected[0]["path"]), required=True)
        return typed("concorde-deliver-response", {
            "target_id": state["target_id"], "focus_id": state["focus_id"],
            "change_id": change_id, "context_id": None, "outcome": "described",
            "answer": "The delivery host verifies the candidate and integration, merges into "
                + primary["branch"] + ", and retains the source worktree when requested or hosting this session.",
            "gaps": [], "checks": [], "artifacts": [], "completed_operations": [],
        })
    with repository_lock(root):
        receipt_file = checked_path(root, relative)
        receipt = decode(read_file(root, relative).decode()) if receipt_file.exists() else None
        if receipt is not None:
            if receipt.get("schema_version") != 1 or receipt.get("change_id") != change_id:
                raise SpecError("delivery receipt has an invalid identity", "invalid_delivery")
            if _is_ancestor(root, receipt["merged_commit"], "refs/heads/" + receipt["target_branch"]):
                complete = _cleanup(host, receipt, keep_worktree=task.get("keep_worktree", receipt.get("retained_worktree", False)))
                return _response(root, receipt, complete)

        inventory = _inventory(root, persist=True)
        selected = [item for item in inventory["worktrees"] if item["change_id"] == change_id]
        if len(selected) != 1:
            raise SpecError("delivery requires one registered live change worktree", "unknown_change")
        source = Path(selected[0]["path"])
        state = read_change(source, required=True)
        if task.get("target_id") not in {None, state["target_id"]}:
            raise SpecError("delivery target differs from the worktree owner", "incompatible_handoff")
        retry = state["status"] == "blocked" and state["phase"] == "deliver"
        if (state["status"] not in {"ready", "delivering"} and not retry) or not state["validated_tree"]:
            raise SpecError("the change worktree has not reached a verified ready state", "incomplete_change")
        _primary_clean(root)
        actual_tree = snapshot_tree(source, state)
        if actual_tree != state["validated_tree"]:
            raise SpecError("candidate files changed after validation", "stale_evidence")
        evidence = state["targets"].get(state["target_id"], state.get("validation"))
        if evidence is None:
            raise SpecError("candidate has no completion or validation evidence", "stale_evidence")
        payload = {"target_id": state["target_id"], "task": evidence["task"],
                   "constraints": evidence.get("constraints", []), "change_id": change_id}
        if state["focus_id"] is not None:
            payload["focus_id"] = state["focus_id"]
        # Delivery reads evidence and runs deterministic checks without starting agents.
        candidate_host = replace(host, project_root=source, coordinated=True)
        Invocation("concorde-validate", configuration, payload, candidate_host).verify_completion()
        source_head = git_value(source, "rev-parse", "HEAD")
        target_head = git_value(root, "rev-parse", "HEAD")
        source_branch = state["branch"]
        candidate = (source_head if git_value(source, "rev-parse", "HEAD^{tree}") == actual_tree
                     else _commit(source, actual_tree, (source_head,), state["task"]))
        if _is_ancestor(root, target_head, candidate):
            merged, merged_tree = candidate, actual_tree
        else:
            result = git(root, "merge-tree", "--write-tree", target_head, candidate, check=False)
            if result.returncode:
                raise SpecError("candidate conflicts with the primary branch; resolve it in its change worktree and revalidate",
                                "merge_conflict")
            merged_tree = result.stdout.splitlines()[0]
            merged = _commit(root, merged_tree, (target_head, candidate),
                             "Deliver " + change_id + " from " + source_branch)
        state.update(phase="deliver", status="delivering", outcome=None)
        save_change(source, state, publish=False, locked=True)
        try:
            checks = _verify_merged_tree(host, merged, merged_tree, change_id)
            if (snapshot_tree(source, state) != actual_tree
                    or git_value(source, "rev-parse", "HEAD") != source_head):
                raise SpecError("candidate changed during delivery verification", "stale_evidence")
            _, current = workspace_identity(root)
            if current["branch"] != primary["branch"] or current["head"] != target_head:
                raise SpecError("primary branch changed during delivery", "stale_delivery")
            _primary_clean(root)
            receipt = {"schema_version": 1, "change_id": change_id, "status": "merging",
                "target_id": state["target_id"], "focus_id": state["focus_id"],
                "source_worktree": str(source), "source_branch": source_branch,
                "candidate_commit": candidate, "candidate_tree": actual_tree,
                "target_branch": current["branch"], "target_before": target_head,
                "merged_commit": merged, "merged_tree": merged_tree,
                "task": state["task"], "constraints": state["constraints"],
                "targets": copy.deepcopy(state["targets"]), "checks": checks,
                "cleanup_error": None}
            # A durable receipt precedes either ref update, so a restarted primary
            # session can distinguish an unmerged candidate from pending cleanup.
            _write_json(root, relative, receipt)
            git(source, "update-ref", "refs/heads/" + source_branch, candidate, source_head)
            # A retained source must not have an index staging the inverse of its new HEAD.
            git(source, "read-tree", candidate)
            git(root, "merge", "--ff-only", "--no-edit", merged)
            receipt["status"] = "cleanup_pending"
            _write_json(root, relative, receipt)
        except Exception:
            if receipt is None or not _is_ancestor(root, receipt["merged_commit"], "HEAD"):
                state.update(phase="deliver", status="blocked", outcome="failed")
                save_change(source, state, publish=False, locked=True)
                _inventory(root, persist=True)
            raise
        complete = _cleanup(host, receipt, keep_worktree=task.get("keep_worktree", receipt.get("retained_worktree", False)))
        return _response(root, receipt, complete)


def _response(root: Path, receipt: dict, complete: bool) -> dict:
    answer = ("Merged the verified change into " + receipt["target_branch"]
              + (" and retained its source worktree." if complete and receipt.get("retained_worktree") else
                 " and removed its temporary worktree and local state." if complete else
                 "; worktree cleanup is pending. Retry deliver from either participating session."))
    return typed("concorde-deliver-response", {
        "target_id": receipt["target_id"], "focus_id": receipt["focus_id"],
        "change_id": receipt["change_id"], "context_id": None,
        "outcome": "delivered" if complete else "failed", "answer": answer,
        "gaps": [], "checks": receipt["checks"],
        "artifacts": [artifact(root, "delivery", _receipt_path(receipt["change_id"]))],
        "completed_operations": ["concorde-deliver"] if complete else [],
    })
