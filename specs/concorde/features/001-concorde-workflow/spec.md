---
id: feature.concorde.workflow
kind: feature
module: module.concorde
refines: []
scenarios:
  - scenario-concorde-establish-and-place-feature
  - scenario-concorde-review-implement-and-reconcile
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
architecture_view: specs/concorde/architecture.json
diagrams:
  - source: specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json
    role: core
    kind: architecture
    scenarios:
      - scenario-concorde-establish-and-place-feature
      - scenario-concorde-review-implement-and-reconcile
    output: generated/architecture/concorde-workflow-components.html
evidence_status: partial
canonical_spec: specs/concorde/features/001-concorde-workflow/spec.md
---

# Feature Specification: Concorde Workflow

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-19

**Revised**: 2026-08-25

**Status**: Concorde workflow, nested checklist routing, and hardening gate implemented; human/browser
evidence remains incomplete

**Input**: User description: "Make Feature 001 describe the actual Concorde workflow, including the
organization of specifications, the development lifecycle, and the commands that keep architecture
and feature work aligned. Add a permanent feature `design.md`; keep Spec Kit plan/task artifacts
temporal; and let users explicitly harden a task-complete milestone into the durable design while
removing the temporal implementation workspace. Keep requirements-quality checklists inside that
temporary workspace rather than at the durable feature root. Move Spec Kit installation and setup
into a separate feature."

## What the Concorde Workflow Is

Concorde is an architecture-aware development workflow for projects in which people direct the
structure and intent while coding agents produce much of the implementation. It combines
spec-driven development with Architecture as Code: feature specifications describe observable
behavior, while maintained module, contract, and Archify sources describe where that behavior
belongs and how immediate submodules collaborate to provide it.

The workflow does not replace the normal Spec Kit phases. Spec Kit remains authoritative for feature
specification, clarification, planning, task generation, implementation, analysis, and convergence.
Concorde surrounds those phases with four architectural controls:

1. locate the providing module and abstraction level before specifying or planning a change;
2. keep feature workspaces inside the providing module's specification package;
3. review affected module boundaries, contracts, refinements, and one-level views before approving
   implementation structure; and
4. provide bounded context and deterministic validation throughout implementation and review.

Installation, component catalogs, bundle preview, preset/extension setup, update, and removal are
specified separately by `feature.concorde.install-with-spec-kit`. Publication of the read-only
documentation site is specified separately by `feature.concorde.publish-project-docsite`.

## Specification and Architecture Organization

All maintained behavioral and architectural intent lives in one recursive `specs/` hierarchy.
Architecture is part of the system specification; it is not maintained in a separate top-level
`architecture/` source tree.

```text
specs/
└── <root-module>/
    ├── module.md                 # responsibility, features, boundary contracts
    ├── architecture.json        # current module + one level of immediate children
    ├── contracts/
    │   └── <contract>/
    │       ├── contract.md       # obligations, failures, compatibility, representation
    │       ├── schema.*          # required for a custom serialized format
    │       └── example.*         # representative custom value
    ├── features/
    │   └── <number>-<feature>/
    │       ├── spec.md           # durable canonical behavioral specification
    │       ├── design.md         # durable accepted feature realization
    │       ├── contracts/        # durable feature-level boundary representations
    │       ├── diagrams/         # maintained feature-owned Archify explanations
    │       └── implementation/   # temporal workspace for one delivery attempt
    │           ├── checklists/   # temporal requirements-quality review state
    │           ├── plan.md
    │           ├── tasks.md
    │           ├── research.md
    │           ├── data-model.md
    │           ├── quickstart.md
    │           └── validation.md
    └── modules/
        └── <child-module>/        # repeats the same package at the next level
```

At one architectural level, a maintainer sees the current module's responsibility, features, and
provided/required I/O contracts; its immediate submodules and their I/O summaries; permitted
external actors; and the organization and contract-governed interactions among those visible
participants. Child features, grandchildren, and deeper implementation details remain hidden until
the maintainer zooms into that child as the new current module.

### Durable specification, durable design, and temporal implementation

A feature remains valid beyond any one attempt to implement it. Its root therefore contains only
durable sources: `spec.md`, `design.md`, normative feature contracts and representations,
and feature-owned diagrams. `spec.md` answers what behavior is required and why it matters without
prescribing its realization. `design.md` records how the accepted implementation realizes that
feature by composing related modules, lower-level features, contracts, data/control flows, and
implementation decisions. It references the relevant module architecture rather than redefining
module boundaries or becoming a second `architecture.json`.

The `implementation/` directory is the active workspace for one delivery attempt. Its plan, research,
technical model, tasks, requirements-quality checklists, runnable acceptance guide, and recorded
evidence answer how that attempt will realize, review, and verify the feature. A specification or
clarification phase may create `implementation/checklists/` before a plan exists; doing so opens the
temporary attempt without turning review state into durable intent. Checkboxes record the current
review cycle, while every accepted requirement or design conclusion must be incorporated into
`spec.md` or, through hardening, `design.md`. Temporal artifacts may change substantially while work
is in progress and do not amend either durable document merely by changing.

When every task in the current attempt is complete, the maintainer may explicitly **harden** that
milestone. Hardening is a reviewable compaction, not an automatic end-of-implementation side effect:
the coding agent proposes the resulting `design.md` and the exact temporal files to remove; Concorde
binds the proposal to the current source digest and verifies task completion; and only explicit
approval applies the design update and removes `implementation/` atomically. The hardened design
retains accepted realization decisions and useful traceability, not the attempt's transient task log.
If any task is incomplete or any existing checklist item remains unresolved, the operation is
ineligible and changes nothing.

