---
name: concorde-dev-loop
description: "Global development loop: route one change, then specify, review the Spec, plan, task, implement, validate and review code to a ready candidate; specify=false skips authoring and run_reviews=false records explicit review skips."
capability: dev_loop
---

# concorde-dev-loop

@include prompts/workflow-host/invoke-operation-opener.md ACTION="run the development loop"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-dev-loop
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-dev-loop
@include prompts/workflow-host/loop-task-request-fields.md
@include prompts/workflow-host/dev-loop-flags.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/main-may-inspect.md WORKERS="a different target worker"
@include prompts/workflow-host/worktree-handoff.md

@include prompts/workflow-host/loop-completion-and-reviews.md
