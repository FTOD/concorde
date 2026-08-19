---
id: feature.concorde.install-starter-workflow
kind: feature
module: module.concorde
refines: []
scenarios:
  - install-starter-workflow
  - initialize-root-architecture
  - retrieve-and-validate-context
  - manage-installation-lifecycle
contracts:
  provided:
    - contract.concorde.starter-workflow
  required:
    - contract.concorde.spec-kit-platform
architecture_view: architecture/concorde/architecture.json
evidence_status: unknown
canonical_spec: specs/001-concorde-starter-workflow/spec.md
---

# Feature Specification: Install Concorde Starter Bundle

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "Integrate Concorde into the Spec Kit ecosystem with a complete
installation process, Concorde presets, and starter Concorde commands usable as agent skills."

## Clarifications

### Session 2026-08-19

- Q: What must be the primary distribution and installation unit for Concorde? → A: A native Spec Kit bundle.
- Q: Which component types belong in the first Concorde bundle? → A: One preset and one command extension only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and Verify Concorde (Priority: P1)

As a maintainer, I can use the native Spec Kit bundle lifecycle to inspect and install Concorde into a
new or existing Spec Kit project so that the architecture-aware workflow and its agent skills are
ready to use without a separate Concorde installer or manual component copying.

**Why this priority**: Installation is the entry point for every other Concorde capability. A usable
starter workflow cannot exist until its exact contents can be inspected, installed, and verified.

**Independent Test**: Starting from a clean supported project, validate and build the Concorde bundle,
inspect its expanded component plan, install it through the native bundle command, and verify that its
preset, extension, and three starter commands are active. This delivers a usable integration even
before any project architecture has been authored.

**Acceptance Scenarios**:

1. **Given** the Concorde bundle source, **When** the maintainer uses the native bundle validation and
   build lifecycle, **Then** Spec Kit accepts its `bundle.yml` manifest and produces an installable,
   versioned bundle artifact.
2. **Given** a supported initialized Spec Kit project, **When** the maintainer inspects the Concorde
   bundle through the native bundle information command, **Then** the expanded plan identifies the
   exact preset, extension, versions, dependencies, trust source, and project-facing changes.
3. **Given** an accepted expanded plan, **When** the maintainer uses the native Spec Kit bundle install
   command with the bundle ID, local directory, manifest, or built artifact, **Then** the same component
   set is installed and the active coding-agent integration exposes the Concorde commands.
4. **Given** a directory that is not yet a Spec Kit project, **When** the maintainer installs the
   starter bundle through the supported initialization path, **Then** the project is initialized and
   Concorde reaches the same verified state as an existing project.
5. **Given** a complete installation, **When** the maintainer repeats installation, **Then** the result
   is successful and no duplicate components or changes to user-authored files are produced.

---

### User Story 2 - Initialize a Root Architecture (Priority: P2)

As a maintainer using a supported coding agent, I can invoke `speckit.concorde.init` to establish a
minimal root module, its boundary contracts, and its bounded architecture view so that the next
feature can be placed before implementation planning.

**Why this priority**: The first useful Concorde action is to establish architectural ownership and
boundaries. This proves that an installed agent skill can create reviewable Concorde sources.

**Independent Test**: Invoke the initialization command in an installed project without Concorde
architecture sources, review the proposed root package, accept it, and confirm that it contains one
root module, explicit provided and required contract sets, stable IDs, and a valid one-level view.

**Acceptance Scenarios**:

1. **Given** an installed project with no Concorde architecture package, **When** the maintainer asks
   the agent to initialize Concorde, **Then** the command proposes the root responsibility, boundary,
   contracts, immediate submodules, and architecture view before writing them.
2. **Given** an accepted proposal, **When** initialization completes, **Then** every created source has
   a stable ID, all references resolve, and no deeper-than-immediate module detail appears in the root
   view.
3. **Given** an existing Concorde architecture package, **When** initialization runs again, **Then** it
   reports the existing package and does not overwrite maintained intent without explicit approval.

---

### User Story 3 - Retrieve and Validate Bounded Context (Priority: P3)

