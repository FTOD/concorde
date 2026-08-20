---
id: contract.example.workflow
kind: contract
module: module.example
role: provided
flow: bidirectional
counterparties:
  - external.maintainer
representation:
  kind: standard
  format: HTTP
  version: "1.1"
  definition: https://www.rfc-editor.org/rfc/rfc9110
features:
  - feature.example.deliver
evidence_status: unknown
---
# Workflow
## Purpose
Invoke the workflow.
## Information
Request and response metadata.
## Obligations
Return a clear outcome.
## Failure Semantics
Return a named failure.
## Compatibility
HTTP semantics remain compatible.
## Evidence
Unknown.
