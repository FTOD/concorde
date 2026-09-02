---
id: module.example
kind: module
parent: null
modules:
  - module.example.consumer
  - module.example.provider
features: []
diagrams: []
---

# Architecture: Permission Planning Fixture

## Responsibility

Provide two isolated fixture modules for permission-boundary tests.

## Boundary

Own only the child-module boundaries and no child implementation details.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `module.example.consumer` | module | Consumer boundary. | `specs/example/modules/consumer/architecture.md` |
| `module.example.provider` | module | Provider boundary. | `specs/example/modules/provider/architecture.md` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `module.example.consumer` | `requires` | `module.example.provider` | The consumer uses one published provider feature contract. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.consume` | Consumer request. | Consumer invokes the provider contract. | Published behavior only. | `contract.provider.api` |

## Modules

| Module | Responsibility | Boundary interaction |
|---|---|---|
| `module.example.consumer` | Consume a published provider API. | Requires `contract.provider.api`. |
| `module.example.provider` | Publish an API while hiding internals. | Provides `contract.provider.api`. |

## Features

None.

## Decisions

- Child implementations stay owned by their child architecture.
