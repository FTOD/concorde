"""Spec tooling's own error type: what failed, where, why it is an error and how to fix it.

Every error Spec tooling raises is a ``SpecError`` or a subclass. Besides its stable ``code`` and a
concrete ``message`` naming the values concerned, it carries its **location** (a project path, a
line, a field or JSON pointer, a node identity), the **reason** it is an error (the rule or
requirement it breaks) and a **remediation**, and the errors that caused it as ``causes``, such as
every fatal Spec problem behind a refused load or the operating system's error behind an
unreadable file. ``record()`` is the error as data, the ``contract.spec.error`` record that Spec
tooling's commands and the Spec MCP server return.

The reason and remediation of each code are registered in ``CODES``; a call site passes its own
when it knows more. A subclass that belongs to another Module registers its codes in its own
``CODES`` table. Spec tooling depends on no other Module for its errors.
"""

from __future__ import annotations

import traceback
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

# code -> (reason: why this is an error, remediation: how to fix it)
CODES: dict[str, tuple[str, str]] = {
    "invalid_spec": (
        "the Spec sources break a rule of the Spec Protocol or of the project configuration",
        "correct the named file or field so that it follows the Protocol, then validate again",
    ),
    "invalid_owner": (
        "every Spec document is owned by exactly one Module (CHK.owns.unique)",
        "list the document in the owns of one Module only",
    ),
    "unsafe_path": (
        "Spec tooling reads only canonical project-relative paths of regular files, never "
        "through a symbolic link or outside the project",
        "use a canonical project-relative path to a regular file and remove the symbolic link",
    ),
    "missing_source": (
        "a file the Specs or the configuration require does not exist or cannot be read",
        "create the file, restore it, or remove the reference to it",
    ),
    "unsupported_profile": (
        "this Spec tooling reads only the project profile and registry schema of Protocol 13 "
        "(schema_version 3)",
        "migrate the configuration and registry to the current profile explicitly",
    ),
    "protocol_mismatch": (
        "the project's Protocol binding must name exactly the Protocol copy installed under "
        ".concorde/protocol/, and that copy must be unchanged",
        "reinstall Concorde, or accept the installed Protocol by updating the binding",
    ),
    "not_installed": (
        "initialization needs the Protocol copy that only the installer places",
        "run the Concorde installer in this project first",
    ),
    "already_initialized": (
        "initialization creates the first Spec only; it never overwrites a configured project",
        "change an initialized project's Specs through ordinary work instead",
    ),
    "invalid_input": (
        "the arguments of the call do not have the required form",
        "correct the named argument and call again",
    ),
    "invalid_task_type": (
        "a grant exists only for the seven task types the Protocol defines",
        "use understand, specify, implement, test, review-spec, review-code or code-to-spec",
    ),
    "unknown_module": (
        "a grant, boundary or query names only Modules the registry registers",
        "name registered Modules, or register the Module first",
    ),
    "unknown_target": (
        "the named Module or node is not declared in the loaded Specs",
        "name a declared Module or node; `concorde validate` lists what exists",
    ),
    "invalid_target": (
        "the identity does not name a document, scenario or context of the requested kind",
        "name an identity of the requested kind",
    ),
    "invalid_focus": (
        "a scenario focus must belong to the Module it narrows",
        "focus on a scenario of the selected Module",
    ),
    "shared_file": (
        "a task may write a file only when every Module that binds it is bound by the task, "
        "so no other Module's promise changes behind its back",
        "bind every Module that binds the shared file, or leave the file unchanged",
    ),
    "invalid_context": (
        "a context holds each registered document member once, with its owner's role and "
        "provenance",
        "recompute the context from the current Specs instead of editing it",
    ),
    "stale_context": (
        "a context is valid only for the exact Spec sources it was computed from",
        "compute the context again from the current Specs",
    ),
    "invalid_proposal": (
        "a proposal is applied only in exactly the shape and content it was proposed with",
        "propose again and apply the new proposal unchanged",
    ),
    "stale_proposal": (
        "a proposal is applied only to the bytes it was computed from",
        "propose again from the current files",
    ),
    "permission_denied": (
        "the change or read lies outside the paths its caller authorized",
        "restrict the change to the authorized paths, or ask for the wider boundary",
    ),
    "contract_violation": (
        "the value does not satisfy the published schema it is checked against",
        "correct the value at the named field so that it satisfies the schema",
    ),
    "duplicate_type": (
        "a typed value's identity is registered once, with one version and one schema",
        "register the type once, or choose a new type identity",
    ),
    "unknown_type": (
        "a typed value names only a registered type",
        "register the type, or use a registered type identity",
    ),
    "invalid_json": (
        "Spec tooling accepts strict JSON: no duplicate fields and no NaN or Infinity",
        "write strict JSON",
    ),
    "invalid_field": (
        "the typed value does not satisfy its registered schema",
        "correct the value at the named field",
    ),
    "incompatible_handoff": (
        "a typed value is accepted only as the type its receiver expects",
        "pass a value of the expected type",
    ),
    "unsupported_version": (
        "a typed value must have its type's registered schema version",
        "convert the value to the registered version",
    ),
    "stale_reference": (
        "an artifact reference is valid only while the referenced bytes are unchanged",
        "recompute the reference from the current file",
    ),
    "invalid_front_matter": (
        "front matter is the restricted YAML subset the Protocol defines",
        "rewrite the front matter in the supported subset",
    ),
    "invalid_declaration": (
        "a verification declaration names scenario identities as string literals in a "
        "parseable test",
        "fix the declaration or the test source",
    ),
    "invalid_diagram": (
        "a checked D2 diagram uses only the semantic subset the Views chapter defines: shapes, "
        "nesting and '->' edges, with no styling or layout",
        "remove the styling or layout statement, or mark the block `d2 illustrative`",
    ),
    "invalid_docsite_template": (
        "the docsite scaffold is copied only from the package's complete, safe template",
        "reinstall or rebuild the Concorde package",
    ),
    "no_root": (
        "the Spec MCP server answers only for one project root",
        "set CLAUDE_PROJECT_DIR or offer exactly one file:// root",
    ),
    "outside_root": (
        "the Spec MCP server answers only about paths inside its root",
        "pass a path inside the server's root",
    ),
    "system_error": (
        "the operating system or the Python runtime refused an operation Spec tooling needed",
        "fix the file, permission or environment named in the message",
    ),
    "unexpected_error": (
        "an exception Spec tooling does not anticipate ended the command; it is a defect",
        "report the error with its location and message",
    ),
}

