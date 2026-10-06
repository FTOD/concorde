"""What every review provider does with the project's Issues, the review's memory.

Issues is an optional integration of the method part: the reviews reach it only through the
issues part's bookkeeping command, ``concorde issues``, JSON in and out, run as the started
worktree's own ``concorde``, and never import its code. Where the issues part is not installed,
which ``concorde`` tells by refusing ``issues`` as a command it does not offer, the reviews read
no earlier Issues, report nothing outside the run and say so in their result.

Before a review judges a Module, the host reads the Module's earlier Issues: its open Issues one of
whose reports one of the review's Operations made. The review reports only what is new or what
changed in an earlier Issue (naming it as ``earlier``) and lists the earlier Issues the Module no
longer has as ``resolved``; an earlier Issue it neither names nor resolves is carried and still
stands. The host, never a worker, then reports every finding through the command with the
provenance it vouches for: a finding that names an offered earlier Issue is appended to it at the
revision read just before, any other creates an Issue. It never closes an Issue, and a refusal of
the command stops the Module's reporting with the command's error link as the cause, never as an
Issue.

Each review supplies only what differs: which Operations made its earlier Issues, which findings
it reports nowhere, and the Issue report of one finding.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

from ..execution.context import RunContext, Stop, evidence
from ..kernel.errors import link
from ..workflows.output import step_output
from ..workflows.step import concorde_command

# The tiers and severities of the Issue report contract, weakest and most severe first; every tier
# but the first is blocking.
TIERS = ("suggestion", "obvious-fix", "preferred-fix", "decision-needed")
SEVERITIES = ("critical", "high", "medium", "low")
BLOCKING = TIERS[1:]
ACTOR = "Method (Issues through concorde issues)"
# How long one call of the command may take: a write waits up to 300 s for the merge lock.
TIMEOUT = 900
# The refusal code by which ``concorde`` names a command of a part the project has not installed,
# which it prints as ``{"error": <link>}`` on standard output, exiting with status 1.
ABSENT_CODE = "part_missing"
NOT_RECORDED = (
    "the findings were not recorded as Issues, since the issues part is not installed"
)


class Refusal(Exception):
    """A refusal of the issues command, or a failure to run it: ``link`` is its error link."""

    def __init__(self, link: dict):
        super().__init__(link.get("detail") or link.get("code") or "refused")
        self.link = link


class Absent(Exception):
    """The issues part is not installed: ``concorde`` does not offer ``issues``."""


def is_blocking(tier: str | None) -> bool:
    return tier in BLOCKING


def review_output(operation: str, verdict: str, modules: list[dict]) -> dict:
    """A review's workflow object under the step output convention: one ``review`` note with the
    verdict and each Module's outcome with its counts, so that a workflow reports the review
    without knowing the review's own payload."""
    return step_output(
        notes=[
            {
                "kind": "review",
                "text": f"{operation} verdict {verdict}: "
                + ", ".join(f"{item['module']} {item['outcome']}" for item in modules),
                "data": {"verdict": verdict, "modules": modules},
            }
        ]
    )


def installed(ctx: RunContext) -> bool | None:
    """Whether the issues part was found installed in this run; None before any call."""
    return ctx.__dict__.get("issues_installed")


def statement(ctx: RunContext) -> str:
    """What the result says about Issues: that the findings were not recorded where the issues
    part is not installed, else nothing."""
    return f" ({NOT_RECORDED})" if installed(ctx) is False else ""


def _failed(detail: str, explanation: str) -> Refusal:
    return Refusal(
        link(
            "component",
            ACTOR,
            "issues_command_failed",
            detail,
            reason="environment",
            explanation=explanation,
            options=[
                "carry this error chain in the task's decision log and escalation, or in the "
                "run's result; never report a failure of the Issue system as an Issue"
            ],
        )
    )


def _absent(completed: subprocess.CompletedProcess, answer) -> bool:
    return (
        completed.returncode == 1
        and isinstance(answer, dict)
        and isinstance(answer.get("error"), dict)
        and answer["error"].get("code") == ABSENT_CODE
    )


