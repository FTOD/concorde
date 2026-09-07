"""Host-owned change state and discovery metadata for Git worktrees.

A linked worktree is one candidate change. Its local control state is never Spec
authority and is never part of a delivered Git tree. The primary worktree keeps
an inventory of every live linked worktree, including ones created outside Concorde.
"""
from __future__ import annotations

import copy
import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from .operation_data import canonical, checked_path, decode
from ..specification.changes import apply_files, file_change
from ..specification.repository import SpecError, identifier, read_file


STATE_PATH = ".concorde/worktree.json"
REGISTRY_PATH = ".concorde/worktrees.json"
WORK_PATH = ".concorde/work"
DELIVERIES_PATH = ".concorde/deliveries"
LOCAL_PATHS = (STATE_PATH, REGISTRY_PATH, WORK_PATH, DELIVERIES_PATH,
               ".concorde/runs", ".concorde/topology-proposals")
GUIDANCE_START = "\n<!-- concorde-change-worktree:start -->\n"
GUIDANCE_END = "<!-- concorde-change-worktree:end -->\n"
GUIDANCE_FILES = ("AGENTS.md", "CLAUDE.md")


def git(root: Path, *arguments: str, input: str | None = None,
        env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(("git", "-C", str(root), *arguments), input=input,
                            capture_output=True, text=True, env=env)
    if check and result.returncode:
        raise SpecError("Git worktree operation failed: " + result.stderr.strip(),
                        "workspace_mismatch")
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
        records.append({
            "path": str(Path(fields["worktree"]).resolve()),
            "branch": branch.removeprefix("refs/heads/") if branch else None,
            "head": fields.get("HEAD"),
            "locked": "locked" in fields,
            "alive": Path(fields["worktree"]).is_dir() and "prunable" not in fields,
        })
    return records


def workspace_identity(root: Path) -> tuple[dict | None, dict | None]:
    records = list_worktrees(root)
    if not records:
        return None, None
    current = next((item for item in records if item["path"] == str(root.resolve())), None)
    if current is None:
        raise SpecError("Operation must start at its Git worktree root", "workspace_mismatch")
    return records[0], current


@contextmanager
def repository_lock(root: Path):
    """Serialize host registry updates and deliveries across linked worktrees."""
    common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False)
    if common.returncode:
        yield
        return
    import fcntl
    lock = Path(common.stdout.strip()) / "concorde-worktrees.lock"
    with lock.open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _write_json(root: Path, relative: str, value: dict) -> None:
    apply_files(root, [file_change(root, relative, canonical(value) + "\n")], {relative})


def _exclude_control_files(root: Path) -> None:
    common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False)
    if common.returncode:
        return
    # Git's shared local exclude file is deliberately outside the delivered tree.
    directory = Path(common.stdout.strip()) / "info"
    directory.mkdir(exist_ok=True)
    path = directory / "exclude"
    if path.is_symlink():
        raise SpecError("Git exclude file must not be a symlink", "unsafe_path")
    before = path.read_text() if path.exists() else ""
    missing = ["/" + item for item in LOCAL_PATHS if "/" + item not in before.splitlines()]
    if missing:
        with path.open("a") as stream:
            stream.write(("\n" if before and not before.endswith("\n") else "")
                         + "# Concorde local worktree control state\n" + "\n".join(missing) + "\n")


def read_change(root: Path, *, required: bool = False) -> dict | None:
    path = checked_path(root, STATE_PATH)
    if not path.exists():
        if required:
            raise SpecError("this Operation requires a managed change worktree", "missing_change")
        return None
    state = decode(read_file(root, STATE_PATH).decode())
    if (not isinstance(state, dict) or type(state.get("schema_version")) is not int
            or state["schema_version"] != 1
            or state.get("path") != str(root.resolve())
            or not isinstance(state.get("targets"), dict)
            or not isinstance(state.get("guidance"), dict)
            or not isinstance(state.get("gaps"), list)
            or not isinstance(state.get("phase"), str) or not state["phase"]
            or not isinstance(state.get("status"), str) or not state["status"]):
        raise SpecError("worktree state has an invalid identity or schema", "invalid_worktree_state")
    identifier(state.get("change_id", ""))
    primary, current = workspace_identity(root)
    if current is not None and (state.get("branch") != current["branch"]
            or state.get("primary_worktree") != primary["path"]):
        raise SpecError("worktree state belongs to a different branch or primary worktree",
                        "workspace_mismatch")
    if set(state["guidance"]) - set(GUIDANCE_FILES):
        raise SpecError("worktree guidance names an unsupported file", "invalid_worktree_state")
    if any(not isinstance(value, dict) or type(value.get("created")) is not bool
           for value in state["guidance"].values()) or any(
               not isinstance(value, dict) for value in state["targets"].values()):
        raise SpecError("worktree progress or guidance has an invalid shape", "invalid_worktree_state")
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
        "path": item["path"], "branch": item["branch"], "head": item["head"],
        "managed": state is not None, "locked": item["locked"],
        "change_id": state["change_id"] if state else None,
        "target_id": state.get("target_id") if state else None,
        "task": (state.get("task") or "")[:300] if state else "",
        "phase": state.get("phase") if state else None,
        "status": state.get("status") if state else "invalid" if invalid else "unmanaged",
        "outcome": state.get("outcome") if state else None,
    }


