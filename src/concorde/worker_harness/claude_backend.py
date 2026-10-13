"""The Claude Code worker backend: settings, write hook, ``claude -p`` and its event stream.

The host generates the worker settings (deny rules, write hook registration, Bash sandbox) and the
write hook from the frozen grant, launches ``claude -p`` with ``--output-format stream-json``, and
reads the stream as it arrives: each tool use updates the progress file, and the final ``result``
record gives the session, the structured output or Claude Code's own error.
"""

from __future__ import annotations

import ipaddress
import itertools
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from ..kernel.errors import link
from .settings import (
    TOOL_SETS,
    SettingsError,
    tool_set,
    worker_settings,
    write_hook_source,
)
from .transient import transient

ACTOR = "Claude Code process (claude -p)"
# The proxy a worker's own model calls go through: an enclosing loopback proxy, such as a
# developer's local model proxy or a sandboxed main agent's session, may be the process's only way
# out, and a developer's own proxy elsewhere applies to workers as to the host.
PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
NO_PROXY_VARIABLES = ("NO_PROXY", "no_proxy")
LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1", "[::1]"}
# What a round's content keeps of the result envelope, as Claude Code gave it: besides how the
# round ended and its turns and cost, the tool calls it refused under the worker settings
# (evidence for telling a refused worker's boundary case), each model's tokens and cost, and the
# time spent waiting for the model.
ENVELOPE_KEPT = (
    "subtype",
    "is_error",
    "num_turns",
    "total_cost_usd",
    "permission_denials",
    "modelUsage",
    "duration_api_ms",
)
# From this version on, Claude Code restores a resumed session's saved totals, so the cost a resumed
# round's envelope reports holds the session's earlier spend too.
RESTORES_TOTALS = (2, 1, 277)


class BackendRefusal(Exception):
    """A backend cannot prepare the run; the run ends ``failed`` before launch."""

    def __init__(self, code: str, detail: str, reason: str, explanation: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.reason = reason
        self.explanation = explanation


@dataclass(frozen=True)
class RoundLimits:
    """What a round may still use of its run's limits: turns, and dollars when the run has a
    budget (launch.md#limits)."""

    max_turns: int
    max_budget_usd: float | None


@dataclass
class RoundOutcome:
    """What one round's agent process reported, before the host judges it."""

    session: str | None = None
    result: dict | None = None
    final_text: str = ""
    failure: dict | None = None
    exhausted: bool = False
    # The error message of a transient model-service error that ended the round, which Workers
    # may retry (launch.md#retries); None for every other ending.
    transient: str | None = None
    info: dict = field(default_factory=dict)
    # What the round consumed as the agent program reported it: the usage fields of a trace node
    # (tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, cost_usd, turns).
    usage: dict = field(default_factory=dict)


def _count(value) -> int | None:
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else None
    )


def _amount(value) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return None


def restores_totals(version) -> bool:
    """Whether the Claude Code ``version`` the stream named restores a resumed session's totals."""
    if not isinstance(version, str):
        return False
    parts = []
    for part in version.strip().split(" ")[0].split("."):
        digits = "".join(itertools.takewhile(str.isdigit, part))
        if not digits:
            break
        parts.append(int(digits))
    return len(parts) >= 3 and tuple(parts[:3]) >= RESTORES_TOTALS


def _tail(data: bytes, size: int = 4000) -> str:
    return data[-size:].decode("utf-8", "replace").strip()


def claude_failure(outcome: dict, envelope: dict | None) -> dict | None:
    """A component link when the Claude Code process itself reported an error, else ``None``."""
    if envelope is None:
        return link(
            "component",
            ACTOR,
            "no_result_envelope",
            f"the process exited with code {outcome.get('exit')} and printed no JSON result "
            f"envelope; standard output ends with: {_tail(outcome['stdout']) or '(empty)'}; "
            f"standard error ends with: {_tail(outcome['stderr']) or '(empty)'}",
            reason="environment",
            explanation="the process ended without a result; it cannot report more",
        )
    subtype = str(envelope.get("subtype") or "success")
    if subtype == "success" and not envelope.get("is_error"):
        return None
    text = envelope.get("result")
    detail = (
        f"the result envelope has subtype {subtype}, is_error {bool(envelope.get('is_error'))}, "
        f"{envelope.get('num_turns', '?')} turn(s), cost {envelope.get('total_cost_usd', '?')} "
        f"USD, exit code {outcome.get('exit')}"
    )
    if isinstance(text, str) and text.strip():
        detail += f"; its final text: {text.strip()[-2000:]}"
    if envelope.get("errors"):
        detail += f"; errors: {json.dumps(envelope['errors'])[-2000:]}"
    stderr = _tail(outcome["stderr"], 2000)
    if stderr:
        detail += f"; standard error ends with: {stderr}"
    exhausted = subtype in ("error_max_turns", "error_max_budget_usd")
    return link(
        "component",
        ACTOR,
        "claude_" + "".join(c if c.isalnum() else "_" for c in subtype.lower()),
        detail,
        reason="exhausted" if exhausted else "environment",
        explanation=(
            "the session reached the turn or budget limit it was started with"
            if exhausted
            else "Claude Code reported an error of the model service or its own execution"
        ),
    )


