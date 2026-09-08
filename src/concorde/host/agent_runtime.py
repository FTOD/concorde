"""Trusted recursive Agent scheduling; model decisions never carry execution authority."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic
from typing import Callable
from uuid import uuid4

from .typed_data import canonical, decode, json_schema, typed, validate_typed
from ..specification.repository import digest


class InvalidAgentStep(ValueError):
    """An attested decision cannot be decoded into the Agent step contract."""


@dataclass(frozen=True)
class AgentConstraints:
    targets: frozenset[str]
    delegates: frozenset[str]
    max_steps: int = 8


@dataclass(frozen=True)
class AgentGrant:
    targets: frozenset[str]
    agents: frozenset[str]


@dataclass(frozen=True)
class AgentLimits:
    max_calls: int = 16
    max_depth: int = 4
    max_decisions: int = 64
    timeout_seconds: float = 300

    def __post_init__(self):
        from math import isfinite
        for name in ("max_calls", "max_depth", "max_decisions"):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == "max_depth" else 1):
                raise ValueError(f"invalid {name}")
        if (type(self.timeout_seconds) not in (int, float)
                or not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0):
            raise ValueError("invalid timeout_seconds")


@dataclass(frozen=True)
class AgentStep:
    source: str
    action: str
    agent_id: str | None = None
    value: dict | None = None
    outcome: str = "completed"
    details: dict | None = None


@dataclass(frozen=True)
class AgentResult:
    invocation_id: str
    parent_id: str | None
    agent_id: str
    outcome: str
    value_json: str | None
    error: str | None
    details_json: str | None = None

    def wire(self) -> dict:
        return {"invocation_id": self.invocation_id, "parent_id": self.parent_id,
                "agent_id": self.agent_id, "outcome": self.outcome,
                "value_json": self.value_json, "error": self.error,
                "details": decode(self.details_json) if self.details_json else None}


@dataclass(frozen=True)
class AgentFrame:
    invocation_id: str
    parent_id: str | None
    agent_id: str
    input_json: str
    context_json: str
    spec: str
    feedback: tuple[AgentResult, ...]
    children_json: str
    result_schema_json: str
    remaining_seconds: float
    deadline: float


@dataclass(frozen=True)
class Harness:
    id: str
    decide: Callable[[AgentFrame], AgentStep]
    configuration_json: str

    def __post_init__(self):
        if not isinstance(self.configuration_json, str):
            raise ValueError("Harness configuration must be serialized JSON")
        configuration = decode(self.configuration_json)
        references = {"model_integration", "context_assembly", "control_loop", "state_handling",
                      "system_environment", "implementation"}
        catalogs = {"capabilities", "tools", "skills"}
        if (not isinstance(configuration, dict) or set(configuration) != references | catalogs
                or any(not isinstance(configuration[key], str) or not configuration[key].strip()
                       for key in references)
                or any(not isinstance(configuration[key], list)
                       or any(not isinstance(item, str) or not item.strip() for item in configuration[key])
                       or len(configuration[key]) != len(set(configuration[key])) for key in catalogs)):
            raise ValueError("Harness requires complete configuration references")
        object.__setattr__(self, "configuration_json", canonical(configuration))


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    spec_path: Path
    harness: Harness
    constraints: AgentConstraints
    input_type: str
    result_type: str


@dataclass(frozen=True)
class AgentRun:
    result: AgentResult
    events: tuple[dict, ...]


def _names(values) -> bool:
    return isinstance(values, frozenset) and all(isinstance(v, str) and v.strip() for v in values)


class AgentRuntime:
    """Host-owned definitions, context resolver and authority; fresh counters for every root call.

    Python callbacks are trusted host code, not an execution sandbox for user-authored Python.
    The model-facing protocol consists only of AgentFrame and AgentStep.
    """

    def __init__(self, definitions, resolve_context, *, limits=AgentLimits(), cancelled=lambda: False):
        definitions = tuple(definitions)
        self._definitions = {definition.id: definition for definition in definitions}
        if len(self._definitions) != len(definitions) or not definitions:
            raise ValueError("Agent IDs must be unique and nonempty")
        self._specs = {}
        for definition in definitions:
            constraints = definition.constraints
            if (not isinstance(definition.id, str) or not definition.id.strip()
                    or not definition.harness.id or not callable(definition.harness.decide)
                    or not _names(constraints.targets) or not constraints.targets
                    or not _names(constraints.delegates)
                    or not constraints.delegates <= self._definitions.keys()
                    or type(constraints.max_steps) is not int or constraints.max_steps < 1):
                raise ValueError("invalid Agent definition or unresolved child binding")
            path = Path(definition.spec_path)
            if path.name != "spec.md" or path.is_symlink():
                raise ValueError("Agent requires an authored spec.md")
            body = path.read_text(encoding="utf-8")
            if not body.strip():
                raise ValueError("empty Agent Spec")
            self._specs[definition.id] = body
            json_schema(definition.input_type)
            json_schema(definition.result_type)
        if not callable(resolve_context) or not callable(cancelled) or not isinstance(limits, AgentLimits):
            raise ValueError("invalid runtime configuration")
        self._resolve_context, self._limits, self._cancelled = resolve_context, limits, cancelled

    def invoke(self, agent_id: str, input: dict, grant: AgentGrant) -> AgentRun:
        if not isinstance(grant, AgentGrant) or not _names(grant.targets) or not _names(grant.agents):
            raise ValueError("host-issued AgentGrant required")
        tree = _Tree(self, grant)
        result = tree.call(agent_id, input, grant, None, 0)
        return AgentRun(result, tuple(tree.events))


class _Tree:
    def __init__(self, runtime, grant):
        self.runtime = runtime
        self.deadline = monotonic() + runtime._limits.timeout_seconds
        self.calls = self.decisions = 0
        self.events = []

    def stopped(self):
        if self.runtime._cancelled():
            return "cancelled"
        if monotonic() >= self.deadline:
            return "limit_exhausted"
        return None

    def call(self, agent_id, input, grant, parent_id, depth):
        invocation_id = str(uuid4())

        def finish(outcome, value=None, error=None, details=None):
            result = AgentResult(invocation_id, parent_id, agent_id, outcome,
                canonical(value) if value is not None else None, error,
                canonical(details) if details is not None else None)
            self.events.append({"event": "return", **result.wire()})
            return result

        stop = self.stopped()
        if stop:
            return finish(stop, error=stop)
        limits = self.runtime._limits
        if depth > limits.max_depth or self.calls >= limits.max_calls:
            return finish("limit_exhausted", error="call_limit")
        definition = self.runtime._definitions.get(agent_id)
        if definition is None or agent_id not in grant.agents:
            return finish("rejected", error="agent_not_admitted")
        effective = AgentGrant(grant.targets & definition.constraints.targets, grant.agents)
        try:
            if not effective.targets:
                raise ValueError("empty target grant")
            admitted_input = validate_typed(input, definition.input_type)
            # The built-in task contract has a target hint, never a permission grant.
            if (definition.input_type == "concorde-agent-task"
                    and admitted_input["data"]["target_id"] not in effective.targets):
                raise ValueError("task target is outside the grant")
            if Path(definition.spec_path).read_text(encoding="utf-8") != self.runtime._specs[agent_id]:
                raise ValueError("Agent Spec changed")
            context = validate_typed(self.runtime._resolve_context(definition, admitted_input, effective),
                                     "concorde-context-snapshot")
            snapshot = context["data"]
            if snapshot["context_id"] != digest({key: value for key, value in snapshot.items() if key != "context_id"}):
                raise ValueError("context identity is invalid")
            if snapshot["implementation_artifacts"]:
                raise ValueError("read-only analysis cannot admit implementation artifacts")
            if snapshot["target_id"] not in effective.targets or snapshot["phase"] != "ask":
                raise ValueError("context is outside the read-only grant")
            if (definition.input_type == "concorde-agent-task"
                    and snapshot["target_id"] != admitted_input["data"]["target_id"]):
                raise ValueError("context target differs from admitted task")
        except Exception:
            stop = self.stopped()
            return finish(stop or "rejected", error=stop or "admission_failed")
        stop = self.stopped()
        if stop:
            return finish(stop, error=stop)
        self.calls += 1
        input_json, context_json = canonical(admitted_input), canonical(context)
        binding = {"agent_id": agent_id, "spec": self.runtime._specs[agent_id],
            "harness": definition.harness.id, "harness_configuration": definition.harness.configuration_json,
            "input_json": input_json, "context_json": context_json,
            "targets": sorted(effective.targets), "agents": sorted(effective.agents),
            "delegates": sorted(definition.constraints.delegates),
            "max_steps": definition.constraints.max_steps,
            "limits": asdict(limits),
            "input_type": definition.input_type, "result_type": definition.result_type}
        self.events.append({"event": "admit", "invocation_id": invocation_id,
            "parent_id": parent_id, "agent_id": agent_id, "depth": depth,
            "binding_digest": digest(binding), "context_id": snapshot["context_id"],
            "harness_id": definition.harness.id,
            "harness_configuration_json": definition.harness.configuration_json})
        children = []
        for child_id in sorted(definition.constraints.delegates & effective.agents):
            child = self.runtime._definitions[child_id]
            if not child.constraints.targets & effective.targets:
                continue
            children.append({"agent_id": child_id, "input_type": child.input_type,
                "result_type": child.result_type,
                "input_schema_json": canonical(json_schema(child.input_type)),
                "result_schema_json": canonical(json_schema(child.result_type))})
        feedback = []
        for _ in range(definition.constraints.max_steps):
            stop = self.stopped()
            if stop or self.decisions >= limits.max_decisions:
                return finish(stop or "limit_exhausted", error=stop or "decision_limit")
            try:
                if Path(definition.spec_path).read_text(encoding="utf-8") != self.runtime._specs[agent_id]:
                    return finish("rejected", error="stale_definition")
                current = validate_typed(self.runtime._resolve_context(definition,
                    decode(input_json), effective), "concorde-context-snapshot")
                stop = self.stopped()
                if stop:
                    return finish(stop, error=stop)
                if canonical(current) != context_json:
                    return finish("rejected", error="stale_context")
                frame = AgentFrame(invocation_id, parent_id, agent_id, input_json, context_json,
                    self.runtime._specs[agent_id], tuple(feedback), canonical(children),
                    canonical(json_schema(definition.result_type)), self.deadline - monotonic(), self.deadline)
                self.decisions += 1
                try:
                    step = definition.harness.decide(frame)
                except InvalidAgentStep:
                    stop = self.stopped()
                    return finish(stop or "rejected", error=stop or "invalid_step")
            except Exception:
                stop = self.stopped()
                return finish(stop or "failed", error=stop or "execution_failed")
            stop = self.stopped()
            if stop:
                return finish(stop, error=stop)
            try:
                if not isinstance(step, AgentStep):
                    raise ValueError("not an AgentStep")
                typed("concorde-agent-loop-step", {"source": step.source, "action": step.action,
                    "agent_id": step.agent_id, "value_json": canonical(step.value) if step.value is not None else None,
                    "outcome": step.outcome, "details": step.details})
                if step.action == "delegate":
                    if not step.agent_id or step.value is None or step.outcome != "completed" or step.details is not None:
                        raise ValueError("invalid delegation")
                elif step.agent_id is not None:
                    raise ValueError("completion cannot select a child")
                elif step.outcome == "completed":
                    validate_typed(step.value, definition.result_type)
                    if step.details is not None:
                        raise ValueError("completion cannot include interruption")
                else:
                    if step.value is not None:
                        raise ValueError("noncompletion cannot include result")
                    self.interruption(step, snapshot)
            except Exception:
                return finish("rejected", error="invalid_step")
            self.events.append({"event": "decision", "invocation_id": invocation_id,
                "source": step.source, "action": step.action, "child_agent": step.agent_id})
            if step.action == "complete":
                return finish(step.outcome, step.value, details=step.details)
            if step.agent_id not in definition.constraints.delegates or step.agent_id not in effective.agents:
                feedback.append(AgentResult(str(uuid4()), invocation_id, step.agent_id,
                                            "rejected", None, "delegation_denied"))
                self.events.append({"event": "return", **feedback[-1].wire()})
            else:
                feedback.append(self.call(step.agent_id, step.value, effective, invocation_id, depth + 1))
            if feedback[-1].outcome in {"cancelled", "limit_exhausted"}:
                return finish(feedback[-1].outcome, error=feedback[-1].error)
        return finish("limit_exhausted", error="step_limit")

    @staticmethod
    def interruption(step, snapshot):
        if step.outcome not in {"spec_incomplete", "waiting"}:
            if step.details is not None:
                raise ValueError("unexpected interruption details")
            return
        details = validate_typed(step.details, "concorde-agent-interruption")["data"]
        if step.outcome == "waiting":
            if not details["decision"] or details["gaps"]:
                raise ValueError("waiting requires only a decision question")
        else:
            if not details["gaps"] or details["decision"] is not None:
                raise ValueError("Spec incomplete requires only gaps")
            for gap in details["gaps"]:
                if any(gap[key] != snapshot[key] for key in ("target_id", "context_id")):
                    raise ValueError("gap does not match snapshot")
