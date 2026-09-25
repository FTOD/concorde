"""The records Adoption's Operations share: schemas, answers, and the checks of a proposal.

The schemas are the contracts of ``specs/concorde/operations/adoption/contracts.md``; the tests
hold them equal. ``proposal_problems`` is the one check of a decomposition proposal against a
worktree, used by the survey after its worker and by the scaffold again before it writes, and
``narrowed_entries`` is the one rule by which a parent's realization entries lose the paths its
children take.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..spec.repository_base import (
    IDENTITY,
    SpecError,
    bound_by,
    covers,
    entry_base,
    expand_entry,
    is_directory_entry,
    skipped_path,
)
from ..spec.schema import ContractError, validate

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
        "decided_by": {"enum": ["worker", "developer"]},
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
        "timeout_seconds": {"type": "integer", "minimum": 1},
        "inputs": {"type": "array", "items": S},
        "reason": S,
    }
)
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
        "checks": {"type": "array", "items": CHECK},
        "decisions": {"type": "array", "items": DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
    }
)
# contract.adoption.decomposition, version 1
DECOMPOSITION_SCHEMA = obj(
    {
        "module": MODULE_ID,
        "summary": S,
        "children": {"type": "array", "items": CHILD},
        "remaining_entries": {"type": "array", "items": S},
        "checks": {"type": "array", "items": CHECK},
        "decisions": {"type": "array", "items": DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
    }
)
# contract.adoption.scaffold-record, version 1
SCAFFOLD_RECORD_SCHEMA = obj(
    {
        "parent": MODULE_ID,
        "survey_run": S,
        "created": {
            "type": "array",
            "items": obj(
                {
                    "id": MODULE_ID,
                    "title": S,
                    "entry": S,
                    "entries": {"type": "array", "items": S},
                }
            ),
        },
        "parent_entries_before": {"type": "array", "items": S},
        "parent_entries_after": {"type": "array", "items": S},
        "files_written": {"type": "array", "items": S},
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
    }
)
DEVIATION = obj(
    {"module": MODULE_ID, "question": QUESTION_ID, "intended": S, "observed": S}
)
# What the code_to_spec worker claims.
DESCRIBE_WORKER_SCHEMA = obj(
    {
        "summary": S,
        "promises": {"type": "array", "items": PROMISE},
        "decisions": {"type": "array", "items": DECISION},
        "open_questions": {"type": "array", "items": QUESTION},
        "deviations": {"type": "array", "items": DEVIATION},
    }
)
# contract.adoption.spec-description, version 1
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
        "validation": obj(
            {
                "new_errors": {"type": "array", "items": FINDING},
                "preexisting_errors": {"type": "integer", "minimum": 0},
            }
        ),
    }
)
# contract.adoption.answers, version 1
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
                }
            ),
        }
    }
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


def answer_problems(
    answers: list[dict],
    decisions: list[dict],
    promises: list[dict] = (),
    deviations: list[dict] = (),
) -> list[str]:
    """Every answer an output does not follow, one sentence each.

    A decision answer (``d.``) is followed by a decision with its identity, decided by the
    developer, whose choice is the answer. A question answer (``q.``) is followed by a promise
    with source ``answer`` naming the question, or by a deviation naming it.
    """
    problems = []
    by_decision = {item["id"]: item for item in decisions}
    for answer in answers:
        identity = answer["id"]
        if identity.startswith("d."):
            decision = by_decision.get(identity)
            if decision is None:
                problems.append(
                    f"the answer to {identity} ({answer['answer']!r}) has no decision "
                    f"{identity} in the output"
                )
            elif (
                decision["decided_by"] != "developer"
                or decision["chosen"] != answer["answer"]
            ):
                problems.append(
                    f"decision {identity} chose {decision['chosen']!r}, decided by "
                    f"{decision['decided_by']}, but the developer answered "
                    f"{answer['answer']!r}"
                )
        elif not any(
            item.get("source") == "answer" and item.get("question") == identity
            for item in promises
        ) and not any(item["question"] == identity for item in deviations):
            problems.append(
                f"the answer to {identity} ({answer['answer']!r}) appears in no promise with "
                "source answer and in no deviation"
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
    """Whether an existing child entry lies within the paths the parent's entries bind."""
    if is_directory_entry(entry):
        directory = root / entry_base(entry)
        if directory.is_symlink() or not directory.is_dir():
            return False
        return any(
            is_directory_entry(parent) and (entry == parent or entry.startswith(parent))
            for parent in parent_entries
        )
    path = root / entry
    if path.is_symlink() or not path.is_file():
        return False
    return any(bound_by(parent, entry) for parent in parent_entries)


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
    check_ids = [check["id"] for check in proposal["checks"]]
    for check in proposal["checks"]:
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
    root: Path, parent_entries: list[str], child_entries: list[str]
) -> dict[str, list[str]]:
    """Each parent entry mapped to the entries that replace it once the children's are removed.

    An entry no child entry touches maps to itself. An entry a child entry covers maps to
    nothing. A directory entry containing a child entry maps to the entries below it that no
    child took: a subdirectory stays one entry when no child took anything inside it, and a
    file is listed exactly. Files the directory exclusion rule skips were never bound and are
    not listed.
    """

    def taken(path: str) -> bool:
        return any(covers(child, path) for child in child_entries)

    def inside(directory: str) -> bool:
        return any(
            child != directory and child.startswith(directory)
            for child in child_entries
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
    "SCAFFOLD_RECORD_SCHEMA",
    "SPEC_DESCRIPTION_SCHEMA",
    "SURVEY_WORKER_SCHEMA",
    "AnswersError",
    "SpecError",
    "answer_problems",
    "child_folder",
    "load_answers",
    "narrowed_entries",
    "proposal_problems",
]
