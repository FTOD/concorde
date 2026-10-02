"""The ``spec_panel`` Operation (see the Spec panel document of Spec review).

For each named Module several ``reviewer`` workers review the same Specs independently and at the
same time, each under the Module's ``review-spec`` grant, and up to two ``architect`` workers judge
the Module among all the Modules, each under its ``review-architecture`` grant; then a ``chair``
worker audits their findings against the Specs, merges them into one panel report and gives each
merged finding its tier. The host labels every worker finding, checks that the chair accounted for
each label exactly once, reports the report's findings as Issues and derives the outcome:

1. ``validate_modules`` (shared with ``spec_review``): load and validate the Specs.
2. ``panel_modules``: per remaining Module, read its earlier Issues, run the panel graph, a
   LangGraph ``StateGraph`` (the reviewers and architects fan out in parallel, ``gather`` joins
   them, ``chair`` merges and the host's accounting sends the report back to the chair once when a
   label is missing), then report the chair's findings as Issues.
3. ``derive_verdict``: each Module's outcome from the Issues that stand, the verdict and the result.

Worker findings, the chair's merges, tiers, rejections, notes and resolutions are worker claims; the
host's own facts (structural findings, grants, audits, scope corrections, the accounting, the Issues
it reported to) are host evidence.
"""

from __future__ import annotations

import copy
import json
import operator
from typing import Annotated, TypedDict

from ...execution.context import (
    Continue,
    RunContext,
    Stop,
    evidence,
)
from ..workers import operation, run_worker
from ..prompts import (
    load_prompt,
)
from ...spec.schema import validate
from .. import review_issues
from . import operation as review
from . import reporting

TASK_TYPE = "review-spec"
ARCHITECTURE_TASK_TYPE = "review-architecture"
OUTCOMES = ["accepted", "changes_required", "incomplete"]
DEFAULT_REVIEWERS = 3
MAX_REVIEWERS = 5
DEFAULT_ARCHITECTS = 2
MAX_ARCHITECTS = 2
REVIEWERS = tuple(f"reviewer{seat}" for seat in range(1, MAX_REVIEWERS + 1))
ARCHITECTS = tuple(f"architect{seat}" for seat in range(1, MAX_ARCHITECTS + 1))
# The panel's worker ids: one per reviewer and architect seat a panel may have, and the chair.
WORKERS = (*REVIEWERS, *ARCHITECTS, "chair")
# The workers' roles in the order the payload lists their reviews, and each role's label prefix.
ROLES = ("reviewer", "architect")
PREFIX = {"reviewer": "r", "architect": "a"}
# The chair's attempts: its report, and one repair when the report leaves a label unaccounted.
CHAIR_ATTEMPTS = 2
LABEL = r"^[ra][1-9][0-9]*\.[1-9][0-9]*$"

RESOLUTION: dict = review.RESOLVED
# A reviewer's finding is a Spec review finding; an architect's judges an architecture dimension
# and may name the other Modules the problem concerns.
REVIEWER_FINDING: dict = copy.deepcopy(review.REVIEWER_FINDING)
ARCHITECT_FINDING: dict = copy.deepcopy(review.REVIEWER_FINDING)
ARCHITECT_FINDING["properties"]["dimension"] = {"enum": review.ARCHITECTURE_DIMENSIONS}
ARCHITECT_FINDING["properties"]["related"] = {
    "type": "array",
    "items": {"type": "string", "minLength": 1},
}
# Any worker finding, as the chair may merge either kind.
FINDING: dict = copy.deepcopy(ARCHITECT_FINDING)
FINDING["properties"]["dimension"] = {
    "enum": list(dict.fromkeys([*review.DIMENSIONS, *review.ARCHITECTURE_DIMENSIONS]))
}


def _output(finding: dict) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["findings"],
        "properties": {
            "findings": {"type": "array", "items": finding},
            "resolved": {"type": "array", "items": RESOLUTION},
        },
    }


