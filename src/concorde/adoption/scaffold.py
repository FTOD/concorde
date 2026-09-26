"""The ``scaffold`` Operation: the host creates the child Modules one accepted survey proposed.

Steps (the Scaffold Operation step table of the Adoption Module Spec):

1. ``admit``: exactly one ``ok`` survey of the same task, admitted with ``--input``.
2. ``recheck``: validate the worktree as a baseline and check the proposal against it again.
3. ``plan``: compute every file change: child entries, the parent's entry and realizations and
   the registry. The proposal's checks are never configured.
4. ``apply``: write them as one file transaction, kept only if validation finds no new error.

No worker runs. Adding Modules is the project-level step the Protocol reserves for the registry
and the parent's ``contains``; every word the scaffold writes about a child comes from the survey.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    evidence,
    spec_cause,
    spec_finding,
)
from .records import (
    DECOMPOSITION_SCHEMA,
    SCAFFOLD_RECORD_SCHEMA,
    child_folder,
    narrowed_entries,
    proposal_problems,
)

# The sentence initialization writes into a root stub's Design section, which stops being true
# once the root contains children.
INIT_PARTS = (
    "The project's parts and their collaborations are not specified yet. This Module contains,\n"
    "uses and includes nothing, and no requirement or scenario has been written.\n"
)
SCAFFOLDED_PARTS = (
    "The parts below were proposed by a survey of the code; their collaborations are not\n"
    "specified yet, and no requirement or scenario has been written.\n"
)


def local(identity: str) -> str:
    """The part of a Module identity after ``module.``, as used in document and node identities."""
    return identity.split(".", 1)[1]


def anchor(identity: str) -> str:
    return local(identity).replace(".", "-")


def admit(ctx: RunContext):
    """Step 1: exactly one ok survey of this task."""
    surveys = {
        identity: value
        for identity, value in ctx.inputs.items()
        if value["operation"] == "survey"
    }
    if len(ctx.inputs) != 1 or len(surveys) != 1:
        given = (
            ", ".join(
                f"{identity} ({value['operation']})"
                for identity, value in ctx.inputs.items()
            )
            or "no --input"
        )
        return ctx.fail(
            "failed",
            "invalid_request",
            "The scaffold needs exactly one survey of its task as --input.",
            f"scaffold was given {given}; it applies exactly one proposal, from an ok survey run "
            f"of task {ctx.task.get('id')}",
            reason="input",
            explanation="the scaffold writes only what one survey proposed and never merges or "
            "guesses proposals",
            options=[
                "run scaffold again with --input naming one ok survey run of the task"
            ],
        )
    [(identity, value)] = surveys.items()
    from ..spec.schema import ContractError, validate

    try:
        validate(value["output"], DECOMPOSITION_SCHEMA)
    except ContractError as error:
        return ctx.fail(
            "failed",
            "invalid_request",
            f"The survey {identity} holds no valid decomposition proposal.",
            f"the output of survey run {identity} is not a contract.adoption.decomposition "
            f"value: {error}",
            reason="input",
            explanation="the scaffold applies only a proposal that satisfies its contract",
            options=["run survey again and scaffold its run"],
        )
    ctx.state["survey_run"] = identity
    ctx.state["proposal"] = value["output"]
    ctx.modules = [value["output"]["module"]]
    return Continue(evidence=[evidence("input", identity, "survey proposal admitted")])


def configured(worktree: Path) -> dict:
    return json.loads((worktree / ".concorde/config.json").read_text(encoding="utf-8"))


def recheck(ctx: RunContext):
    """Step 2: a baseline, and the proposal checked against the worktree as it is now."""
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import SpecError
    from ..spec.validation import validate_repository

    proposal = ctx.state["proposal"]
    module = proposal["module"]
    try:
        repository = SpecRepository(ctx.worktree)
        config = configured(ctx.worktree)
    except (SpecError, OSError, ValueError) as error:
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The task worktree's Specs could not be loaded for the scaffold.",
            f"the Specs of {ctx.worktree} could not be loaded before scaffolding: "
            f"{getattr(error, 'code', type(error).__name__)}: {error}",
            reason="scope",
            explanation="the scaffold changes Specs only from a loadable, validated state",
            evidence=[evidence("spec-load", ctx.worktree.as_posix(), str(error))],
            causes=[spec_cause(error)],
            options=["run validate for the task to see why the Specs do not load"],
        )
    problems = []
    if module not in repository.modules:
        problems.append(f"the surveyed Module {module} is no longer registered")
    else:
        problems += proposal_problems(
            repository,
            module,
            proposal,
            {check.get("id") for check in config.get("checks") or []},
        )
    if problems:
        return ctx.fail(
            "blocked",
            "stale_proposal",
            f"The survey's proposal no longer fits the task worktree ({len(problems)} "
            "mismatch(es)); nothing was written.",
            f"the proposal of survey {ctx.state['survey_run']} for {module} no longer fits "
            f"{ctx.worktree}: " + "; ".join(problems),
            reason="decision",
            explanation="the worktree changed since the survey; whether to survey again or "
            "undo the change is the main agent's decision",
            evidence=[evidence("mismatch", module, item) for item in problems],
            options=["run survey again and scaffold the new run"],
        )
    result = validate_repository(ctx.worktree)
    ctx.state["baseline"] = {
        (f.rule_id, f.source, f.message)
        for f in result.findings
        if f.severity == "error"
    }
    ctx.state["repository"] = repository
    ctx.state["config"] = config
    return Continue(
        evidence=[
            evidence(
                "baseline",
                result.status,
                f"{len(ctx.state['baseline'])} error(s) before the scaffold",
            )
        ]
    )


def child_reading(child: dict, titles: dict[str, str]) -> str:
    identity = child["id"]
    title = child["title"]
    purpose = " ".join(child["purpose"].split())
    uses = "".join(
        f'<a id="uses-{anchor(use["target"])}"></a>\n\n'
        f"{title} uses **{titles.get(use['target'], use['target'])}**, as the survey found: "
        f"{' '.join(use['reason'].split())} What it relies on is not specified yet.\n\n"
        for use in child["uses"]
    )
    return (
        f"# {title}\n\n## Purpose\n\n{purpose}\n\n"
        "## Terminology\n\nNo terms have been defined yet.\n\n"
        "## Usage\n\n"
        f"How {title} is used is not specified yet: its entry points, inputs, results, effects,\n"
        "errors and repeat behaviour are unknown.\n\n"
        "## Design\n\n"
        f"The design of {title} is not specified yet.\n\n"
        f'<a id="realization.{local(identity)}.code"></a>\n\n'
        f"The files a survey of the code assigned to {title} are bound to it as its code. Binding\n"
        "them describes nothing yet about what they do.\n\n"
        + (
            uses
            if uses
            else f"The collaborations of {title} are not specified yet; the survey found none.\n"
        )
    ).rstrip("\n") + "\n"


def external_includes(externals: list[dict], identity: str) -> list[dict]:
    """The external inclusions of vendored code used by ``identity``."""
    return [
        {"kind": "external", "target": item["path"], "reason": item["reason"]}
        for item in externals
        if item["used_by"] == identity
    ]


def child_metadata(child: dict, entry: str, externals: list[dict] = ()) -> dict:
    identity = child["id"]
    return {
        "schema_version": 3,
        "document": {
            "id": f"document.{local(identity)}.module",
            "owner": identity,
            "role": "module",
        },
        "module": {
            "title": child["title"],
            "owns": [entry],
            "contains": [],
            "uses": [
                {"target": use["target"], "meaning": f"#uses-{anchor(use['target'])}"}
                for use in child["uses"]
            ],
            "includes": external_includes(list(externals), identity),
            "participates": [],
        },
        "defines": [
            {
                "id": f"realization.{local(identity)}.code",
                "type": "realization",
                "title": "Code",
                "meaning": f"#realization.{local(identity)}.code",
                "entries": list(child["entries"]),
            }
        ],
        "relations": [],
        "extensions": {},
    }


def parent_reading(text: str, children: list[dict]) -> str:
    """The parent entry with one explaining paragraph per child at the end of Design."""
    paragraphs = "".join(
        f'<a id="contains-{anchor(child["id"])}"></a>\n\n'
        f"**{child['title']}**, proposed by a survey of the code: "
        f"{' '.join(child['purpose'].split())}\n\n"
        for child in children
    )
    text = text.replace(INIT_PARTS, SCAFFOLDED_PARTS, 1)
    lines = text.splitlines(keepends=True)
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == "## Design"),
        None,
    )
    if start is None:
        return text.rstrip("\n") + "\n\n## Design\n\n" + paragraphs.rstrip("\n") + "\n"
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    before = "".join(lines[:end]).rstrip("\n") + "\n\n"
    after = "".join(lines[end:])
    return before + paragraphs.rstrip("\n") + "\n" + ("\n" + after if after else "")


def parent_metadata(
    value: dict,
    children: list[dict],
    replaced: dict[str, list[str]],
    includes: list[dict] = (),
) -> dict:
    value = json.loads(json.dumps(value))
    value["module"]["contains"] = list(value["module"]["contains"]) + [
        {"target": child["id"], "meaning": f"#contains-{anchor(child['id'])}"}
        for child in children
    ]
    value["module"]["includes"] = list(value["module"].get("includes") or []) + list(
        includes
    )
    kept = []
    for record in value.get("defines") or []:
        if record.get("type") != "realization":
            kept.append(record)
            continue
        entries = list(
            dict.fromkeys(
                entry for old in record["entries"] for entry in replaced.get(old, [old])
            )
        )
        if not entries:
            continue
        record["entries"] = entries
        if record.get("pending"):
            record["pending"] = [
                entry for entry in record["pending"] if entry in entries
            ]
        kept.append(record)
    value["defines"] = kept
    return value


def plan(ctx: RunContext):
    """Step 3: every file change, computed from the proposal and the worktree alone."""
    from ..spec.changes import file_change
    from ..spec.registry import RECORD_FIELDS, serialize

    proposal = ctx.state["proposal"]
    repository = ctx.state["repository"]
    module = proposal["module"]
    parent = repository.modules[module]
    externals = list(proposal.get("externals") or [])
    # A child whose directory holds vendored code binds everything in it but that code.
    children = [
        {
            **child,
            "entries": sorted(
                {
                    entry
                    for items in narrowed_entries(
                        ctx.worktree,
                        child["entries"],
                        [],
                        [item["path"] for item in externals],
                    ).values()
                    for entry in items
                }
            ),
        }
        for child in proposal["children"]
    ]
    root = ctx.worktree
    titles = {identity: item.title for identity, item in repository.modules.items()}
    titles.update({child["id"]: child["title"] for child in children})
    before_entries = sorted(repository.realization_entries(module))
    # Vendored code leaves the parent's entries like a child's and becomes external material of
    # the Module that uses it.
    replaced = narrowed_entries(
        root,
        before_entries,
        [entry for child in children for entry in child["entries"]],
        [item["path"] for item in externals],
    )
    changes, created = [], []
    for child in children:
        entry = f"{child_folder(parent.entry, child['id'])}/module.md"
        for path in (entry, entry + ".json"):
            if (root / path).exists():
                return ctx.fail(
                    "blocked",
                    "stale_proposal",
                    f"{path} already exists; nothing was written.",
                    f"the scaffold would create {path} for {child['id']}, but it exists in "
                    f"{root}",
                    reason="decision",
                    explanation="the scaffold only creates documents; it never replaces one",
                    evidence=[evidence("exists", path, "")],
                    options=["remove the file or survey again with another identity"],
                )
        changes.append(file_change(root, entry, child_reading(child, titles)))
        changes.append(
            file_change(
                root,
                entry + ".json",
                json.dumps(
                    child_metadata(child, entry, externals),
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
            )
        )
        created.append(
            {
                "id": child["id"],
                "title": child["title"],
                "entry": entry,
                "entries": child["entries"],
            }
        )
    parent_includes = external_includes(externals, module)
    if children:
        parent_text = (root / parent.entry).read_text(encoding="utf-8")
        changes.append(
            file_change(root, parent.entry, parent_reading(parent_text, children))
        )
    if children or externals:
        parent_value = json.loads(
            (root / (parent.entry + ".json")).read_text(encoding="utf-8")
        )
        changes.append(
            file_change(
                root,
                parent.entry + ".json",
                json.dumps(
                    parent_metadata(parent_value, children, replaced, parent_includes),
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
            )
        )
        registry_path = repository.registry_path
        registry = json.loads((root / registry_path).read_text(encoding="utf-8"))
        for record in registry["modules"]:
            if record["id"] == module:
                record["contains"] = list(record["contains"]) + [
                    {
                        "target": child["id"],
                        "meaning": f"#contains-{anchor(child['id'])}",
                    }
                    for child in children
                ]
                record["includes"] = (
                    list(record.get("includes") or []) + parent_includes
                )
        for child, item in zip(children, created):
            block = child_metadata(child, item["entry"], externals)["module"]
            registry["modules"].append(
                {
                    "id": child["id"],
                    "title": child["title"],
                    "entry": item["entry"],
                    **{name: block[name] for name in RECORD_FIELDS[3:]},
                }
            )
        changes.append(file_change(root, registry_path, serialize(registry)))
    # The proposal's checks are never configured here: a command a model chose after reading
    # code runs only once the developer accepted it.
    after_entries = (
        sorted({entry for items in replaced.values() for entry in items})
        if children or externals
        else before_entries
    )
    ctx.state["changes"] = changes
    ctx.state["record"] = {
        "parent": module,
        "survey_run": ctx.state["survey_run"],
        "created": created,
        "externals": externals,
        "parent_entries_before": before_entries,
        "parent_entries_after": after_entries,
        "files_written": sorted(change["path"] for change in changes),
    }
    return Continue(
        evidence=[
            evidence(
                "scaffold-plan",
                module,
                f"{len(created)} Module(s), {len(changes)} file(s)",
            )
        ]
    )


def apply(ctx: RunContext):
    """Step 4: one file transaction, kept only when validation finds no new error."""
    from ..spec.changes import apply_files
    from ..spec.repository_base import SpecError
    from ..spec.validation import validate_repository

    changes = ctx.state["changes"]
    record = ctx.state["record"]
    if not changes:
        return Continue(
            output=record,
            evidence=[evidence("scaffold", record["parent"], "nothing to create")],
        )
    new: list = []

    def verify():
        result = validate_repository(ctx.worktree)
        new[:] = [
            f
            for f in result.findings
            if f.severity == "error"
            and (f.rule_id, f.source, f.message) not in ctx.state["baseline"]
        ]
        if new:
            raise SpecError(
                f"the scaffold would add {len(new)} structural error(s)",
                "scaffold_invalid",
            )

    folders = {Path(change["path"]).parent for change in changes}
    missing = {folder for folder in folders if not (ctx.worktree / folder).exists()}
    try:
        apply_files(
            ctx.worktree, changes, {change["path"] for change in changes}, verify=verify
        )
    except SpecError as error:
        for folder in sorted(missing, key=lambda item: len(item.parts), reverse=True):
            try:
                (ctx.worktree / folder).rmdir()
            except OSError:
                pass
        if error.code == "scaffold_invalid":
            listing = "; ".join(
                f"{f.rule_id} {f.source or ''}: {f.message}" for f in new
            )
            return ctx.fail(
                "failed",
                "scaffold_invalid",
                f"The scaffold would add {len(new)} structural error(s); nothing was kept.",
                f"writing the Modules proposed by survey {record['survey_run']} would leave "
                f"{len(new)} new structural error(s) in {ctx.worktree}, so every file was "
                f"restored: {listing}",
                reason="capability",
                explanation="the scaffold writes what the proposal says by fixed rules and has "
                "no means to repair a proposal whose Spec does not validate",
                evidence=[
                    evidence("new-error", f.rule_id, f"{f.source}: {f.message}")
                    for f in new
                ],
                causes=[
                    spec_finding(
                        f.rule_id,
                        f.source,
                        f.line,
                        f.message,
                        "validation diagnoses the Specs; it does not change them",
                    )
                    for f in new
                ],
                options=[
                    "run survey again with --goal naming the problem",
                    "report an Issue against the scaffold",
                ],
            )
        return ctx.fail(
            "blocked",
            "stale_proposal",
            f"The scaffold's files changed while it wrote them ({error.code}); nothing was kept.",
            f"the scaffold could not write its files in {ctx.worktree}: {error.code}: {error}",
            reason="decision",
            explanation="the worktree changed under the scaffold; every file was restored",
            causes=[spec_cause(error)],
            options=["run scaffold again once nothing else writes the task worktree"],
        )
    return Continue(
        output=record,
        evidence=[
            evidence(
                "scaffold",
                record["parent"],
                f"created {', '.join(item['id'] for item in record['created']) or 'nothing'}",
            )
        ],
    )


SCAFFOLD = Provider(
    name="scaffold",
    task_type=None,
    writes=True,
    steps=(admit, recheck, plan, apply),
    output_schema=SCAFFOLD_RECORD_SCHEMA,
    requires_loaded_specs=True,
)

__all__ = ["SCAFFOLD"]
