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
---

# Architecture: Example

## Responsibility

Deliver the example workflow.

## Boundary

Own orchestration while delegating transport behavior to the API child module.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.maintainer` | external-system | The human consumer of the example workflow. | `external:example-maintainer` |
| `entity.example.runtime` | program | The workflow orchestrator at the root boundary. | `concept:example.runtime` |
| `module.example.api` | module | The bounded API transport child module. | `specs/example/modules/api/architecture.md` |

## Relationships

| Source | Predicate | Target | Description | Interface |
|---|---|---|---|---|
| `entity.example.maintainer` | calls | `entity.example.runtime` | The maintainer starts delivery. | `contract.example.workflow` |
| `entity.example.runtime` | calls | `module.example.api` | Orchestration delegates transport to the immediate child. | `contract.example.workflow` |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.deliver` | `entity.example.maintainer` requests delivery. | `entity.example.maintainer` calls `entity.example.runtime`.<br>`entity.example.runtime` calls `module.example.api`. | The maintainer receives the workflow result. | `contract.example.workflow` |

## Modules

| Module | Responsibility |
|---|---|
| `module.example.api` | Expose API operations. |

## Features

| Feature | Outcome |
|---|---|
| `feature.example.deliver` | Deliver the example workflow. |

## Decisions

- [level-view.json](diagrams/level-view.json) is an optional projection of the typed entity graph above.
