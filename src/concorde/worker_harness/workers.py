"""Run one worker: prepare its run directory, launch and resume it, audit and validate.

``run_worker`` performs a worker run on the backend the request names, Claude Code or pi: freeze
the grant it was given as data, let the backend generate its configuration from the grant, launch
the worker in its own process group while keeping the progress file current, audit the task
worktree after every round, call the caller's round validation after every clean ``ok`` round,
resume the same session with what it reports to repair, perform the deletions the worker proposed,
and write the run record. The returned record keeps the worker's answer verbatim and apart from what
the host observed itself. Whether a round needs repair is the caller's judgement: the worker
harness runs no check, reads no Spec and knows no glossary.

The run directory is the worker run's trace node ``workers/<run-id>/`` inside the node of the run
that asked, holding ``trace.json`` (the run record), ``status.json``, ``grant.json``, ``brief.md``,
the transcript and one node per round; the generated configuration, credential copies and the
worker's own directories live in a runtime directory under ``/tmp`` that is removed when the run
ends, after the transcript was moved into the run directory.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ..kernel.errors import WORKER_ERROR_SCHEMA, evidence, exception_detail, link
from ..kernel.refusal import KernelError
from ..kernel.schema import register, validate
from ..kernel.tracing.kinds import NodeKind, register as register_kinds
from ..kernel.tracing import layout
from ..kernel.tracing.node import Node
from .audit import audit, rw_allows, snapshot
from .claude_backend import BackendRefusal, ClaudeBackend
from .pi_backend import PiBackend
from .placement import PlacementError, place
from .progress import Progress
from .runs import create_run, now, remove_runtime
from .settings import TASK_TYPES, SettingsError, grant_view

BACKENDS = {"claude": ClaudeBackend, "pi": PiBackend}

TAIL = 20_000
# How much of a round's standard error its node keeps.
STDERR_KEPT = 4 * TAIL
_PATHS = {"type": "array", "items": {"type": "string", "minLength": 1}}
_NULLABLE_TEXT = {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]}
# A free-form object: the typed-value check closes an object without additionalProperties.
_OBJECT = {"type": "object", "additionalProperties": {}}
# contract.workers.worker-run-trace, version 5
WORKER_RUN_TRACE = "concorde-worker-run-trace"
register(
    WORKER_RUN_TRACE,
    5,
    {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "task_type",
            "backend_source",
            "local_model",
            "model_map",
            "tools",
            "transcript",
            "worker_result",
            "deleted",
            "deletions_refused",
            "deletions_absent",
            "deletions_failed",
            "rounds",
        ],
        "properties": {
            "task_type": {"type": "string", "minLength": 1},
            "backend_source": _NULLABLE_TEXT,
            "local_model": _NULLABLE_TEXT,
            "model_map": _NULLABLE_TEXT,
            "tools": {
                "anyOf": [
                    {"type": "null"},
                    {"type": "array", "items": {"type": "string", "minLength": 1}},
                ]
            },
            "transcript": {
                "anyOf": [
                    {"type": "null"},
                    {"type": "string", "minLength": 1, "format": "project-path"},
                ]
            },
            "worker_result": {"anyOf": [{"type": "null"}, _OBJECT]},
            "deleted": _PATHS,
            "deletions_refused": _PATHS,
            "deletions_absent": _PATHS,
            "deletions_failed": _PATHS,
            "rounds": {"type": "integer", "minimum": 0},
        },
    },
)
# contract.workers.worker-round-trace, version 4
WORKER_ROUND_TRACE = "concorde-worker-round-trace"
register(
    WORKER_ROUND_TRACE,
    4,
    {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "round",
            "prompt",
            "session",
            "exit",
            "audit",
            "evidence",
            "validation",
            "agent",
        ],
        "properties": {
            "round": {"type": "integer", "minimum": 1},
            "prompt": {"enum": ["initial", "repair"]},
            "session": _NULLABLE_TEXT,
            "exit": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
            "audit": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["verdict", "changed", "violations"],
                        "properties": {
                            "verdict": {"enum": ["clean", "violation"]},
                            "changed": _PATHS,
                            "violations": _PATHS,
                        },
                    },
                ]
            },
            "evidence": {"type": "array", "items": _OBJECT},
            "validation": {"anyOf": [{"type": "null"}, {"type": "string"}]},
            "agent": _OBJECT,
        },
    },
)
register_kinds(
    NodeKind(
        "worker-run",
        WORKER_RUN_TRACE,
        (
            "modules",
            "operation",
            "worker",
            "task_type",
            "backend",
            "model",
            "reasoning",
            "context_identity",
            "grant_digest",
            "brief_digest",
            "settings_digest",
        ),
    ),
    NodeKind("worker-round", WORKER_ROUND_TRACE, ("backend", "model")),
)

WORKER_RESULT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "summary", "error", "proposed_deletions", "output"],
    "properties": {
        "status": {"enum": ["ok", "blocked", "failed"]},
        "summary": {"type": "string", "minLength": 1},
        "error": {"anyOf": [{"type": "null"}, WORKER_ERROR_SCHEMA]},
        "proposed_deletions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "output": {"type": "object"},
    },
}


def result_schema(output_schema: dict | None) -> dict:
    """The worker result schema with the Operation's own output schema at ``output``."""
    schema = copy.deepcopy(WORKER_RESULT_SCHEMA)
    if output_schema is not None:
        schema["properties"]["output"] = copy.deepcopy(output_schema)
    return schema


