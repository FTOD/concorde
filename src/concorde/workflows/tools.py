"""The workflow part's tools of the project MCP server: ``workflow_step`` and ``workflow_report``.

``workflow_step`` runs the ``concorde workflow step`` of the worktree the session started in as a
child of the call's process, so a step's detached runner is a process of the server's rather than
of a relaying agent's turn or of one of the session's background commands, and lives until its run
ends. ``workflow_report`` reads a saved workflow result of a workspace folder; it builds none and
knows no task, so whoever knows a task's workspace folder passes it. Each tool answers a value or
raises ``ToolRefusal`` with an error link, which the server returns unchanged.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

from ..kernel import binding as binding_file
from ..kernel import errors
from ..kernel.refusal import KernelError
from ..kernel.tracing import layout
from .step import concorde_command

ACTOR = "Concorde project MCP server"
# The longest a workflow_step call waits for its run, so that the call returns within two minutes.
STEP_WAIT = 100
# What a workflow_step call adds to its wait before it gives up on the step command itself.
STEP_GRACE = 60


class ToolRefusal(Exception):
    """A tool call refused with an error link."""

    def __init__(self, link: dict):
        super().__init__(link["detail"])
        self.link = link


def own(tool: str, code: str, detail: str, *, reason="input", explanation, options=()):
    return ToolRefusal(
        errors.link(
            "component",
            f"{ACTOR} ({tool})",
            code,
            detail,
            reason=reason,
            explanation=explanation,
            options=list(options),
        )
    )


def _schema(properties: dict, required=()) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


TOOLS: dict[str, dict] = {
    "workflow_report": {
        "description": "A saved workflow result of a workspace: report `number`, or the "
        "latest. `folder` is the absolute workspace folder, such as `<task folder>/workspace` "
        "of a task `task_show` shows; without it, the folder the workspace binding of this "
        "session's worktree names.",
        "inputSchema": _schema(
            {
                "folder": {"type": "string", "minLength": 1},
                "number": {"type": "integer", "minimum": 1},
            }
        ),
    },
    "workflow_step": {
        "description": "Start or await one workflow step in the bound workspace this session "
        "started in, as a step agent relays it: runs that worktree's own `concorde workflow step "
        "--json <request> --wait <wait>` as a process of this server, so the run it starts "
        "outlives the relaying agent's turn, and returns the step outcome it printed. `request` "
        "is the step request as an object; `wait` is at most 100 seconds (default 100). Refused "
        "in a worktree without a workspace binding.",
        "inputSchema": _schema(
            {
                "request": {"type": "object"},
                "wait": {"type": "integer", "minimum": 0, "maximum": STEP_WAIT},
            },
            ["request"],
        ),
    },
}
# The tools whose calls may take long and are served on a thread of their own, so the session's
# other calls are answered meanwhile.
THREADED = frozenset({"workflow_step"})


def concorde_of(worktree: Path) -> tuple[list[str], dict]:
    """The worktree's own ``concorde`` command line and the environment to run it with: its
    installed command, or its checkout's script, or else this package itself."""
    command = concorde_command(worktree)
    environment = dict(os.environ)
    if command[1:3] == ["-m", "concorde"]:
        # This package itself: make it importable for the child.
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parents[2])]
            + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
        )
    return command, environment


def _bound(tool: str, where: Path) -> tuple[Path, dict]:
    """The root and binding of the session's worktree; ``unbound_worktree`` without one."""
    try:
        root = binding_file.toplevel(where)
        bound = binding_file.load(root)
    except KernelError as error:
        raise own(
            tool,
            "unbound_worktree",
            f"the session's folder {where} has no usable workspace binding: "
            f"{error.code}: {error}",
            reason="environment",
            explanation="a workflow tool works only in the bound workspace of the session that "
            "asks for it, unless it is given a workspace folder",
            options=["run the workflow in a task worktree, from its task session"],
        ) from None
    if bound is None:
        raise own(
            tool,
            "unbound_worktree",
            f"the session's worktree {root} has no workspace binding "
            f"({binding_file.BINDING}), so it is no workspace a workflow could run in",
            reason="environment",
            explanation="a workflow tool works only in the bound workspace of the session that "
            "asks for it, unless it is given a workspace folder",
            options=[
                "run the workflow in a task worktree, from its task session",
                "pass the workspace folder as `folder`",
            ],
        )
    return root, bound


