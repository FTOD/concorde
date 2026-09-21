"""Explicit optional StateGraph Operation boundary around a trusted native Agent service.

This is not a mirror/scheduler for Concorde native workflows. Callers supply the already-authorized
native launch/admission callable in Runtime context. No default model runner, RPC or ambient fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from inspect import isawaitable
from typing import Any, TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import get_runtime

from ..spec.typed_data import DATA_SCHEMAS, typed, validate_typed
from .operation_state import OperationRuntimeContext
from .worker_profile import (
    validate_worker_input,
    validate_worker_output,
    worker_profile,
)


def typed_state(type_id: str, *, name: str | None = None) -> type:
    return TypedDict(
        name or type_id.replace("-", "_"),
        dict.fromkeys(DATA_SCHEMAS[type_id]["properties"], Any),
        total=False,
    )


def state_schema(input_type: str, result_type: str | None, *, name: str) -> type:
    fields = dict.fromkeys(DATA_SCHEMAS[input_type]["properties"], Any)
    fields.update(
        dict.fromkeys(DATA_SCHEMAS[result_type]["properties"], Any)
        if result_type
        else {"result": dict}
    )
    return TypedDict(name, fields, total=False)


@dataclass(frozen=True)
class OperationNode:
    """A genuine callable typed StateGraph Operation, selected explicitly by its embedding host."""

    name: str

    def __post_init__(self):
        object.__setattr__(self, "name", worker_profile(self.name).name)

    @property
    def definition(self):
        from importlib import import_module

        return import_module("operations." + self.name)

    @property
    def input_type(self):
        return worker_profile(self.name).contract.context

    @property
    def result_type(self):
        return worker_profile(self.name).contract.result

    @property
    def input_schema(self):
        return typed_state(self.input_type)

    @property
    def output_schema(self):
        return typed_state(self.result_type)

    def graph(self, launcher=None):
        profile = worker_profile(self.name)

        def prepare(state, runtime):
            data = {
                k: v
                for k, v in state.items()
                if k in DATA_SCHEMAS[self.input_type]["properties"]
            }
            value = typed(self.input_type, data)
            validate_worker_input(profile, value, phase=profile.contract.phase)
            context = runtime.context if runtime else None
            selected = launcher or (
                context.launcher
                if isinstance(context, OperationRuntimeContext)
                else None
            )
            if selected is None:
                raise RuntimeError(
                    "Operation is inspection only until a trusted native Agent service is supplied"
                )
            return value, selected

        def finish(value):
            # Accept typed result or its data only at this explicit embedding boundary.
            result = (
                value
                if isinstance(value, dict) and value.get("type_id")
                else typed(self.result_type, value)
            )
            validate_worker_output(profile, result)
            return validate_typed(result, self.result_type)["data"]

        def invoke(state):
            runtime = get_runtime()
            value, selected = prepare(state, runtime)
            result = selected(value)
            if isawaitable(result):
                raise RuntimeError(
                    "Use ainvoke for an asynchronous native Agent service"
                )
            return finish(result)

        async def ainvoke(state):
            runtime = get_runtime()
            value, selected = prepare(state, runtime)
            result = selected(value)
            if isawaitable(result):
                result = await result
            return finish(result)

        graph = StateGraph(
            state_schema(
                self.input_type, self.result_type, name="TerminalAgentOperation"
            ),
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            context_schema=OperationRuntimeContext,
        )
        graph.add_node("terminal_agent", RunnableLambda(invoke, afunc=ainvoke))
        graph.add_edge(START, "terminal_agent")
        graph.add_edge("terminal_agent", END)
        return graph.compile(name="terminal_agent_operation", checkpointer=False)

    def invoke(self, context, launcher):
        return self.graph(launcher).invoke(
            validate_typed(context, self.input_type)["data"]
        )
