---
id: module.concorde.spec-kit-integration
kind: module
parent: module.concorde
children: []
features:
  - feature.integration.compose-concorde-workflow
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

## Structure

This leaf module has no submodules, so no separate level view is maintained; its structure is the
`concorde-core` preset (a composition layer over Spec Kit's existing commands), the `concorde`
extension (five command surfaces, launchers, and the selected-workspace adapter), and the five
boundary contracts inventoried below. See the installation feature's
<a href="/architecture/concorde-spec-kit-component-model.html">component model</a> for the structural
relationship and
<a href="/architecture/concorde-bundle-installation-flow.html">installation flow</a> for the
release-to-use sequence; their maintained sources are
`specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` and
`specs/concorde/features/003-install-concorde-speckit/diagrams/bundle-installation-flow.json`. The
Feature 001 core view
<a href="/architecture/concorde-workflow-components.html">workflow components</a> (maintained source
`specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json`) shows the
installed surfaces, adapter, and control state at use time.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.integration.compose-concorde-workflow` | A supported Spec Kit project receives composed Concorde guidance and authoritative selected-workspace routing in its normal feature lifecycle, plus portable installed commands for deterministic architecture services; in Concorde's own checkout the same public preset and extension development lifecycle materializes current local sources. | `feature.concorde.install-with-spec-kit`, `feature.concorde.self-host-framework` | [design.md](features/001-compose-concorde-workflow/design.md) |
| `feature.integration.manage-feature-workspace` | A maintainer can review a feature's placement, create its one nested canonical workspace through the standard Spec Kit specify phase or select an existing one through the standard Spec Kit pointer, run every normal phase with durable intent at the feature root and temporal delivery artifacts under `attempt/`, then explicitly harden a completed attempt. | `feature.concorde.workflow` | [design.md](features/002-manage-feature-workspace/design.md) |

## Contracts

| Contract ID | Role | Flow | Counterparty | Definition |
|---|---|---|---|---|
| `contract.integration.workflow-composition` | provided | output | Spec Kit feature lifecycle commands | [contract.md](contracts/workflow-composition/contract.md) |
| `contract.integration.agent-skills` | provided | bidirectional | Supported coding-agent integrations | [contract.md](contracts/agent-skills/contract.md) |
| `contract.integration.feature-workspace` | provided | bidirectional | Maintainers and normal Spec Kit lifecycle commands | [contract.md](contracts/feature-workspace/contract.md) |
| `contract.integration.spec-kit-platform` | required | bidirectional | External Spec Kit `0.16.4` | [contract.md](contracts/spec-kit-platform/contract.md) |
| `contract.integration.architecture-services` | required | bidirectional | `module.concorde.architecture-core` | [contract.md](contracts/architecture-services/contract.md) |

## Submodules

None.

## Representative Scenario

`scenario.integration.place-and-select-feature` shows a maintainer recording a reviewed placement by
running Spec Kit's normal specify phase with the nested workspace directory, which writes the standard
`.specify/feature.json` selection; no Concorde creation or selection command exists. Before every later
normal phase, the preset's command override calls the selected-workspace adapter, which resolves that
selection read-only across `contract.integration.feature-workspace`: it validates the path grammar
and durable pair, checks module or parent registration, reports an active attempt, and returns the
exact durable and temporal paths for the phase. When the phase needs architecture context or
validation, the module invokes Architecture Core across `contract.integration.architecture-services`
and relays deterministic results without mutating sources. Unsafe, stale, unregistered, unknown, or
ambiguous targets leave sources and selection unchanged and return actionable findings.

## Design Rationale

The preset and the extension are complementary, not interchangeable: the preset composes guidance and
selected-workspace routing into Spec Kit's existing nine commands so routing happens before any
inherited root-path assumption, while the extension adds five Concorde surfaces (four runtime-backed
operations and the read-only, agent-followed `ask`) that register through the active coding-agent
integration without hard-coded invocation syntax. Neither component replaces the core Spec Kit
workflow, and every architecture semantic is delegated to Architecture Core. The preset and extension
model and the contract narratives are in the [design reference](design.md).
