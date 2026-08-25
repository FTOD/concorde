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
diagrams:
  - source: specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json
    role: core
    kind: architecture
    scenarios:
      - inspect-install-and-verify-concorde
    output: generated/architecture/concorde-spec-kit-component-model.html
  - source: specs/concorde/features/003-install-concorde-speckit/diagrams/starter-installation-flow.json
    role: supplemental
    kind: workflow
    scenarios:
      - inspect-install-and-verify-concorde
      - manage-concorde-installation
    output: generated/architecture/concorde-starter-installation-flow.html
evidence_status: verified
canonical_spec: specs/concorde/features/003-install-concorde-speckit/spec.md
---

# Feature Specification: Install and Set Up Concorde with Spec Kit

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-22

**Revised**: 2026-08-25

**Status**: Implemented; automated distribution, clean-project acceptance, and deterministic diagram
evidence verified

**Input**: User description: "Install and set up Concorde through Spec Kit, and ensure the released
bundle correctly overrides the normal commands and skills so a user's clean project receives the
same Concorde workflow rather than only this repository's local modifications, including temporal
`implementation/checklists/` placement with no feature-root compatibility directory."

## How Concorde Is Delivered through Spec Kit

Spec Kit is the host platform. It resolves packages, records provenance, installs commands through
the active coding-agent integration, and continues to own the normal feature lifecycle. Concorde is
delivered as independently versioned ecosystem parts with different responsibilities:

| Concept | Responsibility in setup | Explicit boundary |
|---|---|---|
| **Catalog** | Advertises package identity, version, compatibility, download location, integrity, and trust metadata. | It is discovery metadata, not installed product behavior. |
| **Bundle** | Provides an inspectable recipe that pins the compatible Concorde preset and extension versions. | It is not executable behavior, a template layer, or a replacement workflow. |
| **Preset** | Composes Concorde guidance into normal templates and authoritative routing into the existing Spec Kit lifecycle commands. | It introduces no new runtime command namespace and creates no second canonical feature specification. It does not register commands by itself; Spec Kit materializes its resolved command layers. |
| **Extension** | Provides seven Concorde-specific command definitions: six runtime-backed operations plus the agent-followed, read-only `ask` procedure, together with the selected-workspace adapter and deterministic runtime. | It does not own the normal Spec Kit phases or agent-specific presentation syntax, and `ask` is not a runtime operation. |
| **Coding-agent integration** | Materializes both resolved core-command overrides and Concorde-specific commands using the active agent's supported skill or slash-command form. | It adapts invocation syntax without changing command intent or path semantics. |
| **Architecture Core** | Performs project-scoped initialization, bounded context retrieval, and validation after setup. | Its behavior belongs to the Concorde workflow, not to installation. |

The `concorde-starter` bundle pins exactly the tested `concorde-core` preset and `concorde` extension.
Spec Kit expands the recipe before installation, installs each part through its native component
lifecycle, resolves the preset command stack, materializes the result for the active coding-agent
integration, and records ownership for later update or removal. Release building writes the future
catalog/archive location into metadata; it does not contact that URL during the build.

The normal Spec Kit command names remain the user-facing lifecycle. Concorde's preset must provide
the complete routing layer for `specify`, `clarify`, `checklist`, `plan`, `tasks`, `implement`,
`analyze`, `converge`, and `taskstoissues`. Once installed, each resolved command must select the
nested feature workspace before any phase-specific file is read or written. Durable intent and
accepted design stay at the feature root, while requirements-quality checklists, planning, and
delivery artifacts stay under `implementation/`. The preset also supplies the permanent `design.md`
template. The extension
supplies `speckit.concorde.feature.harden`, which proposes and, only after explicit approval,
atomically promotes a completed attempt into that design and removes `implementation/`.
Repository-local `.agents/` skills and `.specify/` scripts are self-hosting evidence only: a released
Concorde installation must work when those checkout files are unavailable.

Two supplemental, text-backed views explain this boundary:

- `diagrams/spec-kit-component-model.json` and its generated component view show the package roles,
  command-composition boundary, active integration, and clean installed project.
- `diagrams/starter-installation-flow.json` and its generated workflow view show release, discovery,
  preview, installation, command materialization, clean-project verification, update, and removal.

