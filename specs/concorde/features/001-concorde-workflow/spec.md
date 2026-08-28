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

**Read first**: [tldr.md](tldr.md) — the self-contained TL;DR of this feature. **Accepted
realization**: [design.md](design.md) — consulted when writing the code or fixing a bug.

**Created**: 2026-08-19

**Revised**: 2026-08-28

**Status**: Revised around a three-tier feature document model: a short feature TL;DR (`tldr.md`,
under 15 minutes of reading), the complete specification (`spec.md`), and the feature design
reference (`design.md`: the accepted realization and the full implementation detail, needed only
when writing the code or fixing a bug). The feature-root `design.md` takes over the file this
hierarchy named `implementation.md` in the 2026-08-27 revision; `design.md` now means "design
reference" at every level. The module level keeps the summary/reference pair (`module.md` +
`design.md`). The nine workflow-step sub-features remain the decomposition. Existing automated
evidence covers the two-document model of the previous revision only; the TL;DR tier and the
feature-root rename are not yet realized, and human comprehension and browser review remain pending.

**Input**: User description (2026-08-27): "Each module has a `module.md`; add a per-module
`design.md`. `module.md` must be a short (reading time under 20 minutes) description of the module —
the most important interface for both humans and AI to quickly understand the design at that level —
and it should use diagrams to represent the structure well. `design.md` should instead contain the
implementation details and the ideas and rationales developed during development; it is a reference
that neither users nor AIs should need to read routinely." User description (2026-08-28): "Currently
the spec contains `spec.md` and `design.md`. I want a more compact version so that programmers and
AI agents understand it more easily. Let's have `tldr.md`, `spec.md`, and `design.md`: `tldr.md` is
a short (reading time under 15 minutes) account of a feature, `spec.md` is slightly more detailed,
and `design.md` is the full implementation detail that should only be required when writing the code
or fixing a bug. Modify feature 001 for this structure."

## Outcome

A maintainer or coding agent can understand any module from its summary and any feature from its
TL;DR in minutes, find every deeper fact by deliberate descent into the specification, the design
reference, or the contracts, and move one correlated change from architectural placement through
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

Revision note (2026-08-28): the accepted-realization file the first answer calls
`implementation.md` is the feature-root `design.md` from this revision onward, and the durable set
of a feature root is the trio `tldr.md` + `spec.md` + `design.md`. Every other answer stands
unchanged: the placeholder is seeded at specification and written in full by the first hardening,
a module `design.md` is written only by hardening or directly by a maintainer, the level view is
the required module diagram, reading-budget overruns are warnings, and adoption is a one-time
refactor of this repository.

## Workflow Boundary

Concorde surrounds the normal Spec Kit lifecycle with architectural controls; it does not replace
Spec Kit's specification, clarification, planning, task, implementation, analysis, convergence, or
issue-conversion procedures. The parent feature owns the end-to-end order, the document model, shared
concepts, cross-step invariants, and command inventory. Each immediate sub-feature owns the
observable behavior of one cohesive workflow step and does not restate this aggregate contract.

Installation, bundle management, update, and removal belong to
`feature.concorde.install-with-spec-kit`. Publication mechanics of the read-only project documentation
belong to `feature.concorde.publish-project-docsite`; this feature states what the published pages
must show for each document tier, not how they are built.

## Document Model

Every level of the hierarchy separates what is **read** from what is **consulted**. What is read is
the primary interface for humans and coding agents and must be absorbable in minutes; what is
consulted keeps the whole specification complete beneath that surface and is opened deliberately,
for one question at a time (constitution A.I and A.II). The name `design.md` means the consulted
design reference at every level.

### Module level

Unchanged by this revision.

