"""Host-owned change state and discovery metadata for Git worktrees.

A linked worktree is one candidate change. Its primary-owned status is never Spec
authority and is never part of a delivered Git tree. Live inventory joins Git
worktree incarnations to primary status, including unmanaged worktrees.
"""

from __future__ import annotations

import copy
import os
import re
import stat
import subprocess
import tempfile
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, overload

from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError, identifier
from ..spec.typed_data import canonical, checked_path, decode
from .status_store import (
    STATUS_PATH,
    all_status,
    read_status,
    status_path as status_path,
    write_status,
)

STATE_PATH = ".concorde/worktree.json"
REGISTRY_PATH = ".concorde/worktrees.json"
WORK_PATH = ".concorde/work"
DELIVERIES_PATH = ".concorde/deliveries"
LOCAL_PATHS = (
    STATE_PATH,
    REGISTRY_PATH,
    STATUS_PATH,
    WORK_PATH,
    DELIVERIES_PATH,
    ".concorde/runs",
    # Historical local artifacts remain excluded from deliverable trees; no producer remains.
    ".concorde/topology-proposals",
    ".concorde/*.legacy-archive",
)
GUIDANCE_START = "\n<!-- concorde-change-worktree:start -->\n"
GUIDANCE_END = "<!-- concorde-change-worktree:end -->\n"
GUIDANCE_FILES = ("AGENTS.md",)
# Historical status retains its original ownership map; this is admission, not creation.
HISTORICAL_GUIDANCE_FILES = ("AGENTS.md", "CLAUDE.md")


def git(
    root: Path,
    *arguments: str,
    input: str | None = None,
    env: dict | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ("git", "-C", str(root), *arguments),
        input=input,
        capture_output=True,
        text=True,
        env=env,
    )
    if check and result.returncode:
        raise SpecError(
            "Git worktree operation failed: " + result.stderr.strip(),
            "workspace_mismatch",
        )
    return result


def git_value(root: Path, *arguments: str) -> str:
    return git(root, *arguments).stdout.strip()


def list_worktrees(root: Path) -> list[dict]:
    result = git(root, "worktree", "list", "--porcelain", "-z", check=False)
    if result.returncode:
        return []
    records = []
    for block in result.stdout.split("\0\0"):
        if not block:
            continue
        fields = {}
        for line in block.split("\0"):
            if line:
                key, _, value = line.partition(" ")
                fields[key] = value
        if "worktree" not in fields or "bare" in fields:
            continue
        branch = fields.get("branch")
        records.append(
            {
                "path": str(Path(fields["worktree"]).resolve()),
                "branch": branch.removeprefix("refs/heads/") if branch else None,
                "head": fields.get("HEAD"),
                "locked": "locked" in fields,
                "alive": Path(fields["worktree"]).is_dir() and "prunable" not in fields,
            }
        )
    return records


