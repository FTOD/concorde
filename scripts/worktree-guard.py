#!/usr/bin/env python3
"""Refuse native worktree creation inside agent sessions of Concorde's own source checkout.

Concorde's project-local Skills are worktree-owned build output (see AGENTS.md). A session that
loaded them in one worktree must not create, move or enter another worktree; the only supported
way to obtain a worktree is a Concorde capability, whose host creates the candidate worktree and
hands off a fresh session under Framework profile P10. This script is the command hook that the
checkout registers in ``.claude/settings.json`` (Claude Code ``PreToolUse`` and ``WorktreeCreate``)
and ``.codex/hooks.json`` (Codex ``PreToolUse``). It reads one hook payload from stdin and either
stays silent (allow) or refuses with a reason.

Decisions:

* ``WorktreeCreate`` (Claude Code): always refused, so ``claude --worktree``, subagents with
  ``isolation: "worktree"`` and background-session worktrees never materialise.
* ``PreToolUse`` for ``EnterWorktree``: refused.
* ``PreToolUse`` for ``Agent``/``Task`` with ``isolation: "worktree"``: refused; other isolation
  values are not worktrees of this checkout and pass.
* ``PreToolUse`` for shell tools: refused when the command text contains ``git … worktree add``
  or ``git … worktree move`` (global git options such as ``-C`` or ``--git-dir=`` included), or a
  ``claude`` launch with ``--worktree``/``-w``. The whole command text is inspected, including
  quoted strings and here-documents, so a file that must mention these commands is written with
  the editor tool rather than a shell here-document.
* Everything else is allowed silently.

A refusal prints a ``permissionDecision: deny`` object on stdout, the reason on stderr and exits
2, which Claude Code and Codex both treat as a block. Unreadable input exits 1: a visible,
non-blocking hook error rather than a blanket refusal of every tool call.

This guards the developer's own session and its native subagents; it is not a sandbox. A command
that only computes ``git worktree add`` at runtime is outside its reach, and Concorde's host, which
runs its own workers with project settings ignored, is unaffected. Consumer projects never receive
this hook: the installer does not ship this script or the integration files that register it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Mapping, NamedTuple

REASON = (
    "Concorde source checkout: agent sessions may not create, move or enter git worktrees. "
    "Concorde Skills are worktree-owned build output, so this session stays in the worktree that "
    "supplied its Skills. To work on a change in its own worktree, invoke a Concorde capability "
    "(for example concorde-dev-loop): its host creates the candidate worktree and hands off a "
    "fresh session under P10. Details: python3 scripts/worktree-guard.py --explain"
)

EXPLANATION = """Concorde source-checkout worktree guard

Why: `.claude/skills/concorde-*` and `.agents/skills/concorde-*` are untracked build output owned
by the worktree that built them. A session that loaded those Skills in worktree A and then
created or entered worktree B would keep A's instructions while acting on B, whose Skills may
differ. Concorde's host avoids this by creating candidate worktrees itself and handing off a fresh
session there (Framework profile P10), so native worktree creation is refused in developer
sessions of this checkout.

Refused: the Claude Code EnterWorktree tool, subagents with isolation "worktree", Claude Code
worktree creation (`claude --worktree`, background-session worktrees), and shell commands that
run `git worktree add`, `git worktree move` or `claude --worktree` / `claude -w`.

Allowed: everything else, including `git worktree list`, starting a session in an existing
host-created worktree, and Concorde capabilities, whose host creates worktrees in its own process.

Registered in: .claude/settings.json (permissions.deny, hooks PreToolUse and WorktreeCreate) and
.codex/hooks.json (PreToolUse) plus .codex/rules/worktree.rules (execpolicy). Codex loads the
project `.codex/` layer only for a trusted project and runs a project hook only after it was
reviewed once with `/hooks`; the execpolicy rules need no separate review.

