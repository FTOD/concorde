---
id: feature.concorde.install-with-spec-kit
kind: feature
module: module.concorde
refines: []
subfeatures:
  - feature.concorde.install-with-spec-kit.publish-release
  - feature.concorde.install-with-spec-kit.one-command-install
scenarios:
  - installation
contracts:
  provided:
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
diagrams:
  - source: specs/concorde/features/003-installation/diagrams/spec-kit-component-model.json
    role: core
    kind: architecture
    scenarios:
      - inspect-install-and-verify-concorde
    output: generated/architecture/concorde-spec-kit-component-model.html
  - source: specs/concorde/features/003-installation/diagrams/bundle-installation-flow.json
    role: supplemental
    kind: workflow
    scenarios:
      - inspect-install-and-verify-concorde
      - manage-concorde-installation
    output: generated/architecture/concorde-bundle-installation-flow.html
evidence_status: partial
canonical_design: specs/concorde/features/003-installation/design.md
---

# Feature Design: Install and Set Up Concorde with Spec Kit

**Read first**: [abstract.md](abstract.md) — the self-contained abstract of this feature. **Accepted
realization**: [implementation.md](implementation.md) — consulted when writing the code or fixing a bug.

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-22

**Revised**: 2026-08-30 — install native reflection-triage agents after the bundle lifecycle

**Status**: Native Spec Kit installation implemented and verified; decomposed into two immediate
sub-features (published release, one-command installation) whose evidence is pending; reconciled on
2026-08-28 with Feature 001's three-tier feature document model (`abstract.md`, `design.md`, `implementation.md`),
whose abstract template and verification changes are not yet realized

**Input**: User description: "Install and set up Concorde through Spec Kit, and ensure the released
bundle correctly overrides the normal commands and skills so a user's clean project receives the
same Concorde workflow rather than only this repository's local modifications, including temporal
`attempt/checklists/` placement with no feature-root compatibility directory."

**Revision input**: User description: "Simplify Concorde installation for feature 003: publish a
real GitHub release with catalogs and archives, and provide a single-command installer script that
sequences the native Spec Kit lifecycle (init, catalog registration, bundle install) idempotently,
with a development mode for local checkouts. Create sub-features under feature 003 as appropriate."

**Revision input**: User description: "Use `concorde` as the preset identity everywhere in the
project, remove the former suffixed preset identity completely, and describe the existing Spec Kit
commands as modified by Concorde rather than replaced by it. The suffix has no intended semantic
distinction."

**Revision input**: User description: "Make Feature 005's reflection subagents part of Concorde
installation, including native Claude and Codex roles, and implement every required installation,
upgrade, removal, release, and self-hosting change."

## How Concorde Is Delivered through Spec Kit

Spec Kit is the host platform. It resolves packages, records provenance, installs commands through
the active coding-agent integration, and continues to own the normal feature lifecycle. Concorde is
delivered as independently versioned ecosystem parts with different responsibilities:

| Concept | Responsibility in setup | Explicit boundary |
|---|---|---|
| **Catalog** | Advertises package identity, version, compatibility, download location, integrity, and trust metadata. | It is discovery metadata, not installed product behavior. |
| **Bundle** | Provides an inspectable recipe that pins the compatible Concorde preset and extension versions. | It is not executable behavior, a template layer, or a second workflow. |
| **Preset** | Composes Concorde guidance into normal templates and authoritative routing into the existing Spec Kit lifecycle commands. | It introduces no new runtime command namespace and creates no second canonical feature specification. It does not register commands by itself; Spec Kit materializes its resolved command layers. |
| **Extension** | Provides five Concorde-specific command definitions, the selected-workspace adapter and deterministic runtime, and Feature 005's canonical reflection-triage bodies, platform wrappers, queue helper, and projection operation. | It does not own normal Spec Kit phases, user permission policy, mutable triage state, or installer lifecycle decisions. |
| **Coding-agent integration** | Materializes resolved command sources, and selects the platform-specific reflection-triage projection that Concorde reconciles after bundle installation. | It adapts presentation without changing command, role, queue, plan, or permission semantics. |
| **Skills** | Are the installed user-facing instructions materialized from preset and extension command sources. | They guide the agent but do not own deterministic operation semantics. |
| **Scripts** | Perform workspace routing and deterministic initialization, context, validation, and acceptance after setup. | Their behavior belongs to the Concorde workflow, not to installation. |
| **Workspace Files** | Preserve durable specifications and accepted realization outside `attempt/` and temporal delivery memory inside it. | They are project-owned workflow state, never package content. |

