---
name: concorde-configure
description: "Operation: apply the Pi worker model selection (model, thinking level, timeout and per-worker overrides); with accept_protocol, rebind the project to the installed Protocol copy."
operation: configure
---

# concorde-configure

@include prompts/workflow-host/invoke-operation-opener.md ACTION=configure
@include prompts/workflow-host/lifecycle-no-cognition.md

@include prompts/workflow-host/task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/target-identity-opener.md
@include prompts/workflow-host/candidate-worktree.md