A later implementation attempt starts from both durable documents—`spec.md` as required behavior and
`design.md` as the accepted realization baseline—and creates a fresh `implementation/` directory.
The attempt may propose changes to either, but only specification review changes `spec.md`, and only a
subsequent approved hardening changes `design.md`. At most one active attempt exists for a feature,
and a successfully hardened feature has no `implementation/` directory.

Tools must resolve `spec.md`, `design.md`, and `contracts/` from the feature root, while resolving
checklists, plan-phase artifacts, and implementation-phase artifacts from `implementation/`. No
compatibility copy or symlink may place `checklists/`, `plan.md`, or `tasks.md` beside the durable
documents.

### Artifact authority

| Information | Canonical source | Role in the workflow |
|---|---|---|
| Feature behavior, requirements, constraints, and representative examples | `spec.md` | Defines what the providing module must make observable. |
| Accepted feature realization | `design.md` | Permanently explains how related modules, features, contracts, flows, and implementation decisions realize the feature, without owning their module architecture. |
| Requirements-quality review state | `implementation/checklists/` | Temporarily records whether the current specification or implementation attempt is ready to proceed; accepted findings must be reflected in durable sources. |
| Proposed feature implementation design and work | `implementation/plan.md` and `implementation/tasks.md` | Temporarily records one chosen delivery approach and its executable work until it is rejected or hardened. |
| Implementation research, technical models, acceptance guidance, and delivery evidence | Other files under `implementation/` | Supports one implementation attempt and never becomes durable feature intent by location. |
| Module responsibility, feature ownership, contracts, constraints, and decisions | `module.md` and contract Markdown | Defines durable architectural prose at that module level. |
| Current-level structure and ordered scenario interactions | `architecture.json` | Defines the machine-readable one-level view. |
| Feature-owned scenario or component explanation | Descriptively named Archify JSON under `diagrams/` | Supplements the text and bounded module view when invocation, collaboration, state, or data movement benefits from a visual explanation. |
| Standard or custom boundary representation | Referenced standard, or maintained schema/grammar and examples | Defines the information that may cross a module boundary. |
| Implementation and executable evidence | Code and tests | Records what exists and what has been demonstrated; durable references to accepted evidence may be summarized in `design.md`. |
| Rendered diagrams, documentation pages, indexes, and reports | Generated projections | Makes canonical sources reviewable; never becomes maintained intent. |

A feature is defined by its text. Scenarios are representative examples that make the behavior and
submodule collaboration concrete; they do not define the feature exhaustively. Feature-owned diagrams
are encouraged whenever they make those examples easier to understand. They may show the modules,
command surfaces, external systems, artifact stores, and contract crossings involved in a scenario,
but cannot silently add behavior or obligations absent from the textual specification and contracts.

## How the Installed Workflow Is Realized

Concorde is not one executable and a skill is not a second runtime. The installed workflow has four
distinct layers. Keeping them distinct lets a maintainer tell which artifact provides instructions,
which artifact chooses paths, and which code performs deterministic architecture operations.

| Layer | What it is | What it does in a user project |
|---|---|---|
| Package-neutral command definition | Markdown shipped by the Concorde preset or extension | Defines the command's agent-readable procedure independently of any one coding-agent UI. |
| Installed command surface | The active integration's materialization of that Markdown, such as a Codex `SKILL.md` or a slash-command file | Gives the maintainer an invocable name and tells the coding agent which procedure and tools to use. It is an instruction surface, not the Python implementation. |
| Portable adapter or launcher | Installed Bash, PowerShell, or Python entry scripts under `.specify/extensions/concorde/` | Resolves the selected workspace or locates the installed runtime without depending on this repository's source-tree paths. |
| Concorde Python runtime | Deterministic Python modules installed with the extension | Implements root initialization, feature creation/selection, bounded context, and validation; reads maintained sources and emits structured results. |

The `concorde-core` preset replaces nine normal Spec Kit command surfaces—`specify`, `clarify`,
`checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues`—so each phase
first invokes `workspace.py --phase <phase>`. The adapter reads the active feature selection and
returns the authoritative phase paths. The coding agent then continues the normal Spec Kit procedure
against either the durable feature root or its temporal `implementation/` directory. The preset does
not implement a second specification, planning, or implementation engine.

The `concorde` extension adds six Concorde-specific command surfaces: `init`, `feature-create`,
`feature-select`, `context`, `validate`, and `feature-harden`. Their instructions invoke the installed Bash or
PowerShell launcher, which locates the extension's Python entry point and runtime. The Python runtime
performs the deterministic operation and returns canonical JSON; the coding agent presents the
result, requests approval when mutation is proposed, or explains findings to the maintainer.

`feature-harden` is deliberately split between agent judgment and deterministic runtime control. The
agent synthesizes a concise candidate `design.md` from the completed attempt, current code/tests, and
durable sources. The runtime decides eligibility, verifies that every task is complete, binds the
proposal to the current sources, confines the design/removal paths, and applies an approved proposal
without leaving a partially updated design or partially removed attempt.

### The two invocation paths

```text
Normal Spec Kit phase
Maintainer → skill or slash command → coding agent follows command Markdown
           → workspace.py --phase <phase> → .specify/feature.json
           → feature root OR implementation/ → normal Spec Kit phase

Concorde architecture operation
Maintainer → skill or slash command → coding agent follows extension command Markdown
           → concorde.sh or concorde.ps1 → concorde.py → Concorde Python runtime
           → .concorde/config.json + specs/ → structured result → review or approval

Feature hardening
Maintainer → feature-harden skill or slash command → agent drafts the accepted feature design
           → runtime verifies completed tasks + proposal digest → maintainer reviews exact change
           → approved atomic apply → design.md updated + implementation/ removed
```