OUTPUTS = {
    "reviewer": _output(REVIEWER_FINDING),
    "architect": _output(ARCHITECT_FINDING),
}
MERGED: dict = copy.deepcopy(FINDING)
MERGED["required"] = [*MERGED["required"], "sources", "note"]
MERGED["properties"]["sources"] = {
    "type": "array",
    "minItems": 1,
    "items": {"type": "string", "pattern": LABEL},
}
MERGED["properties"]["note"] = {"type": "string", "minLength": 1}
REJECTION: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["source", "reason"],
    "properties": {
        "source": {"type": "string", "pattern": LABEL},
        "reason": {"type": "string", "minLength": 1},
    },
}
CHAIR_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings", "rejected"],
    "properties": {
        "findings": {"type": "array", "items": MERGED},
        "rejected": {"type": "array", "items": REJECTION},
        "resolved": {"type": "array", "items": RESOLUTION},
    },
}

# The payload's findings: paths normalized to the task worktree; a worker's finding keeps its label
# and, as its claim, the earlier Issue it named, and a report finding gets the number of distinct workers among its sources,
# the earlier Issue it was appended to and the Issue it was reported to.
IDENTITY: dict = {
    "anyOf": [
        {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        {"type": "null"},
    ]
}

# contract.spec-review.panel-payload, version 5 (panel.md); a test keeps the two equal.
PAYLOAD_SCHEMA: dict = {
    "type": "object",
    "required": ["verdict", "modules", "workflow"],
    "additionalProperties": False,
    "properties": {
        "verdict": {"enum": OUTCOMES},
        # The workflow object of the step output convention, whose own contract defines it.
        "workflow": {"type": "object"},
        "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "module",
                    "outcome",
                    "context_identity",
                    "architecture_identity",
                    "reviews",
                    "findings",
                    "rejected",
                    "earlier_issues",
                ],
                "additionalProperties": False,
                "properties": {
                    "module": {"type": "string", "minLength": 1},
                    "outcome": {"enum": OUTCOMES},
                    "context_identity": IDENTITY,
                    "architecture_identity": IDENTITY,
                    "reviews": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "worker",
                                "role",
                                "seat",
                                "status",
                                "findings",
                                "resolved",
                            ],
                            "properties": {
                                "worker": {"enum": list(WORKERS[:-1])},
                                "role": {"enum": list(ROLES)},
                                "seat": {"type": "integer", "minimum": 1},
                                "status": {"enum": ["ok", "blocked", "failed"]},
                                "findings": {
                                    "type": "array",
                                    "items": {"$ref": "#/$defs/labelled"},
                                },
                                "resolved": {"type": "array", "items": RESOLUTION},
                            },
                        },
                    },
                    "findings": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/reported"},
                    },
                    "rejected": {"type": "array", "items": REJECTION},
                    "earlier_issues": review.EARLIER_ISSUES,
                },
            },
        },
    },
    "$defs": {},
}
_LABELLED: dict = copy.deepcopy(FINDING)
_LABELLED["properties"]["path"] = {"type": "string", "format": "project-path"}
_LABELLED["required"] = [*_LABELLED["required"], "label"]
_LABELLED["properties"]["label"] = {"type": "string", "pattern": LABEL}
_REPORTED: dict = copy.deepcopy(MERGED)
_REPORTED["properties"]["path"] = {"type": "string", "format": "project-path"}
_REPORTED["properties"]["earlier"] = review.ISSUE_ID
_REPORTED["required"] = [*_REPORTED["required"], "workers", "issue"]
_REPORTED["properties"]["workers"] = {"type": "integer", "minimum": 1}
_REPORTED["properties"]["issue"] = {"anyOf": [{"type": "null"}, review.ISSUE_ID]}
PAYLOAD_SCHEMA["$defs"] = {"labelled": _LABELLED, "reported": _REPORTED}


