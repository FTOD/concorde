---
id: contract.example.api
kind: contract
module: module.example.api
role: provided
flow: bidirectional
counterparties:
  - module.example
representation:
  kind: standard
  format: HTTP
  version: "1.1"
  definition: https://www.rfc-editor.org/rfc/rfc9110
features:
  - feature.example.api.invoke
evidence_status: unknown
---
# API
## Purpose
Invoke.
## Information
API input and output.
## Obligations
Respond.
## Failure Semantics
Name failures.
## Compatibility
Versioned HTTP.
## Evidence
Unknown.
