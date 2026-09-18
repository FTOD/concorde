"""Optional Studio adapter; all execution stays behind the public operation host."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NotRequired

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from ..development.operation_host import (
    OperationHost,
    finish_failed_operation_graph,
    invocation_failure,
    operation_graph_nodes,
    validate_invocation,
)
from ..spec.contracts import SKILL_NAMES
from ..spec.repository import SpecError
from ..spec.typed_data import decode
from .worker_executor import WorkerExecutor


class StudioInput(TypedDict):
    invocation: dict[str, Any]
    expected_workspace: NotRequired[dict[str, str] | None]


class StudioOutput(TypedDict):
    result: dict[str, Any] | None
    policies: list[dict[str, Any]]
    events: list[dict[str, Any]]


class StudioState(StudioInput, StudioOutput):
    pass


class StudioRuntimeContext(TypedDict):
    """Invocation-local trusted services; never serialized as graph State."""

    writer: Callable[[dict[str, Any]], None]
    session: NotRequired[dict[str, Any]]


def build_studio_graph(
    operation: str, project_root: Path, package_root: Path, *, executor=None
):
    """Bind to server-owned roots. Requests cannot supply hosts or permissions.

    Hosts and event lists are fresh per invocation; only JSON enters checkpoints.
    The optional executor is a trusted, in-process test seam, never graph input.
    """
    if operation not in SKILL_NAMES:
        raise ValueError(f"Studio entry must be a public operation: {operation}")
    # Preserve the host's symlink-root rejection before normalizing identities.
    bound = OperationHost(project_root, package_root)
    project_root, package_root = bound.project_root, bound.package_root

    def check(state):
        value = state.get("invocation")
        encoded = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        if len(encoded.encode("utf-8")) > 1024 * 1024:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = validate_invocation(decode(encoded), operation)
        expected = state.get("expected_workspace")
        if expected is not None and expected != {
            "project_root": str(project_root),
            "package_root": str(package_root),
        }:
            raise SpecError(
                "Studio server belongs to a different workspace; start a server in this worktree",
                "workspace_mismatch",
            )
        return value

    def validate(state: StudioState):
        try:
            check(state)
            result = None
        except Exception as error:
            result = invocation_failure(operation, error)
        # Reset output on every new run, including rejected runs on reused threads.
        return {"result": result, "policies": [], "events": []}

    def initialize_graph(state, runtime: Runtime[StudioRuntimeContext]):
        if runtime.context is None:
            raise RuntimeError("Studio requires trusted runtime context")
        # Recheck even when resuming directly at the execution checkpoint.
        try:
            value = check(state)
        except Exception as error:
            return {
                "result": invocation_failure(operation, error),
                "policies": [],
                "events": [],
            }
        events = []
        writer = runtime.context["writer"]
        process_executor = (
            executor if executor is not None else WorkerExecutor(package_root)
        )

        def emit(event, **details):
            record = {
                "event": event,
                "time": datetime.now(timezone.utc).isoformat(),
                **details,
            }
            events.append(record)
            writer(record)

        def observed_executor(invocation, **options):
            identity = {
                "operation": invocation.operation,
                "stage": invocation.stage,
                "agent": invocation.agent,
                "invocation_id": invocation.invocation_id,
            }
            host.observe("agent_started", **identity)
            try:
                completion = process_executor(invocation, **options)
            except Exception:
                host.observe("agent_failed", **identity)
                raise
            host.observe("agent_finished", **identity)
            return completion

        host = OperationHost(
            project_root,
            package_root,
            mode=value["mode"],
            executor=observed_executor,
            observer=emit,
        )
        nodes = operation_graph_nodes(
            operation, value["configuration"], value["input"], host_context=host
        )
        runtime.context["session"] = {"nodes": nodes, "host": host, "events": events}
        return {"result": None}

    def bind_node(name):
        if name == "initialize":
            return initialize_graph
        if name == "finalize":

            def finalize(state, runtime: Runtime[StudioRuntimeContext]):
                if runtime.context is None:
                    raise RuntimeError("Studio requires trusted runtime context")
                session = runtime.context.get("session")
                if session is None:
                    return {"result": state["result"], "policies": [], "events": []}
                result = session["nodes"]["finalize"](state)["result"]
                return {
                    "result": result,
                    "policies": session["host"].descriptions,
                    "events": session["events"],
                }

            return finalize

        def call(state, runtime: Runtime[StudioRuntimeContext]):
            if runtime.context is None:
                raise RuntimeError("Studio requires trusted runtime context")
            session = runtime.context.get("session")
            if session is None:
                raise RuntimeError("Studio runtime session is not initialized")
            return session["nodes"][name](state)

        return call

    from ..development.operation_graph import (
        OPERATION_RECURSION_LIMIT,
        build_operation_graph,
        expose_stateless_subgraph,
    )

    operation_graph = build_operation_graph(
        bind_node,
        name=operation,
        input_schema=StudioInput,
        output_schema=StudioOutput,
        context_schema=StudioRuntimeContext,
    )

    def execute(state):
        # Retain the parent's custom stream channel while executing the inspectable subgraph.
        context: StudioRuntimeContext = {"writer": get_stream_writer()}
        try:
            return operation_graph.invoke(
                state, {"recursion_limit": OPERATION_RECURSION_LIMIT}, context=context
            )
        except Exception as error:
            session = context.get("session")
            if session is None:
                return {
                    "result": invocation_failure(operation, error),
                    "policies": [],
                    "events": [],
                }
            result = finish_failed_operation_graph(session["nodes"], error)["result"]
            return {
                "result": result,
                "policies": session["host"].descriptions,
                "events": session["events"],
            }

    builder = StateGraph(
        StudioState, input_schema=StudioInput, output_schema=StudioOutput
    )
    builder.add_node("validate_invocation", validate)
    builder.add_node(operation, execute)
    builder.add_edge(START, "validate_invocation")
    builder.add_conditional_edges(
        "validate_invocation",
        lambda state: END if state["result"] is not None else operation,
        [END, operation],
    )
    builder.add_edge(operation, END)
    compiled = builder.compile(name=operation)
    expose_stateless_subgraph(compiled, operation, operation_graph)
    return compiled
