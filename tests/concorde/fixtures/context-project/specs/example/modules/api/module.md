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

## Structure

The level view is [architecture.json](architecture.json).

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
| `feature.example.api.invoke` | Invoke a workflow API. | `features/001-invoke/design.md` |

## Contracts

| Contract ID | Role | Flow | Counterparty |
|---|---|---|---|
| `contract.example.api` | provided | input | module.example |

## Submodules

| Module | Responsibility |
|---|---|
| `module.example.api.store` | Store records. |

## Representative Scenario

The root module invokes a workflow API; the API module persists through the store module.

## Design Rationale

Fixture modules stay minimal so tests exercise Concorde behavior, not domain detail; implementation
notes live in the [design reference](design.md).
