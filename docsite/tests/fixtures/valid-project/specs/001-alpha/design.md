---
id: feature.fixture.alpha
kind: feature
module: module.fixture
subfeatures:
  - feature.fixture.alpha.prepare
  - feature.fixture.alpha.finish
diagrams:
  - source: specs/001-alpha/diagrams/alpha-components.json
    kind: architecture
    role: core
    scenarios:
      - alpha-overview
    output: generated/architecture/fixture-alpha-components.html
---

# Feature Design: Alpha

**Status**: Draft

## Outcome

Alpha coordinates two focused outcomes.

## Requirements

- Alpha is visible.
