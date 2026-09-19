"""Primary-owned local task status and durable run evidence.

Candidates have no authoritative copies. Git's common-dir identity, not a directory
name, locates the primary. If it is unavailable, stop and retry after restoring it;
never create a replacement archive in a candidate.
"""

from __future__ import annotations

import os
import base64
import hashlib
import tempfile
import sys
from pathlib import Path

from ..spec.repository import SpecError, identifier
from ..spec.typed_data import canonical, checked_path, decode

STATUS_PATH = ".concorde/status"
RUNS_PATH = ".concorde/runs"


def primary_root(root: Path) -> Path:
    from .change_worktree import workspace_identity

    primary, current = workspace_identity(root)
    if current is None:
        return root.resolve()  # explicitly unversioned project; no other participant
    if primary is None or not primary["alive"]:
        raise SpecError(
            "primary unavailable; restore it and retry without local fallback",
            "primary_unavailable",
        )
    return Path(primary["path"])


def status_path(change_id: str) -> str:
    identifier(change_id)
    if change_id == "migration":
        raise SpecError("reserved migration journal identity", "invalid_input")
    return f"{STATUS_PATH}/{change_id}.json"


def read_status(root: Path, change_id: str) -> dict | None:
    path = checked_path(primary_root(root), status_path(change_id))
    return decode(path.read_text()) if path.exists() else None


def all_status(root: Path) -> list[dict]:
    directory = checked_path(primary_root(root), STATUS_PATH)
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        if path.name == "migration.json":
            continue
        value = decode(checked_path(directory, path.name).read_text())
        if (
            not isinstance(value, dict)
            or status_path(value.get("change_id")) != f"{STATUS_PATH}/{path.name}"
        ):
            raise SpecError(
                "status has an invalid stable identity", "invalid_worktree_state"
            )
        records.append(value)
    return records


def atomic_write(root: Path, relative: str, data: bytes) -> None:
    path = checked_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent)
    temporary = Path(name)
    with os.fdopen(descriptor, "wb") as stream:
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _local_storage(root: Path) -> Path:
    """Keep local runtime evidence separate from tracked project configuration."""
    from .change_worktree import git

    primary = primary_root(root)
    tracked = git(primary, "ls-files", "--", STATUS_PATH, RUNS_PATH, check=False)
    if tracked.returncode == 0 and tracked.stdout.strip():
        raise SpecError(
            "runtime status/runs are tracked; explicitly reconcile them before persistence",
            "invalid_worktree_state",
        )
    if root.resolve() != primary and checked_path(root, RUNS_PATH).exists():
        raise SpecError(
            "candidate-local durable runs require explicit migration",
            "migration_required",
        )
    return primary


def write_status(root: Path, value: dict) -> None:
    from .change_worktree import _exclude_control_files, repository_lock

    with repository_lock(root):
        destination = _local_storage(root)
        _exclude_control_files(root)
        atomic_write(
            destination,
            status_path(value["change_id"]),
            (canonical(value) + "\n").encode(),
        )


def run_path(root: Path, relative: str) -> Path:
    if not relative.startswith(RUNS_PATH + "/"):
        raise SpecError("not a durable run path", "unsafe_path")
    return checked_path(primary_root(root), relative)


def write_run(root: Path, relative: str, data: bytes) -> None:
    from .change_worktree import _exclude_control_files, repository_lock

    with repository_lock(root):
        destination = _local_storage(root)
        _exclude_control_files(root)
        atomic_write(destination, relative, data)


def record_manual_merge(
    root: Path, change_id: str, *, commit: str, cleanup: str
) -> dict:
    """Record observed ordinary-Git integration, never perform or authorize a merge."""
    from .change_worktree import git, git_value, repository_lock

    with repository_lock(root):
        primary = primary_root(root)
        state = read_status(root, change_id)
        if state is None:
            raise SpecError("unknown task", "unknown_change")
        resolved = git_value(primary, "rev-parse", "--verify", commit + "^{commit}")
        if git(
            primary, "merge-base", "--is-ancestor", resolved, "HEAD", check=False
        ).returncode:
            raise SpecError(
                "merge commit is not integrated in primary HEAD", "stale_evidence"
            )
        candidate = Path(state["path"])
        prior = state.get("manual_merge") or {}
        candidate_commit = prior.get("candidate_commit")
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
            from .change_worktree import snapshot_tree

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
        state.update(
            manual_merge={
                "commit": resolved,
                "candidate_commit": candidate_commit or resolved,
                "method": "ordinary-git",
            },
            cleanup={"status": "not_needed" if candidate == primary else cleanup},
            outcome="merged",
            status="merged",
            phase="complete",
        )
        write_status(root, state)
        return state


