"""The records Adoption's Operations share: schemas, answers, and the checks of a proposal.

The schemas are the contracts of ``specs/concorde/execution/operations/adoption/contracts.md``; the tests
hold them equal. ``proposal_problems`` is the one check of a decomposition proposal against a
worktree, used by the survey after its worker and by the scaffold again before it writes, and
``narrowed_entries`` is the one rule by which a parent's realization entries lose the paths its
children take.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ...spec.repository_base import (
    IDENTITY,
    SpecError,
    bound_by,
    covers,
    entry_base,
    expand_entry,
    is_directory_entry,
    skipped_path,
)
from ...spec.schema import ContractError, validate
from ...spec.typed_data import TypedDataError, checked_path, safe_path
from ...workflows.output import step_output

S = {"type": "string", "minLength": 1}
MODULE_ID = {
    "type": "string",
    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$",
}
DECISION_ID = {"type": "string", "pattern": "^d\\.[a-z0-9-]+$"}
QUESTION_ID = {"type": "string", "pattern": "^q\\.[a-z0-9-]+$"}


def obj(properties: dict, required=None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties if required is None else required),
        "properties": properties,
    }


DECISION = obj(
    {
        "id": DECISION_ID,
        "module": MODULE_ID,
        "question": S,
        "options": {"type": "array", "minItems": 2, "items": S},
        "chosen": S,
        "reason": S,
        "decided_by": {"enum": ["worker", "main-agent", "developer"]},
    }
)
OPTION_ID = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"}
# A decision as the worker claims it: each option named by an identity of the worker's, and the
# choice by that identity, so that nobody copies an option's text; the host writes ``DECISION``.
WORKER_DECISION = obj(
    {
        "id": DECISION_ID,
        "module": MODULE_ID,
        "question": S,
        "options": {
            "type": "array",
            "minItems": 2,
            "items": obj({"id": OPTION_ID, "text": S}),
        },
        "chosen": {"anyOf": [OPTION_ID, {"type": "null"}]},
        "reason": S,
    }
)
QUESTION = obj(
    {
        "id": QUESTION_ID,
        "module": MODULE_ID,
        "subject": S,
        "observed": S,
        "evidence": {"type": "array", "minItems": 1, "items": S},
        "why_uncertain": S,
        "options": {"type": "array", "minItems": 1, "items": S},
        "recommendation": S,
    }
)
FINDING = obj(
    {
        "rule_id": S,
        "path": {"anyOf": [S, {"type": "null"}]},
        "message": S,
    }
)
CHECK = obj(
    {
        "id": {
            "type": "string",
            "pattern": "^check\\.[a-z0-9-]+(?:\\.[a-z0-9-]+)*$",
        },
        "module": MODULE_ID,
        "argv": {"type": "array", "minItems": 1, "items": S},
        "env": {"type": "object", "additionalProperties": S},
        "when": {"enum": ["always", "readiness"]},
        "timeout_seconds": {"type": "integer", "minimum": 1},
        "inputs": {"type": "array", "items": S},
        "reason": S,
    },
    required=["id", "module", "argv", "timeout_seconds", "inputs", "reason"],
)
# Third-party code the project vendors: material a Module reads, never a Module.
EXTERNAL = obj({"path": S, "used_by": MODULE_ID, "reason": S})
CHILD = obj(
    {
        "id": MODULE_ID,
        "title": S,
        "purpose": S,
        "entries": {"type": "array", "minItems": 1, "items": S},
        "uses": {
            "type": "array",
            "items": obj({"target": MODULE_ID, "reason": S}),
        },
    }
)

# What the survey worker claims: the proposal without the entries the host computes.
SURVEY_WORKER_SCHEMA = obj(
    {
        "summary": S,
        "children": {"type": "array", "items": CHILD},
        "externals": {"type": "array", "items": EXTERNAL},
        "checks": {"type": "array", "items": CHECK},
        "decisions": {"type": "array", "items": WORKER_DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
    }
)
# The workflow object of the step output convention, whose own contract defines its fields.
WORKFLOW = {"type": "object"}
# contract.adoption.decomposition, version 7
DECOMPOSITION_SCHEMA = obj(
    {
        "module": MODULE_ID,
        "summary": S,
        "children": {"type": "array", "items": CHILD},
        "externals": {"type": "array", "items": EXTERNAL},
        "remaining_entries": {"type": "array", "items": S},
        "checks": {"type": "array", "items": CHECK},
        "decisions": {"type": "array", "items": DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
        "workflow": WORKFLOW,
    }
)
PROMISE = obj(
    {
        "module": MODULE_ID,
        "kind": {
            "enum": [
                "requirement",
                "scenario",
                "contract",
                "concept",
                "realization",
                "relation",
                "explanation",
            ]
        },
        "id": {"anyOf": [S, {"type": "null"}]},
        "description": S,
        "source": {"enum": ["code", "answer"]},
        "question": {"anyOf": [QUESTION_ID, {"type": "null"}]},
        "tests": {"type": "array", "items": S},
    },
    required=["module", "kind", "id", "description", "source", "question"],
)
TEST_LINK = obj({"scenario": S, "test": S})
UNLINKED_TEST = obj(
    {"scenario": {"anyOf": [S, {"type": "null"}]}, "test": S, "reason": S}
)
DEVIATION = obj(
    {"module": MODULE_ID, "question": QUESTION_ID, "intended": S, "observed": S}
)
# What the code_to_spec worker claims.
DESCRIBE_WORKER_SCHEMA = obj(
    {
        "summary": S,
        "promises": {"type": "array", "items": PROMISE},
        "decisions": {"type": "array", "items": WORKER_DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
        "deviations": {"type": "array", "items": DEVIATION},
    }
)
# contract.adoption.spec-description, version 5
SPEC_DESCRIPTION_SCHEMA = obj(
    {
        "modules": {"type": "array", "minItems": 1, "items": MODULE_ID},
        "summary": S,
        "changed_documents": {"type": "array", "items": S},
        "created_documents": {"type": "array", "items": S},
        "removed_stubs": {"type": "array", "items": S},
        "promises": {"type": "array", "items": PROMISE},
        "decisions": {"type": "array", "items": DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
        "deviations": {"type": "array", "items": DEVIATION},
        "linked_tests": {"type": "array", "items": TEST_LINK},
        "unlinked_tests": {"type": "array", "items": UNLINKED_TEST},
        "validation": obj(
            {
                "new_errors": {"type": "array", "items": FINDING},
                "preexisting_errors": {"type": "integer", "minimum": 0},
            }
        ),
        "workflow": WORKFLOW,
    }
)
# contract.adoption.answers, version 3
ANSWERS_SCHEMA = obj(
    {
        "answers": {
            "type": "array",
            "minItems": 1,
            "items": obj(
                {
                    "id": {"type": "string", "pattern": "^[dq]\\.[a-z0-9-]+$"},
                    "question": S,
                    "answer": S,
                    "answered_by": {"enum": ["main-agent", "developer"]},
                }
            ),
        }
    }
)


def workflow_object(
    decisions: list[dict],
    questions: list[dict],
    deviations: list[dict] = (),
    checks: list[dict] = (),
    *,
    survey: bool,
) -> dict:
    """What a survey or code_to_spec run declares under Workflows' step output convention
    (req.adoption.step-output): every open question, and for a survey every decision its worker
    took itself, as a decision point; every decision; every deviation; and, for a survey, every
    proposed check as a note."""
    points = [
        {
            "id": item["id"],
            "kind": "question",
            "question": f"{item['subject']}: {item['observed']}",
            "options": list(item["options"]),
            "recommendation": item["recommendation"],
            "module": item["module"],
        }
        for item in questions
    ]
    if survey:
        points += [
            {
                "id": item["id"],
                "kind": "decision",
                "question": item["question"],
                "options": list(item["options"]),
                "recommendation": f"the worker chose {item['chosen']!r}: {item['reason']}",
                "module": item["module"],
            }
            for item in decisions
            if item["decided_by"] == "worker"
        ]
    return step_output(
        decision_points=points,
        decisions=[
            {
                "id": item["id"],
                "question": item["question"],
                "options": list(item["options"]),
                "decision": item["chosen"],
                "reason": item["reason"],
                "decided_by": item["decided_by"],
                "module": item["module"],
            }
            for item in decisions
        ],
        deviations=[
            {
                "subject": f"the answer to {item['question']}",
                "intended": item["intended"],
                "observed": item["observed"],
                "point": item["question"],
                "module": item["module"],
            }
            for item in deviations
        ],
        notes=[
            {
                "kind": "proposed-check",
                "text": f"{item['id']} for {item['module']}: {item['reason']}",
                "data": item,
            }
            for item in checks
        ],
    )


class AnswersError(ValueError):
    """An answers file that cannot be read or does not satisfy its contract."""

    def __init__(self, path: str, message: str):
        super().__init__(f"{path}: {message}")
        self.path = path


def load_answers(path: str | None) -> list[dict]:
    """The answers of ``--answers``, or none; ``AnswersError`` names what is wrong."""
    if not path:
        return []
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise AnswersError(path, f"cannot be read as JSON: {error}") from error
    try:
        validate(value, ANSWERS_SCHEMA)
    except ContractError as error:
        raise AnswersError(
            path, f"is not a contract.adoption.answers value: {error}"
        ) from error
    identities = [item["id"] for item in value["answers"]]
    repeated = sorted({item for item in identities if identities.count(item) > 1})
    if repeated:
        raise AnswersError(path, f"answers {', '.join(repeated)} more than once")
    return value["answers"]


def resolved_decisions(
    claimed: list[dict], answers: list[dict]
) -> tuple[list[dict], list[str]]:
    """The decisions of the output from the worker's claims, and every claim that names no
    option it lists.

    The worker names each option by an identity and its choice by that identity, so the host
    alone writes the chosen option's text and ``decided_by``. A decision an answer settles takes
    the answer as its choice, decided by whoever gave it, whatever the worker named.
    """
    by_answer = {item["id"]: item for item in answers if item["id"].startswith("d.")}
    decisions, problems = [], []
    for claim in claimed:
        texts = {option["id"]: option["text"] for option in claim["options"]}
        identities = [option["id"] for option in claim["options"]]
        repeated = sorted({item for item in identities if identities.count(item) > 1})
        if repeated:
            problems.append(
                f"decision {claim['id']} gives more than one option the identity "
                f"{', '.join(repeated)}"
            )
        answer = by_answer.get(claim["id"])
        if answer is not None:
            chosen, decided_by = answer["answer"], answer["answered_by"]
        elif claim["chosen"] is None:
            problems.append(
                f"decision {claim['id']} chose no option, but no answer settles it"
            )
            continue
        elif claim["chosen"] not in texts:
            problems.append(
                f"decision {claim['id']} chose {claim['chosen']!r}, which names none of its "
                f"options ({', '.join(identities)})"
            )
            continue
        else:
            chosen, decided_by = texts[claim["chosen"]], "worker"
        decisions.append(
            {
                "id": claim["id"],
                "module": claim["module"],
                "question": claim["question"],
                "options": [option["text"] for option in claim["options"]],
                "chosen": chosen,
                "reason": claim["reason"],
                "decided_by": decided_by,
            }
        )
    return decisions, problems


def worktree_relative(root: Path, path: str) -> str:
    """``path`` relative to the worktree ``root`` when it starts with the worktree's absolute
    path, as given or as its real path, and otherwise unchanged.

    A worker's tools take absolute paths, so a path it writes into its result may carry the
    worktree's own path in front; removing that prefix is unambiguous. What follows the path,
    such as ``::test`` or a line number, and a trailing ``/`` are kept.
    """
    for prefix in dict.fromkeys((Path(root).as_posix(), os.path.realpath(root))):
        if path.startswith(prefix + "/") and len(path) > len(prefix) + 1:
            return path[len(prefix) + 1 :]
    return path


def answer_problems(
    answers: list[dict], decisions: list[dict], promises: list[dict] = ()
) -> list[str]:
    """Every answer an output does not follow, one sentence each.

    A decision answer (``d.``) is followed by a decision with its identity, which
    ``resolved_decisions`` records with the answer as its choice. A question answer (``q.``) is
    followed by a promise with source ``answer`` naming the question; a deviation naming it never
    replaces that promise, it only adds that the code does otherwise.
    """
    problems = []
    by_decision = {item["id"]: item for item in decisions}
    for answer in answers:
        identity = answer["id"]
        if identity.startswith("d."):
            if identity not in by_decision:
                problems.append(
                    f"the answer to {identity} ({answer['answer']!r}) has no decision "
                    f"{identity} in the output"
                )
        elif not any(
            item.get("source") == "answer" and item.get("question") == identity
            for item in promises
        ):
            problems.append(
                f"the answer to {identity} ({answer['answer']!r}) appears in no promise with "
                "source answer, which every answered question needs even when a deviation "
                "names it"
            )
    return problems


def repeated_ids(items: list[dict], label: str) -> list[str]:
    identities = [item["id"] for item in items]
    return [
        f"{label} {identity} appears {identities.count(identity)} times"
        for identity in sorted(set(identities))
        if identities.count(identity) > 1
    ]


def normalized(title: str) -> str:
    return " ".join(title.casefold().replace("-", " ").replace("_", " ").split())


def child_folder(parent_entry: str, child_id: str) -> str:
    """The folder of a child's documents: the parent entry's folder plus the identity's last
    segment."""
    folder = parent_entry.rsplit("/", 1)[0]
    return f"{folder}/{child_id.split('.')[-1]}"


def covered_by_parent(root: Path, parent_entries: list[str], entry: str) -> bool:
    """Whether an existing child entry lies within the paths the parent's entries bind.

    The entry is reached through no symbolic link, as the Spec tooling reaches every bound path,
    and a directory entry lies in no directory the exclusion rule skips below the parent's
    directory entry, since the parent never bound the files of such a directory.
    """
    try:
        path = checked_path(root, entry_base(entry))
    except SpecError:
        return False
    if is_directory_entry(entry):
        if not path.is_dir():
            return False
        return any(
            is_directory_entry(parent)
            and entry.startswith(parent)
            and not skipped_path(entry[len(parent) :] + "x")
            for parent in parent_entries
        )
    if not path.is_file():
        return False
    return any(bound_by(parent, entry) for parent in parent_entries)


def evidence_problems(questions: list[dict]) -> list[str]:
    """Every open question's evidence that names an absolute path, which after
    ``worktree_relative`` lies outside the worktree; a line suffix such as ``:12`` is allowed."""
    return [
        f"open question {question['id']}'s evidence {item!r} is an absolute path outside the "
        "worktree; evidence names project-relative paths"
        for question in questions
        for item in question.get("evidence") or []
        if item.startswith("/")
    ]


def proposal_problems(
    repository, module: str, proposal: dict, configured_check_ids: set[str]
) -> list[str]:
    """Every way a proposal does not fit the worktree ``repository`` was loaded from.

    ``proposal`` has at least ``children``, ``checks``, ``decisions`` and ``open_questions``.
    """
    root = Path(repository.root)
    problems: list[str] = []
    registered = set(repository.modules)
    titles = {
        normalized(repository.module(identity).title): identity
        for identity in registered
    }
    parent_entry = repository.module(module).entry
    parent_entries = sorted(repository.realization_entries(module))
    # The files the Concorde installer placed stay with the Module that binds them: they are not
    # the project's code, and the installer replaces them.
    installed = [
        entry
        for realization in repository.realizations(module)
        if realization.id.endswith(".concorde-installation")
        for entry in realization.entries
    ]
    children = proposal["children"]
    child_ids = [child["id"] for child in children]
    for child in children:
        identity = child["id"]
        if not IDENTITY.fullmatch(identity):
            problems.append(f"child identity {identity!r} is not a valid identity")
        if identity in registered:
            problems.append(f"child {identity} is already a registered Module")
        if child_ids.count(identity) > 1:
            problems.append(f"child {identity} is proposed more than once")
        title = normalized(child["title"])
        if title in titles:
            problems.append(
                f"child {identity}'s title {child['title']!r} is already the title of "
                f"{titles[title]}"
            )
        if [normalized(item["title"]) for item in children].count(title) > 1:
            problems.append(f"the title {child['title']!r} is proposed more than once")
        folder = child_folder(parent_entry, identity)
        siblings = [
            item["id"]
            for item in children
            if item["id"] != identity
            and child_folder(parent_entry, item["id"]) == folder
        ]
        if siblings:
            problems.append(
                f"child {identity}'s folder {folder}/ is also the folder of "
                f"{', '.join(siblings)}; the last segments of child identities must differ"
            )
        if (root / folder).exists():
            problems.append(
                f"child {identity}'s folder {folder}/ already exists in the worktree"
            )
        for entry in child["entries"]:
            taken = [path for path in installed if covers(entry, path)]
            if taken:
                problems.append(
                    f"child {identity}'s entry {entry} takes files of the Concorde "
                    f"installation ({', '.join(taken)}), which stay with {module}"
                )
            if not covered_by_parent(root, parent_entries, entry):
                problems.append(
                    f"child {identity}'s entry {entry} does not exist or is not bound by "
                    f"{module} (its entries: {', '.join(parent_entries) or 'none'})"
                )
        for use in child["uses"]:
            target = use["target"]
            if target == identity:
                problems.append(f"child {identity} uses itself")
            elif target not in child_ids and target not in registered:
                problems.append(
                    f"child {identity} uses {target}, which is neither another child nor a "
                    "registered Module"
                )
    child_entries = [entry for child in children for entry in child["entries"]]
    external_paths = [item["path"] for item in proposal.get("externals") or []]
    for item in proposal.get("externals") or []:
        path = item["path"]
        if item["used_by"] != module and item["used_by"] not in child_ids:
            problems.append(
                f"external {path} is used by {item['used_by']}, which is neither {module} nor "
                "a proposed child"
            )
        if not covered_by_parent(root, parent_entries, path):
            problems.append(
                f"external {path} is not an existing path that {module}'s realizations bind"
            )
        # Vendored code inside a child's directory narrows that child; a child that would
        # bind the vendored code itself, or part of it, is a problem.
        if [
            entry
            for entry in child_entries
            if entry == path or covers(path, entry.rstrip("/"))
        ]:
            problems.append(
                f"external {path} overlaps a child's entries; vendored code is read, never "
                "bound"
            )
        if [entry for entry in installed if covers(path, entry)]:
            problems.append(
                f"external {path} takes files of the Concorde installation, which stay with "
                f"{module}"
            )
        if external_paths.count(path) > 1:
            problems.append(f"external {path} is proposed more than once")
    check_ids = [check["id"] for check in proposal["checks"]]
    for check in proposal["checks"]:
        for path in check["inputs"]:
            try:
                safe_path(path, f"/checks/{check['id']}/inputs")
            except TypedDataError:
                problems.append(
                    f"check {check['id']} input {path!r} is not a canonical project-relative "
                    "path, as a configured check's inputs must be"
                )
        if check["module"] != module and check["module"] not in child_ids:
            problems.append(
                f"check {check['id']} is for {check['module']}, which is neither {module} "
                "nor a proposed child"
            )
        if check["id"] in configured_check_ids:
            problems.append(f"check {check['id']} is already configured")
        if check_ids.count(check["id"]) > 1:
            problems.append(f"check {check['id']} is proposed more than once")
    for decision in proposal["decisions"]:
        if (
            decision["decided_by"] == "worker"
            and decision["chosen"] not in decision["options"]
        ):
            problems.append(
                f"decision {decision['id']} chose {decision['chosen']!r}, which is none of "
                "its options"
            )
    problems += repeated_ids(proposal["decisions"], "decision")
    problems += repeated_ids(proposal["open_questions"], "open question")
    return problems


def narrowed_entries(
    root: Path,
    parent_entries: list[str],
    child_entries: list[str],
    absorbed: list[str] = (),
) -> dict[str, list[str]]:
    """Each parent entry mapped to the entries that replace it once the children's are removed.

    An entry no child entry touches maps to itself. An entry a child entry covers maps to
    nothing. A directory entry containing a child entry maps to the entries below it that no
    child took: a subdirectory stays one entry when no child took anything inside it, and a
    file is listed exactly. Files the directory exclusion rule skips were never bound and are
    not listed. ``absorbed`` are paths that take everything inside them, dot files included,
    such as vendored code that becomes external material and may overlap no entry at all.
    """

    def taken(path: str) -> bool:
        if any(covers(item, path.rstrip("/")) or item == path for item in absorbed):
            return True
        # A file is taken only when a child entry binds it: a child's directory entry does not
        # bind the files the exclusion rule skips, such as dot files, which the parent keeps.
        if is_directory_entry(path):
            return any(covers(child, path) for child in child_entries)
        return any(bound_by(child, path) for child in child_entries)

    def inside(directory: str) -> bool:
        return any(
            child != directory and child.startswith(directory)
            for child in (*child_entries, *absorbed)
        )

    def expand(directory: str, base: str) -> list[str]:
        result = []
        absolute = root / entry_base(directory)
        for name in sorted(os.listdir(absolute)):
            path = directory + name
            relative = path[len(base) :]
            if (absolute / name).is_symlink():
                continue  # a directory entry never binds a link, so neither does its narrowing
            if (absolute / name).is_dir():
                sub = path + "/"
                if skipped_path(relative + "/x"):
                    continue
                if taken(sub):
                    continue
                if inside(sub):
                    result += expand(sub, base)
                elif expand_entry(root, sub):
                    result.append(
                        sub
                    )  # only a directory that binds files stays an entry
            elif (absolute / name).is_file() and not skipped_path(relative):
                if not taken(path):
                    result.append(path)
        return result

    replaced: dict[str, list[str]] = {}
    for entry in parent_entries:
        if taken(entry):
            replaced[entry] = []
        elif is_directory_entry(entry) and inside(entry):
            if not (root / entry_base(entry)).is_dir():
                replaced[entry] = [entry]
            else:
                replaced[entry] = expand(entry, entry)
        else:
            replaced[entry] = [entry]
    return replaced


__all__ = [
    "ANSWERS_SCHEMA",
    "DECOMPOSITION_SCHEMA",
    "DESCRIBE_WORKER_SCHEMA",
    "EXTERNAL",
    "MODULE_ID",
    "SPEC_DESCRIPTION_SCHEMA",
    "SURVEY_WORKER_SCHEMA",
    "workflow_object",
    "WORKER_DECISION",
    "AnswersError",
    "S",
    "SpecError",
    "answer_problems",
    "child_folder",
    "evidence_problems",
    "load_answers",
    "narrowed_entries",
    "obj",
    "proposal_problems",
    "resolved_decisions",
    "worktree_relative",
]
