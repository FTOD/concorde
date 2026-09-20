---
name: concorde-context-solve
description: "Operation: assess whether the selected Module Spec supports the task."
operation: context_solve
---

# concorde-context-solve

@prompts/workflow-host/invoke-operation-opener.md ACTION="assess whether the selected Module Spec supports the task"

@prompts/workflow-host/task-request-fields.md

Returns sufficiency or attributed gaps without authoring Specs, planning or implementation.

The calling agent chooses whether and when to invoke other Operations. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.
