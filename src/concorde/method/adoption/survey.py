"""The ``survey`` Operation: a worker reads one Module's code and proposes child Modules.

Steps (the Survey Operation step table of the Adoption Module Spec):

1. ``inventory``: check the answers, load the worktree's Specs, check that exactly one Module is
   surveyed and, in a bound workspace, that no scaffold has written to it since the workspace's
   base commit, and write every file it binds with its size in lines to the run's inventory
   file.
2. ``propose``: the standard worker sequence for task type ``code-to-spec`` with every writable
   level withheld, so the worker reads code and writes nothing, and with the inventory file
   readable beside the grant; the audit fails any change.
3. ``check``: write every path inside the worktree relative to it, record each decision with its
   chosen option's text, check the proposal against the worktree and the answers, and add the
   entries the surveyed Module keeps.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
from pathlib import Path

from ...execution.checks.checks import configured_checks
from ...execution.context import (
    Continue,
    RunContext,
    evidence,
)
from ..specs import spec_cause
from ..workers import operation, run_worker
from ..prompts import (
    load_prompt,
)
from .records import (
    DECOMPOSITION_SCHEMA,
    SURVEY_WORKER_SCHEMA,
    AnswersError,
    answer_problems,
    evidence_problems,
    load_answers,
    narrowed_entries,
    proposal_problems,
    resolved_decisions,
    workflow_object,
    worktree_relative,
)

# The task material of the run's trace node in which the worker finds the inventory.
INVENTORY_FILE = "inventory.txt"


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
    from ...spec.repository import SpecRepository

    return SpecRepository(ctx.worktree)


def module_block_at(worktree: Path, commit: str, path: str) -> dict:
    """The ``module`` block of the entry metadata ``path`` as it was at ``commit``, or an empty one
    when the file did not exist there; ``OSError`` or ``ValueError`` when it cannot be read."""

    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise OSError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
        return result.stdout

    if not git("ls-tree", "--name-only", commit, "--", path).strip():
        return {}
    return json.loads(git("show", f"{commit}:{path}")).get("module") or {}


def scaffold_writes(ctx: RunContext, repository, module: str) -> list[str]:
    """What a scaffold added to the surveyed Module since the workspace's base commit: every
    Module it contains and every external inclusion it has now that its entry metadata did not
    have then, the two additions a scaffold makes to the Module it applies a proposal to."""
    path = repository.module(module).entry + ".json"
    now = json.loads((ctx.worktree / path).read_text(encoding="utf-8"))["module"]
    before = module_block_at(ctx.worktree, ctx.base_commit, path)

    def contained(block: dict) -> set[str]:
        return {item["target"] for item in block.get("contains") or []}

    def external(block: dict) -> set[str]:
        return {
            item["target"]
            for item in block.get("includes") or []
            if item.get("kind") == "external"
        }

    return [
        f"{module} contains {target}"
        for target in sorted(contained(now) - contained(before))
    ] + [
        f"{module} includes the external {target}"
        for target in sorted(external(now) - external(before))
    ]


def specs_failure(ctx: RunContext, error: Exception, what: str, *, caused: bool = True):
    """The run's link when the Specs cannot be loaded for ``what``, with Spec core's error as its
    cause when ``caused``; otherwise the error is in the detail alone."""
    return ctx.fail(
        "failed",
        "specs_unloadable",
        "The worktree's Specs could not be loaded for the survey.",
        f"the Specs of {ctx.worktree} could not be loaded to {what}: "
        f"{getattr(error, 'code', type(error).__name__)}: {error}",
        reason="scope",
        explanation="a survey reads the code a Module binds, which only loadable Specs "
        "declare; repairing the Specs is outside a survey",
        evidence=[evidence("spec-load", ctx.worktree.as_posix(), str(error))],
        causes=[spec_cause(error)] if caused else [],
        options=["run concorde spec-validation to see why the Specs do not load"],
    )


def inventory(ctx: RunContext):
    """Step 1: exactly one surveyed Module, no scaffold's writes in a bound workspace, and every
    file the Module binds with its size, written to the run's inventory file."""
    from ...spec.repository_base import SpecError

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
    module = ctx.modules[0]
    try:
        repository = repository_of(ctx)
        installed = {
            entry
            for realization in repository.realizations(module)
            if realization.id.endswith(".concorde-installation")
            for entry in realization.entries
        }
        # Concorde's own installed files are no code to survey.
        files = [
            path for path in repository.bound_files(module) if path not in installed
        ]
    except (SpecError, OSError, ValueError) as error:
        return specs_failure(ctx, error, f"list the files of {module}")
    if not ctx.unbound:
        try:
            written = scaffold_writes(ctx, repository, module)
        except (SpecError, OSError, ValueError, KeyError, TypeError) as error:
            return specs_failure(
                ctx,
                error,
                f"compare {module}'s entry with the workspace's base commit "
                f"{ctx.base_commit}",
                caused=isinstance(error, SpecError),
            )
        if written:
            return ctx.fail(
                "failed",
                "fresh_workspace_required",
                f"A scaffold has already written to {module} in this workspace; revise the "
                "survey in a fresh workspace.",
                f"since the base commit {ctx.base_commit} of workspace {ctx.workspace_name}, "
                + "; ".join(written)
                + ", which a scaffold wrote; a survey proposes against the Module as it is, so "
                "a survey replayed here would propose against the narrowed Module and its new "
                "children, and nothing undoes what the scaffold wrote",
                reason="scope",
                explanation="revising a survey after its scaffold ran requires a fresh "
                "workspace; the survey never undoes or reconciles a scaffold's writes",
                evidence=[
                    evidence("scaffold-writes", module, item) for item in written
                ],
                options=[
                    (
                        "open a fresh task for the Module and run the survey or the "
                        "brownfield workflow there with the same answers"
                    ),
                    (
                        "keep this workspace and go on from its scaffold, describing the "
                        "created Modules with code_to_spec"
                    ),
                ],
            )
    ctx.state["files"] = [(path, lines_of(ctx.worktree / path)) for path in files]
    listing = ctx.run_dir / INVENTORY_FILE
    listing.write_text(
        "".join(f"{size:>7}  {path}\n" for path, size in ctx.state["files"]),
        encoding="utf-8",
    )
    ctx.state["inventory"] = listing
    return Continue(
        evidence=[
            evidence(
                "inventory",
                listing.as_posix(),
                f"{len(files)} bound file(s) of {module}, "
                f"{sum(size for _, size in ctx.state['files'])} line(s)",
            )
        ]
    )