def call(ctx: RunContext, *words: str) -> dict:
    """The answer of ``concorde issues <words> --root <started worktree>``; ``Absent`` where the
    issues part is not installed, ``Refusal`` carrying the command's link when it refuses."""
    if installed(ctx) is False:
        raise Absent()
    root = Path(ctx.started_in)
    command = concorde_command(root)
    environment = dict(os.environ)
    if command[1:3] == ["-m", "concorde"]:
        # This package itself: make it importable for the child.
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parents[2])]
            + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else [])
        )
    argv = [*command, "issues", *words, "--root", str(root)]
    shown = " ".join(argv)
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise _failed(
            f"`{shown}` could not run to its end: {type(error).__name__}: {error}",
            "the review reaches the project's Issues only through the issues command, which "
            "did not answer",
        ) from error
    try:
        answer = json.loads(completed.stdout) if completed.stdout.strip() else None
    except ValueError:
        answer = None
    if _absent(completed, answer):
        ctx.__dict__["issues_installed"] = False
        raise Absent()
    ctx.__dict__["issues_installed"] = True
    if isinstance(answer, dict) and isinstance(answer.get("error"), dict):
        raise Refusal(answer["error"])
    if completed.returncode != 0 or not isinstance(answer, dict):
        output = (completed.stdout + completed.stderr).strip()[-2000:] or "(no output)"
        raise _failed(
            f"`{shown}` exited {completed.returncode} without an answer or an error link: "
            f"{output}",
            "the issues command answers every call with JSON; this one did not, so the "
            "review cannot tell what it did",
        )
    return answer


def earlier_issues(
    ctx: RunContext, module: str, operations: Iterable[str]
) -> list[dict] | None:
    """The Module's open Issues one of ``operations`` reported, each as its latest report states
    it; None where the issues part is not installed. Raises ``Refusal`` when the project's Issues
    cannot be read."""
    operations = set(operations)
    try:
        rows = call(ctx, "list", "--module", module, "--status", "open")["issues"]
    except Absent:
        return None
    found = []
    for row in rows:
        if (row["owner_target_id"] or row["target_id"]) != module:
            continue
        record = call(ctx, "show", row["id"])["issue"]
        if not any(
            item["source"]["operation"] in operations for item in record["reports"]
        ):
            continue
        latest = record["reports"][-1]["report"]
        found.append(
            {
                "issue": record["id"],
                "severity": latest.get("severity"),
                "tier": latest.get("tier"),
                "title": latest["title"],
                "description": latest["description"],
                "evidence": latest["evidence"],
            }
        )
    return found


# The resume rounds a review gives a worker to correct citations that do not hold.
CITATION_ROUNDS = 1


def citation_repair(problems: list[str]) -> str | None:
    """The repair text that resumes a review worker once with every citation of its findings that
    does not hold, or None when every one holds."""
    if not problems:
        return None
    return (
        "The host checked the citations of your findings, and these do not hold, so those "
        "findings would be rejected and never reported:\n\n"
        + "".join(f"- {problem}\n" for problem in problems)
        + "\nCorrect each of them from the material you were given, or leave the finding out "
        "when you cannot support it. Then end again with your complete structured result: every "
        "finding, the corrected ones included, and every resolution, since it replaces your "
        "previous result.\n"
    )


def without_blank_earlier(finding: dict) -> dict:
    """``finding`` without an ``earlier`` that is empty or blank, which names no earlier Issue: a
    worker may write one for a new finding instead of leaving the field out."""
    name = finding.get("earlier")
    if isinstance(name, str) and not name.strip():
        finding = {key: value for key, value in finding.items() if key != "earlier"}
    return finding


def settle(
    earlier: list[dict],
    findings: list[dict],
    resolved: list[dict],
    *,
    unoffered: str = "a finding names no earlier Issue offered",
) -> dict:
    """Which offered earlier Issue each finding names and which the review resolves.

    A finding keeps ``earlier`` only when it names an offered Issue no other finding named; a
    resolution counts only for an offered Issue no finding named and none resolved before. Every
    other name is listed under ``ignored``, a finding's unoffered one with the reason
    ``unoffered``; every offered Issue neither named nor resolved is carried."""
    offered = {item["issue"]: item for item in earlier}
    named: set[str] = set()
    ignored: list[dict] = []
    for finding in findings:
        name = finding.pop("earlier", None)
        if not (name or "").strip():
            continue
        if name not in offered:
            ignored.append({"issue": name, "reason": unoffered})
        elif name in named:
            ignored.append(
                {"issue": name, "reason": "another finding already names this Issue"}
            )
        else:
            finding["earlier"] = name
            named.add(name)
    done: list[dict] = []
    for item in resolved:
        name = item["issue"]
        if name not in offered:
            reason = "resolves no earlier Issue offered"
        elif name in named:
            reason = "a finding of this review names this Issue"
        elif any(entry["issue"] == name for entry in done):
            reason = "already resolved by this review"
        else:
            done.append({"issue": name, "reason": item["reason"]})
            continue
        ignored.append({"issue": name, "reason": reason})
    closed = named | {entry["issue"] for entry in done}
    carried = [
        {key: item[key] for key in ("issue", "severity", "tier", "title")}
        for item in earlier
        if item["issue"] not in closed
    ]
    return {"carried": carried, "resolved": done, "ignored": ignored}


