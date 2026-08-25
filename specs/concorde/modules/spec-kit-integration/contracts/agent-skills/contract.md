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
  definition: specs/concorde/features/001-concorde-workflow/contracts/agent-commands.md
features:
  - feature.integration.compose-starter-workflow
  - feature.integration.manage-feature-workspace
evidence_status: partial
---

# Agent Skills Contract

## Purpose

Expose portable orchestration for Concorde initialization, feature placement/selection, bounded
context, validation, and source-grounded workflow questions, while presenting the preset's resolved
normal-command overrides through the same active integration.

## Information

Command Markdown carries user arguments, operation intent, selected-workspace routing, runtime
invocation, approval rules, structured output handling, and failure behavior. Registered artifacts
may be skill or slash-command presentations. The workflow-question surface additionally carries the
rules for source grounding, citations, uncertainty, bounded context, and non-mutation without
pretending that an agent-authored answer is deterministic runtime output.

## Obligations

Every integration preserves the canonical command contract, selected-workspace and phase-path
semantics, and project-relative runtime paths for the six operational surfaces. The `ask` artifact
instead reads installed guidance and the smallest relevant bounded project context, cites framework
and project facts, distinguishes inference and uncertainty, asks one focused clarification when
necessary, and performs no mutation or implicit lifecycle operation. Registration must materialize
the currently winning composed layer rather than merely retain matching text in an inactive source.

## Failure Semantics

Missing runtime, unsupported Python, invalid sources, or refused writes remain visible and non-zero.

## Compatibility

Command registration follows Spec Kit 0.16.4 and is tested in skills and slash-command modes.

## Evidence

Initialization, context, and validation are verified in installed Codex skills mode and Gemini
slash-command mode. Evidence remains partial until all seven Concorde-specific intents—including the
read-only question intent—and all nine affected normal commands execute from release-installed
artifacts in both presentation modes.
