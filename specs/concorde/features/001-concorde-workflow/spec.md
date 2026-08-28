---
id: feature.concorde.workflow
kind: feature
module: module.concorde
refines: []
subfeatures:
  - feature.concorde.workflow.initialize-architecture
  - feature.concorde.workflow.retrieve-bounded-context
  - feature.concorde.workflow.answer-workflow-questions
  - feature.concorde.workflow.manage-feature-workspaces
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.workflow.execute-and-reconcile
  - feature.concorde.workflow.validate-architecture
  - feature.concorde.workflow.harden-design
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

**Created**: 2026-08-19

**Revised**: 2026-08-27

**Status**: Entirely revised around a two-document model at every level of the hierarchy: a short
module summary (`module.md`) paired with a module design reference (`design.md`), and a feature
specification (`spec.md`) paired with an accepted realization (`implementation.md`, formerly the
feature-level `design.md`). The nine workflow-step sub-features remain the decomposition. Existing
automated evidence covers the previous document model only; the document-model requirements below
are not yet realized, and human comprehension and browser review remain pending.

**Input**: User description: "Each module has a `module.md`; add a per-module `design.md`.
`module.md` must be a short (reading time under 20 minutes) description of the module — the most
important interface for both humans and AI to quickly understand the design at that level — and it
should use diagrams to represent the structure well. `design.md` should instead contain the
implementation details and the ideas and rationales developed during development; it is a reference
that neither users nor AIs should need to read routinely. To distinguish it from the module-level
`design.md`, rename the feature's `design.md` to `implementation.md`. Entirely revise feature 001."

## Outcome

A maintainer or coding agent can understand any level of the project in minutes from its module
summary, find every deeper fact by deliberate descent into that level's design reference or a
feature's accepted realization, and move one correlated change from architectural placement through
specification, planning, implementation, validation, and accepted realization while every command
respects one selected feature root, bounded context, explicit human authority, and reproducible
source ownership.

## Clarifications

### Session 2026-08-27

- Q: Should a new feature root get a placeholder `implementation.md` at specification time, or
  should the file not exist until the first hardening writes it? → A: Specification seeds a
  placeholder whose only content is the explicit "no realization has been hardened yet" state;
  the first hardening overwrites it in full and later hardenings complete it. A valid root always
  owns the durable pair `spec.md` + `implementation.md`.
- Q: When and by whom is implementation detail and rationale written into a module's `design.md`?
  → A: During work it is captured inside `implementation/`; only an approved hardening proposal
  writes attempt-derived content into `design.md`. Maintainers may edit `design.md` directly at any
  time as an ordinary maintained source; no workflow phase other than hardening writes it.
- Q: What form must the required structure diagram in `module.md` take? → A: The maintained
  level view (`architecture.json`), linked explicitly from the summary and embedded in the
  published page; a leaf without a view records a one-line rationale. The summary may also
  include additional explanatory diagrams (module- or feature-owned maintained views, or inline
  text diagrams), each with a textual counterpart, none redefining the level view, and all within
  the reading budget.
- Q: Should an over-budget `module.md` be a validation error or a warning? → A: A warning: it is
  reported as a finding with remediation, but validation still returns `success`; keeping the
  summary within budget is a review responsibility.
- Q: How are existing projects migrated to the document model? → A: Concorde is currently the
  only adopter of its workflow, so adoption is a one-time refactor of this repository guided by
  validation findings; no migration command, general migration procedure, compatibility alias, or
  transition period is introduced.

## Workflow Boundary

Concorde surrounds the normal Spec Kit lifecycle with architectural controls; it does not replace
Spec Kit's specification, clarification, planning, task, implementation, analysis, convergence, or
issue-conversion procedures. The parent feature owns the end-to-end order, the document model, shared
concepts, cross-step invariants, and command inventory. Each immediate sub-feature owns the
observable behavior of one cohesive workflow step and does not restate this aggregate contract.

Installation, bundle management, update, and removal belong to
`feature.concorde.install-with-spec-kit`. Publication mechanics of the read-only project documentation
belong to `feature.concorde.publish-project-docsite`; this feature states what the published pages
must show for the document model, not how they are built.

## Document Model

Every level of the hierarchy separates a **summary that is read** from a **reference that is
consulted**. The summary is the primary interface for humans and coding agents; the reference keeps
the whole specification complete beneath that surface (constitution A.I and A.II).

### Module level