The component model supports User Stories 1 and 3 by distinguishing discovery, template guidance,
core-command composition, Concorde-specific commands, agent presentation, and runtime ownership. The
installation flow supports all four stories by showing preview and approval before installation,
then materialization and an actual clean-project lifecycle before setup is accepted. Together they
demonstrate the encouraged Concorde pattern: use feature-owned diagrams when component roles or
invocation order would be harder to understand from prose alone.

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
using the separately specified Concorde workflow.

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

### User Story 3 - Verify the Installed Workflow, Not Just Files (Priority: P1)

As a maintainer, I can verify that the release installed the same Concorde workflow used to develop
Concorde itself, so I can begin work without copying or editing command skills by hand.

**Why this priority**: Registered files or matching snippets are not evidence that the resulting
commands execute the correct phase in the correct nested workspace.

**Independent Test**: Build the release, install its bundle into a pristine supported project that
cannot read the Concorde source checkout, and execute the normal lifecycle through one skills-based
and one slash-command-based presentation. Verify every durable and temporal output path, all seven
Concorde-specific surfaces (including six runtime-backed operations), and restoration after the
preset is disabled or removed.

**Acceptance Scenarios**:

1. **Given** a pristine supported Spec Kit project, **When** the released bundle is installed,
   **Then** the active integration contains resolved Concorde-aware forms of all nine normal lifecycle
   commands and all seven Concorde-specific surfaces declared by the installed manifests.
2. **Given** a selected nested feature, **When** `specify`, `clarify`, or `checklist` runs, **Then**
   the canonical `spec.md` and contracts remain at the feature root, every generated checklist is
   placed under `implementation/checklists/`, and no duplicate specification or root checklist is
   created.
3. **Given** the same selected feature, **When** `plan`, `tasks`, `implement`, `analyze`, `converge`,
   or `taskstoissues` runs, **Then** it uses that feature's single active `implementation/` workspace
   and creates no root-level compatibility copy of temporal artifacts.
4. **Given** a newly created feature, **When** its installed workspace is inspected, **Then** it has
   permanent root `spec.md` and `design.md` artifacts plus, while specification review or delivery is
   active, one temporal `implementation/` directory containing its checklists and other attempt
   artifacts.
5. **Given** a path-sensitive normal command, **When** its installed presentation is executed,
   **Then** nested-workspace resolution occurs before any lower command layer or helper can select a
   legacy root-level plan or task path.
6. **Given** one skills-based and one slash-command-based integration, **When** equivalent lifecycle
   and Concorde commands run, **Then** they produce equivalent selected-workspace, phase-path, result,
   and failure behavior.
7. **Given** a completed implementation attempt, **When** the installed hardening command is proposed
   and explicitly approved, **Then** the reviewed design replaces root `design.md` and the exact
   `implementation/` directory, including its resolved checklists, is removed; incomplete tasks,
   unresolved checklist items, or stale proposals make no change.
8. **Given** the Concorde source checkout is unavailable, **When** clean-project verification runs,
   **Then** every command resolves only files installed from the released preset and extension archives.
9. **Given** the preset is disabled or reprioritized, **When** Spec Kit updates its preset registry,
   **Then** existing materialized commands remain active as defined by Spec Kit 0.16.4 while future
   template resolution reflects the new state or priority.
10. **Given** Concorde is updated or removed, **When** Spec Kit rematerializes registered commands,
   **Then** it installs the accepted updated layer or restores the next surviving lower-priority layer
   without leaving stale Concorde instructions.
11. **Given** verified setup, **When** the maintainer starts Feature 001's Concorde workflow, **Then** no
   manual skill edit, extra installer, duplicate feature store, or replacement lifecycle is required.

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
- A lower-priority Spec Kit command invokes a legacy root-level setup helper before an appended
  Concorde routing addendum is reached.
- A preset command appears correct as text but is not the command artifact selected by the active
  coding-agent integration.
- The test environment can accidentally read the Concorde checkout's `.agents/` or `.specify/`
  directories, masking missing release content.
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
- **FR-005**: The preset MUST compose Concorde architecture guidance into normal feature, plan, and
  task templates, supply the permanent feature-design template, and avoid creating a second
  canonical feature specification.
- **FR-006**: The preset MUST provide Concorde-aware command layers for `specify`, `clarify`,
  `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues`; these are
  overrides of existing lifecycle command surfaces, not new Concorde runtime command IDs.
- **FR-007**: Each path-sensitive preset command MUST resolve the selected feature and the correct
  durable or temporal workspace before any inherited instruction or helper can read or write a
  legacy root-level artifact.