An active coding-agent integration owns only presentation and invocation syntax. Spec Kit owns
component resolution and its normal lifecycle. The preset owns phase-surface overrides and routing
instructions. The extension owns the Concorde commands, launchers, adapter, and runtime payload.
Architecture Core and Spec Kit Integration retain their behavioral ownership as defined by module
contracts; file packaging does not transfer that ownership.

## Project Workspace Map

The installed tool payload, maintained intent, temporal work, and generated evidence coexist in one
project, but they do not have equal authority.

```text
<project>/
├── .concorde/config.json                 # control: specification root and runtime policy
├── .specify/feature.json                 # control: selected canonical feature workspace
├── .specify/extensions/concorde/         # installed adapters, launchers, and Python runtime
├── .agents/skills/speckit-*/SKILL.md     # example Codex presentation of command surfaces
├── specs/<module>/
│   ├── module.md                         # architecture: responsibility and boundaries
│   ├── architecture.json                 # architecture: one-level component organization
│   ├── contracts/**/contract.md          # architecture: external I/O obligations
│   └── features/<feature>/
│       ├── spec.md                       # feature: durable behavior
│       ├── design.md                     # feature: durable accepted realization
│       ├── contracts/                    # feature: normative interface representations
│       ├── diagrams/                     # feature: text-backed visual explanations
│       └── implementation/               # temporal: one delivery attempt
│           └── checklists/                # temporal: requirements-quality review state
├── <source directories>/                 # implementation and runtime behavior
├── <test directories>/                   # executable evidence
├── generated/                            # reproducible diagrams and other projections
└── <documentation site>/                 # reproducible read model over canonical sources
```

`.concorde/` and `.specify/` are workflow control or installed-tool locations; they are not feature
or architecture specifications. Under `specs/`, authority is determined by artifact kind and
location: module prose, module contracts, and the bounded `architecture.json` describe architecture;
feature `spec.md`, feature contracts, and diagrams describe durable feature intent and examples;
feature `design.md` describes the durable accepted realization. Checklists and the other
`implementation/` artifacts provide temporary review state, proposals, or evidence; source code,
tests, and generated outputs likewise cannot silently redefine behavioral, design, or architectural
authority.

Contracts intentionally appear at two levels. A module contract records architectural identity,
ownership, direction, and boundary obligations. A feature-local contract or schema may define the
detailed representation needed by that feature. References between them must make the split explicit
so a reader never has to guess which file owns a fact.

## End-to-End Workflow and Commands

The command surface supports the workflow but does not become a second feature lifecycle. Canonical
command intent stays stable even when a coding-agent integration presents it as a skill or slash
command.

| Stage | Maintainer outcome | Primary operation |
|---|---|---|
| 1. Establish the root | Create or review the root module package, its I/O contracts, top-level features, immediate submodules, and one-level view. | `speckit.concorde.init` |
| 2. Locate ownership | Inspect exactly one bounded module level and decide which module owns the behavior at which abstraction. | `speckit.concorde.context <module-or-feature-id>` |
| 3. Create or select work | Create one nested feature root under the owning module, including `spec.md` and `design.md`, or select an existing feature; keep durable sources at the root. | `speckit.concorde.feature.create` / `speckit.concorde.feature.select` |
| 4. Specify and review behavior | Describe the feature in text, clarify uncertainty, record representative scenarios, contracts, refinement links, and expected evidence, add feature-owned diagrams when they improve comprehension, and record the current requirements-quality review under `implementation/checklists/`. | Normal Spec Kit specification, clarification, and checklist phases |
| 5. Agree on architecture | Review ownership, I/O contracts, immediate participants, dependency direction, and the affected one-level view before approving the implementation structure. | Bounded context plus maintained architecture sources |
| 6. Plan the implementation attempt | Read `spec.md` plus the accepted `design.md` baseline, continue or create the temporal `implementation/` workspace, then produce its plan and tasks with explicit architecture, contract, validation, and freshness work where affected. | Normal Spec Kit planning and task phases with Concorde path resolution |
| 7. Implement with bounded context | Give the coding agent only the relevant module level, feature artifacts, contracts, and evidence expectations; descend one level only when needed. | `speckit.concorde.context` plus normal implementation/convergence phases |
| 8. Reconcile and validate | Check maintained sources, references, hierarchy, contracts, views, and evidence; report disagreement or unknown evidence rather than silently rewriting intent. | `speckit.concorde.validate [path-or-id]` |
| 9. Harden an accepted milestone | After all current tasks are complete, review a digest-bound proposal that moves accepted realization details into `design.md`; explicitly approve an atomic design update and removal of `implementation/`. | `speckit.concorde.feature.harden` |
| 10. Review and publish | Review behavioral, design, and architectural changes together, then reproduce the read-only project site through the separate documentation feature. | Documentation publication workflow |

The six Concorde commands support this workflow without replacing the normal Spec Kit phases.
Feature creation and selection belong to Spec Kit Integration; initialization, context retrieval, and
validation belong to Architecture Core.

## Core Component and Interaction Diagram

The maintained architecture view in `diagrams/concorde-workflow-components.json` is the feature's core
diagram and produces `generated/architecture/concorde-workflow-components.html`. It answers the
stable structural question: when a maintainer invokes Concorde in an installed project, which parts
are agent-facing instructions, which parts are executable adapters or Python code, which workspace
artifacts they read or write, and how those responsibilities interact?

- **Skills and commands** separates the Maintainer and Coding Agent Integration from the nine
  preset-replaced Spec Kit phase surfaces and six extension-provided Concorde surfaces.
- **Normal Spec Kit phases** follows a phase surface through the selected-workspace adapter and
  project control state to durable feature sources and the temporal implementation attempt.
