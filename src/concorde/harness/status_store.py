"""Primary-owned change status, provider sections and durable run records.

Candidates have no authoritative copies. Git's common-dir identity, not a directory
name, locates the primary. If it is unavailable, stop and retry after restoring it;
never create a replacement archive in a candidate. Provider sections are stored and
type-checked here but never interpreted.
"""

from __future__ import annotations

from .timing import timed

import os
import copy
import tempfile
import sys
from pathlib import Path

from ..spec.repository import SpecError, identifier, read_file
from ..spec.typed_data import (
    STRING,
    TypedDataError,
    array,
    artifact,
    canonical,
    checked_path,
    decode,
    obj,
    typed,
    validate_typed,
)

STATUS_PATH = ".concorde/status"
RUNS_PATH = ".concorde/runs"
STATUS_VERSION = 3

# The workspace facts of a worktree (Candidate worktrees' records), embedded in context snapshots.
NULLABLE_ID = {"anyOf": [STRING, {"type": "null"}]}
WORKTREE_SUMMARY = obj(
    {
        "path": STRING,
        "branch": NULLABLE_ID,
        "head": NULLABLE_ID,
        "managed": {"type": "boolean"},
        "locked": {"type": "boolean"},
        "change_id": NULLABLE_ID,
        "target_id": NULLABLE_ID,
        "task": {"type": "string"},
        "phase": NULLABLE_ID,
        "status": STRING,
        "outcome": NULLABLE_ID,
    }
)
WORKSPACE_CONTEXT = obj(
    {
        "kind": {"enum": ["primary", "change", "unversioned"]},
        "current_worktree": STRING,
        "current_branch": NULLABLE_ID,
        "primary_worktree": NULLABLE_ID,
        "primary_branch": NULLABLE_ID,
        "change_id": NULLABLE_ID,
        "phase": NULLABLE_ID,
        "status": NULLABLE_ID,
        "outcome": NULLABLE_ID,
        "active_worktrees": array(WORKTREE_SUMMARY),
    }
)

# Provider section name -> the typed-value type its provider declared for it.
_SECTIONS: dict[str, str] = {}


def declare_section(name: str, type_id: str) -> None:
    """Declare the provider section ``name`` of every change status, holding ``type_id`` values.

    A section is declared once; declaring it again with the same type changes nothing, with
    another type it is refused.
    """
    identifier(name)
    existing = _SECTIONS.get(name)
    if existing not in {None, type_id}:
        raise SpecError(
            f"provider section {name!r} is already declared", "invalid_input"
        )
    _SECTIONS[name] = type_id


def declared_sections() -> dict[str, str]:
    return dict(_SECTIONS)


def section(state: dict | None, name: str) -> dict | None:
    """The ``data`` of provider section ``name`` of a change status, or None when absent."""
    value = ((state or {}).get("sections") or {}).get(name)
    return value["data"] if isinstance(value, dict) and "data" in value else None


def put_section(state: dict, name: str, data: dict) -> dict:
    """Place ``data`` into provider section ``name``; the next status write type-checks it."""
    if name not in _SECTIONS:
        raise SpecError(
            f"provider section {name!r} is not declared", "invalid_worktree_state"
        )
    state.setdefault("sections", {})[name] = typed(_SECTIONS[name], data)
    return state["sections"][name]["data"]


def _check_sections(value: dict, previous: dict | None) -> None:
    """Refuse an undeclared or mistyped provider section the write would store or change."""
    sections = value.get("sections")
    if not isinstance(sections, dict):
        raise SpecError(
            "change status has no provider sections map", "invalid_worktree_state"
        )
    stored = (previous or {}).get("sections") or {}
    for name, item in sections.items():
        if stored.get(name) == item:
            continue  # checked when it was written
        if name not in _SECTIONS:
            raise SpecError(
                f"provider section {name!r} is not declared", "invalid_worktree_state"
            )
        try:
            validate_typed(item, _SECTIONS[name], f"/sections/{name}")
        except TypedDataError as error:
            raise SpecError(
                f"provider section {name!r} is invalid: {error}",
                "invalid_worktree_state",
            ) from error


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


def record_root(root: Path, relative: str) -> Path:
    """The worktree that holds ``relative``: status and run records live only in the primary."""
    if relative.startswith((STATUS_PATH + "/", RUNS_PATH + "/")):
        return primary_root(root)
    return root


def read_record(root: Path, relative: str) -> bytes:
    """The bytes of a project file, or of a status or run record in the primary worktree."""
    return read_file(record_root(root, relative), relative)


