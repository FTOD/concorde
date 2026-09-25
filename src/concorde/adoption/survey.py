"""The ``survey`` Operation: a worker reads one Module's code and proposes child Modules.

Steps (the Survey Operation step table of the Adoption Module Spec):

1. ``inventory``: check the answers, load the worktree's Specs, check that exactly one Module is
   surveyed, and list every file it binds with its size in lines.
2. ``propose``: the standard worker sequence for task type ``code-to-spec`` with every writable
   level withheld, so the worker reads code and writes nothing; the audit fails any change.
3. ``check``: check the proposal against the worktree and the answers, and add the entries the
   surveyed Module keeps.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    evidence,
    load_prompt,
    spec_cause,
)
from .records import (
    DECOMPOSITION_SCHEMA,
    SURVEY_WORKER_SCHEMA,
    AnswersError,
    answer_problems,
    load_answers,
    narrowed_entries,
    proposal_problems,
)

# How many lines of the inventory the brief lists before it only counts the rest.
INVENTORY_LIMIT = 5000


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", default="")
    parser.add_argument("--answers")


def lines_of(path: Path) -> int:
    try:
        with path.open("rb") as stream:
            return sum(1 for _ in stream)
    except OSError:
        return 0


def repository_of(ctx: RunContext):
    from ..spec.repository import SpecRepository

    return SpecRepository(ctx.worktree)


def inventory(ctx: RunContext):
    """Step 1: exactly one surveyed Module, and every file it binds with its size."""
    from ..spec.repository_base import SpecError

    try:
        ctx.state["answers"] = load_answers(ctx.arguments.answers)
    except AnswersError as error:
        return answers_failure(ctx, error)
    if len(ctx.modules) != 1:
        return ctx.fail(
            "failed",
            "invalid_request",
            f"A survey is bound to exactly one Module, not {len(ctx.modules)}.",
            f"survey was started for {', '.join(ctx.modules) or 'no Module'}; a survey "
            "proposes the decomposition of exactly one Module",
            reason="input",
            explanation="the proposal names one parent whose realization its children split",
            options=["run survey again with --modules naming one Module"],
        )
    try:
        repository = repository_of(ctx)
        files = repository.bound_files(ctx.modules[0])
    except (SpecError, OSError, ValueError) as error:
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The worktree's Specs could not be loaded for the survey.",
            f"the Specs of {ctx.worktree} could not be loaded to list the files of "
            f"{ctx.modules[0]}: {getattr(error, 'code', type(error).__name__)}: {error}",
            reason="scope",
            explanation="a survey reads the code a Module binds, which only loadable Specs "
            "declare; repairing the Specs is outside a survey",
            evidence=[evidence("spec-load", ctx.worktree.as_posix(), str(error))],
            causes=[spec_cause(error)],
            options=["run validate to see why the Specs do not load"],
        )
    ctx.state["files"] = [(path, lines_of(ctx.worktree / path)) for path in files]
    return Continue(
        evidence=[
            evidence(
                "inventory",
                ctx.modules[0],
                f"{len(files)} bound file(s), "
                f"{sum(size for _, size in ctx.state['files'])} line(s)",
            )
        ]
    )


def instructions(ctx: RunContext, answers: list[dict]) -> str:
    module = ctx.modules[0]
    files = ctx.state["files"]
    listing = "\n".join(f"{size:>7}  {path}" for path, size in files[:INVENTORY_LIMIT])
    if len(files) > INVENTORY_LIMIT:
        listing += f"\n… and {len(files) - INVENTORY_LIMIT} more file(s)"
    parts = [
        load_prompt("survey").strip(),
        "\n\n## This run\n\n",
        f"Surveyed Module: {module}\n\n",
    ]
    if ctx.arguments.goal:
        parts.append(
            f"What the main agent asks you to pay attention to: {ctx.arguments.goal}\n\n"
        )
    parts.append(
        f"The files {module} binds, with their size in lines:\n\n```text\n{listing}\n```\n"
    )
    if answers:
        parts.append(
            "\nThe developer's answers, which you must follow:\n\n```json\n"
            + json.dumps(answers, indent=2, ensure_ascii=False)
            + "\n```\n"
        )
    if ctx.inputs:
        parts.append(
            "\nAdmitted inputs (outputs of earlier ok runs):\n\n```json\n"
            + json.dumps(ctx.inputs, indent=2, ensure_ascii=False)
            + "\n```\n"
        )
    return "".join(parts)


def answers_failure(ctx: RunContext, error: AnswersError):
    return ctx.fail(
        "failed",
        "invalid_answers",
        "The answers file could not be used.",
        f"the answers given with --answers cannot be used: {error}",
        reason="input",
        explanation="answers are the developer's; the Operation never repairs or guesses them",
        evidence=[evidence("answers", error.path, str(error))],
        options=["correct the answers file and run the Operation again"],
    )


def propose(ctx: RunContext):
    """Step 2: the survey worker, reading code under a grant that writes nothing."""
    return ctx.run_worker(
        instructions(ctx, ctx.state["answers"]),
        task_type="code-to-spec",
        output_schema=SURVEY_WORKER_SCHEMA,
        checks=False,
        rounds=0,
        read_only=True,
    )


def configured_check_ids(worktree: Path) -> set[str]:
    try:
        config = json.loads((worktree / ".concorde/config.json").read_text())
    except (OSError, ValueError):
        return set()
    return {
        check.get("id")
        for check in config.get("checks") or []
        if isinstance(check, dict)
    }


def check(ctx: RunContext):
    """Step 3: the proposal fits the worktree and the answers; add the remaining entries."""
    module = ctx.modules[0]
    claims = ctx.output or {}
    repository = repository_of(ctx)
    problems = proposal_problems(
        repository, module, claims, configured_check_ids(ctx.worktree)
    )
    answers = ctx.state.get("answers") or []
    problems += answer_problems(
        [item for item in answers if item["id"].startswith("d.")], claims["decisions"]
    )
    still_open = {item["id"] for item in claims["open_questions"]}
    problems += [
        f"open question {item['id']} was answered ({item['answer']!r}) but is still open"
        for item in answers
        if item["id"].startswith("q.") and item["id"] in still_open
    ]
    if problems:
        ctx.output = None  # the worker's proposal stays in the result's worker field
        return ctx.fail(
            "failed",
            "inconsistent_proposal",
            f"The survey's proposal does not fit the worktree ({len(problems)} problem(s)).",
            f"the decomposition the survey worker proposed for {module} does not fit "
            f"{ctx.worktree}: " + "; ".join(problems),
            reason="capability",
            explanation="the host checks a proposal but never corrects it or relaunches the "
            "worker; the worker's proposal stays in the result's worker field",
            evidence=[evidence("inconsistency", module, item) for item in problems],
            options=[
                "run survey again, with --goal naming what to avoid",
                "run survey again with --answers settling the choices",
            ],
        )
    parent_entries = sorted(repository.realization_entries(module))
    child_entries = [
        entry for child in claims["children"] for entry in child["entries"]
    ]
    replaced = narrowed_entries(ctx.worktree, parent_entries, child_entries)
    remaining = sorted({entry for items in replaced.values() for entry in items})
    output = {
        "module": module,
        "summary": claims["summary"],
        "children": claims["children"],
        "remaining_entries": remaining,
        "checks": claims["checks"],
        "decisions": claims["decisions"],
        "open_questions": claims["open_questions"],
    }
    return Continue(
        output=output,
        evidence=[
            evidence(
                "proposal",
                module,
                f"{len(claims['children'])} child Module(s), {len(claims['checks'])} "
                f"check(s), {len(claims['decisions'])} decision(s), "
                f"{len(claims['open_questions'])} open question(s)",
            )
        ],
    )


SURVEY = Provider(
    name="survey",
    task_type="code-to-spec",
    writes=False,
    steps=(inventory, propose, check),
    output_schema=DECOMPOSITION_SCHEMA,
    add_arguments=add_arguments,
    task_scope="optional",
)

__all__ = ["SURVEY"]