```text
<module>/
├── module.md          summary: read first and, usually, only
├── design.md          reference: consulted deliberately for one specific question
├── architecture.json  level view: the required structure diagram (non-leaf)
├── diagrams/          optional supplemental module-owned views
├── contracts/
├── features/
└── modules/
```

| Document | Purpose | Reader expectation | Shape |
|---|---|---|---|
| `module.md` | Explain what this level does and how its visible parts interact: responsibility, boundary, structure diagram, feature/contract/submodule inventories, one representative scenario, and the key design rationale in a few sentences. | The most important interface to the level for humans and agents. A reader can stop here and go no deeper. | Under 20 minutes of reading; diagram plus tables plus short prose. Long narrative is prohibited. |
| `design.md` | Record the implementation details of the level and the ideas, rationales, alternatives, and decisions developed during development, organized under stable headings. | A reference. Neither humans nor agents need it to understand the level; it is opened only for a detail the summary deliberately leaves out, and it is never an implicit input to a workflow operation. | Unbounded length, but navigable by heading; reachable from the summary. May state that nothing has been recorded yet. |

`module.md`, the level view, and the contract documents remain the only authorities for
responsibility, boundary, organization, and boundary obligations. `design.md` explains and
justifies them; it never redefines them.

### Feature root

```text
features/<number-name>/
├── spec.md            required behavior
├── implementation.md  accepted realization (formerly design.md)
├── diagrams/
├── contracts/
├── subfeatures/       top-level feature only; one level, same shape
└── implementation/    at most one temporal attempt, compacted into implementation.md
```

| Document | Purpose |
|---|---|
| `spec.md` | What the feature must make observable and why; unchanged by this revision. |
| `implementation.md` | How the currently accepted implementation realizes the feature: collaborating modules and lower-level features, contracts and data/control flow, scenario realization, durable decisions, evidence references, and limitations. It is written by the first accepted hardening and completed by each later one; before that it holds only the explicit statement that no realization has been hardened. It carries every content obligation previously placed on the feature-level `design.md`. |
| `implementation/` | The one attempt in progress. Hardening compacts it into `implementation.md` and removes it. |

The name `design.md` is reserved for the module level; the name `implementation.md` is reserved for
feature roots. A `design.md` at a feature root is a legacy artifact to rename, not a valid document.
No compatibility alias or symlink may stand in for either name.

### Where a fact lives

| A reader wants to know… | Reads |
|---|---|
| what a level does, how its parts hang together, and where to go next | `module.md` |
| why the level is designed this way, how it is implemented, what was tried and rejected | `design.md` |
| what a boundary promises and what crosses it | the contract document |
| what a feature must make observable | `spec.md` |
| how the accepted implementation realizes that feature | `implementation.md` |
| what is being attempted right now | `implementation/` |
| what the code actually does and whether it is proven | code and tests |

## Decomposition

| Order | Sub-feature | Owned command surface | Impact of this revision |
|---:|---|---|---|
| 1 | `feature.concorde.workflow.initialize-architecture` | `speckit.concorde.init` | Root package gains `design.md` beside `module.md`; the seeded summary has the required shape. |
| 2 | `feature.concorde.workflow.retrieve-bounded-context` | `speckit.concorde.context` | Context is built from summaries, views, contracts, and feature summaries; `design.md` is returned as a navigation reference only. |
| 3 | `feature.concorde.workflow.answer-workflow-questions` | `speckit.concorde.ask` | Answers ground in installed guidance and summaries first; a reference or accepted realization is opened only on demand and cited. |
| 4 | `feature.concorde.workflow.manage-feature-workspaces` | Feature Workspace Protocol routing of the standard Spec Kit selection (no Concorde command) | The durable pair becomes `spec.md` + `implementation.md`; a root with a legacy `design.md` is invalid. |
| 5 | `feature.concorde.workflow.specify-behavior` | `speckit.specify`, `speckit.clarify`, `speckit.checklist` | Specification seeds or preserves `implementation.md` instead of `design.md`. |
| 6 | `feature.concorde.workflow.plan-delivery` | `speckit.plan`, `speckit.tasks`, `speckit.taskstoissues` | The accepted baseline is `implementation.md`; the level's `module.md` is bounded context and `design.md` is consulted only on demand. |
| 7 | `feature.concorde.workflow.execute-and-reconcile` | `speckit.implement`, `speckit.analyze`, `speckit.converge` | Unchanged except that the durable baseline it consults is `implementation.md`. |
| 8 | `feature.concorde.workflow.validate-architecture` | `speckit.concorde.validate` | New rules for summary shape and reading budget, reference presence, feature-root pairing, and legacy names. |
| 9 | `feature.concorde.workflow.harden-design` | `speckit.concorde.feature.harden` | The compaction target is `implementation.md`; the same reviewed proposal may amend the module `design.md`, applied atomically with it. |

