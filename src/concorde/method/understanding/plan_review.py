"""The ``plan_review`` Operation: a read-only reviewer judges a plan the caller wrote.

Steps (the step table of "How plan_review is built" in the Understanding Module Spec):

1. ``read_plan``: read ``--plan``, keep an exact copy as ``plan.md`` in the run's trace node and
   record its digest; a missing, unreadable, non-UTF-8 or empty plan fails the run.
2. ``settle_iteration``: at most one admitted input is a ``plan_review`` run, the previous
   iteration, and ``--accept``/``--reject`` answer each of its findings exactly once.
3. to 5. ``review``: the standard worker sequence for task type ``review-code`` with the worker
   ``reviewer``, no checks and no resume round; the grant makes nothing writable.
6. ``check_review``: every basis resolves, the responses and restated findings match the previous
   iteration, the verdict follows the findings.

The discussion over several iterations is the caller's: the Operation never loops.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path

from ...execution.context import Continue, RunContext, evidence
from ..workers import operation, run_worker
from ...execution.operations.provider import load_prompt
from ...spec.repository import SpecRepository
from ...spec.repository_base import SpecError, is_identity

NAME = "plan_review"
REVIEWER = "reviewer"
PLAN_COPY = "plan.md"
KINDS = ["goal", "violation", "spec-gap", "code", "scope", "sequence"]
FINDING_ID = {"type": "string", "pattern": "^F[0-9]+$"}
_TEXT = {"type": "string", "minLength": 1}

ANSWER_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["finding", "answer", "text"],
    "properties": {
        "finding": FINDING_ID,
        "answer": {"enum": ["accepted", "rejected"]},
        "text": _TEXT,
    },
}

RESPONSE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["finding", "outcome", "comment"],
    "properties": {
        "finding": FINDING_ID,
        "outcome": {"enum": ["settled", "maintained"]},
        "comment": _TEXT,
    },
}

FINDING_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "severity",
        "kind",
        "module",
        "basis",
        "locations",
        "description",
        "suggestion",
        "previous",
    ],
    "properties": {
        "id": FINDING_ID,
        "severity": {"enum": ["blocking", "advisory"]},
        "kind": {"enum": KINDS},
        "module": {
            "anyOf": [{"type": "string", "pattern": "^module\\."}, {"type": "null"}]
        },
        "basis": {"anyOf": [_TEXT, {"type": "null"}]},
        "locations": {"type": "array", "items": _TEXT},
        "description": _TEXT,
        "suggestion": _TEXT,
        "previous": {"anyOf": [FINDING_ID, {"type": "null"}]},
    },
}

# contract.understanding.plan-review, version 1
# (specs/concorde/execution/operations/understanding/contracts.md)
REPORT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "plan",
        "iteration",
        "previous",
        "answers",
        "summary",
        "responses",
        "findings",
        "verdict",
    ],
    "properties": {
        "plan": {
            "type": "object",
            "additionalProperties": False,
            "required": ["file", "copy", "digest"],
            "properties": {
                "file": _TEXT,
                "copy": _TEXT,
                "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            },
        },
        "iteration": {"type": "integer", "minimum": 1},
        "previous": {"anyOf": [_TEXT, {"type": "null"}]},
        "answers": {"type": "array", "items": ANSWER_SCHEMA},
        "summary": _TEXT,
        "responses": {"type": "array", "items": RESPONSE_SCHEMA},
        "findings": {"type": "array", "items": FINDING_SCHEMA},
        "verdict": {"enum": ["accepted", "changes_required"]},
    },
}

# The reviewer's part of its worker result (``output``); its ``summary`` is the top-level one.
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["responses", "findings"],
    "properties": {
        "responses": {"type": "array", "items": RESPONSE_SCHEMA},
        "findings": {"type": "array", "items": FINDING_SCHEMA},
    },
}

# The previous iteration's plan is shown as a diff when both fit in the brief.
PLAN_DIFF_LIMIT = 100_000


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan", required=True)
    parser.add_argument(
        "--accept",
        nargs=2,
        action="append",
        default=[],
        metavar=("FINDING", "TEXT"),
    )
    parser.add_argument(
        "--reject",
        nargs=2,
        action="append",
        default=[],
        metavar=("FINDING", "TEXT"),
    )


# --- step 1: the plan --------------------------------------------------------------------------


def read_plan(ctx: RunContext):
    """Read the plan, keep its exact copy in the run's trace node and record its digest."""
    given = Path(ctx.arguments.plan)
    path = Path(
        os.path.normpath(given if given.is_absolute() else ctx.worktree / given)
    )
    problem, data = None, b""
    try:
        data = path.read_bytes()
    except OSError as error:
        problem = f"it cannot be read: {error}"
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            problem = f"it is not UTF-8 text: {error}"
        else:
            if not text.strip():
                problem = "it is empty"
    if problem:
        return ctx.fail(
            "failed",
            "plan_unreadable",
            f"The plan {path} cannot be reviewed: {problem}.",
            f"--plan {ctx.arguments.plan} names {path}, which plan_review cannot review because "
            f"{problem}; no worker was launched",
            reason="input",
            explanation="the plan is the caller's file, which the Operation only reads",
            evidence=[evidence("plan", path.as_posix(), problem)],
            options=["write the plan to a UTF-8 text file and pass it with --plan"],
        )
    copy = ctx.run_dir / PLAN_COPY
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_bytes(data)
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    ctx.state["plan"] = {
        "file": path.as_posix(),
        "copy": copy.as_posix(),
        "digest": digest,
    }
    ctx.state["plan_text"] = data.decode("utf-8")
    return Continue(evidence=[evidence("plan", digest, f"{path}; kept as {copy}")])