- **Concorde operations** follows an extension command through portable launchers to the deterministic
  Python runtime and the architecture or feature sources it manages and validates.
- **Project workspace** separates control state, architectural intent, durable behavioral intent,
  accepted feature design, and temporal implementation/evidence.
- **Harden a milestone** shows the task-completion gate and approved movement from a disposable
  attempt into permanent `design.md`.

The core view intentionally does not model chronological message order. If a particular user story
later needs call-by-call timing, retries, or asynchronous returns, it may add a separately declared
`role: supplemental` sequence or workflow diagram without replacing this component model.

The diagram does not replace the textual stories below or the canonical one-level root view in
`specs/concorde/architecture.json`. Its participants are implementation-facing representatives of
the root-level modules and external systems already governed by those sources.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish and Navigate the Architecture Hierarchy (Priority: P1)

As a maintainer, I can establish the project as a root module and inspect one architectural level at
a time so that I understand responsibilities, features, I/O contracts, immediate submodules, and
their organization without being overwhelmed by deeper details.

**Why this priority**: The bounded hierarchy is the foundation for every ownership, planning, and
review decision in Concorde.

**Independent Test**: Initialize a project with a root and two nested module levels, request context
at the root and then one child, and verify that each result exposes only the current module and its
immediate children while preserving navigable references to deeper levels.

**Acceptance Scenarios**:

1. **Given** a project without Concorde architecture sources, **When** the maintainer initializes the
   root, **Then** the proposed package states the root responsibility, explicit provided and required
   contract sets, current-level features, immediate submodules, and one-level view before any source
   is written.
2. **Given** an accepted root package, **When** the maintainer requests root context, **Then** the
   result includes the root I/O and features, immediate submodules and their I/O, relevant externals,
   and their organization, but excludes child features and grandchildren.
3. **Given** a visible child module, **When** the maintainer zooms into it, **Then** the child becomes
   the current module and the same visibility rule repeats at the next level.

---

### User Story 2 - Place and Specify a Feature at the Right Level (Priority: P1)

As a maintainer, I can choose the providing module, create or select its nested feature workspace,
and use the normal feature-specification lifecycle so that behavior has one canonical specification
and explicit architectural ownership.

**Why this priority**: Concorde cannot control structure if features are specified without first
deciding where and at what abstraction level they belong.

**Independent Test**: Starting from a hierarchy with a parent and two children, place a behavior that
spans both children on their nearest common parent, select its nested workspace, specify it through
the normal lifecycle, and verify that no duplicate flat specification is created.

**Acceptance Scenarios**:

1. **Given** proposed behavior owned entirely by one module, **When** the maintainer creates the
   feature, **Then** its workspace is nested under that module's `features/` directory, contains one
   canonical `spec.md` and one durable `design.md`, and becomes the single active Spec Kit workspace.
2. **Given** behavior spanning multiple child modules, **When** ownership is reviewed, **Then** the
   feature is owned by their nearest common parent and lower-level features may refine it from the
   participating children.
3. **Given** an existing nested feature, **When** the maintainer selects it, **Then** specification
   phases resolve the canonical root `spec.md`, planning reads the root `design.md` as its accepted
   baseline, and delivery phases resolve `implementation/plan.md` and `implementation/tasks.md`,
   without copying any artifact beside another authority.
4. **Given** a feature specification, **When** it is reviewed, **Then** its text defines the behavior
   and its scenarios are clearly presented as representative examples rather than exhaustive
   definitions.
5. **Given** a scenario involving multiple components or ordered boundary crossings, **When** the
   specification is reviewed, **Then** a text-backed feature diagram identifies the involved
   components and contract-governed interactions, or the specification records why a diagram would
   not improve understanding.

---

### User Story 3 - Review Architecture Before Approving the Plan (Priority: P2)

As a maintainer, I can review the feature's ownership, refinement links, boundary contracts, and
immediate-submodule collaboration before approving its implementation plan so that structural
decisions remain intentional even when AI writes the code.

**Why this priority**: Architecture reviewed only after implementation cannot reliably constrain the
structure being created.

**Independent Test**: Specify a cross-boundary feature, attempt to approve its plan without a
governing contract and current-level scenario, then add the missing artifacts and confirm that the
architecture review becomes complete.

**Acceptance Scenarios**:

1. **Given** a feature crossing a module boundary, **When** architecture readiness is reviewed,
   **Then** every crossing identifies a provided or required contract and every feature identifies at
   least one provided contract through which it is available.
2. **Given** a custom serialized contract, **When** it is reviewed, **Then** its readable schema or
   grammar, complete information meaning, field semantics, compatibility rules, example, and
   conformance evidence are available together.
3. **Given** a commonly adopted contract format, **When** it is reviewed, **Then** the relevant format
   and version, authoritative definition, and concise explanation of the information passed are
   available without duplicating the standard.
4. **Given** a non-leaf feature scenario, **When** its view is reviewed, **Then** it uses only the
   current module, immediate submodules, and permitted externals, and each boundary interaction names
   its governing contract.

---

### User Story 4 - Implement, Reconcile, and Validate with Bounded Context (Priority: P3)

As a maintainer or coding agent, I can retrieve the smallest sufficient architectural context and
deterministically validate the result after implementation so that local coding work remains aligned
with the reviewed hierarchy and contracts.

**Why this priority**: Bounded context and reproducible validation turn the architecture model into a
development control rather than passive documentation.

**Independent Test**: Implement a feature in a fixture with one deliberate broken refinement and one
missing evidence reference, then confirm that the agent receives only the requested level and that
validation reports both problems consistently without changing maintained sources.

