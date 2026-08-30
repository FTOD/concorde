---
id: feature.concorde.self-host-framework
kind: feature
module: module.concorde
refines: []
scenarios: []
contracts:
  provided:
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
diagrams:
  - source: specs/concorde/features/004-self-host-concorde/diagrams/concorde-self-hosting-components.json
    role: core
    kind: architecture
    scenarios:
      - self-install-current-concorde
      - refresh-self-hosted-concorde
      - verify-self-hosting-freshness
    output: generated/architecture/concorde-self-hosting-components.html
evidence_status: unknown
canonical_design: specs/concorde/features/004-self-host-concorde/design.md
---

# Feature Design: Self-Host the Concorde Framework

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-25

**Revised**: 2026-08-30

**Status**: Draft

**Input**: User description: "Install the Concorde framework into the Concorde project itself so
that every improvement to the framework or workflow is used while developing Concorde."

**Revision Input**: "Support self-hosting through both the Codex and Claude skills integrations."

## Self-Hosting Boundary

Concorde is both a distributable framework and the project used to develop that framework. This
feature makes that relationship explicit: a maintainer can install the current trusted framework
sources into this same checkout, use the resulting commands and guidance for subsequent Concorde
development, refresh them after a framework change, and verify that the active project installation
has not drifted from its authoritative sources.

Feature 003 remains responsible for building and installing released Concorde packages into other
projects. This feature does not weaken that checkout-isolated release proof. It adds a development
self-hosting mode whose authority flows in the opposite direction: the current checkout's maintained
preset, extension, and bundle sources are the expected framework state, while project-local command,
skill, template, and runtime copies are replaceable materializations used by this checkout.

Protocol v1 supports the Codex and Claude skills integrations under the same supported Spec Kit
compatibility line. The active integration determines which registry entries and agent surfaces are
owned, reviewed, refreshed, and verified; materializations belonging only to an inactive integration
remain unrelated agent assets and are preserved.

Self-hosting is an explicit synchronization lifecycle, not an assumption that every open coding-agent
session hot-reloads changed instructions. If the active integration requires a new session or an
explicit reload before refreshed surfaces become effective, the self-hosting result must say so and
must not claim that the current session is already using them.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: `diagrams/concorde-self-hosting-components.json` is the `role: core` Archify
  architecture view. It answers: which components turn the checkout's authoritative Concorde
  framework sources into the active framework used by this same project, and how is drift detected?
- **Components and crossings**: The view shows the maintainer, authoritative framework sources,
  Feature 004, the required Spec Kit component lifecycle, active project materialization, the coding
  agent, preserved Concorde project sources, and the self-hosting drift gate. The installation
  boundary is governed by `contract.concorde.spec-kit-installation` and the required host behavior by
  `contract.concorde.spec-kit-platform`. Codex and Claude are alternative presentations of the
  existing active-project-materialization role, so supporting both does not add a component or
  boundary crossing to the core view.
- **Supplemental decisions**: No dynamic diagram is needed yet. Installation order, refresh, and
  freshness outcomes are fully described by the scenarios below; a workflow or lifecycle view may
  be added later if state or recovery behavior becomes difficult to understand from the text.
- **Generated view**: `generated/architecture/concorde-self-hosting-components.html`.

The compact Archify 2.16 layout preserves those eight component roles and crossings while keeping
all node context readable at the required desktop viewport.

The diagram supplements this specification. It does not replace the root one-level architecture in
`specs/concorde/architecture/diagrams/level-view.json` or redefine the owning modules and their contracts.

The three journeys below are prose-only at the root level. The root architecture already uses
Archify's maximum five guided scenario views for Features 001–003; adding more would invalidate that
canonical view. Feature 004's own core diagram supplies focused install, development, and freshness
views without displacing or conflating the existing root scenarios. Planning must treat scalable
root scenario representation as an architectural constraint rather than silently dropping this
rationale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install the Current Framework into Concorde (Priority: P1)

As a Concorde maintainer, I can inspect and approve installation of the current trusted framework
sources into this checkout so that Concorde development uses the same workflow the project provides
to its users.

**Why this priority**: Without a reproducible bootstrap from the current sources, repository-local
skills and commands can silently become hand-maintained copies rather than evidence of self-use.

**Independent Test**: Starting from a clean supported Concorde checkout with Spec Kit available but
without an active Concorde installation, inspect and approve self-hosting, then verify that the
declared framework surfaces are available to this project and their provenance identifies the
current local source state.

**Acceptance Scenarios**:

1. **Given** a trusted Concorde checkout without an active self-hosted installation, **When** the
   maintainer requests setup, **Then** the proposed change identifies the local framework source set,
   compatibility, affected project materializations, preserved project content, and activation
   boundary before requesting approval.
