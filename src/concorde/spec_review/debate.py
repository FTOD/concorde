"""The ``spec_debate`` Operation (see the Spec debate document of Spec review).

For each named Module a ``reviewer`` and a ``challenger`` take turns on the same Specs under the
Module's ``review-spec`` grant. The host keeps the debate record, a list of items, and moves each
item by the stance a worker takes on it; it never takes a side:

1. ``validate_modules`` (shared with ``spec_review``): load and validate the Specs.
2. ``debate_modules``: per remaining Module, run the debate graph, a LangGraph ``StateGraph``:
   ``propose`` → ``challenge`` → (``respond`` → ``challenge``)* → ``settle``, bounded by
   ``--rounds`` challenge turns.
3. ``derive_verdict``: each Module's outcome from its settled items, the verdict and the result.

An item stands only when both workers agree on a finding, is dropped only when both agree it does
not hold, and is ``contested`` when they still disagree after the last turn: a decision point for
the developer. Every stance, finding and argument is a worker claim; the host's own facts
(structural findings, grants, audits, scope corrections, ignored responses) are host evidence.
"""

from __future__ import annotations

import copy
import json
from typing import TypedDict

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    evidence,
    load_prompt,
)
from ..spec.schema import validate
from . import operation as review

TASK_TYPE = "review-spec"
ROLES = ("reviewer", "challenger")
ITEM_IDENTITY = r"^d\.[1-9][0-9]*$"
STANCES = ["agree", "amend", "object"]
# In increasing precedence: the verdict is the Modules' highest outcome.
OUTCOMES = ["accepted", "undecided", "changes_required", "incomplete"]
DEFAULT_ROUNDS = 2
MAX_ROUNDS = 5

# A finding as a debater states it: the Spec review finding without the review memory's ``earlier``.
FINDING: dict = copy.deepcopy(review.REVIEWER_FINDING)
del FINDING["properties"]["earlier"]
# A finding as the payload carries it, its path normalized to the task worktree.
PAYLOAD_FINDING: dict = copy.deepcopy(FINDING)
PAYLOAD_FINDING["properties"]["path"] = {"type": "string", "format": "project-path"}

RESPONSE: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item", "stance", "reason"],
    "properties": {
        "item": {"type": "string", "pattern": ITEM_IDENTITY},
        "stance": {"enum": STANCES},
        "reason": {"type": "string", "minLength": 1},
        "finding": FINDING,
    },
}
PROPOSE_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": FINDING}},
}
CHALLENGE_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["responses", "additions"],
    "properties": {
        "responses": {"type": "array", "items": RESPONSE},
        "additions": {"type": "array", "items": FINDING},
    },
}
LATER_CHALLENGE_OUTPUT: dict = copy.deepcopy(CHALLENGE_OUTPUT)
LATER_CHALLENGE_OUTPUT["properties"]["additions"]["maxItems"] = 0
RESPOND_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["responses"],
    "properties": {"responses": {"type": "array", "items": RESPONSE}},
}