def record_artifact(root: Path, identifier: str, relative: str) -> dict:
    """``{id, path, digest}`` of a project file, or of a status or run record in the primary."""
    return artifact(record_root(root, relative), identifier, relative)


def verify_record_artifacts(root: Path, value) -> None:
    """Fail with ``stale_reference`` when any artifact embedded in ``value`` changed."""
    from ..spec.typed_data import verify_artifacts

    if isinstance(value, dict):
        if set(value) == {"id", "path", "digest"} and isinstance(value["path"], str):
            verify_artifacts(record_root(root, value["path"]), value)
        else:
            for item in value.values():
                verify_record_artifacts(root, item)
    elif isinstance(value, list):
        for item in value:
            verify_record_artifacts(root, item)


def status_path(change_id: str) -> str:
    identifier(change_id)
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
    return primary


@timed("evidence.write_status")
def write_status(root: Path, value: dict, *, create: bool = False) -> None:
    """Create once or compare-and-swap a complete status under the shared lock.

    Successful saves refresh the caller's revision; a stale snapshot is never
    merged by a field allowlist or silently substituted for newer progress.
    """
    from .change_worktree import _exclude_control_files, repository_lock

    with repository_lock(root):
        destination = _local_storage(root)
        previous = read_status(destination, value["change_id"])
        if create and previous is not None:
            raise SpecError(
                "stable change identity already exists", "workspace_mismatch"
            )
        if not create and (
            previous is None or value.get("revision", 0) != previous.get("revision", 0)
        ):
            raise SpecError(
                "task status changed; reread before updating", "stale_status"
            )
        if previous == value:
            return  # A successful no-op preserves byte-bound lifecycle evidence.
        _check_sections(value, previous)
        updated = copy.deepcopy(value)
        updated["revision"] = (previous or {}).get("revision", 0) + 1
        _exclude_control_files(root)
        atomic_write(
            destination,
            status_path(value["change_id"]),
            (canonical(updated) + "\n").encode(),
        )
        value.update(updated)


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


@timed("evidence.record_run")
def record_run(
    host,
    *,
    operation: str,
    result: dict | None = None,
    task: dict | None = None,
    relayed_run_id: str | None = None,
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
            change = read_change(host.project_root)
            if change is None and task and task.get("change_id"):
                # A request started outside the change's worktree names it explicitly.
                change = read_status(archive, task["change_id"])
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
            if host.session_provenance and host.session_provenance["pi_entry"]:
                entry = host.session_provenance["pi_entry"]
                write_run(
                    archive,
                    f"{RUNS_PATH}/{host.root_invocation_id or host.invocation_id}/pi/{entry['digest'].removeprefix('sha256:')}.ts",
                    entry["content"].encode(),
                )
            record = {
                "schema_version": 3,
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
                "pi_provenance": {
                    key: value
                    for key, value in host.session_provenance.items()
                    if key != "pi_entry"
                }
                | {
                    "pi_entry": {
                        "path": host.session_provenance["pi_entry"]["path"],
                        "digest": host.session_provenance["pi_entry"]["digest"],
                        "catalog_digest": host.session_provenance["pi_entry"][
                            "catalog"
                        ]["digest"],
                    }
                    if host.session_provenance["pi_entry"]
                    else None,
                }
                if host.session_provenance
                else None,
                "relayed_run_id": None,
                "status": "started",
            }
            # A build catalog is not evidence of Pi extension loading or tool execution. Only an explicitly supplied,
            # verified selection can provide that provenance; otherwise it stays unknown.
            if change and result is None and task and _belongs_to(task, change):
                change.setdefault("runs", []).append(relative)
                write_status(host.project_root, change)
        if result is not None:
            record.update(
                status=result["status"], result=result, relayed_run_id=relayed_run_id
            )
            record["artifacts"] = _archive_artifacts(
                host.project_root, archive, host.invocation_id, result
            )
        write_run(archive, relative, (canonical(record) + "\n").encode())


def _belongs_to(task: dict, change: dict) -> bool:
    """Whether a mutating request is part of ``change``: it names the change, or it carries
    exactly the change's recorded intent."""
    if task.get("change_id") is not None:
        return task["change_id"] == change["change_id"]
    return (
        task.get("task") == change.get("task")
        and all(
            field not in task or task[field] == change.get(field)
            for field in ("constraints", "focus_id")
        )
        and "target_id" in task
        and task["target_id"] == (change.get("target_id") or change.get("target_hint"))
    )


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