@dataclass(frozen=True)
class Refusal:
    """What a round validation names when it ends the run: the code, detail and causes of
    Workers' link."""

    code: str
    detail: str
    causes: tuple = ()


@dataclass(frozen=True)
class RoundValidation:
    """A round validation's answer (launch.md#round-validation).

    ``evidence`` is kept with the round, in the caller's own shape; a top-level string of an item
    that is an absolute path below the round's folder is an artifact path, kept relative to that
    folder in the round's node. ``repair`` is the text naming what the worker must repair, which
    becomes the next resume round's prompt; with it, ``failure`` says that the run ends ``failed``
    when no rounds are left for it. Instead of a repair, ``violation`` ends the run at once for what
    the caller does not allow at all, and ``unavailable`` when it could not validate.
    """

    evidence: tuple = ()
    repair: str | None = None
    failure: Refusal | None = None
    violation: Refusal | None = None
    unavailable: Refusal | None = None


@dataclass
class WorkerRequest:
    worktree: Path
    task_type: str
    # The grant as data, in the grant input format (contracts.md#grant-input).
    grant: dict
    instructions: str
    runtime: tuple[Path, ...] = ()
    output_schema: dict | None = None
    rounds: int = 3
    timeout: float = 1800.0
    max_turns: int = 200
    max_budget_usd: float | None = None
    # The project model name the worker configuration chose, recorded only.
    model: str | None = None
    # The model's local id on the backend, passed with --model, and the model map it came from.
    local_model: str | None = None
    model_map: str | None = None
    home: Path | None = None
    claude: str | None = None
    credentials: Path | None = None
    backend: str = "claude"
    # What chose the backend (a configuration entry or the main session's variable), recorded only.
    backend_source: str | None = None
    # The reasoning level: Claude Code's --effort, pi's --thinking.
    reasoning: str | None = None
    # The Operation and worker id the model was chosen for, and the Modules the job is about,
    # labels recorded only.
    operation: str | None = None
    worker: str | None = None
    modules: tuple[str, ...] | None = None
    # The identity of the Operation run that launched the worker, by which an observer pairs
    # the worker with its run.
    operation_run: str | None = None
    pi: str | None = None
    pi_config: Path | None = None
    sandbox_runtime: Path | None = None
    extra: dict = field(default_factory=dict)
    # The caller's round validation, called with the worktree, the round's node folder and the
    # round's worker result, valid against its schema, after every round whose worker ended ok
    # with a clean audit; it answers a ``RoundValidation``.
    round_validation: Callable[[Path, Path, dict], RoundValidation] | None = None
    # Told the run identity as soon as the run exists, so that a caller interrupted while the
    # worker runs can still name it.
    started: Callable[[str], None] | None = None
    # The project's own interpreter, which the worker finds first on its PATH.
    project_python: str | None = None
    # The trace node folder of the run that asked for the worker, below which the worker run's
    # own node, its run directory, is created.
    trace_parent: Path | None = None


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def brief(request: WorkerRequest, worktree: Path) -> str:
    """The worker's only instruction: the task, then its boundary as absolute paths."""
    view = grant_view(request.grant)
    pi = request.backend == "pi"
    shell, writer = ("bash", "write tool") if pi else ("Bash", "Write tool")
    ending = (
        "- End by calling the `concorde_result` tool exactly once with the structured result; "
        "it ends your session."
        if pi
        else "- End with the structured result."
    )

    def listing(level: str) -> str:
        paths = view.paths(level)
        if not paths:
            return "- (none)\n"
        return "".join(
            f"- {(worktree / path).as_posix()}{'/' if path.endswith('/') else ''}\n"
            for path in paths
        )

    return (
        f"# Concorde worker task ({request.task_type})\n\n"
        f"You are a Concorde worker. The task worktree is {worktree.as_posix()}; your working "
        "directory is a private scratch directory outside it, so give your tools absolute "
        "paths. In your structured result, write every path in the task worktree relative to "
        "it, such as `src/app.py`, never as an absolute path.\n\n"
        "## Task\n\n"
        f"{request.instructions.strip()}\n\n"
        "## Your boundary\n\n"
        "You may change only these paths (a path ending with / covers the files below it):\n\n"
        f"{listing('rw')}\n"
        "You may read these paths but not change them:\n\n"
        f"{listing('ro')}\n"
        "You may know that these files exist, but you may not read or change them:\n\n"
        f"{listing('names')}\n"
        "Every other path is hidden from you. A refused read or write means the path is outside "
        "your boundary: do not work around it. If you need it, stop and return `blocked`, naming "
        "the path and why you need it.\n\n"
        + (
            "## Running the project's code\n\n"
            f"The project's own interpreter is {request.project_python}, first on your PATH as "
            "`python`. Run the project's code and tests with it, from the task worktree, never "
            "with another Python on the machine.\n\n"
            if request.project_python
            else ""
        )
        + "## Rules\n\n"
        "- Never use Git and never try to read `.git`.\n"
        "- You cannot delete files. List files that should be deleted in `proposed_deletions`.\n"
        f"- A file you create with {shell} outside the writable paths is lost when you finish; "
        f"create files with the {writer} instead.\n"
        f"{ending} For `ok`, `error` is null. For `blocked` or `failed`, "
        "`error` is required and must let the host reason about it without asking you: a code, "
        "the complete detail (what failed, where, with the exact message or output), your "
        "evidence, everything you tried, why you could not handle it yourself (`unhandled`: "
        "`permission`, `decision`, `scope`, `capability`, `exhausted`, `environment` or `input`, "
        "with a specific explanation), the options you see and your recommendation.\n"
    )


