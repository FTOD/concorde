---
id: module.fixture.nested
kind: module
parent: module.fixture
modules: []
features:
  - feature.fixture.beta
---

# Nested Fixture Architecture

## Responsibility

Own Beta as a bounded child module capability.

## Boundary

The module has no children.

## Entities

No additional architecture-significant entities.

## Relationships

The module registers `feature.fixture.beta`.

## Interactions

A reader opens Beta and follows its relation to Alpha.