POSITION: dict = {"anyOf": [{"type": "null"}, PAYLOAD_FINDING]}
# contract.spec-review.debate-payload, version 1 (debate.md); a test keeps the two equal.
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
                    "turns",
                    "items",
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
                    "turns": {"type": "integer", "minimum": 0},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "id",
                                "proposer",
                                "state",
                                "finding",
                                "positions",
                                "history",
                            ],
                            "properties": {
                                "id": {"type": "string", "pattern": ITEM_IDENTITY},
                                "proposer": {"enum": list(ROLES)},
                                "state": {
                                    "enum": ["agreed", "withdrawn", "contested", "open"]
                                },
                                "finding": POSITION,
                                "positions": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "reviewer": POSITION,
                                        "challenger": POSITION,
                                    },
                                },
                                "history": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "required": ["turn", "role", "stance"],
                                        "properties": {
                                            "turn": {"type": "integer", "minimum": 1},
                                            "role": {"enum": list(ROLES)},
                                            "stance": {"enum": ["propose", *STANCES]},
                                            "reason": {
                                                "type": "string",
                                                "minLength": 1,
                                            },
                                            "finding": PAYLOAD_FINDING,
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


class DebateState(TypedDict):
    """The debate graph's state for one Module; plain JSON so that it could be checkpointed."""

    items: list[dict]
    turn: int
    challenges: int
    context_identity: str | None
    evidence: list[dict]
    # The Module's stop as {status, summary, error}, set when a turn cannot go on.
    stop: dict | None


def _other(role: str) -> str:
    return ROLES[1] if role == ROLES[0] else ROLES[0]


def awaiting(items: list[dict], role: str) -> list[dict]:
    """The open items whose current position the other side took, which ``role`` answers next."""
    return [item for item in items if item["state"] == "open" and item["last"] != role]


def _settle(item: dict) -> None:
    item["state"] = "agreed" if item["current"] is not None else "withdrawn"


def apply_responses(
    items: list[dict], role: str, turn: int, responses: list[dict], findings: dict
) -> tuple[list[dict], list[dict]]:
    """The items after ``role``'s responses of ``turn``, and host evidence of ignored responses.

    ``findings`` maps a response's position in ``responses`` to its amended finding, already
    normalized by the host. Stances: ``agree`` accepts the other side's current position and
    settles the item; ``amend`` makes the amended finding the current position; ``object`` makes
    the responder's own earlier position current again, or "does not hold" when it has none. A
    response for an item not awaiting ``role``, a second response for the same item, and an
    ``amend`` without a finding move nothing and are reported; an awaited item left unanswered
    stays where it is.
    """
    items = copy.deepcopy(items)
    open_items = {item["id"]: item for item in awaiting(items, role)}
    answered: set[str] = set()
    found: list[dict] = []
    for position, response in enumerate(responses):
        identity = response["item"]
        if identity not in open_items or identity in answered:
            found.append(
                evidence(
                    "debate-response",
                    identity,
                    f"turn {turn} {role}: ignored, "
                    + (
                        "a second response to the item"
                        if identity in answered
                        else "the item is not awaiting this role"
                    ),
                )
            )
            continue
        stance = response["stance"]
        if stance == "amend" and position not in findings:
            found.append(
                evidence(
                    "debate-response",
                    identity,
                    f"turn {turn} {role}: ignored, an amend without a finding",
                )
            )
            continue
        answered.add(identity)
        item = open_items[identity]
        entry = {
            "turn": turn,
            "role": role,
            "stance": stance,
            "reason": response["reason"],
        }
        if stance == "agree":
            _settle(item)
        elif stance == "amend":
            amended = findings[position]
            entry["finding"] = amended
            if amended == item["current"]:
                _settle(item)  # the amendment restates the other side's position
            else:
                item["positions"][role] = amended
                item["current"], item["last"] = amended, role
        else:
            own = item["positions"].setdefault(role, None)
            if own == item["current"]:
                _settle(item)  # both sides already hold the same position
            else:
                item["current"], item["last"] = own, role
        item["history"].append(entry)
    for identity in sorted(set(open_items) - answered, key=_order):
        found.append(
            evidence(
                "debate-response",
                identity,
                f"turn {turn} {role}: no response; the item stays open",
            )
        )
    return items, found


def _order(identity: str) -> int:
    return int(identity.split(".")[1])


def new_item(number: int, role: str, turn: int, finding: dict) -> dict:
    return {
        "id": f"d.{number}",
        "proposer": role,
        "state": "open",
        "current": finding,
        "last": role,
        "positions": {role: finding},
        "history": [{"turn": turn, "role": role, "stance": "propose"}],
    }


def outcome(items: list[dict], stopped: bool) -> str:
    """A Module's outcome from its settled items."""
    if stopped:
        return "incomplete"
    if any(
        item["state"] == "agreed" and item["current"]["severity"] == "blocking"
        for item in items
    ):
        return "changes_required"
    if any(
        item["state"] == "contested"
        and any(
            position is not None and position["severity"] == "blocking"
            for position in item["positions"].values()
        )
        for item in items
    ):
        return "undecided"
    return "accepted"


def _payload_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "proposer": item["proposer"],
        "state": item["state"],
        "finding": item["current"] if item["state"] == "agreed" else None,
        "positions": dict(item["positions"]),
        "history": item["history"],
    }


def _describe(finding: dict | None) -> str:
    if finding is None:
        return "the finding does not hold\n"
    return "```json\n" + json.dumps(finding, indent=2) + "\n```\n"


