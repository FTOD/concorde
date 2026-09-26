"""The review memory: every finding the Spec reviews of one Module have kept, open or resolved.

A review is no longer a fresh list each time. Its reviewer receives the Module's open earlier
findings and reports only what is new, what changed in an earlier finding (naming its id) and
which earlier findings the Specs no longer have (with the reason); an earlier finding it does not
mention stays open. The host merges that into the memory, and the Module's outcome is the state of
the memory: any open blocking finding requires changes, however old. The memory is tracked with
the project, one file per Module under ``.concorde/reviews/spec/``, so every task and every
collaborator reviews against the same history; a review inside a task writes it, and the task's
delivery commits it.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..spec.repository_base import SpecError
from ..spec.schema import ContractError, validate

DIRECTORY = ".concorde/reviews/spec"
CONTENT = (
    "path",
    "anchor",
    "line",
    "dimension",
    "severity",
    "problem",
    "evidence",
    "suggestion",
)
IDENTITY = "^f\\.[1-9][0-9]*$"

# contract.spec-review.memory, version 2 (operation.md); a test keeps the two equal.
MEMORY_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "module", "findings"],
    "properties": {
        "schema_version": {"const": 1},
        "module": {"type": "string", "minLength": 1},
        # The Specs the last completed review judged: while the Module's context identity is
        # still this one, a review changes nothing and is not run again.
        "reviewed": {
            "type": "object",
            "additionalProperties": False,
            "required": ["context_identity", "run"],
            "properties": {
                "context_identity": {
                    "type": "string",
                    "pattern": "^sha256:[0-9a-f]{64}$",
                },
                "run": {"type": "string", "minLength": 1},
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "id",
                    "status",
                    "path",
                    "dimension",
                    "severity",
                    "problem",
                    "evidence",
                    "suggestion",
                    "first_run",
                    "last_run",
                    "resolution",
                ],
                "properties": {
                    "id": {"type": "string", "pattern": IDENTITY},
                    "status": {"enum": ["open", "resolved"]},
                    "path": {"type": "string", "minLength": 1},
                    "anchor": {"type": "string", "minLength": 1},
                    "line": {"type": "integer", "minimum": 1},
                    "dimension": {"type": "string", "minLength": 1},
                    "severity": {"enum": ["blocking", "advisory"]},
                    "problem": {"type": "string", "minLength": 1},
                    "evidence": {"type": "string", "minLength": 1},
                    "suggestion": {"type": "string", "minLength": 1},
                    "first_run": {"type": "string", "minLength": 1},
                    "last_run": {"type": "string", "minLength": 1},
                    "resolution": {
                        "anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]
                    },
                },
            },
        },
    },
}


def memory_path(module: str) -> str:
    return f"{DIRECTORY}/{module}.json"


def load(worktree: Path, module: str) -> dict:
    """The Module's memory, empty when no review kept one yet."""
    path = Path(worktree) / memory_path(module)
    if not path.exists():
        return {"schema_version": 1, "module": module, "findings": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        validate(value, MEMORY_SCHEMA)
    except (OSError, ValueError, ContractError) as error:
        raise SpecError(
            f"the review memory {memory_path(module)} of {module} cannot be used: {error}",
            "review_memory_unusable",
            path=memory_path(module),
        ) from error
    if value["module"] != module:
        raise SpecError(
            f"the review memory {memory_path(module)} belongs to {value['module']}, not {module}",
            "review_memory_unusable",
            path=memory_path(module),
        )
    return value


def open_findings(memory: dict) -> list[dict]:
    return [item for item in memory["findings"] if item["status"] == "open"]


def material(memory: dict) -> str:
    """The reviewer's view of the memory: the open earlier findings, with their ids."""
    earlier = open_findings(memory)
    if not earlier:
        return "## Earlier findings\n\nNo earlier review left an open finding for this Module.\n"
    shown = [
        {key: item[key] for key in ("id", *CONTENT) if key in item} for item in earlier
    ]
    return (
        "## Earlier findings\n\n"
        "Earlier reviews left these findings open. Before you report any finding as new, "
        "compare it with each of them: a finding about the same problem, the same passage or "
        "the same kind of defect in the same place, is that earlier finding, however you would "
        "word it now, never a new one. If an earlier finding still stands as written, leave it "
        "out: it stays open. If it still stands but you would state it differently or it has "
        "changed, report it with `earlier` set to its id. If the Specs no longer have the "
        "problem, list it in `resolved` with the reason. Only a problem none of them covers is "
        "a new finding.\n\n```json\n"
        + json.dumps(shown, indent=2, ensure_ascii=False)
        + "\n```\n"
    )


def merge(memory: dict, run_id: str, reported: list[dict], resolved: list[dict]):
    """The memory after one review, and what the review did to it.

    ``reported`` are the review's findings in the payload's shape; a finding a checker disputed
    is kept out of the memory, and one naming an earlier finding that is not open counts as new.
    Every reported finding kept gets its memory ``id``."""
    merged = json.loads(json.dumps(memory))
    by_id = {item["id"]: item for item in merged["findings"]}
    opened = {item["id"] for item in open_findings(merged)}
    numbers = [int(item["id"][2:]) for item in merged["findings"]]
    following = max(numbers, default=0) + 1
    summary = {"new": [], "updated": [], "resolved": [], "carried": [], "ignored": []}
    touched = set()
    for item in resolved:
        identity = item["id"]
        if identity in opened and identity not in touched:
            record = by_id[identity]
            record.update(status="resolved", resolution=item["reason"], last_run=run_id)
            summary["resolved"].append({"id": identity, "reason": item["reason"]})
            touched.add(identity)
        else:
            summary["ignored"].append(
                {"id": identity, "reason": "resolves no open earlier finding"}
            )
    for finding in reported:
        disputed = (finding.get("check") or {}).get("status") == "disputed"
        earlier = finding.get("earlier")
        if disputed:
            finding["id"] = None
            continue
        content = {key: finding[key] for key in CONTENT if key in finding}
        if earlier in opened and earlier not in touched:
            record = by_id[earlier]
            for key in ("anchor", "line"):
                record.pop(key, None)
            record.update(content, last_run=run_id)
            finding["id"] = earlier
            summary["updated"].append(earlier)
            touched.add(earlier)
            continue
        identity = f"f.{following}"
        following += 1
        merged["findings"].append(
            {
                "id": identity,
                "status": "open",
                **content,
                "first_run": run_id,
                "last_run": run_id,
                "resolution": None,
            }
        )
        finding["id"] = identity
        summary["new"].append(identity)
    summary["carried"] = [
        {key: item[key] for key in ("id", *CONTENT) if key in item}
        for item in merged["findings"]
        if item["status"] == "open"
        and item["id"] in opened
        and item["id"] not in touched
    ]
    return merged, summary


def write(worktree: Path, module: str, memory: dict) -> str:
    path = Path(worktree) / memory_path(module)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(memory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return memory_path(module)


__all__ = [
    "DIRECTORY",
    "MEMORY_SCHEMA",
    "load",
    "material",
    "memory_path",
    "merge",
    "write",
]