2. **Given** an approved compatible proposal, **When** self-hosting completes, **Then** this checkout
   has one active Concorde preset and extension composition equivalent to the accepted local sources,
   with provenance sufficient to reproduce and verify that state.
3. **Given** Concorde is not already installed, **When** bootstrap begins, **Then** setup remains
   possible without invoking a Concorde command that can exist only after setup.
4. **Given** the integration cannot make refreshed instructions effective in the current agent
   session, **When** installation succeeds, **Then** the result clearly requires the necessary reload
   or new session and distinguishes materialized state from active-session state.
5. **Given** either Codex or Claude is the active supported integration, **When** an approved
   self-installation completes, **Then** its declared registry and agent surfaces are verified using
   that integration's materialization model before success is recorded.

---

### User Story 2 - Refresh After a Framework Improvement (Priority: P1)

As a Concorde contributor, I can refresh the self-hosted installation after changing the framework
or workflow so that the next development activity uses the improved behavior rather than a stale
copy.

**Why this priority**: Continuous self-application is the purpose of the feature. Initial setup
without a reliable refresh path would prove only one historical snapshot.

**Independent Test**: Add a harmless observable change to one declared framework surface, preview
and approve refresh, satisfy any reported activation step, and verify that the next new agent
interaction observes the change while unrelated project content remains byte-for-byte unchanged.

**Acceptance Scenarios**:

1. **Given** an active self-hosted installation and changed authoritative framework sources, **When**
   refresh is inspected, **Then** the maintainer sees the source-state change and the exact
   materialized surfaces that would be replaced before approval.
2. **Given** an approved refresh, **When** activation completes, **Then** subsequent Concorde
   development uses the refreshed surfaces and records the new source identity.
3. **Given** no authoritative framework source has changed, **When** refresh is repeated, **Then** it
   reports an unchanged state without duplicating registrations or rewriting unrelated files.
4. **Given** an improvement changes package identity, compatibility, or command ownership, **When**
   refresh is attempted, **Then** the change receives the same explicit compatibility and collision
   review as initial self-installation.

---

### User Story 3 - Verify That Self-Hosting Is Current (Priority: P1)

As a maintainer or reviewer, I can deterministically compare the authoritative framework sources with
the active project installation so that the project never claims to be dogfooding changes it has not
actually activated.

**Why this priority**: Self-hosting is trustworthy only when freshness is observable independently
of the files merely being present.

**Independent Test**: Verify one matching installation, alter one active materialization, alter one
authoritative source without refreshing, and remove one expected surface; confirm that each mismatch
is reported deterministically and prevents a current self-hosting claim.

**Acceptance Scenarios**:

1. **Given** a matching self-hosted installation, **When** freshness is verified, **Then** the result
   identifies the source state, active materialization state, integration, compatibility, activation
   status, and a successful no-drift outcome.
2. **Given** a changed source, stale installed copy, missing surface, unexpected owned surface,
   altered active copy, or incompatible host, **When** freshness is verified, **Then** the result names
   each disagreement and the required refresh or remediation without modifying the project.
3. **Given** evidence cannot establish whether the current agent session loaded the latest
   materialization, **When** status is requested, **Then** session activation is reported as unknown
   or reload-required rather than inferred from file equality.
4. **Given** framework sources and project-local materializations disagree, **When** project quality
   gates run, **Then** the milestone cannot claim complete self-application until the disagreement is
   resolved or explicitly documented as a bounded bootstrap gap.

---

### User Story 4 - Preserve Project Work and Recover Safely (Priority: P2)

As a contributor, I can self-install or refresh Concorde without losing project-authored
specifications, designs, diagrams, documentation, code, tests, configuration, or unrelated agent
assets so that self-hosting does not endanger the project it is meant to improve.

**Why this priority**: The target and the product share one checkout, making precise ownership and
failure recovery essential.

**Independent Test**: Seed each preserved content class plus an unrelated agent asset, attempt one
successful refresh and representative failing refreshes, and verify exact preservation, accurate
ownership, recovery of the prior active framework, and actionable residual-state reporting.

**Acceptance Scenarios**:

1. **Given** project-authored content and unrelated integration assets, **When** setup or refresh
   succeeds, **Then** only Concorde-owned materializations named in the approved proposal change.
2. **Given** a failure before activation, **When** recovery completes, **Then** the prior active
   framework remains usable and success is not recorded.
3. **Given** recovery cannot restore every prior artifact, **When** the operation ends, **Then** it
   reports the exact residual state and a safe remediation path.