class PanelState(TypedDict):
    """The panel graph's state for one Module; plain JSON so that it could be checkpointed."""

    # One entry per reviewer and architect, appended by the parallel nodes in any order.
    reviews: Annotated[list[dict], operator.add]
    evidence: Annotated[list[dict], operator.add]
    context_identity: str | None
    architecture_identity: str | None
    # The chair's latest report and the host's accounting of it.
    report: dict | None
    unaccounted: list[str]
    attempts: int
    # The Module's stop as {status, summary, error}, set when the panel cannot go on.
    stop: dict | None


def account(labels: list[str], report: dict) -> list[str]:
    """What is wrong with the report's accounting of ``labels``: every label must appear exactly
    once, in one finding's ``sources`` or as one rejection's ``source``, and no other label may."""
    seen: dict[str, int] = {}
    for finding in report["findings"]:
        for label in finding["sources"]:
            seen[label] = seen.get(label, 0) + 1
    for rejection in report["rejected"]:
        seen[rejection["source"]] = seen.get(rejection["source"], 0) + 1
    problems = [
        f"{label} is not accounted for" for label in labels if label not in seen
    ]
    problems += [
        f"{label} is accounted for {count} times"
        for label, count in seen.items()
        if count > 1 and label in labels
    ]
    problems += [
        f"{label} names no worker finding" for label in seen if label not in labels
    ]
    return problems


def _labels(reviews: list[dict]) -> list[str]:
    return [finding["label"] for item in reviews for finding in item["findings"]]


def _ordered(reviews: list[dict]) -> list[dict]:
    """The reviews by role, reviewers first, then by seat."""
    return sorted(reviews, key=lambda item: (ROLES.index(item["role"]), item["seat"]))


def _stop_value(stop: Stop) -> dict:
    return {"status": stop.status, "summary": stop.summary, "error": stop.error}


