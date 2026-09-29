#!/usr/bin/env python3
"""Move a primary worktree's task records from before Tracing into the history, and archive the
old run store.

Before Tracing, a task left flat files side by side in ``.concorde/tasks/``: its record
``<task>.json``, its decision log ``<task>.decisions.md``, its merge log ``<task>.merge.log`` and
its session material ``<task>.session/``; runs and worker runs lay in ``.concorde/runs/``. The
current code reads neither. This one-off script, for Concorde's own checkout, gives every old task
that ended a history folder ``.concorde/history/<key>/`` in the Tracing layout
(``specs/concorde/tracing/contracts.md#layout``), so that ``concorde trace list --history``, ``task
show`` and retention see it, and packs the old run store into one compressed tar outside the
repository before removing it.

Mapping of one old task into its history folder:

- ``task.json``: the old record in the current record format (``contract.tasks.record``), with
  ``closed.history`` the history key; left out, and the old record kept alone, when it does not fit
  that format.
- ``trace.json``: the task's node (``contract.tasks.task-trace``): started at the open, ended at
  the close with its outcome, the transitions open and the final state, the escalations numbered
  from 1 and the closing, and a ``commit`` and ``bundle`` reference for each delivery.
- ``decisions.md``: the decision log, unchanged.
- ``sessions/<session>/``: a node per recorded task session, its end unknown; for pi its progress
  file, its pi session under ``pi/`` and a node per round under ``rounds/<n>/`` with the round's
  prompt, events, stderr and supervisor log.
- ``legacy/record.json``, ``legacy/merge.log`` and ``legacy/session/``: the old record, the merge
  log and every session file without a place in the layout (a session's boundary configuration),
  unchanged, each an artifact of the task's node. The old record keeps what the layout has no
  field for: the runs, deliveries and workflow steps it listed.

Every file is copied into a staging folder, checked against its source's digest, the staging
folder is renamed to the history folder and only then are the old files removed; a task whose old
record already lies, byte for byte, in a history folder only has its old files removed. The run
store ``.concorde/runs/`` and the old locks ``tasks/.lock`` and ``tasks/merge.lock`` go into one
archive, which is compared with the files by ``tar --compare`` before any of them is removed.
Nothing else under ``.concorde`` is touched: not ``locks/``, ``evidence/``, ``issues/``, any current
task folder or any history folder that exists.

    python3 scripts/development/migrate-legacy-records.py <primary worktree> \\
        --archive ~/concorde-old-records.tar.zst [--dry-run]

``--dry-run`` prints every copy, write, move, archive and removal without doing any. A refusal
prints ``{"error": <error link>}`` and exits 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
CHECKOUT_PYTHON = REPOSITORY / ".venv/bin/python"
if (
    __name__ == "__main__"
    and CHECKOUT_PYTHON.is_file()
    and os.path.realpath(sys.prefix) != os.path.realpath(REPOSITORY / ".venv")
):
    os.execv(CHECKOUT_PYTHON, [str(CHECKOUT_PYTHON), *sys.argv])
sys.path.insert(0, str(REPOSITORY / "src"))

from concorde.errors import evidence, link, render  # noqa: E402
from concorde.spec.schema import ContractError, validate  # noqa: E402
from concorde.tasks import store  # noqa: E402
from concorde.tracing import layout, locks  # noqa: E402
from concorde.tracing import node as trace  # noqa: E402

ACTOR = "legacy records migration"
RECORD_CONTRACT = REPOSITORY / "specs/concorde/coordination/tasks/contracts.md"
RUNS = "runs"
STAGING = ".migrating-"
# The old locks of the flat task store, which go into the archive with the run store.
OLD_LOCKS = (".lock", "merge.lock")
SUFFIXES = {
    ".decisions.md": "decisions",
    ".merge.log": "merge_log",
    ".session": "session",
}
ROUND_FILE = re.compile(
    r"^round-([0-9]+)\.(prompt\.md|events\.jsonl|stderr\.log|supervisor\.log)$"
)
ROUND_NAMES = {
    "prompt.md": store.ROUND_FILES["prompt"],
    "events.jsonl": store.ROUND_FILES["events"],
    "stderr.log": store.ROUND_FILES["stderr"],
    "supervisor.log": store.ROUND_FILES["supervisor"],
}
SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
RECORD_FIELDS = (
    "id",
    "goal",
    "modules",
    "branch",
    "worktree",
    "base_commit",
    "state",
    "created_at",
    "updated_at",
)
COMPRESSION = {
    ".tar.zst": "--zstd",
    ".tzst": "--zstd",
    ".tar.gz": "--gzip",
    ".tgz": "--gzip",
}


class Refused(Exception):
    """The migration cannot go on; ``error`` is its link."""

    def __init__(self, code: str, detail: str, explanation: str, **extra):
        super().__init__(detail)
        self.error = link(
            "component",
            ACTOR,
            code,
            detail,
            reason=extra.pop("reason", "input"),
            explanation=explanation,
            **extra,
        )


@dataclass
class OldTask:
    """The flat files of one task from before Tracing."""

    task: str
    record_path: Path
    record: dict
    decisions: Path | None = None
    merge_log: Path | None = None
    session: Path | None = None

    def sources(self) -> list[Path]:
        return [
            path
            for path in (self.record_path, self.decisions, self.merge_log, self.session)
            if path is not None
        ]


@dataclass
class Migration:
    """What one old task becomes: the files copied, the records written, under one history key."""

    old: OldTask
    key: str
    copies: list[tuple[Path, str]] = field(default_factory=list)
    writes: list[tuple[str, bytes]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # The history folder already holding this task, when an earlier run moved it but did not
    # finish removing the old files.
    done: Path | None = None


@dataclass
class Plan:
    concorde: Path
    migrations: list[Migration] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    archived: list[str] = field(default_factory=list)


# --- reading the old store ----------------------------------------------------------------------


def _is_old_record(path: Path, value) -> bool:
    return (
        isinstance(value, dict)
        and value.get("id") == path.name[: -len(".json")]
        and "schema_version" not in value
        and all(name in value for name in ("goal", "branch", "state", "created_at"))
    )


def old_tasks(concorde: Path) -> tuple[list[OldTask], list[tuple[Path, str]]]:
    """The old tasks of ``concorde/tasks/`` and every entry left alone with the reason."""
    folder = layout.tasks_folder(concorde)
    tasks: dict[str, OldTask] = {}
    parts: dict[str, dict[str, Path]] = {}
    skipped: list[tuple[Path, str]] = []
    for entry in sorted(folder.iterdir()) if folder.is_dir() else []:
        name = entry.name
        if name in OLD_LOCKS and entry.is_file():
            continue
        if entry.is_dir() and not name.endswith(".session"):
            skipped.append((entry, "a task folder of the current layout"))
            continue
        if name.endswith(".json") and entry.is_file():
            try:
                value = json.loads(entry.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                skipped.append((entry, f"not a readable old task record: {error}"))
                continue
            if not _is_old_record(entry, value):
                skipped.append((entry, "not an old task record"))
                continue
            task = value["id"]
            tasks[task] = OldTask(task, entry, value)
            continue
        for suffix, part in SUFFIXES.items():
            if name.endswith(suffix) and (entry.is_dir() == (part == "session")):
                parts.setdefault(name[: -len(suffix)], {})[part] = entry
                break
        else:
            skipped.append((entry, "not a file of the old task store"))
    for task, found in sorted(parts.items()):
        if task not in tasks:
            for path in found.values():
                skipped.append((path, f"no old task record {task}.json beside it"))
            continue
        for part, path in found.items():
            setattr(tasks[task], part, path)
    return [tasks[name] for name in sorted(tasks)], skipped


# --- mapping one task ---------------------------------------------------------------------------


def _record_schema() -> dict:
    text = RECORD_CONTRACT.read_text(encoding="utf-8")
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        value = json.loads(fence)
        if value["id"] == "contract.tasks.record":
            return value["schema"]
    raise Refused(
        "contract_missing",
        f"{RECORD_CONTRACT} holds no contract.tasks.record",
        "the current task record format cannot be checked without its contract",
        reason="environment",
    )


def _node(identity: str, kind: str, started_at: str, **fields) -> dict:
    record = {
        "schema_version": 1,
        "id": identity,
        "kind": kind,
        "started_at": started_at,
        "ended_at": None,
        "status": "unknown",
        "outcome": None,
        "usage": trace.usage(),
        "error": None,
        "metadata": {},
        "artifacts": [],
        "references": [],
        "content": None,
    }
    record.update(fields)
    return record


def _artifacts(files: dict[str, Path], names: list[tuple[str, str]]) -> list[dict]:
    """Artifact entries of the node whose files ``files`` maps (relative path -> source)."""
    return [
        {"id": identity, "path": relative, "digest": trace.digest(files[relative])}
        for identity, relative in names
        if relative in files
    ]


def _serialize(record: dict) -> bytes:
    return (
        json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()


def _session_files(old: OldTask) -> list[tuple[Path, str]]:
    """Every file of the old session folder, with its path relative to it."""
    if old.session is None:
        return []
    return [
        (path, path.relative_to(old.session).as_posix())
        for path in sorted(old.session.rglob("*"))
        if path.is_file() or path.is_symlink()
    ]


def _fitting(record: dict, what: str, notes: list[str]) -> bytes | None:
    """``record`` serialized when it fits the node contract and its content type; else None,
    with a note saying why."""
    try:
        return _serialize(trace.check(record))
    except trace.TraceError as error:
        notes.append(f"{what} gets no node, its files are kept as they are: {error}")
        return None


def _session_node(old: OldTask, session: dict, files: dict[str, Path]) -> dict:
    program = session.get("program") or "claude"
    return _node(
        session["id"],
        "session",
        session.get("started_at") or old.record.get("created_at"),
        metadata=_present(task=old.task, program=program, model=session.get("model")),
        artifacts=_artifacts(files, [("progress", layout.PROGRESS)]),
        content={
            "type_id": store.SESSION_TRACE,
            "schema_version": 1,
            "data": {
                "program": program,
                "name": session.get("name"),
                "main": session.get("main"),
                "model": session.get("model"),
                "reported_id": session.get("reported_id"),
            },
        },
    )


def _round_node(
    session: dict, number: int, entry: dict, files: dict[str, Path]
) -> dict:
    outcome = entry.get("status")
    status = store.ROUND_STATUS.get(outcome, "unknown")
    started = entry.get("started_at")
    ended = entry.get("ended_at") if status != "unknown" else None
    return _node(
        str(number),
        "round",
        started,
        ended_at=ended,
        status=status,
        outcome=outcome if status != "unknown" else None,
        usage=trace.usage(duration_seconds=trace.seconds_between(started, ended)),
        error=entry.get("error") if status in ("blocked", "failed") else None,
        metadata=_present(program="pi", model=session.get("model")),
        artifacts=_artifacts(files, list(store.ROUND_FILES.items())),
        content={
            "type_id": store.ROUND_TRACE,
            "schema_version": 1,
            "data": {
                "round": number,
                "prompt": entry.get("prompt"),
                "answer": entry.get("answer"),
                "outcome": outcome,
                "supervisor_pid": entry.get("supervisor_pid"),
                "report": entry.get("report"),
            },
        },
    )


def _present(**values) -> dict:
    """The metadata among ``values`` that the old record holds."""
    return {name: value for name, value in values.items() if value}


def _below(files: dict[str, Path], folder: str) -> dict[str, Path]:
    """The files of ``files`` inside ``folder``, relative to it."""
    return {
        relative[len(folder) + 1 :]: path
        for relative, path in files.items()
        if relative.startswith(folder + "/")
    }


def plan_task(old: OldTask, key: str, schema: dict) -> Migration:
    """The copies and records that make ``old`` the history folder ``key``."""
    migration = Migration(old, key)
    record = old.record
    closed = record.get("closed") or {}
    # Where each file of the history folder comes from, relative to the folder.
    files: dict[str, Path] = {"legacy/record.json": old.record_path}
    if old.decisions is not None:
        files[store.DECISIONS] = old.decisions
    if old.merge_log is not None:
        files["legacy/merge.log"] = old.merge_log

    sessions = [item for item in record.get("sessions") or [] if isinstance(item, dict)]
    for session in sessions:
        if not SESSION_ID.match(str(session.get("id") or "")):
            raise Refused(
                "session_unnamed",
                f"a task session of old task {old.task} has the identity "
                f"{session.get('id')!r}, which cannot name its folder",
                "a session node's folder is named by its identity",
                evidence=[evidence("file", old.record_path.as_posix())],
            )
    pi = [item for item in sessions if item.get("program") == "pi"]
    # A pi session's files lie loose in the old session folder, so they are its only when the
    # task had exactly one pi session.
    owner = pi[0] if len(pi) == 1 else None
    rounds = {
        item.get("round"): item
        for item in (owner or {}).get("rounds") or []
        if isinstance(item, dict) and isinstance(item.get("round"), int)
    }
    for source, relative in _session_files(old):
        placed = None
        if owner is not None:
            base = f"sessions/{owner['id']}"
            matched = ROUND_FILE.match(relative)
            if matched and int(matched.group(1)) in rounds:
                placed = f"{base}/rounds/{int(matched.group(1))}/{ROUND_NAMES[matched.group(2)]}"
            elif relative == layout.PROGRESS:
                placed = f"{base}/{layout.PROGRESS}"
            elif relative.startswith("pi/"):
                placed = f"{base}/{relative}"
        files[placed or f"legacy/session/{relative}"] = source
    migration.copies = [(source, relative) for relative, source in files.items()]
    written: dict[str, bytes] = {}

    # The task record, in the current format when it fits.
    converted = {
        "schema_version": 2,
        **{name: record.get(name) for name in RECORD_FIELDS},
        "merging": None,
        "closed": {**closed, "history": key},
    }
    try:
        validate(converted, schema)
    except ContractError as error:
        migration.notes.append(
            f"the old record does not fit the current task record at "
            f"{error.field or 'the top'} ({error}); it is kept as legacy/record.json only"
        )
    else:
        written[store.RECORD] = store._serialize(converted)

    # The sessions and their rounds.
    for session in sessions:
        base = f"sessions/{session['id']}"
        data = _fitting(
            _session_node(old, session, _below(files, base)),
            f"task session {session['id']}",
            migration.notes,
        )
        if data is not None:
            written[f"{base}/{layout.TRACE}"] = data
        if session is not owner:
            continue
        for number, entry in sorted(rounds.items()):
            folder = f"{base}/rounds/{number}"
            data = _fitting(
                _round_node(session, number, entry, _below(files, folder)),
                f"round {number} of task session {session['id']}",
                migration.notes,
            )
            if data is not None:
                written[f"{folder}/{layout.TRACE}"] = data

    # The task's own node, written last so that its artifacts include the task record.
    def artifact(identity: str, relative: str) -> dict:
        found = (
            trace.digest(files[relative])
            if relative in files
            else "sha256:" + hashlib.sha256(written[relative]).hexdigest()
        )
        return {"id": identity, "path": relative, "digest": found}

    legacy = [
        ("legacy-record", "legacy/record.json"),
        ("legacy-merge-log", "legacy/merge.log"),
        *(
            (f"legacy-session:{relative[len('legacy/session/') :]}", relative)
            for relative in files
            if relative.startswith("legacy/session/")
        ),
    ]
    named = [("record", store.RECORD), ("decision-log", store.DECISIONS), *legacy]
    state = closed.get("state")
    ended_at = closed.get("at")
    status = "failed" if state == "failed" else "ok"
    errors = closed.get("errors") or []
    common = {
        "ended_at": ended_at,
        "status": status,
        "outcome": closed.get("outcome"),
        "usage": trace.usage(
            duration_seconds=trace.seconds_between(record.get("created_at"), ended_at)
        ),
        "error": errors[0] if status == "failed" and errors else None,
    }
    full = _node(
        old.task,
        "task",
        record.get("created_at"),
        **common,
        metadata=_present(
            task=old.task,
            modules=record.get("modules"),
            branch=record.get("branch"),
            base_commit=record.get("base_commit"),
        ),
        artifacts=[
            artifact(identity, relative)
            for identity, relative in named
            if relative in files or relative in written
        ],
        references=_references(record),
        content={
            "type_id": store.TASK_TRACE,
            "schema_version": 1,
            "data": {
                "goal": record.get("goal"),
                "worktree": record.get("worktree"),
                "transitions": [
                    {"state": "open", "at": record.get("created_at")},
                    {"state": state, "at": ended_at},
                ],
                "escalations": _escalations(record),
                "closing": {
                    "outcome": closed.get("outcome"),
                    "note": closed.get("note"),
                    "errors": errors,
                    "primary_commit": closed.get("primary_commit"),
                    "worktree_removed": closed.get("worktree_removed"),
                    "history": key,
                },
            },
        },
    )
    data = _fitting(full, f"old task {old.task}", migration.notes)
    if data is None:
        # A minimal node that points to the old files, so the history and retention see it.
        minimal = _node(
            old.task,
            "task",
            record.get("created_at"),
            **common,
            metadata={"task": old.task},
            artifacts=[
                artifact(identity, relative)
                for identity, relative in (("decision-log", store.DECISIONS), *legacy)
                if relative in files
            ],
        )
        try:
            data = _serialize(trace.check(minimal))
        except trace.TraceError as error:
            raise Refused(
                "node_invalid",
                f"old task {old.task} ({old.record_path}) cannot be given even a minimal task "
                f"node: {error}",
                "the old record lacks the open and close times a task node needs; the script "
                "does not guess them",
                evidence=[evidence("file", old.record_path.as_posix())],
            ) from error
        migration.notes.append(
            f"old task {old.task} gets a minimal node pointing to legacy/"
        )
    written[layout.TRACE] = data
    migration.writes = list(written.items())
    return migration


def _references(record: dict) -> list[dict]:
    """A ``commit`` and a ``bundle`` reference for each delivery the old record lists."""
    found = []
    for delivery in record.get("deliveries") or []:
        if isinstance(delivery, dict) and delivery.get("commit"):
            found.append({"relation": "commit", "target": delivery["commit"]})
            if delivery.get("bundle"):
                found.append(
                    {
                        "relation": "bundle",
                        "target": f"{delivery['commit']}:{delivery['bundle']}",
                    }
                )
    return found


def _escalations(record: dict) -> list[dict]:
    """The old escalations, numbered from 1; who escalated is the level of the link on top."""
    found = []
    for number, item in enumerate(record.get("escalations") or [], start=1):
        error = item.get("error") if isinstance(item, dict) else None
        found.append(
            {
                "number": number,
                "at": (item or {}).get("at") if isinstance(item, dict) else None,
                "by": (item.get("by") if isinstance(item, dict) else None)
                or (error or {}).get("level"),
                "error": error,
            }
        )
    return found


def _history_holding(concorde: Path, old: OldTask) -> Path | None:
    """The history folder whose ``legacy/record.json`` is ``old``'s record byte for byte."""
    history = layout.history_folder(concorde)
    wanted = trace.digest(old.record_path)
    for folder in sorted(history.iterdir()) if history.is_dir() else []:
        if folder.name.startswith("."):
            continue
        if trace.digest(folder / "legacy/record.json") == wanted:
            return folder
    return None


