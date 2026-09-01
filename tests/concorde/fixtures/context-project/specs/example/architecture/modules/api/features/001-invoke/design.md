---
id: feature.example.api.invoke
kind: feature
module: module.example.api
refines:
  - feature.example.deliver
scenarios:
  - scenario.example.api.invoke
contracts:
  provided:
    - contract.example.api
  required: []
evidence_status: unknown
canonical_design: specs/example/architecture/modules/api/features/001-invoke/design.md
---
# Invoke
## Outcome
Invoke the API.

## Terminology

No local terminology. This level uses inherited terminology unchanged.
