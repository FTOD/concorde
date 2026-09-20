---
name: concorde-plan
description: "Operation: plan work for the explicitly selected Module."
operation: plan
---

# concorde-plan

@prompts/workflow-host/invoke-operation-opener.md ACTION="plan work for the explicitly selected Module"

@prompts/workflow-host/task-request-fields.md

Assesses the complete Spec before accepting a nonempty revision-bound plan. Does not read implementation contents. Missing contracts return to the calling agent for direct Spec and paired metadata edits.

The calling agent chooses whether and when to invoke other Operations. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.