**Acceptance Scenarios**:

1. **Given** an active feature, **When** implementation context is requested, **Then** it contains the
   feature specification, accepted feature design, active attempt artifacts, owning module, relevant
   parent/child refinement links, boundary contracts, current one-level view, and declared evidence,
   but no unrelated deeper hierarchy.
2. **Given** unchanged sources, **When** validation is repeated through different supported agent
   presentations, **Then** findings and ordering are identical.
3. **Given** a mismatch among specification, architecture, code, tests, or generated projections,
   **When** validation runs, **Then** the disagreement is reported with its source and remediation;
   missing implementation evidence remains `unknown` rather than being reported as agreement.
4. **Given** successful validation and human review, **When** the change is published, **Then** the
   generated site preserves source provenance and the same architecture hierarchy without becoming
   a second source of intent.
5. **Given** an installed Concorde project, **When** a maintainer inspects the core diagram and its
   textual counterpart, **Then** the maintainer can trace one normal Spec Kit phase and one Concorde
   architecture operation from invocation to the files and executable components involved, and can
   distinguish maintained architecture, durable feature intent, temporal work, and generated evidence.

---

### User Story 5 - Harden a Completed Milestone into Durable Design (Priority: P2)

As a maintainer, I can deliberately compact a completed and accepted implementation attempt into the
feature's permanent `design.md` and remove its temporal planning artifacts so that future maintainers
see the current realization without mistaking an old task plan for active work.

**Why this priority**: The permanent design is the bridge between behavioral intent and AI-produced
code. Without an explicit hardening lifecycle, accepted implementation knowledge either disappears
with temporary files or leaves stale plans that look authoritative.

**Independent Test**: In one fixture with an unchecked task and one with all tasks complete, invoke
the installed hardening surface. Verify that the first remains byte-identical; the second produces a
reviewable digest-bound proposal; and explicit approval updates `design.md` and removes only the
feature's `implementation/` directory without changing architecture, specification, code, or tests.

**Acceptance Scenarios**:

1. **Given** a feature whose current `tasks.md` contains any unchecked or malformed task item,
   **When** hardening eligibility is checked, **Then** the operation identifies the blocking tasks and
   makes no source change.
2. **Given** every task in the current attempt is complete, **When** hardening is requested, **Then**
   the coding agent proposes a complete `design.md`, the runtime returns the exact design target,
   temporal removal set, and source digest, and nothing is removed before maintainer approval.
3. **Given** a hardening proposal, **When** the maintainer reviews its feature realization, **Then**
   the document explains module/feature collaboration, contract and data/control flow, scenario
   realization, durable implementation decisions, code/evidence references, and known limitations
   without copying module architecture into the feature.
4. **Given** explicit approval of an unchanged proposal, **When** hardening is applied, **Then**
   `design.md` is created or updated and the complete `implementation/` directory is removed as one
   recoverable operation, while `spec.md`, architecture sources, code, and tests remain unchanged.
5. **Given** the sources, task state, candidate design, or removal set changes after proposal,
   **When** apply is attempted, **Then** the digest or confinement check rejects the stale proposal and
   leaves both `design.md` and `implementation/` unchanged.
6. **Given** a hardened feature with no active attempt, **When** a later planning phase starts, **Then**
   it reads both `spec.md` and `design.md`, creates a fresh `implementation/` workspace, and does not
   change `design.md` until another approved hardening.

### Edge Cases

- The correct providing module is unclear, or the behavior spans modules with no obvious common
  parent.
- A requested feature workspace already exists, conflicts with unrelated user content, or is selected
  while another workspace is active.
- An accepted feature has a stale or completed `implementation/` directory from an earlier delivery
  attempt.
- A hardening request has no `tasks.md`, contains zero recognizable task items, mixes complete and
  incomplete task syntax, or is made while implementation files are changing.
- The candidate design is empty, still contains proposal placeholders, attempts to redefine module
  ownership/contracts, or omits traceability needed to understand the accepted realization.
- Hardening is interrupted after staging, the design target is a symlink, or a removal path escapes
  the selected feature's `implementation/` directory.
- A feature is moved between modules after lower-level refinements already refer to it.
- A module is a leaf and therefore has no child-level architecture diagram.
- A scenario requires a participant deeper than the current level or crosses an undeclared boundary.
- A contract changes representation, version, direction, or ownership while dependent features remain
  unchanged.
- A custom contract example no longer conforms to its schema or grammar.
- Architecture sources are valid individually but contain duplicate IDs, cycles, broken references,
  or stale generated projections together.
- Implementation or test evidence is missing, inaccessible, or contradictory.
- An automated tool proposes a structural change that the maintainer has not approved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Concorde MUST maintain module architecture, boundary contracts, and feature workspaces
  in one recursive `specs/` hierarchy that mirrors module ownership.
- **FR-002**: Every module package MUST identify one responsibility, its current-level features,
  explicit provided and required contract sets, immediate submodules, and its parent when one exists.
- **FR-003**: Every non-leaf module MUST maintain one machine-readable architecture view showing only
  the current module, its features and I/O, immediate submodules and their I/O, permitted externals,
  and connections among those visible participants.
- **FR-004**: Selecting a child module MUST repeat the same view at the next level without expanding
  child features, grandchildren, or deeper implementation details in the parent view.
- **FR-005**: Every feature MUST have a stable ID, exactly one providing module at its abstraction
  level, one canonical textual specification, one durable feature design, an observable outcome, and
  relevant provided and required contracts.
- **FR-006**: A feature spanning multiple modules MUST be owned by their nearest common parent and MAY
  be refined by features owned by participating immediate children.