def _material(items: list[dict], role: str) -> str:
    """The items awaiting ``role``, with both positions and the history, and the rest briefly."""
    waiting = awaiting(items, role)
    lines = ["## Items awaiting you\n"]
    if not waiting:
        lines.append("\nNone.\n")
    for item in waiting:
        other = _other(role)
        lines.append(
            f"\n### {item['id']} (proposed by the {item['proposer']})\n\n"
            f"Current position, the {other}'s: {_describe(item['current'])}"
        )
        if role in item["positions"]:
            lines.append(f"\nYour last position: {_describe(item['positions'][role])}")
        lines.append("\nHistory:\n\n")
        for entry in item["history"]:
            reason = f": {entry['reason']}" if entry.get("reason") else ""
            lines.append(
                f"- turn {entry['turn']}, {entry['role']}, {entry['stance']}{reason}\n"
            )
    rest = [item for item in items if item not in waiting]
    if rest:
        lines.append("\n## The other items\n\n")
        for item in rest:
            problem = (item["current"] or item["positions"][item["proposer"]])[
                "problem"
            ]
            lines.append(f"- {item['id']} ({item['state']}): {problem}\n")
    return "".join(lines)


def _turn_section(turn: int, kind: str, first: bool) -> str:
    text = f"## This turn\n\nDebate turn: {turn} ({kind}).\n"
    if kind == "challenge":
        text += (
            "\nThis is your first challenge turn: report the findings the reviewer missed as "
            "`additions`.\n"
            if first
            else "\nThis is a later challenge turn: `additions` must be empty.\n"
        )
    return text


def _stop_value(stop: Stop) -> dict:
    return {"status": stop.status, "summary": stop.summary, "error": stop.error}


