---
id: module.example.api
kind: module
parent: module.example
modules:
  - module.example.api.store
features:
  - feature.example.api.invoke
diagrams:
  - source: diagrams/level-view.json
    kind: architecture
    output: generated/architecture/api.html
---

# Architecture: Example API

## Responsibility

Expose workflow APIs backed by the store child module.

## Boundary

Own transport and validation while delegating persistence.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.api.handler` | function | The API request entry point. | `specs/example/modules/api/architecture.md#handler` |
| `module.example.api.store` | module | The bounded persistence child. | `specs/example/modules/api/modules/store/architecture.md` |

## Relationships

| Source | Predicate | Target | Description | Interface |
|---|---|---|---|---|
| `module.example.api` | owns_entity | `entity.example.api.handler` | The module owns its request handler. | `contract.example.api` |
| `entity.example.api.handler` | calls | `module.example.api.store` | Valid requests are persisted by the immediate child. | `contract.example.api` |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.api.invoke` | The root invokes the API. | `module.example.api` calls `entity.example.api.handler`.<br>`entity.example.api.handler` calls `module.example.api.store`. | The API returns a persisted result. | `contract.example.api` |

## Modules

| Module | Responsibility |
|---|---|
| `module.example.api.store` | Store workflow records. |

## Features

| Feature | Outcome |
|---|---|
| `feature.example.api.invoke` | Invoke a workflow API. |

## Decisions

- [level-view.json](diagrams/level-view.json) projects the API boundary.
