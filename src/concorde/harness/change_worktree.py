"""Candidate worktrees: the change status of each worktree, its lifecycle and the boundary check.

A linked worktree is one candidate change. Its primary-owned status is never Spec
authority and is never part of a delivered Git tree. Live inventory joins Git
worktree incarnations to primary status records, including unmanaged worktrees, and
reads no file inside another worktree. Provider records live in declared provider
sections that this Module stores but never interprets.
"""

from __future__ import annotations

from .timing import Span, timed

import copy
import os
import stat
import subprocess
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, overload

from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError, identifier
from ..spec.typed_data import checked_path
from .status_store import (
    RUNS_PATH,
    STATUS_PATH,
    STATUS_VERSION,
    all_status,
    declare_section as declare_section,
    put_section as put_section,
    read_status,
    section as section,
    status_path as status_path,
    write_status,
)

WORK_PATH = ".concorde/work"
LOCAL_PATHS = (STATUS_PATH, WORK_PATH, RUNS_PATH)
GUIDANCE_START = "\n<!-- concorde-change-worktree:start -->\n"
GUIDANCE_END = "<!-- concorde-change-worktree:end -->\n"
GUIDANCE_FILES = ("AGENTS.md",)


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
    waiting = Span("lock.thread_wait")
    with lock:
        waiting.finish()
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
            with Span("lock.repository_wait"):
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
    Creation is confined to locked registration.
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


def _bound(records: list[dict], path: str, token: str | None, primary: str | None):
    """The change statuses bound to the worktree at ``path`` with incarnation ``token``."""
    candidates = [
        item
        for item in records
        if item.get("path") == path and item.get("git_worktree_id") == token
    ]
    matches = [
        item for item in candidates if item.get("status") not in {"merged", "delivered"}
    ]
    if not matches and primary is not None and primary != path:
        # A retained candidate remains inspectable; terminal primary tasks do not own
        # every future direct task in that same primary workspace.
        matches = [
            item
            for item in candidates
            if item.get("cleanup", {}).get("status") != "removed"
        ]
    return matches