def _launch(request, paths, command, environment, prompt: str, on_line) -> dict:
    """One round: run the command in its own process group, reading standard output as it
    arrives, and always kill the group after."""
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=paths.work,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as error:
        return {
            "error": "launch_failed",
            "detail": str(error),
            "stdout": b"",
            "stderr": b"",
        }
    stdout: list[bytes] = []
    stderr: list[bytes] = []

    def feed() -> None:
        try:
            process.stdin.write(prompt.encode())
            process.stdin.close()
        except OSError:
            pass

    def read_stdout() -> None:
        for line in process.stdout:
            stdout.append(line)
            try:
                on_line(line.decode("utf-8", "replace"))
            except Exception:  # noqa: BLE001 -- progress never changes the run
                pass

    def read_stderr() -> None:
        for chunk in iter(lambda: process.stderr.read(65536), b""):
            stderr.append(chunk)

    threads = [
        threading.Thread(target=target, daemon=True)
        for target in (feed, read_stdout, read_stderr)
    ]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=request.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        _kill_group(process)
    process.wait()
    for thread in threads:
        thread.join(timeout=10)
    return {
        "stdout": b"".join(stdout),
        "stderr": b"".join(stderr)[-4 * TAIL :],
        "exit": process.returncode,
        "timed_out": timed_out,
        "duration": round(time.monotonic() - started, 3),
    }


def _kill_group(process) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def worker_link(record: dict, result: dict) -> dict | None:
    """The worker's own error as a link; its content is the worker's claim."""
    error = result.get("error")
    if not isinstance(error, dict):
        return None
    sessions = [item.get("session") for item in record["rounds"] if item.get("session")]
    return link(
        "worker",
        f"{record['task_type']} worker of {record['run_id']}"
        + (f" (session {sessions[-1]})" if sessions else ""),
        error["code"],
        error["detail"],
        reason=error["unhandled"]["reason"],
        explanation=error["unhandled"]["explanation"],
        evidence=error["evidence"],
        attempts=error["attempts"],
        options=error["options"],
        recommendation=error["recommendation"],
    )


def _consistency(result: dict) -> str | None:
    if result["status"] == "ok" and result.get("error") is not None:
        return (
            "the result has status ok but carries an error; an ok result has error null"
        )
    if result["status"] != "ok" and result.get("error") is None:
        return (
            f"the result has status {result['status']} but no error; a blocked or failed "
            "result must carry its error"
        )
    return None


GRANT_FIELDS = ("task_type", "entries", "context_identity")


def _grant_shape(grant: dict, task_type: str) -> None:
    """Refuse a grant beyond the grant input's fields or for another task type than the request's
    with ``grant_malformed``: the worker harness takes only the grant input, never a richer grant."""
    extra = sorted(set(grant) - set(GRANT_FIELDS))
    if extra:
        raise SettingsError(
            "grant_malformed",
            f"the grant has the field(s) {', '.join(extra)}, which the grant input does not "
            f"define; it holds exactly {', '.join(GRANT_FIELDS)}",
        )
    if grant["task_type"] != task_type:
        raise SettingsError(
            "grant_malformed",
            f"the grant was computed for the task type {grant['task_type']!r}, not the "
            f"request's {task_type!r}",
        )
    if not isinstance(grant["context_identity"], str):
        raise SettingsError(
            "grant_malformed",
            "the grant's context identity is not a string",
        )


def run_worker(request: WorkerRequest) -> dict:
    """Run one worker to its end and return its run record as contract.workers.worker-run-record
    defines it; the record kept is its trace node and its rounds' nodes."""
    worktree = Path(os.path.realpath(request.worktree))
    # Without a parent node, as when a worker is run on its own, the run keeps its node beside
    # the unbound runs of the worktree.
    parent = Path(request.trace_parent or layout.concorde_of(worktree) / "unbound")
    run_id, paths = create_run(parent)
    started = {"node": False}
    try:
        return _run(request, worktree, run_id, paths, started)
    except BaseException:
        if not started["node"]:
            # The run's node could not be started, so no record can end the run; its runtime
            # directory still goes.
            remove_runtime(paths)
        raise


