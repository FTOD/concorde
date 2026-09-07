---
name: concorde-standard-dev-loop
description: "Global development loop: route one change, then specify, review the Spec, plan, task, implement, validate and review code to a ready candidate."
capability: standard_dev_loop
---

# concorde-standard-dev-loop

@include prompts/workflow-host/invoke-operation-opener.md ACTION="standard dev loop"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-standard-dev-loop
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-standard-dev-loop
@include prompts/workflow-host/loop-task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/main-may-inspect.md WORKERS="different target workers"
@include prompts/workflow-host/worktree-handoff.md


@include prompts/workflow-host/loop-completion-and-reviews.md
