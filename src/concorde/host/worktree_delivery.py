"""Deliver an exact candidate from either participating worktree session."""
from __future__ import annotations

import copy
import tempfile
from dataclasses import replace
from pathlib import Path

from .change_worktree import (DELIVERIES_PATH, _inventory, _write_json,
    git, git_value, list_worktrees, read_change, repository_lock, save_change,
    snapshot_tree, workspace_identity)
from .typed_data import artifact, checked_path, decode, typed
from ..specification.changes import confirm_pending_files
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


def _verify_merged_tree(host, commit: str, tree: str, change_id: str, *, phase: str = "staging") -> list[dict]:
    """Run deterministic checks against the actual integration result, without agents."""
    from .capability_host import _check

    with tempfile.TemporaryDirectory(prefix="concorde-delivery-check-") as directory:
        root = Path(directory) / "project"
        git(host.project_root, "worktree", "add", "--detach", str(root), commit)
        try:
            if (root / "concorde.json").is_file():
                # The integration checkout has no untracked generated assets. Self-hosted
                # package validation requires a fresh build of these exact merged sources.
                from .build import write_build
                write_build(root)
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
                            f"{DELIVERIES_PATH}/{change_id}/{phase}/{result['check_id']}.log")
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
            if keep_worktree:
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
    if task.get("merge_primary") and (host.session_root != Path(primary["path"])
                                      or host.project_root != Path(primary["path"])):
        raise SpecError("explicit primary merge requires the primary worktree's owning session",
                        "primary_session_required")
    host = replace(host, project_root=Path(primary["path"]))
    try:
        return _deliver(host, configuration, task)
    except Exception as error:
        if host.mode == "execute" and not task.get("merge_primary"):
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
    from .capability_host import Invocation

    primary = require_delivery_session(host, task["change_id"])
    change_id = task["change_id"]
    relative = _receipt_path(change_id)
    root = host.project_root
    if host.mode == "describe-policy":
        if checked_path(root, relative).exists():
            state = decode(read_file(root, relative).decode())
        else:
            inventory = _inventory(root, persist=False)
            selected = [item for item in inventory["worktrees"] if item["change_id"] == change_id]
            if len(selected) != 1:
                raise SpecError("delivery preview requires one registered change or receipt", "unknown_change")
            state = read_change(Path(selected[0]["path"]), required=True)
        return typed("concorde-deliver-response", {
            "target_id": state["target_id"], "focus_id": state["focus_id"],
            "change_id": change_id, "context_id": None, "outcome": "described",
            "answer": "Delivery verifies integration into concorde/delivered/" + change_id
                + " and removes the source unless explicitly retained. A separate merge_primary:true "
                "request from the primary session is required to update " + primary["branch"] + ".",
            "gaps": [], "checks": [], "artifacts": [], "completed_capabilities": [],
        })
    with repository_lock(root):
        receipt_file = checked_path(root, relative)
        receipt = decode(read_file(root, relative).decode()) if receipt_file.exists() else None
        if receipt is not None and (receipt.get("schema_version") != 1 or receipt.get("change_id") != change_id):
            raise SpecError("delivery receipt has an invalid identity", "invalid_delivery")
        if task.get("merge_primary"):
            if receipt is None:
                raise SpecError("stage this change before requesting its primary merge", "delivery_required")
            return _merge_primary(host, receipt)
        keep_worktree = task.get("keep_worktree", receipt.get("retained_worktree", False) if receipt else False)
        if receipt is not None:
            if _is_ancestor(root, receipt["merged_commit"], "refs/heads/" + receipt["target_branch"]):
                # Persist an explicit retention change before cleanup can be interrupted.
                receipt["retained_worktree"] = keep_worktree
                _write_json(root, relative, receipt)
                complete = _cleanup(host, receipt, keep_worktree=keep_worktree)
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
        target_branch = "concorde/delivered/" + change_id
        target_ref = "refs/heads/" + target_branch
        if git(root, "show-ref", "--verify", "--quiet", target_ref, check=False).returncode == 0:
            raise SpecError("delivery branch already exists without an accepted receipt", "stale_delivery")
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
        # A pending marker is the author's declaration that a listed file is still to be written.
        # Delivery is the deterministic moment that confirms the files that now exist and removes
        # only those markers; the confirmation becomes part of the delivered candidate itself.
        confirmed_files, still_pending = confirm_pending_files(source, host.package_root)
        if confirmed_files:
            actual_tree = snapshot_tree(source, state)
        source_head = git_value(source, "rev-parse", "HEAD")
        target_head = git_value(root, "rev-parse", "HEAD")
        source_branch = state["branch"]
        message = ("Confirm created files for " + change_id) if confirmed_files else state["task"]
        candidate = (source_head if git_value(source, "rev-parse", "HEAD^{tree}") == actual_tree
                     else _commit(source, actual_tree, (source_head,), message))
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
            receipt = {"schema_version": 1, "change_id": change_id, "status": "merging",
                "target_id": state["target_id"], "focus_id": state["focus_id"],
                "source_worktree": str(source), "source_branch": source_branch,
                "candidate_commit": candidate, "candidate_tree": actual_tree,
                "target_branch": target_branch, "target_before": target_head,
                "primary_branch": current["branch"], "primary_merge": None,
                "merged_commit": merged, "merged_tree": merged_tree,
                "task": state["task"], "constraints": state["constraints"],
                "targets": copy.deepcopy(state["targets"]), "checks": checks,
                "confirmed_files": confirmed_files, "still_pending": still_pending,
                "cleanup_error": None, "retained_worktree": keep_worktree}
            # A durable receipt precedes either ref update, so a restarted primary
            # session can distinguish an unmerged candidate from pending cleanup.
            _write_json(root, relative, receipt)
            git(source, "update-ref", "refs/heads/" + source_branch, candidate, source_head)
            # A retained source must not have an index staging the inverse of its new HEAD.
            git(source, "read-tree", candidate)
            if any(item["branch"] == target_branch for item in list_worktrees(root)):
                raise SpecError("delivery branch is checked out in a worktree", "stale_delivery")
            git(root, "update-ref", target_ref, merged, "0" * len(merged))
            receipt["status"] = "cleanup_pending"
            _write_json(root, relative, receipt)
        except Exception:
            if receipt is None or not _is_ancestor(root, receipt["merged_commit"], target_ref):
                state.update(phase="deliver", status="blocked", outcome="failed")
                save_change(source, state, publish=False, locked=True)
                _inventory(root, persist=True)
            raise
        complete = _cleanup(host, receipt, keep_worktree=keep_worktree)
        return _response(root, receipt, complete)


