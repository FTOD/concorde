---
id: feature.concorde.install-with-spec-kit
kind: feature
module: module.concorde
refines: []
scenarios:
  - inspect-install-and-verify-concorde
  - manage-concorde-installation
contracts:
  provided:
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
architecture_view: specs/concorde/architecture.json
evidence_status: partial
canonical_spec: specs/concorde/features/003-install-concorde-speckit/spec.md
---

# Feature Specification: Install and Set Up Concorde with Spec Kit

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-22

**Status**: Implemented; timed first-use and comprehension pilot pending

**Input**: User description: "Create a separate feature for installing and setting up Concorde with
Spec Kit. Installation concerns must no longer define Feature 001, which owns the core Concorde
workflow."

## How Concorde Is Delivered through Spec Kit

Spec Kit is the host platform. It resolves packages, records provenance, installs commands through
the active coding-agent integration, and continues to own the normal feature lifecycle. Concorde is
delivered as independently versioned ecosystem parts with different responsibilities:

| Concept | Responsibility in setup | Explicit boundary |
|---|---|---|
| **Catalog** | Advertises package identity, version, compatibility, download location, integrity, and trust metadata. | It is discovery metadata, not installed product behavior. |
| **Bundle** | Provides an inspectable recipe that pins the compatible Concorde preset and extension versions. | It is not executable behavior, a template layer, or a replacement workflow. |
| **Preset** | Appends Concorde's architecture-aware guidance to the normal feature, plan, and task templates. | It does not register commands or create a second canonical feature specification. |
| **Extension** | Provides portable Concorde command definitions and their deterministic runtime behavior. | It does not own the feature lifecycle or agent-specific presentation syntax. |
| **Coding-agent integration** | Presents installed commands using the active agent's supported skill or slash-command form. | It adapts invocation syntax without changing command intent. |
| **Architecture Core** | Performs project-scoped initialization, bounded context retrieval, and validation after setup. | Its behavior belongs to the core workflow, not to installation. |

The `concorde-starter` bundle pins exactly the tested `concorde-core` preset and `concorde` extension.
Spec Kit expands the recipe before installation, installs each part through its native component
lifecycle, and records ownership for later update or removal. Release building writes the future
catalog/archive location into metadata; it does not contact that URL during the build.

Two supplemental, text-backed views explain this boundary:

- `spec-kit-component-model.json` and its generated component view show the package roles and the
  separate preset and extension use-time paths.
- `starter-installation-flow.json` and its generated workflow view show release, discovery, preview,
  installation, verification, update, and removal.

These diagrams explain this feature and do not replace the canonical one-level root module view in
`specs/concorde/architecture.json`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Concorde Before Installation (Priority: P1)

As a maintainer, I can understand Concorde's package roles and inspect the exact expanded installation
plan before approving setup so that I know what will be added to the project and which system owns
each behavior.

**Why this priority**: A trusted installation starts with a comprehensible, reviewable plan rather
than opaque component copying.

**Independent Test**: Starting with a supported Spec Kit project and an approved Concorde source,
inspect the starter bundle and verify that the plan names the bundle, preset, extension, versions,
compatibility range, composition strategy, integration inheritance, trust source, and intended
project-facing changes.

**Acceptance Scenarios**:

1. **Given** the Concorde release source, **When** the maintainer validates and builds it, **Then** the
   result contains independently identifiable bundle, preset, and extension packages plus catalog
   entries with integrity metadata.
2. **Given** a supported project, **When** the maintainer previews `concorde-starter`, **Then** the
   expanded plan identifies exactly one `concorde-core` preset and one `concorde` extension with their
   pinned versions, compatibility, provenance, and effects.
3. **Given** the textual explanation and diagrams, **When** a first-time maintainer reviews setup,
   **Then** they can distinguish catalog discovery, bundle composition, preset guidance, extension
   behavior, active-agent presentation, and Architecture Core.

---

### User Story 2 - Install Concorde into a New or Existing Project (Priority: P1)

As a maintainer, I can install Concorde through the native Spec Kit component lifecycle into a new or
existing supported project so that the architecture-aware guidance and Concorde commands become
available without a separate installer.

**Why this priority**: Installation is the sole outcome of this feature and the prerequisite for
using the separately specified core workflow.

**Independent Test**: Approve the expanded plan, install the starter bundle into both a clean
initialized project and a supported uninitialized directory, then verify that the installed preset,
extension, provenance, and command presentation match the accepted plan.

**Acceptance Scenarios**:

1. **Given** an accepted expanded plan, **When** the maintainer installs by approved catalog ID,
   directory, manifest, or built artifact, **Then** Spec Kit installs the same pinned component set
   and records its provenance.
2. **Given** an uninitialized directory, **When** the supported initialization-and-install path is
   used, **Then** the directory becomes a supported project with the same Concorde setup as an
   existing project.
3. **Given** the same installed release, **When** installation is repeated, **Then** it succeeds
   without duplicate component state or changes to project-authored specifications.
4. **Given** an unsupported Spec Kit version, untrusted source, incompatible component, or command
   collision, **When** installation is attempted, **Then** setup stops before claiming success and
   names the incompatibility and remediation.

