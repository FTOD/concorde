---
name: concorde-specify-loop
description: "Spec loop: route one change, author or revise its Spec, then independently review it; stop before planning and implementation."
capability: specify_loop
---

# concorde-specify-loop

@include prompts/workflow-host/invoke-capability-opener.md ACTION="run the Spec loop"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-specify-loop
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-specify-loop
@include prompts/workflow-host/loop-task-request-fields.md
@include prompts/workflow-host/specify-loop-flags.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/main-may-inspect.md WORKERS="a different target worker"
@include prompts/workflow-host/worktree-handoff.md

@include prompts/workflow-host/specify-loop-completion.md
