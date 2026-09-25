"""The pi worker backend: the permission extension, ``pi -p`` and its JSON event stream.

The host checks the prerequisites (``pi``, ``rg``, ``fd``, the sandbox-runtime package and, on
Linux, ``bwrap`` and ``socat``), gives the worker its own ``PI_CODING_AGENT_DIR`` with copies of
the user's pi credentials and model definitions, and generates the permission extension from the
frozen grant: ``pi_permission.ts`` with the run's policy embedded, beside ``pi_policy.ts`` with the
pure path decisions. It launches ``pi -p --mode json`` with every other resource disabled and
reads the event stream as it arrives: tool executions update the progress file, the last
successful ``concorde_result`` is the worker result, and a ``concorde-limit`` entry means the
extension stopped the run at a limit.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
from pathlib import Path

from ..errors import link
from .claude_backend import BackendRefusal, RoundOutcome
from .settings import GrantView, sandbox_filesystem

ACTOR = "pi process (pi -p)"
HERE = Path(__file__).resolve().parent
EXTENSION_SOURCE = HERE / "pi_permission.ts"
POLICY_SOURCE = HERE / "pi_policy.ts"
POLICY_MARKER = "const POLICY: Policy = {} as Policy;"
RUNTIME_MARKER = '"@concorde/sandbox-runtime"'
RUNTIME_PACKAGE = "node_modules/@anthropic-ai/sandbox-runtime"
RUNTIME_VERSION = "0.0.77"
RESULT_TOOL = "concorde_result"
LIMIT_ENTRY = "concorde-limit"

COMMON_TOOLS = "read,grep,find,ls"
TOOL_SETS = {
    "understand": f"{COMMON_TOOLS},{RESULT_TOOL}",
    "review-spec": f"{COMMON_TOOLS},{RESULT_TOOL}",
    "review-code": f"{COMMON_TOOLS},{RESULT_TOOL}",
    "test": f"{COMMON_TOOLS},{RESULT_TOOL}",
    "specify": f"{COMMON_TOOLS},edit,write,{RESULT_TOOL}",
    "code-to-spec": f"{COMMON_TOOLS},edit,write,{RESULT_TOOL}",
    "implement": f"{COMMON_TOOLS},edit,write,bash,{RESULT_TOOL}",
}


def _tail(data: bytes, size: int = 4000) -> str:
    return data[-size:].decode("utf-8", "replace").strip()


def sandbox_runtime(request, worktree: Path) -> Path:
    """Where the sandbox-runtime package is expected for this run."""
    if request.sandbox_runtime is not None:
        return Path(request.sandbox_runtime)
    if os.environ.get("CONCORDE_SANDBOX_RUNTIME"):
        return Path(os.environ["CONCORDE_SANDBOX_RUNTIME"])
    from .runs import primary_root

    return primary_root(worktree) / ".concorde/tools/pi-runtime" / RUNTIME_PACKAGE


def which(name: str) -> str | None:
    return shutil.which(name)


def _program(name: str, *alternatives: str) -> str | None:
    for candidate in (name, *alternatives):
        found = which(candidate)
        if found:
            return found
    return None


def prerequisites(request, worktree: Path) -> tuple[dict, list[str]]:
    """The programs a pi run needs, and a description of each one that is missing."""
    missing = []
    pi = request.pi or os.environ.get("CONCORDE_PI") or "pi"
    pi_path = pi if os.path.isabs(pi) and os.access(pi, os.X_OK) else which(pi)
    if not pi_path:
        missing.append(
            f"the pi command {pi!r} is not on PATH; install pi (npm install -g "
            "@earendil-works/pi-coding-agent) or set CONCORDE_PI to its path"
        )
    programs = {
        "pi": pi_path or pi,
        "rg": _program("rg"),
        "fd": _program("fd", "fdfind"),
    }
    if not programs["rg"]:
        missing.append(
            "ripgrep (rg) is not on PATH; install it with your package manager"
        )
    if not programs["fd"]:
        missing.append(
            "fd (also found as fdfind) is not on PATH; install it with your package manager"
        )
    if platform.system() == "Linux":
        for name in ("bwrap", "socat"):
            if not which(name):
                missing.append(
                    f"{name} is not on PATH; the sandbox needs it on Linux; install it with "
                    "your package manager"
                )
    package = sandbox_runtime(request, worktree)
    entry = package / "dist/index.js"
    if not entry.is_file():
        prefix = package.parent.parent.parent
        missing.append(
            f"the sandbox-runtime package is missing at {package} (no dist/index.js); install "
            f"it with `npm install --prefix {prefix} "
            f"@anthropic-ai/sandbox-runtime@{RUNTIME_VERSION}`, or set "
            "CONCORDE_SANDBOX_RUNTIME to an installed @anthropic-ai/sandbox-runtime directory"
        )
    programs["sandbox_runtime"] = package.as_posix()
    return programs, missing


def policy(
    request, worktree: Path, paths, programs: dict, user_home: Path, schema: dict
) -> dict:
    """The permission extension's policy: every path absolute, lists from the frozen grant."""
    view = GrantView(request.grant["entries"])
    package = Path(programs["sandbox_runtime"])
    filesystem = sandbox_filesystem(
        worktree, request.grant, paths, request.runtime, user_home
    )
    filesystem["allowRead"] = sorted(
        set(filesystem["allowRead"]) | {(package / "vendor").as_posix()}
    )
    return {
        "worktree": worktree.as_posix(),
        "rw": view.paths("rw"),
        "ro": view.paths("ro"),
        "names": view.paths("names"),
        "hidden": [paths.control.as_posix(), paths.config.as_posix()],
        "own": [directory.as_posix() for directory in paths.own()],
        "runtime": [
            Path(os.path.realpath(path)).as_posix() for path in request.runtime
        ],
        "userHome": user_home.as_posix(),
        "sandbox": filesystem,
        "programs": {"rg": programs["rg"], "fd": programs["fd"]},
        "limits": {
            "maxTurns": request.max_turns,
            "maxBudgetUsd": request.max_budget_usd,
        },
        "resultSchema": schema,
    }


