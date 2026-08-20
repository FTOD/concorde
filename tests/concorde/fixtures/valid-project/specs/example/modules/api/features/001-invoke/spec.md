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
canonical_spec: specs/example/modules/api/features/001-invoke/spec.md
---
# Invoke API
## Outcome
The API accepts a workflow invocation.
