---
id: feature.fixture.beta
kind: feature
module: module.fixture.nested
related_features:
  - feature.fixture.alpha
interfaces:
  provided:
    - contract.fixture.beta
  required: []
---

# Feature Design: Beta

## Outcome

Beta links to the root architecture.

## Usage

Read the [root architecture](../../../architecture.md).

## Requirements

- Beta is published once.

## Architecture Zoom

Beta is provided by `module.fixture.nested`.
