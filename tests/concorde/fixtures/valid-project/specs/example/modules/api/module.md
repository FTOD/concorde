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

## Structure

This leaf module has no submodules, so no separate level view is maintained; its features and contracts above are the whole structure.

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
| `feature.example.api.invoke` | Invoke one API operation. | `features/001-invoke/design.md` |

## Contracts

| Contract ID | Role | Flow | Counterparty |
|---|---|---|---|
| `contract.example.api` | provided | input | module.example |

## Submodules

None.

## Representative Scenario

The root module invokes one API operation through the API contract and receives its result.

## Design Rationale

Fixture modules stay minimal so tests exercise Concorde behavior, not domain detail; implementation
notes live in the [design reference](design.md).