def _inventory(root: Path, *, persist: bool) -> dict:
    records = list_worktrees(root)
    if not records:
        return {"schema_version": 1, "primary_worktree": None,
                "primary_branch": None, "worktrees": []}
    primary = records[0]
    inventory = {"schema_version": 1, "primary_worktree": primary["path"],
                 "primary_branch": primary["branch"], "worktrees": [
                     _summary(item, primary["path"]) for item in records[1:] if item["alive"]]}
    if persist:
        _exclude_control_files(root)
        _write_json(Path(primary["path"]), REGISTRY_PATH, inventory)
    return inventory


def refresh_registry(root: Path, *, persist: bool = True) -> dict:
    if not persist:
        return _inventory(root, persist=False)
    with repository_lock(root):
        return _inventory(root, persist=True)


def save_change(root: Path, state: dict, *, publish: bool = True, locked: bool = False) -> None:
    if state.get("path") != str(root.resolve()):
        raise SpecError("cannot move change ownership between worktrees", "workspace_mismatch")
    def write():
        _exclude_control_files(root)
        _write_json(root, STATE_PATH, state)
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
            raise SpecError("worktree guidance markers were modified", "invalid_worktree_state")
        return content
    if content.count(GUIDANCE_START) != 1 or content.count(GUIDANCE_END) != 1:
        raise SpecError("worktree guidance markers are ambiguous", "invalid_worktree_state")
    start = content.index(GUIDANCE_START)
    end = content.index(GUIDANCE_END, start) + len(GUIDANCE_END)
    return content[:start] + content[end:]


def _guidance_changes(root: Path, state: dict) -> list[dict]:
    block = (GUIDANCE_START + "## Concorde change worktree\n\n"
        "This agent session starts in a secondary worktree containing an unfinished candidate change.\n"
        f"The host records its lifecycle in `{STATE_PATH}`. `concorde-main` receives this worktree's\n"
        "identity, draft status and the primary worktree's live change inventory. Partial Spec and\n"
        "implementation edits are draft state; resume the recorded phase before claiming completion.\n\n"
        "Do not invoke `concorde-deliver` from this session. Delivery requires opening a new agent\n"
        f"whose initial working directory is the primary worktree: {state['primary_worktree']}.\n"
        "Ask for delivery in that primary session. Changing cwd, using git -C, redirecting the host,\n"
        "or forwarding an invocation does not turn this session into a primary-worktree session.\n"
        "The primary worktree's checked-out branch is the delivery destination; its name need not\n"
        "be main. Only the primary host merges a verified candidate and removes this worktree.\n"
        "Keep this managed block and the local state available until that delivery completes.\n"
        + GUIDANCE_END)
    changes = []
    for relative in GUIDANCE_FILES:
        path = checked_path(root, relative)
        before = path.read_text() if path.exists() else ""
        state["guidance"][relative] = {"created": not path.exists()}
        changes.append(file_change(root, relative, strip_guidance(before) + block))
    return changes


