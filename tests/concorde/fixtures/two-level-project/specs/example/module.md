---
id: module.example
kind: module
parent: null
view: specs/example/architecture.json
children: []
features:
  - feature.example.checkout
  - feature.example.atomic
contracts:
  provided:
    - contract.example.checkout
  required: []
---
# Example Commerce
## Responsibility
Provide checkout behavior.
## Boundary
Own checkout intent and externally observable decisions.
