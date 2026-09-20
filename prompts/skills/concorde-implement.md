---
name: concorde-implement
description: "Operation: implement current accepted tasks inside the selected Module grant."
operation: implement
---

# concorde-implement

@include prompts/workflow-host/invoke-operation-opener.md ACTION="implement current accepted tasks inside the selected Module grant"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-implement
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-implement

@include prompts/workflow-host/task-request-fields.md

Requires a current accepted plan and tasks. The programmer may change only registered implementation files, never Specs, metadata or registry. Component work and necessary contract changes return to the calling agent for separate selection; no child workflow or Spec authoring runs automatically. Completion is not review, validation, readiness or delivery.

The calling agent chooses whether and when to invoke other Operations. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.