class Panel:
    """The panel of one Module: the graph's nodes, bound to the run and the Module's review."""

    def __init__(
        self,
        ctx: RunContext,
        subject: review.ModuleReview,
        prompt: str,
        reviewers: int,
        architects: int,
    ):
        self.ctx = ctx
        self.subject = subject
        self.prompt = prompt
        self.seats = {"reviewer": reviewers, "architect": architects}

    def _brief(self, role: str, section: str, material: str = "") -> str:
        return (
            self.prompt
            + "\n"
            + review._task_section(self.ctx, self.subject, role)
            + "\n"
            + section
            + "\n"
            + reporting.material(self.subject.earlier)
            + ("\n" + material if material else "")
            + review.criteria(self.ctx.worktree)
        )

    def _launch(
        self, worker: str, task_type: str, instructions: str, schema: dict, label: str
    ):
        """The worker ``worker``, one of the panel's worker ids, so that the worker
        configuration may give each worker its own backend, model and thinking level; returns
        (output or None, host evidence, context identity, stop or None)."""
        result = run_worker(
            self.ctx,
            instructions,
            task_type=task_type,
            output_schema=schema,
            rounds=0,
            modules=[self.subject.module],
            worker=worker,
        )
        found = review._labelled(result.evidence, f"{self.subject.module} {label}")
        identity = review._identity(result.evidence)
        if isinstance(result, Stop):
            result.error["actor"] += f", panel of {self.subject.module} {label}"
            return None, found, identity, result
        return result.output or {}, found, identity, None

    def _normalized(self, claimed: list[dict], label: str):
        """The findings normalized as Spec review does, the corrections, or None and a stop."""
        findings, corrections = review._normalize(self.ctx, self.subject, claimed)
        if findings is None:
            return (
                None,
                corrections,
                self.ctx.fail(
                    "failed",
                    "unusable_finding",
                    f"The {label} of {self.subject.module} returned an unusable finding.",
                    f"the {label} of {self.subject.module} named a path outside the task "
                    "worktree: " + "; ".join(item["detail"] for item in corrections),
                    reason="capability",
                    explanation="the host checks every finding's path but never corrects a "
                    "finding or relaunches a worker for it",
                    evidence=corrections,
                    options=["run spec_panel again"],
                ),
            )
        cleaned = [
            {key: value for key, value in item.items() if key not in ("check", "issue")}
            for item in findings
        ]
        return cleaned, corrections, None

    # -- nodes -----------------------------------------------------------------------------

    def fan_out(self, state: PanelState):
        from langgraph.types import Send

        return [
            Send("review", {"role": role, "seat": seat})
            for role in ROLES
            for seat in range(1, self.seats[role] + 1)
        ]

    def review(self, seat_state: dict) -> dict:
        role, seat = seat_state["role"], seat_state["seat"]
        label = worker = f"{role}{seat}"
        output, found, identity, stop = self._launch(
            worker,
            ARCHITECTURE_TASK_TYPE if role == "architect" else TASK_TYPE,
            self._brief(
                role, f"## Your seat\n\nPanel seat: {seat} of {self.seats[role]}.\n"
            ),
            OUTPUTS[role],
            label,
        )
        entry = {
            "worker": worker,
            "role": role,
            "seat": seat,
            "status": "ok",
            "findings": [],
            "resolved": [],
            "identity": identity,
        }
        if stop is None:
            findings, corrections, stop = self._normalized(output["findings"], label)
            found += corrections
            if stop is None:
                entry["findings"] = [
                    {**finding, "label": f"{PREFIX[role]}{seat}.{number}"}
                    for number, finding in enumerate(findings, 1)
                ]
                entry["resolved"] = list(output.get("resolved") or [])
        if stop is not None:
            entry["status"] = stop.status
            entry["stop"] = _stop_value(stop)
        return {"reviews": [entry], "evidence": found}

    def gather(self, state: PanelState) -> dict:
        """Join the workers: stop the Module when any of them could not review."""
        reviews = _ordered(state["reviews"])

        def identity(role: str) -> str | None:
            return next(
                (
                    item["identity"]
                    for item in reviews
                    if item["role"] == role and item["identity"]
                ),
                None,
            )

        identities = {
            "context_identity": identity("reviewer"),
            "architecture_identity": identity("architect"),
        }
        failed = [item for item in reviews if "stop" in item]
        if not failed:
            return identities
        status = (
            "failed"
            if any(item["stop"]["status"] == "failed" for item in failed)
            else "blocked"
        )
        names = ", ".join(item["worker"] for item in failed)
        stop = self.ctx.fail(
            status,
            "panel_short",
            f"{names} of the {self.subject.module} panel did not finish.",
            f"{len(failed)} of {len(reviews)} worker(s) of the {self.subject.module} panel did "
            f"not finish ({names}), so the panel has no complete set of reviews to merge: "
            + "; ".join(
                f"{item['worker']}: {item['stop']['summary']}" for item in failed
            ),
            reason="decision",
            explanation="the chair merges only a complete panel, so that the report never "
            "silently lacks a review; rerunning or shrinking the panel is the main agent's "
            "decision",
            causes=[item["stop"]["error"] for item in failed],
            options=[
                "address each worker's cause, then run spec_panel again",
                "run spec_panel with fewer --reviewers or --architects",
            ],
        )
        return {**identities, "stop": _stop_value(stop)}

    def chair(self, state: PanelState) -> dict:
        attempt = state["attempts"] + 1
        reviews = _ordered(state["reviews"])
        material = ["## The reviews\n"]
        for item in reviews:
            material.append(f"\n### {item['role'].capitalize()} {item['seat']}\n\n")
            if not item["findings"]:
                material.append("No findings.\n")
            for finding in item["findings"]:
                material.append(f"```json\n{json.dumps(finding, indent=2)}\n```\n")
            if item["resolved"]:
                material.append(
                    "\nEarlier Issues it found resolved:\n\n```json\n"
                    + json.dumps(item["resolved"], indent=2)
                    + "\n```\n"
                )
        section = f"## Your report\n\nChair attempt: {attempt}.\n"
        if state["report"] is not None:
            section += (
                "\nYour previous report did not account for every label exactly once:\n\n"
                + "".join(f"- {problem}\n" for problem in state["unaccounted"])
                + "\nReturn the whole report again, corrected. Your previous report:\n\n"
                + f"```json\n{json.dumps(state['report'], indent=2)}\n```\n"
            )
        # The chair checks architects' findings against the other Modules' Specs they cite.
        wide = self.seats["architect"] > 0
        output, found, identity, stop = self._launch(
            "chair",
            ARCHITECTURE_TASK_TYPE if wide else TASK_TYPE,
            self._brief("chair", section, "".join(material)),
            CHAIR_OUTPUT,
            f"chair attempt {attempt}",
        )
        updates: dict = {"attempts": attempt, "evidence": found}
        if wide and identity and not state["architecture_identity"]:
            updates["architecture_identity"] = identity
        if stop is not None:
            updates["stop"] = _stop_value(stop)
            return updates
        merged, corrections, stop = self._normalized(
            [
                {
                    key: value
                    for key, value in item.items()
                    if key not in ("sources", "note")
                }
                for item in output["findings"]
            ],
            f"chair attempt {attempt}",
        )
        updates["evidence"] = found + corrections
        if stop is not None:
            updates["stop"] = _stop_value(stop)
            return updates
        report = {
            "findings": [
                {**finding, "sources": item["sources"], "note": item["note"]}
                for finding, item in zip(merged, output["findings"], strict=True)
            ],
            "rejected": output["rejected"],
            "resolved": list(output.get("resolved") or []),
        }
        problems = account(_labels(reviews), report)
        updates["report"] = report
        updates["unaccounted"] = problems
        updates["evidence"] = updates["evidence"] + [
            evidence(
                "panel-accounting",
                f"{self.subject.module} chair attempt {attempt}",
                "; ".join(problems)
                if problems
                else "every worker finding accounted for once",
            )
        ]
        if problems and attempt >= CHAIR_ATTEMPTS:
            stop = self.ctx.fail(
                "failed",
                "report_unaccounted",
                f"The chair of {self.subject.module} left worker findings unaccounted for.",
                f"after {attempt} attempt(s) the chair's report of {self.subject.module} still "
                "does not account for every reviewer and architect finding exactly once: "
                + "; ".join(problems),
                reason="exhausted",
                explanation="the host never decides a worker finding itself and gives the "
                f"chair {CHAIR_ATTEMPTS} attempts",
                evidence=[
                    evidence("panel-accounting", self.subject.module, problem)
                    for problem in problems
                ],
                options=[
                    "run spec_panel again",
                    "read the reviews in the payload directly",
                ],
            )
            updates["stop"] = _stop_value(stop)
        return updates

    # -- edges -----------------------------------------------------------------------------

    def after_gather(self, state: PanelState) -> str:
        return "end" if state["stop"] else "chair"

    def after_chair(self, state: PanelState) -> str:
        if state["stop"] or not state["unaccounted"]:
            return "end"
        return "chair"

    def graph(self):
        """The compiled panel graph."""
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(PanelState)
        graph.add_node("review", self.review)
        graph.add_node("gather", self.gather)
        graph.add_node("chair", self.chair)
        graph.add_conditional_edges(START, self.fan_out, ["review"])
        graph.add_edge("review", "gather")
        graph.add_conditional_edges(
            "gather", self.after_gather, {"chair": "chair", "end": END}
        )
        graph.add_conditional_edges(
            "chair", self.after_chair, {"chair": "chair", "end": END}
        )
        return graph.compile()

    def run(self) -> PanelState:
        initial: PanelState = {
            "reviews": [],
            "evidence": [],
            "context_identity": None,
            "architecture_identity": None,
            "report": None,
            "unaccounted": [],
            "attempts": 0,
            "stop": None,
        }
        # the workers, gather, then at most CHAIR_ATTEMPTS chair turns.
        steps = CHAIR_ATTEMPTS + 4
        return self.graph().invoke(initial, {"recursion_limit": steps})


