"""Reader Agent: explains one selected target from its resolved Spec context (A1)."""

from __future__ import annotations

from concorde.host.agent_model import Agent, Constraints
from concorde.host.effects import EffectDeclaration
from concorde.host.harness import SPEC_CAPSULE

AGENT = Agent(
    name="reader",
    spec="agents/reader/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        contexts=("concorde-agent-stage-context", "concorde-agent-task", "concorde-agent-loop-context"),
        results=("concorde-agent-stage-result", "concorde-agent-answer", "concorde-agent-loop-step"),
        allow_delegation=True,
    ),
)


def runtime(project_root, package_root, target_id, *, integration="codex", executor=None,
            executor_reference=None, limits=None, cancelled=lambda: False):
    """Bind this same reader Agent to a recursive, target-scoped host graph."""
    from pathlib import Path
    from concorde.host.agent_runtime import AgentRuntime, AgentLimits, RuntimeAgent
    from concorde.host.build import load_agent, verify_fresh
    from concorde.host.native_agent import NativeAgentAdapter
    from concorde.host.typed_data import canonical, typed
    from concorde.specification.context import resolve_context
    from concorde.specification.repository import SpecRepository

    if not isinstance(target_id, str) or not target_id.strip():
        raise ValueError("reader requires one target")
    if executor is not None and (not isinstance(executor_reference, str) or not executor_reference.strip()):
        raise ValueError("an injected executor requires a versioned executor_reference")
    package_root = Path(package_root)
    prompt = load_agent(package_root, AGENT.name)
    node = RuntimeAgent(AGENT, NativeAgentAdapter(integration, executor), package_root,
        frozenset({target_id}), frozenset({AGENT.name}),
        canonical({"adapter": "native-agent/v1", "integration": integration,
                   "executor": executor_reference if executor is not None else "AgentProcessExecutor/deadline/v1"}),
        binding=prompt.binding)

    def resolve(node, input, grant):
        verify_fresh(package_root)
        if input['data']['target_id'] != target_id or target_id not in grant.targets:
            raise ValueError("reader target is not admitted")
        snapshot = resolve_context(SpecRepository(Path(project_root), package_root), target_id,
            phase="ask", task=input['data']['task'], instructions=prompt.body)
        return typed("concorde-context-snapshot", snapshot.value)

    return AgentRuntime([node], resolve, limits=limits if limits is not None else AgentLimits(),
                        cancelled=cancelled)
