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
Deliver.
## Information
Workflow request and result.
## Obligations
Respond deterministically.
## Failure Semantics
Name failures.
## Compatibility
Versioned HTTP.
## Evidence
Unknown.
