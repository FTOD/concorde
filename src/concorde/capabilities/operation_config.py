"""Explicit project Operation settings and digest-bound configuration proposals."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from ..model import Finding, ToolResult
from .operation_data import OperationDataError, checked_path, decode, validate_typed

CONFIG_PATH = ".concorde/config.json"
CONFIG_TYPE = "concorde-operation-configuration"


def _project_root(project_root: str | Path) -> Path:
    project = Path(project_root)
    if project.is_symlink():
        raise OperationDataError("configuration_mismatch", "/configuration", "project root may not be a symlink")
    return project.resolve()


def load_configuration(project_root: str | Path) -> dict:
    project = Path(project_root)
    if project.is_symlink():
        raise OperationDataError("configuration_mismatch", "/configuration", "project root may not be a symlink")
    try:
        document = decode(checked_path(project, CONFIG_PATH).read_text(encoding="utf-8"))
        value = document.get("operation_configuration") if isinstance(document, dict) else None
        if value is None:
            raise OperationDataError("configuration_mismatch", "/configuration", "project Operation settings are missing; apply an explicit configure proposal")
        return validate_typed(value, CONFIG_TYPE, "/configuration")
    except OSError as error:
        raise OperationDataError("configuration_mismatch", "/configuration", f"cannot load project configuration: {error}") from error


def _failure(error: Exception) -> ToolResult:
    return ToolResult("configure", ".", "invalid", findings=(Finding(
        "CONCORDE-CONFIG-001", "error", CONFIG_PATH, str(error),
        "Propose explicit Operation configuration JSON, review its source digest, and apply the accepted proposal."),))


def propose_configuration(project_root: str | Path, configuration: dict) -> ToolResult:
    try:
        project = _project_root(project_root)
        configuration = validate_typed(configuration, CONFIG_TYPE, "/configuration")
        source = checked_path(project, CONFIG_PATH).read_bytes()
        document = decode(source.decode("utf-8"))
        if not isinstance(document, dict):
            raise ValueError("project configuration must be an object")
        if document.get("operation_configuration") == configuration:
            return ToolResult("configure", ".", "unchanged", artifacts=(CONFIG_PATH,))
        proposal = {"proposal_version": 1, "path": CONFIG_PATH,
                    "source_digest": "sha256:" + hashlib.sha256(source).hexdigest(),
                    "configuration": configuration}
        return ToolResult("configure", ".", "proposal", result={"proposal": proposal})
    except (OSError, UnicodeError, ValueError) as error:
        return _failure(error)


def apply_configuration(project_root: str | Path, proposal_path: str) -> ToolResult:
    try:
        project = _project_root(project_root)
        value = decode(checked_path(project, proposal_path).read_text(encoding="utf-8"))
        proposal = value.get("result", {}).get("proposal", value.get("proposal", value))
        if (not isinstance(proposal, dict)
                or set(proposal) != {"proposal_version", "path", "source_digest", "configuration"}
                or type(proposal["proposal_version"]) is not int or proposal["proposal_version"] != 1
                or proposal["path"] != CONFIG_PATH):
            raise ValueError("unsupported configuration proposal")
        configuration = validate_typed(proposal["configuration"], CONFIG_TYPE)
        path = checked_path(project, CONFIG_PATH)
        source = path.read_bytes()
        document = decode(source.decode("utf-8"))
        if not isinstance(document, dict):
            raise ValueError("project configuration must be an object")
        if document.get("operation_configuration") == configuration:
            return ToolResult("configure", ".", "unchanged", artifacts=(CONFIG_PATH,))
        if "sha256:" + hashlib.sha256(source).hexdigest() != proposal["source_digest"]:
            raise ValueError("configuration changed after proposal; request a fresh proposal")
        document["operation_configuration"] = configuration
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="operation-config-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
        try:
            if checked_path(project, CONFIG_PATH).read_bytes() != source:
                raise ValueError("configuration changed during apply")
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return ToolResult("configure", ".", "success", artifacts=(CONFIG_PATH,),
                          result={"configuration": configuration})
    except (OSError, UnicodeError, ValueError, AttributeError, TypeError) as error:
        return _failure(error)