def workspace_identity(root: Path) -> tuple[dict | None, dict | None]:
    if not root.is_dir():
        raise SpecError(
            "workspace is missing; use previously bound primary authority or restore it",
            "primary_unavailable",
        )
    records = list_worktrees(root)
    if not records:
        if (root / ".git").exists() or (root / ".git").is_symlink():
            raise SpecError(
                "Git primary authority is unavailable; restore it before retrying",
                "primary_unavailable",
            )
        return None, None
    current = next(
        (item for item in records if item["path"] == str(root.resolve())), None
    )
    if current is None:
        raise SpecError(
            "An operation must start at its Git worktree root", "workspace_mismatch"
        )
    common = git_value(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    primary = None
    for item in records:
        if not item["alive"]:
            continue
        gitdir = git(Path(item["path"]), "rev-parse", "--absolute-git-dir", check=False)
        if (
            gitdir.returncode == 0
            and Path(gitdir.stdout.strip()).resolve() == Path(common).resolve()
        ):
            primary = item
            break
    if primary is None:
        raise SpecError(
            "primary unavailable; restore its Git worktree and retry",
            "primary_unavailable",
        )
    return primary, current


_LOCKS: dict[str, threading.RLock] = {}
_LOCK_DEPTH = threading.local()


@contextmanager
def repository_lock(root: Path):
    """Serialize coordinator writes, reentrant within one host thread."""
    common = git(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False
    )
    key = common.stdout.strip() if common.returncode == 0 else str(root.resolve())
    lock = _LOCKS.setdefault(key, threading.RLock())
    with lock:
        depths = getattr(_LOCK_DEPTH, "values", {})
        _LOCK_DEPTH.values = depths
        if depths.get(key, 0):
            depths[key] += 1
            try:
                yield
            finally:
                depths[key] -= 1
            return
        import fcntl

        location = (
            Path(key) / "concorde-worktrees.lock" if common.returncode == 0 else None
        )
        if location is None:
            yield
            return
        with location.open("a+b") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            depths[key] = 1
            try:
                yield
            finally:
                depths.pop(key)
                fcntl.flock(stream, fcntl.LOCK_UN)


def worktree_incarnation(root: Path, *, create: bool = False) -> str | None:
    """A narrow identity token in Git admin storage, never candidate task state.

    Git removes this token with the worktree admin directory. Recreating even the
    same path, branch and commit therefore cannot inherit the old incarnation.
    Creation is confined to locked registration or explicitly accepted migration.
    """
    directory = Path(git_value(root, "rev-parse", "--absolute-git-dir"))
    path = checked_path(directory, "concorde-incarnation")
    if not path.exists():
        if not create:
            return None
        from .status_store import atomic_write

        with repository_lock(root):
            if not path.exists():
                atomic_write(directory, path.name, str(uuid.uuid4()).encode())
    token = path.read_text()
    try:
        if str(uuid.UUID(token)) != token:
            raise ValueError("noncanonical token")
    except ValueError as error:
        raise SpecError(
            "invalid worktree incarnation", "invalid_worktree_state"
        ) from error
    return "incarnation:" + token


def _write_json(root: Path, relative: str, value: dict) -> None:
    apply_files(
        root, [file_change(root, relative, canonical(value) + "\n")], {relative}
    )


def _exclude_control_files(root: Path) -> None:
    common = git(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False
    )
    if common.returncode:
        return
    # Git's shared local exclude file is deliberately outside the delivered tree.
    directory = Path(common.stdout.strip()) / "info"
    directory.mkdir(exist_ok=True)
    path = directory / "exclude"
    if path.is_symlink():
        raise SpecError("Git exclude file must not be a symlink", "unsafe_path")
    before = path.read_text() if path.exists() else ""
    missing = [
        "/" + item for item in LOCAL_PATHS if "/" + item not in before.splitlines()
    ]
    if missing:
        with path.open("a") as stream:
            stream.write(
                ("\n" if before and not before.endswith("\n") else "")
                + "# Concorde local worktree control state\n"
                + "\n".join(missing)
                + "\n"
            )


@overload
def read_change(root: Path, *, required: Literal[True]) -> dict: ...


@overload
def read_change(root: Path, *, required: Literal[False] = False) -> dict | None: ...


@overload
def read_change(root: Path, *, required: bool) -> dict | None: ...


def read_change(root: Path, *, required: bool = False) -> dict | None:
    legacy = checked_path(root, STATE_PATH)
    if legacy.exists():
        historical = decode(legacy.read_text())
        if isinstance(historical, dict) and historical.get("schema_version") == 1:
            raise SpecError(
                "schema-1 worktree history requires explicit archival",
                "unsupported_worktree_version",
            )
        raise SpecError(
            "legacy lifecycle state requires migrate-status --apply",
            "migration_required",
        )
    primary, current = workspace_identity(root)
    if (
        primary is not None
        and primary["path"] != str(root.resolve())
        and checked_path(root, ".concorde/runs").exists()
    ):
        raise SpecError(
            "candidate-local durable runs require explicit migration",
            "migration_required",
        )
    git_id = worktree_incarnation(root) if current else None
    located = [
        item for item in all_status(root) if item.get("path") == str(root.resolve())
    ]
    if current and any(
        not str(item.get("git_worktree_id", "")).startswith("incarnation:")
        for item in located
    ):
        raise SpecError(
            "pathname-only task identity requires explicit archival and re-registration",
            "migration_required",
        )
    candidates = [
        item
        for item in located
        if item.get("git_worktree_id") == git_id and (not current or git_id is not None)
    ]
    matches = [
        item for item in candidates if item.get("status") not in {"merged", "delivered"}
    ]
    if not matches and primary is not None and primary["path"] != str(root.resolve()):
        # A retained candidate remains inspectable; terminal primary tasks do not own
        # every future direct task in that same primary workspace.
        matches = [
            item
            for item in candidates
            if item.get("cleanup", {}).get("status") != "removed"
        ]
    if len(matches) > 1:
        raise SpecError("multiple tasks claim this workspace", "workspace_mismatch")
    if not matches:
        if checked_path(root, STATE_PATH).exists():
            raise SpecError(
                "legacy lifecycle state requires migrate-status --apply",
                "migration_required",
            )
        if required:
            raise SpecError(
                "this operation requires a managed change worktree", "missing_change"
            )
        return None
    state = matches[0]
    if isinstance(state, dict) and state.get("schema_version") == 1:
        raise SpecError(
            "legacy worktree state requires explicit archival and fresh validation; "
            "schema 1 cannot resume under the Operations profile",
            "unsupported_worktree_version",
        )
    if (
        not isinstance(state, dict)
        or type(state.get("schema_version")) is not int
        or state["schema_version"] != 2
        or state.get("path") != str(root.resolve())
        or not isinstance(state.get("targets"), dict)
        or not isinstance(state.get("guidance"), dict)
        or not isinstance(state.get("blockers"), list)
        or not isinstance(state.get("phase"), str)
        or not state["phase"]
        or not isinstance(state.get("status"), str)
        or not state["status"]
    ):
        raise SpecError(
            "worktree state has an invalid identity or schema", "invalid_worktree_state"
        )
    try:
        identifier(state.get("change_id"))
        for field in ("branch", "base_branch", "base_commit", "primary_worktree"):
            if field not in state or (
                state[field] is not None
                and (not isinstance(state[field], str) or not state[field].strip())
            ):
                raise ValueError(f"invalid or missing {field}")
        if not {"target_id", "focus_id", "task"}.issubset(state):
            raise ValueError("missing owner fields")
        if state["target_id"] is not None:
            identifier(state["target_id"])
            if not isinstance(state.get("task"), str) or not state["task"].strip():
                raise ValueError("bound owner requires a task")
        elif state["targets"]:
            raise ValueError("target progress requires an owner")
        if state["focus_id"] is not None:
            identifier(state["focus_id"])
        if state.get("target_hint") is not None:
            identifier(state["target_hint"])
        if state.get("task") is not None and (
            not isinstance(state["task"], str) or not state["task"].strip()
        ):
            raise ValueError("invalid task")
        if not isinstance(state.get("constraints"), list) or any(
            not isinstance(item, str) or not item.strip()
            for item in state["constraints"]
        ):
            raise ValueError("invalid constraints")
    except ValueError as error:
        raise SpecError(
            f"worktree owner state is invalid: {error}", "invalid_worktree_state"
        ) from error
    from ..issues.references import receipt
    from ..issues.store import resolve_report
    from ..spec.issue_shapes import BLOCKER
    from ..spec.repository import digest
    from ..spec.typed_data import check_schema

    try:
        for item in state.get("issue_blockers", []):
            check_schema(item["blocker"], BLOCKER)
            expected = digest(
                {
                    "change_id": state["change_id"],
                    "target_id": item["target_id"],
                    "scope_id": item["scope_id"],
                    "phase": item["phase"],
                    "issue_id": item["blocker"]["issue_id"],
                }
            )
            observation = resolve_report(root, receipt(item["blocker"]))
            if (
                item["id"] != expected
                or item["status"] not in {"open", "resolved", "superseded"}
                or observation["source"]["context_id"] not in item["contexts"]
            ):
                raise ValueError("Issue blocker identity or provenance changed")
            if item["status"] == "superseded":
                reassessment = item.get("reassessment", {})
                if (
                    item["phase"] != "specify"
                    or reassessment.get("phase") != "context-solve"
                    or reassessment.get("reason") != "retired_author_prerequisite"
                    or not re.fullmatch(
                        r"sha256:[0-9a-f]{64}", reassessment.get("context_id", "")
                    )
                    or not re.fullmatch(
                        r"sha256:[0-9a-f]{64}", reassessment.get("spec_digest", "")
                    )
                ):
                    raise ValueError("invalid retired-prerequisite supersession")
    except (ValueError, KeyError, TypeError) as error:
        raise SpecError(
            f"invalid Issue blocker history: {error}", "invalid_worktree_state"
        ) from error
    primary, current = workspace_identity(root)
    if current is not None and (
        primary is None or state.get("primary_worktree") != primary["path"]
    ):
        raise SpecError(
            "worktree state belongs to a different branch or primary worktree",
            "workspace_mismatch",
        )
    if set(state["guidance"]) - set(HISTORICAL_GUIDANCE_FILES):
        raise SpecError(
            "worktree guidance names an unsupported file", "invalid_worktree_state"
        )
    if any(
        not isinstance(value, dict) or type(value.get("created")) is not bool
        for value in state["guidance"].values()
    ) or any(not isinstance(value, dict) for value in state["targets"].values()):
        raise SpecError(
            "worktree progress or guidance has an invalid shape",
            "invalid_worktree_state",
        )
    for target in state["targets"].values():
        verify_target_owner(state, target)
    return state


def _summary(item: dict, primary_path: str) -> dict:
    state = None
    invalid = False
    if item["path"] != primary_path:
        try:
            state = read_change(Path(item["path"]))
        except (ValueError, OSError):
            invalid = True
    return {
        "path": item["path"],
        "branch": item["branch"],
        "head": item["head"],
        "managed": state is not None,
        "locked": item["locked"],
        "change_id": state["change_id"] if state else None,
        "target_id": state.get("target_id") if state else None,
        "task": (state.get("task") or "")[:300] if state else "",
        "phase": state.get("phase") if state else None,
        "status": state.get("status")
        if state
        else "invalid"
        if invalid
        else "unmanaged",
        "outcome": state.get("outcome") if state else None,
    }


def _inventory(root: Path, *, persist: bool) -> dict:
    primary, current = workspace_identity(root)
    live = {item["path"]: item for item in list_worktrees(root) if item["alive"]}
    return {
        "schema_version": 2,
        "primary_worktree": primary["path"] if primary else None,
        "primary_branch": primary["branch"] if primary else None,
        "worktrees": [
            _summary(item, primary["path"] if primary else "")
            for item in live.values()
            if not primary or item["path"] != primary["path"]
        ],
    }


def refresh_registry(root: Path, *, persist: bool = True) -> dict:
    if not persist:
        return _inventory(root, persist=False)
    with repository_lock(root):
        return _inventory(root, persist=True)


def save_change(
    root: Path, state: dict, *, publish: bool = True, locked: bool = False
) -> None:
    if state.get("path") != str(root.resolve()):
        raise SpecError(
            "cannot move change ownership between worktrees", "workspace_mismatch"
        )

    def write():
        _exclude_control_files(root)
        _, current = workspace_identity(root)
        if current:
            if state.get("git_worktree_id") != worktree_incarnation(root):
                raise SpecError(
                    "task belongs to another worktree incarnation", "workspace_mismatch"
                )
            state["branch"] = current["branch"]
        write_status(root, state)
        if publish:
            _inventory(root, persist=True)

    if locked:
        write()
    else:
        with repository_lock(root):
            write()


def strip_guidance(content: str) -> str:
    if GUIDANCE_START not in content:
        if "<!-- concorde-change-worktree:" in content:
            raise SpecError(
                "worktree guidance markers were modified", "invalid_worktree_state"
            )
        return content
    if content.count(GUIDANCE_START) != 1 or content.count(GUIDANCE_END) != 1:
        raise SpecError(
            "worktree guidance markers are ambiguous", "invalid_worktree_state"
        )
    start = content.index(GUIDANCE_START)
    end = content.index(GUIDANCE_END, start) + len(GUIDANCE_END)
    return content[:start] + content[end:]


def _guidance_changes(root: Path, state: dict) -> list[dict]:
    block = (
        GUIDANCE_START + "## Concorde change worktree\n\n"
        "This agent session starts in a secondary worktree containing an unfinished candidate change.\n"
        f"The primary coordinator records its lifecycle in `{STATUS_PATH}/{state['change_id']}.json`. Inspect status directly.\n"
        "The caller selects retained Operations and their explicit targets. Partial Spec and\n"
        "implementation edits are draft state; resume the recorded phase before claiming completion.\n\n"
        "You may invoke `concorde-deliver` from this source worktree or the destination worktree.\n"
        f"The destination is the primary worktree: {state['primary_worktree']}.\n"
        "The session's initial working directory must be one of those two participants; a third\n"
        "worktree cannot deliver this change by redirecting or forwarding its invocation.\n"
        "Delivery creates concorde/delivered/<change_id> and leaves the primary branch unchanged.\n"
        "The host removes this source unless keep_worktree:true was explicitly requested.\n"
        "End this session after removal. Only an explicit user request to the sole primary writer\n"
        "authorizes a separate merge_primary:true request from the primary session.\n"
        "Validation and selected reviews establish current readiness; no Operation delivers automatically.\n"
        + GUIDANCE_END
    )
    changes = []
    for relative in GUIDANCE_FILES:
        path = checked_path(root, relative)
        before = path.read_bytes().decode("utf-8") if path.exists() else ""
        state["guidance"][relative] = {"created": not path.exists()}
        changes.append(file_change(root, relative, strip_guidance(before) + block))
    return changes


def ensure_change(
    root: Path,
    *,
    task: dict | None = None,
    change_id: str | None = None,
    allow_primary: bool = False,
    mode: str = "operation",
) -> dict:
    if mode not in {"operation", "maintenance", "direct"}:
        raise SpecError("invalid task mode", "invalid_input")
    existing = read_change(root)
    if (
        change_id is not None
        and existing is None
        and read_status(root, change_id) is not None
    ):
        raise SpecError(
            "stable change identity already belongs to another workspace",
            "workspace_mismatch",
        )
    if existing is not None:
        if change_id is not None and change_id != existing["change_id"]:
            raise SpecError(
                "this worktree already belongs to another change",
                "incompatible_handoff",
            )
        return existing
    legacy = checked_path(root, ".concorde/attempts")
    if legacy.exists() and any(legacy.iterdir()):
        raise SpecError(
            "legacy attempt state is not supported; remove it explicitly before adopting this worktree",
            "legacy_attempt",
        )
    primary, current = workspace_identity(root)
    secondary = (
        current is not None
        and primary is not None
        and current["path"] != primary["path"]
    )
    if not secondary and not allow_primary:
        raise SpecError(
            "a change requires its own linked worktree", "workspace_mismatch"
        )
    if secondary and current is not None and not current["branch"]:
        raise SpecError(
            "a change worktree requires an attached branch", "detached_worktree"
        )
    if current is not None:
        tracked = git_value(
            root,
            "ls-files",
            "--",
            STATE_PATH,
            REGISTRY_PATH,
            WORK_PATH,
            DELIVERIES_PATH,
        )
        if tracked:
            raise SpecError(
                "worktree control paths must not be tracked project files",
                "invalid_worktree_state",
            )
    state = {
        "schema_version": 2,
        "change_id": change_id or "change." + str(uuid.uuid4()),
        "path": str(root.resolve()),
        "branch": current["branch"] if current else None,
        "git_worktree_id": None,
        "primary_worktree": primary["path"] if primary else None,
        "base_commit": current["head"] if current else None,
        "base_branch": primary["branch"] if primary else None,
        "target_id": None,
        "target_hint": (task or {}).get("target_id"),
        "focus_id": (task or {}).get("focus_id"),
        "task": (task or {}).get("task"),
        "constraints": (task or {}).get("constraints", []),
        "phase": "created",
        "status": "active",
        "outcome": None,
        "blockers": [],
        "targets": {},
        "guidance": {},
        "validated_tree": None,
        "validation": None,
        "mode": mode,
        "candidate_worktree": str(root.resolve()) if secondary else None,
        "child": None,
        "runs": [],
        "manual_merge": None,
        "delivery": None,
        "cleanup": {"status": "pending" if secondary else "not_needed"},
    }
    identifier(state["change_id"])
    with repository_lock(root):
        observed = read_change(root)
        if observed is not None:
            if change_id is not None and observed["change_id"] != change_id:
                raise SpecError(
                    "another invocation adopted this worktree", "incompatible_handoff"
                )
            return observed
        if read_status(root, state["change_id"]) is not None:
            raise SpecError(
                "stable change identity already belongs to another workspace",
                "workspace_mismatch",
            )
        state["git_worktree_id"] = (
            worktree_incarnation(root, create=True) if current else None
        )
        _exclude_control_files(root)
        changes = (
            _guidance_changes(root, state) if secondary and mode == "operation" else []
        )
        if changes:
            # The generic text transaction replaces files using private temporary modes.
            # Guidance is appended to user-owned files: retain their modes on success and
            # after rollback, just as the transaction retains their original bytes.
            modes = {
                item["path"]: stat.S_IMODE(
                    checked_path(root, item["path"]).stat().st_mode
                )
                for item in changes
                if item["before_digest"] is not None
            }

            def restore_modes():
                for relative, mode in modes.items():
                    checked_path(root, relative).chmod(mode)

            def register():
                restore_modes()
                write_status(root, state, create=True)

            try:
                apply_files(
                    root,
                    changes,
                    {item["path"] for item in changes},
                    verify=register,
                )
            finally:
                restore_modes()
        else:
            write_status(root, state, create=True)
        _inventory(root, persist=True)
    return state


def submodule_paths(root: Path) -> tuple[str, ...]:
    """The submodule paths declared by ``.gitmodules``, in declaration order."""
    if not (root / ".gitmodules").is_file():
        return ()
    listing = git(
        root,
        "config",
        "-f",
        ".gitmodules",
        "--get-regexp",
        r"^submodule\..*\.path$",
        check=False,
    )
    return tuple(
        line.split(None, 1)[1] for line in listing.stdout.splitlines() if " " in line
    )


def replicate_reference_checkouts(source_root: Path, destination_root: Path) -> None:
    """Give a new linked worktree the primary's vendored reference checkouts without the network.

    A linked worktree starts with every submodule path empty. The external references a Module
    declares must exist in every candidate worktree, so the readable files of each submodule
    checkout are copied from the primary (its git link, dot-entries, excluded directories and
    media stay behind). Git ignores files below an uninitialized gitlink, so the copy never
    enters the candidate's index or delivery.
    """
    from ..spec.repository import REFERENCE_SKIPPED_SUFFIXES, expand_entry

    for relative in submodule_paths(source_root):
        source = source_root / relative
        if not source.is_dir():
            continue
        for path in expand_entry(
            source_root,
            relative.rstrip("/") + "/",
            skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES,
        ):
            copy = destination_root / path
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes((source_root / path).read_bytes())


def create_worktree(
    root: Path, task: dict, *, package_root: Path | None = None
) -> dict:
    primary, current = workspace_identity(root)
    if (
        primary is None
        or current is None
        or current["path"] != primary["path"]
        or not primary["branch"]
    ):
        raise SpecError(
            "create a change from the primary worktree's attached branch",
            "workspace_mismatch",
        )
    change_id = "change." + str(uuid.uuid4())
    branch = "concorde/" + change_id.removeprefix("change.")
    directory = Path(tempfile.mkdtemp(prefix="concorde-worktree-")) / "project"
    git(root, "worktree", "add", "-b", branch, str(directory), current["head"])
    replicate_reference_checkouts(root, directory)
    maintenance = package_root is not None and package_root.resolve() == root.resolve()
    state = ensure_change(
        directory,
        task=task,
        change_id=change_id,
        mode="maintenance" if maintenance else "operation",
    )
    # A source candidate is built by its fresh Concorde-catalog-free writer using its own
    # launcher. Never render candidate outputs with the primary's Python module.
    return {
        "path": str(directory),
        "branch": branch,
        "base_commit": current["head"],
        "change_id": state["change_id"],
        "primary_worktree": primary["path"],
    }


def resume_owner(state: dict, task: dict) -> dict:
    """Restore omitted owner fields; a request cannot replace persisted intent or routing."""
    result = dict(task)
    if state["task"] is None:
        return result
    fields = ["task", "constraints", "focus_id"]
    if state["target_id"] is not None:
        fields.insert(0, "target_id")
    for field in fields:
        if field in task and task[field] != state[field]:
            raise SpecError(
                f"resume {field} conflicts with the recorded change owner",
                "incompatible_handoff",
                field,
            )
        if state[field] is not None:
            result[field] = copy.deepcopy(state[field])
    if state["target_id"] is None and state.get("target_hint") is not None:
        if task.get("target_id", state["target_hint"]) != state["target_hint"]:
            raise SpecError(
                "resume target_id conflicts with the recorded initial selection",
                "incompatible_handoff",
                field="target_id",
            )
        result.setdefault("target_id", state["target_hint"])
    return result


def bind_owner(root: Path, task: dict, *, coordinated: bool = False) -> dict:
    state = read_change(root, required=True)
    if task.get("change_id") not in {None, state["change_id"]}:
        raise SpecError("change ID does not own this worktree", "incompatible_handoff")
    for field in ("target_id", "task"):
        if not isinstance(task.get(field), str) or not task[field].strip():
            raise SpecError(f"owner binding requires {field}", "invalid_input", field)
    identifier(task["target_id"])
    if state["target_id"] is None:
        if state["task"] is not None:
            for field, value in (
                ("task", task["task"]),
                ("constraints", task.get("constraints", [])),
            ):
                if state[field] != value:
                    raise SpecError(
                        f"owner binding conflicts with recorded {field}",
                        "incompatible_handoff",
                        field,
                    )
        state.update(
            target_id=task["target_id"],
            focus_id=task.get("focus_id"),
            task=task["task"],
            constraints=task.get("constraints", []),
        )
        save_change(root, state)
    elif not coordinated:
        resume_owner(state, {"focus_id": None, "constraints": [], **task})
    return state


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
    change = read_change(root, required=True)
    existing = change["targets"].get(target_id)
    if existing is not None:
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
    with repository_lock(root):
        change = read_change(root, required=True)
        identifier(value["target_id"])
        verify_target_owner(change, value)
        previous = change["targets"].get(value["target_id"], {})
        if value.get("revision", 0) != previous.get("revision", 0):
            raise SpecError(
                "target progress changed; reread before updating", "stale_status"
            )
        change["targets"][value["target_id"]] = copy.deepcopy(value)
        save_change(root, change)
        value["revision"] = change["targets"][value["target_id"]]["revision"]


def progress(
    root: Path,
    *,
    phase: str | None = None,
    status: str | None = None,
    outcome: str | None = None,
    blockers=None,
    invalidate: bool = False,
) -> None:
    state = read_change(root)
    if state is None:
        return
    if phase is not None:
        state["phase"] = phase
    if status is not None:
        state["status"] = status
    state["outcome"] = outcome
    if blockers is not None:
        unresolved = [
            item["blocker"]
            for item in state.get("issue_blockers", [])
            if item["status"] == "open"
        ]
        state["blockers"] = list(
            {canonical(gap): gap for gap in [*unresolved, *blockers]}.values()
        )
    if invalidate:
        state["validated_tree"] = None
        state["validation"] = None
    save_change(root, state)


def blocker_scope(state: dict, target_id: str, task: str | None) -> str | None:
    """Bind a request to accepted candidate work, not an ID hashed from task wording.

    Root intent, evolving component intent and required consumer review intent all select the
    same durable Module work scope. A separately requested unrelated task cannot borrow it.
    """
    if task is None:
        return "module:" + target_id
    intents = []
    if state.get("target_id") == target_id:
        intents.append(state.get("task"))
    intents.append(state.get("targets", {}).get(target_id, {}).get("task"))
    intents.append(state.get("review_intents", {}).get(target_id, {}).get("task"))
    for target in state.get("targets", {}).values():
        intents.append(target.get("coordination", {}).get(target_id, {}).get("task"))
    for name in ("shared_spec_reviews", "shared_implementation_reviews"):
        for consumers in state.get(name, {}).values():
            intents.append(consumers.get(target_id, {}).get("task"))
    if task in intents:
        return "module:" + target_id
    return next(
        (
            item["scope_id"]
            for item in state.get("issue_blockers", [])
            if item["target_id"] == target_id and item["task"] == task
        ),
        None,
    )


def record_task_gaps(
    root: Path,
    target_id: str,
    task: str,
    phase: str,
    blockers,
    spec_digest: str,
    *,
    review_input_digest: str | None = None,
    spec_resolution: dict | None = None,
    scope_id: str | None = None,
    assessment_context_id: str | None = None,
) -> None:
    """Retain Issue dependencies by change/Module/phase/Issue, never by task wording.

    A successful fresh assessment releases a dependency, not the referenced Issue. Reports and
    their immutable observations survive independently. Caller admission protects unrelated review
    intents; one candidate has one evolving work scope for each participating Module.
    """
    from ..issues.references import receipt, requires_contract_repair
    from ..issues.store import resolve_report
    from ..spec.repository import digest

    state = read_change(root)
    if state is None:
        return
    history = state.setdefault("issue_blockers", [])
    scope_id = scope_id or blocker_scope(state, target_id, task)
    if scope_id is None:
        if not blockers:
            return
        scope_id = (
            "independent:"
            + resolve_report(root, receipt(blockers[0]))["source"]["invocation_id"]
        )
    existing = {item["id"]: item for item in history}
    for blocker in blockers:
        observation = resolve_report(root, receipt(blocker))
        context_id = observation["source"]["context_id"]
        key = digest(
            {
                "change_id": state["change_id"],
                "target_id": target_id,
                "scope_id": scope_id,
                "phase": phase,
                "issue_id": blocker["issue_id"],
            }
        )
        if key not in existing:
            item = {
                "id": key,
                "target_id": target_id,
                "task": task,
                "phase": phase,
                "scope_id": scope_id,
                "blocker": dict(blocker),
                "status": "open",
                "contexts": [],
                "spec_digest": spec_digest,
            }
            history.append(item)
            existing[key] = item
        item = existing[key]
        item.update(
            blocker=dict(blocker), task=task, status="open", spec_digest=spec_digest
        )
        if spec_resolution is not None:
            evidence = {
                key: value for key, value in spec_resolution.items() if key != "sources"
            }
            evidence["sources"] = [
                {key: value for key, value in source.items() if key != "content"}
                for source in spec_resolution["sources"]
            ]
            item.setdefault("context_evidence", {})[context_id] = evidence
        if review_input_digest is not None:
            item["review_input_digest"] = review_input_digest
        if context_id not in item["contexts"]:
            item["contexts"].append(context_id)
    for item in history:
        # A current assessment can replace the retired prerequisite, not prove
        # that the old author succeeded or that its independently recorded Issue is fixed.
        reassessed_author = (
            phase == "context-solve"
            and item["phase"] == "specify"
            and assessment_context_id is not None
            and item["target_id"] == target_id
            and item["scope_id"] == scope_id
            and item["status"] == "open"
            and not blockers
        )
        if reassessed_author:
            observation = resolve_report(root, receipt(item["blocker"]))
            source = observation["source"]
            if (
                item.get("task") != task
                or source.get("target_id") != target_id
                or source.get("phase") != "specify"
                or source.get("operation") != "concorde-specify"
            ):
                raise SpecError(
                    "retired author relation has ambiguous attribution",
                    "invalid_worktree_state",
                )
            item["status"] = "superseded"
            item["reassessment"] = {
                "phase": phase,
                "context_id": assessment_context_id,
                "spec_digest": spec_digest,
                "reason": "retired_author_prerequisite",
            }
            continue
        if (
            item["target_id"] == target_id
            and item["scope_id"] == scope_id
            and item["status"] == "open"
            and item["phase"] == phase
            and not blockers
            and (
                item.get("spec_digest") != spec_digest
                or (
                    review_input_digest is not None
                    and item.get("review_input_digest") is not None
                    and item["review_input_digest"] != review_input_digest
                )
                or (
                    phase in {"spec-review", "code-review"}
                    and not requires_contract_repair(root, [item["blocker"]])
                )
            )
        ):
            item["status"] = "resolved"
    state["blockers"] = [
        item["blocker"] for item in history if item["status"] == "open"
    ]
    target = state["targets"].get(target_id)
    if target is not None:
        target["blockers"] = [
            item["blocker"]
            for item in history
            if item["status"] == "open" and item["target_id"] == target_id
        ]
    if blockers:
        state["validated_tree"] = None
        state["validation"] = None
    save_change(root, state)


def unchanged_task_gaps(
    root: Path,
    target_id: str,
    task: str,
    phase: str,
    spec_digest: str,
    *,
    review_input_digest: str | None = None,
) -> list[dict]:
    from ..issues.references import requires_contract_repair

    state = read_change(root)
    scope = blocker_scope(state or {}, target_id, task)
    return [
        dict(item["blocker"])
        for item in (state or {}).get("issue_blockers", [])
        if item["status"] == "open"
        and item["target_id"] == target_id
        and item["scope_id"] == scope
        and item["phase"] == phase
        and item.get("spec_digest") == spec_digest
        and (
            phase != "code-review" or requires_contract_repair(root, [item["blocker"]])
        )
        and (
            review_input_digest is None
            or phase not in {"spec-review", "code-review"}
            or item.get("review_input_digest") in {None, review_input_digest}
        )
    ]


def work_path(target_id: str, name: str) -> str:
    identifier(target_id)
    if name not in {"plan.md", "checklist.md", "issue-drafts.json"}:
        raise SpecError("unsupported work artifact", "invalid_input")
    return f"{WORK_PATH}/{target_id}/{name}"


def workspace_context(
    root: Path,
    *,
    persist: bool = False,
    target_id: str | None = None,
    task: str | None = None,
) -> dict:
    inventory = refresh_registry(root, persist=persist)
    primary, current = workspace_identity(root)
    state = read_change(root)
    coordination = (
        state["targets"].get(state["target_id"], {}).get("coordination", {})
        if state
        else {}
    )
    return {
        "kind": "unversioned"
        if current is None
        else "primary"
        if primary is not None and current["path"] == primary["path"]
        else "change",
        "current_worktree": str(root.resolve()),
        "current_branch": current["branch"] if current else None,
        "primary_worktree": inventory["primary_worktree"],
        "primary_branch": inventory["primary_branch"],
        "change_id": state["change_id"] if state else None,
        "phase": state["phase"] if state else None,
        "status": state["status"] if state else None,
        "outcome": state.get("outcome") if state else None,
        "blockers": [
            item["blocker"]
            for item in (state or {}).get("issue_blockers", [])
            if item["status"] == "open"
            and (
                target_id is None
                or (
                    item["target_id"] == target_id
                    and item["scope_id"] == blocker_scope(state or {}, target_id, task)
                )
            )
        ],
        "components": [
            {
                "target_id": target_id,
                "spec_status": record["spec_status"],
                "implementation_status": record["implementation_status"],
                "outcome": record["outcome"],
            }
            for target_id, record in coordination.items()
        ],
        "active_worktrees": inventory["worktrees"],
    }


def snapshot_tree(root: Path, state: dict | None = None) -> str | None:
    """Capture exact deliverable bytes without changing the caller's Git index."""
    if not list_worktrees(root):
        return None
    state = state if state is not None else read_change(root)
    with tempfile.TemporaryDirectory(prefix="concorde-index-") as directory:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(directory) / "index")}
        git(root, "read-tree", "HEAD", env=env)
        git(root, "add", "-A", "--", ".", env=env)
        for path in LOCAL_PATHS:
            tracked = git(root, "ls-files", "-z", "--", path, env=env).stdout.split(
                "\0"
            )
            for member in filter(None, tracked):
                git(root, "update-index", "--force-remove", "--", member, env=env)
        for relative, metadata in (state or {}).get("guidance", {}).items():
            path = checked_path(root, relative)
            if not path.exists():
                continue
            before = path.read_bytes().decode("utf-8")
            clean = strip_guidance(before)
            if metadata["created"] and not clean:
                git(root, "update-index", "--force-remove", "--", relative, env=env)
            elif before != clean:
                blob = git(
                    root, "hash-object", "-w", "--stdin", input=clean
                ).stdout.strip()
                mode = "100755" if path.stat().st_mode & 0o111 else "100644"
                git(
                    root,
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"{mode},{blob},{relative}",
                    env=env,
                )
        return git(root, "write-tree", env=env).stdout.strip()