def plan(concorde: Path) -> Plan:
    """Everything the migration would do in ``concorde``, without changing anything."""
    result = Plan(concorde)
    schema = _record_schema()
    tasks, result.skipped = old_tasks(concorde)
    history = layout.history_folder(concorde)
    taken = {item.name for item in history.iterdir()} if history.is_dir() else set()
    # Oldest first, so a name taken by several gets its keys in the order the tasks were opened.
    tasks.sort(key=lambda item: (str(item.record.get("created_at")), item.task))
    for old in tasks:
        holding = _history_holding(concorde, old)
        if holding is not None:
            migration = Migration(old, holding.name, done=holding)
            result.migrations.append(migration)
            continue
        if not (old.record.get("closed") or {}).get("at"):
            result.skipped.extend(
                (
                    path,
                    f"task {old.task} has not ended (state {old.record.get('state')})",
                )
                for path in old.sources()
            )
            continue
        key = old.task
        number = 2
        while key in taken:
            key = f"{old.task}.{number}"
            number += 1
        taken.add(key)
        result.migrations.append(plan_task(old, key, schema))
    runs = concorde / RUNS
    if runs.is_dir():
        result.archived.extend(f"{RUNS}/{item.name}" for item in sorted(runs.iterdir()))
    for name in OLD_LOCKS:
        if (layout.tasks_folder(concorde) / name).is_file():
            result.archived.append(f"{layout.TASKS}/{name}")
    return result