- **FR-007**: Feature refinement links MUST connect adjacent module levels, remain acyclic, and permit
  one parent feature to be realized by multiple child features and one child feature to support
  multiple parent features.
- **FR-008**: Feature scenarios MUST be identified as representative examples and MUST NOT replace or
  redefine the feature's textual requirements.
- **FR-009**: Every scenario interaction crossing a module boundary MUST name its governing contract
  and use only participants visible at that architectural level unless explicitly marked prose-only.
- **FR-010**: Every contract MUST state its stable ID, owner, provided/required role, flow direction,
  counterparties, obligations, failure semantics, compatibility expectations, and validation
  evidence.
- **FR-011**: A contract using a commonly adopted format MUST name its relevant format and version,
  link to the authoritative definition, and briefly explain the information passed.
- **FR-012**: A custom contract MUST use a programmer-observable serialized representation and MUST
  provide a normative schema or grammar, the complete information meaning, field semantics,
  compatibility rules, at least one representative example, and conformance evidence.
- **FR-013**: Concorde MUST establish or propose the root module package before feature work depends on
  it, and MUST preserve existing maintained intent unless the maintainer approves a presented change.
- **FR-014**: Concorde MUST let maintainers create a feature workspace under its providing module and
  select that workspace for subsequent normal Spec Kit lifecycle phases.
- **FR-015**: Selecting a nested feature workspace MUST preserve one canonical `spec.md` and MUST NOT
  create a duplicate flat or Concorde-specific feature specification.
- **FR-016**: Before a feature plan is approved, the workflow MUST review providing-module ownership,
  abstraction level, parent refinements, participating immediate submodules, governing contracts,
  dependency direction, affected one-level views, and expected implementation/test evidence.
- **FR-017**: Planning and task generation MUST include required architecture, contract, validation,
  traceability, and generated-freshness work whenever the feature changes those concerns.
- **FR-018**: Concorde MUST return one bounded architectural level for a requested module or feature,
  with stable references for deliberate navigation to adjacent levels.
- **FR-019**: Implementation context MUST include only the active feature artifacts and the smallest
  sufficient set of durable specification/design, module, contract, view, refinement, temporal, and
  evidence sources.
- **FR-020**: Concorde MUST deterministically validate IDs, paths, hierarchy, refinements, scenario
  boundaries, contracts, custom representations, view depth, references, evidence status, and
  generated-output freshness without requiring an AI model.
- **FR-021**: Validation MUST be read-only, repeatable, and explicit about rule, severity, location,
  and remediation for every finding.
- **FR-022**: Missing or conflicting implementation evidence MUST be reported as unknown or
  disagreement and MUST NOT be inferred as conformance from valid architecture alone.
- **FR-023**: Maintained architecture changes proposed or authored by an agent MUST require human
  approval and applicable deterministic checks before becoming accepted project intent.
- **FR-024**: The Concorde workflow MUST preserve Spec Kit's authority for specification, clarification,
  planning, tasks, implementation, analysis, and convergence while Concorde owns hierarchy,
  contracts, bounded views, structural traceability, validation, and publication coordination.
- **FR-025**: Generated diagrams, pages, indexes, and reports MUST be reproducible from maintained
  sources, identify their provenance, and remain non-authoritative read models.
- **FR-026**: Each feature root MUST contain a canonical `spec.md` for durable behavior and a
  canonical `design.md` for the durable accepted realization, alongside durable contracts, diagrams,
  and other declared durable representations; requirements-quality checklists, `plan.md`, `tasks.md`,
  implementation research, technical models, runnable acceptance guidance, and attempt evidence MUST
  reside only under that feature's `implementation/` directory.
- **FR-027**: The `implementation/` directory MUST represent at most one active delivery attempt and
  MUST NOT be treated as part of the canonical behavioral specification, accepted design, or module
  architecture merely because it is stored under `specs/`.
- **FR-028**: Workflow tools MUST resolve `spec.md`, `design.md`, and normative feature contracts from
  the feature root; specification, clarification, and custom checklist phases MUST resolve every
  generated checklist under `implementation/checklists/`; planning MUST read both durable documents;
  and all other plan-phase and implementation-phase artifacts MUST resolve from `implementation/`
  without compatibility copies or symlinks at the root.
- **FR-029**: A completed implementation attempt MUST remain temporal until the maintainer explicitly
  chooses to harden it; successful hardening MUST preserve the feature's stable ID, specification,
  providing module, refinement links, architecture sources, code, and tests while updating
  `design.md` and removing the feature's `implementation/` directory.
- **FR-030**: Specification and planning workflows MUST evaluate whether a feature's components and
  interactions would be materially clearer as a core architecture diagram and whether individual
  scenarios additionally need workflow, sequence, data-flow, or lifecycle views; every
  cross-component feature MUST provide a core component diagram or record why prose and the bounded
  module view are sufficient.
- **FR-031**: A feature-owned diagram MUST be maintained as descriptively named Archify JSON under
  the feature's `diagrams/` directory, identify the scenario or question explained, show the relevant
  component participation and contract crossings, have an equivalent textual explanation, and produce
  a validated, provenance-bearing generated projection without redefining feature behavior. The
  generated feature page MUST embed every declared diagram automatically and retain a link to its
  standalone interactive view.
- **FR-032**: Every declared feature diagram MUST identify its role as `core` or `supplemental`. A
  feature MAY declare at most one core diagram; that core diagram MUST use the Archify `architecture`
  type to show stable components, responsibilities, and interactions. Sequence, workflow, data-flow,
  and lifecycle diagrams MUST be supplemental views of narrower dynamic questions and MUST NOT serve
  as the feature's core diagram.
