"""State contracts and trusted runtime context shared by every Capability.

Declarations are dependency-free: schema resolution is lazy so the capability inventory can
also supply the wire-schema registry. State contains data, never hosts, launchers or authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypedDict


class ResultState(TypedDict):
    """A host-backed graph preserves success, rejection and failure in its result channel."""
    result: dict


@dataclass(frozen=True)
class StateContract:
    input_type: str
    output_type: str | None

    @property
    def input_schema(self) -> type:
        from concorde.harness.capability_node import typed_state
        return typed_state(self.input_type)

    @property
    def output_schema(self) -> type:
        from concorde.harness.capability_node import typed_state
        return typed_state(self.output_type) if self.output_type else ResultState


@dataclass(frozen=True)
class CapabilityContext:
    """Trusted, invocation-local LangGraph Runtime context; never a State channel.

    A model launcher must perform the worker admission and execution checks. A host-backed
    graph receives its host and configuration here, not from caller-controlled State.
    """
    host: Any = None
    configuration: dict | None = None
    launcher: Callable[[dict], dict] | None = None


def run_model(profile, state: dict, runtime) -> dict:
    """Execute a model-backed Capability under its own input/output and authority contract."""
    from ..spec.typed_data import typed
    from concorde.harness.worker_profile import validate_worker_input, validate_worker_output

    context = runtime.context
    if not isinstance(context, CapabilityContext) or context.launcher is None:
        raise RuntimeError(f"Capability {profile.name} was compiled for inspection only")
    value = typed(profile.contract.context, dict(state))
    validate_worker_input(profile, value, phase=profile.contract.phase)
    result = typed(profile.contract.result, context.launcher(value))
    validate_worker_output(profile, result)
    return result["data"]


def run_host(name: str, state: dict, runtime) -> ResultState:
    """Adapt State to the existing public wire boundary without losing failure evidence."""
    from ..development.capability_service import run_capability
    from ..spec.typed_data import typed

    context = runtime.context
    if not isinstance(context, CapabilityContext) or context.host is None:
        raise RuntimeError(f"Capability {name} was compiled for inspection only")
    result = run_capability(name, context.configuration, typed(f"{name}-request", dict(state)),
                            host_context=context.host)
    return {"result": result}
