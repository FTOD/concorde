"""The ``spec_panel`` Operation (see the Spec panel document of Spec review).

For each named Module several ``reviewer`` workers review the same Specs independently and at the
same time, each under the Module's ``review-spec`` grant; then a ``chair`` worker audits their
findings against the Specs and merges them into one panel report. The host labels every reviewer
finding, checks that the chair accounted for each label exactly once, and derives the outcome:

1. ``validate_modules`` (shared with ``spec_review``): load and validate the Specs.
2. ``panel_modules``: per remaining Module, run the panel graph, a LangGraph ``StateGraph``: the
   reviewers fan out in parallel, ``gather`` joins them, ``chair`` merges, and ``account`` checks
   the report, sending it back to the chair once when a label is missing.
3. ``derive_verdict``: each Module's outcome from its report, the verdict and the result.

Reviewer findings, the chair's merges, rejections and notes are worker claims; the host's own facts
(structural findings, grants, audits, scope corrections, the accounting) are host evidence.
"""

from __future__ import annotations

import copy
import json
import operator
from typing import Annotated, TypedDict

from ..execution.context import (
    Continue,
    Provider,
    RunContext,
    Stop,
    evidence,
)
from ..operations.provider import (
    load_prompt,
)
from ..spec.schema import validate
from . import operation as review

TASK_TYPE = "review-spec"
OUTCOMES = ["accepted", "changes_required", "incomplete"]
DEFAULT_REVIEWERS = 3
MAX_REVIEWERS = 5
# The panel's worker ids: reviewer<seat> for each seat a panel may have, and the chair.
WORKERS = (*(f"reviewer{seat}" for seat in range(1, MAX_REVIEWERS + 1)), "chair")
# The chair's attempts: its report, and one repair when the report leaves a label unaccounted.
CHAIR_ATTEMPTS = 2
LABEL = r"^r[1-9][0-9]*\.[1-9][0-9]*$"

# A finding as a reviewer states it: the Spec review finding without the review memory's ``earlier``.
FINDING: dict = copy.deepcopy(review.REVIEWER_FINDING)
del FINDING["properties"]["earlier"]
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": FINDING}},
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
    },
}

# The payload's findings: paths normalized to the task worktree, and, for a report finding, the
# number of distinct reviewers among its sources, counted by the host.
LABELLED: dict = copy.deepcopy(FINDING)
LABELLED["properties"]["path"] = {"type": "string", "format": "project-path"}
LABELLED["required"] = [*LABELLED["required"], "label"]
LABELLED["properties"]["label"] = {"type": "string", "pattern": LABEL}
REPORTED: dict = copy.deepcopy(MERGED)
REPORTED["properties"]["path"] = {"type": "string", "format": "project-path"}
REPORTED["required"] = [*REPORTED["required"], "reviewers"]
REPORTED["properties"]["reviewers"] = {"type": "integer", "minimum": 1}

# contract.spec-review.panel-payload, version 1 (panel.md); a test keeps the two equal.
PAYLOAD_SCHEMA: dict = {
    "type": "object",
    "required": ["verdict", "modules"],
    "additionalProperties": False,
    "properties": {
        "verdict": {"enum": OUTCOMES},
        "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "module",
                    "outcome",
                    "context_identity",
                    "reviews",
                    "findings",
                    "rejected",
                ],
                "additionalProperties": False,
                "properties": {
                    "module": {"type": "string", "minLength": 1},
                    "outcome": {"enum": OUTCOMES},
                    "context_identity": {
                        "anyOf": [
                            {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                            {"type": "null"},
                        ]
                    },
                    "reviews": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["reviewer", "worker", "status", "findings"],
                            "properties": {
                                "reviewer": {"type": "integer", "minimum": 1},
                                "worker": {"enum": list(WORKERS[:-1])},
                                "status": {"enum": ["ok", "blocked", "failed"]},
                                "findings": {"type": "array", "items": LABELLED},
                            },
                        },
                    },
                    "findings": {"type": "array", "items": REPORTED},
                    "rejected": {"type": "array", "items": REJECTION},
                },
            },
        },
    },
}


class PanelState(TypedDict):
    """The panel graph's state for one Module; plain JSON so that it could be checkpointed."""

    # One entry per reviewer, appended by the parallel reviewer nodes in any order.
    reviews: Annotated[list[dict], operator.add]
    evidence: Annotated[list[dict], operator.add]
    context_identity: str | None
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
        f"{label} names no reviewer finding" for label in seen if label not in labels
    ]
    return problems


