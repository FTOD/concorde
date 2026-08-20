---
id: contract.example.api
kind: contract
module: module.example.api
role: provided
flow: input
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
Accept an invocation.
## Information
HTTP request fields.
## Obligations
Validate input.
## Failure Semantics
Return an HTTP error.
## Compatibility
HTTP semantics remain compatible.
## Evidence
Unknown.
