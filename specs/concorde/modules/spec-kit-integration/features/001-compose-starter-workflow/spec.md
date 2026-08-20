---
id: feature.integration.compose-starter-workflow
kind: feature
module: module.concorde.spec-kit-integration
refines:
  - feature.concorde.install-starter-workflow
scenarios:
  - scenario.integration.compose-and-register
contracts:
  provided:
    - contract.integration.workflow-composition
    - contract.integration.agent-skills
  required:
    - contract.integration.spec-kit-platform
    - contract.integration.architecture-services
evidence_status: verified
canonical_spec: specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/spec.md
---

# Compose the Concorde Starter Workflow

**Status**: Implemented

## Outcome

A supported Spec Kit project receives append-only Concorde guidance in its normal feature lifecycle
and three portable agent commands that invoke the same deterministic architecture services.

## Representative Scenario

`scenario.integration.compose-and-register` shows Spec Kit composing the preset, registering the
extension for the active agent integration, and an agent invoking Architecture Core. It is a
representative example rather than an exhaustive definition.

## Requirements

- Composition preserves the single canonical Spec Kit feature specification.
- Commands keep identical intent, arguments, result envelopes, and failures across integrations.
- Installed launchers resolve the runtime relative to the extension and require only Python 3.11.
