---
name: concorde-implement
description: "Agent entry: call the programmer to implement current accepted tasks inside the selected Module grant."
---

# concorde-implement

@prompts/workflow-host/invoke-operation-opener.md ACTION="implement current accepted tasks inside the selected Module grant"

@prompts/workflow-host/task-request-fields.md

Requires a current accepted plan and tasks. The programmer may change only files the Module's realization entries bind, never Spec documents, their metadata or the registry. Component work (tasks for another Module of the change scope, such as a contract participant) and necessary contract changes return to the calling agent for separate selection, each as that Module's own implementation in the same candidate; no child workflow or Spec change runs automatically. Completion is not review, validation, readiness or delivery.

The calling agent chooses whether and when to invoke other capabilities. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.

## Native execution

Run prepares an exact direct native programmer call. Invoke returned `call` unchanged and inspect
`details.concorde_native.accepted` plus the typed result. Its capsule index names the actual assigned
candidate and absolute intended implementation paths; write/edit those real paths, not copies.
Broad file/shell and network/credential abstention are prompt-level policy, not OS confinement.
Use the fixed Host run_checks service for genuinely recorded configured check outcomes.
No public Graph/Pi-RPC fallback or automatic downstream readiness/integration occurs.
