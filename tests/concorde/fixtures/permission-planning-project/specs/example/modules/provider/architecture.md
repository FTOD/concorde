---
id: module.example.provider
kind: module
parent: module.example
modules: []
features:
  - feature.example.provider.api
  - feature.example.provider.unrelated
diagrams: []
---

# Architecture: Provider

## Responsibility

Provide a published API backed by private implementation.

## Boundary

Keep provider source, tests, and architecture private from the consumer planner.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.provider-service` | program | Private provider implementation. | `src/provider/private.py` |
| `entity.example.provider-test` | test | Private provider evidence. | `tests/provider/test_private.py` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.example.provider-test` | `tested_by` | `entity.example.provider-service` | Provider evidence remains private. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.provider-api` | API request. | Provider handles request. | Published result. | `contract.provider.api` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.example.provider.api` | Publish provider behavior. |
| `feature.example.provider.unrelated` | Publish unrelated behavior. |

## Decisions

- The feature body is the dependency boundary; this architecture stays private.
