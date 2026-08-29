---
id: module.example
kind: module
parent: null
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

## Structure

The level view is [level-view.json](architecture/diagrams/level-view.json).

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
| `feature.example.deliver` | Deliver the example workflow. | `features/001-deliver/design.md` |

## Contracts

| Contract ID | Role | Flow | Counterparty |
|---|---|---|---|
| `contract.example.workflow` | provided | bidirectional | external.maintainer |

## Submodules

| Module | Responsibility |
|---|---|
| `module.example.api` | Expose API operations. |

## Representative Scenario

A maintainer delivers the example workflow; the root delegates the invocation to the API module through the workflow contract.

## Design Rationale

Fixture modules stay minimal so tests exercise Concorde behavior, not domain detail; implementation
notes live in the [design reference](design.md).