# --- step 2: the iteration ---------------------------------------------------------------------


def answers(ctx: RunContext) -> list[dict]:
    """The caller's answers in the order given: every --accept, then every --reject."""
    return [
        {"finding": finding, "answer": "accepted", "text": text}
        for finding, text in ctx.arguments.accept
    ] + [
        {"finding": finding, "answer": "rejected", "text": text}
        for finding, text in ctx.arguments.reject
    ]


def iteration_problems(
    previous: list[tuple[str, dict]], given: list[dict]
) -> list[str]:
    """Every way the admitted inputs and the answers fail to form one iteration."""
    problems = []
    if len(previous) > 1:
        problems.append(
            "more than one admitted input is a plan_review run ("
            + ", ".join(identity for identity, _ in previous)
            + "); admit only the previous iteration"
        )
        return problems
    if not previous:
        if given:
            problems.append(
                "answers were given ("
                + ", ".join(item["finding"] for item in given)
                + ") but no plan_review run was admitted with --input"
            )
        return problems
    identity, output = previous[0]
    findings = [item["id"] for item in output.get("findings") or []]
    answered = [item["finding"] for item in given]
    for finding in findings:
        count = answered.count(finding)
        if count == 0:
            problems.append(f"finding {finding} of {identity} is not answered")
        elif count > 1:
            problems.append(
                f"finding {finding} of {identity} is answered {count} times"
            )
    for finding in sorted(set(answered) - set(findings)):
        problems.append(f"{identity} has no finding {finding} to answer")
    return problems


def settle_iteration(ctx: RunContext):
    """The previous iteration, if any, and the answers to every one of its findings."""
    previous = [
        (identity, value.get("output") or {})
        for identity, value in ctx.inputs.items()
        if value.get("name") == NAME
    ]
    given = answers(ctx)
    problems = iteration_problems(previous, given)
    if problems:
        return ctx.fail(
            "failed",
            "iteration_mismatch",
            "The inputs and answers do not form one iteration: "
            + "; ".join(problems)
            + ".",
            "plan_review answers the findings of at most one previous iteration, each exactly "
            "once, so it did not launch its reviewer: " + "; ".join(problems),
            reason="input",
            explanation="the caller leads the discussion and answers every finding of the "
            "previous iteration before the next one",
            evidence=[evidence("iteration", "", problem) for problem in problems],
            options=[
                (
                    "answer every finding of the previous plan_review run with --accept or "
                    "--reject, and admit only that run as --input"
                )
            ],
        )
    if previous:
        identity, output = previous[0]
        ctx.state["previous"] = identity
        ctx.state["previous_output"] = output
        ctx.state["iteration"] = int(output.get("iteration") or 1) + 1
    else:
        ctx.state["previous"] = None
        ctx.state["previous_output"] = None
        ctx.state["iteration"] = 1
    ctx.state["answers"] = given
    return Continue(
        evidence=[
            evidence(
                "iteration",
                str(ctx.state["iteration"]),
                f"previous {ctx.state['previous'] or 'none'}; {len(given)} answer(s)",
            )
        ]
    )