Not installed for consumer projects: this is repository policy for developing Concorde itself.
"""

SHELL_TOOLS = frozenset({"bash", "powershell", "shell", "execcommand", "unifiedexec", "localshell"})
SUBAGENT_TOOLS = frozenset({"agent", "task"})

# One global git option, e.g. -C <path>, -c key=value, --git-dir=<path>, --git-dir <path>,
# --no-pager. A separate value never starts with "-" and is never the word "worktree".
_GIT_OPTION = r"-(?:-?[\w-]+)(?:=\S*|\s+(?!worktree(?![\w-]))(?:\"[^\"]*\"|'[^']*'|[^\s-]\S*))?"
GIT_WORKTREE = re.compile(
    rf"(?<![\w-])git(?:\s+{_GIT_OPTION})*\s+worktree(?:\s+-\S*)*\s+(?:add|move)(?![\w-])"
)
CLAUDE_WORKTREE = re.compile(r"(?<![\w-])claude(?![\w-])(?:\s+\S+)*?\s+(?:--worktree|-w)(?=[\s=]|$)")


class Verdict(NamedTuple):
    blocked: bool
    kind: str = ""
    reason: str = ""


ALLOW = Verdict(False)


def _normalise(value: Any) -> str:
    return re.sub(r"[\s_.-]", "", value).lower() if isinstance(value, str) else ""


def _command_text(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, Mapping):
        return ""
    for key in ("command", "cmd", "script", "argv"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return " ".join(str(item) for item in value)
    return ""


def evaluate_command(command: str) -> Verdict:
    """Decide one shell command text as a shell tool would submit it."""

    if GIT_WORKTREE.search(command):
        return Verdict(True, "git-worktree", REASON)
    if CLAUDE_WORKTREE.search(command):
        return Verdict(True, "claude-worktree", REASON)
    return ALLOW


def evaluate(payload: Mapping[str, Any]) -> Verdict:
    """Decide one Claude Code or Codex hook payload."""

    event = _normalise(payload.get("hook_event_name"))
    if event == "worktreecreate":
        return Verdict(True, "worktree-create", REASON)
    if event != "pretooluse":
        return ALLOW
    tool = _normalise(payload.get("tool_name"))
    tool_input = payload.get("tool_input")
    if tool == "enterworktree":
        return Verdict(True, "enter-worktree", REASON)
    if tool in SUBAGENT_TOOLS:
        isolation = tool_input.get("isolation") if isinstance(tool_input, Mapping) else None
        if _normalise(isolation) == "worktree":
            return Verdict(True, "isolated-subagent", REASON)
        return ALLOW
    if tool in SHELL_TOOLS:
        return evaluate_command(_command_text(tool_input))
    return ALLOW


def _deny_output(payload: Mapping[str, Any], verdict: Verdict) -> None:
    if _normalise(payload.get("hook_event_name")) == "pretooluse":
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": verdict.reason,
            }
        }
        sys.stdout.write(json.dumps(decision) + "\n")
        sys.stdout.flush()
    sys.stderr.write(verdict.reason + "\n")
    sys.stderr.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="worktree-guard",
        description="Concorde source-checkout hook: refuse native worktree creation in agent sessions.",
    )
    parser.add_argument("--explain", action="store_true", help="print the policy and exit")
    parser.add_argument("--check", metavar="COMMAND", help="decide one shell command text instead of a hook payload")
    arguments = parser.parse_args(argv)
    if arguments.explain:
        sys.stdout.write(EXPLANATION)
        return 0
    if arguments.check is not None:
        verdict = evaluate_command(arguments.check)
        sys.stdout.write(f"deny ({verdict.kind}): {verdict.reason}\n" if verdict.blocked else "allow\n")
        return 2 if verdict.blocked else 0
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError as error:
        sys.stderr.write(f"worktree-guard: hook input is not JSON ({error})\n")
        return 1
    if not isinstance(payload, dict):
        sys.stderr.write("worktree-guard: hook input is not a JSON object\n")
        return 1
    verdict = evaluate(payload)
    if not verdict.blocked:
        return 0
    _deny_output(payload, verdict)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
