"""Launch one Concorde worker as a Pi process in RPC mode and admit its structured result.

A worker launch names everything the process may use: its workspace, the files it may read and
write, its tool allowlist, the lightweight child agents it may delegate to, its model and thinking
level, its system prompt, its input message and the JSON schema of its result. The runtime turns
that into one private run directory:

- ``agent/``: the Pi configuration directory (``PI_CODING_AGENT_DIR``) with Concorde's settings,
  the developer's Pi credentials (``auth.json`` and custom ``models.json``) copied in, the child
  agent definitions and the pi-subagents configuration that bounds delegation to one level;
- ``policy.json`` and ``system-prompt.md``: what the Concorde worker extension enforces and injects;
- ``tmp/``: the process's temporary directory, so no worker state lands in the shared one;
- ``host.sock``: the host's check service, present only for a worker granted ``run_checks``.

The process starts with Pi's ambient discovery disabled (no sessions, context files, skills,
prompt templates, themes or discovered extensions) and loads only the Concorde worker extension and,
for a worker with children, pi-subagents. The result is the ``details`` of the worker's single
successful ``submit_result`` call; the caller validates it against its own typed contract.
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
from typing import Any, Callable, Literal, Mapping

from .harness import SAFE_ENVIRONMENT
from .pi_rpc import PiRpcCancelled, PiRpcError, PiRpcTimeout, PiRun, run_prompt

BUILTIN_TOOLS = frozenset({"read", "grep", "find", "ls", "edit", "write", "bash"})
CONCORDE_TOOLS = frozenset({"submit_result", "run_checks"})
DELEGATION_TOOL = "subagent"
THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max")

# Provider credentials Pi reads from the environment (Pi's providers documentation). They reach the
# Pi process so it can call its model; the worker extension unsets them before every shell command.
PROVIDER_CREDENTIALS = (
    "AI_GATEWAY_API_KEY", "ANTHROPIC_API_KEY", "ANT_LING_API_KEY", "AWS_BEARER_TOKEN_BEDROCK",
    "AZURE_OPENAI_API_KEY", "CEREBRAS_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_KEY",
    "CLOUDFLARE_GATEWAY_ID", "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY", "HF_TOKEN",
    "MISTRAL_API_KEY", "NVIDIA_API_KEY", "OPENAI_API_KEY", "OPENCODE_API_KEY", "OPENROUTER_API_KEY",
    "RADIUS_API_KEY", "XAI_API_KEY", "ZAI_API_KEY", "ZAI_CODING_CN_API_KEY",
)

PI_SETTINGS = {"defaultProjectTrust": "never", "quietStartup": True, "enableInstallTelemetry": False,
               "subagents": {"disableBuiltins": True}}
# One level of delegation, in the foreground, into fresh contexts, with every background, mission,
# schedule and inter-session channel feature of pi-subagents switched off.
SUBAGENT_CONFIG = {"maxSubagentDepth": 1, "asyncByDefault": False, "forceTopLevelAsync": False,
                   "defaultSubagentContext": "fresh", "missions": {"enabled": False},
                   "scheduledRuns": {"enabled": False}, "intercomBridge": {"mode": "off"},
                   "artifactDir": "temp"}

Outcome = Literal["failed", "cancelled", "limit_exhausted", "invalid_completion"]
# Execution outcomes classify why a run produced no result; they are not error codes.
FAILED: Outcome = "failed"
CANCELLED: Outcome = "cancelled"
LIMIT_EXHAUSTED: Outcome = "limit_exhausted"
INVALID_COMPLETION: Outcome = "invalid_completion"


class WorkerExecutionError(RuntimeError):
    """A worker launch was refused, failed, was cancelled, ran out of time or returned no result."""

    def __init__(self, message: str, outcome: Outcome = FAILED, run: PiRun | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.run = run


@dataclass(frozen=True)
class ChildAgent:
    """One lightweight child: a complete pi-subagents Markdown agent definition."""

    name: str
    definition: str


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
    children: tuple[ChildAgent, ...] = ()
    child_tools: tuple[str, ...] = ()
    model: str | None = None
    thinking: str | None = None
    timeout_seconds: float = 1800


@dataclass(frozen=True)
class WorkerResult:
    value: dict[str, Any]
    run: PiRun
    usage: dict[str, Any]


def validate_launch(launch: WorkerLaunch, *, has_checks: bool) -> None:
    known = BUILTIN_TOOLS | CONCORDE_TOOLS | {DELEGATION_TOOL}
    tools, child_tools = set(launch.tools), set(launch.child_tools)
    if len(tools) != len(launch.tools) or len(child_tools) != len(launch.child_tools):
        raise WorkerExecutionError("worker tool lists contain duplicates")
    if tools - known or child_tools - (BUILTIN_TOOLS | {"run_checks"}):
        raise WorkerExecutionError(f"unknown worker tools: {sorted((tools - known) | (child_tools - BUILTIN_TOOLS - {'run_checks'}))}")
    if "submit_result" not in tools:
        raise WorkerExecutionError("every worker must be granted submit_result")
    if (DELEGATION_TOOL in tools) != bool(launch.children):
        raise WorkerExecutionError("a worker is granted subagent exactly when it declares children")
    if bool(child_tools) != bool(launch.children):
        raise WorkerExecutionError("child tools are declared exactly when the worker declares children")
    if "run_checks" in tools | child_tools and not has_checks:
        raise WorkerExecutionError("run_checks requires a host check service")
    if {"edit", "write"} & tools and not launch.write_paths:
        raise WorkerExecutionError("edit and write require a write grant")
    names = [child.name for child in launch.children]
    if len(names) != len(set(names)) or any(
            not child.definition.startswith("---\n") or f"\nname: {child.name}\n" not in child.definition
            for child in launch.children):
        raise WorkerExecutionError("each child needs a unique name and a definition that declares it")
    if launch.thinking is not None and launch.thinking not in THINKING_LEVELS:
        raise WorkerExecutionError(f"unsupported thinking level: {launch.thinking}")
    if not Path(launch.workspace).is_absolute() or not Path(launch.workspace).is_dir():
        raise WorkerExecutionError("the worker workspace must be an existing absolute directory")
    if launch.timeout_seconds <= 0:
        raise WorkerExecutionError("the worker timeout must be positive")


class _CheckServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True

    def __init__(self, path: str, checks: Callable[[], Any]):
        self.checks = checks
        super().__init__(path, _CheckHandler)


class _CheckHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            request = json.loads(self.rfile.readline() or b"{}")
            if request.get("tool") != "run_checks":
                raise ValueError("unknown host tool")
            reply = self.server.checks()
        except Exception as error:  # the worker receives the failure as its tool result
            reply = {"error": f"{type(error).__name__}: {error}"}
        self.wfile.write(json.dumps(reply).encode("utf-8"))


def _usage(launch: WorkerLaunch, run: PiRun) -> dict[str, Any]:
    stats = run.stats or {}
    tokens = stats.get("tokens") if isinstance(stats.get("tokens"), dict) else {}

    def count(value):
        return value if type(value) is int and value >= 0 else None

    cost = stats.get("cost")
    return {"model": launch.model, "input_tokens": count(tokens.get("input")),
            "cached_input_tokens": count(tokens.get("cacheRead")), "output_tokens": count(tokens.get("output")),
            "total_tokens": count(tokens.get("total")),
            "cost_usd": float(cost) if type(cost) in (int, float) and cost >= 0 else None,
            "turns": count(stats.get("assistantMessages")), "wall_seconds": round(run.wall_seconds, 3)}


@dataclass(frozen=True)
class PiWorkerRuntime:
    """Runs worker launches; every injected field is trusted host configuration, never task input."""

    package_root: Path
    pi_executable: str | None = None
    environment: Mapping[str, str] | None = None
    credentials_dir: Path | None = None
    popen: Callable[..., Any] = subprocess.Popen

    def __call__(self, launch: WorkerLaunch, *, checks: Callable[[], Any] | None = None) -> WorkerResult:
        validate_launch(launch, has_checks=checks is not None)
        source = dict(os.environ if self.environment is None else self.environment)
        executable = self.pi_executable or shutil.which("pi", path=source.get("PATH"))
        if not executable:
            raise WorkerExecutionError("the pi executable is not on PATH")
        extension = (Path(self.package_root) / "pi/extensions/concorde-worker.ts").resolve()
        subagents = (Path(self.package_root) / "pi/node_modules/pi-subagents/index.ts").resolve()
        if not extension.is_file():
            raise WorkerExecutionError(f"the Concorde worker extension is missing: {extension}")
        if launch.children and not subagents.is_file():
            raise WorkerExecutionError("pi-subagents is not installed; run `npm ci --prefix pi` in the Concorde package")
        credentials = self.credentials_dir or Path(
            source.get("PI_CODING_AGENT_DIR") or Path(source.get("HOME", "~")).expanduser() / ".pi" / "agent")
        with tempfile.TemporaryDirectory(prefix="concorde-pi-worker-") as directory:
            run_dir = Path(directory)
            agent_dir, temporary = run_dir / "agent", run_dir / "tmp"
            (agent_dir / "agents").mkdir(parents=True)
            (agent_dir / "extensions" / "subagent").mkdir(parents=True)
            temporary.mkdir()
            for name in ("auth.json", "models.json"):
                if (credentials / name).is_file():
                    shutil.copyfile(credentials / name, agent_dir / name)
                    os.chmod(agent_dir / name, 0o600)
            (agent_dir / "settings.json").write_text(json.dumps(PI_SETTINGS), encoding="utf-8")
            (agent_dir / "extensions" / "subagent" / "config.json").write_text(json.dumps(SUBAGENT_CONFIG), encoding="utf-8")
            for child in launch.children:
                (agent_dir / "agents" / f"{child.name}.md").write_text(child.definition, encoding="utf-8")
            (run_dir / "system-prompt.md").write_text(launch.system_prompt, encoding="utf-8")
            socket_path = run_dir / "host.sock" if checks is not None else None
            policy = {"schema_version": 1, "worker": launch.worker, "workspace": launch.workspace,
                      "read_paths": list(launch.read_paths), "write_paths": list(launch.write_paths),
                      "tools": list(launch.tools), "child_tools": list(launch.child_tools),
                      "children": [child.name for child in launch.children],
                      "system_prompt_path": str(run_dir / "system-prompt.md"),
                      "result_schema": dict(launch.result_schema),
                      "host_socket": str(socket_path) if socket_path else None,
                      "extension_path": str(extension), "scrub_environment": list(PROVIDER_CREDENTIALS)}
            (run_dir / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
            env = {key: value for key, value in source.items()
                   if key in SAFE_ENVIRONMENT or key in PROVIDER_CREDENTIALS}
            env.update(PI_CODING_AGENT_DIR=str(agent_dir), CONCORDE_WORKER_POLICY=str(run_dir / "policy.json"),
                       PI_OFFLINE="1", PI_SKIP_VERSION_CHECK="1", PI_TELEMETRY="0",
                       TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary))
            argv = [executable, "--mode", "rpc", "--no-session", "--no-context-files", "--no-skills",
                    "--no-prompt-templates", "--no-themes", "--no-extensions", "-e", str(extension)]
            if launch.children:
                argv += ["-e", str(subagents)]
            argv += ["--no-approve", "--offline", "--tools", ",".join(launch.tools)]
            if launch.model:
                argv += ["--model", launch.model]
            if launch.thinking:
                argv += ["--thinking", launch.thinking]
            server = _CheckServer(str(socket_path), checks) if checks is not None else None
            if server is not None:
                threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                run = run_prompt(argv, cwd=launch.workspace, env=env, message=launch.message,
                                 timeout=launch.timeout_seconds, popen=self.popen)
            except PiRpcTimeout as error:
                raise WorkerExecutionError(str(error), outcome=LIMIT_EXHAUSTED) from error
            except PiRpcCancelled as error:
                raise WorkerExecutionError(str(error), outcome=CANCELLED) from error
            except PiRpcError as error:
                raise WorkerExecutionError(str(error), outcome=FAILED) from error
            finally:
                if server is not None:
                    server.shutdown()
                    server.server_close()
        submissions = [item for item in run.results_of("submit_result") if not item.get("isError")]
        if len(submissions) != 1:
            raise WorkerExecutionError(
                f"worker {launch.worker} submitted {len(submissions)} results; exactly one is required",
                outcome=INVALID_COMPLETION, run=run)
        value = (submissions[0].get("result") or {}).get("details")
        if not isinstance(value, dict):
            raise WorkerExecutionError("the submitted result is not a JSON object", outcome=INVALID_COMPLETION, run=run)
        return WorkerResult(value=value, run=run, usage=_usage(launch, run))
