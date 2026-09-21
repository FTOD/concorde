"""Admission of every operation invocation: the operation Graph's trusted node bindings.

Every request is initialized, admitted against its registered contract, bound to its
workspace and checked against the initialized configuration before direct Host-tool dispatch
or the selected Graph runs; every outcome, admitted or not, ends in one typed result envelope.
"""

from __future__ import annotations

import copy
import os
import uuid
from dataclasses import replace
from pathlib import Path

from ..distribution.build import BuildError, verify_fresh
from ..operations.dispatch import dispatch_graph_nodes
from ..spec.contracts import DETERMINISTIC_OPERATIONS
from ..spec.repository import SpecError
from ..spec.typed_data import (
    DATA_SCHEMAS,
    OPERATION_CONTRACTS,
    TypedDataError,
    canonical,
    validate_typed,
)
from .change_worktree import progress, read_change, resume_owner, workspace_identity
from .configuration import load_configuration
from .host import OperationHost, resolve_child_operation
from .relay import bind_worktree, verify_local_execution
from .worker_executor import OperationExecutionError
from .worker_profile import ContractError
from .timing import timed, traced_operation


def invoke_operation(
    parent_operation: str,
    child_operation: str,
    configuration: dict,
    payload: dict,
    host: OperationHost,
) -> dict:
    """Adapt existing host-wire composition to an Operation's State-based ``run``.

    Development, Issue solving and recursive per-component review use this transport adapter.
    Model nodes use their own admitted State via OperationNode; both paths check the same USES
    relation. A wire adapter is not a second kind of executable identity.
    """

    child_module = resolve_child_operation(parent_operation, child_operation)
    return run_host_node(
        child_module.run, host, configuration, payload, child_operation
    )


def run_host_node(runner, host, configuration, payload, operation):
    """The wire boundary adapts to State; trusted execution context never enters State."""
    from .operation_state import InvocationRuntime, OperationRuntimeContext

    validate_typed(payload, f"{operation}-request")
    return runner(
        payload["data"],
        InvocationRuntime(
            context=OperationRuntimeContext(host=host, configuration=configuration)
        ),
    )["result"]


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
        data = runtime_input.get("data") if isinstance(runtime_input, dict) else None
        action = data.get("action") if isinstance(data, dict) else None
        if (
            operation
            in {
                "concorde-context-solve",
                "concorde-plan",
                "concorde-tasks",
                "concorde-implement",
                "concorde-spec-review",
                "concorde-code-review",
            }
            or operation in DETERMINISTIC_OPERATIONS
            or (operation == "concorde-issues" and action != "solve")
        ):
            return run_host_tool(nodes)
        try:
            from .operation_graph import (
                OPERATION_RECURSION_LIMIT,
                build_operation_graph,
            )
        except ModuleNotFoundError as error:
            if error.name == "langgraph" or (error.name or "").startswith("langgraph."):
                raise SpecError(
                    "the selected Graph backend requires the configured LangGraph runtime",
                    "missing_runtime",
                ) from error
            raise

        return build_operation_graph(nodes.__getitem__, name=operation).invoke(
            {}, {"recursion_limit": OPERATION_RECURSION_LIMIT}
        )["result"]
    except KeyboardInterrupt:
        # A host interrupt (Ctrl-C, or SIGTERM from the developer's client) that arrives outside
        # a worker launch ends the Graph the way a cancelled worker does: the cancellation is
        # recorded in the change's lifecycle evidence and reported through the result envelope.
        cancelled = OperationExecutionError(
            "operation cancelled by the host", outcome="cancelled"
        )
        return finish_failed_operation_graph(nodes, cancelled)["result"]
    except Exception as error:
        return finish_failed_operation_graph(nodes, error)["result"]


def _is_graph_command(value):
    # Graph commands remain supported only when an explicit graph actually
    # returns one. Deterministic tool admission imports no LangGraph runtime.
    if value is None or isinstance(value, dict):
        return False
    from langgraph.types import Command

    return isinstance(value, Command)


def run_host_tool(nodes):
    """Finite deterministic admission/dispatch, not model orchestration.

    Providers retain schema, worktree, configuration, evidence and finalization
    checks. No model callback or arbitrary node sequence is admitted here.
    """
    state = {}
    for name in (
        "initialize",
        "admit_request",
        "bind_workspace",
        "check_configuration",
    ):
        state.update(nodes[name](state))
        if state.get("result") is not None:
            return nodes["finalize"](state)["result"]
    state.update(nodes["dispatch/select_operation"](state))
    if state.get("result") is not None:
        return nodes["finalize"](state)["result"]
    route = state["route"]
    if route == "prepare_target":
        state.update(nodes["dispatch/prepare_target/bind_target"](state))
        route = state["route"]
    if route == "issues":
        state.update(nodes["dispatch/issues/select_operation"](state))
        route = state["route"]
        if route in {"inspect", "report", "reopen"}:
            state.update(nodes["dispatch/issues/" + route](state))
        elif route != "__end__":
            raise SpecError(
                "model workflow cannot execute as a Host tool", "invalid_input"
            )
    elif route in {
        "relay",
        "deliver",
        "project",
        "validate",
        "describe_policy",
        "context_solve",
        "plan",
        "tasks",
        "implement",
        "review",
    }:
        state.update(nodes["dispatch/" + route](state))
    elif route != "__end__":
        raise SpecError("not a deterministic Host tool", "invalid_input")
    return nodes["finalize"](state)["result"]