The decomposition follows maintainer outcomes rather than implementation packages. Commands are
grouped only when they operate on the same selected artifacts as one recognizable workflow step.
Stable child IDs are unchanged by this revision. The children inherit `module.concorde`, cannot own
children, and remain distinct from adjacent-module feature refinement.

## Shared Vocabulary and Invariants

- A **module** owns one responsibility, its current-level features, boundary contracts, a view of
  itself plus immediate children, a **module summary** (`module.md`), and a **module design
  reference** (`design.md`).
- A **feature root** is either a top-level feature or one immediate sub-feature. It owns durable
  `spec.md` and `implementation.md` documents and at most one temporal `implementation/` attempt.
- A **selection** identifies exactly one canonical feature root. All lifecycle phases use the paths
  returned for that selected root.
- **Bounded context** exposes one architectural level built from summaries, views, contracts, and
  feature summaries. Parent and sibling feature relationships are concise navigation context, not
  permission to load their bodies or attempts. A design reference is navigation, not content.
- `module.md` owns what a level does and how it is organized; `design.md` owns how and why it is
  built; `spec.md` owns required behavior; `implementation.md` owns the accepted realization;
  `implementation/` owns one temporary attempt. Generated pages and reports are projections, not
  maintained intent.
- A **reading budget** bounds every module summary: under 20 minutes for a first-time reader.
- Human approval is required before architecture creation or hardening mutates maintained intent.
  Read-only questions, context retrieval, analysis, and validation do not grant approval.
- Feature containment and adjacent-module feature refinement are separate relationships with
  separate validation and documentation labels.

## End-to-End Workflow

| Stage | Maintainer outcome | Operation | Reads | Writes |
|---:|---|---|---|---|
| 1 | Establish or review the root module package and its boundary. | `speckit.concorde.init` | Existing project metadata | `.concorde/config.json`, `module.md`, `design.md`, level view, accepted initial contracts |
| 2 | Inspect exactly one level and choose where the feature is specified. | `speckit.concorde.context` | Summaries, level views, contracts, feature summaries | — |
| Any | Ask a source-grounded, read-only workflow question. | `speckit.concorde.ask` | Installed guidance and summaries; a reference only when the question requires it | — |
| 3 | Create the feature root at its canonical path, or select an existing root through the standard Spec Kit selection (`.specify/feature.json` / `SPECIFY_FEATURE_DIRECTORY`). | `speckit.specify` / Spec Kit selection | — | New `spec.md` + `implementation.md`; selection pointer |
| 4 | Define behavior, resolve material uncertainty, and review requirements quality. | `speckit.specify` / `speckit.clarify` / `speckit.checklist` | `spec.md`; existing `implementation.md` read-only; level summary | `spec.md`; `implementation/checklists/` |
| 5 | Plan one implementation attempt, order its work, and optionally project tasks into issues. | `speckit.plan` / `speckit.tasks` / `speckit.taskstoissues` | `spec.md`, `implementation.md`, level summary; references on demand | `implementation/` |
| 6 | Execute tasks, analyze artifact consistency, and append only genuine remaining work. | `speckit.implement` / `speckit.analyze` / `speckit.converge` | The attempt and the durable pair | `implementation/`, code, tests |
| 7 | Deterministically validate maintained architecture and evidence references. | `speckit.concorde.validate` | All maintained sources | — |
| 8 | Review and explicitly compact a completed attempt into durable accepted realization. | `speckit.concorde.feature.harden` | Durable pair, complete attempt, level summary and reference | `implementation.md`; optional reviewed `design.md` amendment; removes `implementation/` |

Validation may be invoked after any maintained structural change, not only at stage 7. Context and
the question surface may be used whenever a maintainer needs to navigate or understand the workflow.

## Cross-Sub-feature Relationships

