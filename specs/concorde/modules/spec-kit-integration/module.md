---
id: module.concorde.spec-kit-integration
kind: module
parent: module.concorde
children: []
features:
  - feature.integration.compose-starter-workflow
contracts:
  provided:
    - contract.integration.workflow-composition
    - contract.integration.agent-skills
  required:
    - contract.integration.spec-kit-platform
    - contract.integration.architecture-services
---

# Spec Kit Integration

## Responsibility

Compose Concorde's architectural rules into the normal Spec Kit lifecycle and expose portable
Concorde commands through the active coding-agent integration.

## Boundary

This module owns preset and extension packaging, command instructions, hook declarations, and
translation between Spec Kit lifecycle context and Architecture Core services. It does not own Spec
Kit core phases, agent-specific runtimes, or architecture validation semantics.

## Feature Set

- `feature.integration.compose-starter-workflow` refines
  `feature.concorde.install-starter-workflow` and owns preset composition and command registration.

## Canonical Contract Definitions

Maintained definitions live under `contracts/*/contract.md`; the summaries below provide bounded
context.

### `contract.integration.workflow-composition`

- **Role / flow**: provided, output.
- **Consumers**: Spec Kit feature lifecycle commands.
- **Representation**: commonly adopted Spec Kit preset manifest and template composition, version
  `0.16.4`.
- **Information**: architecture ownership, contract, scenario, traceability, and quality-gate guidance.
- **Guarantees**: composition preserves core lifecycle responsibilities and creates no duplicate
  canonical feature specification.
- **Failure**: unresolved templates or incompatible composition stop the affected workflow phase.
- **Evidence**: verified by append-only resolver composition and nested-workspace acceptance.

### `contract.integration.agent-skills`

- **Role / flow**: provided, bidirectional.
- **Consumers**: supported coding-agent integrations.
- **Representation**: commonly adopted Spec Kit extension command Markdown, version `0.16.4`.
- **Information**: user arguments, bounded project context, requested action, result, and diagnostics.
- **Guarantees**: canonical commands `speckit.concorde.init`, `speckit.concorde.context`, and
  `speckit.concorde.validate` register in the active integration without hard-coded invocation syntax.
- **Failure**: unsupported integrations or missing dependencies produce an actionable diagnostic.
- **Evidence**: verified in Codex skills mode and Gemini slash-command mode.

### `contract.integration.spec-kit-platform`

- **Role / flow**: required, bidirectional.
- **Provider**: external Spec Kit `0.16.4`.
- **Representation**: commonly adopted extension, preset, command-registration, and hook contracts.
- **Guarantees required**: runtime template resolution and install-time command registration behave as
  documented by Spec Kit.
- **Failure**: incompatibility stops installation or the affected phase without silent fallback.
- **Evidence**: verified against Spec Kit 0.16.4 by the native lifecycle suite.

### `contract.integration.architecture-services`

- **Role / flow**: required, bidirectional.
- **Provider**: `module.concorde.architecture-core`.
- **Representation**: custom Concorde Architecture Service Protocol v1 defined by Architecture Core.
- **Information**: target path or stable ID, operation, bounded context, validation findings, and
  artifact changes.
- **Guarantees required**: deterministic results and explicit unknown evidence.
- **Failure**: invalid sources fail without partial silent mutation.
- **Evidence**: verified by structured-result, launcher, and installed starter-journey tests.