The `concorde-bundle` bundle pins exactly the tested `concorde` preset and `concorde` extension.
Their shared name is unambiguous because Spec Kit identifies components by type and ID: the preset
is `preset:concorde`, while the extension is `extension:concorde`. Spec Kit expands the recipe before
installation, installs each part through its native component lifecycle, resolves the preset command
stack, materializes the result for the active coding-agent integration, and records ownership for
later update or removal. Release building writes the future catalog/archive location into metadata;
it does not contact that URL during the build.

The normal Spec Kit command names remain the user-facing lifecycle. Concorde modifies their installed
agent instructions through its preset, which must provide the complete routing layer for `specify`,
`clarify`, `checklist`, `plan`, `tasks`, `implement`,
`analyze`, `converge`, and `taskstoissues`. Once installed, each resolved command must select the
nested feature workspace before any phase-specific file is read or written. Durable intent
(`abstract.md` and `design.md`) and the accepted design reference (`implementation.md`) stay at the feature root,
while requirements-quality checklists, planning, and delivery artifacts stay under
`attempt/`. The preset also supplies the feature abstract template and the permanent `implementation.md`
template. The extension supplies `speckit.concorde.impl.accept`, which proposes and, only after
explicit approval, atomically promotes a completed attempt into that design reference and removes
`attempt/`.
Repository-local `.agents/`, `.codex/`, and `.claude/` files are self-hosting or migration evidence
only. A released installation must obtain canonical agent assets from the installed extension,
materialize its active integration's native triage skill and two roles, and work when the checkout is
unavailable. Because Spec Kit 0.16.4 has no arbitrary custom-agent projection primitive, the
Concorde installer owns one bounded post-bundle projection stage backed by an installed deterministic
operation and a digest receipt; it does not bypass or replace the bundle lifecycle.

Two supplemental, text-backed views explain this boundary:

- `diagrams/spec-kit-component-model.json` and its generated component view show the package roles,
  command-modification boundary, active integration, and clean installed project.
- `diagrams/bundle-installation-flow.json` and its generated workflow view show release, discovery,
  preview, installation, command materialization, clean-project verification, update, and removal.

The component model supports User Stories 1 and 3 by distinguishing discovery, template guidance,
normal-command modification, Concorde-specific commands, canonical agent assets, project-native
agent presentation, and runtime ownership. The installation flow supports all four stories by
showing preview and approval before installation, then component materialization, owned agent
projection, and an actual clean-project lifecycle before setup is accepted. Together they
demonstrate the encouraged Concorde pattern: use feature-owned diagrams when component roles or
invocation order would be harder to understand from prose alone.

These diagrams explain this feature and do not supersede the canonical project interaction view in
`specs/concorde/architecture/diagrams/level-view.json`.
Their concise node context is the Archify 2.16 presentation of the same package roles and lifecycle;
the textual requirements and contracts retain the complete semantics.

## Decomposition

The component step-by-step path is complete and verified, but Spec Kit 0.16.4 cannot project
arbitrary native custom-agent files. The full documented manual path is therefore bundle install
followed by the installed `agent-assets` operation. It still asks every consumer to be a release
builder: no release has been published, so setup also requires the Concorde checkout, a local build,
a local catalog server, and three catalog registrations. Two immediate sub-features remove that
burden without changing package or projection authority:

| Order | Sub-feature | Owned outcome |
|---:|---|---|
| 1 | `feature.concorde.install-with-spec-kit.publish-release` | A marked version is built, verified, and published to a stable public location that Spec Kit catalogs can read, with a current-release pointer. |
| 2 | `feature.concorde.install-with-spec-kit.one-command-install` | One command sequences project initialization, catalog registration, bundle installation, and the installed agent projector idempotently against a published release or local checkout. |

The parent keeps the package model, Spec Kit's lifecycle authority, the inspect-before-install rule,
the clean-project verification matrix, and update/removal behavior. The children inherit
`module.concorde`, cannot own children, and reference these aggregate facts rather than restating
them. The one-command installer is an accelerator over public Spec Kit operations plus the installed
extension's projector. The manual bundle-plus-projector path remains sufficient, and no installer
may bypass the bundle recipe or render from checkout-local assets.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Concorde Before Installation (Priority: P1)

