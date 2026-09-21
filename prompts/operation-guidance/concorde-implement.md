---
name: concorde-implement
description: "Operation: implement current accepted tasks inside the selected Module grant."
operation: implement
---

# concorde-implement

@prompts/workflow-host/invoke-operation-opener.md ACTION="implement current accepted tasks inside the selected Module grant"

@prompts/workflow-host/task-request-fields.md

Requires a current accepted plan and tasks. The programmer may change only registered implementation files, never Specs, metadata or registry. Component work and necessary contract changes return to the calling agent for separate selection; no child workflow or Spec authoring runs automatically. Completion is not review, validation, readiness or delivery.

The calling agent chooses whether and when to invoke other Operations. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.

## Native execution

Run prepares an exact direct native programmer call. Invoke returned `call` unchanged and inspect
`details.concorde_native.accepted` plus the typed result. Its capsule index names the actual assigned
candidate and absolute intended implementation paths; write/edit those real paths, not copies.
Broad file/shell and network/credential abstention are prompt-level policy, not OS confinement.
Use the fixed Host run_checks service for genuinely recorded configured check outcomes.
No public Graph/Pi-RPC fallback or automatic downstream readiness/integration occurs.