def _head(worktree: Path) -> str | None:
    try:
        found = subprocess.run(
            ["git", "-C", str(worktree), "rev-parse", "--verify", "--quiet", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return found.stdout.strip() or None if found.returncode == 0 else None


def _report(ctx: RunContext, value: dict, provenance: dict) -> dict:
    """The command's receipt of one report recorded with ``provenance``."""
    with tempfile.TemporaryDirectory(prefix="concorde-issue-") as folder:
        report_file = Path(folder) / "report.json"
        provenance_file = Path(folder) / "provenance.json"
        report_file.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        provenance_file.write_text(
            json.dumps(provenance, ensure_ascii=False), encoding="utf-8"
        )
        return call(
            ctx,
            "report",
            "--file",
            str(report_file),
            "--provenance",
            str(provenance_file),
        )["receipt"]


def _unclaim(
    findings: list[dict], earlier: list[dict] | None, settled: dict | None
) -> None:
    """Take ``earlier`` from every finding that was not reported, whose earlier Issue was not
    appended to and so is carried in ``settled``, in the order ``earlier`` offered them."""
    unappended = {
        finding.pop("earlier")
        for finding in findings
        if finding["issue"] is None and finding.get("earlier")
    }
    if not unappended or settled is None:
        return
    carried = {item["issue"] for item in settled["carried"]} | unappended
    settled["carried"] = [
        {key: item[key] for key in ("issue", "severity", "tier", "title")}
        for item in earlier or []
        if item["issue"] in carried
    ]


def report(
    ctx: RunContext,
    module: str,
    findings: list[dict],
    identity: str | None,
    issue_report: Callable[[int, dict], dict],
    *,
    review: str,
    earlier: list[dict] | None = None,
    settled: dict | None = None,
) -> tuple[list[dict], Stop | None]:
    """Report every finding of one Module; returns the host evidence and, when the issues command
    refused a report, the Module's stop. Each finding gets its ``issue``, which stays None where
    the issues part is not installed.

    ``issue_report`` gives the Issue report of the finding at a position, counted from 1, without
    ``issue_id`` and ``expected_revision``; ``review`` names the review in the stop, such as
    ``code review``. A finding left unreported keeps no ``earlier``, since nothing was appended to
    that Issue, which still stands and so joins the ``carried`` of ``settled``, the review's
    settlement of ``earlier``, the Issues it offered."""
    for finding in findings:
        finding["issue"] = None
    found: list[dict] = []
    provenance = {
        "invocation_id": ctx.run_id,
        "agent": "operation",
        "operation": ctx.name,
        "phase": "report",
        "target_id": module,
        "context_id": identity,
        "change_id": ctx.workspace_name,
        "head": ctx.commit or _head(ctx.worktree),
    }
    try:
        for position, finding in enumerate(findings, 1):
            value = issue_report(position, finding)
            named = finding.get("earlier")
            if named:
                revision = call(ctx, "show", named)["revision"]
                value.update(issue_id=named, expected_revision=revision)
            receipt = _report(ctx, value, provenance)
            finding["issue"] = receipt["issue_id"]
            found.append(
                evidence(
                    "issue",
                    receipt["issue_id"],
                    f"{module} finding {position}: "
                    f"{'appended to' if named else 'created'} the Issue, report "
                    f"{receipt['report_id']}",
                )
            )
    except Absent:
        _unclaim(findings, earlier, settled)
        return [evidence("issues-not-recorded", module, NOT_RECORDED)], None
    except Refusal as refusal:
        _unclaim(findings, earlier, settled)
        reported = sum(1 for finding in findings if finding["issue"])
        stop = ctx.fail(
            "failed",
            "issues_unreported",
            f"The Issues of {module}'s {review} could not all be written.",
            f"the issues command refused a report of {module}'s {review} after {reported} of "
            f"its {len(findings)} finding(s) were reported, so the rest were not: {refusal}",
            reason="environment",
            explanation="a failure of the Issue system is never reported as an Issue, and the "
            "Operation does not retry it; the findings stay in the result",
            causes=[refusal.link],
            options=[
                "carry this error chain in the task's decision log and escalation",
                "once the Issue store works again, run the review again",
            ],
        )
        return found, stop
    return found, None


__all__ = [
    "BLOCKING",
    "CITATION_ROUNDS",
    "NOT_RECORDED",
    "SEVERITIES",
    "TIERS",
    "Absent",
    "citation_repair",
    "Refusal",
    "earlier_issues",
    "installed",
    "is_blocking",
    "review_output",
    "report",
    "settle",
    "statement",
    "without_blank_earlier",
]