As a maintainer or coding agent, I can invoke `speckit.concorde.context` and
`speckit.concorde.validate` so that work begins with the correct architectural level and structural
errors are found before planning or implementation.

**Why this priority**: Bounded context and deterministic validation turn the architecture sources into
an operational development control rather than passive documentation.

**Independent Test**: Against a small hierarchy containing one deliberate invalid reference, request
context for the root and run validation. Confirm that context contains only the root and its immediate
children and that validation reports the broken reference with a rule, location, and remediation.

**Acceptance Scenarios**:

1. **Given** a valid multi-level architecture, **When** context is requested for one module, **Then**
   the result includes that module's features and I/O, its immediate children and their I/O, relevant
   external actors, scenarios, and refinement links, with no grandchildren or child features expanded.
2. **Given** the same unchanged sources, **When** validation is repeated, **Then** it returns the same
   findings and outcome regardless of the coding agent used to invoke it.
3. **Given** an invalid ID, hierarchy, scenario participant, contract reference, or one-level view,
   **When** validation runs, **Then** every detected violation identifies the governing rule, affected
   source, and a concrete remediation without silently changing maintained intent.

---

### User Story 4 - Manage the Installation Lifecycle (Priority: P4)

As a maintainer, I can inspect status, update Concorde, or remove its installed components while
preserving project-owned architecture sources and components still required by other bundles.

**Why this priority**: A trustworthy ecosystem integration includes safe maintenance and exit paths,
not only a successful first installation.

**Independent Test**: Install the starter workflow, create project architecture sources, update to a
compatible release, and remove the bundle. Confirm that component state is accurate throughout and
that all project-owned sources and shared dependencies remain unchanged.

**Acceptance Scenarios**:

1. **Given** an installed older compatible release, **When** the maintainer previews and accepts an
   update, **Then** the reported component versions are refreshed and project-owned architecture
   sources remain unchanged.
2. **Given** installed Concorde components, **When** the maintainer removes the starter bundle, **Then**
   only components owned solely by that bundle are removed and project-authored sources are retained.
3. **Given** an installation or update that fails partway, **When** recovery completes, **Then** the
   project is not recorded as successfully updated and any residual partial state is reported.

### Edge Cases

- The project already has higher-priority local overrides or stacked presets for a template Concorde
  wants to compose.
- Another extension or preset provides a command or template with the same identity.
- The installed Spec Kit version is unsupported, unreadable, or changes during installation.
- The active coding-agent integration is missing, disabled, or requires a reload before new skills
  become visible.
- A bundle component resolves during preview but becomes unavailable before installation.
- Installation loses access to its source or fails after only some components are written.
- Initialization encounters a partially authored architecture package or a file with unrelated user
  content at a proposed target path.
- Context is requested for an unknown, duplicated, or cyclic module or feature ID.
- Validation runs when implementation or test evidence is absent; the result must remain `unknown`,
  not imply agreement.
- Removal encounters a component shared with another installed bundle or a locally modified component.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST provide a native Spec Kit bundle with a schema-versioned `bundle.yml`
  manifest that composes the initial Concorde preset and Concorde extension into one inspectable,
  versioned installation unit.
- **FR-002**: The starter bundle MUST use the standard Spec Kit bundle lifecycle for validation,
  building, inspection, installation, listing, update, and removal and MUST NOT require a separate
  Concorde installer.
- **FR-003**: Before installation or update, maintainers MUST be able to inspect the fully expanded
  component identities, pinned versions, preset priority and strategy, dependencies, trust sources,
  compatibility constraints, and intended changes through the native bundle information interface.
- **FR-004**: The installed component set MUST match the expanded bundle plan accepted by the
  maintainer.
- **FR-005**: The initial preset MUST add Concorde's providing-module, stable-ID, refinement, scenario,
  contract, architecture-view, and evidence expectations to feature specification work.
- **FR-006**: The initial preset MUST require architecture ownership and boundary review before an
  implementation plan can be treated as complete.
- **FR-007**: The initial preset MUST require implementation tasks to cover affected maintained
  architecture sources, contracts, validation, and generated-output freshness when applicable.