def _labels(reviews: list[dict]) -> list[str]:
    return [finding["label"] for item in reviews for finding in item["findings"]]


def _stop_value(stop: Stop) -> dict:
    return {"status": stop.status, "summary": stop.summary, "error": stop.error}


class Panel:
    """The panel of one Module: the graph's nodes, bound to the run and the Module's review."""

    def __init__(
        self, ctx: RunContext, subject: review.ModuleReview, prompt: str, size: int
    ):
        self.ctx = ctx
        self.subject = subject
        self.prompt = prompt
        self.size = size

    def _brief(self, role: str, section: str, material: str = "") -> str:
        return (
            self.prompt
            + "\n"
            + review._task_section(self.ctx, self.subject, role)
            + "\n"
            + section
            + ("\n" + material if material else "")
        )

    def _launch(self, worker: str, instructions: str, schema: dict, label: str):
        """The worker ``worker``, one of the panel's worker ids, so that the worker model
        configuration may give each reviewer and the chair its own backend, model and thinking
        level; returns (output or None, host evidence, context identity, stop or None)."""
        result = self.ctx.run_worker(
            instructions,
            task_type=TASK_TYPE,
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
            {key: value for key, value in item.items() if key not in ("check", "id")}
            for item in findings
        ]
        return cleaned, corrections, None

    # -- nodes -----------------------------------------------------------------------------

    def fan_out(self, state: PanelState):
        from langgraph.types import Send

        return [Send("review", {"seat": seat}) for seat in range(1, self.size + 1)]

    def review(self, seat_state: dict) -> dict:
        seat = seat_state["seat"]
        label = worker = f"reviewer{seat}"
        output, found, identity, stop = self._launch(
            worker,
            self._brief(
                "reviewer", f"## Your seat\n\nPanel seat: {seat} of {self.size}.\n"
            ),
            REVIEWER_OUTPUT,
            label,
        )
        entry = {
            "reviewer": seat,
            "worker": worker,
            "status": "ok",
            "findings": [],
            "identity": identity,
        }
        if stop is None:
            findings, corrections, stop = self._normalized(output["findings"], label)
            found += corrections
            if stop is None:
                entry["findings"] = [
                    {**finding, "label": f"r{seat}.{number}"}
                    for number, finding in enumerate(findings, 1)
                ]
        if stop is not None:
            entry["status"] = stop.status
            entry["stop"] = _stop_value(stop)
        return {"reviews": [entry], "evidence": found}

    def gather(self, state: PanelState) -> dict:
        """Join the reviewers: stop the Module when any of them could not review."""
        reviews = sorted(state["reviews"], key=lambda item: item["reviewer"])
        identity = next(
            (item["identity"] for item in reviews if item["identity"]), None
        )
        failed = [item for item in reviews if "stop" in item]
        if not failed:
            return {"context_identity": identity}
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
            f"{len(failed)} of {self.size} reviewer(s) of {self.subject.module} did not finish "
            f"({names}), so the panel has no complete set of reviews to merge: "
            + "; ".join(
                f"{item['worker']}: {item['stop']['summary']}" for item in failed
            ),
            reason="decision",
            explanation="the chair merges only a complete panel, so that the report never "
            "silently lacks a reviewer; rerunning or shrinking the panel is the main agent's "
            "decision",
            causes=[item["stop"]["error"] for item in failed],
            options=[
                "address each reviewer's cause, then run spec_panel again",
                "run spec_panel with fewer --reviewers",
            ],
        )
        return {"context_identity": identity, "stop": _stop_value(stop)}

    def chair(self, state: PanelState) -> dict:
        attempt = state["attempts"] + 1
        reviews = sorted(state["reviews"], key=lambda item: item["reviewer"])
        material = ["## The reviews\n"]
        for item in reviews:
            material.append(f"\n### Reviewer {item['reviewer']}\n\n")
            if not item["findings"]:
                material.append("No findings.\n")
            for finding in item["findings"]:
                material.append(f"```json\n{json.dumps(finding, indent=2)}\n```\n")
        section = f"## Your report\n\nChair attempt: {attempt}.\n"
        if state["report"] is not None:
            section += (
                "\nYour previous report did not account for every label exactly once:\n\n"
                + "".join(f"- {problem}\n" for problem in state["unaccounted"])
                + "\nReturn the whole report again, corrected. Your previous report:\n\n"
                + f"```json\n{json.dumps(state['report'], indent=2)}\n```\n"
            )
        output, found, _, stop = self._launch(
            "chair",
            self._brief("chair", section, "".join(material)),
            CHAIR_OUTPUT,
            f"chair attempt {attempt}",
        )
        updates: dict = {"attempts": attempt, "evidence": found}
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
                else "every reviewer finding accounted for once",
            )
        ]
        if problems and attempt >= CHAIR_ATTEMPTS:
            stop = self.ctx.fail(
                "failed",
                "report_unaccounted",
                f"The chair of {self.subject.module} left reviewer findings unaccounted for.",
                f"after {attempt} attempt(s) the chair's report of {self.subject.module} still "
                "does not account for every reviewer finding exactly once: "
                + "; ".join(problems),
                reason="exhausted",
                explanation="the host never decides a reviewer finding itself and gives the "
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
            "report": None,
            "unaccounted": [],
            "attempts": 0,
            "stop": None,
        }
        # the reviewers, gather, then at most CHAIR_ATTEMPTS chair turns.
        steps = CHAIR_ATTEMPTS + 4
        return self.graph().invoke(initial, {"recursion_limit": steps})


