"""The issues part's tools of the project MCP server: ``issue_list``, ``issue_show``,
``issue_check``, ``issue_report``, ``issue_close`` and ``issue_reopen``.

The project MCP server, Distribution's host, calls ``answer`` in a fresh process of the primary
worktree's current Concorde with the call as one JSON object: the ``tool``, its ``arguments`` and
the session's provenance (``primary``, ``where``). The tools answer and refuse exactly as
``concorde issues`` does, recording the session as ``main-agent`` in the primary worktree and as
``task-session`` with its task in a bound task worktree, and never wait for the merge lock.
"""

from __future__ import annotations

from pathlib import Path

from ..kernel import binding as binding_file
from ..kernel.errors import link
from ..kernel.refusal import KernelError
from ..kernel.schema import validate
from . import command as issues

ACTOR = "Concorde project MCP server"

TEXT = {"type": "string", "minLength": 1}
ISSUE = {"type": "string", "minLength": 1}
EVIDENCE = {"type": "array", "items": TEXT, "minItems": 1}
# What every Issue write tool says of the recovery the write runs first.
RECOVERY = (
    " Before writing, it puts back what a killed Issue write left uncommitted; refused with "
    "recovery_failed when that fails, the record staying uncommitted until the cause is fixed "
    "and `concorde issues recover` (no tool) puts it back, and with uncommitted_change when the "
    "Issue's record holds a change no Issue write made, to be inspected and reverted in the "
    "primary worktree, never committed by hand."
)


def schema(properties: dict, required=()) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


TOOLS: dict[str, dict] = {
    "issue_list": {
        "description": "A summary row per Issue of the project with its severity and tier, as "
        "`concorde issues list`: every Issue, open and closed, unless filtered. `status` keeps "
        "the Issues with that status, `module` those whose latest report has that owner or "
        "reporting Module, `tier` those whose latest report has one of those tiers and "
        "`severity` those whose latest report has one of those severities; given together, an "
        "Issue must pass each. Rows come by identity, or with `sort` severity most severe "
        "first, then by tier, decision-needed first, then the Issue reported first, Issues "
        "without a severity last.",
        "inputSchema": schema(
            {
                "status": {"enum": ["open", "closed"]},
                "module": TEXT,
                "tier": {
                    "type": "array",
                    "items": {"enum": list(issues.TIERS)},
                    "minItems": 1,
                },
                "severity": {
                    "type": "array",
                    "items": {"enum": list(issues.SEVERITIES)},
                    "minItems": 1,
                },
                "sort": {"enum": ["severity"]},
            }
        ),
    },
    "issue_show": {
        "description": "One Issue's complete record and revision, as `concorde issues show`.",
        "inputSchema": schema({"issue": ISSUE}, ["issue"]),
    },
    "issue_check": {
        "description": "Check every Issue record the primary worktree keeps, as `concorde issues "
        "check` there: errors and notes, each naming the record.",
        "inputSchema": schema({}),
    },
    "issue_report": {
        "description": "Record an Issue report, as `concorde issues report`: `report` is the "
        "report object (contract.issues.report, with its tier and severity), or `file` a report "
        "file; `check` checks it and records nothing. It creates an Issue, or appends to the one "
        "its issue_id names at its expected_revision. Evidence paths are checked in the "
        "session's worktree; the report is recorded as the session's (main-agent in the primary "
        "worktree, task-session with its task in a task worktree). Refused at once with "
        "merge_busy, naming the holder, while another process holds the merge lock."
        + RECOVERY,
        "inputSchema": schema(
            {
                "report": {"type": "object"},
                "file": TEXT,
                "check": {"type": "boolean"},
            }
        ),
    },
    "issue_close": {
        "description": "Close an open Issue at its current revision, as `concorde issues "
        "close`: `reason` resolved, duplicate (with `duplicate_of`) or not-actionable, a `note` "
        "and at least one `evidence` item. Refused at once with merge_busy while another "
        "process holds the merge lock." + RECOVERY,
        "inputSchema": schema(
            {
                "issue": ISSUE,
                "reason": {"enum": list(issues.CLOSING_REASONS)},
                "note": TEXT,
                "evidence": EVIDENCE,
                "duplicate_of": ISSUE,
            },
            ["issue", "reason", "note", "evidence"],
        ),
    },
    "issue_reopen": {
        "description": "Reopen a closed Issue at its current revision, as `concorde issues "
        "reopen`, with a `note` and at least one `evidence` item. Refused at once with "
        "merge_busy while another process holds the merge lock." + RECOVERY,
        "inputSchema": schema(
            {"issue": ISSUE, "note": TEXT, "evidence": EVIDENCE},
            ["issue", "note", "evidence"],
        ),
    },
}