4. **Given** locally edited materialized files, **When** refresh is proposed, **Then** they are
   reported as drift and are never promoted automatically into authoritative framework sources.

### Edge Cases

- The checkout has no prior self-hosting receipt but contains hand-created files at expected
  materialization paths.
- A framework source changes while a refresh proposal is awaiting approval.
- The active coding agent caches a skill that has already been refreshed on disk.
- The bundle recipe and its referenced preset or extension identify incompatible local versions.
- A source file is untracked, ignored, unreadable, or outside the trusted checkout boundary.
- The selected feature has temporal work in progress while framework commands are refreshed.
- Another preset or extension owns a colliding command surface.
- Codex and Claude are both installed, but only one is active when self-hosting is proposed.
- The active integration represents some development-mode skill surfaces as safe links into an
  installed component rather than as regular copied files.
- Self-hosting is invoked from a worktree, detached revision, or checkout with unrelated changes.
- Verification can compare files but cannot prove which instruction version the running agent loaded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Concorde MUST provide a supported self-hosting lifecycle that installs the current
  trusted Concorde framework sources into the Concorde project checkout itself.
- **FR-002**: Self-hosting MUST distinguish authoritative framework sources from project-local
  materializations, and MUST NOT treat an installed skill, command, template, runtime copy, catalog,
  generated diagram, or generated page as framework source authority.
- **FR-003**: The authoritative self-hosting source set MUST include the same preset, extension, and
  bundle responsibilities that form the distributed Concorde framework.
- **FR-004**: Initial bootstrap MUST work without depending on a Concorde command that is available
  only after successful self-installation.
- **FR-005**: Before initial setup or refresh mutates project state, Concorde MUST present the source
  identity, compatibility, planned owned changes, preserved content classes, and required activation
  step for explicit maintainer approval.
- **FR-006**: Self-hosting MUST use the supported Spec Kit component and active-integration lifecycle
  rather than create a second command registry or parallel feature workflow.
- **FR-007**: A successful self-installation MUST materialize all and only the command, skill,
  template, adapter, runtime, and registration surfaces declared by the accepted local framework
  composition.
- **FR-008**: A successful self-installation or refresh MUST record verifiable provenance that binds
  the active materialization to the accepted authoritative source state and host compatibility.
- **FR-009**: A contributor MUST be able to preview and refresh the active self-hosted installation
  after any authoritative framework source changes.
- **FR-010**: Repeating setup or refresh against unchanged sources MUST be idempotent and MUST NOT
  duplicate component ownership, registrations, commands, skills, or templates.
- **FR-011**: Concorde MUST provide a read-only freshness check that compares the complete declared
  self-hosting source set and expected materializations with the active project installation.
- **FR-012**: Freshness results MUST distinguish source identity, on-disk materialization, component
  registration, host compatibility, and current-session activation rather than collapse them into one
  unqualified success state.
- **FR-013**: Missing, stale, altered, extra owned, incompatible, or unverifiable self-hosting state
  MUST produce deterministic, actionable disagreement or unknown findings and MUST prevent a current
  self-application claim.
- **FR-014**: An accepted framework change MUST be refreshed and activated before the project can
  count that change as used in Concorde's own subsequent development evidence.
- **FR-015**: When the coding-agent integration does not hot-reload changed instructions, Concorde
  MUST identify the required reload or new-session boundary and MUST NOT claim the running session
  uses the refreshed version without evidence.
- **FR-016**: Setup, refresh, and recovery MUST preserve project-authored specifications, designs,
  contracts, diagrams, documentation, code, tests, project configuration, generated evidence, and
  unrelated integration assets unless an exact item is separately included in the approved change.
- **FR-017**: Locally edited materializations MUST be reported as drift and MUST NOT be copied back
  into authoritative framework sources automatically.
- **FR-018**: Setup and refresh MUST either activate the complete approved materialization or retain
  the prior usable state; partial residual state MUST be reported exactly and never recorded as
  success.
- **FR-019**: Self-hosting status MUST remain inspectable when no feature workspace is selected and
  MUST NOT change feature selection or an active temporal implementation attempt.
- **FR-020**: The self-hosted workflow MUST remain behaviorally equivalent to installation of the
  same accepted component contents through Feature 003, except for explicitly documented local-source
  provenance and activation differences.
- **FR-021**: Concorde's project quality gates MUST detect unresolved self-hosting drift whenever a
  framework or workflow improvement claims self-application evidence.
- **FR-022**: Self-hosting diagnostics MUST identify the affected authority, expected state, observed
  state, lifecycle stage, and safe remediation without exposing unrelated file contents.