def service_error(envelope: dict) -> str | None:
    """The model service's error a failed envelope reports: Claude Code's final text when it is an
    `API Error`, and the errors it lists."""
    parts = []
    text = envelope.get("result")
    if isinstance(text, str) and text.strip().startswith("API Error"):
        parts.append(text.strip())
    errors = envelope.get("errors")
    if isinstance(errors, list):
        parts += [
            item if isinstance(item, str) else json.dumps(item) for item in errors
        ]
    return "; ".join(parts)[-2000:] or None


def envelope_of(stdout: bytes) -> dict | None:
    """The last ``result`` record of the stream, or a single JSON envelope."""
    text = stdout.decode("utf-8", "replace").strip()
    for line in reversed(text.splitlines() or [""]):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and value.get("type") == "result":
            return value
    try:
        value = json.loads(text)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _on_loopback(proxy: str) -> bool:
    """Whether a proxy variable's value names a proxy on the loopback interface."""
    try:
        host = urlsplit(proxy if "://" in proxy else f"http://{proxy}").hostname
    except ValueError:
        return False
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def proxy_environment(host: dict[str, str] | None = None) -> dict[str, str]:
    """The proxy variables a worker inherits from the host's environment.

    Every set ``HTTP_PROXY``/``HTTPS_PROXY`` in either case passes on, and with one the
    ``NO_PROXY``/``no_proxy`` values. When every passed proxy is on loopback, as a sandboxed main
    agent's session proxy is, loopback leaves the no-proxy lists: the process's network namespace
    may hold nothing but that proxy, so ``localhost`` is reachable only through it. Without a proxy
    nothing passes on.
    """
    host = os.environ if host is None else host
    proxies = {name: host[name] for name in PROXY_VARIABLES if host.get(name)}
    if not proxies:
        return {}
    environment = dict(proxies)
    loopback = all(_on_loopback(value) for value in proxies.values())
    for name in NO_PROXY_VARIABLES:
        if name not in host:
            continue
        entries = [entry.strip() for entry in host[name].split(",")]
        if loopback:
            entries = [e for e in entries if e.lower() not in LOOPBACK_NAMES]
        kept = ",".join(entry for entry in entries if entry)
        if kept:
            environment[name] = kept
    return environment


class ClaudeStream:
    """Reads one round's ``stream-json`` output.

    ``totals`` maps each session of the run to the cost the latest envelope of that session
    reported, which the stream updates; ``resumed`` is the session the round resumes, if any."""

    def __init__(self, totals: dict | None = None, resumed: str | None = None):
        # The session the output named so far, such as in its first ``system`` record, before
        # the round's envelope confirms it.
        self.session: str | None = None
        self.totals = {} if totals is None else totals
        self.resumed = resumed
        # The Claude Code version the stream's init record named.
        self.version: str | None = None

    def feed(self, line: str) -> list[tuple[str, dict]]:
        """The tool uses this line reports, as ``(tool, input)`` pairs."""
        try:
            record = json.loads(line)
        except ValueError:
            return []
        if not isinstance(record, dict):
            return []
        if isinstance(record.get("session_id"), str) and record["session_id"]:
            self.session = record["session_id"]
        if record.get("type") == "system" and record.get("subtype") == "init":
            version = record.get("claude_code_version")
            self.version = version if isinstance(version, str) else None
        if record.get("type") != "assistant":
            return []
        content = (record.get("message") or {}).get("content")
        if not isinstance(content, list):
            return []
        return [
            (str(block.get("name")), block.get("input") or {})
            for block in content
            if isinstance(block, dict) and block.get("type") == "tool_use"
        ]

    def conclude(self, outcome: dict) -> RoundOutcome:
        envelope = envelope_of(outcome["stdout"])
        concluded = RoundOutcome()
        if envelope:
            concluded.session = envelope.get("session_id")
            concluded.info = {
                "claude": {
                    **{key: envelope.get(key) for key in ENVELOPE_KEPT},
                    "claude_code_version": self.version,
                }
            }
            used = (
                envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
            )
            concluded.usage = {
                "tokens_in": _count(used.get("input_tokens")),
                "tokens_out": _count(used.get("output_tokens")),
                "tokens_cache_read": _count(used.get("cache_read_input_tokens")),
                "tokens_cache_write": _count(used.get("cache_creation_input_tokens")),
                "cost_usd": self._own_cost(_amount(envelope.get("total_cost_usd"))),
                "turns": _count(envelope.get("num_turns")),
            }
            concluded.result = envelope.get("structured_output")
            concluded.final_text = str(envelope.get("result") or "").strip()
        # A round that ended without its envelope, such as one killed at its deadline, still
        # names the session its output announced last.
        concluded.session = concluded.session or self.session
        reported = _amount(envelope.get("total_cost_usd")) if envelope else None
        if concluded.session and reported is not None:
            self.totals[concluded.session] = reported
        concluded.failure = claude_failure(outcome, envelope)
        concluded.exhausted = bool(
            concluded.failure
            and concluded.failure["unhandled"]["reason"] == "exhausted"
        )
        if envelope and concluded.failure and not concluded.exhausted:
            message = service_error(envelope)
            if transient(message):
                concluded.transient = message
        return concluded

    def _own_cost(self, reported: float | None) -> float | None:
        """The round's own cost: the cost its envelope reported, less the total the session's
        earlier round reported when this Claude Code restored it on resume (launch.md#limits).
        A reported cost below that total was not restored and counts whole."""
        earlier = self.totals.get(self.resumed) if self.resumed else None
        if (
            reported is None
            or earlier is None
            or reported < earlier
            or not restores_totals(self.version)
        ):
            return reported
        return round(reported - earlier, 10)


