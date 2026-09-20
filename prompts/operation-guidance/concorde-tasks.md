---
name: concorde-tasks
description: "Operation: derive implementation acceptance tasks from the current accepted plan."
operation: tasks
---

# concorde-tasks

@prompts/workflow-host/invoke-operation-opener.md ACTION="derive implementation acceptance tasks from the current accepted plan"

@prompts/workflow-host/task-request-fields.md

Requires the managed change and current accepted plan for the same intent. Returns new incomplete tasks, preserving prior task identities in history. Optional repair_task_scope binds the exact incomplete task-list digest; optional repair_review names a current blocking code-review ArtifactRef for this same intent. Neither field bypasses currentness or review gates.

The calling agent chooses whether and when to invoke other Operations. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.