As a maintainer, I can understand Concorde's package roles and inspect the exact expanded installation
plan before approving setup so that I know what will be added to the project and which system owns
each behavior.

**Why this priority**: A trusted installation starts with a comprehensible, reviewable plan rather
than opaque component copying.

**Independent Test**: Starting with a supported Spec Kit project and an approved Concorde source,
inspect the Concorde bundle and verify that the plan names the bundle, preset, extension, versions,
compatibility range, composition strategy, integration inheritance, trust source, and intended
project-facing changes.

**Acceptance Scenarios**:

1. **Given** the Concorde release source, **When** the maintainer validates and builds it, **Then** the
   result contains independently identifiable bundle, preset, and extension packages plus catalog
   entries with integrity metadata.
2. **Given** a supported project, **When** the maintainer previews `concorde-bundle`, **Then** the
   expanded plan identifies exactly one `concorde` preset and one `concorde` extension, qualified by
   component type, with their pinned versions, compatibility, provenance, and effects.
3. **Given** the textual explanation and diagrams, **When** a first-time maintainer reviews setup,
   **Then** they can distinguish catalog discovery, bundle composition, preset guidance, extension
   behavior, active-agent presentation, and Scripts.

---

### User Story 2 - Install Concorde into a New or Existing Project (Priority: P1)

As a maintainer, I can install Concorde through its Spec Kit bundle lifecycle plus one bounded,
previewed Concorde agent-projection stage into a new or existing supported project, so that the
architecture-aware guidance, commands, and native reflection-triage subagents become available
without copying repository-local files.

**Why this priority**: Installation is the sole outcome of this feature and the prerequisite for
using the separately specified Concorde workflow.

**Independent Test**: Approve the expanded component and agent plan, install into clean Claude and
Codex projects plus a supported existing project, then verify that the installed preset, extension,
command presentation, native triage skill/roles, shared default config, and projection receipt match
the accepted plan while project-owned state is preserved.

**Acceptance Scenarios**:

1. **Given** an accepted expanded plan, **When** the maintainer installs by approved catalog ID,
   directory, manifest, or built artifact, **Then** Spec Kit installs the same pinned component set
   and records its provenance.
2. **Given** an uninitialized directory, **When** the supported initialization-and-install path is
   used, **Then** the directory becomes a supported project with the same Concorde setup as an
   existing project.
3. **Given** the same installed release, **When** installation is repeated, **Then** it succeeds
   without duplicate component state, projection churn, or changes to project-authored
   specifications, triage config, plans, reflection log, or unrelated agent files.
4. **Given** an unsupported Spec Kit version, untrusted source, incompatible component, or command
   collision, **When** installation is attempted, **Then** setup stops before claiming success and
   names the incompatibility and remediation.
5. **Given** legacy or modified native reflection-agent files, **When** projection is previewed,
   **Then** setup reports create/adopt/update/remove/preserve/conflict actions and makes no change
   until every conflict is resolved or explicitly adopted.

---

### User Story 3 - Verify the Installed Workflow, Not Just Files (Priority: P1)

As a maintainer, I can verify that the release installed the same Concorde workflow used to develop
Concorde itself, so I can begin work without copying or editing command skills by hand.

**Why this priority**: Registered files or matching snippets are not evidence that the resulting
commands execute the correct phase in the correct nested workspace.

**Independent Test**: Build the release, install it into pristine Claude and Codex projects that
cannot read the Concorde source checkout, and execute the normal lifecycle through both presentation
styles. Verify every durable and temporal output path, all five Concorde-specific commands, both
native reflection-agent projections with shared semantics/state, and restoration after update or
removal.

**Acceptance Scenarios**:

1. **Given** a pristine supported Spec Kit project, **When** the released bundle is installed,
   **Then** the active integration contains resolved Concorde-aware forms of all nine normal lifecycle
   commands, the additive fast-loop surface, all five Concorde-specific commands, and the native
   reflection-triage skill plus investigator and implementer roles selected by the installed assets.