# --- steps 3 to 5: the reviewer ----------------------------------------------------------------


def plan_diff(previous: dict | None, text: str) -> str:
    """The change from the previous iteration's kept plan to this one, or an empty string."""
    if not previous:
        return ""
    try:
        before = Path(previous["plan"]["copy"]).read_text(encoding="utf-8")
    except (KeyError, TypeError, OSError, UnicodeDecodeError):
        return ""
    if len(before) + len(text) > PLAN_DIFF_LIMIT:
        return ""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            text.splitlines(keepends=True),
            "previous plan",
            "this plan",
        )
    )


def previous_material(ctx: RunContext) -> str:
    output = ctx.state["previous_output"]
    if output is None:
        return (
            "This is the first iteration: there is no previous review to respond to.\n"
        )
    answered = {item["finding"]: item for item in ctx.state["answers"]}
    parts = [
        (
            f"This is iteration {ctx.state['iteration']}. The previous iteration, run "
            f"{ctx.state['previous']}, reported the findings below; the caller answered "
            "each.\n"
        )
    ]
    for finding in output.get("findings") or []:
        answer = answered[finding["id"]]
        parts.append(
            f"\n### {finding['id']} ({finding['severity']}, {finding['kind']})\n\n"
            + "```json\n"
            + json.dumps(finding, indent=2)
            + "\n```\n\n"
            + f"Answer: **{answer['answer']}**: {answer['text']}\n"
        )
    diff = plan_diff(output, ctx.state["plan_text"])
    if diff:
        parts.append(
            "\n### How the plan changed since the previous iteration\n\n```diff\n"
            + diff
            + "\n```\n"
        )
    return "".join(parts)


def other_inputs(ctx: RunContext) -> str:
    material = {
        identity: value
        for identity, value in ctx.inputs.items()
        if identity != ctx.state["previous"]
    }
    if not material:
        return ""
    return (
        "\n## Other admitted inputs\n\nOutputs of earlier ok runs of this workspace, given as "
        "material:\n\n```json\n" + json.dumps(material, indent=2) + "\n```\n"
    )


def instructions(ctx: RunContext) -> str:
    return (
        load_prompt("plan-review").strip()
        + "\n\n## This review\n\n"
        + f"Bound Modules: {', '.join(ctx.modules)}\n\n"
        + f"The workspace's goal: {ctx.goal or '(none)'}\n\n"
        + "## The plan\n\n"
        + f"The caller's plan ({ctx.state['plan']['file']}):\n\n"
        + "````markdown\n"
        + ctx.state["plan_text"].rstrip("\n")
        + "\n````\n\n"
        + "## The previous iteration\n\n"
        + previous_material(ctx)
        + other_inputs(ctx)
    )


def review(ctx: RunContext):
    """Steps 3 to 5: run the reviewer once, without checks or resume rounds."""
    return run_worker(
        ctx,
        instructions(ctx),
        task_type="review-code",
        output_schema=REVIEWER_OUTPUT,
        worker=REVIEWER,
        checks=False,
        rounds=0,
    )


# --- step 6: the report ------------------------------------------------------------------------


def unresolved_bases(
    worktree: Path, modules: list[str], findings: list[dict]
) -> list[tuple[str, str]]:
    """(finding id, basis) for every basis outside the bound Modules' Spec context, and for
    every ``violation`` without one.

    A basis is a stable identity whose defining document lies in the Spec context of a bound
    Module, or a document path of that context, optionally followed by ``#anchor``.
    """
    repository = SpecRepository(worktree)
    documents: set[str] = set()
    for module in modules:
        documents.update(repository.spec_context(module).paths)
    problems = []
    for finding in findings:
        basis = finding["basis"]
        if basis is None:
            if finding["kind"] == "violation":
                problems.append((finding["id"], "(none)"))
            continue
        if is_identity(basis):
            document = repository.definer(basis)
            known = document is not None and document in documents
        else:
            known = basis.split("#", 1)[0] in documents
        if not known:
            problems.append((finding["id"], basis))
    return problems