class ClaudeBackend:
    name = "claude"
    failure_code = "claude_failed"
    process = "Claude Code"
    missing_command = "Workers cannot install or repair the claude command; set CONCORDE_CLAUDE or PATH"

    def __init__(self):
        # The cost the latest envelope of each session of the run reported.
        self.totals: dict[str, float] = {}

    def tools(self, task_type: str, grant: dict | None = None) -> str:
        return tool_set(TOOL_SETS, task_type, grant)

    def executable(self, request) -> str:
        return request.claude or os.environ.get("CONCORDE_CLAUDE") or "claude"

    def prepare(
        self, request, worktree: Path, paths, schema: dict, placement=None
    ) -> Path:
        """Write the settings and the write hook; return the file whose digest the record keeps."""
        try:
            settings = worker_settings(
                worktree,
                request.grant,
                paths,
                python=sys.executable,
                runtime=request.runtime,
                home=request.home,
                primary=placement.primary if placement else None,
                git=placement.git if placement else (),
            )
        except SettingsError as error:
            raise BackendRefusal(
                error.code,
                f"the worker settings cannot be generated: {error}",
                "environment",
                "the settings follow from the grant and the file layout, which Workers cannot "
                "change",
            ) from error
        settings_file = paths.control / "settings.json"
        settings_file.write_text(json.dumps(settings, indent=2, sort_keys=True))
        (paths.control / "write_hook.py").write_text(
            write_hook_source(worktree, request.grant)
        )
        credentials = self._credentials(request)
        if credentials is not None:
            shutil.copy2(credentials, paths.config / ".credentials.json")
            os.chmod(paths.config / ".credentials.json", 0o600)
        return settings_file

    def _credentials(self, request) -> Path | None:
        if request.credentials is not None:
            return request.credentials
        base = os.environ.get("CLAUDE_CONFIG_DIR")
        candidate = (
            Path(base) if base else Path.home() / ".claude"
        ) / ".credentials.json"
        return candidate if candidate.is_file() else None

    def environment(self, request, paths) -> dict[str, str]:
        environment = {
            "PATH": (
                f"{Path(request.project_python).parent}{os.pathsep}"
                if request.project_python
                else ""
            )
            + os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "HOME": paths.home.as_posix(),
            "TMPDIR": paths.tmp.as_posix(),
            "CLAUDE_CONFIG_DIR": paths.config.as_posix(),
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        }
        if os.environ.get("ANTHROPIC_API_KEY"):
            environment["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
        environment.update(proxy_environment())
        return environment

    def command(
        self, request, paths, schema_text: str, session: str | None, limits: RoundLimits
    ) -> list[str]:
        command = [
            self.executable(request),
            "-p",
            "--settings",
            (paths.control / "settings.json").as_posix(),
            "--tools",
            self.tools(request.task_type, request.grant),
            "--json-schema",
            schema_text,
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "bypassPermissions",
            "--allow-dangerously-skip-permissions",
            "--strict-mcp-config",
            "--max-turns",
            str(limits.max_turns),
        ]
        if limits.max_budget_usd is not None:
            command += ["--max-budget-usd", f"{limits.max_budget_usd:.2f}"]
        if request.local_model:
            command += ["--model", request.local_model]
        if request.reasoning:
            command += ["--effort", request.reasoning]
        if session:
            command += ["--resume", session]
        return command

    def round_environment(self, limits: RoundLimits) -> dict[str, str]:
        """The round's own variables: none, since the command line carries its limits."""
        return {}

    def stream(self, session: str | None = None) -> ClaudeStream:
        return ClaudeStream(self.totals, session)

    def transcript(self, paths, session: str | None) -> str | None:
        if not session:
            return None
        found = sorted((paths.config / "projects").glob(f"*/{session}.jsonl"))
        return found[0].as_posix() if found else None


__all__ = [
    "ACTOR",
    "BackendRefusal",
    "ClaudeBackend",
    "ClaudeStream",
    "RoundLimits",
    "RoundOutcome",
    "claude_failure",
    "envelope_of",
]
