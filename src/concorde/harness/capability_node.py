"""One State-based node interface for code, model and composed graph Capabilities.

The registry owns identity. Worker profiles are optional execution configuration, not another
kind of executable entity. Wire envelopes are adapted only at the host/process boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from ..spec.typed_data import DATA_SCHEMAS, typed, validate_typed
from .capability_state import CapabilityContext


def typed_state(type_id: str, *, name: str | None = None) -> type:
    """Declare exactly the admitted channels; runtime validation checks required values."""
    fields = {key: Any for key in DATA_SCHEMAS[type_id]["properties"]}
    return TypedDict(name or type_id.replace("-", "_"), fields, total=False)  # type: ignore[misc]


def state_schema(input_type: str, result_type: str | None, *, name: str) -> type:
    fields: dict[str, Any] = {key: Any for key in DATA_SCHEMAS[input_type]["properties"]}
    if result_type:
        fields.update({key: Any for key in DATA_SCHEMAS[result_type]["properties"]})
    else:
        fields["result"] = dict
    return TypedDict(name, fields, total=False)  # type: ignore[misc]


@dataclass(frozen=True)
class CapabilityNode:
    """Resolve a registered Capability and expose its State schemas and compiled node."""
    name: str

    def __post_init__(self):
        name = self.name.removeprefix("concorde-").replace("-", "_")
        from capabilities import CAPABILITIES
        if name not in CAPABILITIES:
            raise ValueError(f"unknown capability: {self.name!r}")
        object.__setattr__(self, "name", name)

    @property
    def definition(self):
        return import_module(f"capabilities.{self.name}")

    @property
    def input_type(self) -> str:
        return self.definition.STATE.input_type

    @property
    def result_type(self) -> str | None:
        return self.definition.STATE.output_type

    @property
    def input_schema(self) -> type:
        return self.definition.STATE.input_schema

    @property
    def output_schema(self) -> type:
        return self.definition.STATE.output_schema

    def flow(self, launcher=None):
        """Compile for direct embedding as a LangGraph subgraph.

        Each invocation supplies trusted CapabilityContext through Runtime, not through State.
        ``launcher`` is a compatibility seam for the host's already-admitted worker invocation.
        No reducer is implicit: these channels have one writer; parent graphs own merge policy.
        """
        module = self.definition
        input_type, result_type = self.input_type, self.result_type

        def invoke(state, runtime: Runtime[CapabilityContext]):
            data = {key: value for key, value in dict(state).items()
                    if key in DATA_SCHEMAS[input_type]["properties"]}
            typed(input_type, data)
            if launcher is not None:
                runtime = Runtime(context=CapabilityContext(launcher=launcher))
            update = module.run(data, runtime)
            if result_type:
                return validate_typed(typed(result_type, update), result_type)["data"]
            if not isinstance(update, dict) or set(update) != {"result"}:
                raise ValueError("a host Capability must return exactly its result channel")
            return update

        graph = StateGraph(state_schema(input_type, result_type, name=self.name),
                           input_schema=self.input_schema, output_schema=self.output_schema,
                           context_schema=CapabilityContext)
        graph.add_node(self.name, invoke)
        graph.add_edge(START, self.name)
        graph.add_edge(self.name, END)
        return graph.compile(name=self.name, checkpointer=False)

    def invoke(self, context: dict, launcher) -> dict:
        """Adapt an existing admitted worker wire value to the same State-based node."""
        value = validate_typed(context, self.input_type)
        return self.flow(launcher).invoke(value["data"])
