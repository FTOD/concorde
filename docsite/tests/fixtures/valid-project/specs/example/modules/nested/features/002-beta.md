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
evidence_status: verified
---

# Feature Design: Beta

**Status**: Approved

## Outcome

Beta links to the documentation home.

## Usage

Read the [documentation home](../../../../../docs/index.md).

## Requirements

- Beta is published once.

## Architecture Zoom

Beta is provided by `module.fixture.nested`.