2. **Given** a selected nested feature, **When** `specify`, `clarify`, or `checklist` runs, **Then**
   the canonical `design.md` and contracts remain at the feature root, every generated checklist is
   placed under `attempt/checklists/`, and no duplicate specification or root checklist is
   created.
3. **Given** the same selected feature, **When** `plan`, `tasks`, `implement`, `analyze`, `converge`,
   or `taskstoissues` runs, **Then** it uses that feature's single active `attempt/` workspace
   and creates no root-level compatibility copy of temporal artifacts.
4. **Given** a newly created feature, **When** its installed workspace is inspected, **Then** it has
   permanent root `abstract.md`, `design.md`, and `implementation.md` artifacts plus, while specification review or
   delivery is active, one temporal `attempt/` directory containing its checklists and other attempt
   artifacts.
5. **Given** a path-sensitive normal command, **When** its installed presentation is executed,
   **Then** nested-workspace resolution occurs before any lower command layer or helper can select a
   legacy root-level plan or task path.
6. **Given** one skills-based and one slash-command-based integration, **When** equivalent lifecycle
   and Concorde commands run, **Then** they produce equivalent selected-workspace, phase-path, result,
   and failure behavior.
7. **Given** a completed implementation attempt, **When** the installed acceptance command is proposed
   and explicitly approved, **Then** the reviewed design replaces root `implementation.md` and the exact
   `attempt/` directory, including its resolved checklists, is removed; incomplete tasks,
   unresolved checklist items, or stale proposals make no change.
8. **Given** the Concorde source checkout is unavailable, **When** clean-project verification runs,
   **Then** every command and custom-agent projection resolves only files installed from the released
   preset and extension archives.
9. **Given** the preset is disabled or reprioritized, **When** Spec Kit updates its preset registry,
   **Then** existing materialized commands remain active as defined by Spec Kit 0.16.4 while future
   template resolution reflects the new state or priority.
10. **Given** Concorde is updated or removed, **When** Spec Kit rematerializes registered commands,
   **Then** it installs the accepted updated layer or restores the next surviving lower-priority
   command layer, and Concorde updates or removes only digest-matching projection files without
   leaving stale owned roles.
11. **Given** verified setup, **When** the maintainer starts Feature 001's Concorde workflow, **Then** no
   manual skill/agent edit, duplicate feature store, or second component lifecycle is required.

---

### User Story 4 - Update or Remove Concorde Safely (Priority: P3)

As a maintainer, I can preview and apply compatible updates or remove Concorde-owned components while
preserving project-authored sources and components shared with other installations.

**Why this priority**: Safe maintenance and exit paths are part of a trustworthy setup lifecycle.

**Independent Test**: Install the Concorde bundle, author project architecture sources, update to a
compatible release, and remove the bundle; verify accurate component state throughout and unchanged
project-owned sources.

**Acceptance Scenarios**:

1. **Given** an installed older release, **When** the maintainer previews and accepts an update,
   **Then** only the approved component versions and matching owned projections change while project
   configuration, shared triage state, inactive integration surfaces, and sources remain unchanged.
2. **Given** installed Concorde components, **When** the bundle is removed, **Then** only components
   and agent projections owned solely by that installation are removed while shared dependencies,
   modified projections, unrelated agent files, and project-authored `.concorde/` and `specs/`
   sources remain.
3. **Given** an installation or update failure, **When** recovery completes, **Then** success is not
   recorded and any residual partial state is reported explicitly.

### Edge Cases

- A catalog entry is valid during preview but its archive becomes unavailable before installation.
- The target project has stacked presets, local template overrides, or an existing component with the
  same stable identity.
- The preset and extension share the `concorde` ID but occupy distinct Spec Kit component namespaces.
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
- A generated reflection role was edited after installation and its digest no longer matches the
  projection receipt.
- A manual pre-install Claude workflow uses the same target paths but has no Concorde ownership
  receipt.
- Claude and Codex projections are both present and refreshing the active integration must preserve
  the inactive one.
- Bundle installation succeeds but agent projection conflicts or fails before terminal success.
- A component is shared with another bundle or installed independently.
- Project-owned `.concorde/` or `specs/` sources are malformed; installation must not treat them as
  component-owned files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Concorde MUST provide one native, schema-versioned Spec Kit bundle as the primary
  component installation unit. A complete setup MAY require the Concorde installer only for the
  bounded agent-projection lifecycle that Spec Kit 0.16.4 cannot express; that stage MUST consume
  the already installed extension and MUST NOT replace or bypass the bundle.