Initialization must precede operations that depend on an existing Concorde hierarchy and is the
first writer of a module summary and reference. Workspace management establishes the selected root
consumed by all normal Spec Kit phases. Specification is the durable behavioral input to planning;
planning creates the temporal artifacts consumed by execution; validation may challenge any
maintained structural claim; hardening is eligible only after execution work and review state are
complete, and it is the only workflow step that carries rationale developed during an attempt into
a module design reference. A later attempt begins again from the durable specification and the last
accepted realization.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: The maintained parent diagram `diagrams/concorde-workflow-components.json` is
  the one core `architecture` view because it shows the shared invocation layers and artifact
  authorities used across all nine children: the maintainer, the coding-agent integration, the nine
  Spec Kit phase surfaces, the five Concorde surfaces, the selected-workspace adapter, the launchers
  and runtime, project control state, architecture sources (module summaries, design references,
  contracts, views), the selected feature intent, the accepted realization, and the temporal attempt.
  Its textual counterpart is the Document Model, End-to-End Workflow, and Decomposition sections
  above. The child specifications use this parent view plus the bounded module view; they do not
  duplicate it.
- **Supplemental decisions**: None. The stage order in the End-to-End Workflow table and the
  acceptance scenarios below carry the sequencing; no scenario needs a separate dynamic view.
- **Generated view**: `generated/architecture/concorde-workflow-components.html`, a reproducible
  projection rather than maintained intent.

## User Scenarios & Testing

### User Story 1 - Understand one level in minutes (Priority: P1)

A maintainer or coding agent opens a module summary and, within the reading budget, can state what
the module does, see its structure, list its features, contracts, and submodules, follow one
representative scenario, and decide whether to descend — without opening `design.md`.

**Why this priority**: This is the purpose the whole hierarchy serves. If the summary does not carry
the level on its own, every other workflow step is working from an unreadable map.

**Independent Test**: Give first-time readers the root module summary of a validated project and a
timed set of questions from the "Where a fact lives" table; confirm the summary alone answers the
level questions and that the deterministic reading-budget and shape checks pass for every module.

**Acceptance Scenarios**:

1. **Given** a validated module, **When** a reader opens its `module.md`, **Then** it presents a
   structure diagram, the feature, contract, and submodule inventories, the responsibility, the
   boundary, and one representative scenario within the reading budget.
2. **Given** a question about why or how the level is built, **When** the reader follows the
   summary's reference link, **Then** `design.md` answers it under a stable heading and the summary
   itself was not lengthened to do so.
3. **Given** a bounded-context or workflow-question request for a module, **When** the response is
   produced, **Then** it is built from the summary, level view, contracts, and feature summaries and
   returns `design.md` only as a navigation reference unless the question explicitly asked for its
   content.

---

### User Story 2 - Complete a governed change under the document model (Priority: P1)

A maintainer establishes architectural ownership, selects the right feature root, specifies and
plans the change, directs implementation, validates maintained sources, and accepts the resulting
realization, with the accepted realization landing in `implementation.md` and the ideas developed
along the way landing in the level's `design.md` — never in the summary.

**Why this priority**: The lifecycle is the product; the document model is only real if every step
reads and writes the right document.

**Independent Test**: Complete the lifecycle for one top-level feature and one sub-feature and verify
that every phase uses only the selected root's authoritative paths and the new document names.

**Acceptance Scenarios**:

1. **Given** an initialized project, **When** a maintainer completes all ordered stages, **Then** the
   result has one canonical `spec.md`, one accepted `implementation.md`, no temporal attempt, a
   module summary untouched by hardening, and — when the reviewed proposal included one — a module
   `design.md` amended exactly as reviewed.
2. **Given** a new root is created through specification, **When** the phase completes, **Then**
   the root contains `spec.md` and an `implementation.md` stating that no realization is hardened,
   and contains no `design.md`.
3. **Given** an immediate sub-feature is selected, **When** normal phases run, **Then** the parent's
   durable pair is read-only context and sibling bodies and attempts are not implicitly loaded.

---

### User Story 3 - Refactor this repository to the document model (Priority: P2)

Concorde is currently the only adopter of its own workflow, so the move to the new model is a
one-time refactor of this repository: rename every feature-level `design.md` to
`implementation.md`, add a `design.md` reference to every module, bring every `module.md` to the
summary shape, and update the installed guidance, templates, contracts, and framework docs that
name those files — with validation naming every leftover and publication showing the new pages.

**Why this priority**: The model is only trustworthy once this checkout lives under it, and
constitution B.II requires Concorde to develop itself with its own rules before the milestone is
declared complete.

