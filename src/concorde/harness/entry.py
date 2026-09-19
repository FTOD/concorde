"""The shared executable boundary of every public Skill and Studio entry."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any

from ..spec.repository import SpecError
from ..spec.typed_data import canonical, decode
from .admission import run_host_node
from .host import OperationHost
from .usage import read_usage, summarize_usage


def validate_invocation(value: Any, operation: str | None = None) -> dict:
    """Validate the shared CLI/Studio envelope before selecting a trusted host."""
    if not isinstance(value, dict) or set(value) != {
        "type_id",
        "schema_version",
        "operation_id",
        "mode",
        "configuration",
        "input",
    }:
        raise SpecError("invocation fields do not match schema 3", "invalid_input")
    if (
        value["type_id"] != "concorde-operation-invocation"
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 3
    ):
        raise SpecError(
            "Profile 15 requires concorde-operation-invocation schema 3",
            "unsupported_version",
        )
    if operation is not None and value["operation_id"] != operation:
        raise SpecError(
            "invocation does not match this entry point", "incompatible_handoff"
        )
    return value


def invocation_failure(operation: str | None, error: Exception) -> dict:
    """The same pre-host failure envelope for paired CLI and Studio entries."""
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
            {
                "code": getattr(error, "code", "invalid_input"),
                "field": getattr(error, "field", ""),
                "message": str(error),
            }
        ],
    }


def json_main(package_root: Path, operation: str, runner) -> int:
    """Shared stdin/limit/envelope/result handling for every skill's executable boundary.

    ``runner(state, runtime)`` is the Skill's Operation node. This boundary validates the wire
    envelope and adapts it to State plus trusted Runtime context; it does not dispatch by name. Only a skill has an executable
    boundary at all, so every caller already knows and validates its own ``operation`` before
    reaching here (``scripts/run-operation.py``); there is no internal/stage fallback to guard.
    """

    host = None
    try:
        if sys.argv[1:]:
            raise SpecError(
                "Operation inputs must be one JSON invocation on stdin", "invalid_input"
            )
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = validate_invocation(
            decode(raw.decode() if isinstance(raw, bytes) else raw), operation
        )
        if os.environ.get("CONCORDE_STUDIO_URL") and os.environ.get(
            "CONCORDE_SESSION_SELECTION"
        ):
            raise SpecError(
                "private candidate selection cannot fall back to a Studio runtime",
                "workspace_mismatch",
            )
        if os.environ.get("CONCORDE_STUDIO_URL"):
            from .studio_client import run_in_studio

            state = run_in_studio(
                os.environ["CONCORDE_STUDIO_URL"], value, Path.cwd(), package_root
            )
            result = state["result"]
            if state.get("policies"):
                print(canonical({"policies": state["policies"]}), file=sys.stderr)
        else:
            selection = None
            if os.environ.get("CONCORDE_SESSION_SELECTION"):
                from ..distribution.session_selection import load_selection

                # Pin code/Skills to the candidate while allowing explicitly scoped
                # disposable consumer projects as data. Never redirect into a sibling
                # worktree of the source repository with those loaded instructions.
                if package_root.resolve() != Path.cwd().resolve():
                    from .change_worktree import git

                    package_common = git(
                        package_root,
                        "rev-parse",
                        "--path-format=absolute",
                        "--git-common-dir",
                        check=False,
                    )
                    project_common = git(
                        Path.cwd(),
                        "rev-parse",
                        "--path-format=absolute",
                        "--git-common-dir",
                        check=False,
                    )
                    if (
                        package_common.returncode == 0
                        and project_common.returncode == 0
                        and package_common.stdout.strip()
                        == project_common.stdout.strip()
                    ):
                        raise SpecError(
                            "private selection cannot redirect into another source worktree",
                            "workspace_mismatch",
                        )
                selection = load_selection(
                    package_root, Path(os.environ["CONCORDE_SESSION_SELECTION"])
                )
                if selection["mode"] == "maintenance":
                    raise SpecError(
                        "maintenance authoring uses deterministic development commands, not public Operations",
                        "fresh_session_required",
                    )
            host = OperationHost(
                Path.cwd(),
                package_root,
                mode=value["mode"],
                session_provenance=selection,
            )
            result = run_host_node(
                runner, host, value["configuration"], value["input"], operation
            )

    except KeyboardInterrupt:
        result = invocation_failure(
            operation,
            SpecError("operation cancelled by the host", "execution_cancelled"),
        )
    except Exception as error:
        result = invocation_failure(operation, error)
    if host and host.descriptions:
        print(canonical({"policies": host.descriptions}), file=sys.stderr)
    if host is not None and result.get("invocation_id"):
        records = read_usage(host.project_root, result["invocation_id"])
        if records:
            summary = summarize_usage(records)
            print(
                canonical(
                    {
                        "usage": {
                            "root_invocation_id": result["invocation_id"],
                            "schema_version": summary["schema_version"],
                            "complete": summary["complete"],
                            "historical_records": summary["historical_records"],
                            "unsupported_records": summary["unsupported_records"],
                            "total": summary["total"],
                            "by_step": summary["by_step"],
                        }
                    }
                ),
                file=sys.stderr,
            )
    print(canonical(result))
    return 0 if result["status"] in {"succeeded", "described"} else 3