# --- carrying it out ----------------------------------------------------------------------------


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _check_copies(migration: Migration, folder: Path) -> None:
    for source, relative in migration.copies:
        if trace.digest(folder / relative) != trace.digest(source):
            raise Refused(
                "copy_mismatch",
                f"{folder / relative} differs from its source {source} of old task "
                f"{migration.old.task}; the old files stay where they are",
                "a copy that does not match its source would lose the source's content",
                reason="environment",
                evidence=[evidence("file", source.as_posix())],
            )


def migrate(concorde: Path, migration: Migration, say) -> None:
    """Move one old task into the history, or finish removing it when that was done before."""
    old = migration.old
    if migration.done is not None:
        say(f"already in history {migration.done}: {old.task}")
        _check_preserved(old, migration.done)
        for path in old.sources():
            say(f"remove {path}")
            _remove(path)
        return
    history = layout.history_folder(concorde)
    target = history / migration.key
    if target.exists():
        raise Refused(
            "history_taken",
            f"the history key {migration.key} of old task {old.task} was taken while migrating",
            "a history folder is never replaced",
            reason="environment",
            evidence=[evidence("file", target.as_posix())],
        )
    staging = history / f"{STAGING}{migration.key}"
    if staging.exists():
        # Only an interrupted run of this script leaves one, before any old file was removed.
        shutil.rmtree(staging)
    for source, relative in migration.copies:
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)
    for relative, data in migration.writes:
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    _check_copies(migration, staging)
    os.rename(staging, target)
    say(f"moved {old.task} to {target}")
    for path in old.sources():
        say(f"remove {path}")
        _remove(path)