- **FR-008**: The extension MUST register seven Concorde-specific surfaces through the target
  project's active coding-agent integration: six operations with the portable selected-workspace or
  runtime support they require and one agent-followed, read-only `ask` procedure with no runtime verb.
- **FR-009**: Setup MUST preserve Spec Kit's authority for its normal lifecycle and MUST NOT install a
  dedicated Concorde workflow component or reusable steps in the initial bundle.
- **FR-010**: Catalogs MUST remain discovery and trust metadata for independent bundle, preset, and
  extension packages and MUST NOT be presented as installed runtime components.
- **FR-011**: Release building MUST treat the supplied base address as metadata for future catalog and
  archive locations and MUST NOT require contacting that address during the build.
- **FR-012**: The initial release MUST state its supported Spec Kit range and reject an unsupported
  version before making installation changes.
- **FR-013**: Installation MUST inherit the target project's active coding-agent integration rather
  than hard-code one agent presentation.
- **FR-014**: Canonical command intent, arguments, results, selected-workspace semantics, phase paths,
  and failures MUST remain equivalent across every supported skill or slash-command presentation.
- **FR-015**: Installation MUST support approved local source, manifest, built-artifact, and trusted
  catalog inputs while applying the active source-trust policy.
- **FR-016**: Repeated installation of the same release MUST be idempotent and MUST NOT duplicate
  registry state or modify project-authored sources.
- **FR-017**: Setup verification MUST identify the installed bundle, preset, extension, versions,
  source, active/disabled state, resolved template contributions, resolved command layers, and the
  command artifacts materialized for the active integration.
- **FR-018**: Setup verification MUST execute every normal command whose artifact path is changed by
  Concorde and MUST prove the durable-root/temporal-`implementation/` path matrix without root-level
  checklist, plan, task, or other temporal compatibility copies or symlinks.
- **FR-019**: Setup verification MUST exercise all six installed runtime-backed Concorde command
  intents and inspect the installed `ask` procedure's grounding, citation, uncertainty, bounded
  context, checkout independence, and non-mutation rules through each supported presentation style
  without making installation responsible for their core workflow semantics.
- **FR-020**: Clean-project acceptance MUST install from the built bundle and generated catalogs with
  the Concorde checkout unavailable; project-local `.agents/`, `.specify/`, templates, or scripts in
  this repository MUST NOT count as distributed product behavior.
- **FR-021**: Preset disable and priority change MUST preserve already materialized commands according
  to Spec Kit 0.16.4 while changing future resolution; update and removal MUST rematerialize the
  accepted or next surviving command layer without stale Concorde instructions.
- **FR-022**: Compatible update MUST preserve project configuration and project-authored
  specifications while applying only the maintainer-approved component plan.
- **FR-023**: Removal MUST delete only components owned solely by the Concorde bundle and MUST preserve
  shared components and all project-authored `.concorde/` and `specs/` sources.
- **FR-024**: Failed installation, command materialization, or update MUST NOT record success and MUST
  report any residual state that could not be restored automatically.
- **FR-025**: Setup documentation MUST explain Spec Kit, catalog, bundle, preset, extension,
  coding-agent integration, and Architecture Core responsibilities without treating them as
  interchangeable.
- **FR-026**: This feature MUST provide text-backed component and installation/use-flow diagrams that
  distinguish release sources from installed files, template composition from command composition,
  normal command overrides from Concorde-specific commands, and self-hosting files from release
  inputs.
- **FR-027**: Supplemental setup diagrams MUST remain separate from the canonical root module
  `architecture.json`, identify their maintained sources and generated outputs, and pass deterministic
  validation and freshness checks.
- **FR-028**: Setup guidance MUST end by directing the maintainer to Feature 001's core Concorde
  workflow rather than describing installation as the workflow itself.
- **FR-029**: A command-registration check that only finds expected text MUST NOT be accepted as setup
  evidence; verification MUST execute the installed winning command surfaces and compare their
  observable workspace results with the accepted distribution contract.
- **FR-030**: Clean-project verification MUST prove that feature creation provides root `design.md`
  and that installed hardening refuses incomplete or stale attempts and applies only an explicitly
  approved, digest-bound proposal to the selected feature.