def inconsistencies(
    previous: dict | None,
    responses: list[dict],
    findings: list[dict],
    modules: list[str],
) -> list[str]:
    """Every way the review fails to answer the previous iteration or names an unbound Module."""
    problems = []
    earlier = [item["id"] for item in (previous or {}).get("findings") or []]
    answered = [item["finding"] for item in responses]
    for finding in earlier:
        count = answered.count(finding)
        if count != 1:
            problems.append(
                f"previous finding {finding} has {count} responses instead of one"
            )
    for finding in sorted(set(answered) - set(earlier)):
        problems.append(
            f"a response names {finding}, which the previous iteration has not"
        )
    maintained = {
        item["finding"] for item in responses if item["outcome"] == "maintained"
    }
    restated = [item["previous"] for item in findings if item["previous"] is not None]
    for finding in sorted(maintained):
        count = restated.count(finding)
        if count != 1:
            problems.append(
                f"maintained finding {finding} is restated {count} times instead of once"
            )
    for item in findings:
        if item["previous"] is not None and item["previous"] not in maintained:
            problems.append(
                f"{item['id']} restates {item['previous']}, which is not maintained"
            )
    for item in findings:
        if item["module"] is not None and item["module"] not in modules:
            problems.append(
                f"{item['id']} concerns {item['module']}, which is not bound"
            )
    return problems


def check_review(ctx: RunContext):
    """Step 6: resolve every basis, check consistency with the previous iteration, derive the
    verdict."""
    claimed = ctx.output or {}
    responses = list(claimed.get("responses") or [])
    findings = list(claimed.get("findings") or [])
    ctx.output = None
    try:
        unresolved = unresolved_bases(ctx.worktree, ctx.modules, findings)
    except (SpecError, OSError, ValueError) as error:
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The workspace's Specs could not be loaded to check the review.",
            f"the Specs of {ctx.worktree} could not be loaded after the reviewer finished, so "
            f"the bases its findings cite cannot be resolved: {error}",
            reason="scope",
            explanation="plan_review reads Specs and never repairs them",
            evidence=[evidence("spec-load", ctx.worktree.as_posix(), str(error))],
            options=[
                "run concorde task-validation in the workspace",
                "repair the Specs",
            ],
        )
    if unresolved:
        return ctx.fail(
            "failed",
            "unresolved_basis",
            "A finding cites a basis the bound Modules' Spec context does not define.",
            "the reviewer's findings cite bases that the Spec context of "
            f"{', '.join(ctx.modules)} does not define, or a violation cites none, so the "
            "review is discarded: "
            + ", ".join(f"{finding} cites {basis}" for finding, basis in unresolved),
            reason="capability",
            explanation="the host checks every basis but never corrects a finding or "
            "relaunches the reviewer",
            evidence=[
                evidence("unresolved-basis", basis, finding)
                for finding, basis in unresolved
            ],
            options=[
                "run plan_review again with the same answers",
                "check the Spec context of the bound Modules",
            ],
        )
    problems = inconsistencies(
        ctx.state["previous_output"], responses, findings, ctx.modules
    )
    if problems:
        return ctx.fail(
            "failed",
            "inconsistent_review",
            "The review is inconsistent: " + "; ".join(problems) + ".",
            "the reviewer's answer does not match the previous iteration or the bound "
            "Modules, so the review is discarded: " + "; ".join(problems),
            reason="capability",
            explanation="the host checks the review but never corrects it or relaunches "
            "the reviewer",
            evidence=[
                evidence("inconsistent-review", "", problem) for problem in problems
            ],
            options=[
                "run plan_review again with the same answers",
                "read the reviewer's answer in `worker`",
            ],
        )
    blocking = any(item["severity"] == "blocking" for item in findings)
    verdict = "changes_required" if blocking else "accepted"
    report = {
        "plan": ctx.state["plan"],
        "iteration": ctx.state["iteration"],
        "previous": ctx.state["previous"],
        "answers": ctx.state["answers"],
        "summary": (ctx.worker or {}).get("summary") or "reviewed",
        "responses": responses,
        "findings": findings,
        "verdict": verdict,
    }
    return Continue(
        output=report,
        evidence=[
            evidence(
                "verdict",
                verdict,
                f"{len(findings)} finding(s), "
                f"{sum(item['severity'] == 'blocking' for item in findings)} blocking; "
                f"{len(responses)} response(s)",
            )
        ],
    )


PLAN_REVIEW = operation(
    name=NAME,
    task_type="review-code",
    writes=False,
    steps=(read_plan, settle_iteration, review, check_review),
    output_schema=REPORT_SCHEMA,
    add_arguments=add_arguments,
    workers=(REVIEWER,),
)

__all__ = ["PLAN_REVIEW", "REPORT_SCHEMA", "REVIEWER_OUTPUT", "unresolved_bases"]
