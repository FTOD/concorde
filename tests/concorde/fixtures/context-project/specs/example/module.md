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

Deliver workflows.

## Boundary

Own root orchestration.

## Structure

The level view is [architecture.json](architecture.json).

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
| `feature.example.deliver` | Deliver a workflow. | `features/001-deliver/design.md` |

## Contracts

| Contract ID | Role | Flow | Counterparty |
|---|---|---|---|
| `contract.example.workflow` | provided | bidirectional | external.maintainer |

## Submodules

| Module | Responsibility |
|---|---|
| `module.example.api` | Expose workflow APIs. |

## Representative Scenario

A maintainer delivers a workflow; the root invokes the API module through the workflow contract.

## Design Rationale

Fixture modules stay minimal so tests exercise Concorde behavior, not domain detail; implementation
notes live in the [design reference](design.md).
