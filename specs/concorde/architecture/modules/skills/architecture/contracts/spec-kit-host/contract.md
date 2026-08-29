---
id: contract.skills.spec-kit-host
kind: contract
module: module.concorde.skills
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
  - feature.skills.compose-workflow
evidence_status: partial
---

# Spec Kit Host Contract

## Purpose

Consume public component packaging, template/command composition, feature selection, lifecycle, and
agent registration services.

## Information

The platform exchanges manifests, resolved template/command stacks, installed component records,
active integration identity, five registered Concorde command artifacts, explicit feature-directory
selection, and the normal lifecycle phase context. Four Concorde artifacts describe runtime-backed
operations; `speckit.concorde.ask` is package-neutral agent guidance with no launcher registration.

## Obligations

Spec Kit validates compatibility before mutation, exposes deterministic component ownership, and
preserves one explicitly selected feature root across phases. Concorde command composition may adapt
artifact paths but must preserve the standard meaning of every phase.

## Failure Semantics

Unsupported versions and registration failures stop the affected operation without silent fallback.

## Compatibility

The supported platform is exactly Spec Kit 0.16.4 for the initial release.

## Evidence

Component packaging and registration of five Concorde-specific command artifacts are verified
against Specify CLI 0.16.4. Evidence is partial until clean-project tests execute the four runtime
intents, review the read-only question intent in both supported presentations, and execute all nine
affected normal-command surfaces from release-installed artifacts, prove the complete phase-path
matrix (durable `abstract.md`/`design.md`/`implementation.md`, module `module.md`/`design.md`, and temporal
`attempt/`), and verify lower-layer restoration.
