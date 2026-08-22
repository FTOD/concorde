---
id: feature.integration.compose-starter-workflow
kind: feature
module: module.concorde.spec-kit-integration
refines:
  - feature.concorde.install-with-spec-kit
scenarios:
  - scenario.integration.compose-and-register
contracts:
  provided:
    - contract.integration.workflow-composition
    - contract.integration.agent-skills
  required:
    - contract.integration.spec-kit-platform
    - contract.integration.architecture-services
evidence_status: partial
canonical_spec: specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/spec.md
---

# Compose Concorde into the Spec Kit Lifecycle

**Status**: Automated composition and clean installed-command parity implemented; human and browser visual evidence pending

## Outcome

A supported Spec Kit project receives composed Concorde guidance and authoritative selected-workspace
routing in its normal feature lifecycle, plus portable installed commands for deterministic
architecture services. Nested feature placement and selection semantics are owned separately by
`feature.integration.manage-feature-workspace`.

## Representative Scenario

`scenario.integration.compose-and-register` shows Spec Kit composing templates and existing-command
overrides from the preset, registering the extension's new commands, materializing both through the
active integration, and verifying them in a clean target. It is a representative example rather than
an exhaustive definition.

## Diagram Decision

The parent installation feature's `diagrams/spec-kit-component-model.json` separates preset guidance,
extension commands, active-agent presentation, and Architecture Core, while
`diagrams/starter-installation-flow.json` shows their setup order. Those diagrams and the Integration boundary
contracts fully cover this refinement; a separate child diagram would repeat the same flow.

## Requirements

- Composition preserves the single canonical Spec Kit feature specification.
- The preset's template layers, preset's existing-command overrides, and extension's new executable
  commands are explained as distinct contributions installed through their native Spec Kit mechanisms.
- All nine affected normal commands resolve the selected durable or temporal workspace before any
  inherited root-path assumption can execute.
- Commands keep identical intent, arguments, result envelopes, and failures across integrations.
- Installed launchers resolve the runtime relative to the extension and require only Python 3.11.
- Clean-project evidence installs from the release bundle with the Concorde checkout unavailable;
  local self-hosting skills and scripts are not accepted as product evidence.
