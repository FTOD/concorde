---
name: concorde-fast-loop
description: "Global development loop without Spec authoring: route one change, then plan, task, implement and validate to a ready candidate; reviews are optional and every skip is recorded."
capability: fast_loop
---

# concorde-fast-loop

@include prompts/workflow-host/invoke-operation-opener.md ACTION="fast loop"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-fast-loop
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-fast-loop
@include prompts/workflow-host/loop-task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/main-may-inspect.md WORKERS="a different target worker"
@include prompts/workflow-host/worktree-handoff.md


@include prompts/workflow-host/loop-completion-and-reviews.md
