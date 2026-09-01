---
id: module.example
kind: module
parent: null
modules: []
features:
  - feature.example.checkout
  - feature.example.atomic
  - feature.example.checkout.authorize
  - feature.example.checkout.confirm
---

# Architecture: Checkout Example

## Responsibility

Coordinate checkout, authorization, confirmation, and atomic fixture behavior.

## Boundary

Own checkout capability composition without creating a feature hierarchy.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.example.shopper` | external-system | The checkout consumer. | `external:fixture-shopper` |
| `entity.example.checkout` | program | The checkout coordinator. | `concept:example.checkout` |
| `entity.example.authorizer` | service | The authorization decision provider. | `concept:example.authorizer` |
| `entity.example.confirmer` | service | The order confirmation provider. | `concept:example.confirmer` |

## Relationships

| Source | Predicate | Target | Description | Interface |
|---|---|---|---|---|
| `entity.example.shopper` | calls | `entity.example.checkout` | The shopper begins checkout. | `contract.example.checkout` |
| `entity.example.checkout` | calls | `entity.example.authorizer` | Checkout requests authorization. | `contract.example.authorization` |
| `entity.example.checkout` | calls | `entity.example.confirmer` | Authorized checkout requests confirmation. | `contract.example.confirmation` |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.example.checkout` | `entity.example.shopper` requests checkout. | `entity.example.shopper` calls `entity.example.checkout`.<br>`entity.example.checkout` calls `entity.example.authorizer`.<br>`entity.example.checkout` calls `entity.example.confirmer`. | One correlated checkout result is returned. | `contract.example.checkout`, `contract.example.authorization`, `contract.example.confirmation` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.example.checkout` | Complete checkout. |
| `feature.example.atomic` | Perform one atomic behavior. |
| `feature.example.checkout.authorize` | Authorize payment. |
| `feature.example.checkout.confirm` | Confirm an order. |

## Decisions

- Former subfeatures are flat related features with preserved stable IDs.
