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
  - feature.integration.manage-feature-workspace
evidence_status: partial
---

# Spec Kit Platform Contract

## Purpose

Consume public component packaging, template/command composition, feature selection, lifecycle, and
agent registration services.

## Information

The platform exchanges manifests, resolved template/command stacks, installed component records,
active integration identity, registered command artifacts, explicit feature-directory selection, and
the normal lifecycle phase context.

## Obligations

Spec Kit validates compatibility before mutation, exposes deterministic component ownership, and
preserves one explicitly selected feature root across phases. Concorde command composition may adapt
artifact paths but must preserve the standard meaning of every phase.

## Failure Semantics

Unsupported versions and registration failures stop the affected operation without silent fallback.

## Compatibility

The supported platform is exactly Spec Kit 0.16.4 for the starter release.

## Evidence

Component packaging and three starter commands are verified against Specify CLI 0.16.4. Evidence is
partial until clean-project tests prove public command composition, nested feature selection, and the
complete durable/temporal phase path matrix.
