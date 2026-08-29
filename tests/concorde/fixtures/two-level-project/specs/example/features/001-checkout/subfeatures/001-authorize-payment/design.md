---
id: feature.example.checkout.authorize
kind: feature
module: module.example
parent_feature: feature.example.checkout
refines: []
subfeatures: []
scenarios:
  - scenario.example.checkout.authorize
contracts:
  provided:
    - contract.example.checkout
  required: []
architecture_view: specs/example/architecture.json
evidence_status: verified
canonical_design: specs/example/features/001-checkout/subfeatures/001-authorize-payment/design.md
---
# Feature Design: Authorize Payment
**Status**: Verified fixture
## Outcome
A valid checkout receives an authorization decision.
## Requirements
The decision is explicit and traceable to the parent checkout.