def workflow_step(where: Path, arguments: dict) -> dict:
    """The step outcome ``concorde workflow step`` printed in the session's worktree.

    The command runs as the server's child, and the runner it detaches is a process of its own:
    it lives until its run ends, whether or not the relaying agent's turn, the session's Bash
    calls or the session itself still run. A worktree without a workspace binding is refused
    with ``unbound_worktree``; a request the step command refuses is refused with its own link,
    unchanged; an output that is no JSON object with ``step_failed``.
    """
    tool = "workflow_step"
    root, _ = _bound(tool, where)
    wait = arguments.get("wait", STEP_WAIT)
    command, environment = concorde_of(root)
    command += [
        "workflow",
        "step",
        "--json",
        json.dumps(arguments["request"], ensure_ascii=False),
        "--wait",
        str(wait),
    ]
    shown = shlex.join(command)
    try:
        done = subprocess.run(
            command,
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=wait + STEP_GRACE,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise own(
            tool,
            "step_failed",
            f"`{shown}` in {root} did not answer: {error}",
            reason="environment",
            explanation="the server only passes the step command's answer on and has none",
            options=[
                "ask for the same step again; the same key never starts a run twice"
            ],
        ) from None
    try:
        value = json.loads(done.stdout)
    except ValueError:
        value = None
    if not isinstance(value, dict):
        raise own(
            tool,
            "step_failed",
            f"`{shown}` in {root} exited with status {done.returncode} and printed no JSON "
            f"object: {(done.stderr or done.stdout).strip()[-2000:] or '(no output)'}",
            reason="environment",
            explanation="the server only passes the step command's answer on and has none",
            options=[
                "ask for the same step again; the same key never starts a run twice"
            ],
        )
    if "key" not in value and isinstance(value.get("error"), dict):
        # The step command refused the request or the workspace: its own link, unchanged.
        raise ToolRefusal(value["error"])
    return value


def workflow_report(where: Path, arguments: dict) -> dict:
    """A saved workflow result of a workspace folder, the latest unless ``number`` names one."""
    tool = "workflow_report"
    if arguments.get("folder"):
        folder = Path(arguments["folder"])
        if not folder.is_absolute():
            raise own(
                tool,
                "invalid_input",
                f"the workspace folder {folder} is not an absolute path",
                explanation="a workspace folder is named as its binding names it, absolutely",
            )
    else:
        _, bound = _bound(tool, where)
        folder = Path(bound["traces"])
    reports = layout.workflow_folder(folder) / "reports"
    numbers = sorted(
        int(path.stem)
        for path in (reports.glob("*.json") if reports.is_dir() else ())
        if path.stem.isdigit()
    )
    if not numbers:
        raise own(
            tool,
            "no_report",
            f"the workspace folder {folder} has no workflow result in {reports}",
            explanation="a workflow result exists only once `concorde workflow report` saved one",
        )
    number = arguments.get("number") or numbers[-1]
    path = reports / f"{number}.json"
    if not path.is_file():
        raise own(
            tool,
            "no_report",
            f"the workspace folder {folder} has no workflow result {number}; it has "
            f"{', '.join(map(str, numbers))}",
            explanation="a workflow result exists only once `concorde workflow report` saved one",
        )
    return {
        "folder": folder.as_posix(),
        "number": number,
        "path": path.as_posix(),
        "report": json.loads(path.read_text(encoding="utf-8")),
    }


CALLS = {"workflow_step": workflow_step, "workflow_report": workflow_report}

__all__ = [
    "CALLS",
    "STEP_GRACE",
    "STEP_WAIT",
    "THREADED",
    "TOOLS",
    "ToolRefusal",
    "concorde_of",
]
