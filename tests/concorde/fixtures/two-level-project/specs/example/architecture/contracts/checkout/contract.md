---
id: contract.example.checkout
kind: contract
module: module.example
role: provided
flow: bidirectional
counterparties:
  - external.shopper
representation:
  kind: standard
  format: Checkout Fixture
  version: "1"
  definition: https://example.invalid/checkout
features:
  - feature.example.checkout
  - feature.example.checkout.authorize
  - feature.example.checkout.confirm
  - feature.example.atomic
evidence_status: unknown
---
# Checkout Contract
## Purpose
Expose representative checkout outcomes.
## Information
Checkout requests and decisions.
## Obligations
Return one observable result.
## Failure Semantics
Failures are explicit.
## Compatibility
Version 1 remains stable.
## Evidence
Fixture evidence is unknown.