class Refusal(Exception):
    def __init__(self, tool: str, detail: str):
        super().__init__(detail)
        self.link = link(
            "component",
            f"{ACTOR} ({tool})",
            "invalid_input",
            detail,
            reason="input",
            explanation="the call's arguments are not ones the tool can pass on to Issues",
        )


def _reporter(primary: Path, where: Path) -> tuple[Path, str, str | None]:
    """The session's worktree, whom its Issue writes are recorded as and its task: a bound task
    worktree's session is its task's task session, any other the main agent."""
    try:
        root = binding_file.toplevel(where)
        bound = binding_file.load(root)
    except KernelError:
        return primary, "main-agent", None
    if bound is None or root == primary:
        return root, "main-agent", None
    return root, "task-session", bound["workspace"]


def _call(name: str, primary: Path, where: Path, arguments: dict):
    if name == "issue_list":
        return issues.list_action(
            primary,
            status=arguments.get("status"),
            module=arguments.get("module"),
            tiers=arguments.get("tier"),
            severities=arguments.get("severity"),
            sort=arguments.get("sort"),
        )
    if name == "issue_show":
        return issues.show_action(primary, arguments["issue"])
    if name == "issue_check":
        return issues.check(primary)[0]
    if name == "issue_report":
        root, agent, task = _reporter(primary, where)
        if ("report" in arguments) == ("file" in arguments):
            raise Refusal(
                name,
                "give the report either as `report`, an object, or as `file`, a path",
            )
        file = arguments.get("file")
        return issues.report_action(
            root,
            file=Path(root, file) if file is not None else None,
            report=arguments.get("report"),
            task=task,
            check_only=arguments.get("check", False),
            agent=agent,
            wait=0.0,
        )
    actor = _reporter(primary, where)[1]
    if name == "issue_close":
        return issues.dispose(
            primary,
            arguments["issue"],
            arguments["reason"],
            arguments["note"],
            arguments["evidence"],
            duplicate_of=arguments.get("duplicate_of"),
            actor=actor,
            wait=0.0,
        )
    return issues.dispose(
        primary,
        arguments["issue"],
        "reopened",
        arguments["note"],
        arguments["evidence"],
        actor=actor,
        wait=0.0,
    )


def answer(envelope: dict) -> dict:
    """The answer of one call of the tool ``envelope["tool"]``: ``{"value"}`` or ``{"error"}``,
    the Issues command's own link unchanged."""
    name = str(envelope.get("tool"))
    try:
        if name not in TOOLS:
            raise Refusal(name, f"the issues part has no tool {name!r}")
        arguments = envelope.get("arguments")
        arguments = {} if arguments is None else arguments
        if not isinstance(arguments, dict):
            raise Refusal(name, f"the arguments are not an object: {arguments!r}"[:300])
        try:
            validate(arguments, TOOLS[name]["inputSchema"])
        except KernelError as error:
            raise Refusal(
                name, f"the arguments of {name} are invalid: {error}"
            ) from None
        primary = Path(envelope["primary"])
        value = _call(name, primary, Path(envelope.get("where") or primary), arguments)
    except (Refusal, issues.Refusal) as refusal:
        return {"error": refusal.link}
    return {"value": value}


__all__ = ["TOOLS", "answer"]