- **FR-002**: The Concorde bundle MUST be a non-executable recipe that pins exactly one independently
  versioned `concorde` preset and one independently versioned `concorde` extension, distinguished by
  their Spec Kit component types.
- **FR-003**: Before installation or update, maintainers MUST be able to inspect the fully expanded
  component identities, versions, dependencies, compatibility constraints, preset strategy and
  priority, trust sources, integration inheritance, intended component changes, native agent target
  paths, ownership actions, and conflicts.
- **FR-004**: The installed component set, versions, and agent projections MUST match the plan
  accepted by the maintainer.
- **FR-005**: The preset MUST compose Concorde architecture guidance into normal feature, plan, and
  task templates, supply the feature abstract template and the permanent feature `implementation.md`
  template, and avoid creating a second canonical feature specification.
- **FR-006**: The preset MUST provide Concorde-aware instruction layers that modify `specify`, `clarify`,
  `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues`; these are
  existing lifecycle command surfaces, not new Concorde runtime command IDs.
- **FR-007**: Each path-sensitive preset command MUST resolve the selected feature and the correct
  durable or temporal workspace before any inherited instruction or helper can read or write a
  legacy root-level artifact.
- **FR-008**: The extension MUST register five Concorde-specific surfaces through the target
  project's active coding-agent integration: four operations with the portable selected-workspace or
  runtime support they require and one agent-followed, read-only `ask` procedure with no runtime
  verb. It MUST additionally carry Feature 005's canonical triage bodies, wrappers, queue helper,
  default config, and deterministic projection operation as support assets rather than a sixth
  command surface.
- **FR-009**: Setup MUST preserve Spec Kit's authority for its normal lifecycle and MUST NOT install a
  dedicated Concorde workflow component or reusable bundle steps. The post-bundle agent projection
  MUST remain a deterministic Concorde installation operation, not a parallel component lifecycle.
- **FR-010**: Catalogs MUST remain discovery and trust metadata for independent bundle, preset, and
  extension packages and MUST NOT be presented as installed runtime components.
- **FR-011**: Release building MUST treat the supplied base address as metadata for future catalog and
  archive locations and MUST NOT require contacting that address during the build.
- **FR-012**: The initial release MUST state its supported Spec Kit range and reject an unsupported
  version before making installation changes.
- **FR-013**: Installation MUST inherit the target project's active coding-agent integration rather
  than hard-code one agent presentation, and MUST select only that integration's native triage
  projection unless the maintainer explicitly requests another supported projection.
- **FR-014**: Canonical command intent, arguments, results, selected-workspace semantics, phase paths,
  failures, triage actions, route/plan vocabulary, and role write boundaries MUST remain equivalent
  across every supported presentation.
- **FR-015**: Installation MUST support approved local source, manifest, built-artifact, and trusted
  catalog inputs while applying the active source-trust policy.
- **FR-016**: Repeated installation of the same release MUST be idempotent and MUST NOT duplicate
  registry or receipt state, rewrite unchanged projections, or modify project-authored sources and
  shared triage state.
- **FR-017**: Setup verification MUST identify the installed bundle, type-qualified preset and
  extension identities, versions,
  source, active/disabled state, resolved template contributions, resolved command layers, and the
  command artifacts materialized for the active integration, plus every native triage projection,
  its canonical source digest, and its ownership receipt.
- **FR-018**: Setup verification MUST execute every normal command whose artifact path is changed by
  Concorde and MUST prove the durable-root/temporal-`attempt/` path matrix without root-level
  checklist, plan, task, or other temporal compatibility copies or symlinks.
- **FR-019**: Setup verification MUST exercise all four installed runtime-backed Concorde command
  intents and inspect the installed `ask` procedure's grounding, citation, uncertainty, bounded
  context, checkout independence, and non-mutation rules through each supported presentation style
  without making installation responsible for their core workflow semantics. It MUST structurally
  parse and compare Claude/Codex triage skill and role projections without requiring a live model.
- **FR-020**: Clean-project acceptance MUST install from the built bundle and generated catalogs with
  the Concorde checkout unavailable; project-local `.agents/`, `.specify/`, templates, or scripts in
  this repository MUST NOT count as distributed product behavior, and projected agents MUST derive
  only from the extension archive installed in the clean target.