```text
<module>/
├── module.md          summary: read first and, usually, only (under 20 minutes)
├── design.md          module design reference: consulted for one specific question
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
responsibility, boundary, organization, and boundary obligations. The module `design.md` explains
and justifies them; it never redefines them.

### Feature root

```text
features/<number-name>/
├── tldr.md            read first: what the feature is, in under 15 minutes
├── spec.md            the complete behavioral authority
├── design.md          feature design reference: accepted realization and full implementation detail
├── diagrams/
├── contracts/
├── subfeatures/       top-level feature only; one level, same shape
└── implementation/    at most one temporal attempt, compacted into design.md
```

| Document | Purpose | Reader expectation | Shape |
|---|---|---|---|
| `tldr.md` | Give a self-contained quick understanding of the feature: its purpose, its functionality (what it does and does not do), its basic structure (the participating parts and how they collaborate, with the declared core diagram when there is one), and its logic (how it works and the rules code must not break), plus where the rest lives. | The first — and for most questions the only — feature document a programmer or agent opens. Complete on its own for a quick understanding; its links to `spec.md` and `design.md` redirect, they are never required reading. It summarizes; it never defines. | Under 15 minutes of reading; five fixed sections (`Purpose`, `Functionality`, `Structure`, `Logic`, `Read Next`); a diagram or text sketch, short lists, short prose. |
| `spec.md` | Define required behavior completely: user scenarios, functional requirements, success criteria, scope, key entities, clarifications, assumptions, dependencies, and architecture alignment. | The authority whenever a requirement is defined, reviewed, tested, or disputed. Self-contained: readable without the TL;DR, more detailed than it, and still free of realization detail; it may link to `tldr.md` and `design.md` for redirection. | The Spec Kit specification shape. No deterministic reading budget; anything that explains *how* rather than *what* belongs in `design.md`. |
| `design.md` | Record how the currently accepted implementation realizes the feature: collaborating modules and lower-level features, contracts and data/control flow, scenario realization, durable implementation decisions, evidence references, known limitations, and the full implementation detail a coder needs. | Required only when writing the code or fixing a bug. Written by hardening; before the first accepted milestone it states only that no realization has been hardened. | Six fixed sections (`Realization Overview`, `Module and Feature Collaboration`, `Scenario Realization`, `Durable Implementation Decisions`, `Traceability and Evidence`, `Known Limitations`) followed by any further headings the implementation detail needs; unbounded, navigable by heading. |
| `implementation/` | The one attempt in progress: plan, tasks, checklists, research, models, guidance, evidence. | Hardening compacts it into `design.md` and removes it. | Temporal; never published. |

The reading path is **orientation → authority → reference**: `tldr.md` answers "what is this",
`spec.md` answers "exactly what must hold", `design.md` answers "how is it built". A feature root
that still holds `implementation.md` is a legacy artifact to rename to `design.md`; a root holding
both names is ambiguous. No compatibility alias or symlink may stand in for `tldr.md`, `spec.md`,
or `design.md`.

### How the tiers stay honest

- The TL;DR may not state a requirement, scope boundary, or success criterion that `spec.md` does
  not state; where the two disagree, `spec.md` prevails and the disagreement is a defect of the
  TL;DR that analysis reports and specification review fixes.
- Both read tiers stand alone: the TL;DR is understood without opening anything else, and
  `spec.md` is understood without the TL;DR. Cross-links between `tldr.md`, `spec.md`, and
  `design.md` exist so a reader can jump to the next level of detail, never because one document
  depends on another.
- The rules stated in the TL;DR's `Logic` section cite the requirement IDs in `spec.md` they
  summarize, so a reader can descend from a rule to its exact wording in one step.
- Validation checks the TL;DR deterministically for presence, section shape, its structure link,
  and the reading budget; whether it is a faithful summary remains a review responsibility.
- The feature `design.md` explains and realizes `spec.md`; it never redefines required behavior.
  A behavior change goes through specification review, then through a new attempt and hardening.

### Where a fact lives

| A reader wants to know… | Reads |
|---|---|
| what a level does, how its parts hang together, and where to go next | `module.md` |
| why the level is designed this way, how it is implemented, what was tried and rejected | the module `design.md` |
| what a boundary promises and what crosses it | the contract document |
| what a feature does, how it is basically structured, and how it works | `tldr.md` |
| exactly what a feature must make observable, and how that is accepted and measured | `spec.md` |
| how the accepted implementation realizes the feature, in full detail | the feature `design.md` |
| what is being attempted right now | `implementation/` |
| what the code actually does and whether it is proven | code and tests |

## Decomposition

| Order | Sub-feature | Owned command surface | Impact of this revision |
|---:|---|---|---|
| 1 | `feature.concorde.workflow.initialize-architecture` | `speckit.concorde.init` | Unchanged: initialization creates the root module package and no feature root. |
| 2 | `feature.concorde.workflow.retrieve-bounded-context` | `speckit.concorde.context` | Feature summary fields gain the TL;DR path; module and feature `design.md` are returned as navigation references only. |
| 3 | `feature.concorde.workflow.answer-workflow-questions` | `speckit.concorde.ask` | Answers ground in installed guidance, module summaries, and feature TL;DRs first; `spec.md` is opened for a requirement's exact wording and a `design.md` only for implementation detail or rationale, each cited. |
| 4 | `feature.concorde.workflow.manage-feature-workspaces` | Feature Workspace Protocol routing of the standard Spec Kit selection (no Concorde command) | The durable set becomes the trio `tldr.md` + `spec.md` + `design.md`; a root with a legacy `implementation.md` is invalid. |
| 5 | `feature.concorde.workflow.specify-behavior` | `speckit.specify`, `speckit.clarify`, `speckit.checklist` | Specification authors `tldr.md` and `spec.md` together and seeds or preserves the placeholder `design.md`; clarification keeps the TL;DR current; checklists review the TL;DR. |
| 6 | `feature.concorde.workflow.plan-delivery` | `speckit.plan`, `speckit.tasks`, `speckit.taskstoissues` | The accepted baseline is the feature `design.md`; the TL;DR is orientation, not a planning input. |
| 7 | `feature.concorde.workflow.execute-and-reconcile` | `speckit.implement`, `speckit.analyze`, `speckit.converge` | Implementation reads the feature `design.md` as its baseline; analysis reports TL;DR/specification disagreement. |
| 8 | `feature.concorde.workflow.validate-architecture` | `speckit.concorde.validate` | New rules for TL;DR presence, shape, and reading budget; the durable trio; and the legacy `implementation.md` name. |
| 9 | `feature.concorde.workflow.harden-design` | `speckit.concorde.feature.harden` | The compaction target is the feature `design.md`; the same reviewed proposal may amend the module `design.md`; hardening never writes `tldr.md` or `spec.md`. |

The decomposition follows maintainer outcomes rather than implementation packages. Commands are
grouped only when they operate on the same selected artifacts as one recognizable workflow step.
Stable child IDs are unchanged by this revision. The children inherit `module.concorde`, cannot own
children, and remain distinct from adjacent-module feature refinement.

## Shared Vocabulary and Invariants

- A **module** owns one responsibility, its current-level features, boundary contracts, a view of
  itself plus immediate children, a **module summary** (`module.md`), and a **module design
  reference** (`design.md`).
- A **feature root** is either a top-level feature or one immediate sub-feature. It owns the
  **durable trio** — the **feature TL;DR** (`tldr.md`), the **feature specification** (`spec.md`),
  and the **feature design reference** (`design.md`, also called the accepted realization) — and
  at most one temporal `implementation/` attempt.
- A **design reference** is the module or feature `design.md`: consulted deliberately, never an
  implicit input, and cited whenever its content is used.
- A **selection** identifies exactly one canonical feature root. All lifecycle phases use the paths
  returned for that selected root.
- **Bounded context** exposes one architectural level built from module summaries, level views,
  contracts, and feature summary fields (ID, title, outcome, evidence status, canonical root, TL;DR
  path). Parent and sibling feature relationships are concise navigation context, not permission to
  load their bodies or attempts.
- `module.md` owns what a level does and how it is organized; the module `design.md` owns how and
  why it is built; `tldr.md` orients; `spec.md` owns required behavior; the feature `design.md` owns
  the accepted realization; `implementation/` owns one temporary attempt. Generated pages and
  reports are projections, not maintained intent.
- A **reading budget** bounds every document that is read first: under 20 minutes for a module
  summary and under 15 minutes for a feature TL;DR, for a first-time reader.
- Human approval is required before architecture creation or hardening mutates maintained intent.
  Read-only questions, context retrieval, analysis, and validation do not grant approval.
- Feature containment and adjacent-module feature refinement are separate relationships with
  separate validation and documentation labels.

## End-to-End Workflow

| Stage | Maintainer outcome | Operation | Reads | Writes |
|---:|---|---|---|---|
| 1 | Establish or review the root module package and its boundary. | `speckit.concorde.init` | Existing project metadata | `.concorde/config.json`, `module.md`, module `design.md`, level view, accepted initial contracts |
| 2 | Inspect exactly one level and choose where the feature is specified. | `speckit.concorde.context` | Summaries, level views, contracts, feature summary fields | — |
| Any | Ask a source-grounded, read-only workflow question. | `speckit.concorde.ask` | Installed guidance, module summaries, feature TL;DRs; a specification or design reference only when the question requires it | — |
| 3 | Create the feature root at its canonical path, or select an existing root through the standard Spec Kit selection (`.specify/feature.json` / `SPECIFY_FEATURE_DIRECTORY`). | `speckit.specify` / Spec Kit selection | — | New `tldr.md` + `spec.md` + placeholder `design.md`; selection pointer |
| 4 | Define behavior, resolve material uncertainty, keep the TL;DR faithful, and review requirements quality. | `speckit.specify` / `speckit.clarify` / `speckit.checklist` | `tldr.md`, `spec.md`; existing feature `design.md` read-only; level summary | `tldr.md`, `spec.md`; `implementation/checklists/` |
| 5 | Plan one implementation attempt, order its work, and optionally project tasks into issues. | `speckit.plan` / `speckit.tasks` / `speckit.taskstoissues` | `spec.md`, feature `design.md`, level summary; the module reference on demand | `implementation/` |
| 6 | Execute tasks, analyze artifact consistency, and append only genuine remaining work. | `speckit.implement` / `speckit.analyze` / `speckit.converge` | The attempt and the durable trio | `implementation/`, code, tests |
| 7 | Deterministically validate maintained architecture and evidence references. | `speckit.concorde.validate` | All maintained sources | — |
| 8 | Review and explicitly compact a completed attempt into the accepted realization. | `speckit.concorde.feature.harden` | Durable trio, complete attempt, level summary and module reference | Feature `design.md`; optional reviewed module `design.md` amendment; removes `implementation/` |

Validation may be invoked after any maintained structural change, not only at stage 7. Context and
the question surface may be used whenever a maintainer needs to navigate or understand the workflow.

## Cross-Sub-feature Relationships

Initialization must precede operations that depend on an existing Concorde hierarchy and is the
first writer of a module summary and reference. Workspace management establishes the selected root
consumed by all normal Spec Kit phases. Specification is the durable behavioral input to planning
and is the only writer of the TL;DR; planning creates the temporal artifacts consumed by execution;
validation may challenge any maintained structural claim; hardening is eligible only after execution
work and review state are complete, is the only writer of the feature design reference, and is the
only workflow step that carries rationale developed during an attempt into a module design
reference. A later attempt begins again from the durable specification and the last accepted
realization.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: The maintained parent diagram `diagrams/concorde-workflow-components.json` is
  the one core `architecture` view because it shows the shared invocation layers and artifact
  authorities used across all nine children: the maintainer, the coding-agent integration, the nine
  Spec Kit phase surfaces, the five Concorde surfaces, the selected-workspace adapter, the launchers
  and runtime, project control state, architecture sources (module summaries, design references,
  contracts, views), the selected feature intent (TL;DR and specification), the feature design
  reference, and the temporal attempt. Its textual counterpart is the Document Model, End-to-End
  Workflow, and Decomposition sections above. The child specifications use this parent view plus
  the bounded module view; they do not duplicate it.
- **Supplemental decisions**: None. The stage order in the End-to-End Workflow table and the
  acceptance scenarios below carry the sequencing; no scenario needs a separate dynamic view.
- **Generated view**: `generated/architecture/concorde-workflow-components.html`, a reproducible
  projection rather than maintained intent.

## User Scenarios & Testing

### User Story 1 - Understand one level or one feature in minutes (Priority: P1)

A maintainer or coding agent opens a module summary or a feature TL;DR and, within its reading
budget, can state what it does, see its structure, list its parts, follow its main behavior, name the
rules code must respect, and decide whether to descend — without opening a `design.md`.

**Why this priority**: This is the purpose the whole hierarchy serves. If the summary and the TL;DR
do not carry their level on their own, every other workflow step is working from an unreadable map.

**Independent Test**: Give first-time readers the root module summary and one feature TL;DR of a
validated project and a timed set of questions from the "Where a fact lives" table; confirm those
two documents alone answer the level and feature questions and that the deterministic
reading-budget and shape checks pass for every module and every feature root.

**Acceptance Scenarios**:

1. **Given** a validated module, **When** a reader opens its `module.md`, **Then** it presents a
   structure diagram, the feature, contract, and submodule inventories, the responsibility, the
   boundary, and one representative scenario within the reading budget.
2. **Given** a validated feature root, **When** a programmer or agent opens its `tldr.md`, **Then**
   within 15 minutes, and without opening any other document, it presents the purpose, the
   functionality, the basic structure (with the declared core diagram when one exists), and the
   logic — how it works and the rules code must respect, with their `spec.md` requirement IDs — and
   where each deeper fact lives.
3. **Given** a question about exactly what must hold, **When** the reader follows a key rule's
   requirement ID, **Then** `spec.md` states it in one identifiable place and the TL;DR did not
   restate or extend it.
4. **Given** a question about how a feature or level is built, **When** the reader follows the
   `design.md` link, **Then** the design reference answers it under a stable heading and neither
   the summary nor the TL;DR was lengthened to do so.
5. **Given** a bounded-context or workflow-question request, **When** the response is produced,
   **Then** it is built from module summaries, level views, contracts, feature summary fields, and
   feature TL;DRs, and returns any `design.md` only as a navigation reference unless the question
   explicitly asked for its content.

---

### User Story 2 - Complete a governed change under the three-tier model (Priority: P1)

A maintainer establishes architectural ownership, selects the right feature root, specifies the
change as a TL;DR plus a specification, plans it, directs implementation, validates maintained
sources, and accepts the resulting realization, with the accepted realization landing in the feature
`design.md`, the ideas developed along the way landing in the module `design.md`, and the TL;DR and
specification untouched by hardening.

**Why this priority**: The lifecycle is the product; the document model is only real if every step
reads and writes the right tier.

**Independent Test**: Complete the lifecycle for one top-level feature and one sub-feature and verify
that every phase uses only the selected root's authoritative paths and the three document names.

**Acceptance Scenarios**:

1. **Given** an initialized project, **When** a maintainer completes all ordered stages, **Then** the
   result has one canonical `tldr.md` and `spec.md`, one accepted feature `design.md`, no temporal
   attempt, a module summary untouched by hardening, and — when the reviewed proposal included one —
   a module `design.md` amended exactly as reviewed.
2. **Given** a new root is created through specification, **When** the phase completes, **Then**
   the root contains a `tldr.md` in the required shape, a `spec.md`, and a `design.md` stating that
   no realization is hardened, and contains no `implementation.md`.
3. **Given** a clarification changes the specification, **When** the phase completes, **Then** the
   TL;DR reflects the accepted answer wherever it summarized the changed behavior, and no
   `design.md` changed.
4. **Given** an immediate sub-feature is selected, **When** normal phases run, **Then** the parent's
   durable trio is read-only context and sibling bodies and attempts are not implicitly loaded.

---

### User Story 3 - Refactor this repository to the three-tier model (Priority: P2)

Concorde is currently the only adopter of its own workflow, so the move to the new model is a
one-time refactor of this repository: write a `tldr.md` for every feature root, rename every
feature-level `implementation.md` to `design.md`, and update the installed guidance, templates,
contracts, schemas, examples, and framework docs that name those files — with validation naming
every leftover and publication showing the new pages.

**Why this priority**: The model is only trustworthy once this checkout lives under it, and
constitution B.II requires Concorde to develop itself with its own rules before the milestone is
declared complete.

**Independent Test**: Validate this repository before the refactor and confirm every legacy root and
missing TL;DR is reported; after it, validate and publish the repository and search its maintained
sources, templates, commands, and framework docs for any remaining feature-level `implementation.md`
reference.

**Acceptance Scenarios**:

1. **Given** this repository before the refactor, **When** validation runs, **Then** every
   feature-root `implementation.md` and every root without `tldr.md` is reported with a concrete
   remediation and no source is rewritten.
2. **Given** the refactor is applied, **When** validation and publication run, **Then** zero legacy
   findings remain, every module page embeds its level view and links its reference page, and every
   feature page opens on its TL;DR with the specification and the design reference one link away.
3. **Given** the completed refactor, **When** the installed templates, command instructions,
   contracts, examples, and framework documentation are searched, **Then** none treats a
   feature-level `implementation.md` as valid, and no migration command, alias, or transition shim
   exists.

---

### User Story 4 - Stop safely at a review boundary (Priority: P2)

A maintainer can inspect any proposal, question answer, context result, analysis report, or validation
finding before authorizing a mutation.

**Why this priority**: Explicit human authority over maintained intent is a constitutional
obligation, and hardening may now touch two design references in one proposal, so review must see
both.

**Independent Test**: Exercise every review-only mode against a snapshot and verify maintained
sources are byte-identical afterward.

**Acceptance Scenarios**:

1. **Given** an initialization or hardening proposal, **When** approval is withheld, **Then** no
   maintained source or selection state changes.
2. **Given** a hardening proposal that includes a module `design.md` amendment, **When** it is
   presented, **Then** the maintainer sees the exact reference change alongside the candidate
   feature `design.md` and the cleanup manifest before deciding.
3. **Given** missing or conflicting evidence, **When** validation or analysis runs, **Then** the
   result reports disagreement or uncertainty rather than rewriting intent.

---

### User Story 5 - Resume from durable authority (Priority: P3)

A maintainer starts a later delivery attempt from the current TL;DR, specification, and accepted
realization without depending on a previous temporal task log.

**Why this priority**: Durable authority is what makes the temporal attempt safe to discard.

**Independent Test**: Harden one attempt, begin another, and verify the new attempt resolves the same
durable root without root-level compatibility copies.

**Acceptance Scenarios**:

1. **Given** a hardened feature, **When** planning starts again, **Then** a fresh `implementation/`
   workspace is created beneath that feature root and `tldr.md`, `spec.md`, and `design.md` remain
   authoritative.

### Edge Cases

- A module summary exceeds the reading budget, lacks a structure diagram or inventory table, or a
  leaf module has no level view and records no rationale for omitting a diagram.
- A feature TL;DR is missing, exceeds its reading budget, lacks one of its five sections, does not
  link the feature's declared core diagram, cannot be understood without opening `spec.md`, or
  states a rule, scope boundary, or criterion that `spec.md` does not state.
- A module `design.md` is missing, unreachable from its summary, or contradicts the summary, the
  level view, or a contract.
- A feature root contains both a legacy `implementation.md` and a `design.md`, or only the legacy
  file, or a `design.md` without a `tldr.md`.
- A hardening proposal tries to edit `tldr.md`, `spec.md`, `module.md`, or a module `design.md` at
  a level other than the one at which the feature is specified.
- A question or planning step needs a detail that exists only in a design reference.
- A command receives an unknown, ambiguous, unsafe, or stale module/feature target.
- A sub-feature specification names a child as its parent or attempts a third containment level.
- A phase finds an existing non-empty attempt and must report it as active rather than replace it.
- A contract, refinement, scenario, diagram, or parent registration is missing or contradictory.
- The maintained source digest changes between proposal review and approved application.
- Generated evidence disagrees with maintained intent or cannot be reproduced.

## Requirements

### Functional Requirements

**Module level**

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
  budget. Narrative that would breach the budget belongs in the module `design.md`.
- **FR-003**: The module `design.md` MUST be the level's reference for implementation details and
  for the ideas, rationales, alternatives, and decisions developed during development; it MUST be
  organized under stable headings, MUST be reachable from `module.md`, MAY state explicitly that
  nothing has been recorded yet, and MUST NOT redefine responsibility, boundary, contracts, or
  organization owned by `module.md`, the contract documents, and the level view. A maintainer MAY
  edit it directly as an ordinary maintained source; workflow operations write it only through an
  approved hardening proposal.
- **FR-004**: No workflow operation MAY treat any `design.md` — module or feature — as an implicit
  input. Bounded context, workflow questions, and planning MUST reach one only through deliberate
  navigation or an explicit request, and MUST cite it whenever its content is used.

**Feature root**

- **FR-005**: Every feature root MUST own the durable trio `tldr.md`, `spec.md`, and `design.md`
  as real files, and at most one `implementation/` attempt. A root missing any of the three is
  invalid.
- **FR-006**: `tldr.md` MUST be self-contained — from it alone, without opening any other
  document, a reader gets a quick understanding of the feature's purpose, functionality, basic
  structure, and logic — MUST be readable in under 15 minutes, and MUST consist of exactly five
  sections in this order: `Purpose` (the outcome and for whom), `Functionality` (what the feature
  does and does not do: its operations, surfaces, and boundaries), `Structure` (the participating
  parts and how they collaborate, linking the feature's declared core diagram when one exists or
  otherwise the parent's core view, the level view, or an inline text sketch), `Logic` (how it
  works — the main flows in order — and the rules an implementer must not break, each rule citing
  the `spec.md` requirement ID it summarizes), and `Read Next` (links to `spec.md`, `design.md`,
  the contracts, the module summary, and any sub-features for the reader who wants the next level
  of detail). Its links redirect; they are never required to understand it. It MUST NOT state a
  requirement, scope boundary, or success criterion absent from `spec.md`; where they disagree,
  `spec.md` prevails. It is authored by specification, kept current by specification and
  clarification, and never written by any other workflow step.
- **FR-007**: `spec.md` MUST remain the complete, self-contained authority for required behavior —
  user scenarios, functional requirements, success criteria, scope, key entities, clarifications,
  assumptions, dependencies, and architecture alignment — MUST be understandable without the
  TL;DR, MUST be free of realization detail, MAY link to `tldr.md` and `design.md` for
  redirection, and has no deterministic reading budget; the TL;DR MUST be derivable from it.
- **FR-008**: The feature `design.md` MUST record how the currently accepted implementation realizes
  the feature under the six fixed sections (`Realization Overview`, `Module and Feature
  Collaboration`, `Scenario Realization`, `Durable Implementation Decisions`, `Traceability and
  Evidence`, `Known Limitations`), followed by any further headings the full implementation detail
  needs; before the first accepted milestone it MUST hold only the explicit "no realization
  hardened" state. The first accepted hardening MUST overwrite the placeholder in full and each later
  hardening MUST complete it; no other workflow step writes its substantive content.
- **FR-009**: `design.md` MUST mean the design reference at every level. A feature root holding
  `implementation.md` MUST be rejected as a legacy artifact with a rename-to-`design.md`
  remediation, a root holding both names MUST be rejected as ambiguous, and no compatibility alias
  or symlink may stand in for `tldr.md`, `spec.md`, or `design.md`.

**Workflow steps**

- **FR-010**: Initialization MUST create the root module summary in the required shape and its
  design reference together, and re-running against the same package MUST remain unchanged.
- **FR-011**: Bounded context MUST be built from module summaries, level views, contracts, and
  feature summary fields (ID, title, outcome, evidence status, canonical root, TL;DR path), and
  MUST return a module or feature `design.md` only as a stable navigation reference.
- **FR-012**: Workflow questions MUST answer from installed guidance, module summaries, and feature
  TL;DRs first, MUST open `spec.md` only when a requirement's exact wording is needed, MUST open a
  design reference only when the question asks for implementation detail, rationale, or accepted
  realization, and MUST cite what was opened.
- **FR-013**: Workspace resolution MUST return the selected root's `tldr.md`, `spec.md`, and
  `design.md` as its durable trio (and the parent's read-only trio for a sub-feature) and MUST
  report a root whose accepted realization still bears the legacy name `implementation.md` as
  invalid.
- **FR-014**: Specification MUST author `tldr.md` and `spec.md` together for a new root and seed a
  `design.md` holding only the not-yet-hardened state; for an existing root it MUST preserve
  `design.md` byte-for-byte. Clarification MUST encode accepted answers into `spec.md` and update
  the TL;DR wherever it summarized the changed behavior. Requirements-quality review MUST cover the
  TL;DR's shape, budget, and faithfulness to `spec.md`.
- **FR-015**: Planning MUST read `spec.md` and the feature `design.md` as the durable inputs and the
  level's `module.md` as bounded context, MAY use the TL;DR for orientation only, and MUST NOT
  update any durable document, module summary, or design reference.
- **FR-016**: Implementation MUST read the feature `design.md` as its accepted baseline; analysis
  MUST report any disagreement between `tldr.md` and `spec.md` alongside its other inconsistencies;
  neither they nor convergence MAY write a durable document.
- **FR-017**: Hardening MUST compact the completed attempt into the selected root's `design.md` and
  remove `implementation/`; the same reviewed proposal MAY carry the implementation details and
  rationales developed during the attempt into the `design.md` of the level at which the feature is
  specified. Every part of the proposal MUST apply atomically under one explicit approval or not at
  all, and hardening MUST NOT edit `tldr.md`, `spec.md`, or any `module.md`.
- **FR-018**: Validation MUST deterministically check module summary shape (required sections, an
  explicit link to the level view or a recorded leaf rationale, inventory tables) and reading
  budget; module reference presence and reachability; TL;DR presence, section shape, structure
  link, and reading budget; the durable trio; and legacy names, reporting each breach as an
  actionable finding without rewriting any source. A reading-budget overrun of a summary or a
  TL;DR is a warning-severity finding that does not change the validation status; every other
  breach in this list is an error.
- **FR-019**: Published pages MUST render each module summary as the level's page with its structure
  diagram embedded and its design reference as a separately linked page; MUST open each feature on
  its TL;DR with the specification and the feature design reference as separately linked pages and
  the declared core diagram embedded; and MUST exclude every temporal attempt.

**Migration**

- **FR-020**: Installed guidance, templates, command instructions, contracts, schemas, examples,
  framework documentation, and this repository's own specification hierarchy MUST be migrated
  together as one one-time refactor of this repository — currently the only adopter of the
  workflow — so that every feature root owns the durable trio and no maintained source treats a
  feature-level `implementation.md` as valid. No migration command, compatibility alias, or
  transition period is introduced; validation findings name any leftover, and affected contract
  changes MUST follow their compatibility rules.
- **FR-021**: The child specifications of this feature MUST be reconciled with this document model
  before the feature is treated as architecture-complete.

**Shared invariants**

- **FR-022**: Concorde MUST preserve the ordered workflow and command ownership declared in the
  Decomposition and End-to-End Workflow sections.
- **FR-023**: Every command MUST operate on one explicit or selected canonical target and MUST reject
  ambiguous, unsafe, or structurally invalid targets.
- **FR-024**: All normal Spec Kit phases MUST use the selected Feature Workspace Protocol paths and
  MUST NOT derive competing root-level plan, task, or checklist paths.
- **FR-025**: The workflow MUST support exactly two feature-containment levels while keeping
  containment independent from adjacent-module refinement; parent specifications own aggregate
  outcomes, shared invariants, ordering, and decomposition, and child specifications own focused
  workflow-step behavior.
- **FR-026**: Bounded operations MUST disclose their target, source basis, status, and complete
  findings without silently expanding unrelated deeper content.
- **FR-027**: Proposal-only, question, context, analysis, and validation operations MUST be read-only.
- **FR-028**: Mutations of maintained architectural intent, accepted realization, or a design
  reference MUST require explicit approval of the presented proposal and MUST fail safely if
  reviewed inputs become stale.
- **FR-029**: Missing or conflicting implementation evidence MUST be represented as unknown or
  disagreement, never as inferred agreement.
- **FR-030**: Installed Codex and slash-command presentations MUST preserve equivalent command intent,
  arguments, path authority, review boundaries, and failure behavior.
- **FR-031**: Generated diagrams, documentation, indexes, manifests, and reports MUST remain
  reproducible projections of maintained sources and MUST exclude temporal attempts.
- **FR-032**: A feature-owned diagram MUST supplement text, declare its role, live under the owning
  lifecycle root's `diagrams/`, and never silently define behavior or contracts.
- **FR-033**: The workflow MUST remain usable in an installed project without depending on this
  repository's source-tree paths.
- **FR-034**: Deterministic operations MUST return stable structured statuses and actionable findings
  suitable for both human review and automated tests.

### Scope

**In scope**: the three-tier feature document model (`tldr.md`, `spec.md`, `design.md`) and the
two-document module model; the reading budgets; the feature-root rename from `implementation.md` to
`design.md`; root initialization; bounded context; workflow questions; Feature Workspace Protocol
resolution of the standard Spec Kit selection; selected-root routing for all nine normal Spec Kit
phases; architecture validation; feature hardening including reviewed module-reference amendments;
migration of installed guidance and of Concorde's own hierarchy; the shared authority and
containment model connecting those operations.

**Out of scope**: installation and bundle lifecycle; documentation-site publication mechanics;
application-specific implementation quality; a third feature-containment level; a second feature
lifecycle or registry; a generated or derived TL;DR (it is authored); a reading budget for `spec.md`;
a migration command, general-purpose migration procedure, or compatibility period for the previous
document models; relaxing the one-providing-module placement rule toward constitution A.III, which
remains a separately tracked follow-up.

### Key Entities

- **Module**: One architectural responsibility with current-level features, contracts, children, a
  one-level view, a summary, and a design reference.
- **Module summary** (`module.md`): The bounded, budgeted, diagram-backed description of a level;
  the primary interface for readers of a level.
- **Module design reference** (`design.md`): The level's reference for implementation detail and
  development rationale; reached deliberately, never implicitly.
- **Feature root**: A top-level feature or immediate sub-feature with its own durable and temporal
  artifact boundaries.
- **Feature TL;DR** (`tldr.md`): The self-contained, budgeted, five-section quick understanding of
  a feature (purpose, functionality, structure, logic, where to read next); the primary interface
  for readers of a feature; summarizes `spec.md` and never defines beyond it.
- **Feature specification** (`spec.md`): The complete authority for what a feature must make
  observable and how that is accepted and measured.
- **Feature design reference** (`design.md`, the accepted realization): The durable account of how
  the currently accepted implementation realizes a feature, with the full implementation detail;
  needed only when writing the code or fixing a bug.
- **Implementation attempt** (`implementation/`): Temporary plan, tasks, checklists, research,
  models, guidance, and evidence for one delivery cycle.
- **Reading budget**: The maximum first-time reading effort a module summary (20 minutes) or a
  feature TL;DR (15 minutes) may demand.
- **Selection**: The canonical pointer to exactly one feature root.
- **Workspace result**: Versioned paths and bounded relationship context for the selected root.
- **Proposal**: A reviewable, source-bound description of a permitted maintained mutation,
  including an optional module design-reference amendment.
- **Finding**: A deterministic rule result identifying severity, location, explanation, and remedy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every module summary in a validated project — including all five in Concorde's own
  hierarchy — is within the reading budget and links its level view (or records a leaf
  rationale), contains the three inventory tables, and includes one representative scenario.
- **SC-002**: Every feature TL;DR in a validated project — including all 20 in Concorde's own
  hierarchy — is within the 15-minute reading budget, has exactly the five required sections in
  order, links its structure diagram or sketch, and cites `spec.md` requirement IDs for the rules
  in its `Logic` section.
- **SC-003**: After the refactor, 100% of feature roots (20 in this repository) contain `tldr.md`,
  `spec.md`, and `design.md`, 0 contain `implementation.md`, and 100% of modules (5 in this
  repository) contain `design.md`.
- **SC-004**: In all bounded-context, question, and planning fixtures, no module or feature
  `design.md` body appears in a result unless it was explicitly requested, and every use of one is
  cited.
- **SC-005**: At least 90% of first-time maintainers can name the correct document for each row of
  the "Where a fact lives" table and the command for each workflow stage after no more than five
  minutes with one module summary and one feature TL;DR, and can describe that feature's
  functionality, basic structure, and logic from the TL;DR alone.
- **SC-006**: All 14 installed command surfaces map to exactly one sub-feature and appear once in the
  aggregate workflow inventory.
- **SC-007**: In all lifecycle routing tests, every phase reads or writes only the selected top-level
  feature or immediate sub-feature paths returned by the workspace result, and no phase other than
  specification and clarification writes `tldr.md` or `spec.md`.
- **SC-008**: In all approval-gated fixtures, withholding approval or changing reviewed sources causes
  zero maintained-intent mutations, including zero design-reference changes.
- **SC-009**: Repeated validation of unchanged sources produces byte-equivalent ordered findings,
  including the document-model rules.
- **SC-010**: All seeded invalid cases — missing, over-budget, or malformed TL;DR; legacy
  feature-level `implementation.md`; missing module `design.md`; summary over budget or missing its
  diagram or tables; and the existing hierarchy, containment, refinement, contract, scenario, path,
  and selection cases — produce actionable findings.
- **SC-011**: Every generated module page embeds its structure diagram and links its reference page;
  every generated feature page opens on the TL;DR, embeds the declared core diagram, and links the
  specification and the design reference; every generated parent page lists its immediate
  sub-features once in authored order; every child page exposes parent and sibling navigation; no
  temporal attempt is published.
- **SC-012**: A completed approved hardening leaves the reviewed feature `design.md` and any
  reviewed module `design.md` amendment, removes exactly the selected attempt, and preserves every
  `tldr.md`, `spec.md`, parent, sibling, child, and summary authority not named by the proposal.
- **SC-013**: In every analysis fixture with a seeded TL;DR/specification disagreement, the report
  names the disagreeing statement and the prevailing `spec.md` requirement.

## Assumptions

- The module reading budget is measured deterministically as at most 4,000 words in the Markdown
  body of `module.md`, and the TL;DR reading budget as at most 3,000 words in the Markdown body of
  `tldr.md`, both excluding front matter and embedded diagram source, corresponding to 20 and 15
  minutes at 200 words per minute; validation reports an overrun as a warning-severity finding
  (status remains `success`) rather than silently passing.
- Self-contained means the TL;DR states the feature's facts at lower resolution than `spec.md`,
  not that it repeats the specification: the two documents carry the same truth at two depths, and
  their links only move the reader between depths.
- The TL;DR is an authored Markdown document, not a generated projection, because a faithful
  summary requires editorial judgment; it is required at both containment levels so that every
  feature root has the same shape and every feature page opens the same way, and a sub-feature's
  TL;DR may be very short.
- `spec.md` carries no deterministic budget; "slightly more detailed" is enforced by content rules
  (requirements only, no realization detail) and by review, not by a word count.
- Reusing the name `design.md` at the feature root is deliberate: at every level it is the document
  that is consulted rather than read, so a reader who has learned the module convention needs no
  second name. The 2026-08-27 rename to `implementation.md` is superseded.
- The feature `design.md` is required for every feature root; a seeded reference that states no
  realization has been hardened is valid content, mirroring the empty module reference.
- Hardening is the reviewed vehicle by which rationale developed during an attempt reaches the
  module `design.md`; until then that rationale lives inside `implementation/`. No other workflow
  step writes a design reference, maintainers may edit one directly like any maintained source, and
  architecture changes to a summary continue to go through reviewed architecture edits and
  validation.
- The rename and the new tier apply to every feature root at both containment levels and to every
  installed template, command, contract, schema, and example that names the accepted realization;
  the affected protocol, profile, proposal, and manifest versions follow their own compatibility
  rules, which the implementation plan decides.
- Concorde is currently the only adopter of its workflow, so adopting the model is a one-time
  refactor of this repository (constitution B.II) rather than a supported migration path; its 5
  modules and 20 feature roots are the acceptance fixture, and the legacy-name validation rules
  remain only as validity checks.
- Spec Kit remains authoritative for its nine normal lifecycle procedures; Concorde is already
  installed and the project has a supported Spec Kit version.
- Parent context and sibling summaries are sufficient for ordinary child work; deeper sources are
  opened only by deliberate navigation.
- Human comprehension metrics require separate pilot evidence and are not implied by automated tests.

## Dependencies

- `contract.concorde.workflow` and `contract.concorde.spec-kit-platform`, plus the Architecture
  Source Profile and Feature Workspace Protocol they reference, whose compatibility rules govern the
  new tier and the rename.
- The maintained `module.concorde` hierarchy, contracts, and bounded architecture view.
- `feature.concorde.publish-project-docsite` for rendering module summary, module reference, feature
  TL;DR, specification, and feature reference pages; `feature.concorde.install-with-spec-kit` for
  distributing migrated templates and commands; and `feature.concorde.self-host-framework` for
  materializing them in this checkout.

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
  the document model (FR-021).
- **Parent refinement**: none; this is a root-level feature.
- **Representative scenarios**: `scenario-concorde-establish-and-place-feature` and
  `scenario-concorde-review-implement-and-reconcile`, maintained in the root view.
- **Core feature diagram**: `diagrams/concorde-workflow-components.json` (`architecture`, `core`).
- **Supplemental diagrams**: none.
- **Contracts**: provides `contract.concorde.workflow`; requires `contract.concorde.spec-kit-platform`.
- **Architecture view**: `specs/concorde/architecture.json`.
- **Evidence status**: `partial` — existing evidence covers the previous two-document model; the
  TL;DR tier and the feature-root rename have no realization yet.