---

### User Story 3 - Verify the Concorde Setup (Priority: P2)

As a maintainer, I can verify that the preset contribution, extension commands, and active coding-agent
presentation are ready so that I can begin the core Concorde workflow with confidence.

**Why this priority**: Files being copied is not sufficient evidence that the installed workflow can
actually be discovered and used.

**Independent Test**: After installation, inspect component status, resolve the normal feature
templates, discover the Concorde commands through two supported agent presentation styles, and invoke
the existing read-only or proposal-first operations against a fixture project.

**Acceptance Scenarios**:

1. **Given** a complete installation, **When** a normal feature template is resolved, **Then** the
   original Spec Kit content remains authoritative and Concorde guidance is appended without a second
   canonical feature specification.
2. **Given** the installed extension, **When** the active coding-agent integration is inspected,
   **Then** `speckit.concorde.init`, `speckit.concorde.context`, and
   `speckit.concorde.validate` are discoverable in its supported invocation form.
3. **Given** two supported agent integrations, **When** equivalent Concorde commands are invoked,
   **Then** their intent, inputs, outputs, project scope, and failure behavior remain equivalent.
4. **Given** verified setup, **When** the maintainer starts Feature 001's core workflow, **Then** no
   additional Concorde installer, duplicate feature store, or replacement lifecycle is required.

---

### User Story 4 - Update or Remove Concorde Safely (Priority: P3)

As a maintainer, I can preview and apply compatible updates or remove Concorde-owned components while
preserving project-authored sources and components shared with other installations.

**Why this priority**: Safe maintenance and exit paths are part of a trustworthy setup lifecycle.

**Independent Test**: Install the starter bundle, author project architecture sources, update to a
compatible release, and remove the bundle; verify accurate component state throughout and unchanged
project-owned sources.

**Acceptance Scenarios**:

1. **Given** an installed older release, **When** the maintainer previews and accepts an update,
   **Then** only the approved component versions change and project configuration and sources remain
   unchanged.
2. **Given** installed Concorde components, **When** the bundle is removed, **Then** only components
   owned solely by that bundle are removed while shared dependencies and project-authored `.concorde/`
   and `specs/` sources remain.
3. **Given** an installation or update failure, **When** recovery completes, **Then** success is not
   recorded and any residual partial state is reported explicitly.

### Edge Cases

- A catalog entry is valid during preview but its archive becomes unavailable before installation.
- The target project has stacked presets, local template overrides, or an existing component with the
  same stable identity.
- The active coding-agent integration is absent, disabled, or requires a reload before commands are
  visible.
- A built release uses a future public base address that is not reachable from the build environment.
- Installation loses access to its source or fails after only part of the component plan is applied.
- A locally modified installed component would be overwritten by update or removed.
- A component is shared with another bundle or installed independently.
- Project-owned `.concorde/` or `specs/` sources are malformed; installation must not treat them as
  component-owned files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Concorde MUST provide one native, schema-versioned Spec Kit bundle as the primary
  installation unit and MUST NOT require a separate Concorde installer.
- **FR-002**: The starter bundle MUST be a non-executable recipe that pins exactly one independently
  versioned Concorde preset and one independently versioned Concorde extension.
- **FR-003**: Before installation or update, maintainers MUST be able to inspect the fully expanded
  component identities, versions, dependencies, compatibility constraints, preset strategy and
  priority, trust sources, integration inheritance, and intended changes.
- **FR-004**: The installed component set and versions MUST match the plan accepted by the maintainer.
- **FR-005**: The preset MUST append Concorde architecture guidance to the normal feature, plan, and
  task artifacts without replacing core templates or creating a second canonical feature
  specification.
- **FR-006**: The extension MUST register portable Concorde commands and their supporting runtime
  through the target project's active coding-agent integration.
- **FR-007**: Setup MUST preserve Spec Kit's authority for its normal lifecycle and MUST NOT install a
  dedicated Concorde workflow component or reusable steps in the initial bundle.
- **FR-008**: Catalogs MUST remain discovery and trust metadata for independent bundle, preset, and
  extension packages and MUST NOT be presented as installed runtime components.
- **FR-009**: Release building MUST treat the supplied base address as metadata for future catalog and
  archive locations and MUST NOT require contacting that address during the build.
- **FR-010**: The initial release MUST state its supported Spec Kit range and reject an unsupported
  version before making installation changes.
- **FR-011**: Installation MUST inherit the target project's active coding-agent integration rather
  than hard-code one agent presentation.
- **FR-012**: Canonical command intent, arguments, results, project scope, and failures MUST remain
  equivalent across every supported skill or slash-command presentation.
- **FR-013**: Installation MUST support approved local source, manifest, built-artifact, and trusted
  catalog inputs while applying the active source-trust policy.
- **FR-014**: Repeated installation of the same release MUST be idempotent and MUST NOT duplicate
  registry state or modify project-authored sources.
- **FR-015**: Setup verification MUST identify the installed bundle, preset, extension, versions,
  source, active/disabled state, composed guidance, and discoverable Concorde commands.
