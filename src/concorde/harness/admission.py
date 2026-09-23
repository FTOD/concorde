"""Admission of every capability request: the fixed sequence from request to result envelope.

Every request is read, admitted against the declaration of the capability it names, bound to its
workspace and checked against the stored configuration before the dispatcher the launcher supplied
runs it; every outcome, admitted or not, ends in one result envelope. Admission knows no provider:
what differs between capabilities comes from their declarations and, where one is named, the
provider's target selection hook.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
import uuid
from dataclasses import replace
from pathlib import Path

from ..spec.repository import SpecError, SpecRepository
from ..spec.typed_data import (
    TypedDataError,
    canonical,
    check_schema,
    data_schema,
    validate_typed,
)
from .change_worktree import (
    bind_owner,
    component_request,
    progress,
    read_change,
    resume_owner,
    workspace_identity,
)
from .configuration import load_configuration
from .execution_error import OperationExecutionError, error_entry
from .host import AdmittedRequest, OperationHost
from .relay import bind_worktree, relay_operation
from .timing import timed, traced_operation

# contract.admission.capability-declaration, version 1.
_NAME = {"type": "string", "minLength": 1}
CAPABILITY_DECLARATION = {
    "type": "object",
    "properties": {
        "capability": _NAME,
        "public": {"type": "boolean"},
        "model_backed": {"type": "boolean"},
        "request_type": _NAME,
        "response_type": _NAME,
        "mutation": {
            "type": "object",
            "properties": {
                "policy": {"enum": ["never", "always", "by-action"]},
                "actions": {"type": "array", "items": _NAME},
            },
            "required": ["policy", "actions"],
        },
        "workspace": {
            "enum": ["candidate", "primary-opt-in", "delivery-session", "none"]
        },
        "target": {
            "type": "object",
            "properties": {
                "selection": {"enum": ["bound-module", "none", "provider-hook"]},
                "hook": {"anyOf": [_NAME, {"type": "null"}]},
            },
            "required": ["selection", "hook"],
        },
        "default_task": {"anyOf": [_NAME, {"type": "null"}]},
        "configuration": {"enum": ["stored", "request"]},
        "entry_point": _NAME,
    },
    "required": [
        "capability",
        "public",
        "model_backed",
        "request_type",
        "response_type",
        "mutation",
        "workspace",
        "target",
        "default_task",
        "configuration",
        "entry_point",
    ],
}

BUILD_MANIFEST = "generated/build-manifest.json"


def resolve_entry(reference: str, field: str = "entry_point"):
    """The callable a ``package.module:function`` reference names, or ``invalid_input``."""
    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name or not attribute:
        raise SpecError(f"{reference!r} is not module:function", "invalid_input", field)
    try:
        value = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as error:
        raise SpecError(
            f"{reference!r} does not resolve: {error}", "invalid_input", field
        ) from error
    if not callable(value):
        raise SpecError(f"{reference!r} is not callable", "invalid_input", field)
    return value


def check_declaration(declaration) -> dict:
    """Refuse a capability declaration that violates its contract, before any effect."""
    try:
        check_schema(declaration, CAPABILITY_DECLARATION)
    except TypedDataError as error:
        raise SpecError(
            f"invalid capability declaration: {error}", "invalid_input", error.field
        ) from error
    mutation = declaration["mutation"]
    if (mutation["policy"] == "by-action") != bool(mutation["actions"]):
        raise SpecError(
            "mutation actions are listed exactly for the by-action policy",
            "invalid_input",
            "/mutation/actions",
        )
    if declaration["workspace"] == "none" and mutation["policy"] != "never":
        raise SpecError(
            "the none workspace needs mutation policy never",
            "invalid_input",
            "/workspace",
        )
    target = declaration["target"]
    if (target["selection"] == "provider-hook") != (target["hook"] is not None):
        raise SpecError(
            "a target hook is named exactly for provider-hook selection",
            "invalid_input",
            "/target/hook",
        )
    resolve_entry(declaration["entry_point"], "/entry_point")
    if target["hook"] is not None:
        resolve_entry(target["hook"], "/target/hook")
    return declaration


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verify_build(package_root: Path) -> None:
    """Refuse with ``stale_build`` unless the build manifest says the build is fresh.

    Freshness is exactly as contract.distribution.build-manifest defines it: the manifest exists
    and parses, and every recorded source is a regular file reached through no symbolic link
    whose current digest equals the recorded one. Output bytes are never compared.
    """
    root = Path(package_root)
    path = root / BUILD_MANIFEST
    try:
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                "no build manifest; run the build before using this package"
            )
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "sources", "outputs"}
            or manifest["schema_version"] != 1
            or not isinstance(manifest["sources"], dict)
            or not isinstance(manifest["outputs"], dict)
        ):
            raise ValueError("the build manifest is malformed")
        for relative, expected in manifest["sources"].items():
            source = root
            for part in Path(relative).parts:
                source = source / part
                if source.is_symlink():
                    raise ValueError(f"build source is a symbolic link: {relative}")
            if not source.is_file():
                raise ValueError(f"build source is missing: {relative}")
            if _digest(source.read_bytes()) != expected:
                raise ValueError(f"build source changed since the build: {relative}")
    except (OSError, UnicodeError, ValueError) as error:
        raise SpecError(f"stale build at {root}: {error}", "stale_build") from error


def bind_module_target(
    project_root: Path, package_root: Path, data: dict, *, mutates: bool
) -> dict:
    """Admit ``target_id`` and any ``focus_id``, restoring the recorded owner of a mutation."""
    if not isinstance(data.get("target_id"), str):
        raise SpecError("select an explicit target_id", "invalid_input", "/target_id")
    repository = SpecRepository(project_root, package_root)
    if mutates:
        change = read_change(project_root)
        if change:
            owner = change.get("target_id")
            if owner is not None and owner not in repository.modules:
                raise SpecError(
                    "recorded change owner is not registered",
                    "invalid_worktree_state",
                    field="target_id",
                )
            # Restore only this change's intent; a component request keeps its own task.
            if owner in {None, data["target_id"]}:
                data = resume_owner(change, data)
    repository.module(data["target_id"], data.get("focus_id"))
    return data


@traced_operation
def run_operation(
    operation: str,
    configuration: dict | None,
    runtime_input: dict,
    *,
    host_context: OperationHost,
) -> dict:
    nodes = operation_graph_nodes(
        operation, configuration, runtime_input, host_context=host_context
    )
    try:
        return run_host_tool(nodes)
    except KeyboardInterrupt:
        # A host interrupt (Ctrl-C, or SIGTERM from the developer's client) ends the request the
        # way a cancelled Agent call does: recorded as the change's lifecycle status and reported
        # through the result envelope.
        cancelled = OperationExecutionError(
            "operation cancelled by the host", outcome="cancelled"
        )
        return finish_failed_operation_graph(nodes, cancelled)["result"]
    except Exception as error:
        return finish_failed_operation_graph(nodes, error)["result"]


ADMISSION_STEPS = (
    "initialize",
    "admit_request",
    "bind_workspace",
    "check_configuration",
    "dispatch",
)


def run_host_tool(nodes):
    """The fixed admission sequence; a failed step goes straight to finalization."""
    state = {}
    for name in ADMISSION_STEPS:
        state.update(nodes[name](state))
        if state.get("result") is not None:
            break
    return nodes["finalize"](state)["result"]


def finish_failed_operation_graph(nodes, error):
    """An unexpected failure still uses the error envelope and final lifecycle evidence."""
    nodes["fail"]({"error": error})
    return nodes["finalize"]({})


def operation_graph_nodes(operation, configuration, runtime_input, *, host_context):
    """Fresh trusted step bindings; neither host authority nor callbacks enter the request."""
    # A top-level request never inherits a lifecycle status a prior request on this same host
    # object left behind; nested requests share the one dict by reference so a child's
    # cancelled/limit_exhausted outcome keeps propagating to its parent.
    lifecycle = {} if host_context.depth == 0 else host_context.lifecycle
    invocation_id = str(uuid.uuid4())
    host = replace(
        host_context,
        invocation_id=invocation_id,
        evidence=[],
        depth=host_context.depth + 1,
        lifecycle=lifecycle,
        root_invocation_id=host_context.root_invocation_id or invocation_id,
    )
    services = host.services
    catalog = services.catalog if services is not None else {}
    declaration = None
    record_progress = False
    run_started = False
    relayed_run_id = None
    data = None
    mutates = False
    host.observe(
        "operation_started",
        operation=operation,
        invocation_id=host.invocation_id,
        depth=host.depth,
    )
    result = {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation if operation in catalog else None,
        "invocation_id": host.invocation_id,
        "mode": host.mode,
        "status": "blocked",
        "workspace": None,
        "output": None,
        "errors": [],
    }

    @timed("admission.request")
    def admit_request():
        nonlocal configuration, data, mutates, declaration
        if services is None:
            raise SpecError(
                "no capability catalog was supplied to admission", "unknown_operation"
            )
        if operation not in catalog:
            raise SpecError("unknown capability", "unknown_operation")
        declaration = check_declaration(copy.deepcopy(dict(catalog[operation])))
        if not declaration["public"] or declaration["capability"] != operation:
            raise SpecError("unknown capability", "unknown_operation")
        if host.mode not in {"execute", "describe-policy"}:
            raise SpecError("unknown operation mode", "invalid_input")
        if host.depth == 1 and services.installation is not None:
            services.installation.verify(host.project_root, host.package_root)
        if host.depth == 1 and declaration["model_backed"]:
            verify_build(host.package_root)
        # Establish the exact entry root before reading configuration or project Specs.
        # A subdirectory must not fail as a misleading missing project instead.
        workspace_identity(host.project_root)
        if declaration["configuration"] == "request":
            if configuration is not None:
                raise SpecError(
                    "this capability takes its configuration from its request; "
                    "the envelope configuration must be null",
                    "invalid_input",
                    "/configuration",
                )
        else:
            configuration = validate_typed(
                configuration
                if configuration is not None
                else load_configuration(host.project_root),
                "concorde-operation-configuration",
            )
        data = copy.deepcopy(
            validate_typed(runtime_input, declaration["request_type"])["data"]
        )
        if declaration["default_task"] is not None:
            data.setdefault("task", declaration["default_task"])
        mutation = declaration["mutation"]
        mutates = mutation["policy"] == "always" or (
            mutation["policy"] == "by-action"
            and data.get("action") in mutation["actions"]
        )
        target = declaration["target"]
        if target["selection"] == "provider-hook":
            data, mutates = resolve_entry(target["hook"], "/target/hook")(
                host.project_root, host.package_root, data
            )
        elif target["selection"] == "bound-module":
            data = bind_module_target(
                host.project_root, host.package_root, data, mutates=mutates
            )

    @timed("admission.workspace")
    def bind_workspace():
        nonlocal host, record_progress
        assert data is not None and declaration is not None
        if declaration["workspace"] == "delivery-session":
            # Runs where it was started; the provider decides whether this worktree takes part.
            _, current = workspace_identity(host.project_root)
            result["workspace"] = (
                {"path": current["path"], "branch": current["branch"]}
                if current
                else None
            )
            return
        host, workspace = bind_worktree(host, mutates, data)
        result["workspace"] = workspace
        if workspace and workspace.get("relay"):
            # The candidate receives this exact request; a request type that records the
            # change carries the candidate's change_id, the others adopt the candidate as is.
            relayed = dict(runtime_input["data"])
            request_type = declaration["request_type"]
            if "change_id" in data_schema(request_type).get("properties", {}):
                relayed["change_id"] = workspace["change_id"]
            invocation = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": operation,
                "mode": host.mode,
                "configuration": None,
                "input": {**runtime_input, "data": relayed},
            }
            target = {key: value for key, value in workspace.items() if key != "relay"}
            host = replace(
                host,
                relay_target={**target, "invocation": invocation, "mutates": mutates},
            )
            # The candidate records its own progress; this request only relays.
            record_progress = False
            return
        record_progress = mutates and host.depth == 1 and not host.native_transport
        if mutates:
            change = read_change(host.project_root)
            if change and (
                change["status"] in {"delivering", "cleanup_pending"}
                or (
                    change.get("delivery")
                    and change.get("cleanup", {}).get("status") == "pending"
                    and change.get("outcome") == "delivered"
                )
            ):
                record_progress = False
                raise SpecError(
                    "this candidate is being delivered; resume delivery from either participating worktree",
                    "delivery_in_progress",
                )

    @timed("admission.configuration")
    def check_configuration():
        nonlocal host, run_started
        assert declaration is not None
        if declaration["configuration"] == "stored":
            if configuration != load_configuration(host.project_root):
                raise SpecError(
                    "invocation configuration differs from initialized project settings",
                    "configuration_mismatch",
                )
            if host.configuration_snapshot and host.configuration_snapshot != canonical(
                configuration
            ):
                raise SpecError(
                    "child configuration differs from the host snapshot",
                    "configuration_mismatch",
                )
            host = replace(host, configuration_snapshot=canonical(configuration))
        if host.mode == "execute":
            from .status_store import primary_root, record_run

            host = replace(host, archive_root=primary_root(host.project_root))
            record_run(host, operation=operation, task=data if mutates else None)
            run_started = True

    def accept_output(output):
        assert declaration is not None
        if (
            not isinstance(output, dict)
            or output.get("type_id") != declaration["response_type"]
        ):
            raise SpecError(
                f"{operation} returned no {declaration['response_type']} value",
                "invalid_completion",
            )
        outcome = output["data"].get("outcome", "completed")
        result.update(
            output=output,
            status="described"
            if host.mode == "describe-policy"
            else "succeeded"
            if outcome in {"completed", "ready", "delivered"}
            else "failed"
            if outcome == "failed"
            else "blocked",
        )

    @timed("admission.dispatch")
    def dispatch():
        nonlocal host, relayed_run_id
        assert data is not None and declaration is not None and services is not None
        target = host.relay_target
        if target is not None:
            runner = host.relay or relay_operation
            envelope, diagnostics = runner(
                host, operation, target["invocation"], Path(target["path"])
            )
            if diagnostics:
                sys.stderr.write(diagnostics.rstrip("\n") + "\n")
                sys.stderr.flush()
            # The candidate's launcher produced the complete envelope, including its own
            # invocation identity; this request adopts it and its run record links to it.
            relayed_run_id = envelope.get("invocation_id")
            result.update(
                invocation_id=envelope["invocation_id"],
                status=envelope["status"],
                output=envelope["output"],
                errors=list(envelope["errors"]),
                workspace=envelope["workspace"],
            )
            return
        if declaration["target"]["selection"] != "none":
            # A request for a Module that does not own the change is admitted only as the
            # component request the owner's Planning records derive; its owner is unchanged.
            change = read_change(host.project_root)
            if (
                change
                and change.get("target_id") not in {None, data["target_id"]}
                and component_request(
                    SpecRepository(host.project_root, host.package_root), change, data
                )
            ):
                host = replace(host, coordinated=True)
            if host.mode == "execute" and mutates:
                bind_owner(host.project_root, data, coordinated=host.coordinated)
        accept_output(
            services.dispatcher(
                AdmittedRequest(
                    operation=operation,
                    declaration=declaration,
                    configuration=configuration,
                    data=data,
                    mutates=mutates,
                    host=host,
                )
            )
        )

    def guarded(step, *, accepts_state=False):
        def node(state):
            updates = {}
            try:
                updates = (step(state) if accepts_state else step()) or {}
            except OperationExecutionError as error:
                lifecycle_status = (
                    "cancelled"
                    if error.outcome == "cancelled"
                    else "limit_exhausted"
                    if error.outcome == "limit_exhausted"
                    else "failed"
                )
                code = (
                    "execution_cancelled"
                    if error.outcome == "cancelled"
                    else "execution_limit"
                    if error.outcome == "limit_exhausted"
                    else "execution_failed"
                )
                host.lifecycle["status"] = lifecycle_status
                result.update(
                    status="failed",
                    errors=[
                        error_entry(
                            error,
                            code=code,
                            layer="admission",
                            attempt=host.invocation_id,
                        )
                    ],
                )
                if error.code:
                    host.lifecycle["status"] = "blocked"
                    result.update(
                        status="blocked",
                        errors=[
                            error_entry(
                                error,
                                code=error.code,
                                layer="admission",
                                attempt=host.invocation_id,
                            )
                        ],
                    )
            except Exception as error:
                # A refusal carries its stable code and blocks; anything else is a failure.
                code = getattr(error, "code", None)
                refused = isinstance(error, (SpecError, TypedDataError)) or (
                    isinstance(code, str) and bool(code)
                )
                result.update(
                    status="blocked" if refused else "failed",
                    errors=[
                        error_entry(
                            error,
                            code=code if refused else None,
                            layer="admission",
                            attempt=host.invocation_id,
                        )
                    ],
                )
            return {
                **updates,
                "result": result if result["errors"] else None,
            }

        return node

    def initialize(state):
        return {"result": None}

    def fail(state):
        def raise_failure():
            result["output"] = None
            raise state["error"]

        return guarded(raise_failure)(state)

    @timed("admission.finalize")
    def finalize(state):
        nonlocal record_progress
        execution_error = host.lifecycle.get("execution_error")
        if execution_error and not result["errors"]:
            # Preserve the failed Review domain output and its incomplete report while
            # reporting the executor interruption through the existing envelope field.
            result["errors"] = [
                {
                    "code": execution_error,
                    "field": "",
                    "message": "Reviewer execution was interrupted.",
                }
            ]
        persistence_error = host.lifecycle.get("persistence_error")
        if persistence_error and not any(
            error["code"] == "state_persistence_failed" for error in result["errors"]
        ):
            # A lost status write is reported beside the retained typed output, never instead of it.
            result["errors"].append(
                {
                    "code": "state_persistence_failed",
                    "field": "",
                    "message": persistence_error,
                }
            )
        if any(
            error["code"]
            in {"incompatible_handoff", "workspace_mismatch", "invalid_worktree_state"}
            for error in result["errors"]
        ):
            record_progress = False
        if (
            record_progress
            and host.mode == "execute"
            and result["status"] not in {"succeeded", "described"}
        ):
            output = result["output"]["data"] if result["output"] else {}
            try:
                progress(
                    host.project_root,
                    status=host.lifecycle.get("status")
                    or ("blocked" if result["status"] == "blocked" else "failed"),
                    outcome=output.get("outcome")
                    or (result["errors"][0]["code"] if result["errors"] else "failed"),
                    blockers=output.get("blockers", []),
                )
            except (ValueError, OSError) as error:
                result["errors"].append(
                    {
                        "code": "state_persistence_failed",
                        "field": "",
                        "message": str(error),
                    }
                )
        if run_started:
            try:
                from .status_store import record_run

                record_run(
                    host,
                    operation=operation,
                    result=result,
                    relayed_run_id=relayed_run_id,
                )
            except (ValueError, OSError) as error:
                result["errors"].append(
                    {
                        "code": "state_persistence_failed",
                        "field": "",
                        "message": str(error),
                    }
                )
                if result["status"] == "succeeded":
                    result["status"] = "blocked"
        host_context.evidence.extend(host.evidence)
        host.observe(
            "operation_finished",
            operation=operation,
            invocation_id=host.invocation_id,
            depth=host.depth,
            status=(
                host.lifecycle["status"]
                if host.lifecycle.get("status") in {"cancelled", "limit_exhausted"}
                else result["status"]
            ),
        )
        return {"result": result}

    return {
        "initialize": initialize,
        "admit_request": guarded(admit_request),
        "bind_workspace": guarded(bind_workspace),
        "check_configuration": guarded(check_configuration),
        "dispatch": guarded(dispatch),
        "finalize": finalize,
        "fail": fail,
    }