- **FR-021**: Preset disable and priority change MUST preserve already materialized commands according
  to Spec Kit 0.16.4 while changing future resolution; update and removal MUST rematerialize the
  accepted or next surviving command layer without stale Concorde instructions and MUST reconcile
  owned agent projections without deleting inactive integration surfaces.
- **FR-022**: Compatible update MUST preserve project configuration and project-authored
  specifications, `.concorde/reflections/config.json`, reflection plans/worktrees/log, unrelated
  agent files, and modified unowned projections while applying only the maintainer-approved plan.
- **FR-023**: Removal MUST delete only components owned solely by the Concorde bundle and MUST preserve
  shared components and all project-authored `.concorde/` and `specs/` sources. It MAY delete a
  projected agent file only when the projection receipt owns its path and its current digest still
  matches the receipt.
- **FR-024**: Failed installation, command materialization, or update MUST NOT record success and MUST
  report any residual component or agent-projection state that could not be restored automatically.
- **FR-025**: Setup documentation MUST explain Spec Kit, catalog, bundle, preset, extension,
  coding-agent integration, and Scripts responsibilities without treating them as
  interchangeable.
- **FR-026**: This feature MUST provide text-backed component and installation/use-flow diagrams that
  distinguish release sources from installed files, template composition from command composition,
  normal commands modified by Concorde from Concorde-specific commands, component installation from
  native agent projection, and self-hosting files from release inputs.
- **FR-027**: Supplemental setup diagrams MUST remain separate from the root module's level views
  under `architecture/diagrams/`, identify their maintained sources and generated outputs, and pass deterministic
  validation and freshness checks.
- **FR-028**: Setup guidance MUST end by directing the maintainer to Feature 001's core Concorde
  workflow rather than describing installation as the workflow itself.
- **FR-029**: A command-registration check that only finds expected text MUST NOT be accepted as setup
  evidence; verification MUST execute the installed winning command surfaces and compare their
  observable workspace results with the accepted distribution contract.
- **FR-030**: Clean-project verification MUST prove that feature creation provides root `abstract.md`,
  `design.md`, and `implementation.md` and that installed acceptance refuses incomplete or stale attempts and applies only an explicitly
  approved, digest-bound proposal to the selected feature.
- **FR-031**: Installed `specify`, `clarify`, and `checklist` surfaces MUST route every generated
  requirements-quality artifact to the selected feature's `attempt/checklists/` directory;
  they MUST NOT create or preserve a feature-root `checklists/` compatibility location.
- **FR-032**: Each released version MUST be published to a stable public location whose catalogs are
  registrable from a clean project without the Concorde checkout or a local server; the published
  locations MUST equal the locations the catalogs advertise. Detail belongs to
  `feature.concorde.install-with-spec-kit.publish-release`.
- **FR-033**: Any convenience installation surface MUST sequence public Spec Kit operations for
  project/component lifecycle, MUST install through the bundle recipe, and MAY then invoke only the
  installed extension's deterministic agent-projector operation. It MUST converge on the same
  component, registry, command, projection, and receipt state as the documented bundle-plus-projector
  path. Detail belongs to `feature.concorde.install-with-spec-kit.one-command-install`.
- **FR-034**: The preset package ID and maintained source directory MUST be `concorde`; the extension
  MUST retain its `concorde` ID, and every bundle, catalog, registry, diagnostic, test, and guide MUST
  distinguish the two using their component type rather than a suffix on either ID.
- **FR-035**: The completed repository and every self-hosted materialization MUST contain no file,
  directory, manifest value, generated projection, or tracked text using the superseded preset token,
  and MUST install no compatibility alias or duplicate preset identity.
- **FR-036**: User-facing guidance MUST describe the nine existing Spec Kit command surfaces as
  modified by Concorde, not replaced by Concorde. Where the manifest's `replace` composition strategy
  is technically relevant, guidance MAY name that strategy while making clear that the command name,
  lifecycle role, and continued use are preserved.
- **FR-037**: Development self-hosting, release building, clean-project installation, update, and
  removal MUST converge on the type-qualified `preset:concorde`, `extension:concorde`, and
  `bundle:concorde-bundle` identities without a stale preset directory, registry entry, command layer,
  archive, or catalog entry.