class Debate:
    """The debate of one Module: the graph's nodes, bound to the run and the Module's review."""

    def __init__(
        self, ctx: RunContext, subject: review.ModuleReview, prompt: str, rounds: int
    ):
        self.ctx = ctx
        self.subject = subject
        self.prompt = prompt
        self.rounds = rounds

    # -- one worker turn -------------------------------------------------------------------

    def _turn(self, state: DebateState, role: str, kind: str, schema: dict):
        """Run one worker turn; returns (output, updates) or (None, updates with the stop)."""
        turn = state["turn"] + 1
        instructions = (
            self.prompt
            + "\n"
            + review._task_section(self.ctx, self.subject, role)
            + "\n"
            + _turn_section(turn, kind, state["challenges"] == 0)
            + ("\n" + _material(state["items"], role) if kind != "propose" else "")
        )
        result = self.ctx.run_worker(
            instructions,
            task_type=TASK_TYPE,
            output_schema=schema,
            rounds=0,
            modules=[self.subject.module],
            role=role,
        )
        found = review._labelled(
            result.evidence, f"{self.subject.module} {role} turn {turn}"
        )
        updates: dict = {
            "turn": turn,
            "evidence": state["evidence"] + found,
            "context_identity": state["context_identity"]
            or review._identity(result.evidence),
        }
        if isinstance(result, Stop):
            result.error["actor"] += f", debate of {self.subject.module} turn {turn}"
            updates["stop"] = _stop_value(result)
            return None, updates
        return result.output or {}, updates

    def _normalized(self, claimed: list[dict], updates: dict, label: str):
        """The findings normalized as Spec review does, or None after setting the stop."""
        findings, corrections = review._normalize(self.ctx, self.subject, claimed)
        updates["evidence"] = updates["evidence"] + corrections
        if findings is None:
            stop = self.ctx.fail(
                "failed",
                "unusable_finding",
                f"The {label} of {self.subject.module} returned an unusable finding.",
                f"the {label} of {self.subject.module} named a path outside the task worktree: "
                + "; ".join(item["detail"] for item in corrections),
                reason="capability",
                explanation="the host checks every finding's path but never corrects a "
                "finding or relaunches a debater",
                evidence=corrections,
                options=["run spec_debate again"],
            )
            updates["stop"] = _stop_value(stop)
            return None
        return [
            {key: value for key, value in item.items() if key not in ("check", "id")}
            for item in findings
        ]

    def _responses(self, state: DebateState, role: str, output: dict, updates: dict):
        """Apply ``role``'s responses to the items; False after setting the stop."""
        responses = output.get("responses", [])
        amended = [
            (position, response["finding"])
            for position, response in enumerate(responses)
            if response["stance"] == "amend" and "finding" in response
        ]
        normalized = self._normalized(
            [finding for _, finding in amended], updates, role
        )
        if normalized is None:
            return False
        findings = {
            position: finding
            for (position, _), finding in zip(amended, normalized, strict=True)
        }
        items, found = apply_responses(
            state["items"], role, updates["turn"], responses, findings
        )
        updates["items"] = items
        updates["evidence"] = updates["evidence"] + found
        return True

    # -- nodes -----------------------------------------------------------------------------

    def propose(self, state: DebateState) -> dict:
        output, updates = self._turn(state, "reviewer", "propose", PROPOSE_OUTPUT)
        if output is None:
            return updates
        findings = self._normalized(output.get("findings", []), updates, "reviewer")
        if findings is None:
            return updates
        updates["items"] = [
            new_item(number, "reviewer", updates["turn"], finding)
            for number, finding in enumerate(findings, 1)
        ]
        return updates

    def challenge(self, state: DebateState) -> dict:
        first = state["challenges"] == 0
        output, updates = self._turn(
            state,
            "challenger",
            "challenge",
            CHALLENGE_OUTPUT if first else LATER_CHALLENGE_OUTPUT,
        )
        updates["challenges"] = state["challenges"] + 1
        if output is None or not self._responses(state, "challenger", output, updates):
            return updates
        additions = self._normalized(output.get("additions", []), updates, "challenger")
        if additions is None:
            return updates
        items = updates["items"]
        updates["items"] = items + [
            new_item(len(items) + number, "challenger", updates["turn"], finding)
            for number, finding in enumerate(additions, 1)
        ]
        return updates

    def respond(self, state: DebateState) -> dict:
        output, updates = self._turn(state, "reviewer", "respond", RESPOND_OUTPUT)
        if output is not None:
            self._responses(state, "reviewer", output, updates)
        return updates

    def settle(self, state: DebateState) -> dict:
        items = copy.deepcopy(state["items"])
        for item in items:
            if item["state"] == "open":
                item["state"] = "contested"
        return {"items": items}

    # -- edges -----------------------------------------------------------------------------

    def after_propose(self, state: DebateState) -> str:
        return "end" if state["stop"] else "challenge"

    def after_challenge(self, state: DebateState) -> str:
        if state["stop"]:
            return "end"
        return "respond" if awaiting(state["items"], "reviewer") else "settle"

    def after_respond(self, state: DebateState) -> str:
        if state["stop"]:
            return "end"
        if awaiting(state["items"], "challenger") and state["challenges"] < self.rounds:
            return "challenge"
        return "settle"

    def graph(self):
        """The compiled debate graph."""
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(DebateState)
        graph.add_node("propose", self.propose)
        graph.add_node("challenge", self.challenge)
        graph.add_node("respond", self.respond)
        graph.add_node("settle", self.settle)
        graph.add_edge(START, "propose")
        graph.add_conditional_edges(
            "propose", self.after_propose, {"challenge": "challenge", "end": END}
        )
        graph.add_conditional_edges(
            "challenge",
            self.after_challenge,
            {"respond": "respond", "settle": "settle", "end": END},
        )
        graph.add_conditional_edges(
            "respond",
            self.after_respond,
            {"challenge": "challenge", "settle": "settle", "end": END},
        )
        graph.add_edge("settle", END)
        return graph.compile()

    def run(self) -> DebateState:
        initial: DebateState = {
            "items": [],
            "turn": 0,
            "challenges": 0,
            "context_identity": None,
            "evidence": [],
            "stop": None,
        }
        # propose, then at most `rounds` challenge and respond turns, then settle.
        limit = 2 * self.rounds + 4
        return self.graph().invoke(initial, {"recursion_limit": limit})


def _debates(ctx: RunContext) -> dict[str, DebateState]:
    return ctx.__dict__.setdefault("spec_debate", {})