def inventory_summary(files: list[tuple[str, int]]) -> str:
    """The inventory's totals and, per top-level directory or file, its files and lines."""
    groups: dict[str, list[int]] = {}
    for path, size in files:
        top = path.split("/", 1)[0] + ("/" if "/" in path else "")
        counts = groups.setdefault(top, [0, 0])
        counts[0] += 1
        counts[1] += size
    rows = "\n".join(
        f"{count:>7} file(s) {lines:>9} line(s)  {top}"
        for top, (count, lines) in sorted(groups.items())
    )
    return (
        f"{len(files)} file(s), {sum(size for _, size in files)} line(s) in all; by top-level "
        f"path:\n\n```text\n{rows}\n```\n"
    )


def instructions(ctx: RunContext, answers: list[dict]) -> str:
    module = ctx.modules[0]
    files = ctx.state["files"]
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
        f"The inventory of {module}: every file it binds, one per line with its size in lines, "
        f"is in the file {ctx.state['inventory'].as_posix()}, which you may read beside your "
        "grant. " + inventory_summary(files)
    )
    if answers:
        parts.append(
            "\nThe answers to earlier decisions and questions, which you must follow:\n\n```json\n"
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
        explanation="answers are settled above the task; the Operation never repairs or guesses them",
        evidence=[evidence("answers", error.path, str(error))],
        options=["correct the answers file and run the Operation again"],
    )


def propose(ctx: RunContext):
    """Step 2: the survey worker, reading code under a grant that writes nothing."""
    return run_worker(
        ctx,
        instructions(ctx, ctx.state["answers"]),
        task_type="code-to-spec",
        output_schema=SURVEY_WORKER_SCHEMA,
        checks=False,
        rounds=0,
        read_only=True,
        readable=(ctx.state["inventory"],),
    )


def relative_proposal(root: Path, claims: dict) -> dict:
    """The worker's proposal with every path inside the worktree written relative to it."""
    claims = copy.deepcopy(claims)
    for child in claims.get("children") or []:
        child["entries"] = [worktree_relative(root, path) for path in child["entries"]]
    for item in claims.get("externals") or []:
        item["path"] = worktree_relative(root, item["path"])
    for proposed in claims.get("checks") or []:
        proposed["inputs"] = [
            worktree_relative(root, path) for path in proposed["inputs"]
        ]
    for question in claims.get("open_questions") or []:
        question["evidence"] = [
            worktree_relative(root, path) for path in question["evidence"]
        ]
    return claims


def check(ctx: RunContext):
    """Step 3: the proposal fits the worktree and the answers; add the remaining entries."""
    module = ctx.modules[0]
    claims = relative_proposal(ctx.worktree, ctx.output or {})
    # The configuration names a directory input without the trailing `/` a realization entry
    # carries; the proposal is made to fit the configuration, not the other way round.
    for proposed in claims.get("checks") or []:
        proposed["inputs"] = [
            path.rstrip("/") if path.rstrip("/") else path
            for path in proposed["inputs"]
        ]
    answers = ctx.state.get("answers") or []
    claims["decisions"], problems = resolved_decisions(claims["decisions"], answers)
    repository = repository_of(ctx)
    existing = {check["id"] for check in configured_checks(repository.root)}
    problems += proposal_problems(repository, module, claims, existing)
    problems += evidence_problems(claims["open_questions"])
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
    replaced = narrowed_entries(
        ctx.worktree,
        parent_entries,
        child_entries,
        [item["path"] for item in claims["externals"]],
    )
    remaining = sorted({entry for items in replaced.values() for entry in items})
    output = {
        "module": module,
        "summary": claims["summary"],
        "children": claims["children"],
        "externals": claims["externals"],
        "remaining_entries": remaining,
        "checks": claims["checks"],
        "decisions": claims["decisions"],
        "open_questions": claims["open_questions"],
        "workflow": workflow_object(
            claims["decisions"],
            claims["open_questions"],
            checks=claims["checks"],
            survey=True,
        ),
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


SURVEY = operation(
    name="survey",
    task_type="code-to-spec",
    writes=False,
    steps=(inventory, propose, check),
    output_schema=DECOMPOSITION_SCHEMA,
    add_arguments=add_arguments,
    binding="optional",
)

__all__ = ["SURVEY"]