**Independent Test**: Validate this repository before the refactor and confirm every legacy root and
missing reference is reported; after it, validate and publish the repository and search its
maintained sources, templates, commands, and framework docs for any remaining feature-level
`design.md` reference.

**Acceptance Scenarios**:

1. **Given** this repository before the refactor, **When** validation runs, **Then** every
   feature-root `design.md` and every module without `design.md` is reported with a concrete
   remediation and no source is rewritten.
2. **Given** the refactor is applied, **When** validation and publication run, **Then** zero legacy
   findings remain, every module page embeds its level view and links its reference page, and every
   feature page pairs its specification with its accepted realization.
3. **Given** the completed refactor, **When** the installed templates, command instructions,
   contracts, examples, and framework documentation are searched, **Then** none treats a
   feature-level `design.md` as valid, and no migration command, alias, or transition shim exists.

---

### User Story 4 - Stop safely at a review boundary (Priority: P2)

A maintainer can inspect any proposal, question answer, context result, analysis report, or validation
finding before authorizing a mutation.

**Why this priority**: Explicit human authority over maintained intent is a constitutional
obligation; the new hardening scope (a module reference amendment) widens what a proposal may touch
and therefore what review must see.

**Independent Test**: Exercise every review-only mode against a snapshot and verify maintained
sources are byte-identical afterward.

**Acceptance Scenarios**:

1. **Given** an initialization or hardening proposal, **When** approval is withheld, **Then** no
   maintained source or selection state changes.
2. **Given** a hardening proposal that includes a module `design.md` amendment, **When** it is
   presented, **Then** the maintainer sees the exact reference change alongside the candidate
   `implementation.md` and the cleanup manifest before deciding.
3. **Given** missing or conflicting evidence, **When** validation or analysis runs, **Then** the
   result reports disagreement or uncertainty rather than rewriting intent.

---

### User Story 5 - Resume from durable authority (Priority: P3)

A maintainer starts a later delivery attempt from the current specification and accepted realization
without depending on a previous temporal task log.

**Why this priority**: Durable authority is what makes the temporal attempt safe to discard.

**Independent Test**: Harden one attempt, begin another, and verify the new attempt resolves the same
durable root without root-level compatibility copies.

**Acceptance Scenarios**:

1. **Given** a hardened feature, **When** planning starts again, **Then** a fresh `implementation/`
   workspace is created beneath that feature root and `spec.md` plus `implementation.md` remain
   authoritative.

### Edge Cases

- A module summary exceeds the reading budget, lacks a structure diagram or inventory table, or a
  leaf module has no level view and records no rationale for omitting a diagram.
- A module `design.md` is missing, unreachable from its summary, or contradicts the summary, the
  level view, or a contract.
- A feature root contains both a legacy `design.md` and an `implementation.md`, or only the legacy
  file.
- A hardening proposal tries to edit `module.md`, or a `design.md` at a level other than the one at
  which the feature is specified.
- A question or planning step needs a detail that exists only in a design reference.
- A command receives an unknown, ambiguous, unsafe, or stale module/feature target.
- A sub-feature specification names a child as its parent or attempts a third containment level.
- A phase finds an existing non-empty attempt and must report it as active rather than replace it.
- A contract, refinement, scenario, diagram, or parent registration is missing or contradictory.
- The maintained source digest changes between proposal review and approved application.
- Generated evidence disagrees with maintained intent or cannot be reproduced.

## Requirements

### Functional Requirements

**Document model**

- **FR-001**: Every module MUST own a `module.md` summary and a `design.md` reference at its module
  root, alongside its contracts, features, and (for a non-leaf module) its level view.
- **FR-002**: `module.md` MUST be readable in under 20 minutes and MUST combine short prose
  covering responsibility, boundary, one representative scenario, and the key design rationale;
  inventory tables for features, boundary contracts, and immediate submodules; and the level's
  structure diagram, which is the maintained level view (`architecture.json`) linked explicitly
  from the summary and embedded in the published page (a leaf module without a view records a
  one-line rationale instead). The summary MAY include additional explanatory diagrams — module-
  or feature-owned maintained views, or inline text diagrams — each with a textual counterpart and
  none redefining structure owned by the level view, provided the summary stays within its reading
  budget. Narrative that would breach the budget belongs in `design.md`.