def debate_modules(ctx: RunContext):
    """Step 2: the debate graph per Module that passed validation."""
    try:
        import langgraph.graph  # noqa: F401
    except ImportError as error:
        return ctx.fail(
            "failed",
            "langgraph_unavailable",
            "spec_debate needs LangGraph, which this Python cannot import.",
            f"the interpreter running the Operation host cannot import langgraph ({error}); "
            "spec_debate runs its debate as a LangGraph graph",
            reason="environment",
            explanation="Concorde's runtime needs only the standard library; the spec_debate "
            "pilot is the one Operation that needs LangGraph, and the host does not install it",
            evidence=[evidence("host-error", "langgraph", str(error))],
            options=[
                (
                    "run the Operation with the development environment's interpreter, "
                    "`.venv/bin/python scripts/concorde.py run spec_debate ...`, after "
                    "`uv sync --group dev`"
                ),
                "run spec_review instead",
            ],
        )
    prompt = load_prompt("debate-spec")
    found: list[dict] = []
    rounds = ctx.arguments.rounds
    for subject in review._state(ctx).reviews.values():
        if subject.stop is not None:
            continue
        debate = Debate(ctx, subject, prompt, rounds)
        if not (ctx.run_dir / "debate-graph.mmd").exists():
            (ctx.run_dir / "debate-graph.mmd").write_text(
                debate.graph().get_graph().draw_mermaid()
            )
            found.append(
                evidence(
                    "graph",
                    (ctx.run_dir / "debate-graph.mmd").as_posix(),
                    "the debate graph",
                )
            )
        try:
            state = debate.run()
        except Exception as error:  # noqa: BLE001 -- a graph or node defect is recorded with its trace
            subject.stop = ctx.exception(
                f"Spec debate graph ({subject.module})",
                error,
                "debate_graph_failed",
                f"The debate of {subject.module} stopped on an unexpected error.",
            )
            found.extend(subject.stop.evidence)
            continue
        _debates(ctx)[subject.module] = state
        subject.context_identity = state["context_identity"]
        found.extend(state["evidence"])
        if state["stop"]:
            stop = state["stop"]
            subject.stop = Stop(stop["status"], stop["summary"], [], stop["error"])
    return Continue(evidence=found)


def derive_verdict(ctx: RunContext):
    """Step 3: each Module's outcome, the verdict and the result, all derived by the host."""
    debates = _debates(ctx)
    subjects = list(review._state(ctx).reviews.values())
    modules = []
    for subject in subjects:
        state = debates.get(subject.module)
        items = state["items"] if state else []
        modules.append(
            {
                "module": subject.module,
                "outcome": outcome(items, subject.stop is not None),
                "context_identity": subject.context_identity,
                "turns": state["turn"] if state else 0,
                "items": [_payload_item(item) for item in items],
            }
        )
    verdict = max((item["outcome"] for item in modules), key=OUTCOMES.index)
    payload = {"verdict": verdict, "modules": modules}
    validate(payload, PAYLOAD_SCHEMA)
    ctx.output = payload
    counted = [item for module in modules for item in module["items"]]
    counts = (
        f"{sum(1 for i in counted if i['state'] == 'agreed' and i['finding']['severity'] == 'blocking')} "
        f"agreed blocking finding(s), "
        f"{sum(1 for i in counted if i['state'] == 'contested')} decision point(s), "
        f"{sum(1 for i in counted if i['state'] == 'withdrawn')} withdrawn"
    )
    incomplete = [subject for subject in subjects if subject.stop is not None]
    if not incomplete:
        return Stop("ok", f"Spec debate: {verdict}; {counts}.")
    status = (
        "failed" if any(s.stop.status == "failed" for s in incomplete) else "blocked"
    )
    names = ", ".join(subject.module for subject in incomplete)
    reasons = "; ".join(f"{s.module}: {s.stop.summary}" for s in incomplete)
    return ctx.fail(
        status,
        "debate_incomplete",
        f"Spec debate: incomplete for {names} ({reasons}); {counts}.",
        f"the debate of {len(incomplete)} of {len(subjects)} Module(s) is incomplete, each a "
        f"cause below: {reasons}; {counts} in the debated Modules",
        reason="decision",
        explanation="spec_debate debates each Module once and never repairs or reruns; how "
        "to complete the review is the main agent's decision",
        causes=[subject.stop.error for subject in incomplete],
        options=["address each cause, then run spec_debate again for those Modules"],
    )


def _rounds(value: str) -> int:
    import argparse

    number = int(value)
    if not 1 <= number <= MAX_ROUNDS:
        raise argparse.ArgumentTypeError(f"--rounds must be 1 to {MAX_ROUNDS}")
    return number


def add_arguments(parser) -> None:
    parser.add_argument(
        "--rounds",
        type=_rounds,
        default=DEFAULT_ROUNDS,
        help=f"the most challenge turns per Module (1 to {MAX_ROUNDS}, default "
        f"{DEFAULT_ROUNDS})",
    )


SPEC_DEBATE = Provider(
    "spec_debate",
    TASK_TYPE,
    False,
    (review.validate_modules, debate_modules, derive_verdict),
    PAYLOAD_SCHEMA,
    add_arguments,
    task_scope="optional",
    roles=ROLES,
)

__all__ = [
    "CHALLENGE_OUTPUT",
    "PAYLOAD_SCHEMA",
    "PROPOSE_OUTPUT",
    "RESPOND_OUTPUT",
    "SPEC_DEBATE",
    "apply_responses",
    "outcome",
]