def _run(
    request: WorkerRequest, worktree: Path, run_id: str, paths, started: dict
) -> dict:
    """The run of ``run_worker`` once its run and runtime directories exist; ``started`` is told
    when the run's node exists, from which on the run always ends its own record."""
    actor = f"Workers run {run_id} ({request.task_type} worker)"
    backend = BACKENDS[request.backend]() if request.backend in BACKENDS else None
    trace = paths.trace
    progress = Progress(
        trace,
        run_id=run_id,
        task_type=request.task_type,
        backend=request.backend,
        worktree=worktree.as_posix(),
        operation_run_id=request.operation_run,
    )
    context_identity = (
        request.grant.get("context_identity")
        if isinstance(request.grant, dict)
        else None
    )
    # The node keeps a context identity only as a string; the grant check refuses any other.
    if not isinstance(context_identity, str):
        context_identity = None
    record: dict = {
        "run_id": run_id,
        "task_type": request.task_type,
        "backend": request.backend,
        "backend_source": request.backend_source,
        "operation": request.operation,
        "worker": request.worker,
        "model": request.model,
        "local_model": request.local_model,
        "model_map": request.model_map,
        "reasoning": request.reasoning,
        "worktree": worktree.as_posix(),
        "context_identity": context_identity,
        "grant_digest": None,
        "settings_digest": None,
        "brief_digest": None,
        # The tool set the backend prepared, null until it did.
        "tools": None,
        "started_at": now(),
        "ended_at": None,
        "rounds": [],
        "transcript": None,
        "stderr_tail": "",
        "worker_result": None,
        "deleted": [],
        "deletions_refused": [],
        "deletions_absent": [],
        "deletions_failed": [],
        "status": "failed",
        "error": None,
        "run_directory": trace.as_posix(),
        "runtime_directory": paths.root.as_posix(),
    }
    modules = request.modules
    node = Node(
        trace,
        run_id,
        "worker-run",
        content_type=WORKER_RUN_TRACE,
        metadata={
            "modules": list(modules) if isinstance(modules, (list, tuple)) else None,
            "operation": request.operation,
            "worker": request.worker,
            "task_type": request.task_type,
            "backend": request.backend,
            "model": request.model,
            "reasoning": request.reasoning,
            "context_identity": context_identity,
        },
        content=_run_content(record),
        started_at=record["started_at"],
    )
    for identity, relative in (
        ("progress", layout.PROGRESS),
        ("grant", "grant.json"),
        ("brief", "brief.md"),
        ("transcript", "transcript.jsonl"),
    ):
        node.keep(identity, relative)
    node.start()
    started["node"] = True
    # The transcript the backend writes in the runtime directory, moved into the run directory
    # when the run ends, and the latest session the worker's output named, even in a round that
    # never returned.
    source: dict = {"transcript": None, "session": None}
    rounds: dict = {}
    attempts: list[str] = []
    # The valid worker result of the last round if its audit was clean: its proposed deletions are
    # performed when the run ends, unless the round validation answered a violation.
    pending: dict = {"result": None}

    def workers_link(
        code: str, detail: str, reason: str, explanation: str, **extra
    ) -> dict:
        found = list(extra.pop("evidence", ()))
        if record["transcript"]:
            found.append(evidence("transcript", record["transcript"], ""))
        found.append(evidence("trace", run_id, trace.as_posix()))
        return link(
            "workers",
            actor,
            code,
            detail,
            reason=reason,
            explanation=explanation,
            evidence=found,
            **extra,
        )

    def deletion_link(failed: list[str], cause: dict | None) -> dict:
        def listed(paths) -> str:
            return ", ".join(paths) or "none"

        return workers_link(
            "deletion_failed",
            f"the host could not delete {len(failed)} of the worker's proposed deletion(s): "
            f"{', '.join(failed)}; it deleted {listed(record['deleted'])}, refused "
            f"{listed(record['deletions_refused'])} and found already absent "
            f"{listed(record['deletions_absent'])}; the deletions it made stay done",
            "environment",
            "Workers deletes only what the worker proposed and does not retry a deletion the "
            "operating system refused",
            attempts=attempts,
            causes=[cause],
        )

    def finish(status: str, error: dict | None = None) -> dict:
        problems: list[str] = []
        if backend is not None and source["session"]:
            found = backend.transcript(paths, source["session"])
            if found:
                source["transcript"] = found
        if source["transcript"]:
            problem = _keep_transcript(source["transcript"], trace)
            record["transcript"] = (
                (trace / TRANSCRIPT).as_posix() if problem is None else None
            )
            if problem is not None:
                problems.append(problem)
        result, pending["result"] = pending["result"], None
        if result is not None:
            failed = _finalize(worktree, record, result)
            if failed:
                status, error = "failed", deletion_link(failed, error)
        problem = remove_runtime(paths)
        if problem is not None:
            problems.append(problem)
        if problems:
            status, error = (
                "failed",
                workers_link(
                    "cleanup_failed",
                    "the host could not clean up once the worker had ended: "
                    + "; ".join(problems),
                    "environment",
                    "Workers keeps the transcript and removes the runtime directory with the "
                    "file system's own operations and cannot repair what the operating system "
                    "refused; what remains is for whoever runs the host to remove",
                    attempts=attempts,
                    causes=[error],
                ),
            )
        for number, round_node in list(rounds.items()):
            if round_node.record["status"] == "running":
                _finish_round(
                    round_node, record["rounds"][number - 1], "failed", "interrupted"
                )
        record["status"] = status
        record["error"] = error
        record["ended_at"] = now()
        interrupted = bool(error) and error.get("code") == "interrupted"
        # The progress file is final before the node takes the digests of its files.
        progress.finish(status)
        node.finish(
            status,
            outcome="interrupted" if interrupted else status,
            error=error,
            content=_run_content(record),
            ended_at=record["ended_at"],
            grant_digest=record["grant_digest"],
            brief_digest=record["brief_digest"],
            settings_digest=record["settings_digest"],
        )
        return record

    def fail(code: str, detail: str, reason: str, explanation: str, **extra) -> dict:
        return finish(
            "failed", workers_link(code, detail, reason, explanation, **extra)
        )

    def attempt() -> dict:
        if backend is None:
            return fail(
                "unknown_backend",
                f"the worker request names the backend {request.backend!r}; Workers knows "
                + ", ".join(sorted(BACKENDS)),
                "input",
                "the backend is chosen by the configuration reader before the launch, and "
                "Workers launches only the programs it knows",
            )
        if (
            request.task_type not in TASK_TYPES
            or not isinstance(request.grant, dict)
            or not request.grant.get("task_type")
            or not request.grant.get("context_identity")
            or "entries" not in request.grant
        ):
            missing = [
                name
                for name, present in (
                    ("a known task type", request.task_type in TASK_TYPES),
                    ("a grant object", isinstance(request.grant, dict)),
                    (
                        "the grant's task type",
                        isinstance(request.grant, dict)
                        and bool(request.grant.get("task_type")),
                    ),
                    (
                        "a context identity",
                        isinstance(request.grant, dict)
                        and bool(request.grant.get("context_identity")),
                    ),
                    (
                        "grant entries",
                        isinstance(request.grant, dict) and "entries" in request.grant,
                    ),
                )
                if not present
            ]
            return fail(
                "grant_unavailable",
                f"the worker request for task type {request.task_type!r} lacks "
                + ", ".join(missing),
                "input",
                "Workers launches only with a complete frozen grant, which its caller computes",
            )
        try:
            rw = grant_view(request.grant).paths("rw")
            _grant_shape(request.grant, request.task_type)
        except SettingsError as error:
            return fail(
                error.code,
                f"the worker request's grant for task type {request.task_type!r} is "
                f"malformed: {error}",
                "input",
                "Workers launches only with a well-formed frozen grant, which its caller "
                "computes; it never repairs or guesses a grant",
            )
        grant_file = trace / "grant.json"
        grant_file.write_text(json.dumps(request.grant, indent=2, sort_keys=True))
        record["grant_digest"] = _digest(grant_file)
        schema = result_schema(request.output_schema)
        schema_text = json.dumps(schema, separators=(",", ":"))
        (paths.control / "result.schema.json").write_text(schema_text)
        try:
            placement = place(worktree, request.runtime)
        except PlacementError as error:
            return fail(
                error.code,
                str(error),
                "environment",
                "Workers hides a repository's Git metadata from a worker only where it knows "
                "it, so it never launches a worker in another placement and cannot move the "
                "worktree itself",
            )
        try:
            configuration = backend.prepare(request, worktree, paths, schema, placement)
        except BackendRefusal as refusal:
            return fail(
                refusal.code, refusal.detail, refusal.reason, refusal.explanation
            )
        record["tools"] = backend.tools(request.task_type, request.grant)
        brief_file = trace / "brief.md"
        brief_file.write_text(brief(request, worktree))
        record.update(
            settings_digest=_digest(configuration), brief_digest=_digest(brief_file)
        )
        node.update(
            grant_digest=record["grant_digest"],
            brief_digest=record["brief_digest"],
            settings_digest=record["settings_digest"],
        )
        try:
            before = snapshot(worktree)
        except (OSError, subprocess.CalledProcessError) as error:
            return fail(
                "snapshot_failed",
                f"the task worktree {worktree} cannot be snapshotted before the launch: "
                + exception_detail(error),
                "environment",
                "the audit needs a snapshot from read-only Git, which failed",
            )

        session: str | None = None
        environment = backend.environment(request, paths)
        prompt, kind = brief_file.read_text(), "initial"
        for number in range(1, request.rounds + 2):
            pending["result"] = None
            round_record: dict = {"round": number, "prompt": kind}
            record["rounds"].append(round_record)
            round_node = _start_round(trace, number, request, round_record)
            rounds[number] = round_node
            node.update(content=_run_content(record))
            command = backend.command(request, paths, schema_text, session)
            stream = backend.stream()

            def on_line(line: str, stream=stream) -> None:
                for tool, arguments in stream.feed(line):
                    progress.action(tool, arguments)
                if stream.session:
                    source["session"] = stream.session

            progress.phase("worker", round=number)
            outcome = _launch(request, paths, command, environment, prompt, on_line)
            record["stderr_tail"] = outcome["stderr"][-TAIL:].decode("utf-8", "replace")
            _keep_stderr(round_node, outcome["stderr"])
            round_record.update(
                exit=outcome.get("exit"), duration=outcome.get("duration")
            )
            if outcome.get("error"):
                _finish_round(round_node, round_record, "failed", "launch_failed")
                return fail(
                    outcome["error"],
                    f"round {number}: the command {command[0]} could not be started: "
                    f"{outcome.get('detail', '')}",
                    "environment",
                    backend.missing_command,
                    attempts=attempts,
                )
            concluded = stream.conclude(outcome)
            if concluded.session:
                session = concluded.session
            source["session"] = session or source["session"]
            round_record["session"] = session
            round_record.update(concluded.info)
            round_record["usage"] = dict(concluded.usage)
            source["transcript"] = backend.transcript(paths, session)
            if source["transcript"]:
                record["transcript"] = (trace / TRANSCRIPT).as_posix()
            progress.phase("audit")
            verdict = audit(worktree, before, rw)
            round_record["audit"] = verdict.record()
            # A write outside the grant is reported whatever else went wrong in the round.
            outside = (
                ""
                if verdict.clean
                else f"; the worker also changed {len(verdict.violations)} path(s) outside "
                f"the grant's writable paths: {', '.join(verdict.violations)}"
            )
            result = concluded.result
            invalid = None
            try:
                if result is None:
                    text = concluded.final_text
                    raise KernelError(
                        "invalid_field",
                        "the worker ended without a structured result"
                        + (f"; its final text: {text[-2000:]}" if text else ""),
                    )
                validate(result, schema)
                invalid = _consistency(result)
            except KernelError as error:
                invalid = f"{error.field or '/'}: {error}"
            # A valid result is kept whatever else ended the round, and its proposed deletions
            # are performed at the end when the round's audit was clean.
            if invalid is None:
                record["worker_result"] = result
                if verdict.clean:
                    pending["result"] = result
            if outcome["timed_out"]:
                _finish_round(round_node, round_record, "failed", "timed_out")
                return fail(
                    "worker_timeout",
                    f"round {number} did not finish within {request.timeout}s; the process "
                    f"group was killed{outside}",
                    "exhausted",
                    f"Workers stops every round at the configured timeout ({request.timeout}s, "
                    "limits.timeout_seconds of .concorde/workers.json) and does not extend it",
                    attempts=attempts,
                )
            failure = concluded.failure
            if failure is not None:
                exhausted = concluded.exhausted
                _finish_round(
                    round_node,
                    round_record,
                    "failed",
                    "limit_reached" if exhausted else "process_failed",
                )
                return fail(
                    "worker_limit_reached" if exhausted else backend.failure_code,
                    f"round {number}: the {backend.process} process ended with an error "
                    f"({failure['code']}) before a structured result{outside}",
                    "exhausted" if exhausted else "environment",
                    (
                        f"Workers does not raise the limits it was given (max_turns "
                        f"{request.max_turns}, max_budget_usd {request.max_budget_usd})"
                        if exhausted
                        else f"Workers does not retry a failed {backend.process} process"
                    ),
                    attempts=attempts,
                    causes=[failure],
                )
            if not verdict.clean:
                _finish_round(round_node, round_record, "failed", "audit_violation")
                return fail(
                    "audit_violation",
                    f"round {number}: the worker changed {len(verdict.violations)} path(s) "
                    f"outside the grant's writable paths: {', '.join(verdict.violations)}; "
                    + (
                        f"its result was invalid: {invalid}"
                        if invalid
                        else f"the worker itself reported status {result['status']}"
                    ),
                    "permission",
                    "Workers never accepts a write outside the grant and never widens it",
                    evidence=[
                        evidence("audit", str(number), f"violation: {path}")
                        for path in verdict.violations
                    ],
                    attempts=attempts,
                    causes=[None if invalid else worker_link(record, result)],
                )
            if invalid:
                _finish_round(round_node, round_record, "failed", "result_invalid")
                return fail(
                    "worker_result_invalid",
                    f"round {number}: the worker's result does not satisfy its result "
                    f"schema: {invalid}",
                    "capability",
                    "Workers cannot repair a worker's answer and does not relaunch a worker for "
                    "an invalid one",
                    evidence=[
                        evidence(
                            "result-schema",
                            "the worker result schema of this run, given to the worker",
                            "",
                        )
                    ],
                    attempts=attempts,
                )
            if result["status"] != "ok":
                _finish_round(
                    round_node, round_record, result["status"], result["status"]
                )
                cause = worker_link(record, result)
                return finish(
                    result["status"],
                    link(
                        "workers",
                        actor,
                        f"worker_{result['status']}",
                        f"the {request.task_type} worker ended {result['status']} in round "
                        f"{number} with {cause['code']}: {cause['detail']}",
                        reason="capability",
                        explanation="Workers resumes a worker only to repair what its caller's "
                        "round validation reports; it returns every other blocker unchanged",
                        evidence=[evidence("trace", run_id, trace.as_posix())]
                        + (
                            [evidence("transcript", record["transcript"])]
                            if record["transcript"]
                            else []
                        ),
                        attempts=attempts,
                        causes=[cause],
                    ),
                )
            if request.round_validation is None:
                _finish_round(round_node, round_record, "ok", "ok")
                return finish("ok")
            progress.phase("validation", round=number)
            try:
                answer = request.round_validation(worktree, round_node.folder, result)
                if not isinstance(answer, RoundValidation):
                    raise TypeError(
                        f"it answered a {type(answer).__name__}, not a RoundValidation"
                    )
            except Exception as error:  # noqa: BLE001 -- the caller's code, reported in full
                detail = exception_detail(error)
                round_record["evidence"] = []
                round_record["validation"] = f"not run: {detail}"
                _finish_round(
                    round_node, round_record, "failed", "validation_unavailable"
                )
                return fail(
                    "validation_unavailable",
                    f"round {number}: the round validation raised instead of answering: "
                    f"{detail}",
                    "capability",
                    "Workers cannot validate a round itself and never accepts a round its "
                    "caller could not validate",
                    attempts=attempts,
                )
            round_record["evidence"] = [dict(item) for item in answer.evidence]
            if answer.unavailable is not None:
                refusal = answer.unavailable
                round_record["validation"] = f"not run: {refusal.detail}"
                _finish_round(
                    round_node, round_record, "failed", "validation_unavailable"
                )
                return fail(
                    refusal.code,
                    f"round {number}: the round validation could not validate: "
                    f"{refusal.detail}",
                    "environment",
                    "Workers cannot validate a round itself and never accepts a round its "
                    "caller could not validate",
                    attempts=attempts,
                    causes=list(refusal.causes),
                )
            if answer.violation is not None:
                # A round its caller does not allow at all leaves the worktree to the caller.
                pending["result"] = None
                refusal = answer.violation
                round_record["validation"] = f"violation: {refusal.detail}"
                _finish_round(
                    round_node, round_record, "failed", "validation_violation"
                )
                return fail(
                    refusal.code,
                    f"round {number}: {refusal.detail}",
                    "permission",
                    "Workers never resumes a round its caller does not allow at all",
                    attempts=attempts,
                    causes=list(refusal.causes),
                )
            if not answer.repair:
                round_record["validation"] = "clean"
                _finish_round(round_node, round_record, "ok", "ok")
                return finish("ok")
            round_record["validation"] = answer.repair
            attempts.append(
                f"round {number}: the worker ended ok; "
                + (
                    answer.failure.detail
                    if answer.failure is not None
                    else "the round validation reported something to repair"
                )
            )
            if number > request.rounds:
                if answer.failure is None:
                    _finish_round(round_node, round_record, "ok", "ok")
                    return finish("ok")
                refusal = answer.failure
                _finish_round(round_node, round_record, "failed", "validation_failed")
                return fail(
                    refusal.code,
                    f"{refusal.detail}, after {number} round(s) ({request.rounds} resume "
                    "round(s) allowed)",
                    "exhausted",
                    f"Workers resumes the worker at most {request.rounds} time(s) with what its "
                    "round validation reports and does not extend that",
                    attempts=attempts,
                    causes=list(refusal.causes),
                )
            _finish_round(round_node, round_record, "failed", "repair")
            prompt, kind = answer.repair, "repair"
        raise AssertionError("every round ends the run or resumes it")

    try:
        if request.started is not None:
            request.started(run_id)
        return attempt()
    except BaseException as error:
        # A signal (the host's cancellation), an interrupt or an unexpected error ended the run:
        # its record and progress file still end, so no reader sees a worker that runs forever,
        # and the worktree is left as the interruption found it.
        if record["ended_at"] is None:
            pending["result"] = None
            fail(
                "interrupted",
                f"the worker run ended before it finished: {type(error).__name__}"
                + (f" ({error})" if str(error) else ""),
                "environment",
                "the run was ended from outside the worker, and Workers does not resume it",
            )
        raise