- **FR-016**: At minimum, setup verification MUST exercise `speckit.concorde.init`,
  `speckit.concorde.context`, and `speckit.concorde.validate` through the active integration without
  making installation responsible for their core workflow semantics.
- **FR-017**: Compatible update MUST preserve project configuration and project-authored
  specifications while applying only the maintainer-approved component plan.
- **FR-018**: Removal MUST delete only components owned solely by the Concorde bundle and MUST preserve
  shared components and all project-authored `.concorde/` and `specs/` sources.
- **FR-019**: Failed installation or update MUST NOT record success and MUST report any residual state
  that could not be restored automatically.
- **FR-020**: Setup documentation MUST explain Spec Kit, catalog, bundle, preset, extension,
  coding-agent integration, and Architecture Core responsibilities without treating them as
  interchangeable.
- **FR-021**: This feature MUST provide text-backed component and installation/use-flow diagrams that
  distinguish installation-time composition from the preset-guidance and extension-command use-time
  paths.
- **FR-022**: Supplemental setup diagrams MUST remain separate from the canonical root module
  `architecture.json`, identify their maintained sources and generated outputs, and pass deterministic
  validation and freshness checks.
- **FR-023**: Setup guidance MUST end by directing the maintainer to Feature 001's core Concorde
  workflow rather than describing installation as the workflow itself.

### Scope

**Included**:

- Package-role education and setup diagrams.
- Release validation/build, catalogs, preview, installation, provenance, verification, update, and
  removal.
- One preset and one extension installed together through one bundle recipe.
- Command discovery and cross-integration equivalence checks for the installed starter operations.

**Excluded**:

- Defining the module/feature hierarchy, feature authoring lifecycle, architecture review gates,
  contract rules, or bounded implementation workflow; those belong to Feature 001.
- Publishing the project documentation site; that belongs to Feature 002.
- A second installer, a replacement Spec Kit lifecycle, a dedicated workflow component, or reusable
  workflow steps.
- Treating generated catalogs or release archives as maintained project intent.

### Key Entities

- **Bundle Recipe**: The inspectable installation plan that pins compatible component identities and
  versions but performs no runtime behavior itself.
- **Preset Package**: The passive, append-only contribution to normal lifecycle artifacts.
- **Extension Package**: The active command and runtime contribution installed through Spec Kit.
- **Catalog Entry**: Trusted discovery metadata containing package identity, version, location,
  compatibility, integrity, and policy information.
- **Expanded Component Plan**: The exact preview accepted before installation and later compared with
  installed state.
- **Active Coding-Agent Integration**: The presentation adapter that renders canonical extension
  commands in a supported agent-specific form.
- **Installation Record**: Provenance and ownership state used for verification, update, and safe
  removal.
- **Supplemental Explanatory View**: A maintained, text-backed setup diagram with a reproducible
  generated output, provenance, and validation evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of first-time maintainers can inspect the expanded plan and complete setup
  in a supported project within 15 minutes using only the quick start.
- **SC-002**: Preview and installation identify the same component IDs and versions in 100% of local,
  manifest, artifact, and trusted-catalog acceptance paths.
- **SC-003**: Three consecutive installations of the same release produce one unchanged installed
  component set and no modifications to project-authored sources.
- **SC-004**: All supported coding-agent presentations expose the required starter commands with
  equivalent observable behavior.
- **SC-005**: Every seeded unsupported-version, untrusted-source, missing-component, digest,
  collision, and partial-failure case stops without a false success record and provides actionable
  recovery information.
- **SC-006**: Compatible update and bundle removal preserve 100% of project-authored `.concorde/` and
  `specs/` source hashes and retain every shared component.
- **SC-007**: At least 90% of first-time maintainers can, after no more than five minutes of review,
  correctly distinguish catalog, bundle, preset, extension, active integration, Architecture Core,
  and the unchanged normal Spec Kit lifecycle.
- **SC-008**: Both supplemental views pass all deterministic diagram, containment, theme, provenance,
  and freshness checks with zero errors or warnings.

## Assumptions

- Spec Kit `0.16.4` is the first supported host version; broader support requires equivalent
  acceptance evidence before it is advertised.
- `concorde-starter` remains integration-agnostic and lets Spec Kit inherit the target project's
  active coding-agent integration.
- Project-authored architecture sources are user data, not installed component files.
- The first bundle deliberately contains one passive guidance component and one active command
  component; additional component types require a separate scope decision.
- Local development may serve built catalogs and archives over localhost to exercise the same
  resolution path as publication, but the release builder only writes the supplied location into
  metadata.
- The existing implementation evidence may be reused after references are remapped to this separated
  feature; the remaining first-use comprehension outcome requires real participants.

## Dependencies

- A supported Spec Kit distribution with bundle, preset, extension, catalog, provenance, and active
  integration capabilities.
- A supported coding-agent integration capable of presenting installed extension commands.
- The Concorde distribution and Spec Kit Integration modules and their boundary contracts.
- Feature 001 for the core workflow used after setup.
