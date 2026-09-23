"""The ``understand`` Operation: a reading worker assesses the bound Modules' Specs for a goal.

Steps (the step table of the Understanding Module Spec):

1. ``assess``: the standard worker sequence for task type ``understand`` (grant, settings, brief,
   launch, audit, run record) with one round and no checks; the grant makes nothing writable, so
   any change to the task worktree fails the run.
2. ``check_assessment``: every Module the assessment names must exist in the task worktree's
   Specs, and the assessment must be consistent (gaps exactly when insufficient, a plan exactly
   when requested and sufficient, one entry per bound Module).
"""

from __future__ import annotations

import argparse
import json

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    evidence,
    host_escalation,
    load_prompt,
)

MODULE_ID = {"type": "string", "pattern": "^module\\."}
OPERATIONS = [
    "understand",
    "specify",
    "implement",
    "test",
    "spec_review",
    "code_review",
    "validate",
    "delivery",
]

# contract.understanding.assessment, version 1 (specs/concorde/operations/understanding/contracts.md)
ASSESSMENT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["goal", "modules", "sufficient", "gaps", "plan"],
    "properties": {
        "goal": {"type": "string", "minLength": 1},
        "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["module", "promises"],
                "properties": {
                    "module": MODULE_ID,
                    "promises": {"type": "string", "minLength": 1},
                },
            },
        },
        "sufficient": {"type": "boolean"},
        "gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "module",
                    "document",
                    "missing",
                    "needed_for",
                    "suggestion",
                ],
                "properties": {
                    "module": MODULE_ID,
                    "document": {"type": "string", "minLength": 1},
                    "missing": {"type": "string", "minLength": 1},
                    "needed_for": {"type": "string", "minLength": 1},
                    "suggestion": {"type": "string", "minLength": 1},
                },
            },
        },
        "plan": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["summary", "modules", "pending", "steps", "decisions"],
                    "properties": {
                        "summary": {"type": "string", "minLength": 1},
                        "modules": {"type": "array", "minItems": 1, "items": MODULE_ID},
                        "pending": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["module", "realization", "path", "reason"],
                                "properties": {
                                    "module": MODULE_ID,
                                    "realization": {
                                        "type": "string",
                                        "pattern": "^realization\\.",
                                    },
                                    "path": {"type": "string", "minLength": 1},
                                    "reason": {"type": "string", "minLength": 1},
                                },
                            },
                        },
                        "steps": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["operation", "modules", "purpose"],
                                "properties": {
                                    "operation": {"enum": OPERATIONS},
                                    "modules": {"type": "array", "items": MODULE_ID},
                                    "purpose": {"type": "string", "minLength": 1},
                                },
                            },
                        },
                        "decisions": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1},
                        },
                    },
                },
            ]
        },
    },
}


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", required=True)
    parser.add_argument("--plan", action="store_true")


def task_material(ctx: RunContext) -> str:
    """The task's goal and the admitted inputs, as brief text."""
    parts = [f"The task's own goal: {ctx.task.get('goal', '(none)')}\n"]
    if ctx.inputs:
        parts.append(
            "\nAdmitted inputs (outputs of earlier ok runs of this task):\n\n```json\n"
            + json.dumps(ctx.inputs, indent=2)
            + "\n```\n"
        )
    return "".join(parts)


def instructions(ctx: RunContext) -> str:
    requested = "yes" if ctx.arguments.plan else "no"
    return (
        load_prompt("understand").strip()
        + "\n\n## This run\n\n"
        + f"Bound Modules: {', '.join(ctx.modules)}\n\n"
        + f"Plan requested: {requested}\n\n"
        + f"Goal: {ctx.arguments.goal}\n\n"
        + task_material(ctx)
    )


