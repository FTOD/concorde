"""One target-bound reader Agent, with optional recursive decomposition."""
from pathlib import Path

from ..host.agent_runtime import AgentConstraints, AgentDefinition, Harness
from ..host.build import verify_fresh
from ..host.native_agent import NativeAgentAdapter
from ..host.typed_data import canonical
from ..specification.repository import digest


def definition(package_root, target_id, integration="codex", executor=None, *, executor_reference=None):
    verify_fresh(package_root)
    if not isinstance(target_id, str) or not target_id.strip():
        raise ValueError("reader requires one target")
    agent_id = "concorde-recursive-reader"
    if executor is not None:
        if not isinstance(executor_reference, str) or not executor_reference.strip():
            raise ValueError("an injected executor requires a versioned executor_reference")
    else:
        executor_reference = "AgentProcessExecutor/native-enforcement/v1"
    implementation = digest({relative: digest((Path(package_root) / relative).read_bytes())
        for relative in ("src/concorde/agents/reader.py", "src/concorde/host/native_agent.py",
                         "src/concorde/host/agent_runtime.py", "src/concorde/host/agent_executor.py",
                         "src/concorde/host/permissions.py")})
    configuration = canonical({"model_integration": integration,
        "capabilities": ["api.execution.execute"], "tools": [], "skills": [],
        "context_assembly": "service.spec-context/ask/profile-8",
        "control_loop": "AgentRuntime/recursive-read-only/v1",
        "state_handling": "invocation-local-ordered-feedback/no-resume/v1",
        "system_environment": executor_reference, "implementation": implementation})
    return AgentDefinition(agent_id, Path(package_root) / "prompts/agents/reader/spec.md",
        Harness(f"native-reader-{integration}-v1", NativeAgentAdapter(integration, executor), configuration),
        AgentConstraints(frozenset({target_id}), frozenset({agent_id})),
        "concorde-agent-task", "concorde-agent-answer")


def runtime(project_root, package_root, target_id, *, integration="codex", executor=None,
            executor_reference=None, limits=None, cancelled=lambda: False):
    """Install the reader with the existing complete-context service, without granting invocation."""
    from ..host.agent_runtime import AgentLimits, AgentRuntime
    from ..host.typed_data import typed
    from ..specification.context import resolve_context
    from ..specification.repository import SpecRepository

    agent = definition(package_root, target_id, integration, executor,
                       executor_reference=executor_reference)

    def resolve(definition, input, grant):
        verify_fresh(package_root)
        if input['data']['target_id'] != target_id or target_id not in grant.targets:
            raise ValueError("reader target is not admitted")
        snapshot = resolve_context(SpecRepository(Path(project_root), Path(package_root)), target_id,
            phase="ask", task=input['data']['task'], instructions=definition.spec_path.read_text())
        return typed("concorde-context-snapshot", snapshot.value)

    return AgentRuntime([agent], resolve, limits=limits if limits is not None else AgentLimits(),
                        cancelled=cancelled)
