"""The JSON boundary of every capability request: one invocation in, one result envelope out."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any

from ..spec.repository import SpecError
from ..spec.typed_data import TypedDataError, canonical, check_schema, decode
from .admission import run_operation
from .host import AdmissionServices, OperationHost

MAX_INVOCATION_BYTES = 1024 * 1024

# contract.admission.invocation, version 3.
INVOCATION = {
    "type": "object",
    "properties": {
        "type_id": {"const": "concorde-operation-invocation"},
        "schema_version": {"const": 3},
        "operation_id": {"type": "string", "minLength": 1},
        "mode": {"enum": ["execute", "describe-policy"]},
        "configuration": {
            "anyOf": [
                {"type": "object", "additionalProperties": {}},
                {"type": "null"},
            ]
        },
        "input": {"type": "object", "additionalProperties": {}},
    },
    "required": [
        "type_id",
        "schema_version",
        "operation_id",
        "mode",
        "configuration",
        "input",
    ],
}


def validate_invocation(value: Any, operation: str | None = None) -> dict:
    """Check the capability request envelope before a host is created for it."""
    if not isinstance(value, dict) or set(value) != set(INVOCATION["required"]):
        raise SpecError("invocation fields do not match schema 3", "invalid_input")
    if (
        value["type_id"] != "concorde-operation-invocation"
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 3
    ):
        raise SpecError(
            "a capability request must be concorde-operation-invocation schema 3",
            "unsupported_version",
        )
    try:
        check_schema(value, INVOCATION)
    except TypedDataError as error:
        raise SpecError(str(error), "invalid_input", error.field) from error
    if operation is not None and value["operation_id"] != operation:
        raise SpecError(
            "invocation does not match this entry point", "incompatible_handoff"
        )
    return value


def invocation_failure(operation: str | None, error: Exception) -> dict:
    """The envelope of a request refused before admission."""
    from .execution_error import error_entry

    return {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation,
        "invocation_id": str(uuid.uuid4()),
        "mode": None,
        "status": "blocked",
        "workspace": None,
        "output": None,
        "errors": [
            error_entry(
                error, code=getattr(error, "code", "invalid_input"), layer="entry"
            )
        ],
    }


def json_main(
    package_root: Path,
    operation: str,
    *,
    services: AdmissionServices,
    session_provenance: dict | None = None,
) -> int:
    """Read one capability request from standard input and print its one result envelope.

    The launcher has already resolved ``operation`` in the catalog and verified any session
    selection; it hands admission the catalog's declarations, the dispatcher and the installation
    service through ``services``.
    """
    host = None
    try:
        if sys.argv[1:]:
            raise SpecError(
                "Operation inputs must be one JSON invocation on stdin", "invalid_input"
            )
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(MAX_INVOCATION_BYTES + 1)
        if len(raw) > MAX_INVOCATION_BYTES:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = validate_invocation(
            decode(raw.decode() if isinstance(raw, bytes) else raw), operation
        )
        from .status_store import primary_root

        host = OperationHost(
            Path.cwd(),
            package_root,
            mode=value["mode"],
            services=services,
            session_provenance=session_provenance,
            archive_root=primary_root(Path.cwd()),
        )
        result = run_operation(
            operation, value["configuration"], value["input"], host_context=host
        )
    except KeyboardInterrupt:
        result = invocation_failure(
            operation,
            SpecError("operation cancelled by the host", "execution_cancelled"),
        )
    except Exception as error:
        result = invocation_failure(operation, error)
        # Once the envelope has selected a host, a refusal belongs to that admitted mode.
        if host is not None and host.mode in {"execute", "describe-policy"}:
            result["mode"] = host.mode
    print(canonical(result))
    return 0 if result["status"] in {"succeeded", "described"} else 3
