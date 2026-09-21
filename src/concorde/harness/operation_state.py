"""State contracts and trusted runtime context shared by every Operation.

Declarations are dependency-free: schema resolution is lazy so the operation inventory can
also supply the wire-schema registry. State contains data, never hosts, launchers or authority.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypedDict


class ResultState(TypedDict):
    """A host-backed graph preserves success, rejection and failure in its result channel."""

    result: dict


@dataclass(frozen=True)
class StateContract:
    input_type: str
    output_type: str | None

    @property
    def input_schema(self) -> type:
        from concorde.harness.operation_node import typed_state

        return typed_state(self.input_type)

    @property
    def output_schema(self) -> type:
        from concorde.harness.operation_node import typed_state

        return typed_state(self.output_type) if self.output_type else ResultState


@dataclass(frozen=True)
class OperationRuntimeContext:
    """Trusted, invocation-local LangGraph Runtime context; never a State channel.

    A model launcher must perform the worker admission and execution checks. A host-backed
    graph receives its host and configuration here, not from caller-controlled State.
    """

    host: Any = None
    configuration: dict | None = None
    launcher: Callable[[dict], dict] | None = None


@dataclass(frozen=True)
class InvocationRuntime:
    """Dependency-free carrier for trusted Host-tool calls, outside task data."""

    context: OperationRuntimeContext


def run_model(profile, state: dict, runtime) -> dict:
    """Execute a model-backed Operation under its own input/output and authority contract."""
    from concorde.harness.worker_profile import (
        validate_worker_input,
        validate_worker_output,
    )

    from ..spec.typed_data import typed

    context = runtime.context
    if not isinstance(context, OperationRuntimeContext) or context.launcher is None:
        raise RuntimeError(f"Operation {profile.name} was compiled for inspection only")
    value = typed(profile.contract.context, dict(state))
    validate_worker_input(profile, value, phase=profile.contract.phase)
    result = typed(profile.contract.result, context.launcher(value))
    validate_worker_output(profile, result)
    return result["data"]


def run_host(name: str, state: dict, runtime) -> ResultState:
    """Adapt State to the existing public wire boundary without losing failure evidence."""
    from ..spec.typed_data import typed
    from .admission import run_operation

    context = runtime.context
    if not isinstance(context, OperationRuntimeContext) or context.host is None:
        raise RuntimeError(f"Operation {name} was compiled for inspection only")
    result = run_operation(
        name,
        context.configuration,
        typed(f"{name}-request", dict(state)),
        host_context=context.host,
    )
    return {"result": result}