UNREGISTERED = (
    "the code is not registered with a reason",
    "report the error with its location and message",
)


class SpecError(ValueError):
    """A Spec tooling error with its location, reason, remediation and causes."""

    CODES: dict[str, tuple[str, str]] = CODES
    DEFAULT_CODE = "invalid_spec"

    def __init__(
        self,
        message: str,
        code: str | None = None,
        field: str = "",
        *,
        path: str | None = None,
        line: int | None = None,
        subject: str | None = None,
        reason: str | None = None,
        remediation: str | None = None,
        causes: Iterable["SpecError"] = (),
    ):
        self.code = code or self.DEFAULT_CODE
        self.field = field
        self.message = message
        self.path, self.line, self.subject = path, line, subject
        known = self.CODES.get(self.code) or CODES.get(self.code) or UNREGISTERED
        self.reason = reason or known[0]
        self.remediation = remediation or known[1]
        self.causes = tuple(causes)
        super().__init__(message)

    def location(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "field": self.field or None,
            "subject": self.subject,
        }

    def where(self) -> str:
        parts = [self.path or ""]
        if self.path and self.line:
            parts[0] += f":{self.line}"
        if self.field and self.field != self.path:
            parts.append(f"field {self.field}" if self.path else self.field)
        if self.subject:
            parts.append(self.subject)
        return ", ".join(part for part in parts if part)

    def record(self) -> dict[str, Any]:
        """The error as a ``contract.spec.error`` record."""
        return {
            "code": self.code,
            "message": str(self),
            "reason": self.reason,
            "location": self.location(),
            "remediation": self.remediation,
            "causes": [cause.record() for cause in self.causes],
        }

    def describe(self) -> str:
        """One paragraph for a human or a log: what, where, why, how to fix, and the causes."""
        where = self.where()
        text = f"{self.code}: {self}" + (f" (at {where})" if where else "")
        text += f"; why: {self.reason}; to fix: {self.remediation}"
        if self.causes:
            text += "; caused by: " + " | ".join(
                cause.describe() for cause in self.causes
            )
        return text


@lru_cache(maxsize=1)
def check_statements() -> dict[str, str]:
    """Each Protocol check's statement, from the check table of the packaged Protocol."""
    table = Path(__file__).resolve().parents[3] / "protocol/checks.md"
    try:
        lines = table.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    statements = {}
    for line in lines:
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) > 3 and cells[1].startswith("`CHK."):
            statements[cells[1].strip("`")] = cells[2]
    return statements


def from_finding(finding, code: str = "invalid_spec") -> SpecError:
    """A validation finding (``Finding``) as a cause, keeping its rule, location and advice;
    its reason is the rule's own statement when the Protocol states one."""
    statement = check_statements().get(finding.rule_id)
    error = SpecError(
        f"{finding.rule_id}: {finding.message}",
        code,
        path=finding.source or None,
        line=finding.line,
        subject=finding.subject_id,
        reason=f"{finding.rule_id} requires: {statement}"
        if statement
        else f"the check {finding.rule_id} fails",
        remediation=finding.remediation or None,
    )
    error.rule_id = finding.rule_id
    return error


def system_cause(error: BaseException, **location) -> SpecError:
    """An operating-system or runtime exception as a ``system_error`` cause."""
    path = location.pop("path", None) or getattr(error, "filename", None)
    return SpecError(
        f"{type(error).__name__}: {error}",
        "system_error",
        path=str(path) if path else None,
        **location,
    )


def unexpected(error: BaseException) -> SpecError:
    """An unanticipated exception, located where it was raised."""
    if isinstance(error, SpecError):
        return error
    frames = traceback.extract_tb(error.__traceback__)
    last = frames[-1] if frames else None
    return SpecError(
        f"{type(error).__name__}: {error}",
        "unexpected_error",
        path=last.filename if last else None,
        line=last.lineno if last else None,
        subject=last.name if last else None,
    )


# contract.spec.error
ERROR_SCHEMA: dict = {
    "$ref": "#/$defs/error",
    "$defs": {
        "error": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "code",
                "message",
                "reason",
                "location",
                "remediation",
                "causes",
            ],
            "properties": {
                "code": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
                "message": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
                "location": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "line", "field", "subject"],
                    "properties": {
                        "path": {"anyOf": [{"type": "null"}, {"type": "string"}]},
                        "line": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
                        "field": {"anyOf": [{"type": "null"}, {"type": "string"}]},
                        "subject": {"anyOf": [{"type": "null"}, {"type": "string"}]},
                    },
                },
                "remediation": {"type": "string", "minLength": 1},
                "causes": {"type": "array", "items": {"$ref": "#/$defs/error"}},
            },
        }
    },
}


__all__ = [
    "CODES",
    "ERROR_SCHEMA",
    "SpecError",
    "from_finding",
    "system_cause",
    "unexpected",
]