def _panels(ctx: RunContext) -> dict[str, PanelState]:
    return ctx.__dict__.setdefault("spec_panel", {})


def _report(ctx: RunContext, subject: review.ModuleReview, state: PanelState):
    """Step 4: settle the earlier Issues the chair's report names and report its findings."""
    report = state["report"]
    subject.findings = _unreported(report)
    return review.report_findings(
        ctx,
        subject,
        report["resolved"],
        state["architecture_identity"] or state["context_identity"],
    )


def panel_modules(ctx: RunContext):
    """Steps 2 to 4: the earlier Issues, the panel graph and the Issue reports per Module."""
    try:
        import langgraph.graph  # noqa: F401
    except ImportError as error:
        return ctx.fail(
            "failed",
            "langgraph_unavailable",
            "spec_panel needs LangGraph, which this Python cannot import.",
            f"the interpreter running the Execution runner cannot import langgraph ({error}); "
            "spec_panel runs its panel as a LangGraph graph",
            reason="environment",
            explanation="LangGraph is one of Concorde's runtime dependencies, which the "
            "installer puts in Concorde's own environment; this interpreter lacks it",
            evidence=[evidence("host-error", "langgraph", str(error))],
            options=[
                "install Concorde again, or run `uv sync` in a source checkout",
                "run spec_review instead",
            ],
        )
    prompt = load_prompt("panel-spec")
    found: list[dict] = []
    for subject in review._state(ctx).reviews.values():
        if subject.stop is not None:
            continue
        found.extend(review.read_earlier(ctx, subject))
        if subject.stop is not None:
            continue
        panel = Panel(
            ctx, subject, prompt, ctx.arguments.reviewers, ctx.arguments.architects
        )
        drawing = ctx.run_dir / "panel-graph.mmd"
        if not drawing.exists():
            drawing.write_text(panel.graph().get_graph().draw_mermaid())
            found.append(evidence("graph", drawing.as_posix(), "the panel graph"))
        try:
            state = panel.run()
        except Exception as error:  # noqa: BLE001 -- a graph or node defect is recorded with its trace
            subject.stop = ctx.exception(
                f"Spec panel graph ({subject.module})",
                error,
                "panel_graph_failed",
                f"The panel of {subject.module} stopped on an unexpected error.",
            )
            found.extend(subject.stop.evidence)
            continue
        _panels(ctx)[subject.module] = state
        subject.context_identity = state["context_identity"]
        found.extend(state["evidence"])
        if state["stop"]:
            stop = state["stop"]
            subject.stop = Stop(stop["status"], stop["summary"], [], stop["error"])
            continue
        found.extend(_report(ctx, subject, state))
    return Continue(evidence=found)