def ensure_change(root: Path, *, task: dict | None = None, change_id: str | None = None,
                  allow_primary: bool = False) -> dict:
    existing = read_change(root)
    if existing is not None:
        if change_id is not None and change_id != existing["change_id"]:
            raise SpecError("this worktree already belongs to another change", "incompatible_handoff")
        return existing
    legacy = checked_path(root, ".concorde/attempts")
    if legacy.exists() and any(legacy.iterdir()):
        raise SpecError("legacy attempt state is not supported; remove it explicitly before adopting this worktree",
                        "legacy_attempt")
    primary, current = workspace_identity(root)
    secondary = current is not None and current["path"] != primary["path"]
    if not secondary and not allow_primary:
        raise SpecError("a change requires its own linked worktree", "workspace_mismatch")
    if secondary and not current["branch"]:
        raise SpecError("a change worktree requires an attached branch", "detached_worktree")
    if current is not None:
        tracked = git_value(root, "ls-files", "--", STATE_PATH, REGISTRY_PATH, WORK_PATH, DELIVERIES_PATH)
        if tracked:
            raise SpecError("worktree control paths must not be tracked project files",
                            "invalid_worktree_state")
    state = {
        "schema_version": 1, "change_id": change_id or "change." + str(uuid.uuid4()),
        "path": str(root.resolve()), "branch": current["branch"] if current else None,
        "primary_worktree": primary["path"] if primary else None,
        "base_commit": current["head"] if current else None,
        "base_branch": primary["branch"] if primary else None,
        "target_id": None, "focus_id": None, "task": (task or {}).get("task"),
        "constraints": (task or {}).get("constraints", []),
        "phase": "created", "status": "active", "outcome": None, "gaps": [],
        "targets": {}, "guidance": {}, "validated_tree": None, "validation": None,
    }
    identifier(state["change_id"])
    with repository_lock(root):
        observed = read_change(root)
        if observed is not None:
            if change_id is not None and observed["change_id"] != change_id:
                raise SpecError("another invocation adopted this worktree", "incompatible_handoff")
            return observed
        _exclude_control_files(root)
        changes = _guidance_changes(root, state) if secondary else []
        changes.append(file_change(root, STATE_PATH, canonical(state) + "\n"))
        apply_files(root, changes, {item["path"] for item in changes})
        _inventory(root, persist=True)
    return state


def create_worktree(root: Path, task: dict) -> dict:
    primary, current = workspace_identity(root)
    if primary is None or current["path"] != primary["path"] or not primary["branch"]:
        raise SpecError("create a change from the primary worktree's attached branch", "workspace_mismatch")
    change_id = "change." + str(uuid.uuid4())
    branch = "concorde/" + change_id.removeprefix("change.")
    directory = Path(tempfile.mkdtemp(prefix="concorde-worktree-")) / "project"
    git(root, "worktree", "add", "-b", branch, str(directory), current["head"])
    state = ensure_change(directory, task=task, change_id=change_id)
    return {"path": str(directory), "branch": branch, "base_commit": current["head"],
            "change_id": state["change_id"], "primary_worktree": primary["path"]}


def bind_owner(root: Path, task: dict, *, coordinated: bool = False) -> dict:
    state = read_change(root, required=True)
    if task.get("change_id") not in {None, state["change_id"]}:
        raise SpecError("change ID does not own this worktree", "incompatible_handoff")
    if state["target_id"] is None:
        state.update(target_id=task["target_id"], focus_id=task.get("focus_id"),
                     task=task["task"], constraints=task.get("constraints", []))
        save_change(root, state)
    elif not coordinated and (state["target_id"] != task["target_id"]
            or state["focus_id"] != task.get("focus_id")
            or state["task"] != task["task"]
            or state["constraints"] != task.get("constraints", [])):
        raise SpecError("this worktree is owned by a different top-level task; use a separate worktree",
                        "incompatible_handoff")
    return state


def target_state(root: Path, target_id: str, focus_id: str | None, *, create: bool = False) -> dict:
    change = read_change(root, required=True)
    existing = change["targets"].get(target_id)
    if existing is not None:
        if existing.get("focus_id") != focus_id:
            raise SpecError("target work belongs to a different focus", "incompatible_handoff")
        return copy.deepcopy(existing)
    if not create:
        raise SpecError("this Operation requires an authored target plan", "missing_plan")
    return {"schema_version": 1, "target_id": target_id, "focus_id": focus_id,
            "plan": "", "tasks": [], "checks": [], "spec_digest": None,
            "implementation_digest": None, "completed_operations": [],
            "phase": "plan", "status": "active"}


def save_target_state(root: Path, value: dict) -> None:
    change = read_change(root, required=True)
    identifier(value["target_id"])
    change["targets"][value["target_id"]] = value
    save_change(root, change)


def progress(root: Path, *, phase: str | None = None, status: str | None = None,
             outcome: str | None = None, gaps=None, invalidate: bool = False) -> None:
    state = read_change(root)
    if state is None:
        return
    if phase is not None:
        state["phase"] = phase
    if status is not None:
        state["status"] = status
    state["outcome"] = outcome
    if gaps is not None:
        unresolved = [item["gap"] for item in state.get("gap_history", []) if item["status"] == "open"]
        state["gaps"] = list({canonical(gap): gap for gap in [*unresolved, *gaps]}.values())
    if invalidate:
        state["validated_tree"] = None
        state["validation"] = None
    save_change(root, state)