TRANSCRIPT = "transcript.jsonl"


def _run_content(record: dict) -> dict:
    """The content of the worker run's trace node: what is not one of its uniform fields."""
    return {
        "task_type": record["task_type"],
        "backend_source": record["backend_source"],
        "local_model": record["local_model"],
        "model_map": record["model_map"],
        # The record keeps the tool set as the backend's comma-separated list; its trace node
        # keeps it as an array of tool names.
        "tools": [name for name in record["tools"].split(",") if name]
        if record["tools"] is not None
        else None,
        "transcript": TRANSCRIPT if record["transcript"] else None,
        "worker_result": record["worker_result"],
        "deleted": list(record["deleted"]),
        "deletions_refused": list(record["deletions_refused"]),
        "deletions_absent": list(record["deletions_absent"]),
        "deletions_failed": list(record["deletions_failed"]),
        "rounds": len(record["rounds"]),
    }


def _start_round(
    trace: Path, number: int, request: WorkerRequest, round_record: dict
) -> Node:
    round_node = Node(
        layout.round_folder(trace, number),
        str(number),
        "worker-round",
        content_type=WORKER_ROUND_TRACE,
        metadata={"backend": request.backend, "model": request.model},
        content=_round_content(round_record, layout.round_folder(trace, number)),
    )
    round_node.keep("stderr", "stderr.log")
    return round_node.start()