def migrate_legacy(root: Path, *, apply: bool = False) -> dict:
    """Explicit non-destructive, idempotent import with an interruption-safe journal.

    All collisions are compared before writes. Sources remain byte-for-byte archived
    in primary historical run storage before any original is removed. An interrupted
    copy retries identical targets; different bytes always require human resolution.
    Archived data is historical, never a second authoritative store or fresh readiness.
    """
    from .change_worktree import list_worktrees, repository_lock

    with repository_lock(root):
        primary = primary_root(root)
        journal = f"{STATUS_PATH}/migration.json"
        journal_file = checked_path(primary, journal)
        if journal_file.exists():
            pending = decode(journal_file.read_text())
            if pending.get("status") == "planned" and "payloads" in pending:
                if apply:
                    _finish_migration(primary, journal, pending)
                return {
                    key: value for key, value in pending.items() if key != "payloads"
                }
        records: dict[str, dict] = {}
        copies: dict[str, bytes] = {}
        archives: list[Path] = []
        roots = [
            Path(item["path"]) for item in list_worktrees(root) if item["alive"]
        ] or [primary]
        for source in roots:
            old = checked_path(source, ".concorde/worktree.json")
            if old.exists():
                state = decode(old.read_text())
                if state.get("schema_version") != 2 or state.get("path") != str(source):
                    raise SpecError(
                        "legacy state needs explicit version/identity repair",
                        "migration_conflict",
                    )
                key = state["change_id"]
                if key in records and records[key] != state:
                    raise SpecError(
                        "duplicate legacy change identity", "migration_conflict"
                    )
                state.update(
                    mode="operation",
                    child=None,
                    runs=[],
                    cleanup={"status": "pending"},
                    migration={"source": str(old), "requires_validation": True},
                )
                # Old readiness is not current evidence under the new execution profile.
                state.update(
                    status="blocked",
                    phase="migration",
                    validated_tree=None,
                    validation=None,
                )
                records[key] = state
                archives.append(old)
            runs = checked_path(source, RUNS_PATH)
            if source != primary and runs.exists():
                for path in runs.rglob("*"):
                    if path.is_symlink():
                        raise SpecError("legacy run symlink", "migration_conflict")
                    if path.is_file():
                        relative = RUNS_PATH + "/" + path.relative_to(runs).as_posix()
                        data = path.read_bytes()
                        if relative in copies and copies[relative] != data:
                            raise SpecError(
                                "run identity collision", "migration_conflict"
                            )
                        copies[relative] = data
                archives.append(runs)
        deliveries = checked_path(primary, ".concorde/deliveries")
        if deliveries.exists():
            for path in deliveries.glob("*.json"):
                receipt = decode(checked_path(deliveries, path.name).read_text())
                key = receipt["change_id"]
                state = records.setdefault(
                    key,
                    {
                        "schema_version": 2,
                        "change_id": key,
                        "path": receipt["source_worktree"],
                        "phase": "complete",
                        "status": "delivered",
                        "outcome": "delivered",
                        "mode": "operation",
                    },
                )
                state["delivery"] = receipt
                state["cleanup"] = {
                    "status": "pending"
                    if receipt["status"] == "cleanup_pending"
                    else "retained"
                    if receipt.get("retained_worktree")
                    else "removed"
                }
            # Preserve detailed legacy logs in a clearly historical run archive.
            for path in deliveries.rglob("*"):
                if path.is_symlink():
                    raise SpecError("legacy delivery symlink", "migration_conflict")
                if path.is_file() and path.suffix != ".json":
                    copies[
                        f"{RUNS_PATH}/legacy-delivery/{path.relative_to(deliveries).as_posix()}"
                    ] = path.read_bytes()
            archives.append(deliveries)
        registry = checked_path(primary, ".concorde/worktrees.json")
        if registry.exists():
            archives.append(registry)
        for key, state in records.items():
            copies[status_path(key)] = (canonical(state) + "\n").encode()
        source_files = {}
        for source in archives:
            paths = sorted(source.rglob("*")) if source.is_dir() else [source]
            archive_id = hashlib.sha256(str(source).encode()).hexdigest()
            for path in paths:
                if any(p.is_symlink() for p in (path, *path.parents)):
                    raise SpecError(
                        f"unsafe migration source: {path}", "migration_conflict"
                    )
                if not path.is_file():
                    continue
                suffix = (
                    path.relative_to(source).as_posix()
                    if source.is_dir()
                    else source.name
                )
                relative = f"{RUNS_PATH}/legacy-migration/{archive_id}/{suffix}"
                data = path.read_bytes()
                copies[relative] = data
                source_files[str(path)] = {
                    "archive": relative,
                    "digest": hashlib.sha256(data).hexdigest(),
                }
        for relative, data in copies.items():
            target = checked_path(primary, relative)
            if target.exists() and target.read_bytes() != data:
                raise SpecError(
                    f"migration collision: {relative}", "migration_conflict"
                )
        plan = {
            "schema_version": 1,
            "targets": sorted(copies),
            "archives": [str(p) for p in archives],
            "source_files": source_files,
            "status": "planned",
        }
        if apply and archives:
            from .change_worktree import _exclude_control_files

            _exclude_control_files(root)
            plan["payloads"] = {
                path: base64.b64encode(data).decode() for path, data in copies.items()
            }
            atomic_write(primary, journal, (canonical(plan) + "\n").encode())
            _finish_migration(primary, journal, plan)
            plan.pop("payloads", None)
        return plan