def _check_preserved(old: OldTask, folder: Path) -> None:
    """Refuse unless every old file's content lies somewhere in the history folder ``folder``,
    which an earlier run made before it was interrupted."""
    present = {trace.digest(path) for path in folder.rglob("*") if path.is_file()}
    sources = [old.record_path, old.decisions, old.merge_log]
    sources.extend(source for source, _ in _session_files(old))
    lost = [
        path
        for path in sources
        if path is not None and trace.digest(path) not in present
    ]
    if lost:
        raise Refused(
            "history_differs",
            f"the history folder {folder} holds the old record of task {old.task}, but not "
            f"the content of {', '.join(path.as_posix() for path in lost)}; the old files stay "
            "where they are",
            "removing them would lose what the history does not hold, and a history folder "
            "is never changed",
            options=["move the files named into an archive by hand", "leave them"],
            evidence=[evidence("file", folder.as_posix())],
        )


def _compression(archive: Path) -> str:
    for suffix, flag in COMPRESSION.items():
        if archive.name.endswith(suffix):
            return flag
    raise Refused(
        "archive_format",
        f"the archive {archive} ends in none of {', '.join(COMPRESSION)}",
        "the compression is chosen by the archive's name",
        options=[f"name the archive <name>{suffix}" for suffix in COMPRESSION],
    )


