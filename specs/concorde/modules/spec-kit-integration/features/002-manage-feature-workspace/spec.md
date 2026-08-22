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
workspace, and run every normal Spec Kit phase with durable intent at the feature root and temporal
delivery artifacts under `implementation/`.

## Representative Scenario

`scenario.integration.place-and-select-feature` illustrates reviewed placement followed by normal
specification and phase-specific path routing. It is an example, not the feature definition.

## Requirements

- Creation must not silently choose or change architectural ownership.
- Selection must use Spec Kit's supported project-scoped feature pointer rather than a Concorde copy.
- Specify, contracts, and checklists resolve from the feature root.
- Plan, tasks, implement, analyze, and converge resolve from `implementation/`.
- Existing active or accepted delivery attempts require an explicit resume or conflict decision.
- Installed behavior must be delivered through supported preset/extension mechanisms and covered by
  clean-project compatibility tests.

## Evidence

Automated contract, integration, and acceptance tests verify proposal safety, deterministic nested
placement, atomic selection, explicit resume handling, all nine phase-routing addenda, and both
Codex-skill and slash-command composition in clean projects. Evidence remains `partial` because the
human placement and authority-comprehension protocols have not been conducted.
