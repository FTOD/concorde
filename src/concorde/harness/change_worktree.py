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

from ..spec.typed_data import canonical, checked_path, decode
from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError, identifier, read_file


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
        raise SpecError("A capability must start at its Git worktree root", "workspace_mismatch")
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
            raise SpecError("this capability requires a managed change worktree", "missing_change")
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
    try:
        identifier(state.get("change_id"))
        for field in ("branch", "base_branch", "base_commit", "primary_worktree"):
            if field not in state or (state[field] is not None and (
                    not isinstance(state[field], str) or not state[field].strip())):
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
                not isinstance(state["task"], str) or not state["task"].strip()):
            raise ValueError("invalid task")
        if not isinstance(state.get("constraints"), list) or any(
                not isinstance(item, str) or not item.strip() for item in state["constraints"]):
            raise ValueError("invalid constraints")
    except ValueError as error:
        raise SpecError(f"worktree owner state is invalid: {error}", "invalid_worktree_state") from error
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
    if "graph" in state and not isinstance(state["graph"], dict):
        raise SpecError("worktree graph state has an invalid shape", "invalid_worktree_state")
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
        "You may invoke `concorde-deliver` from this source worktree or the destination worktree.\n"
        f"The destination is the primary worktree: {state['primary_worktree']}.\n"
        "The session's initial working directory must be one of those two participants; a third\n"
        "worktree cannot deliver this change by redirecting or forwarding its invocation.\n"
        "Delivery creates concorde/delivered/<change_id> and leaves the primary branch unchanged.\n"
        "The host removes this source unless keep_worktree:true was explicitly requested.\n"
        "End this session after removal. Only an explicit user request to the sole primary writer\n"
        "authorizes a separate merge_primary:true request from the primary session.\n"
        "Development loops stop at a ready candidate and never deliver automatically.\n"
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
        "target_id": None, "target_hint": (task or {}).get("target_id"),
        "focus_id": (task or {}).get("focus_id"), "task": (task or {}).get("task"),
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


def create_worktree(root: Path, task: dict, *, package_root: Path | None = None) -> dict:
    primary, current = workspace_identity(root)
    if primary is None or current["path"] != primary["path"] or not primary["branch"]:
        raise SpecError("create a change from the primary worktree's attached branch", "workspace_mismatch")
    change_id = "change." + str(uuid.uuid4())
    branch = "concorde/" + change_id.removeprefix("change.")
    directory = Path(tempfile.mkdtemp(prefix="concorde-worktree-")) / "project"
    git(root, "worktree", "add", "-b", branch, str(directory), current["head"])
    state = ensure_change(directory, task=task, change_id=change_id)
    if package_root is not None and package_root.resolve() == root.resolve():
        # Self-hosted Concorde: the new linked worktree is also its own package root, and
        # generated/ is untracked, so the handoff must not open on a build-less checkout.
        from ..distribution.build import write_build
        write_build(directory)
    return {"path": str(directory), "branch": branch, "base_commit": current["head"],
            "change_id": state["change_id"], "primary_worktree": primary["path"]}


def resume_owner(state: dict, task: dict) -> dict:
    """Restore omitted owner fields; a request cannot replace persisted intent or routing."""
    result = dict(task)
    if state["task"] is None:
        return result
    fields = ["task", "constraints", "focus_id"]
    if state["target_id"] is not None:
        fields.append("target_id")
    for field in fields:
        if field in task and task[field] != state[field]:
            raise SpecError(f"resume {field} conflicts with the recorded change owner",
                            "incompatible_handoff", field)
        if state[field] is not None:
            result[field] = copy.deepcopy(state[field])
    if state["target_id"] is None and state.get("target_hint") is not None:
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
            for field, value in (("task", task["task"]), ("constraints", task.get("constraints", []))):
                if state[field] != value:
                    raise SpecError(f"owner binding conflicts with recorded {field}",
                                    "incompatible_handoff", field)
        state.update(target_id=task["target_id"], focus_id=task.get("focus_id"),
                     task=task["task"], constraints=task.get("constraints", []))
        save_change(root, state)
    elif not coordinated:
        resume_owner(state, {"focus_id": None, "constraints": [], **task})
    return state


