"""Launch one Concorde worker as a Pi process in RPC mode and admit its structured result.

A worker launch names everything the process may use: its workspace, the files it may read and
write, its non-delegating tool allowlist, its model and thinking
level, its system prompt, its input message and the JSON schema of its result. The runtime turns
that into one private run directory:

- ``agent/``: the Pi configuration directory (``PI_CODING_AGENT_DIR``) with Concorde's settings,
  the developer's Pi credentials (``auth.json`` and custom ``models.json``) copied in;
- ``policy.json`` and ``system-prompt.md``: what the Concorde worker extension enforces and injects;
- ``tmp/``: the process's temporary directory, so no worker state lands in the shared one;
- ``host.sock``: the host's check/report service, present for ``run_checks`` or ``report_issue``.

The process starts with Pi's ambient discovery disabled (no sessions, context files, skills,
prompt templates, themes or discovered extensions) and loads only the Concorde worker extension. It runs inside the worker sandbox (``worker_sandbox``):
the host filesystem read-only with the developer's secrets, agent-client state and other
worktrees masked, only the launch's write paths and the run directory writable, a private
temporary directory and PID namespace; an unavailable sandbox refuses the launch. The result is
the ``details`` of the worker's single successful ``submit_result`` call; the caller validates it
against its own typed contract.
"""

from __future__ import annotations

import json
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, cast

from .harness import SAFE_ENVIRONMENT
from .pi_rpc import PiRpcCancelled, PiRpcError, PiRpcTimeout, PiRun, run_prompt
from .timing import Span, timed
from .worker_sandbox import (
    WorkerSandboxError,
    bubblewrap_argv,
    create_placeholders,
    plan_mounts,
    remove_untouched_placeholders,
    unavailable_reason,
)

BUILTIN_TOOLS = frozenset({"read", "grep", "find", "ls", "edit", "write", "bash"})
CONCORDE_TOOLS = frozenset({"submit_result", "run_checks", "report_issue"})
THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max")

# Provider credentials Pi reads from the environment (Pi's providers documentation). They reach the
# Pi process so it can call its model; the worker extension unsets them before every shell command.
PROVIDER_CREDENTIALS = (
    "AI_GATEWAY_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANT_LING_API_KEY",
    "AWS_BEARER_TOKEN_BEDROCK",
    "AZURE_OPENAI_API_KEY",
    "CEREBRAS_API_KEY",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_API_KEY",
    "CLOUDFLARE_GATEWAY_ID",
    "DEEPSEEK_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "HF_TOKEN",
    "MISTRAL_API_KEY",
    "NVIDIA_API_KEY",
    "OPENAI_API_KEY",
    "OPENCODE_API_KEY",
    "OPENROUTER_API_KEY",
    "RADIUS_API_KEY",
    "XAI_API_KEY",
    "ZAI_API_KEY",
    "ZAI_CODING_CN_API_KEY",
)

PI_SETTINGS = {
    "defaultProjectTrust": "never",
    "quietStartup": True,
    "enableInstallTelemetry": False,
}
Outcome = Literal["failed", "cancelled", "limit_exhausted", "invalid_completion"]
# Execution outcomes classify why a run produced no result; they are not error codes.
FAILED: Outcome = "failed"
CANCELLED: Outcome = "cancelled"
LIMIT_EXHAUSTED: Outcome = "limit_exhausted"
INVALID_COMPLETION: Outcome = "invalid_completion"


class WorkerExecutionError(RuntimeError):
    """A worker launch was refused, failed, was cancelled, ran out of time or returned no result."""

    def __init__(
        self, message: str, outcome: Outcome = FAILED, run: PiRun | None = None
    ):
        super().__init__(message)
        self.outcome: Outcome = outcome
        self.run = run


@dataclass(frozen=True)
class WorkerLaunch:
    worker: str
    workspace: str
    system_prompt: str
    message: str
    result_schema: Mapping[str, Any]
    tools: tuple[str, ...]
    read_paths: tuple[str, ...] = ()
    write_paths: tuple[str, ...] = ()
    model: str | None = None
    thinking: str | None = None
    timeout_seconds: float = 1800
    report_schema: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class WorkerResult:
    value: dict[str, Any]
    run: PiRun
    usage: dict[str, Any]