def _panels(ctx: RunContext) -> dict[str, PanelState]:
    return ctx.__dict__.setdefault("spec_panel", {})


def panel_modules(ctx: RunContext):
    """Step 2: the panel graph per Module that passed validation."""
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
    size = ctx.arguments.reviewers
    for subject in review._state(ctx).reviews.values():
        if subject.stop is not None:
            continue
        panel = Panel(ctx, subject, prompt, size)
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
    return Continue(evidence=found)


def _module_payload(subject: review.ModuleReview, state: PanelState | None) -> dict:
    reviews = sorted(
        (state or {}).get("reviews", []), key=lambda item: item["reviewer"]
    )
    report = (state or {}).get("report") or {"findings": [], "rejected": []}
    findings = [
        {
            **finding,
            "reviewers": len({label.split(".")[0] for label in finding["sources"]}),
        }
        for finding in report["findings"]
    ]
    if subject.stop is not None:
        outcome = "incomplete"
    elif any(item["severity"] == "blocking" for item in findings):
        outcome = "changes_required"
    else:
        outcome = "accepted"
    return {
        "module": subject.module,
        "outcome": outcome,
        "context_identity": subject.context_identity,
        "reviews": [
            {
                "reviewer": item["reviewer"],
                "worker": item["worker"],
                "status": item["status"],
                "findings": item["findings"],
            }
            for item in reviews
        ],
        "findings": findings,
        "rejected": report["rejected"],
    }


def derive_verdict(ctx: RunContext):
    """Step 3: each Module's outcome, the verdict and the result, all derived by the host."""
    panels = _panels(ctx)
    subjects = list(review._state(ctx).reviews.values())
    modules = [
        _module_payload(subject, panels.get(subject.module)) for subject in subjects
    ]
    verdict = max((item["outcome"] for item in modules), key=OUTCOMES.index)
    payload = {"verdict": verdict, "modules": modules}
    validate(payload, PAYLOAD_SCHEMA)
    ctx.output = payload
    reported = [item for module in modules for item in module["findings"]]
    raw = sum(len(r["findings"]) for module in modules for r in module["reviews"])
    counts = (
        f"{sum(1 for item in reported if item['severity'] == 'blocking')} blocking and "
        f"{sum(1 for item in reported if item['severity'] == 'advisory')} advisory finding(s) "
        f"merged from {raw} reviewer finding(s), "
        f"{sum(len(module['rejected']) for module in modules)} rejected"
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


def _reviewers(value: str) -> int:
    import argparse

    number = int(value)
    if not 2 <= number <= MAX_REVIEWERS:
        raise argparse.ArgumentTypeError(f"--reviewers must be 2 to {MAX_REVIEWERS}")
    return number


def add_arguments(parser) -> None:
    parser.add_argument(
        "--reviewers",
        type=_reviewers,
        default=DEFAULT_REVIEWERS,
        help=f"the reviewers per Module (2 to {MAX_REVIEWERS}, default {DEFAULT_REVIEWERS})",
    )


SPEC_PANEL = Provider(
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
    "CHAIR_OUTPUT",
    "PAYLOAD_SCHEMA",
    "REVIEWER_OUTPUT",
    "SPEC_PANEL",
    "account",
]
