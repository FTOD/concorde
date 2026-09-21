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

## Native invocation

Run prepares an invocation-bound named native workflow. Invoke its exact returned `call` through
native `subagent` (async), then poll `concorde` with `operation: concorde-plan, action: result`.
The workflow runs a fresh assessor, independently accepts sufficiency, then prepares a fresh planner
and independently accepts its nonempty plan. A passing gate or async launch receipt is not success.
Read both native execution state and Host accepted/typed result; accepted blockers do not mean a plan
was persisted. No Python model scheduler or legacy worker fallback is used.

File scope is prompt-level policy. Only complete Specs and admitted references are supplied; no project
implementation contents, delegation, write or shell grants are added. Native runtime selection uses
`CONCORDE_NATIVE_SUBAGENTS_ROOT`. The assigned candidate is reused; primary requests bind a managed
candidate while status and durable evidence remain primary-owned.
