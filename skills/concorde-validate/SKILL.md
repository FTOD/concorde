---
name: concorde-validate
description: "Lifecycle: run deterministic Spec and configured code checks and record readiness for the current candidate."
capability: validate
---

# concorde-validate

@include prompts/workflow-host/invoke-capability-opener.md ACTION=validate
@include prompts/workflow-host/lifecycle-no-cognition.md

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-validate
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-validate
@include prompts/workflow-host/task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/target-identity-opener.md
@include prompts/workflow-host/worktree-handoff.md
