"""The deterministic findings of ``project_review`` (see the Project review Module Spec,
"Deterministic findings").

Three kinds of problem need no worker to establish:

- ``check``: a configured check of a covered Module that failed or timed out;
- ``coverage``: the scenarios of a covered Module that no verification declaration in a file any
  Module binds names, read as Spec core's structural validation reads them;
- ``unowned``: the files Git tracks in the examined worktree that Validation's rule for a changed
  path would not account for: no Spec document member, glossary, control record, generated or build
  output or external material, and bound by no Module.

Each problem is one Issue, of a fixed title, tier and severity: one per check, one per Module's
uncovered scenarios and one for the unowned files, owned by the root Module. Its earlier Issue is
the open Issue of the same Module, the same provenance phase and the same title that a
``project_review`` reported: the host appends to it only when its text changed, carries it when it
did not, and lists it as resolved when the problem is gone. It never closes one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...execution.context import RunContext, Stop
from ...kernel.schema import digest
from ...spec.repository_base import bound_by, control_path, covers
from ...spec.verification import scan_declarations
from ...spec.validation import (
    build_path,
    generated,
    generated_outputs,
    version_controlled,
)
from .. import review_issues

PHASES = ("check", "coverage", "unowned")
# The tier and severity of each kind of problem.
GRADES = {
    "check:failed": ("obvious-fix", "high"),
    "check:timeout": ("decision-needed", "medium"),
    "coverage": ("obvious-fix", "medium"),
    "unowned": ("decision-needed", "medium"),
}
# The Issue type and subtype of each kind of problem: a scenario no test verifies is a missing
# test, as a code review's, and a file no Module binds lacks the promise that would cover it.
KINDS = {
    "check": ("bug", None),
    "coverage": ("gap", "implementation-spec-mismatch"),
    "unowned": ("gap", "missing-contract"),
}
UNOWNED_TITLE = "Tracked files bound to no Module"
LISTED = 50


@dataclass
class Problem:
    """One deterministic problem, as its Issue report states it, with the subjects it names."""

    phase: str
    module: str
    title: str
    tier: str
    severity: str
    description: str
    impact: str
    basis: str
    evidence: list[dict]
    subjects: list[str]
    identity: str
    issue: str | None = None
    earlier: str | None = None

    def payload(self) -> dict:
        found = {
            "phase": self.phase,
            "module": self.module,
            "title": self.title,
            "tier": self.tier,
            "severity": self.severity,
            "subjects": self.subjects,
            "issue": self.issue,
        }
        if self.earlier:
            found["earlier"] = self.earlier
        return found


@dataclass
class Settlement:
    """What the run did with the deterministic earlier Issues of the Modules it examined."""

    carried: list[dict] = field(default_factory=list)
    resolved: list[dict] = field(default_factory=list)


def check_title(check: str) -> str:
    return f"Configured check {check} does not pass"


def coverage_title(module: str) -> str:
    return f"Scenarios of {module} that no test verifies"


def _listing(items: list[str]) -> str:
    shown = "".join(f"- {item}\n" for item in items[:LISTED])
    if len(items) > LISTED:
        shown += f"- … and {len(items) - LISTED} more\n"
    return shown


def check_problems(
    ctx: RunContext, results: list[dict], digests: dict
) -> list[Problem]:
    """One problem per configured check that did not pass."""
    found = []
    for item in results:
        if item["status"] == "passed":
            continue
        tier, severity = GRADES[
            f"check:{'timeout' if item['status'] == 'timeout' else 'failed'}"
        ]
        log = Path(item["log"]).as_posix()
        found.append(
            Problem(
                "check",
                item["module"],
                check_title(item["check_id"]),
                tier,
                severity,
                f"The configured check {item['check_id']} of {item['module']} "
                + (
                    "did not finish within its time limit."
                    if item["status"] == "timeout"
                    else f"failed with exit status {item['exit_code']}."
                )
                + "\n\nSuggested repair: read the check's log, find whether the code, the test or "
                "the check's configuration is wrong, and fix it so the check passes.",
                "The Module's own configured check does not pass on the examined commit, so the "
                "promises it tests are not shown to hold, and every task's validation of this "
                "Module fails until it does.",
                f"{ctx.name} run {ctx.run_id} ran the check through Check execution in its "
                f"read-only check boundary: status {item['status']}, exit code "
                f"{item['exit_code']}; its log is {log}.",
                [
                    {
                        "path": f".concorde/checks/{item['module']}.json",
                        "description": f"configures {item['check_id']}",
                    }
                ],
                [item["check_id"]],
                digests.get(item["module"])
                or digest([item["check_id"], item["status"]]),
            )
        )
    return found


def coverage_problems(
    ctx: RunContext, repository, modules: list[str], identities: dict
) -> list[Problem]:
    """One problem per covered Module with a scenario no verification declaration names. A test
    file that cannot be read declares nothing, as for structural validation, which reports it."""
    listed = sorted(
        {
            path
            for module in repository.modules
            for path in repository.bound_files(module)
        }
    )
    declared = {
        item.scenario_id for item in scan_declarations(repository.root, listed, [])
    }
    uncovered: dict[str, list] = {}
    for scenario in repository.scenario_nodes.values():
        if scenario.owner in modules and scenario.id not in declared:
            uncovered.setdefault(scenario.owner, []).append(scenario)
    found = []
    for module, items in sorted(uncovered.items()):
        items.sort(key=lambda item: item.id)
        tier, severity = GRADES["coverage"]
        scenarios = [item.id for item in items]
        documents = sorted({item.document for item in items})
        found.append(
            Problem(
                "coverage",
                module,
                coverage_title(module),
                tier,
                severity,
                f"{len(scenarios)} scenario(s) of {module} are named by no test's "
                f"verification declaration:\n\n{_listing(scenarios)}\nSuggested repair: "
                "declare each scenario in the tests that exercise it, or write such a test.",
                "Nothing that runs shows these promised situations to hold, so a change that "
                "breaks one passes every check.",
                f"{ctx.name} run {ctx.run_id} read the verification declarations of every file "
                "a Module binds in the examined worktree; none names these scenarios.",
                [
                    {"path": path, "description": "defines scenarios no test verifies"}
                    for path in documents[:LISTED]
                ],
                scenarios,
                identities.get(module) or digest(scenarios),
            )
        )
    return found


def unowned_paths(repository) -> list[str] | None:
    """The files Git tracks in the repository's worktree that Validation's rule for a changed
    path would not account for, submodules left out; None when Git cannot list them."""
    listed = version_controlled(repository.root)
    if listed is None:
        return None
    files, _ = listed
    members = set(repository.source_documents) | (
        {repository.glossary_path} if repository.glossary_path else set()
    )
    outputs = generated_outputs(repository.root)
    entries = [
        entry for module in repository.modules.values() for entry in module.files
    ]
    external = [
        entry
        for module in repository.modules.values()
        for entry in repository.external_inclusions(module)
    ]
    return [
        path
        for path in files
        if not (
            path in members
            or control_path(path)
            or generated(path, outputs)
            or build_path(path)
            or any(covers(entry, path) for entry in external)
            or any(bound_by(entry, path) for entry in entries)
        )
    ]


def unowned_problem(ctx: RunContext, root: str, paths: list[str]) -> Problem | None:
    """The one problem of the tracked files bound to no Module, owned by the root Module."""
    if not paths:
        return None
    tier, severity = GRADES["unowned"]
    return Problem(
        "unowned",
        root,
        UNOWNED_TITLE,
        tier,
        severity,
        f"{len(paths)} file(s) Git tracks are bound to no Module and are no Spec document, "
        f"control record, generated output or external material:\n\n{_listing(paths)}\n"
        "Suggested repair: bind each to the Module whose responsibility it realizes, declare it "
        "external material, or remove it.",
        "No Module answers for these files: no task is bounded to change them, no worker may "
        "write them and no review judges them.",
        f"{ctx.name} run {ctx.run_id} listed the files Git tracks in the examined worktree and "
        "applied Validation's rule for a changed path to each.",
        [
            {"path": path, "description": "bound to no Module"}
            for path in paths[:LISTED]
        ],
        paths,
        digest(paths),
    )


def _report(problem: Problem) -> dict:
    return {
        "report_key": f"{problem.module}/{problem.subjects[0]}"
        if problem.phase == "check"
        else problem.module,
        "tier": problem.tier,
        "severity": problem.severity,
        "type": KINDS[problem.phase][0],
        "subtype": KINDS[problem.phase][1],
        "title": problem.title,
        "description": problem.description,
        "impact": problem.impact,
        "basis": problem.basis,
        "owner_target_id": problem.module,
        "evidence": problem.evidence,
    }


def settle_and_report(
    ctx: RunContext,
    problems: list[Problem],
    examined: dict[str, set[str]],
) -> tuple[list[dict], Settlement, Stop | None]:
    """Settle the deterministic earlier Issues of every examined Module and phase with the
    problems found, and report every new or changed problem; ``examined`` maps each phase to the
    Modules it examined. Returns the host evidence, the settlement and the stop of a refusal."""
    found: list[dict] = []
    settlement = Settlement()
    groups: dict[tuple[str, str], list[Problem]] = {}
    for problem in problems:
        groups.setdefault((problem.phase, problem.module), []).append(problem)
    pairs = sorted(
        {(phase, module) for phase, modules in examined.items() for module in modules}
        | set(groups)
    )
    try:
        for phase, module in pairs:
            earlier = review_issues.earlier_issues(
                ctx, module, {"project_review": (phase,)}
            )
            mine = groups.get((phase, module), [])
            if earlier is None:
                # The issues part is not installed: the problems stay in the result.
                continue
            titles = {problem.title: problem for problem in mine}
            carried = []
            for item in earlier:
                problem = titles.get(item["title"])
                if problem is None:
                    settlement.resolved.append(
                        {
                            "issue": item["issue"],
                            "reason": f"{ctx.name} run {ctx.run_id} no longer finds "
                            f"this {phase} problem of {module}: {item['title']}",
                        }
                    )
                    continue
                if problem.earlier is None:
                    # The first open Issue of the title is the problem's; it takes a new report
                    # only when the problem's text, tier or severity changed.
                    problem.earlier = item["issue"]
                    if item["description"] != problem.description or (
                        item["tier"],
                        item["severity"],
                    ) != (problem.tier, problem.severity):
                        continue
                    problem.issue = item["issue"]
                # An unchanged problem's Issue, or another open Issue of the same title, stands.
                carried.append(
                    {key: item[key] for key in ("issue", "severity", "tier", "title")}
                )
            settlement.carried.extend(carried)
            changed = [problem for problem in mine if problem.issue is None]
            if not changed:
                continue
            values = [
                {
                    **_report(problem),
                    "earlier": problem.earlier,
                    "tier": problem.tier,
                    "issue": None,
                }
                for problem in changed
            ]
            reported, stop = review_issues.report(
                ctx,
                module,
                values,
                changed[0].identity,
                lambda position, value: {
                    key: item
                    for key, item in value.items()
                    if key not in ("earlier", "issue")
                },
                review=f"{phase} findings",
                phase=phase,
            )
            found.extend(reported)
            for problem, value in zip(changed, values, strict=True):
                problem.issue = value["issue"]
                if not value.get("earlier"):
                    problem.earlier = None
            if stop is not None:
                return found, settlement, stop
    except review_issues.Refusal as refusal:
        return (
            found,
            settlement,
            ctx.fail(
                "failed",
                "issues_unreadable",
                "The earlier Issues of the deterministic findings cannot be read.",
                f"the project's Issues could not be read for the deterministic findings: "
                f"{refusal}",
                reason="environment",
                explanation="the host settles each deterministic problem with its earlier "
                "Issue, which it must be able to read; a failure of the Issue system is never "
                "reported as an Issue",
                causes=[refusal.link],
                options=["repair the Issue records (issue_check), then run again"],
            ),
        )
    return found, settlement, None


__all__ = [
    "GRADES",
    "PHASES",
    "Problem",
    "Settlement",
    "check_problems",
    "coverage_problems",
    "settle_and_report",
    "unowned_paths",
    "unowned_problem",
]
