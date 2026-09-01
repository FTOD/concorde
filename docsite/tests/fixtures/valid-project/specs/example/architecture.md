---
id: module.fixture
kind: module
parent: null
modules:
  - module.fixture.nested
features:
  - feature.fixture.alpha
---

# Fixture Architecture

## Responsibility

Provide a root architecture source for content-registry tests.

## Boundary

The fixture owns Alpha and one nested module.

## Entities

| ID | Type | Definition | Locator |
|---|---|---|---|
| `module.fixture.nested` | module | A bounded nested fixture module. | `specs/example/modules/nested/architecture.md` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `module.fixture` | `contains_module` | `module.fixture.nested` | The root contains the nested module. |

## Interactions

A reader opens this module, follows Alpha, or descends into the nested module. The maintained
[Fixture Level View](diagrams/fixture-level-view.json) explains the same bounded structure.
