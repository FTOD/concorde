---
id: feature.example.deliver
kind: feature
module: module.example
refines: []
scenarios:
  - scenario.example.deliver
contracts:
  provided:
    - contract.example.workflow
  required: []
diagrams:
  - source: specs/example/features/001-deliver/diagrams/delivery-sequence.json
    role: supplemental
    kind: sequence
    scenarios:
      - scenario.example.deliver
    output: generated/architecture/example-delivery-sequence.html
evidence_status: unknown
canonical_design: specs/example/features/001-deliver/design.md
---
# Deliver
## Outcome
Deliver a workflow.

## Terminology

No local terminology. This level uses inherited terminology unchanged.
