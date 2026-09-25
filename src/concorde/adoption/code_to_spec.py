"""The ``code_to_spec`` Operation: a worker reads the bound Modules' code and writes their Specs.

Steps (the Code to spec Operation step table of the Adoption Module Spec):

1. ``baseline``: validate the task worktree's Specs and remember their errors.
2. ``prepare``: create the ``requirements.md``, ``scenarios.md`` and ``contracts.md`` stubs a bound
   Module lacks, owned by it, and reconcile the registry mirror, before the grant is frozen.
3. ``describe``: the standard worker sequence for task type ``code-to-spec`` (grant, settings,
   brief, launch, audit, run record) with one round and no checks.
4. ``tidy``: remove the stubs the worker left unchanged and reconcile the registry mirror.

Steps 2 to 4 run as the one host step ``describe_code``, so that ``tidy`` runs in a ``finally``
however the worker step ends, an exception or a cancellation included.
5. ``revalidate``: validate again and split the errors into new and pre-existing ones.
6. ``observe``: the Spec description from the host's observations and the worker's claims, the
   answers check, and the status.
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
    load_prompt,
    protocol_guide,
    spec_cause,
    spec_finding,
)
from ..spec.repository_base import SpecError
from .records import (
    DESCRIBE_WORKER_SCHEMA,
    SPEC_DESCRIPTION_SCHEMA,
    AnswersError,
    answer_problems,
    load_answers,
    repeated_ids,
)
from .survey import answers_failure

STUBS = {
    "requirements.md": "requirements",
    "scenarios.md": "scenarios",
    "contracts.md": "contracts",
}


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", default="")
    parser.add_argument("--answers")


def key(finding) -> tuple:
    return (finding.rule_id, finding.source, finding.message)


def finding_value(finding) -> dict:
    return {
        "rule_id": finding.rule_id,
        "path": finding.source or None,
        "message": finding.message,
    }


def stub_text(title: str, kind: str) -> str:
    return (
        f"# {title} {kind}\n\n"
        f"The {kind} of [{title}](module.md) are not specified yet.\n"
    )


def baseline(ctx: RunContext):
    """Step 1: the errors before the change, and the answers."""
    from ..spec.validation import validate_repository

    try:
        ctx.state["answers"] = load_answers(ctx.arguments.answers)
    except AnswersError as error:
        return answers_failure(ctx, error)
    result = validate_repository(ctx.worktree)
    if any(f.rule_id == "CONCORDE-SOURCE-008" for f in result.findings):
        message = next(
            f.message for f in result.findings if f.rule_id == "CONCORDE-SOURCE-008"
        )
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The task worktree's Specs could not be loaded for the baseline.",
            f"the Specs of {ctx.worktree} could not be loaded before the description: {message}",
            reason="scope",
            explanation="a code_to_spec worker edits Spec documents under a grant computed from "
            "loadable Specs; repairing the configuration or registry is outside it",
            evidence=[evidence("spec-load", ctx.worktree.as_posix(), message)],
            options=["run validate for the task to see why the Specs do not load"],
        )
    ctx.state["baseline"] = {key(f) for f in result.findings if f.severity == "error"}
    return Continue(
        evidence=[
            evidence(
                "baseline",
                result.status,
                f"{len(ctx.state['baseline'])} error(s) before the change",
            )
        ]
    )


def prepare(ctx: RunContext):
    """Step 2: the implementation document stubs each bound Module lacks, owned by it."""
    from ..spec.changes import apply_files, file_change
    from ..spec.registry import registry_command
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError

    try:
        repository = SpecRepository(ctx.worktree)
    except (SpecError, OSError, ValueError) as error:
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The task worktree's Specs could not be loaded to prepare the documents.",
            f"the Specs of {ctx.worktree} could not be loaded: {error}",
            reason="scope",
            explanation="the host prepares documents only in loadable Specs",
            causes=[spec_cause(error)],
            options=["run validate for the task to see why the Specs do not load"],
        )
    unknown = [module for module in ctx.modules if module not in repository.modules]
    if unknown:
        return ctx.fail(
            "failed",
            "unknown_modules",
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not registered.",
            f"code_to_spec was bound to {', '.join(unknown)}, which the Specs of "
            f"{ctx.worktree} do not register (registered: {', '.join(sorted(repository.modules))})",
            reason="input",
            explanation="a Module must exist before its code can be described; the scaffold "
            "creates Modules, code_to_spec never does",
            options=["run scaffold first, or bind registered Modules"],
        )
    changes, stubs = [], []
    for module in ctx.modules:
        item = repository.modules[module]
        folder = item.entry.rsplit("/", 1)[0]
        metadata_path = item.entry + ".json"
        ctx.state.setdefault("metadata", {})[module] = metadata_path
        metadata = json.loads(
            (ctx.worktree / metadata_path).read_text(encoding="utf-8")
        )
        owned = list(metadata["module"]["owns"])
        added = []
        for name, kind in STUBS.items():
            path = f"{folder}/{name}"
            if path in owned or (ctx.worktree / path).exists():
                continue
            changes.append(file_change(ctx.worktree, path, stub_text(item.title, kind)))
            changes.append(
                file_change(
                    ctx.worktree,
                    path + ".json",
                    json.dumps(
                        {
                            "schema_version": 3,
                            "document": {
                                "id": f"document.{module.split('.', 1)[1]}.{kind}",
                                "owner": module,
                                "role": "implementation",
                            },
                            "defines": [],
                            "relations": [],
                            "extensions": {},
                        },
                        indent=2,
                    )
                    + "\n",
                )
            )
            added.append(path)
        if added:
            metadata["module"]["owns"] = owned + added
            changes.append(
                file_change(
                    ctx.worktree,
                    metadata_path,
                    json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
                )
            )
            stubs += [(module, path) for path in added]
    if changes:
        apply_files(ctx.worktree, changes, {change["path"] for change in changes})
        registry_command(ctx.worktree, write=True)
    ctx.state["stubs"] = {
        path: (module, (ctx.worktree / path).read_bytes()) for module, path in stubs
    }
    return Continue(
        evidence=[
            evidence("stubs", "", ", ".join(path for _, path in stubs) or "none needed")
        ]
    )


def instructions(ctx: RunContext) -> str:
    from ..spec.repository import SpecRepository

    repository = SpecRepository(ctx.worktree)
    modules = "\n".join(
        f"- {identity}: {item.title}"
        for identity, item in sorted(repository.modules.items())
    )
    parts = [
        load_prompt("code-to-spec").strip(),
        "\n\n## This run\n\n",
        f"Modules to describe: {', '.join(ctx.modules)}\n\n",
        f"Registered Modules, which your `uses` may name:\n\n{modules}\n\n",
    ]
    if ctx.arguments.goal:
        parts.append(
            f"What the main agent asks you to pay attention to: {ctx.arguments.goal}\n\n"
        )
    stubs = ctx.state.get("stubs") or {}
    if stubs:
        parts.append(
            "Implementation document stubs prepared for you, removed again if you leave them "
            "unchanged: " + ", ".join(sorted(stubs)) + "\n"
        )
    answers = ctx.state.get("answers") or []
    if answers:
        parts.append(
            "\nThe developer's answers, which you must follow:\n\n```json\n"
            + json.dumps(answers, indent=2, ensure_ascii=False)
            + "\n```\n"
        )
    if ctx.inputs:
        parts.append(
            "\nAdmitted inputs (outputs of earlier ok runs of this task):\n\n```json\n"
            + json.dumps(ctx.inputs, indent=2, ensure_ascii=False)
            + "\n```\n"
        )
    parts.append(protocol_guide(ctx.worktree))
    return "".join(parts)


def describe(ctx: RunContext):
    """Step 3: the worker. It never stops the run itself, so that ``tidy`` removes the stubs on
    every way out; ``observe`` returns what stopped it."""
    from ..harness.runs import read_record

    outcome = ctx.run_worker(
        instructions(ctx),
        task_type="code-to-spec",
        output_schema=DESCRIBE_WORKER_SCHEMA,
        checks=False,
        rounds=0,
    )
    if isinstance(outcome, Stop):
        ctx.state["stop"] = outcome
    if not ctx.worker_runs:
        # No worker ran (the grant or the model could not be settled): nothing to observe.
        ctx.state["unobserved"] = True
        return Continue(evidence=outcome.evidence)
    record = read_record(ctx.primary, ctx.worker_runs[-1])
    ctx.state["record"] = record
    ctx.state["unobserved"] = any(
        (item.get("audit") or {}).get("verdict") == "violation"
        for item in record.get("rounds") or []
    ) or any(error["code"] == "audit_violation" for error in record.get("errors") or [])
    return Continue(evidence=outcome.evidence)


def tidy(ctx: RunContext):
    """Step 4: remove the stubs left unchanged, and reconcile the registry mirror."""
    from ..spec.changes import apply_files, file_change
    from ..spec.registry import registry_command

    unchanged = [
        (module, path)
        for path, (module, content) in (ctx.state.get("stubs") or {}).items()
        if (ctx.worktree / path).is_file()
        and (ctx.worktree / path).read_bytes() == content
    ]
    by_module: dict[str, list[str]] = {}
    for module, path in unchanged:
        by_module.setdefault(module, []).append(path)
    notes = []
    for module, paths in by_module.items():
        # The entry's metadata path was noted when the stubs were prepared: the worker may have
        # left the Specs unloadable, and the stubs must go all the same.
        metadata_path = ctx.state["metadata"][module]
        try:
            metadata = json.loads(
                (ctx.worktree / metadata_path).read_text(encoding="utf-8")
            )
            metadata["module"]["owns"] = [
                path for path in metadata["module"]["owns"] if path not in paths
            ]
            apply_files(
                ctx.worktree,
                [
                    file_change(
                        ctx.worktree,
                        metadata_path,
                        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
                    )
                ],
                {metadata_path},
            )
        except (OSError, ValueError, KeyError, TypeError, SpecError) as error:
            notes.append(
                evidence(
                    "owns-not-updated",
                    metadata_path,
                    f"the stubs were removed but {metadata_path} could not be updated: {error}",
                )
            )
        for path in paths:
            (ctx.worktree / path).unlink(missing_ok=True)
            (ctx.worktree / (path + ".json")).unlink(missing_ok=True)
    ctx.state["removed"] = sorted(path for _, path in unchanged)
    result = registry_command(ctx.worktree, write=True)
    return Continue(
        evidence=notes
        + [
            evidence("stubs-removed", "", ", ".join(ctx.state["removed"]) or "none"),
            evidence("registry", result.status, ""),
        ]
    )


def describe_code(ctx: RunContext):
    """Steps 2 to 7 as one step: prepare the stubs, run the worker, and remove the stubs left
    unchanged however the worker step ends, an exception or a cancellation included."""
    prepared = prepare(ctx)
    if isinstance(prepared, Stop):
        return prepared
    found = list(prepared.evidence)
    try:
        found += describe(ctx).evidence
    finally:
        found += tidy(ctx).evidence
    return Continue(evidence=found)


def revalidate(ctx: RunContext):
    """Step 5: new and pre-existing structural errors."""
    from ..spec.validation import validate_repository

    result = validate_repository(ctx.worktree)
    errors = [f for f in result.findings if f.severity == "error"]
    ctx.state["new"] = [f for f in errors if key(f) not in ctx.state["baseline"]]
    ctx.state["old"] = [f for f in errors if key(f) in ctx.state["baseline"]]
    return Continue(
        evidence=[
            evidence(
                "validation",
                result.status,
                f"{len(ctx.state['new'])} new error(s), {len(ctx.state['old'])} pre-existing",
            )
        ]
    )


def observe(ctx: RunContext):
    """Step 6: the Spec description, the consistency of the claims, and the status."""
    stop = ctx.state.get("stop")
    if stop is not None and ctx.state.get("unobserved"):
        # A write outside the grant, or no worker at all: nothing the worker did is reported.
        return stop
    record = ctx.state.get("record") or {}
    changed = sorted(
        {
            path
            for item in record.get("rounds") or []
            for path in (item.get("audit") or {}).get("changed", [])
        }
    )
    stubs = ctx.state.get("stubs") or {}
    removed = ctx.state.get("removed") or []
    claims = ((record.get("worker_result") or {}).get("output")) or {}
    output = {
        "modules": list(ctx.modules),
        "summary": claims.get("summary")
        or (record.get("worker_result") or {}).get("summary")
        or "The worker gave no account of its description.",
        "changed_documents": changed,
        "created_documents": sorted(path for path in stubs if path not in removed),
        "removed_stubs": removed,
        "promises": claims.get("promises", []),
        "decisions": claims.get("decisions", []),
        "open_questions": claims.get("open_questions", []),
        "deviations": claims.get("deviations", []),
        "validation": {
            "new_errors": [finding_value(f) for f in ctx.state["new"]],
            "preexisting_errors": len(ctx.state["old"]),
        },
    }
    ctx.output = output
    found = [
        evidence(
            "spec-description",
            "",
            f"{len(changed)} changed, {len(output['created_documents'])} stub(s) filled, "
            f"{len(removed)} removed; {len(output['open_questions'])} open question(s)",
        )
    ]
    if stop is not None:
        return Stop(stop.status, stop.summary, found, stop.error)
    new = ctx.state["new"]
    if new:
        listing = "; ".join(f"{f.rule_id} {f.source or ''}: {f.message}" for f in new)
        return ctx.fail(
            "blocked",
            "new_structural_errors",
            f"The description introduced {len(new)} structural error(s); the edits stay in the "
            "task worktree.",
            f"after the worker described {', '.join(ctx.modules)} the task's Specs have "
            f"{len(new)} new structural error(s): {listing}",
            reason="decision",
            explanation="code_to_spec runs its worker once and never repairs a Spec "
            "automatically; whether to repair, rerun or discard the edits is the main agent's "
            "decision",
            evidence=found,
            causes=[
                spec_finding(
                    f.rule_id,
                    f.source,
                    getattr(f, "line", None),
                    f.message,
                    "validation diagnoses the Specs; it does not change them",
                )
                for f in new
            ],
            options=[
                "repair the documents by hand",
                "run code_to_spec again with a --goal naming the problem",
                "discard the edits",
            ],
        )
    problems = []
    for item in (
        output["promises"]
        + output["decisions"]
        + output["open_questions"]
        + output["deviations"]
    ):
        if item["module"] not in ctx.modules:
            problems.append(
                f"{item.get('id') or item.get('question') or item['description']!s} names "
                f"{item['module']}, which this run did not describe"
            )
    for item in output["promises"]:
        if item["source"] == "answer" and not item.get("question"):
            problems.append(
                f"promise {item.get('id') or item['description']!r} has source answer but names "
                "no question"
            )
    for decision in output["decisions"]:
        if (
            decision["decided_by"] == "worker"
            and decision["chosen"] not in decision["options"]
        ):
            problems.append(
                f"decision {decision['id']} chose {decision['chosen']!r}, which is none of its "
                "options"
            )
    problems += repeated_ids(output["decisions"], "decision")
    problems += repeated_ids(output["open_questions"], "open question")
    problems += answer_problems(
        ctx.state.get("answers") or [],
        output["decisions"],
        output["promises"],
        output["deviations"],
    )
    if problems:
        ctx.output = None
        return ctx.fail(
            "failed",
            "inconsistent_description",
            f"The worker's description is inconsistent ({len(problems)} problem(s)).",
            f"the description of {', '.join(ctx.modules)} is inconsistent: "
            + "; ".join(problems),
            reason="capability",
            explanation="the host checks the worker's account but never corrects it or "
            "relaunches the worker; the edits stay in the task worktree",
            evidence=found + [evidence("inconsistency", "", item) for item in problems],
            options=[
                "run code_to_spec again",
                "inspect the worker's claims in the result",
            ],
        )
    return Continue(output=output, evidence=found)


CODE_TO_SPEC = Provider(
    name="code_to_spec",
    task_type="code-to-spec",
    writes=True,
    steps=(baseline, describe_code, revalidate, observe),
    output_schema=SPEC_DESCRIPTION_SCHEMA,
    add_arguments=add_arguments,
)

__all__ = ["CODE_TO_SPEC"]