- **FR-003**: `design.md` MUST be the level's reference for implementation details and for the
  ideas, rationales, alternatives, and decisions developed during development; it MUST be organized
  under stable headings, MUST be reachable from `module.md`, MAY state explicitly that nothing has
  been recorded yet, and MUST NOT redefine responsibility, boundary, contracts, or organization
  owned by `module.md`, the contract documents, and the level view. A maintainer MAY edit it directly
  as an ordinary maintained source; workflow operations write it only through an approved hardening
  proposal.
- **FR-004**: No workflow operation MAY treat a module `design.md` as an implicit input. Bounded
  context, workflow questions, and planning MUST reach it only through deliberate navigation or an
  explicit request, and MUST cite it whenever its content is used.
- **FR-005**: Every feature root MUST own `spec.md` and `implementation.md` and at most one
  `implementation/` attempt. `implementation.md` MUST carry every content obligation previously
  placed on the feature-level `design.md`, including the explicit "no realization hardened" state
  before the first accepted milestone. The first accepted hardening MUST overwrite the placeholder
  in full and each later hardening MUST complete it; no other workflow step writes its substantive
  content, and a root without the file is invalid.
- **FR-006**: The name `design.md` MUST be reserved for module level and `implementation.md` for
  feature roots. A `design.md` at a feature root MUST be rejected as a legacy artifact with a rename
  remediation, and no compatibility alias or symlink may stand in for either name.

**Workflow steps**

- **FR-007**: Initialization MUST create the root module summary in the required shape and its
  design reference together, and re-running against the same package MUST remain unchanged.
- **FR-008**: Bounded context MUST be built from module summaries, level views, contracts, and
  feature summaries, and MUST return a module `design.md` only as a stable navigation reference.
- **FR-009**: Workflow questions MUST answer from installed guidance and module summaries first and
  MUST open a design reference or accepted realization only when the question asks for
  implementation detail or rationale, citing what was opened.