def _tar(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tar", *arguments], cwd=cwd, capture_output=True, text=True, check=False
    )


def archive(concorde: Path, members: list[str], target: Path, say) -> None:
    """Pack ``members`` (paths relative to ``concorde``) into ``target``, compare the archive
    with the files, and remove them only when it matches them all."""
    flag = _compression(target)
    handle, name = tempfile.mkstemp(prefix="concorde-archive-", suffix=".members")
    listing = Path(name)
    with os.fdopen(handle, "w") as stream:
        stream.write("".join(f"{item}\0" for item in members))
    try:
        created = _tar(
            [flag, "--null", "-T", str(listing), "-cf", str(target)], concorde
        )
        if created.returncode != 0:
            raise Refused(
                "archive_failed",
                f"tar could not write {target} (exit {created.returncode}): "
                f"{created.stderr.strip()}; nothing was removed",
                "the old run store is removed only once it is archived",
                reason="environment",
            )
        say(f"archived {len(members)} entries into {target}")
        listed = _tar([flag, "-tf", str(target)], concorde)
        compared = _tar([flag, "--compare", "-f", str(target)], concorde)
    finally:
        listing.unlink(missing_ok=True)
    names = {line.rstrip("/") for line in listed.stdout.splitlines() if line}
    missing = [
        path.relative_to(concorde).as_posix()
        for member in members
        for path in [concorde / member, *sorted((concorde / member).rglob("*"))]
        if path.relative_to(concorde).as_posix() not in names
    ]
    if listed.returncode != 0 or compared.returncode != 0 or missing:
        raise Refused(
            "archive_unverified",
            f"the archive {target} does not match the files it was made from: listing exit "
            f"{listed.returncode}, compare exit {compared.returncode} "
            f"({(compared.stdout + compared.stderr).strip()[:2000]}), "
            f"{len(missing)} entries missing from it ({', '.join(missing[:20])}); nothing was "
            "removed, and the archive is left for inspection",
            "only what an archive verifiably holds is removed",
            reason="environment",
            evidence=[evidence("file", target.as_posix())],
        )
    say(
        f"verified {target}: {len(names)} entries listed, tar --compare found no difference"
    )
    for member in members:
        say(f"remove {concorde / member}")
        _remove(concorde / member)
    runs = concorde / RUNS
    if runs.is_dir() and not any(runs.iterdir()):
        say(f"remove {runs}")
        runs.rmdir()