@timed("pi.prepare_validate")
def validate_launch(
    launch: WorkerLaunch, *, has_checks: bool, has_reporter: bool = False
) -> None:
    tools = set(launch.tools)
    if len(tools) != len(launch.tools):
        raise WorkerExecutionError("worker tool lists contain duplicates")
    unknown = tools - BUILTIN_TOOLS - CONCORDE_TOOLS
    if unknown:
        raise WorkerExecutionError(
            f"unknown or non-terminal worker tools: {sorted(unknown)}"
        )
    if "submit_result" not in tools:
        raise WorkerExecutionError("every worker must be granted submit_result")
    if "run_checks" in tools and not has_checks:
        raise WorkerExecutionError("run_checks requires a host check service")
    if ("report_issue" in tools) != (has_reporter and launch.report_schema is not None):
        raise WorkerExecutionError(
            "report_issue requires exactly a host reporter and its schema"
        )
    if launch.report_schema is not None and "report_issue" not in tools:
        raise WorkerExecutionError(
            "a report schema cannot grant an unlisted reporting tool"
        )
    if {"edit", "write"} & tools and not launch.write_paths:
        raise WorkerExecutionError("edit and write require a write grant")
    if launch.thinking is not None and launch.thinking not in THINKING_LEVELS:
        raise WorkerExecutionError(f"unsupported thinking level: {launch.thinking}")
    if not Path(launch.workspace).is_absolute() or not Path(launch.workspace).is_dir():
        raise WorkerExecutionError(
            "the worker workspace must be an existing absolute directory"
        )
    if launch.timeout_seconds <= 0:
        raise WorkerExecutionError("the worker timeout must be positive")


class _HostToolServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True

    def __init__(
        self,
        path: str,
        checks: Callable[[], Any] | None,
        reporter: Callable[[dict], Any] | None,
    ):
        from contextvars import copy_context

        context = copy_context()
        self.checks = (
            (lambda: context.copy().run(checks)) if checks is not None else None
        )
        self.reporter = (
            (lambda value: context.copy().run(reporter, value))
            if reporter is not None
            else None
        )
        super().__init__(path, _HostToolHandler)


class _HostToolHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            server = self.server
            if not isinstance(server, _HostToolServer):
                raise ValueError("host tool handler requires its declared server")
            self.connection.settimeout(10)
            raw = self.rfile.readline(128 * 1024 + 1)
            if len(raw) > 128 * 1024 or not raw.endswith(b"\n"):
                raise ValueError(
                    "host tool request exceeds its frame limit or is incomplete"
                )
            request = json.loads(raw)
            if request == {"tool": "run_checks"} and server.checks is not None:
                reply = server.checks()
            elif (
                isinstance(request, dict)
                and set(request) == {"tool", "report"}
                and request["tool"] == "report_issue"
                and server.reporter is not None
            ):
                reply = server.reporter(request["report"])
            else:
                raise ValueError("unknown or ungranted host tool")
        except (
            Exception
        ) as error:  # explicit rejection, never a successful report receipt
            from .execution_error import exception_feedback, safe_text

            feedback = exception_feedback(error, layer="worker-host-tool")
            reply = {
                "error": safe_text(f"{type(error).__name__}: {error}")
                + "\n"
                + json.dumps(feedback),
                "feedback": feedback,
            }
        try:
            self.wfile.write(json.dumps(reply).encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError):
            # An accepted report is already durable even if its worker was cancelled before ack.
            pass


def _usage(launch: WorkerLaunch, run: PiRun) -> dict[str, Any]:
    stats = run.stats or {}
    reported_tokens = stats.get("tokens")
    tokens = reported_tokens if isinstance(reported_tokens, dict) else {}

    def count(value):
        return value if type(value) is int and value >= 0 else None

    cost = stats.get("cost")
    try:
        cost_usd = (
            float(cost)
            if isinstance(cost, (int, float))
            and not isinstance(cost, bool)
            and cost >= 0
            else None
        )
    except OverflowError:
        cost_usd = None
    return {
        "model": launch.model,
        "input_tokens": count(tokens.get("input")),
        "cached_input_tokens": count(tokens.get("cacheRead")),
        "output_tokens": count(tokens.get("output")),
        "total_tokens": count(tokens.get("total")),
        "cost_usd": cost_usd,
        "turns": count(stats.get("assistantMessages")),
        "wall_seconds": round(run.wall_seconds, 3),
    }