def _round_content(round_record: dict, folder: Path) -> dict:
    agent = {key: round_record[key] for key in ("claude", "pi") if key in round_record}
    evidence_kept = [
        {key: _artifact(value, folder) for key, value in item.items()}
        for item in round_record.get("evidence") or []
    ]
    exit_code = round_record.get("exit")
    validation = round_record.get("validation")
    return {
        "round": round_record["round"],
        "prompt": round_record["prompt"],
        "session": round_record.get("session") or None,
        "exit": exit_code if isinstance(exit_code, int) else None,
        "audit": round_record.get("audit"),
        "evidence": evidence_kept,
        "validation": validation if isinstance(validation, str) else None,
        "agent": agent,
    }


def _artifact(value, folder: Path):
    """An evidence value as a round's node keeps it: an absolute path below the round's folder
    relative to it, anything else unchanged."""
    if isinstance(value, str) and os.path.isabs(value):
        try:
            return Path(value).relative_to(folder).as_posix()
        except ValueError:
            return value
    return value


def _finish_round(
    round_node: Node, round_record: dict, status: str, outcome: str
) -> None:
    used = dict(round_record.get("usage") or {})
    if round_record.get("duration") is not None:
        used["duration_seconds"] = round_record["duration"]
    # The returned record holds the round's usage as its node keeps it.
    round_record["usage"] = used
    round_node.finish(
        status,
        outcome=outcome,
        used=used,
        content=_round_content(round_record, round_node.folder),
        error=None,
    )