def _finish_migration(primary: Path, journal: str, plan: dict) -> None:
    # The journal is durable before any target/archive transition. Replay all comparisons
    # first so a retry cannot overwrite a conflicting concurrently edited target.
    for name, record in plan["source_files"].items():
        source = Path(name)
        if any(p.is_symlink() for p in (source, *source.parents)):
            raise SpecError(f"unsafe migration source: {source}", "migration_conflict")
        if source.exists() and (
            not source.is_file()
            or hashlib.sha256(source.read_bytes()).hexdigest() != record["digest"]
        ):
            raise SpecError(f"migration source changed: {source}", "migration_conflict")
        if (
            not source.exists()
            and not checked_path(primary, record["archive"]).is_file()
        ):
            raise SpecError(
                f"unarchived source vanished: {source}", "migration_conflict"
            )
    for name in plan["archives"]:
        directory = Path(name)
        if directory.is_dir() and any(
            str(p) not in plan["source_files"]
            for p in directory.rglob("*")
            if p.is_file() or p.is_symlink()
        ):
            raise SpecError(
                f"migration source gained files: {directory}", "migration_conflict"
            )
    for relative, payload in plan["payloads"].items():
        data = base64.b64decode(payload, validate=True)
        target = checked_path(primary, relative)
        if target.exists() and target.read_bytes() != data:
            raise SpecError(
                f"interrupted migration collision: {relative}", "migration_conflict"
            )
    for relative, payload in plan["payloads"].items():
        atomic_write(primary, relative, base64.b64decode(payload, validate=True))
    # Every original byte is now archived in primary. Remove only the exact unchanged
    # source files; the journal makes partial removal resumable across filesystems.
    for name, record in plan["source_files"].items():
        source = Path(name)
        if source.exists():
            if hashlib.sha256(source.read_bytes()).hexdigest() != record["digest"]:
                raise SpecError(
                    f"migration source changed: {source}", "migration_conflict"
                )
            source.unlink()
    for name in plan["archives"]:
        directory = Path(name)
        if directory.is_dir():
            for child in sorted(
                directory.rglob("*"), key=lambda p: len(p.parts), reverse=True
            ):
                if child.is_dir():
                    child.rmdir()
            directory.rmdir()
    plan["status"] = "completed"
    plan.pop("payloads", None)  # detailed evidence now lives only in the run archive
    atomic_write(primary, journal, (canonical(plan) + "\n").encode())


