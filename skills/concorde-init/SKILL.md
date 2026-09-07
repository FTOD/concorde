---
name: concorde-init
description: "Lifecycle: propose and apply explicit project initialization with a pinned Protocol and an honest registry stub."
capability: init
---

# concorde-init

@include prompts/workflow-host/invoke-operation-opener.md ACTION=init
@include prompts/workflow-host/lifecycle-no-cognition.md

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-init
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-init
@include prompts/workflow-host/task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/target-identity-opener.md
@include prompts/workflow-host/worktree-handoff.md