def target_state(root: Path, target_id: str, focus_id: str | None, *, create: bool = False) -> dict:
    change = read_change(root, required=True)
    existing = change["targets"].get(target_id)
    if existing is not None:
        if existing.get("focus_id") != focus_id:
            raise SpecError("target work belongs to a different focus", "incompatible_handoff")
        return copy.deepcopy(existing)
    if not create:
        raise SpecError("this capability requires an authored target plan", "missing_plan")
    return {"schema_version": 1, "target_id": target_id, "focus_id": focus_id,
            "plan": "", "tasks": [], "checks": [], "spec_digest": None,
            "implementation_digest": None, "completed_capabilities": [],
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


def graph_state(root: Path, target_id: str, *, policy: dict, spec_digest: str,
                implementation_digest: str | None) -> dict:
    """Create or return this target's dev-loop repair-graph record.

    A human editing the Spec or the implementation directly (outside an admitted repair)
    invalidates any pending repair count and feedback fingerprint: the record resets to
    iteration zero and a ``human`` transition is appended, so a stale repair state never
    silently controls a re-run driven by new human input.
    """

    change = read_change(root, required=True)
    graph = change.setdefault("graph", {})
    record = graph.get(target_id)
    if record is None:
        record = {"policy": dict(policy), "spec_digest": spec_digest, "repair_iteration": 0,
                  "last_feedback_digest": None, "last_implementation_digest": implementation_digest,
                  "repair": None, "transitions": []}
        graph[target_id] = record
    else:
        spec_changed = record["spec_digest"] != spec_digest
        implementation_changed = (record["last_implementation_digest"] is not None
            and implementation_digest is not None
            and record["last_implementation_digest"] != implementation_digest)
        if spec_changed or implementation_changed:
            record.update(spec_digest=spec_digest, repair_iteration=0,
                          last_feedback_digest=None, repair=None)
            record["transitions"].append({
                "iteration": 0, "from": "human", "to": "reset", "trigger": "human",
                "outcome": "spec_changed" if spec_changed else "implementation_changed",
                "artifact": None, "input_digest": None, "finding_ids": [], "status": None})
        record["last_implementation_digest"] = implementation_digest
    save_change(root, change)
    return copy.deepcopy(record)


def record_transition(root: Path, target_id: str, **fields) -> None:
    """Append one Graph transition record for this target (G4: attributed selected transitions)."""

    change = read_change(root, required=True)
    graph = change.setdefault("graph", {})
    record = graph.setdefault(target_id, {"policy": {}, "spec_digest": None, "repair_iteration": 0,
        "last_feedback_digest": None, "last_implementation_digest": None, "repair": None, "transitions": []})
    record["transitions"].append(dict(fields))
    save_change(root, change)


def record_task_gaps(root: Path, target_id: str, task: str, phase: str, gaps, spec_digest: str,
                     *, review_input_digest: str | None = None) -> None:
    """Persist task-local blocking contracts; unrelated progress cannot erase them."""
    from ..spec.repository import digest
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
        if review_input_digest is not None and phase in {"spec-review", "code-review"}:
            item["review_input_digest"] = review_input_digest
        if gap["context_id"] not in item["contexts"]:
            item["contexts"].append(gap["context_id"])
    for item in history:
        if (item["target_id"] == target_id and item["task"] == task and item["phase"] == phase
                and not gaps and (phase == "specify" or item.get("spec_digest") != spec_digest
                    or (phase in {"spec-review", "code-review"} and review_input_digest is not None
                        and item.get("review_input_digest") is not None
                        and item["review_input_digest"] != review_input_digest))):
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


def unchanged_task_gaps(root: Path, target_id: str, task: str, phase: str, spec_digest: str,
                        *, review_input_digest: str | None = None) -> list[dict]:
    state = read_change(root)
    return [dict(item["gap"]) for item in (state or {}).get("gap_history", [])
            if item["status"] == "open" and item["target_id"] == target_id and item["task"] == task
            and item["phase"] == phase and item.get("spec_digest") == spec_digest
            and (review_input_digest is None or phase not in {"spec-review", "code-review"}
                 or item.get("review_input_digest") in {None, review_input_digest})]


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
