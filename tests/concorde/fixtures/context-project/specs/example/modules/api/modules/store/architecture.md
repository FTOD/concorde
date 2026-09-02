---
id: module.example.api.store
kind: module
parent: module.example.api
modules: []
features: []
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/example-store.html
---

# Architecture: Example Store

## Responsibility

Store workflow records.

## Boundary

Own persistence details and exclude API transport behavior.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.store.records` | data-store | The conceptual workflow record store. | `concept:example.store.records` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `module.example.api.store` | owns_entity | `entity.example.store.records` | The store module owns persisted records. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.store.persist` | The API requests persistence. | `module.example.api.store` writes_to `entity.example.store.records`. | One record is persisted. | None |

## Modules

None.

## Features

None.

## Decisions

- [System overview](diagrams/system-overview.json) projects the store entities and relationships.
- Persistence stays behind the child-module boundary.
