---
id: module.example.api
kind: module
parent: module.example
children: []
features:
  - feature.example.api.invoke
contracts:
  provided:
    - contract.example.api
  required: []
---
# API
## Responsibility
Expose API operations.
## Boundary
Own transport, not orchestration.
