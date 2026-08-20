---
id: module.example.api
kind: module
parent: module.example
view: specs/example/modules/api/architecture.json
children:
  - module.example.api.store
features:
  - feature.example.api.invoke
contracts:
  provided:
    - contract.example.api
  required: []
---
# API
## Responsibility
Expose workflow APIs.
## Boundary
Own API behavior.