def record_task_gaps(root: Path, target_id: str, task: str, phase: str, gaps, spec_digest: str) -> None:
    """Persist task-local blocking contracts; unrelated progress cannot erase them."""
    from ..specification.repository import digest
    state = read_change(root)
    if state is None:
        return
    history = state.setdefault("gap_history", [])
    existing = {item["id"]: item for item in history}
    for gap in gaps:
        key = digest({"target_id": target_id, "task": task, "phase": phase,
                      **{field: gap[field] for field in ("question", "blocked_step", "needed_contract")}})
        if key not in existing:
            item = {"id": key, "target_id": target_id, "task": task, "phase": phase,
                    "gap": dict(gap), "status": "open", "contexts": [], "spec_digest": spec_digest}
            history.append(item)
            existing[key] = item
        item = existing[key]
        item.update(gap=dict(gap), status="open", spec_digest=spec_digest)
        if gap["context_id"] not in item["contexts"]:
            item["contexts"].append(gap["context_id"])
    for item in history:
        if (item["target_id"] == target_id and item["task"] == task and item["phase"] == phase
                and not gaps and (phase == "specify" or item.get("spec_digest") != spec_digest)):
            item["status"] = "resolved"
    state["gaps"] = [item["gap"] for item in history if item["status"] == "open"]
    target = state["targets"].get(target_id)
    if target is not None:
        target["gaps"] = [item["gap"] for item in history
                          if item["status"] == "open" and item["target_id"] == target_id]
    if gaps:
        state["validated_tree"] = None
        state["validation"] = None
    save_change(root, state)


def unchanged_task_gaps(root: Path, target_id: str, task: str, phase: str, spec_digest: str) -> list[dict]:
    state = read_change(root)
    return [dict(item["gap"]) for item in (state or {}).get("gap_history", [])
            if item["status"] == "open" and item["target_id"] == target_id and item["task"] == task
            and item["phase"] == phase and item.get("spec_digest") == spec_digest]


def work_path(target_id: str, name: str) -> str:
    identifier(target_id)
    if name not in {"plan.md", "checklist.md", "issue-drafts.json"}:
        raise SpecError("unsupported work artifact", "invalid_input")
    return f"{WORK_PATH}/{target_id}/{name}"


def workspace_context(root: Path, *, persist: bool = False) -> dict:
    inventory = refresh_registry(root, persist=persist)
    primary, current = workspace_identity(root)
    state = read_change(root)
    coordination = (state["targets"].get(state["target_id"], {}).get("coordination", {})
                    if state else {})
    return {
        "kind": "unversioned" if current is None else
                "primary" if current["path"] == primary["path"] else "change",
        "current_worktree": str(root.resolve()),
        "current_branch": current["branch"] if current else None,
        "primary_worktree": inventory["primary_worktree"],
        "primary_branch": inventory["primary_branch"],
        "change_id": state["change_id"] if state else None,
        "phase": state["phase"] if state else None,
        "status": state["status"] if state else None,
        "outcome": state.get("outcome") if state else None,
        "gaps": state["gaps"] if state else [],
        "components": [{"target_id": target_id, "spec_status": record["spec_status"],
                        "implementation_status": record["implementation_status"],
                        "outcome": record["outcome"]} for target_id, record in coordination.items()],
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
            tracked = git(root, "ls-files", "-z", "--", path, env=env).stdout.split("\0")
            for member in filter(None, tracked):
                if member == ".concorde/topology-proposals/.gitignore":
                    continue
                git(root, "update-index", "--force-remove", "--", member, env=env)
        for relative, metadata in (state or {}).get("guidance", {}).items():
            path = checked_path(root, relative)
            if not path.exists():
                continue
            before = path.read_text()
            clean = strip_guidance(before)
            if metadata["created"] and not clean:
                git(root, "update-index", "--force-remove", "--", relative, env=env)
            elif before != clean:
                blob = git(root, "hash-object", "-w", "--stdin", input=clean).stdout.strip()
                mode = "100755" if path.stat().st_mode & 0o111 else "100644"
                git(root, "update-index", "--add", "--cacheinfo", f"{mode},{blob},{relative}", env=env)
        return git(root, "write-tree", env=env).stdout.strip()