def _read_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() and not path.is_symlink() else None


def _return_refreshed_auth(copy: Path, original: Path, issued: bytes | None) -> None:
    """Carry an OAuth refresh Pi made inside the run back to the developer's credentials.

    A provider may rotate its refresh token, so a refresh left in the discarded copy would strand
    the developer's own file. The copy is written back only when it changed, is a JSON object, and
    the developer's file still holds the bytes the run was issued, so a concurrent refresh wins.
    """
    refreshed = _read_bytes(copy)
    if (
        issued is None
        or refreshed is None
        or refreshed == issued
        or _read_bytes(original) != issued
    ):
        return
    try:
        if not isinstance(json.loads(refreshed), dict):
            return
    except ValueError:
        return
    staged = original.with_name(f".{original.name}.{os.getpid()}.concorde")
    staged.write_bytes(refreshed)
    os.chmod(staged, 0o600)
    os.replace(staged, original)


@dataclass(frozen=True)
class PiWorkerRuntime:
    """Runs worker launches; every injected field is trusted host configuration, never task input."""

    package_root: Path
    pi_executable: str | None = None
    environment: Mapping[str, str] | None = None
    credentials_dir: Path | None = None
    popen: Callable[..., Any] = subprocess.Popen

    @timed("pi.worker_total")
    def __call__(
        self,
        launch: WorkerLaunch,
        *,
        checks: Callable[[], Any] | None = None,
        report_issue: Callable[[dict], Any] | None = None,
    ) -> WorkerResult:
        preparation = Span(
            "pi.prepare",
            prompt_bytes=len(launch.system_prompt.encode()),
            context_bytes=len(launch.message.encode()),
        )
        validate_launch(
            launch, has_checks=checks is not None, has_reporter=report_issue is not None
        )
        source = dict(os.environ if self.environment is None else self.environment)
        executable = self.pi_executable or shutil.which("pi", path=source.get("PATH"))
        if not executable:
            raise WorkerExecutionError("the pi executable is not on PATH")
        extension = (
            Path(self.package_root) / "pi/extensions/concorde-worker.ts"
        ).absolute()
        if not extension.is_file():
            raise WorkerExecutionError(
                f"the Concorde worker extension is missing: {extension}"
            )
        unavailable = unavailable_reason()
        if unavailable:
            # The boundary is part of the launch contract: never run a worker unconfined instead.
            raise WorkerExecutionError(f"worker sandbox unavailable: {unavailable}")
        credentials = self.credentials_dir or Path(
            source.get("PI_CODING_AGENT_DIR")
            or Path(source.get("HOME", "~")).expanduser() / ".pi" / "agent"
        )
        with tempfile.TemporaryDirectory(
            prefix="concorde-pi-worker-", dir="/tmp"
        ) as directory:
            run_dir = Path(directory)
            agent_dir, temporary, home = (
                run_dir / "agent",
                run_dir / "tmp",
                run_dir / "home",
            )
            agent_dir.mkdir()
            temporary.mkdir()
            home.mkdir()
            for name in ("auth.json", "models.json"):
                if (credentials / name).is_file():
                    shutil.copyfile(credentials / name, agent_dir / name)
                    os.chmod(agent_dir / name, 0o600)
            issued_auth = _read_bytes(agent_dir / "auth.json")
            (agent_dir / "settings.json").write_text(
                json.dumps(PI_SETTINGS), encoding="utf-8"
            )
            (run_dir / "system-prompt.md").write_text(
                launch.system_prompt, encoding="utf-8"
            )
            socket_path = (
                run_dir / "host.sock"
                if checks is not None or report_issue is not None
                else None
            )
            policy = {
                "schema_version": 2,
                "worker": launch.worker,
                "workspace": launch.workspace,
                "read_paths": list(launch.read_paths),
                "write_paths": list(launch.write_paths),
                "tools": list(launch.tools),
                "system_prompt_path": str(run_dir / "system-prompt.md"),
                "result_schema": dict(launch.result_schema),
                "report_schema": dict(launch.report_schema)
                if launch.report_schema is not None
                else None,
                "host_socket": str(socket_path) if socket_path else None,
                "scrub_environment": list(PROVIDER_CREDENTIALS),
            }
            (run_dir / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
            env = {
                key: value
                for key, value in source.items()
                if key in SAFE_ENVIRONMENT or key in PROVIDER_CREDENTIALS
            }
            # The process's HOME is inside the run directory: the developer's own home stays
            # readable only where the sandbox does not mask it, and nothing is written there.
            env.update(
                PI_CODING_AGENT_DIR=str(agent_dir),
                CONCORDE_WORKER_POLICY=str(run_dir / "policy.json"),
                PI_OFFLINE="1",
                PI_SKIP_VERSION_CHECK="1",
                PI_TELEMETRY="0",
                HOME=str(home),
                TMPDIR=str(temporary),
                TMP=str(temporary),
                TEMP=str(temporary),
            )
            argv = [
                executable,
                "--mode",
                "rpc",
                "--no-session",
                "--no-context-files",
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--no-extensions",
                "-e",
                str(extension),
            ]
            argv += ["--no-approve", "--offline", "--tools", ",".join(launch.tools)]
            if launch.model:
                argv += ["--model", launch.model]
            if launch.thinking:
                argv += ["--thinking", launch.thinking]
            preparation.finish()
            placeholders: tuple[str, ...] = ()
            try:
                # The mount plan is the launch's grant: workspace read-only, write paths and
                # pending placeholders writable, run directory writable, secrets and other
                # worktrees masked. The Pi process runs inside it.
                local = Path(self.package_root) / "pi/node_modules/typebox"
                managed = (
                    Path(self.package_root).parent
                    / ".venv/share/concorde/pi/node_modules/typebox"
                )
                installed = (
                    Path(self.package_root).name == "framework"
                    and Path(self.package_root).parent.name == ".concorde"
                )
                dependencies = (managed if installed else local).absolute()
                plan = plan_mounts(
                    launch.workspace,
                    launch.write_paths,
                    run_dir,
                    runtime_files=(extension,),
                    runtime_directories=(dependencies,),
                )
                placeholders = create_placeholders(plan)
                command = bubblewrap_argv(plan, argv)
            except WorkerSandboxError as error:
                remove_untouched_placeholders(placeholders)
                raise WorkerExecutionError(
                    f"worker sandbox unavailable: {error}"
                ) from error
            server = (
                _HostToolServer(str(socket_path), checks, report_issue)
                if socket_path is not None
                else None
            )
            if server is not None:
                threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                run = run_prompt(
                    command,
                    cwd=launch.workspace,
                    env=env,
                    message=launch.message,
                    timeout=launch.timeout_seconds,
                    popen=cast(Any, self.popen),
                )
            except PiRpcTimeout as error:
                raise WorkerExecutionError(
                    str(error), outcome=LIMIT_EXHAUSTED, run=error.run
                ) from error
            except PiRpcCancelled as error:
                raise WorkerExecutionError(
                    str(error), outcome=CANCELLED, run=error.run
                ) from error
            except PiRpcError as error:
                raise WorkerExecutionError(
                    str(error), outcome=FAILED, run=error.run
                ) from error
            finally:
                if server is not None:
                    server.shutdown()
                    server.server_close()
                remove_untouched_placeholders(placeholders)
                _return_refreshed_auth(
                    agent_dir / "auth.json", credentials / "auth.json", issued_auth
                )
        submissions = [
            item for item in run.results_of("submit_result") if not item.get("isError")
        ]
        if len(submissions) != 1:
            raise WorkerExecutionError(
                f"worker {launch.worker} submitted {len(submissions)} results; exactly one is required",
                outcome=INVALID_COMPLETION,
                run=run,
            )
        value = (submissions[0].get("result") or {}).get("details")
        if not isinstance(value, dict):
            raise WorkerExecutionError(
                "the submitted result is not a JSON object",
                outcome=INVALID_COMPLETION,
                run=run,
            )
        return WorkerResult(value=value, run=run, usage=_usage(launch, run))