def _unreported(report: dict) -> list[dict]:
    """The chair's report as it came, for a Module that stopped before it reported an Issue."""
    return [
        {
            **finding,
            "workers": len({label.split(".")[0] for label in finding["sources"]}),
            "issue": None,
        }
        for finding in report["findings"]
    ]


def _module_payload(subject: review.ModuleReview, state: PanelState | None) -> dict:
    state = state or {}
    report = state.get("report") or {"findings": [], "rejected": []}
    return {
        "module": subject.module,
        "outcome": subject.outcome,
        "context_identity": subject.context_identity,
        "architecture_identity": state.get("architecture_identity"),
        "reviews": [
            {
                "worker": item["worker"],
                "role": item["role"],
                "seat": item["seat"],
                "status": item["status"],
                "findings": item["findings"],
                "resolved": item["resolved"],
            }
            for item in _ordered(state.get("reviews", []))
        ],
        "findings": subject.findings
        if subject.summary is not None
        else _unreported(report),
        "rejected": report["rejected"],
        "earlier_issues": subject.summary,
    }


def derive_verdict(ctx: RunContext):
    """Step 5: each Module's outcome, the verdict and the result, all derived by the host."""
    panels = _panels(ctx)
    subjects = list(review._state(ctx).reviews.values())
    modules = [
        _module_payload(subject, panels.get(subject.module)) for subject in subjects
    ]
    verdict = max((item["outcome"] for item in modules), key=OUTCOMES.index)
    payload = {
        "verdict": verdict,
        "modules": modules,
        "workflow": review_issues.review_output(
            "spec_panel", verdict, review.blocking_counts(modules)
        ),
    }
    validate(payload, PAYLOAD_SCHEMA)
    ctx.output = payload
    reported = [item for module in modules for item in module["findings"]]
    raw = sum(len(r["findings"]) for module in modules for r in module["reviews"])
    standing = sum(subject.standing for subject in subjects if subject.stop is None)
    blocking = sum(1 for item in reported if reporting.is_blocking(item["tier"]))
    counts = (
        f"{blocking} blocking finding(s) and {len(reported) - blocking} suggestion(s) "
        f"merged from {raw} worker finding(s), "
        f"{sum(len(module['rejected']) for module in modules)} rejected; "
        f"{standing} blocking Issue(s) stand{review_issues.statement(ctx)}"
    )
    incomplete = [subject for subject in subjects if subject.stop is not None]
    if not incomplete:
        return Stop("ok", f"Spec panel: {verdict}; {counts}.")
    status = (
        "failed" if any(s.stop.status == "failed" for s in incomplete) else "blocked"
    )
    names = ", ".join(subject.module for subject in incomplete)
    reasons = "; ".join(f"{s.module}: {s.stop.summary}" for s in incomplete)
    return ctx.fail(
        status,
        "panel_incomplete",
        f"Spec panel: incomplete for {names} ({reasons}); {counts}.",
        f"the panel of {len(incomplete)} of {len(subjects)} Module(s) is incomplete, each a "
        f"cause below: {reasons}; {counts} in the complete panels",
        reason="decision",
        explanation="spec_panel runs each Module's panel once and never repairs or reruns it; "
        "how to complete the review is the main agent's decision",
        causes=[subject.stop.error for subject in incomplete],
        options=["address each cause, then run spec_panel again for those Modules"],
    )