- **FR-008**: Preset composition MUST preserve Spec Kit's ownership of specification, clarification,
  planning, tasks, implementation, analysis, and convergence and MUST NOT create a duplicate canonical
  feature specification.
- **FR-009**: The initial extension MUST register `speckit.concorde.init`,
  `speckit.concorde.context`, and `speckit.concorde.validate` through the active agent integration.
- **FR-010**: The registered commands MUST keep the same intent, inputs, outputs, and failure behavior
  across all supported agent invocation syntaxes.
- **FR-011**: `speckit.concorde.init` MUST propose and, after approval, establish a minimal root
  architecture package with stable IDs, explicit boundary contract sets, immediate submodules, and a
  one-level architecture view.
- **FR-012**: Initialization MUST preserve existing maintained sources unless the maintainer explicitly
  approves a presented change.
- **FR-013**: `speckit.concorde.context` MUST return exactly one bounded architectural level for a
  requested module or feature and MUST expose stable references for deliberate navigation to deeper
  levels.
- **FR-014**: `speckit.concorde.validate` MUST deterministically check IDs, references, containment,
  refinement, scenario participants, boundary contracts, one-level visibility, and explicit evidence
  status without requiring an LLM.
- **FR-015**: Every validation finding MUST identify its rule, severity, affected source, and actionable
  remediation; validation MUST NOT silently modify maintained intent.
- **FR-016**: The initial release MUST support Spec Kit `0.16.4` and MUST reject unsupported versions
  before making installation changes.
- **FR-017**: The starter commands MUST be verified in Codex skills mode and at least one supported
  slash-command integration before the feature is accepted.
- **FR-018**: Repeated installation of the same release MUST be idempotent and MUST NOT duplicate
  registry state or alter user-authored sources.
- **FR-019**: Update MUST preserve user configuration and architecture sources while applying the
  maintainer-approved component version plan.
- **FR-020**: Removal MUST remove only components owned solely by the Concorde bundle and MUST preserve
  project-authored architecture sources and shared dependencies.
- **FR-021**: Failed installation or update MUST NOT record success and MUST report any residual partial
  state that could not be restored automatically.
- **FR-022**: Installation status and provenance MUST let maintainers identify the installed bundle,
  preset, extension, versions, source, and active or disabled state.
- **FR-023**: The starter workflow MUST include a concise quick start covering preview, installation,
  command discovery, root initialization, context retrieval, validation, update, and removal.
- **FR-024**: The architecture package and generated command results MUST distinguish intended design,
  implementation evidence, and unknown evidence rather than infer agreement among them.
- **FR-025**: The bundle manifest MUST declare schema version, stable bundle ID, display name, semantic
  version, role, description, author, license, supported Spec Kit range, component references, and
  discovery tags in the same contract used by the official Spec Kit bundle examples.
- **FR-026**: The bundle MUST be integration-agnostic so installation inherits the target project's
  active coding-agent integration.
- **FR-027**: The bundle MUST be installable from its local source directory, `bundle.yml` manifest,
  or built artifact during development and from a trusted catalog ID or approved artifact when
  distributed.
- **FR-028**: The first bundle MUST contain exactly one Concorde preset and one Concorde command
  extension; it MUST NOT declare a dedicated Concorde workflow or reusable steps.

### Scope

**Included**:

- One native, schema-valid Spec Kit starter bundle that can be validated, built, inspected, installed,
  updated, and removed through the standard bundle system.
- One architecture-aware preset covering feature, plan, and task expectations.
- One extension providing the three starter agent commands.
- Preview, installation, verification, idempotency, update, status/provenance, failure reporting, and
  safe removal.
- Root architecture initialization, one-level context retrieval, and deterministic structural
  validation.
- Compatibility acceptance for Spec Kit `0.16.4`, Codex skills mode, and one slash-command integration.

**Excluded**:

- Automatic reconstruction of architecture from source code.
- Complete contract-schema authoring assistance beyond the minimal root package.
- Archify rendering commands and Docusaurus publication commands.
- Cross-repository catalogs, organizational governance, or runtime topology ingestion.
- Automatic acceptance of architecture proposed by an agent.
- Support claims for Spec Kit versions or agent integrations not covered by acceptance evidence.
- A dedicated Concorde workflow and reusable Spec Kit steps; these require separate future features
  after the starter preset and commands are proven.

