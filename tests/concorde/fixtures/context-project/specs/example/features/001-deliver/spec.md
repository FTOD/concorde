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
canonical_spec: specs/example/features/001-deliver/spec.md
---
# Deliver
## Outcome
Deliver a workflow.
