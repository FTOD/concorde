---
id: module.example
kind: module
parent: null
view: specs/example/architecture.json
children:
  - module.example.api
features:
  - feature.example.deliver
contracts:
  provided:
    - contract.example.workflow
  required: []
---
# Example
## Responsibility
Deliver the example workflow.
## Boundary
Own orchestration, not API internals.
