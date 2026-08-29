---
id: module.example
kind: module
parent: null
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

## Structure

The level view is [level-view.json](architecture/diagrams/level-view.json).

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
| `feature.example.checkout` | Complete a checkout. | `features/001-checkout/design.md` |
| `feature.example.atomic` | Commit atomically. | `features/002-atomic/design.md` |

## Contracts

| Contract ID | Role | Flow | Counterparty |
|---|---|---|---|
| `contract.example.checkout` | provided | bidirectional | external.customer |

## Submodules

None.

## Representative Scenario

A customer completes a checkout: payment is authorized and the order is confirmed through the checkout contract.

## Design Rationale

Fixture modules stay minimal so tests exercise Concorde behavior, not domain detail; implementation
notes live in the [design reference](design.md).
