"""The Claude Code worker backend: settings, write hook, ``claude -p`` and its event stream.

The host generates the worker settings (deny rules, write hook registration, Bash sandbox) and the
write hook from the frozen grant, launches ``claude -p`` with ``--output-format stream-json``, and
reads the stream as it arrives: each tool use updates the progress file, and the final ``result``
record gives the session, the structured output or Claude Code's own error.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import link
from .settings import TOOL_SETS, SettingsError, worker_settings, write_hook_source

ACTOR = "Claude Code process (claude -p)"


class BackendRefusal(Exception):
    """A backend cannot prepare the run; the run ends ``failed`` before launch."""

    def __init__(self, code: str, detail: str, reason: str, explanation: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.reason = reason
        self.explanation = explanation


@dataclass
class RoundOutcome:
    """What one round's agent process reported, before the host judges it."""

    session: str | None = None
    result: dict | None = None
    final_text: str = ""
    failure: dict | None = None
    exhausted: bool = False
    info: dict = field(default_factory=dict)


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


class ClaudeStream:
    """Reads one round's ``stream-json`` output."""

    def feed(self, line: str) -> list[tuple[str, dict]]:
        """The tool uses this line reports, as ``(tool, input)`` pairs."""
        try:
            record = json.loads(line)
        except ValueError:
            return []
        if not isinstance(record, dict) or record.get("type") != "assistant":
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
                    key: envelope.get(key)
                    for key in ("subtype", "is_error", "num_turns", "total_cost_usd")
                }
            }
            concluded.result = envelope.get("structured_output")
            concluded.final_text = str(envelope.get("result") or "").strip()
        concluded.failure = claude_failure(outcome, envelope)
        concluded.exhausted = bool(
            concluded.failure
            and concluded.failure["unhandled"]["reason"] == "exhausted"
        )
        return concluded


class ClaudeBackend:
    name = "claude"
    failure_code = "claude_failed"
    process = "Claude Code"
    missing_command = "Workers cannot install or repair the claude command; set CONCORDE_CLAUDE or PATH"

    def tools(self, task_type: str) -> str:
        return TOOL_SETS[task_type]

    def executable(self, request) -> str:
        return request.claude or os.environ.get("CONCORDE_CLAUDE") or "claude"

    def prepare(self, request, worktree: Path, paths, schema: dict) -> Path:
        """Write the settings and the write hook; return the file whose digest the record keeps."""
        try:
            settings = worker_settings(
                worktree,
                request.grant,
                paths,
                python=sys.executable,
                runtime=request.runtime,
                home=request.home,
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
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
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
        return environment

    def command(
        self, request, paths, schema_text: str, session: str | None
    ) -> list[str]:
        command = [
            self.executable(request),
            "-p",
            "--settings",
            (paths.control / "settings.json").as_posix(),
            "--tools",
            TOOL_SETS[request.task_type],
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
            str(request.max_turns),
        ]
        if request.max_budget_usd is not None:
            command += ["--max-budget-usd", str(request.max_budget_usd)]
        if request.model:
            command += ["--model", request.model]
        if session:
            command += ["--resume", session]
        return command

    def stream(self) -> ClaudeStream:
        return ClaudeStream()

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
    "RoundOutcome",
    "claude_failure",
    "envelope_of",
]
