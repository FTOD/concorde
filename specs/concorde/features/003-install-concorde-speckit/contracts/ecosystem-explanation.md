# Interface Profile: Spec Kit Ecosystem Explanation

This feature-local profile governs how Feature 003 explains the existing root
`contract.concorde.spec-kit-installation`. It does not declare a second architecture contract or replace
package manifests, module contracts, or the feature specification.

## Purpose

Give maintainers one consistent textual and visual model of how Concorde participates in Spec Kit,
including install-time composition and the two distinct use-time paths.

## Role Model

| Role | Required explanation |
|---|---|
| Spec Kit | Owns resolution, template composition, installation, registries, provenance, update/removal, and active-integration selection. |
| Catalog | Carries discovery and trust metadata for independently packaged bundle, preset, and extension archives. |
| Bundle | Is a passive, non-executable recipe pinning exactly one preset and one extension. |
| Preset | Composes architecture guidance into templates (including the Concorde-only `abstract-template` for the feature-root `abstract.md` and `implementation-template` for the feature-root `design.md`) and authoritative selected-workspace routing into nine existing lifecycle commands. It introduces no new runtime command namespace. |
| Extension | Actively contributes five Concorde-specific surfaces: four runtime-backed intents, one agent-followed read-only question procedure, a selected-workspace adapter, and the deterministic runtime used only by the operations. |
| Active coding-agent integration | Materializes resolved core-command overrides and Concorde-specific commands in agent-native syntax without owning their behavior. |
| Skills | Are the installed user-facing command instructions materialized from the preset and extension sources. |
| Scripts | Implement workspace routing and deterministic initialization, context, validation, and acceptance operations. |
| Workspace Files | Preserve durable specification and accepted realization outside `attempt/`, and temporal delivery memory inside it. |

The explanation must say that Concorde augments the standard Spec Kit lifecycle; it does not replace
`specify`, `plan`, `tasks`, or the single canonical feature `design.md`. It must also distinguish the
source checkout's self-hosting `.agents/` and `.specify/` files from the preset and extension files
that a clean target actually receives from release archives.

## Authority Split

| Fact | Authority |
|---|---|
| Package identity, version, and content declarations | Bundle, preset, and extension manifests |
| Catalog location, digest, compatibility, and trust metadata | Generated catalog entries |
| Feature behavior and success criteria | Feature 003 `design.md` |
| Boundary obligations and failure semantics | Canonical module contracts and feature-local interface contracts |
| Supplemental visual composition | The two Feature 003 Archify JSON sources |
| Existing lifecycle-command routing instructions | Preset command sources and their resolved installed surfaces |
| Concorde-specific command/runtime behavior | Extension implementation |
| Published visual projection | Generated HTML, which is reproducible and non-authoritative |

## Required Views

| Question | Maintained source | Published projection |
|---|---|---|
| What are the ecosystem components, and who owns what? | `diagrams/spec-kit-component-model.json` | `/architecture/concorde-spec-kit-component-model.html` |
| What happens during release/install and along each use-time path? | `diagrams/bundle-installation-flow.json` | `/architecture/concorde-bundle-installation-flow.html` |

These are feature-owned Feature 003 explanations: the component model is the single `role: core`
architecture view and the installation flow is `role: supplemental`. Both supplement rather than
replace the module-owned level views under `architecture/diagrams/`, do not participate in
Scripts source Profile 4, and must not redefine the root module's one-level participants or contracts.

## Accessibility and Evidence

- `abstract.md`, `design.md`, `implementation.md`, and the relevant module summary, module design reference, and
  contract prose must contain a complete explanation that can be understood without opening either
  diagram.
- Both source JSON files must pass all Archify showcase checks and produce fresh, provenance-bearing
  generated HTML.
- Deterministic diagram validation must cover composition, provenance, freshness, and configured
  light/dark theme behavior without errors or warnings.
- The existing documentation site publishes the generated views; this feature adds no render or
  publication command to the Concorde bundle.

## Failure Semantics

The explanation is invalid when roles conflict across prose or diagrams, a diagram implies that the
bundle embeds or executes its components, the active integration is shown as owning behavior, the
preset is shown as runtime-owning or as introducing Concorde-specific command IDs, command
composition is described as template composition only, self-hosting checkout files are presented as
release inputs, a supplemental view is treated as canonical module architecture, a generated output
is stale, or the textual explanation depends on the visual.

## Compatibility

The profile describes the tested Spec Kit 0.16.4 integration. Any later component kind, lifecycle
owner, agent-integration responsibility, or supported Spec Kit version requires synchronized updates
to prose, both diagrams where affected, validation evidence, and the comprehension pilot.