def check_lifecycle(state) -> dict:
    """Refuse a change status whose identity, owner or lifecycle fields are malformed."""
    if (
        not isinstance(state, dict)
        or type(state.get("schema_version")) is not int
        or state["schema_version"] != STATUS_VERSION
        or not isinstance(state.get("guidance"), dict)
        or not isinstance(state.get("sections"), dict)
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
    if set(state["guidance"]) - set(GUIDANCE_FILES) or any(
        not isinstance(value, dict) or type(value.get("created")) is not bool
        for value in state["guidance"].values()
    ):
        raise SpecError(
            "worktree guidance has an invalid shape", "invalid_worktree_state"
        )
    return state


def read_change(root: Path, *, required: bool = False) -> dict | None:
    primary, current = workspace_identity(root)
    git_id = worktree_incarnation(root) if current else None
    if current is not None and git_id is None:
        matches = []
    else:
        matches = _bound(
            all_status(root),
            str(root.resolve()),
            git_id,
            primary["path"] if primary else None,
        )
    if len(matches) > 1:
        raise SpecError("multiple tasks claim this workspace", "workspace_mismatch")
    if not matches:
        if required:
            raise SpecError(
                "this operation requires a managed change worktree", "missing_change"
            )
        return None
    state = check_lifecycle(matches[0])
    if current is not None and (
        primary is None or state.get("primary_worktree") != primary["path"]
    ):
        raise SpecError(
            "worktree state belongs to a different branch or primary worktree",
            "workspace_mismatch",
        )
    return state


def _incarnations(root: Path) -> dict[str, str | None]:
    """Linked worktree path -> its incarnation token, read from Git's administrative directories.

    Each linked worktree's administrative directory names the worktree in its ``gitdir`` file
    and holds the token; no file inside any worktree is read.
    """
    common = git(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False
    )
    if common.returncode:
        return {}
    tokens: dict[str, str | None] = {}
    directory = Path(common.stdout.strip()) / "worktrees"
    if not directory.is_dir():
        return tokens
    for admin in sorted(directory.iterdir()):
        try:
            pointer = (admin / "gitdir").read_text().strip()
            path = str(Path(pointer).parent.resolve())
            marker = admin / "concorde-incarnation"
            token = marker.read_text() if marker.is_file() else None
        except OSError:
            continue
        try:
            if token is not None and str(uuid.UUID(token)) != token:
                raise ValueError("noncanonical token")
        except ValueError:
            tokens[path] = "invalid"
            continue
        tokens[path] = None if token is None else "incarnation:" + token
    return tokens


def _summary(
    item: dict, primary_path: str, records: list[dict] | None, token: str | None
) -> dict:
    state = None
    invalid = records is None or token == "invalid"
    if not invalid and item["path"] != primary_path and token is not None:
        matches = _bound(records or [], item["path"], token, primary_path)
        try:
            if len(matches) > 1:
                raise ValueError("several changes claim one worktree")
            state = check_lifecycle(matches[0]) if matches else None
            if state is not None and state.get("primary_worktree") != primary_path:
                raise ValueError("the change belongs to another primary worktree")
        except ValueError:
            state, invalid = None, True
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


def _inventory(root: Path) -> dict:
    """Every live linked worktree, summarized from Git and the primary's status records only."""
    primary, current = workspace_identity(root)
    live = {item["path"]: item for item in list_worktrees(root) if item["alive"]}
    try:
        records = all_status(root) if primary else []
    except ValueError:
        records = None
    tokens = _incarnations(root) if primary else {}
    return {
        "schema_version": 2,
        "primary_worktree": primary["path"] if primary else None,
        "primary_branch": primary["branch"] if primary else None,
        "worktrees": [
            _summary(
                item,
                primary["path"] if primary else "",
                records,
                tokens.get(item["path"]),
            )
            for item in live.values()
            if not primary or item["path"] != primary["path"]
        ],
    }


def refresh_registry(root: Path, *, persist: bool = True) -> dict:
    """The worktree inventory; ``persist`` reads it under the repository lock."""
    if not persist:
        return _inventory(root)
    with repository_lock(root):
        return _inventory(root)


def save_change(root: Path, state: dict, *, locked: bool = False) -> None:
    """Write the change status bound to this worktree; its provider sections are type-checked."""
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
        tracked = git_value(root, "ls-files", "--", WORK_PATH)
        if tracked:
            raise SpecError(
                "worktree control paths must not be tracked project files",
                "invalid_worktree_state",
            )
    state = {
        "schema_version": STATUS_VERSION,
        "change_id": change_id or "change." + str(uuid.uuid4()),
        "mode": mode,
        "path": str(root.resolve()),
        "branch": current["branch"] if current else None,
        "git_worktree_id": None,
        "primary_worktree": primary["path"] if primary else None,
        "base_commit": current["head"] if current else None,
        "base_branch": primary["branch"] if primary else None,
        "candidate_worktree": str(root.resolve()) if secondary else None,
        "target_id": None,
        "target_hint": (task or {}).get("target_id"),
        "focus_id": (task or {}).get("focus_id"),
        "task": (task or {}).get("task"),
        "constraints": (task or {}).get("constraints", []),
        "phase": "created",
        "status": "active",
        "outcome": None,
        "guidance": {},
        "child": None,
        "runs": [],
        "cleanup": {"status": "pending" if secondary else "not_needed"},
        "sections": {},
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


@timed("worktree.create")
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


# The rule that admits a request for a Module other than the change's owner as a component
# request. Planning owns it and registers it when its records load; with none registered no
# such request is admitted.
_COMPONENT_POLICY = None


def register_component_policy(policy) -> None:
    """Register ``policy(repository, change, task) -> bool``; only one rule may be registered."""
    global _COMPONENT_POLICY
    if _COMPONENT_POLICY not in {None, policy}:
        raise SpecError(
            "a component request policy is already registered", "invalid_input"
        )
    _COMPONENT_POLICY = policy


def component_request(repository, change: dict, task: dict) -> bool:
    """Whether ``task`` is a component request of ``change`` under the registered policy."""
    return _COMPONENT_POLICY is not None and bool(
        _COMPONENT_POLICY(repository, change, task)
    )


def bind_owner(root: Path, task: dict, *, component: bool = False) -> dict:
    """Bind a mutating request to the change of this worktree.

    The first request records its owner; a later request must carry the recorded intent,
    except a component request, which is admitted without taking the change's ownership.
    """
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
    elif not component:
        resume_owner(state, {"focus_id": None, "constraints": [], **task})
    return state


def progress(
    root: Path,
    *,
    phase: str | None = None,
    status: str | None = None,
    outcome: str | None = None,
) -> None:
    """Record the lifecycle position of the change bound to this worktree, if any."""
    state = read_change(root)
    if state is None:
        return
    if phase is not None:
        state["phase"] = phase
    if status is not None:
        state["status"] = status
    state["outcome"] = outcome
    save_change(root, state)


def work_path(target_id: str, name: str) -> str:
    identifier(target_id)
    if name not in {"plan.md", "checklist.md", "issue-drafts.json"}:
        raise SpecError("unsupported work artifact", "invalid_input")
    return f"{WORK_PATH}/{target_id}/{name}"


def workspace_context(root: Path, *, persist: bool = False) -> dict:
    """The workspace facts of ``root``: where it is, its change's lifecycle and the other
    live worktrees, from Git and the primary's status records only."""
    inventory = refresh_registry(root, persist=persist)
    primary, current = workspace_identity(root)
    state = read_change(root)
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


# --- the worktree boundary check -----------------------------------------------------------


class WorktreeBoundaryError(ValueError):
    """The requested mutation has no authorized isolated Git worktree."""


@dataclass(frozen=True)
class WorktreeBoundary:
    project_root: str
    repository_root: str
    head: str
    git_dir: str
    common_dir: str
    isolated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _boundary_git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(root), *arguments),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise WorktreeBoundaryError(
            f"cannot execute Git worktree preflight: {error}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise WorktreeBoundaryError(detail)
    value = result.stdout.strip()
    if not value:
        raise WorktreeBoundaryError("Git worktree preflight returned an empty value")
    return value


def inspect_worktree(project_root: str | Path) -> WorktreeBoundary:
    """Return immutable Git identity without reading working-tree file contents."""

    candidate = Path(project_root)
    if candidate.is_symlink():
        raise WorktreeBoundaryError(f"project root may not be a symlink: {candidate}")
    root = candidate.resolve()
    if not root.is_dir():
        raise WorktreeBoundaryError(f"project root is not a directory: {root}")

    repository_root = Path(
        _boundary_git(root, "rev-parse", "--show-toplevel")
    ).resolve()
    git_dir = Path(_boundary_git(root, "rev-parse", "--absolute-git-dir")).resolve()
    common_value = _boundary_git(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    common_dir = Path(common_value).resolve()
    head = _boundary_git(root, "rev-parse", "--verify", "HEAD^{commit}")
    return WorktreeBoundary(
        project_root=root.as_posix(),
        repository_root=repository_root.as_posix(),
        head=head,
        git_dir=git_dir.as_posix(),
        common_dir=common_dir.as_posix(),
        isolated=git_dir != common_dir,
    )


ISOLATION_GUIDANCE = (
    "Create a unique branch and linked worktree from the primary worktree's committed HEAD "
    "(git worktree add -b <branch> <path> HEAD) and retry from that worktree's root."
)


def require_isolated_worktree(
    project_root: str | Path,
    *,
    allow_primary_worktree: bool = False,
) -> WorktreeBoundary:
    """Require a linked worktree unless the developer explicitly authorized primary mutation.

    Every refusal says how to obtain an isolated worktree.
    """

    candidate = Path(project_root)
    if candidate.is_symlink():
        raise WorktreeBoundaryError(
            f"project root may not be a symlink: {candidate}. {ISOLATION_GUIDANCE}"
        )
    root = candidate.resolve()
    if not root.is_dir():
        raise WorktreeBoundaryError(
            f"project root is not a directory: {root}. {ISOLATION_GUIDANCE}"
        )
    try:
        probe = subprocess.run(
            ("git", "-C", str(root), "rev-parse", "--is-inside-work-tree"),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        if not allow_primary_worktree:
            raise WorktreeBoundaryError(
                f"cannot execute Git worktree preflight: {error}. {ISOLATION_GUIDANCE}"
            ) from error
        probe = None
    if probe is None or probe.returncode != 0 or probe.stdout.strip() != "true":
        if allow_primary_worktree:
            return WorktreeBoundary(
                project_root=root.as_posix(),
                repository_root="",
                head="",
                git_dir="",
                common_dir="",
                isolated=False,
            )
        raise WorktreeBoundaryError(
            "agent-authored mutation requires a committed linked Git worktree; this directory is "
            "not a Git worktree. Use --allow-primary-worktree only when the developer explicitly "
            "authorized mutation of this current directory. " + ISOLATION_GUIDANCE
        )
    try:
        boundary = inspect_worktree(project_root)
    except WorktreeBoundaryError as error:
        raise WorktreeBoundaryError(
            f"Git worktree preflight failed: {error}. {ISOLATION_GUIDANCE}"
        ) from error
    if boundary.isolated or allow_primary_worktree:
        return boundary
    raise WorktreeBoundaryError(
        "agent-authored mutation is not allowed in the primary Git worktree; create a unique "
        f"branch and linked worktree from committed HEAD {boundary.head}, then retry there. "
        "Primary staged, unstaged, untracked, and ignored files are outside the request authority. "
        "Use --allow-primary-worktree only when the developer explicitly authorized mutation of "
        "the primary worktree for this request."
    )