def _merge_primary(host, receipt: dict) -> dict:
    """Only the primary owner may promote an already staged change, under the repository lock."""
    root = host.project_root
    change_id = receipt.get("change_id", "")
    relative = _receipt_path(change_id)
    if (receipt.get("schema_version") != 1
            or receipt.get("target_branch") != "concorde/delivered/" + change_id
            or not receipt.get("primary_branch")):
        raise SpecError("primary merge requires a staged delivery receipt", "invalid_delivery")
    primary, _ = workspace_identity(root)
    if primary["branch"] != receipt["primary_branch"]:
        raise SpecError("primary branch differs from the recorded delivery destination", "stale_delivery")
    promotion = receipt.get("primary_merge")
    if promotion and _is_ancestor(root, promotion["commit"], "HEAD"):
        promotion["status"] = "merged"
        _write_json(root, relative, receipt)
        return _response(root, receipt, receipt["status"] == "delivered")
    if promotion and promotion["status"] == "merged":
        raise SpecError("the primary merge is no longer on its recorded branch", "stale_delivery")
    if receipt["status"] != "delivered":
        raise SpecError("finish delivery cleanup before requesting the primary merge", "delivery_required")
    target_ref = "refs/heads/" + receipt["target_branch"]
    if git_value(root, "rev-parse", target_ref) != receipt["merged_commit"]:
        raise SpecError("the staged branch changed after verification", "stale_delivery")
    _primary_clean(root)
    before = primary["head"]
    candidate = receipt["merged_commit"]
    if _is_ancestor(root, candidate, before):
        merged, tree = before, git_value(root, "rev-parse", "HEAD^{tree}")
    elif _is_ancestor(root, before, candidate):
        merged, tree = candidate, receipt["merged_tree"]
    else:
        result = git(root, "merge-tree", "--write-tree", before, candidate, check=False)
        if result.returncode:
            raise SpecError("delivered branch conflicts with the primary branch; preserve it and "
                            "resolve in a new change worktree before delivery", "merge_conflict")
        tree = result.stdout.splitlines()[0]
        merged = _commit(root, tree, (before, candidate), "Merge delivered " + change_id)
    checks = _verify_merged_tree(host, merged, tree, change_id, phase="primary")
    current, _ = workspace_identity(root)
    if current["branch"] != primary["branch"] or current["head"] != before:
        raise SpecError("primary branch changed during merge verification", "stale_delivery")
    if git_value(root, "rev-parse", target_ref) != candidate:
        raise SpecError("staged branch changed during merge verification", "stale_delivery")
    _primary_clean(root)
    receipt["primary_merge"] = {"status": "merging", "branch": primary["branch"],
                                "before": before, "commit": merged, "tree": tree, "checks": checks}
    _write_json(root, relative, receipt)
    git(root, "merge", "--ff-only", "--no-edit", merged)
    receipt["primary_merge"]["status"] = "merged"
    _write_json(root, relative, receipt)
    return _response(root, receipt, True)


def _response(root: Path, receipt: dict, complete: bool) -> dict:
    answer = ("Merged the verified change into " + receipt["target_branch"]
              + (" and retained its source worktree." if complete and receipt.get("retained_worktree") else
                 " and removed its temporary worktree and local state." if complete else
                 "; worktree cleanup is pending. Retry deliver from a participating session."))
    confirmed = receipt.get("confirmed_files") or []
    if confirmed:
        answer += (" Confirmed created files: "
                   + ", ".join(sorted(item["path"] for item in confirmed)) + ".")
    if receipt.get("still_pending"):
        answer += (" Files still declared pending: "
                   + ", ".join(receipt["still_pending"]) + ".")
    promotion = receipt.get("primary_merge") or {}
    if promotion.get("status") == "merged":
        answer += " Explicitly merged into primary branch " + receipt["primary_merge"]["branch"] + "."
    elif receipt.get("primary_branch"):
        answer += " The primary branch is unchanged; its owning session must receive an explicit merge request."
    return typed("concorde-deliver-response", {
        "target_id": receipt["target_id"], "focus_id": receipt["focus_id"],
        "change_id": receipt["change_id"], "context_id": None,
        "outcome": "delivered" if complete else "failed", "answer": answer,
        "gaps": [], "checks": promotion.get("checks", receipt["checks"]),
        "artifacts": [artifact(root, "delivery", _receipt_path(receipt["change_id"]))],
        "completed_capabilities": ["concorde-deliver"] if complete else [],
    })