def record_run(
    host, *, operation: str, result: dict | None = None, task: dict | None = None
) -> None:
    """Capture actual source provenance before execution and retain every final envelope."""
    from .change_worktree import (
        git_value,
        read_change,
        repository_lock,
        snapshot_tree,
        workspace_identity,
    )
    from ..spec.repository import digest

    archive = host.archive_root or primary_root(host.project_root)
    with repository_lock(archive):
        relative = f"{RUNS_PATH}/{host.invocation_id}/run.json"
        path = run_path(archive, relative)
        if path.exists():
            record = decode(path.read_text())
        else:
            primary, current = workspace_identity(host.project_root)
            change = (
                read_status(archive, task["change_id"])
                if operation == "concorde-deliver" and task and task.get("change_id")
                else read_change(host.project_root)
            )
            manifest = host.package_root / "generated/build-manifest.json"
            runtime = host.package_root / "scripts/run-operation.py"
            input_tree = (
                snapshot_tree(
                    host.project_root,
                    change
                    if change and change.get("path") == str(host.project_root)
                    else {},
                )
                if current
                else None
            )
            build_reference = None
            if manifest.is_file():
                build_bytes = manifest.read_bytes()
                build_reference = f"{RUNS_PATH}/{host.root_invocation_id or host.invocation_id}/builds/{digest(build_bytes).removeprefix('sha256:')}.json"
                write_run(archive, build_reference, build_bytes)
            if host.session_provenance:
                for skill in host.session_provenance["skills"]:
                    write_run(
                        archive,
                        f"{RUNS_PATH}/{host.root_invocation_id or host.invocation_id}/skills/{skill['digest'].removeprefix('sha256:')}.md",
                        skill["body"].encode(),
                    )
            record = {
                "schema_version": 1,
                "run_id": host.invocation_id,
                "root_run_id": host.root_invocation_id or host.invocation_id,
                "change_id": change["change_id"] if change else None,
                "operation": operation,
                "source_worktree": str(host.project_root),
                "branch": current["branch"] if current else None,
                "commit": current["head"] if current else None,
                "input_tree": input_tree,
                "dirty_input_digest": digest(
                    {"commit": current["head"], "tree": input_tree}
                )
                if current
                else None,
                "dirty": input_tree
                != git_value(host.project_root, "rev-parse", "HEAD^{tree}")
                if current
                else None,
                "runtime": {
                    "root": str(host.package_root),
                    "python": sys.executable,
                    "python_version": sys.version,
                    "launcher_digest": digest(runtime.read_bytes())
                    if runtime.is_file()
                    else None,
                },
                "build_artifact": build_reference,
                "build_digest": digest(manifest.read_bytes())
                if manifest.is_file()
                else None,
                "skill_provenance": {
                    key: value
                    for key, value in host.session_provenance.items()
                    if key != "skills"
                }
                | {
                    "skills": [
                        {key: value for key, value in skill.items() if key != "body"}
                        for skill in host.session_provenance["skills"]
                    ]
                }
                if host.session_provenance
                else None,
                "status": "started",
            }
            # A build catalog is not evidence of Skill loading. Only an explicitly supplied,
            # verified selection can provide that provenance; otherwise it stays unknown.
            if (
                change
                and result is None
                and task
                and (
                    operation == "concorde-deliver"
                    or (
                        task.get("task") == change.get("task")
                        and all(
                            field not in task or task[field] == change.get(field)
                            for field in ("constraints", "focus_id")
                        )
                        and (
                            "target_id" in task
                            and task["target_id"]
                            == (change.get("target_id") or change.get("target_hint"))
                        )
                    )
                )
            ):
                change.setdefault("runs", []).append(relative)
                write_status(host.project_root, change)
        if result is not None:
            record.update(status=result["status"], result=result)
            record["artifacts"] = _archive_artifacts(
                host.project_root, archive, host.invocation_id, result
            )
        write_run(archive, relative, (canonical(record) + "\n").encode())


def _archive_artifacts(source: Path, archive: Path, run_id: str, result) -> list[dict]:
    """Keep accepted artifact bytes after scratch, status or candidate paths change."""
    from ..spec.repository import digest, read_file

    records = []
    seen = set()

    def visit(value):
        if isinstance(value, dict):
            if set(value) == {"id", "path", "digest"}:
                key = (value["path"], value["digest"])
                if key in seen:
                    return
                seen.add(key)
                try:
                    root = (
                        archive
                        if value["path"].startswith(
                            (STATUS_PATH + "/", RUNS_PATH + "/")
                        )
                        else source
                    )
                    data = read_file(root, value["path"])
                    if digest(data) != value["digest"]:
                        raise ValueError("artifact changed before this record")
                except (OSError, ValueError):
                    # A composed result can name an earlier stage's mutable status. That
                    # stage has its own snapshot; do not fabricate current bytes here.
                    records.append({**value, "status": "unavailable", "archive": None})
                else:
                    relative = f"{RUNS_PATH}/{run_id}/artifacts/{value['digest'].removeprefix('sha256:')}/{value['path']}"
                    write_run(archive, relative, data)
                    records.append({**value, "status": "archived", "archive": relative})
            else:
                for child in value.values():
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return records


def coordinate_child(
    root: Path, change_id: str, *, child_id: str, phase: str, release: bool = False
) -> dict:
    """Primary coordinator records one writer/test owner; does not spawn a session."""
    from .change_worktree import repository_lock

    with repository_lock(root):
        if root.resolve() != primary_root(root):
            raise SpecError(
                "child ownership is assigned by the primary coordinator",
                "primary_session_required",
            )
        state = read_status(root, change_id)
        if state is None:
            raise SpecError("unknown task", "unknown_change")
        if not release and any(
            other["change_id"] != change_id
            and other.get("path") == state.get("path")
            and other.get("child")
            for other in all_status(root)
        ):
            raise SpecError(
                "another task child owns this workspace", "workspace_mismatch"
            )
        owner = state.get("child")
        if owner and owner["id"] != child_id:
            raise SpecError(
                "another child still owns this workspace", "workspace_mismatch"
            )
        if not child_id.strip() or phase not in {"maintenance", "test", "task"}:
            raise SpecError("invalid child identity or phase", "invalid_input")
        state["child"] = (
            None
            if release
            else {
                "id": child_id,
                "phase": phase,
                "fresh_context": True,
                "fork_context": False,
            }
        )
        state["phase"] = "handoff" if release else phase
        write_status(root, state)
        return state
