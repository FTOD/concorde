---
id: module.example
kind: module
parent: null
modules:
  - module.example.api
features:
  - feature.example.deliver
diagrams:
  - source: diagrams/level-view.json
    kind: architecture
    output: generated/architecture/example.html
  - source: diagrams/delivery-sequence.json
    kind: sequence
    output: generated/architecture/example-delivery.html
---

# Architecture: Example

## Responsibility

Deliver workflows through a bounded API child.

## Boundary

Own workflow orchestration and exclude API persistence internals.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.maintainer` | external-system | The workflow consumer. | `external:example-maintainer` |
| `entity.example.runtime` | program | The root workflow orchestrator. | `concept:example.runtime` |
| `module.example.api` | module | The bounded API child module. | `specs/example/modules/api/architecture.md` |

## Relationships

| Source | Predicate | Target | Description | Interface |
|---|---|---|---|---|
| `entity.example.maintainer` | calls | `entity.example.runtime` | The maintainer starts delivery. | `contract.example.workflow` |
| `entity.example.runtime` | calls | `module.example.api` | The root delegates the request to the API. | `contract.example.workflow` |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.deliver` | `entity.example.maintainer` requests delivery. | `entity.example.maintainer` calls `entity.example.runtime`.<br>`entity.example.runtime` calls `module.example.api`. | A named workflow result is returned. | `contract.example.workflow` |

## Modules

| Module | Responsibility |
|---|---|
| `module.example.api` | Expose workflow APIs. |

## Features

| Feature | Outcome |
|---|---|
| `feature.example.deliver` | Deliver a workflow. |

## Decisions

- [level-view.json](diagrams/level-view.json) and [delivery-sequence.json](diagrams/delivery-sequence.json) project this architecture.
