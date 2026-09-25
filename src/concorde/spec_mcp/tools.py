"""The six tools of the Spec MCP server, each a thin call into Spec core for one root.

Every tool loads a fresh repository from the server root, so an answer always reflects the Specs
as they are when the call arrives. A failure is raised as ``ToolError`` with a code; the server
turns it into an MCP tool error and never returns a partial answer.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..spec.errors import SpecError, system_cause, unexpected


class ToolError(SpecError):
    """A Spec MCP tool call that cannot be answered."""

    def __init__(self, code: str, message: str, field: str = "", **details):
        super().__init__(message, code, field, **details)


STRINGS = {"type": "array", "items": {"type": "string"}, "minItems": 1}
TOOLS: dict[str, dict] = {
    "boundary": {
        "description": (
            "The grant a task type gives the listed Modules of this worktree: every path the "
            "task may know by name (names), read (ro) or write (rw); unlisted paths are denied."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "modules": STRINGS,
                "task_type": {
                    "enum": [
                        "understand",
                        "specify",
                        "implement",
                        "test",
                        "review-spec",
                        "review-code",
                        "code-to-spec",
                    ]
                },
            },
            "required": ["modules", "task_type"],
        },
    },
    "modules": {
        "description": "Every registered Module in registry order, with its parent.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "module": {
        "description": (
            "One Module's entry, owned documents, relations, realizations and configured checks."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    "context": {
        "description": (
            "The Spec context of a Module, or of a scenario's owner: its context identity and "
            "one source record per selected document member."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    "impact": {
        "description": (
            "Which Modules writing the given paths concerns: readers of a document member, "
            "binders of any other file."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"paths": STRINGS},
            "required": ["paths"],
        },
    },
    "validate": {
        "description": "Run the structural checks, optionally for one Module, and return the findings.",
        "inputSchema": {
            "type": "object",
            "properties": {"target": {"type": "string"}},
        },
    },
}


def _repository(root: Path):
    from ..spec.repository import SpecRepository

    return SpecRepository(root)


def _strings(arguments: dict, name: str) -> list[str]:
    value = arguments.get(name)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ToolError(
            "invalid_input",
            f"{name} must be a nonempty array of nonempty strings, not {value!r}"[:300],
            name,
        )
    return value


def _string(arguments: dict, name: str, required: bool = True) -> str | None:
    value = arguments.get(name)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value:
        raise ToolError(
            "invalid_input",
            f"{name} must be a nonempty string, not {value!r}"[:300],
            name,
        )
    return value


def confine(root: Path, path: str) -> str:
    """The canonical project-relative form of ``path``, refused when it leaves ``root``."""
    candidate = Path(path)
    absolute = candidate if candidate.is_absolute() else root / candidate
    resolved = Path(os.path.realpath(absolute))
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        raise ToolError(
            "outside_root",
            f"{path} resolves to {resolved}, which is outside the server root {root}",
            "paths",
            path=path,
        ) from None
    text = relative.as_posix()
    if text in ("", "."):
        raise ToolError(
            "invalid_input",
            f"{path} names the server root itself, not a path inside it",
            "paths",
            path=path,
        )
    return text + ("/" if path.endswith("/") and not text.endswith("/") else "")


def boundary(root: Path, arguments: dict) -> dict:
    from ..spec.grants import grant

    modules = _strings(arguments, "modules")
    task_type = _string(arguments, "task_type")
    value = grant(_repository(root), modules, task_type).value
    return {"context_identity": value["context_identity"], "entries": value["entries"]}


def modules(root: Path, arguments: dict) -> dict:
    repository = _repository(root)
    return {
        "modules": [
            {
                "id": record["id"],
                "title": record["title"],
                "entry": record["entry"],
                "parent": repository.modules[record["id"]].parent,
            }
            for record in repository.registry["modules"]
        ]
    }


def module(root: Path, arguments: dict) -> dict:
    identity = _string(arguments, "id")
    repository = _repository(root)
    if identity not in repository.modules:
        raise ToolError(
            "unknown_module",
            f"{identity} is not registered in {root}; registered: "
            + ", ".join(sorted(repository.modules)),
            "id",
            subject=identity,
        )
    record = next(
        item for item in repository.registry["modules"] if item["id"] == identity
    )
    return {
        "id": identity,
        "title": record["title"],
        "entry": record["entry"],
        "documents": list(record["owns"]),
        "contains": record["contains"],
        "uses": record["uses"],
        "includes": record["includes"],
        "participates": record["participates"],
        "realizations": [
            {
                "id": item.id,
                "title": item.title,
                "entries": list(item.entries),
                "pending": list(item.pending),
            }
            for item in repository.realizations(identity)
        ],
        "checks": sorted(
            check["id"]
            for check in repository.checks.values()
            if check["module"] == identity
        ),
    }


def context(root: Path, arguments: dict) -> dict:
    from ..spec.grants import context_identity

    identity = _string(arguments, "id")
    repository = _repository(root)
    value = repository.spec_context(identity).value
    return {
        "module": value["module_id"],
        "context_identity": context_identity(repository, [value["module_id"]]),
        "sources": value["sources"],
    }


def impact(root: Path, arguments: dict) -> dict:
    paths = [confine(root, item) for item in _strings(arguments, "paths")]
    repository = _repository(root)
    contexts = {
        identity: set(repository.spec_context(identity).paths)
        for identity in repository.modules
    }
    rows, union = [], set()
    for path in paths:
        if path in repository.document_targets or path.removesuffix(".json") in (
            repository.document_targets
        ):
            concerned = sorted(
                identity for identity, members in contexts.items() if path in members
            )
        else:
            concerned = sorted(repository.implemented_by(path))
        union.update(concerned)
        rows.append({"path": path, "modules": concerned})
    return {"paths": rows, "modules": sorted(union)}


def validate(root: Path, arguments: dict) -> dict:
    from ..spec.diagnostics import tool_envelope
    from ..spec.validation import validate_repository

    target = _string(arguments, "target", required=False)
    return tool_envelope(validate_repository(root, target))


HANDLERS = {
    "boundary": boundary,
    "modules": modules,
    "module": module,
    "context": context,
    "impact": impact,
    "validate": validate,
}


def call(root: Path, name: str, arguments: dict) -> dict:
    """Run one tool; raise a ``SpecError`` that says what failed, where and why."""
    if name not in HANDLERS:
        raise ToolError(
            "invalid_input",
            f"unknown tool {name!r}; the tools are {', '.join(HANDLERS)}",
            "name",
        )
    if not isinstance(arguments, dict):
        raise ToolError(
            "invalid_input",
            f"the arguments of {name} must be an object, not a JSON "
            f"{type(arguments).__name__}",
            "arguments",
        )
    try:
        return HANDLERS[name](root, arguments)
    except SpecError:
        raise
    except OSError as error:
        raise ToolError(
            "system_error",
            f"{name} could not read the Specs of {root}",
            causes=[system_cause(error)],
        ) from error
    except Exception as error:  # noqa: BLE001 -- a defect still answers with its location
        raise unexpected(error) from error


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
