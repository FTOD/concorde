---
id: contract.integration.workflow-composition
kind: contract
module: module.concorde.spec-kit-integration
role: provided
flow: output
counterparties:
  - external.spec-kit
representation:
  kind: standard
  format: Spec Kit preset template composition
  version: "0.16.4"
  definition: https://github.com/github/spec-kit/blob/v0.16.4/presets/ARCHITECTURE.md
features:
  - feature.integration.compose-starter-workflow
  - feature.integration.manage-feature-workspace
evidence_status: partial
---

# Workflow Composition Contract

## Purpose

Compose Concorde architecture guidance and selected-workspace routing into Spec Kit's normal
lifecycle while preserving the selected feature's durable/temporal path boundary.

## Information

The standard preset format carries template or command identity, source path, priority, and
composition strategy. Concorde contributes four template layers and nine existing-command layers.

## Obligations

Composition preserves core phase semantics and one canonical root `spec.md` while adding ownership,
contract, view, evidence, and freshness gates. The installed winning command surface resolves the
selected workspace before any inherited step assumes a root-level temporal artifact. Durable phases
use the feature root; planning and delivery phases use `implementation/`; neither path creates root
aliases. Repository-local self-hosting commands and scripts are not distributed evidence.

## Failure Semantics

Missing fragments, ambiguous winning layers, an inherited root-path step that runs before workspace
resolution, or an incompatible resolver stop composition with a diagnostic.

## Compatibility

Validated against the Spec Kit 0.16.4 composition stack.

## Evidence

Template composition is verified by resolver-stack tests. Evidence remains partial until the
installed winning surfaces execute the complete phase-path matrix in clean skills and slash-command
projects with the source checkout unavailable. Disable preserves registered commands according to
Spec Kit 0.16.4; removal restores surviving lower layers.
