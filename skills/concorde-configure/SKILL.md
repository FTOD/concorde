---
name: concorde-configure
description: "Lifecycle: apply the initialized integration and enforcement configuration."
capability: configure
---

# concorde-configure

@include prompts/workflow-host/invoke-capability-opener.md ACTION=configure
@include prompts/workflow-host/lifecycle-no-cognition.md

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-configure
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-configure
@include prompts/workflow-host/task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/target-identity-opener.md
@include prompts/workflow-host/worktree-handoff.md