def held_locks(concorde: Path, members: list[str]) -> list[Path]:
    """The lock files among ``members`` a process still holds."""
    found = []
    for member in members:
        path = concorde / member
        candidates = [path] if path.is_file() else sorted(path.rglob("*.lock"))
        found.extend(
            item
            for item in candidates
            if item.name.endswith(".lock") and locks.held(item)
        )
    return found


def describe(result: Plan, archive_path: Path) -> list[str]:
    lines = []
    for migration in result.migrations:
        old = migration.old
        if migration.done is not None:
            lines.append(f"already in history {migration.done}: {old.task}")
            lines.extend(f"remove {path}" for path in old.sources())
            continue
        target = layout.history_folder(result.concorde) / migration.key
        lines.append(f"task {old.task} ({old.record.get('state')}) -> {target}")
        lines.extend(
            f"  copy {source} -> {relative}" for source, relative in migration.copies
        )
        lines.extend(f"  write {relative}" for relative, _ in migration.writes)
        lines.extend(f"  note {note}" for note in migration.notes)
        lines.extend(f"  remove {path}" for path in old.sources())
    for path, reason in result.skipped:
        lines.append(f"skip {path}: {reason}")
    if result.archived:
        lines.append(f"archive into {archive_path}:")
        lines.extend(f"  {result.concorde / member}" for member in result.archived)
        lines.append("  then remove each of them once the archive is verified")
    return lines


