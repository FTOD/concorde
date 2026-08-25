---
id: feature.integration.manage-feature-workspace
kind: feature
module: module.concorde.spec-kit-integration
refines:
  - feature.concorde.core-workflow
scenarios:
  - scenario.integration.place-and-select-feature
contracts:
  provided:
    - contract.integration.feature-workspace
    - contract.integration.workflow-composition
    - contract.integration.agent-skills
  required:
    - contract.integration.spec-kit-platform
    - contract.integration.architecture-services
evidence_status: partial
canonical_spec: specs/concorde/modules/spec-kit-integration/features/002-manage-feature-workspace/spec.md
---

# Manage a Nested Feature Workspace

**Status**: Implemented for automated workspace behavior; human workflow evidence pending

## Outcome

A maintainer can review a feature's providing module, create or select its one nested canonical
workspace, run every normal Spec Kit phase with durable intent and accepted design at the feature
root and temporal delivery artifacts under `implementation/`, then explicitly harden a completed
attempt into that permanent design.

## Representative Scenario

`scenario.integration.place-and-select-feature` illustrates reviewed placement followed by normal
specification and phase-specific path routing. It is an example, not the feature definition.

## Diagram Decision

The parent feature's `diagrams/core-workflow-components.json` core architecture view shows the Coding
Agent invoking this Integration-owned workspace service through
`feature.create`/`feature.select`/`feature.harden`,
with the selected workspace shared with the normal Spec Kit lifecycle and Architecture Core. It is
the text-backed cross-component view for this refinement; another child diagram would duplicate that
component boundary.

## Requirements

- Creation must not silently choose or change architectural ownership.
- Selection must use Spec Kit's supported project-scoped feature pointer rather than a Concorde copy.
- Specify and contracts resolve from the feature root; every generated checklist resolves from
  `implementation/checklists/` while reading the durable specification as context.
- Permanent accepted realization resolves from root `design.md` and is never changed by normal phases.
- Plan, tasks, implement, analyze, and converge resolve from `implementation/`.
- Existing active or accepted delivery attempts require an explicit resume or conflict decision.
- Hardening requires complete tasks, a reviewed digest-bound design proposal, and explicit approval;
  it removes only the selected feature's temporal `implementation/` workspace.
- Installed behavior must be delivered through supported preset/extension mechanisms and covered by
  clean-project compatibility tests.

## Evidence

Automated contract, integration, and acceptance tests verify proposal safety, deterministic nested
placement, atomic selection, explicit resume and hardening handling, all nine complete phase-command
replacements, and both
Codex-skill and slash-command composition in clean projects. Evidence remains `partial` because the
human placement and authority-comprehension protocols have not been conducted.
