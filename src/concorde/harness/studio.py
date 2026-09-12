"""Optional Studio adapter; all execution stays behind the public capability host."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from typing_extensions import NotRequired, TypedDict
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from ..spec.typed_data import decode
from ..spec.contracts import SKILL_NAMES
from .agent_executor import AgentProcessExecutor
from ..development.capability_host import (CapabilityHost, capability_flow_nodes, finish_failed_capability_flow,
                                           invocation_failure, validate_invocation)
from ..spec.repository import SpecError


class StudioInput(TypedDict):
    invocation: dict[str, Any]
    expected_workspace: NotRequired[dict[str, str] | None]


class StudioOutput(TypedDict):
    result: dict[str, Any] | None
    policies: list[dict[str, Any]]
    events: list[dict[str, Any]]


class StudioState(StudioInput, StudioOutput):
    pass


def build_studio_flow(capability: str, project_root: Path, package_root: Path, *, executor=None):
    """Bind to server-owned roots. Requests cannot supply hosts or permissions.

    Hosts and event lists are fresh per invocation; only JSON enters checkpoints.
    The optional executor is a trusted, in-process test seam, never graph input.
    """
    if capability not in SKILL_NAMES:
        raise ValueError(f"Studio entry must be a public capability: {capability}")
    # Preserve the host's symlink-root rejection before normalizing identities.
    bound = CapabilityHost(project_root, package_root)
    project_root, package_root = bound.project_root, bound.package_root

    def check(state):
        value = state.get("invocation")
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > 1024 * 1024:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = validate_invocation(decode(encoded), capability)
        expected = state.get("expected_workspace")
        if expected is not None and expected != {
            "project_root": str(project_root), "package_root": str(package_root)
        }:
            raise SpecError("Studio server belongs to a different workspace; start a server in this worktree",
                            "workspace_mismatch")
        return value

    def validate(state: StudioState):
        try:
            check(state)
            result = None
        except Exception as error:
            result = invocation_failure(capability, error)
        # Reset output on every new run, including rejected runs on reused threads.
        return {"result": result, "policies": [], "events": []}

    def initialize_flow(state, runtime: Runtime):
        # Recheck even when resuming directly at the execution checkpoint.
        try:
            value = check(state)
        except Exception as error:
            return {"result": invocation_failure(capability, error), "policies": [], "events": []}
        events = []
        writer = runtime.context["writer"]
        process_executor = executor if executor is not None else AgentProcessExecutor()

        def emit(event, **details):
            record = {"event": event, "time": datetime.now(timezone.utc).isoformat(), **details}
            events.append(record)
            writer(record)

        def observed_executor(launch):
            identity = {"capability": launch.capability, "stage": launch.stage,
                        "role": launch.role, "invocation_id": launch.invocation_id}
            host.observe("agent_started", **identity)
            try:
                completion = process_executor(launch)
            except Exception:
                host.observe("agent_failed", **identity)
                raise
            host.observe("agent_finished", **identity)
            return completion

        host = CapabilityHost(project_root, package_root, mode=value["mode"],
                             executor=observed_executor, observer=emit)
        nodes = capability_flow_nodes(capability, value["configuration"], value["input"], host_context=host)
        runtime.context["session"] = {"nodes": nodes, "host": host, "events": events}
        return {"result": None}

    def bind_node(name):
        if name == "initialize":
            return initialize_flow
        if name == "finalize":
            def finalize(state, runtime: Runtime):
                session = runtime.context.get("session")
                if session is None:
                    return {"result": state["result"], "policies": [], "events": []}
                result = session["nodes"]["finalize"](state)["result"]
                return {"result": result, "policies": session["host"].descriptions,
                        "events": session["events"]}
            return finalize
        def call(state, runtime: Runtime):
            return runtime.context["session"]["nodes"][name](state)
        return call

    from ..development.capability_flow import (build_capability_flow, expose_stateless_subflow,
                                               CAPABILITY_RECURSION_LIMIT)
    capability_flow = build_capability_flow(bind_node, name=capability,
        input_schema=StudioInput, output_schema=StudioOutput, context_schema=dict)

    def execute(state):
        # Retain the parent's custom stream channel while executing the inspectable subflow.
        context = {"writer": get_stream_writer()}
        try:
            return capability_flow.invoke(state, {"recursion_limit": CAPABILITY_RECURSION_LIMIT}, context=context)
        except Exception as error:
            session = context.get("session")
            if session is None:
                return {"result": invocation_failure(capability, error), "policies": [], "events": []}
            result = finish_failed_capability_flow(session["nodes"], error)["result"]
            return {"result": result, "policies": session["host"].descriptions, "events": session["events"]}

    builder = StateGraph(StudioState, input_schema=StudioInput, output_schema=StudioOutput)
    builder.add_node("validate_invocation", validate)
    builder.add_node(capability, execute)
    builder.add_edge(START, "validate_invocation")
    builder.add_conditional_edges("validate_invocation",
        lambda state: END if state["result"] is not None else capability, [END, capability])
    builder.add_edge(capability, END)
    compiled = builder.compile(name=capability)
    expose_stateless_subflow(compiled, capability, capability_flow)
    return compiled


# Retained for existing project entry modules. New authored code calls this a Flow.
build_studio_graph = build_studio_flow
