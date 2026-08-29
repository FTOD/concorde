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
canonical_design: specs/example/modules/api/features/001-invoke/design.md
---
# Invoke API
## Outcome
The API accepts a workflow invocation.