- **FR-038**: Release archives and catalogs MUST include every canonical Feature 005 agent asset,
  wrapper, queue helper, and projection runtime file in the extension's allowlisted inventory and
  integrity digest, with capability metadata that exactly matches the manifest.
- **FR-039**: Agent projection preview MUST be read-only and classify every desired, superseded, or
  legacy target as `create`, `unchanged`, `adopt`, `update`, `remove`, `preserve`, or `conflict`,
  including exact target paths and remediation.
- **FR-040**: Projection apply MUST occur only after successful bundle install/update, MUST use the
  installed extension bytes, MUST write a versioned digest receipt, and MUST verify every output
  before terminal installation success is reported.
- **FR-041**: Existing manual agent files MAY be adopted only when they are byte-identical to the
  desired projection or when the maintainer explicitly authorizes a reviewed migration. Otherwise
  setup MUST preserve them and stop with a conflict.
- **FR-042**: Agent projection removal and superseded-path cleanup MUST use the same digest ownership
  rule as update; a missing or modified owned path MUST be preserved/reported and MUST NOT cause
  unrelated owned outputs or shared state to be deleted.
- **FR-043**: Development self-hosting and clean-install acceptance MUST exercise Claude and Codex
  projection cycles, including switching integrations, and prove that inactive surfaces survive,
  customized shared config/plans survive, and no checkout path appears in rendered files.

### Scope

**Included**:

- Package-role education and setup diagrams.
- Release validation/build, catalogs, preview, installation, provenance, verification, update, and
  removal.
- One preset and one extension installed together through one bundle recipe.
- Command discovery and cross-integration equivalence checks for the installed Concorde operations.
- Canonical reflection-triage agent assets in the extension; deterministic preview, projection,
  receipt verification, migration conflict handling, update, and removal for Claude and Codex.
- Authoritative composition of all affected normal Spec Kit commands and clean-project execution of
  their durable/temporal path matrix.
- The preset identity and maintained directory rename, including every release, installation,
  self-hosting, documentation, specification, fixture, and generated projection reference.

**Excluded**:

- Defining the module/feature hierarchy, feature authoring lifecycle, architecture review gates,
  contract rules, or bounded implementation workflow; those belong to Feature 001.
- Publishing the project documentation site; that belongs to Feature 002.
- A second Spec Kit lifecycle, a dedicated workflow component, or reusable bundle steps. The
  `one-command-install` sub-feature may invoke the installed deterministic agent projector after
  public Spec Kit operations; arbitrary copying outside the manifest/receipt contract and bypassing
  the bundle lifecycle remain excluded.
- Treating generated catalogs or release archives as maintained project intent.

### Key Entities

- **Bundle Recipe**: The inspectable installation plan that pins compatible component identities and
  versions but performs no runtime behavior itself.
- **Preset Package**: The `preset:concorde` contribution that supplies architecture-aware templates
  and modifies existing lifecycle command instructions without introducing a new runtime namespace.
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
- **Agent Projection Plan**: The previewed integration, desired native skill/role targets, canonical
  source digest, action classification, conflicts, and remediation applied after component install.
- **Agent Projection Receipt**: Installer-owned path/digest records proving which generated native
  files Concorde may later update or remove; it never owns shared config, plans, worktrees, or logs.
- **Supplemental Explanatory View**: A maintained, text-backed setup diagram with a reproducible
  generated output, provenance, and validation evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-002**: Preview and installation identify the same component IDs and versions in 100% of local,
  manifest, artifact, and trusted-catalog acceptance paths.
- **SC-003**: Three consecutive installations of the same release produce one unchanged component,
  command, projection, and receipt state and no modifications to project-authored sources or shared
  triage state.
- **SC-004**: In 100% of supported coding-agent presentations, the nine affected normal commands,
  fast-loop, five Concorde-specific commands, and three native triage surfaces are materialized from
  the installed release; commands and roles preserve equivalent semantics.
- **SC-005**: Every seeded unsupported-version, untrusted-source, missing-component, digest,
  collision, and partial-failure case stops without a false success record and provides actionable
  recovery information.
- **SC-006**: Compatible update and bundle removal preserve 100% of project-authored `.concorde/`
  and `specs/` source hashes, shared triage state, modified/unowned agent files, inactive integration
  surfaces, and every shared component.
