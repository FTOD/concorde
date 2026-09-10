"""Codex/Claude Agent adapter: one fresh native decision, host-mediated child calls."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from time import monotonic
from uuid import uuid4

from .agent_executor import AgentProcessExecutor
from .agent_runtime import AgentFrame, AgentStep, InvalidAgentStep
from .agent_model import binding_from_json, external_agent_name
from .effects import EffectDeclaration
from .permissions import (CapabilityExecutionResult, PolicyBinding, build_launch_specification,
                          compile_policy, render_claude_configuration, render_codex_configuration)
from ..spec.typed_data import TypedDataError, canonical, decode, typed, validate_typed
from ..spec.repository import digest


@dataclass(frozen=True)
class NativeAgentAdapter:
    requires_binding = True
    integration: str = "codex"
    executor: object = None

    def __post_init__(self):
        if self.integration not in {"codex", "claude"}:
            raise ValueError("unsupported Agent integration")

    def __call__(self, frame: AgentFrame) -> AgentStep:
        if frame.agent_binding_json is None:
            raise ValueError("native decisions require the canonical Agent binding")
        binding = binding_from_json(frame.agent_binding_json)
        native_agent = external_agent_name(binding.agent)
        deadline = frame.deadline

        def remaining():
            seconds = deadline - monotonic()
            if seconds <= 0:
                raise TimeoutError("Agent deadline exhausted")
            return seconds

        runtime = typed("concorde-agent-loop-context", {
            "invocation_id": frame.invocation_id, "parent_id": frame.parent_id,
            "agent_id": frame.agent_id, "input_json": frame.input_json,
            "context_json": frame.context_json, "feedback": [item.wire() for item in frame.feedback],
            "children": decode(frame.children_json), "result_schema_json": frame.result_schema_json})
        context_digest = digest(runtime)
        decision_id = str(uuid4())

        def runner(argv, *, cwd, env, input_text, timeout=None):
            return subprocess.run(argv, cwd=cwd, env=dict(env), input=input_text, text=True,
                capture_output=True, check=False, timeout=min(remaining(), timeout) if timeout is not None else remaining())

        def probe(integration, executable):
            completed = subprocess.run((executable, "--version"), text=True, capture_output=True,
                check=False, timeout=remaining())
            return (completed.stdout or completed.stderr).strip() if completed.returncode == 0 else ""

        with tempfile.TemporaryDirectory(prefix="concorde-agent-decision-") as directory:
            root = Path(directory)
            serialized = canonical(runtime) + "\n"
            (root / "context.json").write_text(serialized, encoding="utf-8")
            policy = compile_policy(EffectDeclaration(("spec-context",), (), False, "none"),
                PolicyBinding("concorde-agent-loop", "ask", len(frame.feedback), native_agent, native_agent),
                {"spec-context": ("context.json",)})
            renderer = render_codex_configuration if self.integration == "codex" else render_claude_configuration
            native = renderer(policy, native_enforcement=True)
            launch = build_launch_specification(capability="concorde-agent-loop", stage="ask",
                occurrence=len(frame.feedback), role=native_agent, integration=self.integration,
                agent=native_agent, project_root=str(root), request="Choose one bounded Agent loop action.",
                prompt=frame.spec, prior_results=(), workspace_receipt_json=canonical({
                    "context_id": context_digest, "source_digest": context_digest, "role_paths": {"spec-context": ["context.json"]}}),
                workspace_digest=context_digest, policy=policy, native_configuration=native,
                runtime_input_json=canonical(runtime), invocation_id=decision_id,
                capability_configuration_json=canonical(typed("concorde-capability-configuration",
                    {"integration": self.integration, "enforcement": "native"})),
                agent_binding_json=frame.agent_binding_json)
            remaining()
            result = (AgentProcessExecutor(runner=runner, version_probe=probe)(launch)
                      if self.executor is None else self.executor(launch, deadline=deadline))
            if not isinstance(result, CapabilityExecutionResult):
                raise ValueError("Agent adapter requires native completion evidence")
            receipt, completion = result.receipt, result.completion
            if (receipt.requested_launch_digest != launch.digest or receipt.policy_digest != policy.digest
                    or receipt.status != "success" or completion.status != "success"
                    or completion.invocation_id != decision_id or completion.workspace_digest != context_digest
                    or receipt.launch_digest != completion.launch_digest
                    or receipt.runtime_bootstrap_digest != completion.runtime_bootstrap_digest
                    or receipt.integration != self.integration or receipt.exit_code != 0
                    or receipt.agent_binding_digest != binding.digest
                    or receipt.completion_status != "success" or completion.schema_version != 3
                    or completion.capability != launch.capability or completion.stage != launch.stage
                    or completion.occurrence != launch.occurrence or completion.role != launch.role
                    or receipt.enforcement != "native" or receipt.completion_schema_version != 3
                    or receipt.limitations != "none" or completion.limitations != "none"
                    or not completion.gates or any(gate.status != "passed" for gate in completion.gates)):
                raise ValueError("Agent decision evidence does not match its launch")
            if (root / "context.json").read_text(encoding="utf-8") != serialized:
                raise ValueError("Agent decision context changed")
            try:
                data = validate_typed(completion.domain_output, "concorde-agent-loop-step")["data"]
                value = decode(data["value_json"]) if data["value_json"] is not None else None
            except TypedDataError as error:
                raise InvalidAgentStep("invalid native Agent decision") from error
            if data["source"] != "model-driven":
                raise InvalidAgentStep("native decisions must identify model-driven dispatch")
            return AgentStep(data["source"], data["action"], data["agent_id"],
                value,
                data["outcome"], data["details"])
