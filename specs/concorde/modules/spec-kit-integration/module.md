---
id: module.concorde.spec-kit-integration
kind: module
parent: module.concorde
children: []
features:
  - feature.integration.compose-starter-workflow
  - feature.integration.manage-feature-workspace
contracts:
  provided:
    - contract.integration.workflow-composition
    - contract.integration.agent-skills
    - contract.integration.feature-workspace
  required:
    - contract.integration.spec-kit-platform
    - contract.integration.architecture-services
---

# Spec Kit Integration

## Responsibility

Compose Concorde's architectural rules into the normal Spec Kit lifecycle, resolve the active nested
feature workspace, and expose portable Concorde commands through the active coding-agent integration.

## Boundary

This module owns preset and extension packaging, nested feature-workspace selection, command
instructions, hook declarations, and translation between Spec Kit lifecycle context and Architecture
Core services. It does not own Spec Kit core phases, agent-specific runtimes, or architecture
validation semantics.

## Feature Set

- `feature.integration.compose-starter-workflow` refines
  `feature.concorde.install-with-spec-kit`; it owns preset composition and installed command
  registration at this level.
- `feature.integration.manage-feature-workspace` refines `feature.concorde.workflow`; it owns
  reviewed nested feature placement, active selection, and phase-specific durable/temporal path
  routing.

## Preset and Extension Model

The preset and extension are complementary but not interchangeable:

- `concorde-core` is a composition layer without its own runtime. Its template layers add Concorde
  prompts and gates to Spec Kit's existing spec, plan, and task templates. Its command layers override
  the nine affected normal lifecycle surfaces so selected-workspace routing occurs before any
  inherited root-path assumption. Phase meanings remain unchanged: durable `spec.md` and contracts
  stay at the feature root, while requirements-quality checklists and all planning/delivery artifacts
  stay under `implementation/`.
- `concorde` is an active capability package. At installation time, Spec Kit registers its command
  definitions through the target project's active coding-agent integration. At use time, those agent
  commands invoke the same deterministic Architecture Core runtime regardless of their displayed
  skill or slash-command syntax.

Neither component replaces the core Spec Kit workflow. The bundle merely installs the tested pair.
See the installation feature's
<a href="/architecture/concorde-spec-kit-component-model.html">component model</a> for the structural
relationship and
<a href="/architecture/concorde-starter-installation-flow.html">installation flow</a> for the
release-to-use sequence. Their maintained sources are
`specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` and
`specs/concorde/features/003-install-concorde-speckit/diagrams/starter-installation-flow.json`.

## Canonical Contract Definitions

Maintained definitions live under `contracts/*/contract.md`; the summaries below provide bounded
context.

### `contract.integration.workflow-composition`

- **Role / flow**: provided, output.
- **Consumers**: Spec Kit feature lifecycle commands.
- **Representation**: commonly adopted Spec Kit preset manifest and template composition, version
  `0.16.4`.
- **Information**: architecture ownership, contract, scenario, traceability, and quality-gate guidance.
- **Guarantees**: composition preserves core lifecycle responsibilities, materializes the winning
  command layer in the active integration, creates no duplicate canonical feature specification, and
  creates no root-level compatibility copy of plan or tasks.
- **Failure**: unresolved templates or incompatible composition stop the affected workflow phase.
- **Evidence**: template composition is verified. Installed durable/temporal routing remains partial
  until every affected winning command surface executes in clean Codex skills and Gemini slash-command
  projects through public preset composition with the source checkout unavailable.

### `contract.integration.agent-skills`

- **Role / flow**: provided, bidirectional.
- **Consumers**: supported coding-agent integrations.
- **Representation**: commonly adopted Spec Kit extension command Markdown, version `0.16.4`.
- **Information**: user arguments, bounded project context, requested action, result, and diagnostics.
- **Guarantees**: canonical commands `speckit.concorde.init`, `speckit.concorde.context`,
  `speckit.concorde.validate`, `speckit.concorde.feature.create`, and
  `speckit.concorde.feature.select`, plus `speckit.concorde.feature.harden`, register in the active integration without hard-coded invocation
  syntax.
- **Failure**: unsupported integrations or missing dependencies produce an actionable diagnostic.
- **Evidence**: all six command artifacts register in Codex skills mode; initialization, context,
  and validation execute in Codex skills and Gemini slash-command modes. Evidence remains partial
  until feature creation/selection and the complete normal-command matrix execute from release
  archives in both modes; platform-compatible registered spellings use `feature-create` and
  `feature-select`.

### `contract.integration.feature-workspace`

- **Role / flow**: provided, bidirectional.
- **Consumers**: maintainers and normal Spec Kit lifecycle commands.
- **Representation**: custom Concorde Feature Workspace Protocol v2 plus Spec Kit's standard
  project-local `feature_directory` selection field.
- **Information**: reviewed placement, exact durable/temporal paths, selection changes, conflicts,
  findings, and inspected source digest.
- **Guarantees**: one nested canonical specification, no root-level plan/task aliases, atomic
  selection, and no silent replacement of an implementation attempt.
- **Failure**: unsafe, stale, occupied, unknown, or ambiguous targets leave sources and selection
  unchanged and return actionable findings.
- **Evidence**: proposal, safe selection, resume conflict, phase routing, clean installation, and
  no-root-alias behavior are covered by contract, unit, integration, and acceptance tests.

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
