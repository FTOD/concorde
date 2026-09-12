"""Trusted recursive Agent scheduling; model decisions never carry execution authority."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic
from typing import Callable
from uuid import uuid4

from ..spec.typed_data import canonical, decode, json_schema, typed, validate_typed
from .agent_model import Agent, AgentBinding, agent_definition, binding_json, resolve_agent
from .harness import HARNESSES
from .agent_executor import CapabilityExecutionError
from ..spec.repository import digest


class InvalidAgentStep(ValueError):
    """An attested decision cannot be decoded into the Agent step contract."""


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
    agent_binding_json: str | None = None


@dataclass(frozen=True)
class RuntimeAgent:
    """A host graph binding to the canonical Agent model, not another Agent definition."""

    agent: Agent
    decide: Callable[[AgentFrame], AgentStep]
    package_root: Path
    targets: frozenset[str]
    delegates: frozenset[str]
    decision_reference: str
    input_type: str = "concorde-agent-task"
    result_type: str = "concorde-agent-answer"
    max_steps: int = 8
    binding: AgentBinding | None = None

    @property
    def id(self) -> str:
        return self.agent.name

    @property
    def spec_path(self) -> Path:
        return self.package_root / self.agent.spec

    @property
    def timeout_seconds(self) -> float:
        values = [self.agent.harness.loop.timeout_seconds]
        if self.agent.constraints.limits is not None:
            values.append(self.agent.constraints.limits.timeout_seconds)
        return min(values)


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
        from ..spec.contracts import load_capability_inventory
        capability_names = {"concorde-" + name.replace("_", "-")
                            for name in load_capability_inventory().CAPABILITIES}
        definitions = tuple(definitions)
        self._definitions = {definition.id: definition for definition in definitions}
        if len(self._definitions) != len(definitions) or not definitions:
            raise ValueError("Agent IDs must be unique and nonempty")
        self._specs = {}
        for definition in definitions:
            constraints = definition
            if (not isinstance(definition.id, str) or not definition.id.strip()
                    or not isinstance(definition.agent, Agent) or not callable(definition.decide)
                    or not isinstance(definition.decision_reference, str) or not definition.decision_reference.strip()
                    or not _names(constraints.targets) or not constraints.targets
                    or not _names(constraints.delegates)
                    or not constraints.delegates <= self._definitions.keys()
                    or type(constraints.max_steps) is not int or constraints.max_steps < 1):
                raise ValueError("invalid Agent definition or unresolved child binding")
            agent = definition.agent
            if (HARNESSES.get(agent.harness.name) != agent.harness
                    or agent.constraints.effects.writes or agent.constraints.effects.network
                    or agent.constraints.effects.credentials != "none"
                    or set(agent.constraints.effects.reads) - set(agent.harness.effects.reads)
                    or set(agent.constraints.capabilities) - capability_names
                    or set(agent.constraints.capabilities) - set(agent.harness.capabilities)
                    or set(agent.constraints.contexts) - set(agent.harness.contexts)
                    or set(agent.constraints.results) - set(agent.harness.results)
                    or type(agent.constraints.allow_delegation) is not bool
                    or (agent.constraints.allow_delegation and (
                        "concorde-agent-loop-context" not in agent.constraints.contexts
                        or "concorde-agent-loop-step" not in agent.constraints.results))
                    or definition.input_type not in agent.constraints.contexts
                    or definition.result_type not in agent.constraints.results
                    or (definition.delegates and not agent.constraints.allow_delegation)):
                raise ValueError("runtime binding exceeds the canonical Agent contract")
            if definition.binding is not None and (agent_definition(agent.name) != agent
                    or resolve_agent(definition.package_root, agent.name) != definition.binding):
                raise ValueError("native Agent binding is stale")
            if getattr(definition.decide, "requires_binding", False) and definition.binding is None:
                raise ValueError("native decisions require a registered Agent binding")
            path = Path(definition.spec_path)
            if path.name != "spec.md" or path.is_symlink():
                raise ValueError("Agent requires an authored spec.md")
            body = path.read_bytes().decode("utf-8")
            if not body.strip():
                raise ValueError("empty Agent Spec")
            self._specs[definition.id] = body
            json_schema(definition.input_type)
            json_schema(definition.result_type)
        if not callable(resolve_context) or not callable(cancelled) or not isinstance(limits, AgentLimits):
            raise ValueError("invalid runtime configuration")
        self._resolve_context, self._limits, self._cancelled = resolve_context, limits, cancelled

    def _spec_current(self, definition: RuntimeAgent) -> bool:
        path = Path(definition.spec_path)
        try:
            return (not path.is_symlink()
                    and path.read_bytes().decode("utf-8") == self._specs[definition.id])
        except (OSError, UnicodeError):
            return False

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

    def stopped(self, deadline=None):
        if self.runtime._cancelled():
            return "cancelled"
        if monotonic() >= min(self.deadline, deadline if deadline is not None else self.deadline):
            return "limit_exhausted"
        return None

    def call(self, agent_id, input, grant, parent_id, depth, deadline=None):
        deadline = self.deadline if deadline is None else min(self.deadline, deadline)
        stopped = lambda: self.stopped(deadline)
        invocation_id = str(uuid4())

        def finish(outcome, value=None, error=None, details=None):
            result = AgentResult(invocation_id, parent_id, agent_id, outcome,
                canonical(value) if value is not None else None, error,
                canonical(details) if details is not None else None)
            self.events.append({"event": "return", **result.wire()})
            return {"result": result}

        from .agent_flow import build_agent_flow

        definition = effective = input_json = context_json = snapshot = children = limits = step = None
        feedback = []
        steps = 0

        def admit(state):
            nonlocal definition, deadline, effective, input_json, context_json, snapshot, children, limits
            stop = stopped()
            if stop:
                return finish(stop, error=stop)
            limits = self.runtime._limits
            if depth > limits.max_depth or self.calls >= limits.max_calls:
                return finish("limit_exhausted", error="call_limit")
            self.calls += 1
            definition = self.runtime._definitions.get(agent_id)
            if definition is None or agent_id not in grant.agents:
                return finish("rejected", error="agent_not_admitted")
            deadline = min(deadline, monotonic() + definition.timeout_seconds)
            effective = AgentGrant(grant.targets & definition.targets, grant.agents)
            try:
                if not effective.targets:
                    raise ValueError("empty target grant")
                admitted_input = validate_typed(input, definition.input_type)
                # The built-in task contract has a target hint, never a permission grant.
                if (definition.input_type == "concorde-agent-task"
                        and admitted_input["data"]["target_id"] not in effective.targets):
                    raise ValueError("task target is outside the grant")
                if not self.runtime._spec_current(definition):
                    stop = stopped()
                    return finish(stop or "rejected", error=stop or "stale_definition")
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
                stop = stopped()
                return finish(stop or "rejected", error=stop or "admission_failed")
            stop = stopped()
            if stop:
                return finish(stop, error=stop)
            input_json, context_json = canonical(admitted_input), canonical(context)
            binding = {"agent_id": agent_id, "spec": self.runtime._specs[agent_id],
                "agent_definition": asdict(definition.agent),
                "decision_reference": definition.decision_reference,
                "native_binding": definition.binding.digest if definition.binding else None,
                "input_json": input_json, "context_json": context_json,
                "targets": sorted(effective.targets), "agents": sorted(effective.agents),
                "delegates": sorted(definition.delegates),
                "max_steps": definition.max_steps,
                "limits": asdict(limits),
                "input_type": definition.input_type, "result_type": definition.result_type}
            self.events.append({"event": "admit", "invocation_id": invocation_id,
                "parent_id": parent_id, "agent_id": agent_id, "depth": depth,
                "binding_digest": digest(binding), "context_id": snapshot["context_id"],
                "harness_id": definition.agent.harness.name,
                "harness_configuration_json": canonical(asdict(definition.agent.harness))})
            children = []
            for child_id in sorted(definition.delegates & effective.agents):
                child = self.runtime._definitions[child_id]
                if not child.targets & effective.targets:
                    continue
                children.append({"agent_id": child_id, "input_type": child.input_type,
                    "result_type": child.result_type,
                    "input_schema_json": canonical(json_schema(child.input_type)),
                    "result_schema_json": canonical(json_schema(child.result_type))})
            return {}

        def decide(state):
            nonlocal step, steps
            if steps >= definition.max_steps:
                return finish("limit_exhausted", error="step_limit")
            steps += 1
            stop = stopped()
            if stop or self.decisions >= limits.max_decisions:
                return finish(stop or "limit_exhausted", error=stop or "decision_limit")
            try:
                if not self.runtime._spec_current(definition):
                    stop = stopped()
                    return finish(stop or "rejected", error=stop or "stale_definition")
                current = validate_typed(self.runtime._resolve_context(definition,
                    decode(input_json), effective), "concorde-context-snapshot")
                stop = stopped()
                if stop:
                    return finish(stop, error=stop)
                if canonical(current) != context_json:
                    return finish("rejected", error="stale_context")
                if definition.binding is not None:
                    try:
                        current_binding = resolve_agent(definition.package_root, definition.agent.name)
                    except ValueError:
                        return finish("rejected", error="stale_definition")
                    if current_binding != definition.binding:
                        return finish("rejected", error="stale_definition")
                    instructions = (definition.package_root / definition.binding.instructions_path).read_text()
                    native_binding = binding_json(definition.binding)
                else:
                    instructions, native_binding = self.runtime._specs[agent_id], None
                frame = AgentFrame(invocation_id, parent_id, agent_id, input_json, context_json,
                    instructions, tuple(feedback), canonical(children),
                    canonical(json_schema(definition.result_type)), deadline - monotonic(), deadline, native_binding)
                self.decisions += 1
                try:
                    step = definition.decide(frame)
                except InvalidAgentStep:
                    stop = stopped()
                    return finish(stop or "rejected", error=stop or "invalid_step")
                except CapabilityExecutionError as error:
                    stop = stopped()
                    if stop:
                        return finish(stop, error=stop)
                    if error.outcome in {"cancelled", "limit_exhausted"}:
                        return finish(error.outcome, error=error.outcome)
                    return finish("failed", error="invalid_completion" if error.outcome == "invalid_completion"
                                  else "execution_failed")
                except KeyboardInterrupt:
                    return finish("cancelled", error="cancelled")
            except Exception:
                stop = stopped()
                return finish(stop or "failed", error=stop or "execution_failed")
            stop = stopped()
            if stop:
                return finish(stop, error=stop)
            return {}

        def validate_step(state):
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
            return {"action": step.action}

        def delegate(state):
            if step.agent_id not in definition.delegates or step.agent_id not in effective.agents:
                if self.calls >= limits.max_calls:
                    return finish("limit_exhausted", error="call_limit")
                self.calls += 1
                feedback.append(AgentResult(str(uuid4()), invocation_id, step.agent_id,
                                            "rejected", None, "delegation_denied"))
                self.events.append({"event": "return", **feedback[-1].wire()})
            else:
                feedback.append(self.call(step.agent_id, step.value, effective, invocation_id, depth + 1, deadline))
            if feedback[-1].outcome in {"cancelled", "limit_exhausted"}:
                return finish(feedback[-1].outcome, error=feedback[-1].error)
            return {}

        def complete(state):
            return finish(step.outcome, step.value, details=step.details)

        nodes = {"admit": admit, "decide": decide, "validate_step": validate_step,
                 "delegate": delegate, "complete": complete}
        # A scheduling bound leaves room for the host's typed step/decision-limit result.
        max_steps = max(item.max_steps for item in self.runtime._definitions.values())
        return build_agent_flow(nodes.__getitem__).invoke({},
            {"recursion_limit": 3 * max_steps + 4})["result"]

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
