---
id: contract.integration.spec-kit-platform
kind: contract
module: module.concorde.spec-kit-integration
role: required
flow: bidirectional
counterparties:
  - external.spec-kit
representation:
  kind: standard
  format: Spec Kit extension and preset platform
  version: "0.16.4"
  definition: https://github.com/github/spec-kit/tree/v0.16.4
features:
  - feature.integration.compose-starter-workflow
evidence_status: verified
---

# Spec Kit Platform Contract

## Purpose

Consume public component packaging, template resolution, and agent registration services.

## Information

The platform exchanges manifests, resolved template stacks, installed component records, active
integration identity, and registered command artifacts.

## Obligations

Spec Kit validates compatibility before mutation and exposes deterministic component ownership.

## Failure Semantics

Unsupported versions and registration failures stop the affected operation without silent fallback.

## Compatibility

The supported platform is exactly Spec Kit 0.16.4 for the starter release.

## Evidence

Verified against Specify CLI 0.16.4 by the clean-project lifecycle suite.