- **FR-033**: The installed workflow MUST preserve a reviewable distinction among package-neutral
  command definitions, agent-specific skill or slash-command presentations, portable adapters or
  launchers, and deterministic Python runtime behavior; an agent presentation MUST NOT be documented
  as though it independently implements the operation.
- **FR-034**: Every overridden normal Spec Kit phase MUST resolve the selected feature and its
  phase-specific durable or temporal path—including the durable design path—through the installed
  workspace adapter before accessing lifecycle artifacts, while every Concorde-specific operation
  MUST reach its installed Python runtime through a project-relative portable launcher rather than
  this repository's source path.
- **FR-035**: Workflow explanations, bounded context, and validation findings MUST classify relevant
  project artifacts as workflow control or installed tooling, maintained architecture, durable
  behavioral intent, durable accepted feature design, temporal implementation/evidence, or generated
  read model, and MUST NOT promote control state, implementation artifacts, or generated projections
  into specification, design, or architecture authority.
- **FR-036**: `design.md` MUST explain the accepted realization of its feature through related
  modules/features, contract and data/control flows, representative scenario realization, durable
  implementation decisions, implementation/evidence references, and known limitations; it MUST
  reference rather than redefine module responsibilities, boundaries, and architecture views.
- **FR-037**: Creating a feature MUST establish both root durable documents. Before the first hardened
  milestone, `design.md` MUST explicitly state that no implementation realization has yet been
  hardened rather than inventing implementation details.
- **FR-038**: Concorde MUST provide the canonical command `speckit.concorde.feature.harden` through
  every supported installed agent presentation, and its package-neutral command definition MUST
  separate agent-authored design synthesis from deterministic runtime eligibility and mutation.
- **FR-039**: Hardening eligibility MUST require an existing active `implementation/tasks.md` with at
  least one recognizable task and every task marked complete, plus every recognizable item in any
  existing `implementation/checklists/*.md` marked satisfied; missing, unchecked, or malformed task
  items and unresolved checklist items MUST block hardening without modifying any file.
- **FR-040**: Before mutation, hardening MUST present the candidate `design.md`, exact temporal removal
  set, target feature, and digest covering all durable and temporal inputs; approval MUST apply only to
  those exact unchanged bytes and paths.
- **FR-041**: Hardening MUST accept only the selected feature's root `design.md` as the durable target
  and only its complete `implementation/` directory as the removal target; it MUST reject absolute,
  escaping, symlinked, partial, or cross-feature targets.
- **FR-042**: Applying an approved hardening proposal MUST be failure-safe: either the new durable
  design is present and the temporal directory is absent, or the prior design and complete temporal
  directory remain recoverable without partial cleanup.
- **FR-043**: A successful hardening result MUST report the hardened feature, prior and resulting
  design digest, removed artifacts, retained authorities, and any findings in deterministic order.
- **FR-044**: Normal planning, task, implementation, analysis, and convergence instructions shipped
  to user projects MUST treat `design.md` as the accepted baseline and `implementation/` as a proposed
  delta; none may update `design.md` directly or remove the temporal workspace in place of the
  explicit hardening command.

### Scope

**Included**:

- The recursive module and feature hierarchy under `specs/`.
- Module ownership, feature refinement, scenarios, boundary contracts, and one-level views.
- Root initialization, bounded context retrieval, nested feature creation/selection, and deterministic
  validation as workflow operations.
- Separation of durable behavioral specification, durable accepted feature design, and one temporal
  `implementation/` workspace.
- User-triggered hardening of a task-complete milestone into `design.md`, followed by safe removal of
  its temporal workspace.
- Architecture gates around the normal specification, plan, task, implementation, convergence, and
  review lifecycle.
- Traceability among maintained intent, implementation, tests, validation, and generated projections.
- Text-backed feature-owned diagrams for scenarios whose component collaboration, invocation order,
  state changes, or data movement benefit from visual explanation.
- The observable installed boundary among command definitions, agent presentations, adapters,
  launchers, Python runtime, project control state, and maintained workspace artifacts.

**Excluded**:

- Spec Kit bundle/catalog installation, setup, update, removal, and package-role education; these are
  owned by `feature.concorde.install-with-spec-kit`.
- Internal algorithms of Spec Kit, coding-agent integrations, Archify, or the documentation generator
  beyond the observable command, adapter, runtime, source, and projection boundaries needed to use
  and review Concorde correctly.
- Replacing normal feature specifications with a separate Concorde behavioral artifact.
- Automatically accepting AI-authored architecture or treating structural validation as proof of
  implementation correctness.
- Modeling every class, function, or call edge as an architectural module.

### Key Entities

- **Module**: An architecturally meaningful unit with a stable identity, one responsibility, boundary
  contracts, current-level features, and optional immediate submodules.
- **Feature**: Textually specified observable behavior owned by exactly one module at one abstraction
  level and optionally refined at the adjacent child level.
- **Feature Workspace**: The single nested location containing the normal lifecycle artifacts for one
  feature, divided into durable specification/design sources and a temporal implementation workspace.
- **Feature Design**: The permanent `design.md` account of the currently accepted feature realization,
  including module/feature collaboration, flows, durable decisions, and evidence references without
  becoming the owner of module architecture.
- **Implementation Workspace**: The `implementation/` subdirectory containing the plan, tasks,
  requirements-quality checklists, research, technical model, acceptance guide, and evidence for at
  most one active delivery attempt.
- **Hardening Proposal**: A reviewable, digest-bound candidate design and exact cleanup manifest for a
  task-complete attempt; it grants no mutation authority until explicitly approved.
- **Installed Command Surface**: An agent-facing skill or slash-command presentation materialized
  from package-neutral command Markdown; it instructs an agent but is not itself the deterministic
  Concorde runtime.