def assess(ctx: RunContext):
    """Steps 1 to 4: run the understand worker once, without checks or resume rounds."""
    outcome = ctx.run_worker(
        instructions(ctx),
        task_type="understand",
        output_schema=ASSESSMENT_SCHEMA,
        checks=False,
        rounds=0,
    )
    if isinstance(outcome, Continue) and outcome.output is not None:
        # The goal is the host's own argument; the worker only repeats it.
        outcome.output = {**outcome.output, "goal": ctx.arguments.goal}
    return outcome


def named_modules(assessment: dict) -> set[str]:
    names = {item["module"] for item in assessment["modules"]}
    names |= {item["module"] for item in assessment["gaps"]}
    plan = assessment.get("plan")
    if plan:
        names |= set(plan["modules"])
        names |= {item["module"] for item in plan["pending"]}
        for step in plan["steps"]:
            names |= set(step["modules"])
    return names


def inconsistencies(
    assessment: dict, modules: list[str], plan_requested: bool
) -> list[str]:
    problems = []
    sufficient, gaps, plan = (
        assessment["sufficient"],
        assessment["gaps"],
        assessment["plan"],
    )
    if sufficient and gaps:
        problems.append("the assessment is sufficient but lists Spec gaps")
    if not sufficient and not gaps:
        problems.append("the assessment is insufficient but lists no Spec gap")
    if plan is not None and not plan_requested:
        problems.append("the assessment carries a plan although none was requested")
    if plan is not None and not sufficient:
        problems.append(
            "the assessment carries a plan although the Spec is insufficient"
        )
    if plan is None and plan_requested and sufficient:
        problems.append(
            "a plan was requested and the Spec is sufficient, but no plan was given"
        )
    assessed = {item["module"] for item in assessment["modules"]}
    missing = [module for module in modules if module not in assessed]
    if missing:
        problems.append(
            f"no assessment entry for the bound Module(s) {', '.join(missing)}"
        )
    return problems


def check_assessment(ctx: RunContext):
    """Step 5: the named Modules exist in the task worktree's Specs; the assessment is consistent."""
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    assessment = ctx.output or {}
    try:
        known = set(SpecRepository(ctx.worktree).modules)
    except (SpecError, OSError, ValueError) as error:
        ctx.output = None
        return Stop(
            "failed",
            "The task worktree's Specs could not be loaded to check the assessment.",
            [evidence("spec-load", ctx.worktree.as_posix(), str(error))],
            host_escalation(f"the Specs cannot be loaded: {error}"),
        )
    unknown = sorted(named_modules(assessment) - known)
    if unknown:
        ctx.output = None
        return Stop(
            "failed",
            f"The assessment names {len(unknown)} Module(s) the task worktree does not define.",
            [
                evidence("unknown-module", identity, "not in the task worktree's Specs")
                for identity in unknown
            ],
            host_escalation(
                f"the assessment names unknown Modules: {', '.join(unknown)}",
                options=[
                    "run understand again with a clearer goal",
                    "register the Module first if it should exist",
                ],
            ),
        )
    problems = inconsistencies(assessment, ctx.modules, bool(ctx.arguments.plan))
    if problems:
        ctx.output = None
        return Stop(
            "failed",
            "The assessment is inconsistent: " + "; ".join(problems) + ".",
            [evidence("inconsistent-assessment", "", problem) for problem in problems],
            host_escalation(
                "inconsistent assessment: " + "; ".join(problems),
                options=[
                    "run understand again",
                    "read the worker's answer in `worker`",
                ],
            ),
        )
    verdict = "sufficient" if assessment["sufficient"] else "insufficient"
    return Continue(
        evidence=[
            evidence(
                "assessment",
                verdict,
                f"{len(named_modules(assessment))} named Module(s) exist; "
                f"{len(assessment['gaps'])} gap(s); plan {'given' if assessment['plan'] else 'none'}",
            )
        ]
    )


UNDERSTAND = Provider(
    name="understand",
    task_type="understand",
    writes=False,
    steps=(assess, check_assessment),
    output_schema=ASSESSMENT_SCHEMA,
    add_arguments=add_arguments,
)

__all__ = ["ASSESSMENT_SCHEMA", "UNDERSTAND"]
