---
id: feature.integration.manage-feature-workspace
kind: feature
module: module.concorde.spec-kit-integration
refines:
  - feature.concorde.workflow
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

A maintainer can review a feature's placement, create its one nested canonical workspace through the
standard Spec Kit specify phase or select an existing one through the standard Spec Kit pointer, run
every normal Spec Kit phase with durable intent and accepted design at the feature root and temporal
delivery artifacts under `implementation/`, then explicitly harden a completed attempt into that
permanent design.

## Representative Scenario

`scenario.integration.place-and-select-feature` illustrates reviewed placement expressed through the
standard Spec Kit selection, followed by normal specification and phase-specific path routing. It is
an example, not the feature definition.

## Diagram Decision

The parent feature's `diagrams/concorde-workflow-components.json` core architecture view shows the
Coding Agent reaching this Integration-owned workspace service through the selected-workspace
adapter that every normal phase invokes and through `feature.harden`, with the selected workspace
shared with the normal Spec Kit lifecycle and Architecture Core. It is the text-backed
cross-component view for this refinement; another child diagram would duplicate that component
boundary.

## Requirements

- Creation is the standard `speckit.specify` phase with `SPECIFY_FEATURE_DIRECTORY` set to the
  canonical root; the preset's specify addendum seeds `spec.md` and the adjacent `implementation.md` and
  persists the root to `.specify/feature.json`. It must not silently choose or change architectural
  ownership: the author records ownership in the spec front matter and feature lists, and
  `speckit.concorde.validate` enforces it deterministically.
- Selection must use Spec Kit's supported project-scoped feature pointer rather than a Concorde copy
  or a Concorde selection command.
- The selected-workspace adapter resolves and validates the selected root before every normal phase:
  safe path, canonical `spec.md`/`implementation.md` pair, workspace kind, parent context and sibling
  summaries for a sub-feature, durable/temporal paths, and `implementation_state`.
- Specify and contracts resolve from the feature root; every generated checklist resolves from
  `implementation/checklists/` while reading the durable specification as context.
- Permanent accepted realization resolves from root `implementation.md` and is never changed by normal phases.
- Plan, tasks, implement, analyze, and converge resolve from `implementation/`.
- An existing non-empty delivery attempt is reported through `implementation_state: active` and is
  never replaced or removed silently.
- Hardening requires complete tasks, a reviewed digest-bound design proposal, and explicit approval;
  it removes only the selected feature's temporal `implementation/` workspace.
- Installed behavior must be delivered through supported preset/extension mechanisms and covered by
  clean-project compatibility tests.

## Evidence

Automated contract, integration, and acceptance tests verify deterministic nested resolution of the
standard Spec Kit selection, active-attempt reporting, explicit hardening handling, all nine complete
phase-command replacements, and both Codex-skill and slash-command composition in clean projects.
Evidence remains `partial` because the human placement and authority-comprehension protocols have not
been conducted.
