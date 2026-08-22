---
id: contract.integration.agent-skills
kind: contract
module: module.concorde.spec-kit-integration
role: provided
flow: bidirectional
counterparties:
  - external.coding-agent
representation:
  kind: standard
  format: Spec Kit extension command Markdown
  version: "0.16.4"
  definition: specs/concorde/features/001-concorde-starter-workflow/contracts/agent-commands.md
features:
  - feature.integration.compose-starter-workflow
  - feature.integration.manage-feature-workspace
evidence_status: partial
---

# Agent Skills Contract

## Purpose

Expose portable orchestration for Concorde initialization, feature placement/selection, bounded
context, and validation.

## Information

Command Markdown carries user arguments, operation intent, runtime invocation, approval rules,
structured output handling, and failure behavior.

## Obligations

Every integration preserves the canonical operation contract and uses project-relative runtime paths.

## Failure Semantics

Missing runtime, unsupported Python, invalid sources, or refused writes remain visible and non-zero.

## Compatibility

Command registration follows Spec Kit 0.16.4 and is tested in skills and slash-command modes.

## Evidence

Initialization, context, and validation are verified in installed Codex skills mode and Gemini
slash-command mode. Evidence remains partial until feature creation and selection pass the same suite.
