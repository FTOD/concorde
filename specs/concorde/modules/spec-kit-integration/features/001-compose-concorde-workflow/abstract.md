# Feature Abstract: Compose Concorde into the Spec Kit Lifecycle

`feature.integration.compose-concorde-workflow` · specified at `module.concorde.spec-kit-integration`
· refines `feature.concorde.install-with-spec-kit` and `feature.concorde.self-host-framework` ·
about three minutes. This page is enough to understand how Concorde's guidance and commands enter a
Spec Kit project and what must hold; the links at the end only redirect you when you want more.

## Purpose

A supported Spec Kit project receives composed Concorde guidance and authoritative selected-workspace
routing in its normal feature lifecycle, plus portable installed commands for deterministic
architecture services. It serves the maintainer whose project should gain architectural controls
without a second orchestrator, and the Concorde contributor whose own checkout is materialized from
current local sources through the same public preset and extension development lifecycle.

## Functionality

Two components with distinct, native Spec Kit mechanisms:

| Component | Contribution | Installed through |
|---|---|---|
| `concorde-core` preset | Template layers plus overrides of the nine existing normal commands, each resolving the selected durable or temporal workspace before any inherited root-path assumption runs. | Spec Kit preset composition. |
| `concorde` extension | New executable Concorde commands, launchers that locate the runtime relative to the extension, and portable access to deterministic architecture services. | Spec Kit extension registration. |

Both are materialized by the active coding-agent integration in its native skill or slash-command
syntax, and commands keep identical intent, arguments, result envelopes, and failures across
integrations. The single canonical Spec Kit feature specification is preserved. Nested feature
placement and selection semantics belong to `feature.integration.manage-feature-workspace`; in
Concorde's own checkout, approval, recovery, receipts, drift comparison, and activation reporting
belong to the root self-hosting feature.

**Not part of this feature**: Spec Kit's core phases, agent-specific runtimes, architecture
validation semantics, workspace placement and selection, and self-hosting approval or drift
detection.

## Structure

The installation feature's core view
<a href="/architecture/concorde-spec-kit-component-model.html">Spec Kit component model</a>
separates preset guidance, extension commands, active-agent presentation, and Architecture Core;
its supplemental <a href="/architecture/concorde-bundle-installation-flow.html">bundle
installation flow</a> shows their setup order (maintained sources under
`specs/concorde/features/003-install-concorde-speckit/diagrams/`). This refinement adds no diagram.

```text
Spec Kit 0.16.4 (spec-kit-platform) ── installs ──▶ concorde-core preset ──▶ templates + 9 command overrides ─┐
                                    └─ registers ─▶ concorde extension  ──▶ Concorde commands + launchers ────┤
active coding-agent integration ◀── materializes both (agent-skills) ◀───────────────────────────────────────┘
installed command ──▶ selected-workspace routing ──▶ launcher ──▶ runtime (Python 3.11) ──architecture-services──▶ Architecture Core
```

The module provides `contract.integration.workflow-composition` and
`contract.integration.agent-skills` and requires `contract.integration.spec-kit-platform` and
`contract.integration.architecture-services`; every architecture semantic is delegated to
Architecture Core.

## Logic

**From components to working commands**

1. Spec Kit installs the preset and registers the extension from the release bundle (or, in the
   Concorde checkout, from local sources through the public development lifecycle).
2. Spec Kit resolves component layers; the active integration materializes the winners as
   agent-native surfaces.
3. Each normal phase first resolves the selected workspace, then runs its composed guidance.
4. A Concorde command calls its launcher, which locates the runtime relative to the extension and
   invokes Architecture Core deterministically.
5. Evidence comes from a clean project installed from the release bundle with the checkout
   unavailable.

**Rules the implementation must keep**

- Composition preserves the single canonical Spec Kit feature specification (Requirements, item 1).
- Template layers, existing-command overrides, and new executable commands are distinct
  contributions installed through their native Spec Kit mechanisms (Requirements, item 2).
- All nine affected normal commands resolve the selected durable or temporal workspace before any
  inherited root-path assumption can execute (Requirements, item 3).
- Commands keep identical intent, arguments, result envelopes, and failures across integrations
  (Requirements, item 4).
- Installed launchers resolve the runtime relative to the extension and require only Python 3.11
  (Requirements, item 5).
- Clean-project evidence installs from the release bundle with the checkout unavailable; local
  self-hosting skills and scripts are not product evidence (Requirements, item 6).
- Development self-hosting uses public local preset and extension installation and stays
  behaviorally equivalent to the same contents installed through the bundle (Requirements, item 7).

## Read Next

- **Exact outcome, scenario, and requirements** — [design.md](design.md).
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md).
- **The contracts** — [workflow-composition](../../contracts/workflow-composition/contract.md),
  [agent-skills](../../contracts/agent-skills/contract.md),
  [spec-kit-platform](../../contracts/spec-kit-platform/contract.md), and
  [architecture-services](../../contracts/architecture-services/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the Spec Kit Integration
  summary) and its [design reference](../../design.md); the sibling feature is
  [manage-feature-workspace](../002-manage-feature-workspace/design.md); the root summary is
  [module.md](../../../../module.md).
- **The parent features** — [Install and Set Up Concorde with Spec Kit](../../../../features/003-install-concorde-speckit/abstract.md)
  and [Self-Host the Concorde Framework](../../../../features/004-self-host-concorde/abstract.md).
- **Framework guide** — [docs/commands.md](../../../../../../docs/commands.md).