- **FR-031**: Installed `specify`, `clarify`, and `checklist` surfaces MUST route every generated
  requirements-quality artifact to the selected feature's `implementation/checklists/` directory;
  they MUST NOT create or preserve a feature-root `checklists/` compatibility location.

### Scope

**Included**:

- Package-role education and setup diagrams.
- Release validation/build, catalogs, preview, installation, provenance, verification, update, and
  removal.
- One preset and one extension installed together through one bundle recipe.
- Command discovery and cross-integration equivalence checks for the installed starter operations.
- Authoritative composition of all affected normal Spec Kit commands and clean-project execution of
  their durable/temporal path matrix.

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
- **Preset Package**: The composable contribution that supplies architecture-aware templates and
  overrides existing lifecycle command instructions without introducing a new runtime namespace.
- **Extension Package**: The active command and runtime contribution installed through Spec Kit.
- **Catalog Entry**: Trusted discovery metadata containing package identity, version, location,
  compatibility, integrity, and policy information.
- **Expanded Component Plan**: The exact preview accepted before installation and later compared with
  installed state.
- **Active Coding-Agent Integration**: The presentation adapter that renders canonical extension
  commands in a supported agent-specific form.
- **Resolved Command Surface**: The winning composed instructions materialized for one normal or
  Concorde-specific command in the active coding-agent integration.
- **Clean Target Project**: A supported project whose verification environment cannot access the
  Concorde source checkout and therefore exposes missing distribution content.
- **Installation Record**: Provenance and ownership state used for verification, update, and safe
  removal.
- **Supplemental Explanatory View**: A maintained, text-backed setup diagram with a reproducible
  generated output, provenance, and validation evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-002**: Preview and installation identify the same component IDs and versions in 100% of local,
  manifest, artifact, and trusted-catalog acceptance paths.
- **SC-003**: Three consecutive installations of the same release produce one unchanged installed
  component set and no modifications to project-authored sources.
- **SC-004**: In 100% of supported coding-agent presentations, the nine affected normal commands and
  seven Concorde-specific surfaces are materialized from the installed release; the six operations
  expose equivalent runtime behavior and `ask` preserves equivalent read-only explanatory semantics.
- **SC-005**: Every seeded unsupported-version, untrusted-source, missing-component, digest,
  collision, and partial-failure case stops without a false success record and provides actionable
  recovery information.
- **SC-006**: Compatible update and bundle removal preserve 100% of project-authored `.concorde/` and
  `specs/` source hashes and retain every shared component.
- **SC-008**: Both supplemental views pass all deterministic diagram, containment, theme, provenance,
  and freshness checks with zero errors or warnings.
- **SC-009**: Every command in the phase-path acceptance matrix reads or writes only its specified
  durable feature-root or temporal `implementation/` location in three consecutive clean-project
  runs, with every checklist below `implementation/checklists/` and zero root compatibility copies or
  symlinks.
- **SC-010**: Clean-project verification succeeds with zero reads from the Concorde checkout and
  fails when any required preset command layer, extension command, adapter, or runtime file is
  removed from the release archive.
- **SC-011**: Disable and reprioritize preserve all nine already materialized winners, while update
  and removal materialize the expected accepted or next surviving layer for all nine commands, with
  zero stale Concorde instructions.

## Assumptions

- Spec Kit `0.16.4` is the first supported host version; broader support requires equivalent
  acceptance evidence before it is advertised.
- Spec Kit's public preset command-composition and install-time registration contracts are the
  supported integration boundary. Arbitrary replacement of Spec Kit's installed core scripts is not
  assumed to be distributable by the starter bundle.
- `concorde-starter` remains integration-agnostic and lets Spec Kit inherit the target project's
  active coding-agent integration.
- Project-authored architecture sources are user data, not installed component files.
- The first bundle deliberately contains one composition component and one active capability
  component; additional component types require a separate scope decision.
- Local development may serve built catalogs and archives over localhost to exercise the same
  resolution path as publication, but the release builder only writes the supplied location into
  metadata.
- Existing bundle lifecycle evidence may be reused, but self-hosting skills, string-presence checks,
  and manually routed test fixtures do not satisfy the installed-command acceptance criteria.

## Dependencies

- A supported Spec Kit distribution with bundle, preset, extension, catalog, provenance, and active
  integration capabilities.
- A supported coding-agent integration capable of presenting installed extension commands.
- The Concorde distribution and Spec Kit Integration modules and their boundary contracts.
- Feature 001 for the Concorde workflow used after setup.