### Key Entities

- **Concorde Starter Bundle**: The native Spec Kit installation unit identified by its manifest ID and
  semantic version. It declares role, compatibility, tags, exactly one pinned Concorde preset, and
  exactly one pinned Concorde command extension; Spec Kit records its lifecycle provenance.
- **Concorde Core Preset**: The composable rules and artifact guidance that add architecture context
  and quality gates to existing Spec Kit phases.
- **Concorde Extension**: The registered capability set that exposes the starter Concorde agent
  commands and their lifecycle integration.
- **Architecture Package**: The maintained root module, contracts, feature references, child module
  boundaries, and one-level architecture view for one project.
- **Bounded Context**: A deterministic projection of one current module, its features and I/O,
  immediate children and their I/O, permitted externals, scenarios, and refinement links.
- **Validation Finding**: A deterministic rule result containing severity, affected source, and
  remediation.
- **Installation Record**: Provenance describing installed component identities, versions, ownership,
  source, active state, and lifecycle outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer starting from a clean supported environment can preview, install, discover
  the commands, initialize a root architecture, and run its first validation in under 10 minutes by
  following only the quick start.
- **SC-002**: Across all acceptance fixtures, 100% of successful installations apply exactly the
  expanded component set shown by the native bundle information command.
- **SC-003**: Repeating installation three times produces zero duplicate registrations and zero changes
  to user-authored files after the first successful run.
- **SC-004**: 100% of seeded invalid architecture fixtures are detected with the expected rule,
  affected source, and actionable remediation, with zero silent source modifications.
- **SC-005**: For every context fixture, 100% of returned entities belong to the requested current
  level, its immediate children, or permitted external actors; no child feature or grandchild is
  expanded.
- **SC-006**: The three starter commands are discoverable and successfully complete their primary
  scenarios in Codex skills mode and at least one slash-command integration.
- **SC-007**: Update and removal acceptance tests preserve 100% of project-authored architecture
  sources and shared components.
- **SC-008**: Three repeated validations of unchanged sources produce byte-equivalent structured
  findings and the same pass/fail outcome.
- **SC-009**: At least 90% of first-time pilot maintainers complete the primary install-and-validate
  journey without assistance beyond the bundled quick start.
- **SC-010**: A feature specification created after installation records all required Concorde
  architecture references in its single canonical Spec Kit artifact, with no duplicate feature spec.

## Assumptions

- The native Spec Kit bundle is Concorde's primary distribution and installation unit; its manifest is
  modeled on the repository's official bundle examples and composes independently versioned preset and
  extension components without adding runtime behavior of its own.
- Spec Kit `0.16.4`, already recorded in this project, is the first supported version; expanding the
  range is a later evidence-based decision.
- The bundle is integration-agnostic and inherits the target project's active agent integration.
- Codex is the first skills-mode acceptance target because this repository currently uses the Codex
  integration; one slash-command integration supplies the portability check.
- Project-authored architecture sources are user data and remain after component removal.
- The preset composes only the artifact guidance required for this vertical slice and remains stackable
  with unrelated presets.
- Dedicated Concorde workflows and reusable steps are deferred until the preset and command extension
  have passed the starter bundle's installation and usage acceptance tests.
- In this specification, "starter workflow" describes the user journey enabled by the bundle; it does
  not mean that the bundle contains a Spec Kit workflow component.
- The three starter commands may coordinate deterministic project-scoped operations, but architectural
  changes remain reviewable proposals until the maintainer approves them.
- Publishing and visual rendering are architecturally represented but intentionally deferred so the
  first slice can prove installation, authoring context, and validation end to end.

## Dependencies

- A supported Spec Kit distribution with bundle, preset, extension, template-resolution, provenance,
  and active-integration command registration capabilities.
- A supported coding-agent integration capable of exposing installed extension commands.
- The Concorde constitution and root architecture package as the governing source for this feature.
- Access to a trusted local development source or explicitly approved install source for the starter
  bundle components during acceptance testing.
