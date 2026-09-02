---
id: module.example.api
kind: module
parent: module.example
modules: []
features:
  - feature.example.api.invoke
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/example-api.html
---

# Architecture: Example API

## Responsibility

Expose API operations.

## Boundary

Own transport validation and exclude root orchestration.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.api.handler` | function | The API request entry point. | `specs/example/modules/api/architecture.md#handler` |

## Relationships

| Source | Predicate | Target | Description | Interface |
|---|---|---|---|---|
| `module.example.api` | owns_entity | `entity.example.api.handler` | The API module owns its transport entry point. | `contract.example.api` |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.api.invoke` | The root invokes the API. | `module.example.api` calls `entity.example.api.handler`. | The handler returns a validated result. | `contract.example.api` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.example.api.invoke` | Invoke one API operation. |

## Decisions

- [System overview](diagrams/system-overview.json) projects the API entities and relationships.
- The API handler is architecture-significant; private helpers are intentionally omitted.