- **SC-008**: Both supplemental views pass all deterministic diagram, containment, theme, provenance,
  and freshness checks with zero errors or warnings.
- **SC-009**: Every command in the phase-path acceptance matrix reads or writes only its specified
  durable feature-root or temporal `attempt/` location in three consecutive clean-project
  runs, with every checklist below `attempt/checklists/` and zero root compatibility copies or
  symlinks.
- **SC-010**: Clean-project verification succeeds with zero reads from the Concorde checkout and
  fails when any required preset layer, extension command, adapter, runtime, queue helper, canonical
  agent body, or platform wrapper is removed from the release archive.
- **SC-011**: Disable and reprioritize preserve all nine already materialized winners, while update
  and removal materialize the expected accepted or next surviving layer for all nine commands, with
  zero stale Concorde instructions.
- **SC-012**: A first-time maintainer on a machine without the Concorde checkout installs the
  current published release into a project with one command in under 5 minutes.
- **SC-013**: The one-command path and documented manual bundle-plus-projector path produce identical
  components, registries, commands, projections, receipts, and shared default config in 100% of
  acceptance runs for the same release and integration.
- **SC-014**: A repository-wide tracked-path and tracked-content scan, followed by release build,
  self-host refresh, and clean-project install, finds zero uses of the superseded preset token and
  reports exactly `preset:concorde`, `extension:concorde`, and `bundle:concorde-bundle`.
- **SC-015**: Fresh Claude and Codex installations contain 100% of the three expected native triage
  outputs, and parsed projections agree on all four actions, four routes, plan statuses, shared paths,
  and role write boundaries with zero mandatory model pins or checkout paths.
- **SC-016**: Three repeated installs of one release change zero bytes after the first across
  components, registries, commands, agent projections, receipts, and shared triage state.
- **SC-017**: In update/remove fixtures, 100% of digest-matching owned projections are reconciled,
  0% of modified/unowned/inactive-integration files are lost, and every conflict prevents a false
  success report.
- **SC-018**: Release build/verification and self-hosting inventory 100% of canonical agent assets
  and the shared queue helper; removing any required member makes the applicable clean-project gate
  fail with an actionable finding.

## Assumptions

- Spec Kit `0.16.4` is the first supported host version; broader support requires equivalent
  acceptance evidence before it is advertised.
- Spec Kit's public preset command-composition and install-time registration contracts are the
  supported integration boundary. Arbitrary mutation of Spec Kit's installed scripts is not
  assumed to be distributable by the Concorde bundle.
- Spec Kit 0.16.4 has no native manifest field for arbitrary custom-agent projections; the Concorde
  installer therefore invokes only an integrity-covered operation from the installed extension and
  documents the equivalent manual bundle-plus-projector path.
- `concorde-bundle` remains integration-agnostic and lets Spec Kit inherit the target project's
  active coding-agent integration.
- Project-authored architecture sources are user data, not installed component files.
- The first bundle deliberately contains one composition component and one active capability
  component; additional component types require a separate scope decision.
- Preset and extension identities are namespaced by Spec Kit component type, so their shared
  `concorde` ID is unambiguous in manifests, registries, catalogs, and lifecycle commands.
- No publicly supported release requires an in-place migration from the superseded development-only
  preset identity; current development installations are rematerialized from the renamed maintained
  sources, with no alias retained.
- Local development may serve built catalogs and archives over localhost to exercise the same
  resolution path as publication, but the release builder only writes the supplied location into
  metadata. Once a release is published, the published location is the default consumer source and
  the localhost path remains the development and acceptance path.
- Existing bundle lifecycle evidence may be reused, but self-hosting skills, string-presence checks,
  and manually routed test fixtures do not satisfy the installed-command acceptance criteria.

## Dependencies

- A supported Spec Kit distribution with bundle, preset, extension, catalog, provenance, and active
  integration capabilities.
- A supported coding-agent integration capable of presenting installed extension commands.
- Feature 005's Reflection Triage Contract v1 and canonical extension agent assets.
- The Concorde distribution and Skills modules and their boundary contracts.
- Feature 001 for the Concorde workflow used after setup.
- The `publish-release` sub-feature for a publicly reachable release, and the `one-command-install`
  sub-feature for the accelerated component-plus-projection path over it.