def _count(name: str, low: int, high: int):
    def parse(value: str) -> int:
        import argparse

        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"--{name} must be {low} to {high}")
        return number

    return parse


def add_arguments(parser) -> None:
    parser.add_argument(
        "--reviewers",
        type=_count("reviewers", 2, MAX_REVIEWERS),
        default=DEFAULT_REVIEWERS,
        help=f"the reviewers per Module (2 to {MAX_REVIEWERS}, default {DEFAULT_REVIEWERS})",
    )
    parser.add_argument(
        "--architects",
        type=_count("architects", 0, MAX_ARCHITECTS),
        default=DEFAULT_ARCHITECTS,
        help=f"the architects per Module (0 to {MAX_ARCHITECTS}, default "
        f"{DEFAULT_ARCHITECTS})",
    )


SPEC_PANEL = operation(
    "spec_panel",
    TASK_TYPE,
    False,
    (review.validate_modules, panel_modules, derive_verdict),
    PAYLOAD_SCHEMA,
    add_arguments,
    binding="optional",
    workers=WORKERS,
)

__all__ = [
    "ARCHITECT_FINDING",
    "CHAIR_OUTPUT",
    "OUTPUTS",
    "PAYLOAD_SCHEMA",
    "SPEC_PANEL",
    "account",
]