def extension_source(policy_value: dict, runtime_package: Path) -> str:
    """``pi_permission.ts`` with the policy and the sandbox-runtime entry point embedded."""
    source = EXTENSION_SOURCE.read_text(encoding="utf-8")
    if POLICY_MARKER not in source or RUNTIME_MARKER not in source:
        raise ValueError(f"{EXTENSION_SOURCE} lacks the policy or runtime marker")
    source = source.replace(
        POLICY_MARKER,
        "const POLICY: Policy = " + json.dumps(policy_value, sort_keys=True) + ";",
        1,
    )
    return source.replace(
        RUNTIME_MARKER, json.dumps((runtime_package / "dist/index.js").as_posix()), 1
    )


class PiStream:
    """Reads one round's JSON event stream."""

    def __init__(self):
        self.session: str | None = None
        self.result: dict | None = None
        self.limit: dict | None = None
        self.stop_reason: str | None = None
        self.error_message: str | None = None
        self.final_text = ""
        self.turns = 0
        self.cost = 0.0

    def feed(self, line: str) -> list[tuple[str, dict]]:
        try:
            record = json.loads(line)
        except ValueError:
            return []
        if not isinstance(record, dict):
            return []
        kind = record.get("type")
        if kind == "session":
            self.session = record.get("id") or self.session
        elif kind == "tool_execution_start":
            return [(str(record.get("toolName")), record.get("args") or {})]
        elif kind == "tool_execution_end":
            if record.get("toolName") == RESULT_TOOL and not record.get("isError"):
                details = (record.get("result") or {}).get("details")
                self.result = details if isinstance(details, dict) else None
        elif kind == "turn_end":
            self.turns += 1
        elif kind == "message_end":
            message = record.get("message") or {}
            if message.get("role") == "assistant":
                self.stop_reason = message.get("stopReason")
                self.error_message = message.get("errorMessage")
                cost = ((message.get("usage") or {}).get("cost") or {}).get("total")
                if isinstance(cost, (int, float)):
                    self.cost += cost
                texts = [
                    block.get("text", "")
                    for block in message.get("content") or []
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if any(text.strip() for text in texts):
                    self.final_text = "\n".join(texts).strip()
        elif kind == "entry_appended":
            entry = record.get("entry") or {}
            if entry.get("customType") == LIMIT_ENTRY:
                self.limit = entry.get("data") or {}
        return []

    def conclude(self, outcome: dict) -> RoundOutcome:
        concluded = RoundOutcome(
            session=self.session,
            result=self.result,
            final_text=self.final_text,
            info={
                "pi": {
                    "stop_reason": self.stop_reason,
                    "turns": self.turns,
                    "cost": round(self.cost, 6),
                }
            },
        )
        summary = (
            f"exit code {outcome.get('exit')}, {self.turns} turn(s), reported cost "
            f"{round(self.cost, 6)}, last stop reason {self.stop_reason or '(none)'}"
        )
        if self.error_message:
            summary += f", error message: {self.error_message[-2000:]}"
        stderr = _tail(outcome["stderr"], 2000)
        if stderr:
            summary += f"; standard error ends with: {stderr}"
        if self.limit is not None:
            concluded.exhausted = True
            concluded.failure = link(
                "component",
                ACTOR,
                "pi_limit_reached",
                f"the permission extension stopped the run at its {self.limit.get('limit')} "
                f"limit ({self.limit.get('value')} reached, at most "
                f"{self.limit.get('maximum')} allowed); {summary}",
                reason="exhausted",
                explanation="the run reached a limit it was started with",
            )
        elif self.result is None and (
            outcome.get("exit") != 0
            or self.session is None
            or self.stop_reason in ("error", "aborted")
        ):
            concluded.failure = link(
                "component",
                ACTOR,
                "pi_error",
                f"pi ended without a worker result: {summary}"
                + (
                    ""
                    if self.session
                    else f"; it printed no session record; standard output ends with: "
                    f"{_tail(outcome['stdout']) or '(empty)'}"
                ),
                reason="environment",
                explanation="pi reported an error of the model service or its own execution",
            )
        return concluded


class PiBackend:
    name = "pi"
    failure_code = "pi_failed"
    process = "pi"
    missing_command = (
        "Workers cannot install or repair the pi command; set CONCORDE_PI or PATH"
    )

    def __init__(self):
        self.programs: dict = {}

    def tools(self, task_type: str) -> str:
        return TOOL_SETS[task_type]

    def prepare(self, request, worktree: Path, paths, schema: dict) -> Path:
        programs, missing = prerequisites(request, worktree)
        if missing:
            raise BackendRefusal(
                "pi_runtime_missing",
                f"the pi backend cannot start on this machine: {'; '.join(missing)}",
                "environment",
                "Workers does not install programs; the machine running the host must provide "
                "them",
            )
        self.programs = programs
        self._configure(request, paths)
        user_home = Path(os.path.realpath(request.home or Path.home()))
        value = policy(request, worktree, paths, programs, user_home, schema)
        shutil.copy2(POLICY_SOURCE, paths.control / "pi_policy.ts")
        extension = paths.control / "permission.ts"
        extension.write_text(
            extension_source(value, Path(programs["sandbox_runtime"])), encoding="utf-8"
        )
        return extension

    def _configure(self, request, paths) -> None:
        """The worker's ``PI_CODING_AGENT_DIR``: credentials, model definitions, no packages."""
        source = request.pi_config
        if source is None:
            configured = os.environ.get("PI_CODING_AGENT_DIR")
            source = Path(configured) if configured else Path.home() / ".pi/agent"
        for name in ("auth.json", "models.json"):
            original = Path(source) / name
            if original.is_file():
                shutil.copy2(original, paths.config / name)
                os.chmod(paths.config / name, 0o600)
        (paths.config / "settings.json").write_text(
            json.dumps({"defaultProjectTrust": "never"}) + "\n"
        )
        (paths.config / "sessions").mkdir(exist_ok=True)

    def environment(self, request, paths) -> dict[str, str]:
        environment = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "HOME": paths.home.as_posix(),
            "TMPDIR": paths.tmp.as_posix(),
            "PI_CODING_AGENT_DIR": paths.config.as_posix(),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
        }
        for name, value in os.environ.items():
            if name.endswith("_API_KEY") and value:
                environment[name] = value
        return environment

    def command(
        self, request, paths, schema_text: str, session: str | None
    ) -> list[str]:
        command = [
            self.programs.get("pi") or request.pi or "pi",
            "-p",
            "--mode",
            "json",
            "--no-extensions",
            "-e",
            (paths.control / "permission.ts").as_posix(),
            "--no-context-files",
            "--no-skills",
            "--no-prompt-templates",
            "--tools",
            TOOL_SETS[request.task_type],
            "--session-dir",
            (paths.config / "sessions").as_posix(),
            "--session-id",
            session or paths.root.name,
        ]
        if request.model:
            command += ["--model", request.model]
        if request.reasoning:
            command += ["--thinking", request.reasoning]
        return command

    def stream(self) -> PiStream:
        return PiStream()

    def transcript(self, paths, session: str | None) -> str | None:
        if not session:
            return None
        found = sorted((paths.config / "sessions").glob(f"*_{session}.jsonl"))
        return found[-1].as_posix() if found else None


__all__ = [
    "ACTOR",
    "LIMIT_ENTRY",
    "PiBackend",
    "PiStream",
    "RESULT_TOOL",
    "TOOL_SETS",
    "extension_source",
    "policy",
    "prerequisites",
]
