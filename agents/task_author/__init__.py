"""Turn an accepted plan into implementation acceptance tasks."""
from concorde.harness.agent_model import Agent, Contract
from concorde.harness.effects import EffectDeclaration

AGENT = Agent(
    name="task_author", spec="agents/task_author/spec.md", workspace="capsule",
    contract=Contract(
        phase="tasks",
        context="concorde-agent-stage-context", result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context", "references"), (), False, "none"),
        stage_inputs=("concorde-plan-artifact", "concorde-task-identity-constraints",
                      "concorde-implementation-task", "concorde-review-result", "concorde-task-scope-feedback"),
        required_inputs=("concorde-plan-artifact", "concorde-task-identity-constraints"),
        output_fields=("tasks",)),
    tools=("read", "grep", "find", "ls"),
    timeout_seconds=1800,
)