- **Workspace Adapter and Runtime Launcher**: Project-relative executable entry scripts that resolve
  phase paths or locate and invoke the installed Python runtime without depending on Concorde's
  authoring repository.
- **Workspace Control State**: Project-scoped configuration and active-feature selection used to
  locate canonical sources; it controls workflow resolution but does not define feature behavior or
  module architecture.
- **Scenario**: A representative behavioral example whose participants and interactions are bounded
  to one architecture level.
- **Contract**: A directional boundary agreement defining obligations and observable information
  exchanged between a module and an external counterparty.
- **Architecture View**: The machine-readable structure and scenario traces for one current module and
  its immediate children only.
- **Feature Diagram**: A descriptively named, maintained Archify explanation declared as either the
  feature's single optional core component-interaction architecture view or a supplemental dynamic
  view; it supplements `spec.md` and the module view without becoming behavioral or architectural
  authority for facts owned elsewhere.
- **Bounded Context**: The smallest resolved set of current-level architecture and active feature
  sources required for one decision or implementation task.
- **Evidence Reference**: A stable link to implementation, tests, or generated validation material,
  with verified, partial, unknown, or conflicting status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of first-time maintainers can identify the correct providing module and
  create or select the canonical feature workspace within 10 minutes using only the workflow guide.
- **SC-002**: In a three-level test hierarchy, 100% of bounded context results expose the current
  module and immediate children while excluding child features and grandchildren.
- **SC-003**: In acceptance fixtures, 100% of cross-boundary scenario interactions resolve to a
  documented contract with role, flow, representation, and failure semantics.
- **SC-004**: A complete normal feature lifecycle produces exactly one canonical feature
  specification and no duplicate flat or architecture-specific copy.
- **SC-005**: Repeated validation of unchanged sources produces byte-equivalent ordered findings in
  100% of supported environments.
- **SC-006**: Every seeded hierarchy, refinement, contract, scenario-boundary, evidence, and freshness
  defect is detected and includes an actionable location and remediation.
- **SC-007**: At least 90% of pilot maintainers can explain, after no more than five minutes of review,
  that feature text defines behavior, scenarios illustrate it, module prose defines responsibility
  and contracts, and one-level views define current structure.
- **SC-008**: All architecture changes in the acceptance sample show explicit human approval and
  separate behavioral, structural, and implementation evidence before being marked complete.
- **SC-009**: In 100% of workflow path-resolution tests, specification and contract operations read
  the feature root, every generated checklist is written below `implementation/checklists/`, planning
  reads root `spec.md` and `design.md`, and task, implementation, analysis, and convergence operations
  use the same feature's `implementation/` workspace; no root-level `checklists/`, `plan.md`, or
  `tasks.md` is created.
- **SC-010**: Every required feature-owned diagram passes core/supplemental role validation and all
  deterministic Archify showcase, provenance, and freshness checks with zero errors or warnings;
  every diagrammed boundary crossing resolves to its textual contract reference, and every declared
  diagram appears on the canonical generated feature page without manual page markup.
- **SC-011**: After no more than five minutes with the installed-workflow explanation and core
  diagram, at least 90% of first-time maintainers can correctly trace both invocation paths, identify
  which steps are agent instructions versus deterministic scripts/runtime, and classify representative
  project paths into architecture, feature, temporal implementation/evidence, control/tooling, and
  generated read-model categories.
- **SC-012**: In 100% of hardening fixtures with any incomplete, missing, or malformed task state or
  unresolved checklist item, the operation returns an actionable blocker and all feature bytes remain
  unchanged.
- **SC-013**: In 100% of approved hardening fixtures, the resulting `design.md` matches the reviewed
  candidate, the complete `implementation/` directory is absent, all out-of-scope files are
  byte-identical, and an injected apply failure restores the pre-operation state.
- **SC-014**: In 100% of clean installed-project tests across supported agent presentations, the
  feature-hardening surface uses only release-installed command/runtime artifacts and returns
  equivalent eligibility, proposal, stale-digest, and apply results.
- **SC-015**: At least 90% of pilot maintainers can, after five minutes of review, correctly distinguish
  what belongs in `spec.md`, `design.md`, module architecture, and `implementation/`, and can identify
  when a milestone is eligible to harden.

## Assumptions

- Projects already use or intend to use the normal Spec Kit feature lifecycle; Concorde augments that
  lifecycle rather than providing an independent replacement.
- Architecturally meaningful module boundaries are chosen by maintainers with agent assistance and do
  not need to correspond one-to-one with source directories.
- The root module is the default starting point, while deeper module packages are created only when
  another abstraction level improves ownership or comprehension.
- One representative primary scenario is normally sufficient to explain a feature, with alternative,
  failure, degraded, or supplemental visual scenarios added only when they improve understanding.
- Initialization, feature creation/selection, bounded context, validation, and feature hardening form
  the Concorde-specific command surface; normal Spec Kit phases remain responsible for feature
  delivery between them.
- One active implementation workspace is sufficient; accepted attempt history remains available
  through version control and durable design/evidence references rather than archived temporal
  directories inside the canonical feature root.
- Task completion and resolution of every existing checklist item are deterministic hardening
  eligibility gates. Maintainer acceptance remains the separate authorization gate and is never
  inferred from checked boxes or passing validation.
- Documentation publication consumes validated sources through the separate Documentation feature and
  does not mutate maintained intent.

## Dependencies

- The Concorde constitution and root module package as governing architectural authority.
- A supported Spec Kit lifecycle capable of resolving one explicitly selected nested feature
  workspace.
- The separately installed Concorde preset and extension described by
  `feature.concorde.install-with-spec-kit`.
- The project documentation publication feature for the final read-only review surface.