- **FR-023**: Protocol v1 self-hosting MUST support both the Codex and Claude skills integrations on
  the supported Spec Kit compatibility line; proposal, collision detection, ownership, verification,
  drift reporting, rollback, and receipt evidence MUST follow the active integration's declared
  registry and surface model while preserving inactive-integration assets.

### Key Entities

- **Authoritative Framework Source Set**: The trusted preset, extension, bundle, and declared package
  inputs whose accepted state should be used by this checkout.
- **Self-Hosting Proposal**: A reviewable statement of source identity, compatibility, owned changes,
  preserved content, activation boundary, and expected resulting state; it grants no mutation
  authority until explicitly approved.
- **Active Project Materialization**: Replaceable Concorde-owned skills, commands, templates,
  adapters, runtime files, and registrations made available through the project's active integration.
- **Self-Hosting Receipt**: Provenance connecting one accepted source state to its completed
  materialization, compatibility, ownership, and activation result.
- **Freshness Result**: A read-only comparison that classifies matching, disagreement, missing, and
  unknown evidence across source, materialization, registration, compatibility, and session state.
- **Activation Boundary**: The point at which a refreshed materialization becomes observable to new
  development work, including any required agent reload or new session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can move from a clean supported Concorde checkout to a verified
  self-hosted installation in under five minutes, excluding dependency download time.
- **SC-002**: In all acceptance fixtures, 100% of surfaces declared by the accepted local framework
  composition are present with matching provenance and no undeclared Concorde-owned surface remains.
- **SC-003**: Freshness checks detect 100% of seeded changed-source, stale-copy, altered-copy,
  missing-surface, extra-owned-surface, incompatible-host, and unverifiable-session cases.
- **SC-004**: Repeating setup or refresh against unchanged sources produces zero material changes and
  zero duplicate ownership or registration records.
- **SC-005**: Successful and failed self-hosting fixtures preserve 100% of seeded project-authored
  content and unrelated integration assets byte-for-byte.
- **SC-006**: After an observable framework change is refreshed and its activation requirement is
  satisfied, 100% of new test interactions use the changed behavior without reading an obsolete
  checkout-local copy.
- **SC-007**: No failed, partial, stale, or unverifiable fixture reports both current and successfully
  activated self-hosting.
- **SC-008**: In a maintainer review, the authoritative framework source, active materialization,
  provenance, drift status, and any required activation step can each be identified within three
  minutes from the self-hosting result and documentation.
- **SC-009**: The complete proposal, apply, unchanged refresh, drift, rollback, and preservation
  acceptance matrix passes for both Codex and Claude, including each integration's declared surface
  representation.

## Scope

### In Scope

- Bootstrap of the current trusted Concorde sources into this same project checkout.
- Review, approval, provenance, refresh, drift detection, activation reporting, and recovery.
- Preservation of project-authored content and unrelated integration assets.
- Equivalence checks between local self-hosting and the distributable framework composition.
- Self-application evidence in Concorde's own development quality gates.

### Out of Scope

- Replacing Feature 003's released installation, catalog, update, or removal lifecycle for user
  projects.
- Automatically mutating the installation on every source-file save.
- Guaranteeing that an already running third-party coding agent hot-reloads changed instructions.
- Promoting edits from installed materializations back into authoritative framework sources.
- Treating self-hosting as proof that released archives work without checkout-isolated Feature 003
  acceptance evidence.

## Assumptions

- The checkout is trusted by the maintainer and uses the explicitly supported Spec Kit version.
- Spec Kit 0.16.4's Codex and Claude skills integrations are the supported protocol v1 targets;
  other integrations and later Spec Kit versions remain unsupported until equivalent evidence exists.
- An explicit preview-and-refresh action is acceptable; continuous file-watcher mutation is not
  required.
- The active coding-agent integration can identify whether it supports immediate instruction reload
  or requires a new session.
- Local self-hosting does not require publishing or downloading a release, but it must preserve the
  same component responsibilities and observable workflow as the corresponding distribution.
- Existing project-local skills and `.specify/` artifacts may be stale or hand-maintained and are not
  assumed correct merely because they exist.
- Feature 001 remains authoritative for workflow behavior, while Feature 003 remains authoritative
  for released installation behavior.

## Dependencies

- `feature.concorde.workflow` for the workflow semantics exercised after activation.
- `feature.concorde.install-with-spec-kit` for the accepted component composition and user-project
  installation boundary against which self-hosting equivalence is measured.
- `contract.concorde.spec-kit-installation` and `contract.concorde.spec-kit-platform` for component
  lifecycle, integration materialization, provenance, ownership, and compatibility behavior.
- The selected coding-agent integration's documented activation and reload behavior.
