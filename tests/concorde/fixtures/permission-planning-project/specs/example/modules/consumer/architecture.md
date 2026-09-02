---
id: module.example.consumer
kind: module
parent: module.example
modules: []
features:
  - feature.example.consumer.change
diagrams: []
---

# Architecture: Consumer

## Responsibility

Consume the provider's published API.

## Boundary

Own consumer source and tests, not provider internals.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.consumer-service` | program | Consumer behavior. | `src/consumer/service.py` |
| `entity.example.consumer-test` | test | Consumer executable evidence. | `tests/consumer/test_service.py` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.example.consumer-test` | `tested_by` | `entity.example.consumer-service` | Fixture evidence covers the consumer. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.consumer-change` | Change request. | Consumer reads the published API. | Consumer changes safely. | `contract.example.consumer.change`, `contract.provider.api` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.example.consumer.change` | Change the consumer through a provider contract. |

## Decisions

- Owned source/test locators are the consumer's executable planning context.