def _keep_stderr(round_node: Node, stderr: bytes) -> None:
    try:
        (round_node.folder / "stderr.log").write_bytes(stderr[-STDERR_KEPT:])
    except OSError:
        pass


def _keep_transcript(source: str, trace: Path) -> str | None:
    """Move the session's transcript from the runtime directory into the run directory; None
    once it is there, otherwise why it is not."""
    try:
        shutil.copyfile(source, trace / TRANSCRIPT)
    except OSError as error:
        return (
            f"the transcript {source} could not be kept as {trace / TRANSCRIPT}: "
            f"{error.strerror or error}"
        )
    return None


def _finalize(worktree: Path, record: dict, result: dict) -> list[str]:
    """Perform the proposed deletions after the last round's clean audit; return each failed one
    with its error. A repeated entry is dropped, an absent one recorded as absent, and a failure does not
    stop the others."""
    rw = [
        entry["path"]
        for entry in json.loads(
            (Path(record["run_directory"]) / "grant.json").read_text()
        )["entries"]
        if entry["level"] == "rw"
    ]
    seen: set[Path] = set()
    failures: list[str] = []
    for proposed in result.get("proposed_deletions", []):
        lexical = Path(os.path.normpath(os.path.join(worktree, proposed)))
        # The directories' symbolic links resolved, so that the path judged is the entry the
        # deletion removes; a final link is removed itself, never its target.
        absolute = Path(os.path.realpath(lexical.parent)) / lexical.name
        if absolute in seen:
            continue
        seen.add(absolute)
        try:
            relative = absolute.relative_to(worktree).as_posix()
        except ValueError:
            record["deletions_refused"].append(proposed)
            continue
        exists = os.path.lexists(absolute)
        if not rw_allows(rw, relative) or (exists and not absolute.is_file()):
            record["deletions_refused"].append(proposed)
        elif not exists:
            record["deletions_absent"].append(relative)
        else:
            try:
                absolute.unlink()
            except OSError as error:
                record["deletions_failed"].append(relative)
                failures.append(f"{relative} ({error.strerror or error})")
            else:
                record["deleted"].append(relative)
    return failures


__all__ = [
    "WORKER_RESULT_SCHEMA",
    "Refusal",
    "RoundValidation",
    "WorkerRequest",
    "brief",
    "result_schema",
    "run_worker",
]