- **FR-010**: Workspace resolution MUST return the selected root's `spec.md` and `implementation.md`
  as its durable pair (and the parent's read-only pair for a sub-feature) and MUST report a root
  whose accepted realization still bears the legacy name as invalid.
- **FR-011**: Specification MUST seed `spec.md` and an `implementation.md` holding only the
  not-yet-hardened state for a new root, and MUST preserve an existing `implementation.md`
  byte-for-byte.
- **FR-012**: Planning MUST read `spec.md` and `implementation.md` as the durable inputs and the
  level's `module.md` as bounded context, and MUST NOT update either durable document, any module
  summary, or any module reference.
- **FR-013**: Hardening MUST compact the completed attempt into the selected root's
  `implementation.md` and remove `implementation/`; the same reviewed proposal MAY carry the
  implementation details and rationales developed during the attempt into the `design.md` of the
  level at which the feature is specified. Every part of the proposal MUST apply atomically under
  one explicit approval or not at all, and hardening MUST NOT edit any `module.md`.
- **FR-014**: Validation MUST deterministically check summary shape (required sections, an
  explicit link to the level view or a recorded leaf rationale, inventory tables), the reading
  budget, reference presence and reachability, feature-root pairing, and legacy names, reporting
  each breach as an actionable finding without rewriting any source. A reading-budget overrun is a
  warning-severity finding that does not change the validation status; every other breach in this
  list is an error.
- **FR-015**: Published pages MUST render each module summary as the level's page with its structure
  diagram embedded and its design reference as a separately linked page, MUST pair each feature
  page's specification with its accepted realization, and MUST exclude every temporal attempt.

**Migration**

- **FR-016**: Installed guidance, templates, command instructions, contracts, schemas, examples,
  framework documentation, and this repository's own specification hierarchy MUST be migrated
  together as one one-time refactor of this repository — currently the only adopter of the
  workflow — so that no maintained source treats a feature-level `design.md` as valid. No
  migration command, compatibility alias, or transition period is introduced; validation findings
  name any leftover, and affected contract changes MUST follow their compatibility rules.
- **FR-017**: The child specifications of this feature MUST be reconciled with this document model
  before the feature is treated as architecture-complete.

**Shared invariants**

- **FR-018**: Concorde MUST preserve the ordered workflow and command ownership declared in the
  Decomposition and End-to-End Workflow sections.
- **FR-019**: Every command MUST operate on one explicit or selected canonical target and MUST reject
  ambiguous, unsafe, or structurally invalid targets.
- **FR-020**: All normal Spec Kit phases MUST use the selected Feature Workspace Protocol paths and
  MUST NOT derive competing root-level plan, task, or checklist paths.
- **FR-021**: The workflow MUST support exactly two feature-containment levels while keeping
  containment independent from adjacent-module refinement; parent specifications own aggregate
  outcomes, shared invariants, ordering, and decomposition, and child specifications own focused
  workflow-step behavior.
- **FR-022**: Bounded operations MUST disclose their target, source basis, status, and complete
  findings without silently expanding unrelated deeper content.
- **FR-023**: Proposal-only, question, context, analysis, and validation operations MUST be read-only.
- **FR-024**: Mutations of maintained architectural intent, accepted realization, or a design
  reference MUST require explicit approval of the presented proposal and MUST fail safely if
  reviewed inputs become stale.
- **FR-025**: Missing or conflicting implementation evidence MUST be represented as unknown or
  disagreement, never as inferred agreement.
- **FR-026**: Installed Codex and slash-command presentations MUST preserve equivalent command intent,
  arguments, path authority, review boundaries, and failure behavior.
- **FR-027**: Generated diagrams, documentation, indexes, manifests, and reports MUST remain
  reproducible projections of maintained sources and MUST exclude temporal attempts.
- **FR-028**: A feature-owned diagram MUST supplement text, declare its role, live under the owning
  lifecycle root's `diagrams/`, and never silently define behavior or contracts.
- **FR-029**: The workflow MUST remain usable in an installed project without depending on this
  repository's source-tree paths.
- **FR-030**: Deterministic operations MUST return stable structured statuses and actionable findings
  suitable for both human review and automated tests.

### Scope

**In scope**: the two-document model at module level and feature root; the reading budget; the
rename of the feature-level accepted realization; root initialization; bounded context; workflow
questions; Feature Workspace Protocol resolution of the standard Spec Kit selection; selected-root
routing for all nine normal Spec Kit phases; architecture validation; feature hardening including
reviewed design-reference amendments; migration of installed guidance and of Concorde's own
hierarchy; the shared authority and containment model connecting those operations.

**Out of scope**: installation and bundle lifecycle; documentation-site publication mechanics;
application-specific implementation quality; a third feature-containment level; a second feature
lifecycle or registry; a per-feature `design.md` (the name is reserved for modules); a migration
command, general-purpose migration procedure, or compatibility period for the previous document
model; relaxing the one-providing-module placement rule toward constitution A.III, which remains a
separately tracked follow-up.

### Key Entities

- **Module**: One architectural responsibility with current-level features, contracts, children, a
  one-level view, a summary, and a design reference.
- **Module summary** (`module.md`): The bounded, budgeted, diagram-backed description of a level;
  the primary interface for readers.
- **Module design reference** (`design.md`): The level's reference for implementation detail and
  development rationale; reached deliberately, never implicitly.
- **Feature root**: A top-level feature or immediate sub-feature with its own durable and temporal
  artifact boundaries.
- **Accepted realization** (`implementation.md`): The durable account of how the currently accepted
  implementation realizes a feature.
- **Implementation attempt** (`implementation/`): Temporary plan, tasks, checklists, research,
  models, guidance, and evidence for one delivery cycle.
- **Reading budget**: The maximum first-time reading effort a module summary may demand.
- **Selection**: The canonical pointer to exactly one feature root.
- **Workspace result**: Versioned paths and bounded relationship context for the selected root.
- **Proposal**: A reviewable, source-bound description of a permitted maintained mutation, now
  including an optional design-reference amendment.
- **Finding**: A deterministic rule result identifying severity, location, explanation, and remedy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every module summary in a validated project — including all five in Concorde's own
  hierarchy — is within the reading budget and links its level view (or records a leaf
  rationale), contains the three inventory tables, and includes one representative scenario.
- **SC-002**: After the refactor, 100% of feature roots (20 in this repository) contain `spec.md` and
  `implementation.md`, 0 contain `design.md`, and 100% of modules (5 in this repository) contain
  `design.md`.
- **SC-003**: In all bounded-context, question, and planning fixtures, no module `design.md` body
  appears in a result unless it was explicitly requested, and every use of one is cited.
- **SC-004**: At least 90% of first-time maintainers can name the correct document for each row of
  the "Where a fact lives" table and the command for each workflow stage after no more than five
  minutes with a module summary and this feature.
- **SC-005**: All 14 installed command surfaces map to exactly one sub-feature and appear once in the
  aggregate workflow inventory.
- **SC-006**: In all lifecycle routing tests, every phase reads or writes only the selected top-level
  feature or immediate sub-feature paths returned by the workspace result.
- **SC-007**: In all approval-gated fixtures, withholding approval or changing reviewed sources causes
  zero maintained-intent mutations, including zero design-reference changes.
- **SC-008**: Repeated validation of unchanged sources produces byte-equivalent ordered findings,
  including the document-model rules.
- **SC-009**: All seeded invalid cases — legacy feature-level `design.md`, missing module `design.md`,
  summary over budget or missing its diagram or tables, and the existing hierarchy, containment,
  refinement, contract, scenario, path, and selection cases — produce actionable findings.
- **SC-010**: Every generated module page embeds its structure diagram and links its reference page;
  every generated parent page lists its immediate sub-features once in authored order; every child
  page exposes parent and sibling navigation; no temporal attempt is published.
- **SC-011**: A completed approved hardening leaves the reviewed `implementation.md` and any reviewed
  `design.md` amendment, removes exactly the selected attempt, and preserves every parent, sibling,
  child, and summary authority not named by the proposal.

## Assumptions

- The reading budget is measured deterministically as at most 4,000 words in the Markdown body of
  `module.md`, excluding front matter and embedded diagram source, which corresponds to 20 minutes
  at 200 words per minute; validation reports an overrun as a warning-severity finding (status
  remains `success`) rather than silently passing.
- A module `design.md` is required for every module, including leaves; a seeded reference that
  states nothing has been recorded yet is valid content, mirroring the "no realization hardened"
  state of a new feature root.
- Hardening is the reviewed vehicle by which rationale developed during an attempt reaches the
  module `design.md`; until then that rationale lives inside `implementation/`. No other workflow
  step writes a design reference, maintainers may edit one directly like any maintained source, and
  architecture changes to a summary continue to go through reviewed architecture edits and
  validation.
- The rename applies to every feature root at both containment levels and to every installed
  template, command, contract, schema, and example that names the accepted realization; the
  affected protocol and profile versions follow their own compatibility rules, which the
  implementation plan decides.
- Concorde is currently the only adopter of its workflow, so adopting the document model is a
  one-time refactor of this repository (constitution B.II) rather than a supported migration path;
  its 5 modules and 20 feature roots are the acceptance fixture, and the legacy-name validation
  rules remain only as validity checks.
- Spec Kit remains authoritative for its nine normal lifecycle procedures; Concorde is already
  installed and the project has a supported Spec Kit version.
- Parent context and sibling summaries are sufficient for ordinary child work; deeper sources are
  opened only by deliberate navigation.
- Human comprehension metrics require separate pilot evidence and are not implied by automated tests.

## Dependencies

- `contract.concorde.workflow` and `contract.concorde.spec-kit-platform`, plus the Architecture
  Source Profile and Feature Workspace Protocol they reference, whose compatibility rules govern the
  rename.
- The maintained `module.concorde` hierarchy, contracts, and bounded architecture view.
- `feature.concorde.publish-project-docsite` for rendering module summary and reference pages,
  `feature.concorde.install-with-spec-kit` for distributing migrated templates and commands, and
  `feature.concorde.self-host-framework` for materializing them in this checkout.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.workflow`
- **Providing module**: `module.concorde`
- **Decomposition decision**: nine ordered immediate sub-features, one per cohesive workflow step;
  IDs unchanged by this revision.
- **Feature containment**: this parent registers its `subfeatures` in authored order; each child
  declares `parent_feature`, inherits `module.concorde`, owns one `## Outcome`, and cannot contain a
  child.
- **Authority split**: this parent owns the document model, aggregate outcome, vocabulary, ordering,
  and cross-child relationships; each child owns focused step behavior and must be reconciled with
  the document model (FR-017).
- **Parent refinement**: none; this is a root-level feature.
- **Representative scenarios**: `scenario-concorde-establish-and-place-feature` and
  `scenario-concorde-review-implement-and-reconcile`, maintained in the root view.
- **Core feature diagram**: `diagrams/concorde-workflow-components.json` (`architecture`, `core`).
- **Supplemental diagrams**: none.
- **Contracts**: provides `contract.concorde.workflow`; requires `contract.concorde.spec-kit-platform`.
- **Architecture view**: `specs/concorde/architecture.json`.
- **Evidence status**: `partial` — existing evidence covers the previous document model; the
  document-model requirements have no realization yet.
