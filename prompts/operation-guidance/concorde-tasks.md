---
name: concorde-tasks
description: "Agent entry: call the task-author to derive implementation acceptance tasks from the current accepted plan."
operation: tasks
---

# concorde-tasks

@prompts/workflow-host/invoke-operation-opener.md ACTION="derive implementation acceptance tasks from the current accepted plan"

@prompts/workflow-host/task-request-fields.md

Requires the managed change and current accepted plan for the same intent. Returns new incomplete tasks, preserving prior task identities in history. Optional repair_task_scope binds the exact incomplete task-list digest; optional repair_review names a current blocking code-review ArtifactRef for this same intent. Neither field bypasses currentness or review gates.

The calling agent chooses whether and when to invoke other capabilities. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.

## Native invocation

Run prepares a direct native task-author call from the exact current accepted plan. Invoke the
returned native `subagent` call unchanged. Inspect `details.concorde_native.accepted` and its typed
result, not native structured output or gate success alone. Reserved IDs and explicit scope/review
repair feedback remain Host-checked; failed/stale/empty/colliding results preserve prior tasks.

File scope is prompt-level policy. Only complete Specs and admitted references are supplied; no project
implementation contents, delegation, write or shell grants are added. Native runtime selection uses
`CONCORDE_NATIVE_SUBAGENTS_ROOT`. The assigned candidate is reused; primary requests bind a managed
candidate while status and durable evidence remain primary-owned.