def finish_failed_operation_graph(nodes, error):
    """A scheduler failure still uses the host's error envelope and final lifecycle evidence."""
    nodes["fail"]({"error": error})
    return nodes["finalize"]({})


def operation_graph_nodes(operation, configuration, runtime_input, *, host_context):
    """Fresh trusted node bindings; neither host authority nor callbacks enter the public input."""
    END = "__end__"

    # A depth-1 (top-level) invocation never inherits a lifecycle status a prior invocation on
    # this same host object left behind; nested calls still share the one dict by reference so a
    # child's cancelled/limit_exhausted outcome keeps propagating to its enclosing loop.
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
    record_progress = False
    run_started = False
    task = None
    mutation = False
    host.observe(
        "operation_started",
        operation=operation,
        invocation_id=host.invocation_id,
        depth=host.depth,
    )
    result = {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation if operation in OPERATION_CONTRACTS else None,
        "invocation_id": host.invocation_id,
        "mode": host.mode,
        "status": "blocked",
        "workspace": None,
        "output": None,
        "errors": [],
    }

    @timed("admission.request")
    def admit_request():
        nonlocal configuration, task, mutation
        if os.environ.get("CONCORDE_WORKER_POLICY"):
            raise SpecError(
                "terminal workers cannot invoke Operations", "permission_denied"
            )
        if operation not in OPERATION_CONTRACTS:
            raise SpecError("unknown registered operation", "unknown_operation")
        if host.mode not in {"execute", "describe-policy"}:
            raise SpecError("unknown operation mode", "invalid_input")
        if host.depth == 1:
            verify_local_execution(host)
        if host.depth == 1 and operation not in DETERMINISTIC_OPERATIONS:
            # The build is the only instruction source. Deterministic operations run no agent
            # cognition and load no WorkerProfile, so they never consume generated/; every other
            # top-level invocation is verified once here, and load_model_instructions verifies it
            # again independently before trusting any generated/agents/*.md body.
            verify_fresh(host.package_root)
        # Establish the exact entry root before reading configuration or project Specs.
        # A subdirectory must not fail as a misleading missing project instead.
        workspace_identity(host.project_root)
        configuration = validate_typed(
            configuration
            if configuration is not None
            else load_configuration(host.project_root),
            "concorde-operation-configuration",
        )
        task = validate_typed(runtime_input, OPERATION_CONTRACTS[operation][0])["data"]
        task = copy.deepcopy(task)
        if operation not in {"concorde-deliver", "concorde-issues"}:
            task.setdefault("task", "Inspect the selected records")
        mutation = operation not in {
            "concorde-context-solve",
            "concorde-spec-review",
            "concorde-code-review",
        }
        if operation == "concorde-init":
            mutation = task["action"] == "apply"
        if operation == "concorde-issues":
            from ..issues.graph import prepare_request

            # Issue selection, attribution and current bytes are host-bound before workspace creation.
            task = prepare_request(host.project_root, host.package_root, task)
            mutation = task["action"] == "solve" and not task.get("_issue_closed")
        if operation not in {"concorde-init", "concorde-configure", "concorde-deliver"}:
            from ..spec.repository import SpecRepository

            repository = SpecRepository(host.project_root, host.package_root)
            if mutation:
                change = read_change(host.project_root)
                if change:
                    owner = change.get("target_id")
                    if owner is not None and owner not in repository.targets:
                        raise SpecError(
                            "recorded change owner is not registered",
                            "invalid_worktree_state",
                            field="target_id",
                        )
                    # Restore only this change's intent. Separately admitted component work
                    # retains its explicit task and is checked by target admission below.
                    if owner in {None, task["target_id"]}:
                        task = resume_owner(change, task)
            repository.select(task["target_id"], task.get("focus_id"))

    @timed("admission.workspace")
    def bind_workspace():
        nonlocal host, record_progress
        assert task is not None, "workspace binding requires an admitted task"
        if operation == "concorde-deliver":
            from .worktree_delivery import require_delivery_session

            primary = require_delivery_session(host, task["change_id"])
            workspace = {"path": primary["path"], "branch": primary["branch"]}
        elif operation == "concorde-issues" and (
            task["action"] != "solve" or task.get("_issue_closed")
        ):
            workspace = (
                None  # bookkeeping operations do not create a development candidate
            )
        else:
            host, workspace = bind_worktree(host, mutation, task)
        result["workspace"] = workspace
        if workspace and workspace.get("relay"):
            candidate = Path(workspace["path"])
            if operation == "concorde-issues":
                from ..issues.graph import copy_selection

                copy_selection(host.project_root, candidate, task)
            # The candidate receives this exact request; a request type that records the
            # change carries the candidate's change_id, the others adopt the candidate as is.
            data = dict(runtime_input["data"])
            request_type = OPERATION_CONTRACTS[operation][0]
            if "change_id" in DATA_SCHEMAS[request_type].get("properties", {}):
                data["change_id"] = workspace["change_id"]
            invocation = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": operation,
                "mode": host.mode,
                "configuration": None,
                "input": {**runtime_input, "data": data},
            }
            target = {key: value for key, value in workspace.items() if key != "relay"}
            host = replace(host, relay_target={**target, "invocation": invocation})
            # The candidate records its own progress; this invocation only relays.
            record_progress = False
            return
        record_progress = (
            mutation
            and operation != "concorde-deliver"
            and host.depth == 1
            and not host.native_transport
        )
        if mutation and operation != "concorde-deliver":
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
        if operation != "concorde-init" and configuration != load_configuration(
            host.project_root
        ):
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
        if host.mode == "execute" and host.relay_target is None:
            from .status_store import primary_root, record_run

            host = replace(host, archive_root=primary_root(host.project_root))
            record_run(host, operation=operation, task=task if mutation else None)
            run_started = True

    def accept_output(output):
        outcome = output["data"].get("outcome", "completed")
        result.update(
            output=output,
            status="described"
            if host.mode == "describe-policy"
            else "succeeded"
            if outcome
            in {
                "completed",
                "ready",
                "delivered",
            }
            else "failed"
            if outcome == "failed"
            else "blocked",
        )

    dispatch_nodes = None

    def dispatch(name, state):
        nonlocal dispatch_nodes
        if dispatch_nodes is None:
            dispatch_nodes = dispatch_graph_nodes(operation, configuration, task, host)
        updates = dispatch_nodes[name](state)
        payload = (updates.update or {}) if _is_graph_command(updates) else updates
        if isinstance(payload.get("relayed"), dict):
            # The candidate's launcher produced the complete envelope; adopt it as this
            # invocation's result rather than deriving a second status from its output.
            relayed = payload["relayed"]
            result.update(
                status=relayed["status"],
                output=relayed["output"],
                errors=list(relayed["errors"]),
                workspace=relayed["workspace"],
            )
        elif (
            isinstance(payload.get("output"), dict)
            and payload["output"].get("type_id") == OPERATION_CONTRACTS[operation][1]
        ):
            accept_output(payload["output"])
        return updates

    def guarded(operation, *, accepts_state=False):
        def node(state):
            updates = {}
            try:
                updates = (operation(state) if accepts_state else operation()) or {}
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
                    errors=[{"code": code, "field": "", "message": str(error)}],
                )
                if error.code:
                    host.lifecycle["status"] = "blocked"
                    result.update(
                        status="blocked",
                        errors=[
                            {"code": error.code, "field": "", "message": str(error)}
                        ],
                    )
            except (SpecError, TypedDataError, ContractError) as error:
                result["errors"] = [
                    {"code": error.code, "field": error.field, "message": str(error)}
                ]
            except BuildError as error:
                result["errors"] = [
                    {"code": error.code, "field": "", "message": str(error)}
                ]
            except Exception as error:
                result.update(
                    status="failed",
                    errors=[
                        {"code": "execution_failed", "field": "", "message": str(error)}
                    ],
                )
            if _is_graph_command(updates):
                from langgraph.types import Command

                # A node that selects its own transition keeps it unless the guard recorded an
                # error, which ends the Graph with the typed failure envelope in state.
                if result["errors"]:
                    return Command(
                        goto=END, update={**(updates.update or {}), "result": result}
                    )
                return Command(
                    goto=updates.goto, update={**(updates.update or {}), "result": None}
                )
            return {
                **updates,
                "result": result if result["errors"] else None,
                **({"route": "__end__"} if result["errors"] else {}),
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
            data = result["output"]["data"] if result["output"] else {}
            try:
                progress(
                    host.project_root,
                    status=host.lifecycle.get("status")
                    or ("blocked" if result["status"] == "blocked" else "failed"),
                    outcome=data.get("outcome")
                    or (result["errors"][0]["code"] if result["errors"] else "failed"),
                    blockers=data.get("blockers", []),
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

                record_run(host, operation=operation, result=result)
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

    from ..operations.dispatch_graph import DISPATCH_NODES

    return {
        "initialize": initialize,
        "admit_request": guarded(admit_request),
        "bind_workspace": guarded(bind_workspace),
        "check_configuration": guarded(check_configuration),
        "finalize": finalize,
        "fail": fail,
        **{
            "dispatch/" + name: guarded(
                lambda state, name=name: dispatch(name, state), accepts_state=True
            )
            for name in DISPATCH_NODES
        },
    }