def run(primary: Path, archive_path: Path, *, dry_run: bool, say=print) -> Plan:
    concorde = layout.concorde_of(primary)
    if not concorde.is_dir():
        raise Refused(
            "not_a_project",
            f"{primary} has no .concorde directory",
            "the script works only on a primary worktree's .concorde",
        )
    archive_path = Path(os.path.abspath(archive_path.expanduser()))
    try:
        archive_path.relative_to(os.path.realpath(primary))
        inside = True
    except ValueError:
        inside = False
    if inside:
        raise Refused(
            "archive_inside",
            f"the archive {archive_path} lies inside the primary worktree {primary}",
            "the archive is kept outside the repository",
        )
    result = plan(concorde)
    if dry_run:
        for line in describe(result, archive_path):
            say(line)
        return result
    if result.archived:
        _compression(archive_path)
        if archive_path.exists():
            raise Refused(
                "archive_exists",
                f"the archive {archive_path} already exists",
                "an existing archive is never overwritten",
                options=["name another archive", "move the existing one away"],
            )
        held = held_locks(concorde, result.archived)
        if held:
            raise Refused(
                "lock_held",
                "the old run store has locks a process still holds: "
                + ", ".join(path.as_posix() for path in held),
                "a held lock means an old process may still be writing the run store",
                reason="environment",
            )
    try:
        with locks.hold(layout.lock_file(concorde, "merge"), ACTOR, wait=0.0):
            for migration in result.migrations:
                migrate(concorde, migration, say)
            for path, reason in result.skipped:
                say(f"skip {path}: {reason}")
            if result.archived:
                archive(concorde, result.archived, archive_path, say)
    except locks.LockBusy as error:
        raise Refused(
            "merge_busy",
            f"the merge lock {error.path} is held by {error.holder}",
            "task open, merge and close move task folders while they hold it",
            reason="environment",
        ) from error
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("primary", type=Path, help="the primary worktree's root")
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help="the compressed tar (.tar.zst or .tar.gz) the old run store is packed into",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print every step without doing any"
    )
    arguments = parser.parse_args(argv)
    try:
        result = run(
            arguments.primary.resolve(), arguments.archive, dry_run=arguments.dry_run
        )
    except OSError as error:
        refusal = Refused(
            "migration_failed",
            f"{error}; every old task moved before it is complete in the history, the task "
            "being moved kept its old files, and a staging folder .migrating-<key> it left is "
            "replaced by the next run",
            "the file system refused an operation the migration needs",
            reason="environment",
            options=["fix the cause and run the script again"],
        )
    except Refused as caught:
        refusal = caught
    else:
        refusal = None
    if refusal is not None:
        print(json.dumps({"error": refusal.error}, indent=2))
        print(render(refusal.error), file=sys.stderr)
        return 1
    moved = sum(1 for item in result.migrations if item.done is None)
    print(
        f"{'would move' if arguments.dry_run else 'moved'} {moved} old tasks, "
        f"{'would finish' if arguments.dry_run else 'finished'} "
        f"{len(result.migrations) - moved}, skipped {len(result.skipped)} entries, "
        f"{'would archive' if arguments.dry_run else 'archived'} {len(result.archived)} entries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
