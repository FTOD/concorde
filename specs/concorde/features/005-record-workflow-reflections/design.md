---
id: feature.concorde.record-workflow-reflections
kind: feature
module: module.concorde
refines: []
scenarios: []
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
diagrams:
  - source: specs/concorde/features/005-record-workflow-reflections/diagrams/workflow-reflection-components.json
    role: core
    kind: architecture
    scenarios:
      - record-during-planning-and-implementation
      - review-and-improve
      - carry-lessons-through-acceptance
    output: generated/architecture/workflow-reflection-components.html
evidence_status: unknown
canonical_design: specs/concorde/features/005-record-workflow-reflections/design.md
---

# Feature Design: Record Workflow Reflections

**Read first**: [abstract.md](abstract.md) — the self-contained abstract of this feature. **Accepted
realization**: [implementation.md](implementation.md) — consulted when writing the code or fixing a bug.

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-28

**Revised**: 2026-08-28 — the log is project-wide, not per attempt

**Status**: Draft

**Input**: User description: "I want a new feature to the project. I want the project to have
self-reflection, or self-improvement, which means, during the planning or implementation stage, if
the agent sees difficulties or problems, the agent should write down these problems. The problem
should be recorded in the files. No extra commands are required." Revision (2026-08-28): "The
reflection files should not be in the feature's implementation folder, it should be global (because
the problems met when trying to implement a feature is usually related to existing implementations
even concerning other features)."

## Outcome

Whenever a coding agent working inside the Concorde workflow — planning an attempt, ordering its
tasks, executing them, analyzing consistency, or converging remaining work — meets a difficulty or
problem it cannot resolve as the specification, the accepted design, the installed guidance, or the
plan expects, it records that problem as a structured entry in the project's one reflection log, a
maintained, version-controlled file at the specification root. It does so through the phases that
already exist, with no new command, without touching any other durable document, and without
stopping work that can continue. Each entry says which feature was being worked on and which source
— in that feature, in another feature's existing implementation, in a module, in the guidance, or in
a tool — the problem is about. A maintainer reads the log to improve the specification, the
architecture, the guidance, or the tooling; acceptance cites the attempt's entries in the design
reference; and the log itself outlives every attempt.

## Reflection Boundary

The workflow already tells an agent what to read, what to write, and what it may never edit. What
it lacks is a place for the agent to say *this did not work as described*. Today such observations
are scattered across chat transcripts, commit messages, or an ad-hoc paragraph in `research.md`,
and they disappear when the attempt is accepted. This feature gives them one home and one lifecycle:

- **One log for the whole project.** A problem met while implementing one feature is usually about
  something that already exists — another feature's realization, a module boundary, a contract, an
  installed instruction, a tool. A per-feature or per-attempt file would scatter the same problem
  across roots and delete it with the attempt. The log therefore lives once, at the specification
  root, beside the root module summary; every entry names the feature that was being worked on
  (`Feature`) and the source the problem concerns (`Concerns`), which may be anywhere in the project.
- **During an attempt** the agent appends entries as problems are met. The log is the only
  maintained document an agent may extend in response to a problem with a durable document; the
  durable document itself stays untouched.
- **Between attempts** the maintainer reads, resolves, or dismisses entries in place and makes the
  actual improvement through the normal path: specification review for a specification problem, an
  architecture change for a placement or contract problem, a change to the installed guidance or
  runtime for a guidance or tooling problem.
- **At acceptance** the proposal presents the entries recorded for the feature by status; resolved
  entries that shaped the realization are cited among the design reference's decisions, and every
  still-open entry is cited among its known limitations. Acceptance never removes or rewrites the log.

For the Concorde project itself, entries about guidance and tooling are the feedback loop the
constitution's self-application principle asks for: they are the concrete, cumulative list of what
the framework got wrong while developing itself.

The feature adds no command surface. The recording obligation, the log's shape, and the acceptance
citation rule are carried by the phases, templates, and operations the workflow already has.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: `diagrams/workflow-reflection-components.json` is the `role: core` Archify
  architecture view. It answers: which parts of the workflow produce, hold, review, check, and
  cite a reflection entry, and which boundaries the entry crosses on the way?
- **Components and crossings**: The view shows the coding agent, the maintainer, the Spec Kit phase
  surfaces after specification (plan, tasks, implement, analyze, converge), this feature, the
  selected feature's durable specification (`abstract.md` + `design.md`, cited and never edited), the
  project reflection log at the specification root, the feature design reference (`implementation.md`), and
  deterministic validation, feature acceptance, and the level's module design reference. Every
  crossing from the phases and operations into maintained sources is governed by
  `contract.concorde.workflow`; the host phase behavior is required through
  `contract.concorde.spec-kit-platform`.
- **Supplemental decisions**: None. The order of events inside one phase (meet the problem, record
  it, continue or stop) is fully carried by the scenarios below; a lifecycle view of entry statuses
  is not needed for three states.
- **Generated view**: `generated/architecture/workflow-reflection-components.html`.

The diagram supplements this specification. It does not replace the root one-level architecture in
`specs/concorde/architecture/diagrams/level-view.json`, does not redefine the modules that realize the workflow, and
does not add a scenario to the root view: the root view already uses its five guided scenario
slots, so this feature's three journeys are drawn only in its own core view.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a Difficulty While Planning (Priority: P1)

As a coding agent planning an implementation attempt, I can write down a difficulty I meet in the
specification, the accepted design, another feature's existing realization, the level's
architecture, or the planning guidance, so that the plan carries my assumption openly and the
maintainer sees the problem instead of discovering it in the code.

**Why this priority**: Planning is where most specification gaps and conflicts with existing
implementations surface first. If they are silently absorbed as assumptions, every later phase
inherits an invisible decision.

**Independent Test**: Seed a project whose selected feature specification contains one ambiguous
requirement, one requirement that conflicts with another feature's accepted design reference, and
one planning instruction that cannot be followed in the project's setup. Run planning and verify
that the project log holds three entries of the matching kinds, each attributed to the selected
feature and the second concerning the other feature, that the plan proceeds under stated
assumptions, that no other durable document changed, and that the planning completion report lists
the three entries.

**Acceptance Scenarios**:

1. **Given** a requirement that admits two materially different readings, **When** planning reaches
   it, **Then** the agent records an entry of kind `specification` naming the requirement, the two
   readings, the reading it assumed, and the effect `assumed`, and continues planning.
2. **Given** a requirement that cannot be satisfied without changing another feature's accepted
   realization or breaching a declared boundary contract, **When** planning detects the tension,
   **Then** the agent records an entry of kind `architecture` or `implementation` whose `Concerns`
   names that other feature, design reference, or contract, and the plan's architecture gate lists
   the entry as an open question for the maintainer rather than resolving it unilaterally.
3. **Given** installed planning guidance that refers to an artifact or step that does not exist in
   this project, **When** the agent cannot follow it, **Then** the agent records an entry of kind
   `guidance` citing the exact instruction and what it did instead.
4. **Given** a project that has no reflection log yet, **When** the first phase that meets a
   problem records it, **Then** the log is created at the specification root from the template and
   holds the entry.

---

### User Story 2 - Record a Problem While Implementing (Priority: P1)

As a coding agent executing tasks, I can write down a problem — a task that cannot be completed as
planned, existing code of another feature that behaves differently from its design reference, a tool
or runtime that fails or misleads, a missing dependency, a workaround I had to take — in the same
phase in which I meet it, so that my workaround is reviewable and the next attempt, on any feature,
does not repeat the discovery.

**Why this priority**: Implementation is where guidance, tooling, environment, and cross-feature
problems appear, and where an unrecorded workaround becomes silent technical debt.

**Independent Test**: Seed an attempt whose task list includes one task that a validation tool
rejects for a reason the guidance does not explain, one task blocked by a missing dependency, one
task that exposes existing code of another feature disagreeing with that feature's design reference,
and one task where the agent must choose between two acceptable implementations. Run
implementation and verify that each situation produces an entry with the required fields in the
same phase, that the non-blocking cases complete with the effect stated, that the blocking case stops
with the stop reason recorded, and that a repeated encounter with the same problem — even from a
different feature — updates the existing entry rather than adding a duplicate.

**Acceptance Scenarios**:

1. **Given** a tool the guidance told the agent to run fails or contradicts the guidance, **When**
   the agent works around it, **Then** the log gains an entry of kind `tooling` with the command,
   the observed result, the workaround, and the effect `worked-around`.
2. **Given** a task cannot proceed because a dependency, permission, or fixture is unavailable,
   **When** the agent must stop, **Then** it records an entry with the effect `blocked` and the
   stop reason before halting, and the halt follows the existing stop rules unchanged.
3. **Given** existing code or tests of another feature disagree with that feature's design
   reference, **When** the agent discovers it, **Then** it records an entry of kind
   `implementation` whose `Concerns` names the other feature or its design reference, and does not
   edit that feature's durable documents.
4. **Given** the agent meets a problem already recorded — by this attempt or by an earlier one on
   any feature — **When** it would record it again, **Then** it updates the existing entry with the
   new occurrence and feature instead of creating a second entry.
5. **Given** the implementation phase completes, **When** it reports, **Then** the report lists the
   entries added during the phase and the number of open entries attributed to the feature.
6. **Given** analysis runs over the attempt, **When** it reports inconsistencies, **Then** it also
   lists the open entries attributed to the feature and flags any entry whose referenced source has
   changed since the entry was recorded.

---

### User Story 3 - Review Reflections and Improve the Project (Priority: P2)

As a maintainer, I can read every recorded problem of the project from one place, filter it by
feature or by the source it concerns, decide what to do about each one, and see that decision
recorded, so that the specification, the architecture, the guidance, and the tooling improve from
what the agents actually experienced across all features.

**Why this priority**: The log is only useful when a human acts on it. Without a review path the
feature produces a diary, not improvement.

**Independent Test**: Starting from a log with open entries of every kind attributed to two
features, resolve one through specification review, one through an architecture change, one
through a guidance change, dismiss one with a note, and leave one open. Verify that each entry's
status and resolution note are correct, that the resolved entries reference the change that resolved
them, that nothing was deleted, and that the maintainer could find all open entries for one feature
and all entries concerning one module within two minutes from the root module summary.

**Acceptance Scenarios**:

1. **Given** an open `specification` entry, **When** the maintainer runs specification review and
   the specification changes, **Then** the entry is marked `resolved` with a note pointing at the
   revised requirement, and the log keeps the original problem statement.
2. **Given** an open `guidance` or `tooling` entry in the Concorde project itself, **When** the
   maintainer accepts it, **Then** it is recorded as planned framework work or resolved by a
   framework change, and that change counts as used only after the self-hosted installation is
   refreshed.
3. **Given** an entry the maintainer judges not worth acting on, **When** it is dismissed, **Then**
   it stays in the log with status `dismissed` and the reason.
4. **Given** a maintainer who has not followed the recent attempts, **When** they open the root
   module summary, **Then** the location of the log and the count of open entries per feature are
   discoverable without reading any plan or task list.

---

### User Story 4 - Carry the Attempt's Lessons Through Acceptance (Priority: P2)

As a maintainer accepting a milestone, I can see every entry recorded for the feature and its status
before the attempt is removed, so that the resolved lessons that shaped the realization reach the
design reference and every open problem is stated as a known limitation, while the log itself stays
intact for the next attempt on any feature.

**Why this priority**: Acceptance deletes the attempt and writes the design reference in full; it is
the moment the attempt's experience must be reflected in the accepted realization.

**Independent Test**: Accept an attempt whose feature has resolved, dismissed, and open entries in
the project log, alongside entries attributed to other features. Verify that the proposal presents
the feature's entries by status, that the accepted design reference cites the realization-shaping
resolved entries among its decisions and every open entry among its known limitations, that an open
entry the candidate does not cite prevents apply, that entries of other features are untouched and
unlisted, and that the log is byte-identical after apply.

**Acceptance Scenarios**:

1. **Given** a resolved entry that changed how the feature is realized, **When** acceptance drafts
   the feature design reference, **Then** the decision appears among its durable implementation
   decisions citing the entry's identifier.
2. **Given** an open entry attributed to the feature at acceptance time, **When** the proposal is
   presented, **Then** the entry appears among the feature's known limitations with its identifier,
   and when it concerns the level's guidance, tooling, or architecture, also in the module design
   reference amendment as planned work.
3. **Given** an open entry attributed to the feature that the candidate design reference does not
   cite, **When** apply is requested, **Then** apply is refused with a finding naming the entry, and
   the attempt is preserved.
4. **Given** the maintainer approves the proposal, **When** apply completes, **Then** the attempt is
   removed, the log is unchanged, and every entry of the feature remains readable in the log with its
   status.

---

### User Story 5 - Detect a Malformed Log Deterministically (Priority: P3)

As a reviewer, I can rely on deterministic validation to tell me when the project log is malformed —
a missing field, a duplicate identifier, an invalid status, an entry attributed to an unknown
feature, an unresolvable reference — so that the log stays machine-checkable and trustworthy without
a human reading every entry.

**Why this priority**: The log feeds acceptance and review; a malformed log would let entries be
silently ignored. It is P3 because the core value exists once entries are written at all.

**Independent Test**: Seed logs with one breach of each shape rule and one well-formed log. Run
validation twice and verify that each breach produces exactly one actionable finding, that the
well-formed log produces none, that no file was rewritten, and that both runs are byte-equivalent.

**Acceptance Scenarios**:

1. **Given** an entry missing a required field or using an unknown kind, effect, or status,
   **When** validation runs, **Then** it reports the entry, the rule, and the remedy without editing
   the log.
2. **Given** two entries with the same identifier, an entry attributed to a feature that does not
   exist, or an entry referencing a source that does not resolve, **When** validation runs, **Then**
   each is a separate finding.
3. **Given** the project has no reflection log, **When** validation runs, **Then** it reports nothing
   about reflections; an absent log is not a breach.

### Edge Cases

- The agent works on a sub-feature: the entry is attributed to the sub-feature's own stable ID;
  a problem about the parent's specification names the parent requirement in `Concerns`.
- A problem is met and resolved by the agent within the same phase (for example, a flaky tool that
  succeeds on retry): it is still recorded, with status `resolved` and the resolution noted.
- The same underlying problem appears in planning and again in implementation, or in two
  different features' attempts: one entry, several recorded occurrences naming phase and feature.
- The maintainer edits the log by hand between phases: agents treat the maintainer's status and
  notes as authoritative and never reverse them.
- An entry would contain a secret, a credential, or a large raw log: the entry cites the evidence
  file or the redacted location instead.
- The attempt is discarded without acceptance: the entries stay in the log with their statuses;
  nothing is lost and nothing needs archiving.
- Guidance is refreshed while an attempt is in progress: entries recorded against the previous
  guidance keep their original citation and are flagged by analysis as referencing changed sources.
- Two agents work on two features at once and both append: entries are appended, never renumbered;
  a version-control merge conflict on the log is resolved by keeping both entries and renumbering
  the later one.
- A project adopting Concorde never meets a problem worth recording: no log exists and validation
  reports nothing.
- The log grows over years: entries stay short (FR-014); a maintainer may move `resolved` and
  `dismissed` entries under an `## Archive` heading in the same file, which validation still checks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST let a coding agent record difficulties and problems through the
  existing planning, task-ordering, implementation, analysis, and convergence phases, and MUST NOT
  introduce a new command surface, a new approval step, or a runtime dependency on the Concorde
  checkout for this purpose.
- **FR-002**: A difficulty or problem is anything that prevents the agent from following the
  specification, the accepted design reference, an existing implementation it depends on, the
  installed guidance, the level's architecture, or the plan as written, or that forces it to
  assume, work around, defer, or stop. The agent MUST record each such problem in the phase in
  which it is met and before that phase reports completion.
- **FR-003**: The project MUST hold exactly one reflection log at `reflections.md` directly inside
  the specification root (beside the root module summary). The first phase that records a problem
  MUST create a missing log from the installed template; every phase MUST reach it through the
  path the workspace result returns, never through a per-feature or per-attempt copy.
- **FR-004**: Every entry MUST carry: a stable identifier unique within the log; the phase and date
  it was recorded; the stable ID of the feature or sub-feature that was selected when it was
  recorded (`Feature`); exactly one kind; the source it concerns (`Concerns`), as a stable ID or a
  repository-relative location anywhere in the project that resolves; the problem as expected versus
  observed; the effect on the work, one of `assumed`, `worked-around`, `deferred`, or `blocked`,
  with what the agent did; a suggested improvement; and a status, one of `open`, `resolved`, or
  `dismissed`, with a resolution note when not `open`.
- **FR-005**: The kinds MUST be `specification` (an ambiguous, missing, or contradictory
  requirement), `architecture` (a placement, boundary, contract, or view problem), `guidance` (an
  installed instruction or template that is unclear, wrong, or impossible to follow), `tooling` (a
  command, runtime, validator, or generator that fails or misleads), `environment` (a missing
  dependency, permission, fixture, or host capability), and `implementation` (existing code or tests
  that disagree with their design reference, or a trade-off, workaround, or known debt the agent
  chose).
- **FR-006**: Recording MUST NOT halt a phase that can otherwise continue. When a problem blocks the
  phase, the agent MUST record it with the effect `blocked` and the stop reason before halting, and
  the existing stop and review rules of that phase remain unchanged.
- **FR-007**: Recording MUST NOT edit `abstract.md`, `design.md`, any `implementation.md`, any `module.md`,
  contracts, level views, feature diagrams, or another feature's code or tests. A problem with a
  durable document or an existing implementation is recorded; the source is changed only through the
  phase or operation that owns it.
- **FR-008**: When a recorded problem is met again — in any phase, on any feature — the agent MUST
  update the existing entry with the new occurrence (phase, date, feature) rather than add a
  duplicate. Agents MUST NOT delete entries, renumber existing entries, or reverse a status or note
  set by the maintainer; a status change MUST preserve the original problem statement.
- **FR-009**: Every phase that records into the log MUST list the entries it added and the number
  of open entries attributed to the selected feature in its completion report. Analysis MUST list
  those open entries and flag any entry whose referenced source changed after the entry was
  recorded. Convergence MUST treat an open entry attributed to the feature with the effect
  `deferred` as candidate remaining work only when it is genuine remaining work of the feature, and
  MUST NOT create work for dismissed entries.
- **FR-010**: A maintainer MUST be able to resolve or dismiss any entry by editing the log directly,
  recording the note and, for a resolved entry, a reference to the change that resolved it.
- **FR-011**: The acceptance proposal MUST present every entry attributed to the feature with its
  status. The candidate feature `implementation.md` MUST cite the identifier of every such entry that is
  still `open` among its known limitations, and SHOULD cite resolved entries that shaped the
  realization among its decisions; entries whose lesson concerns the level's guidance, tooling, or
  architecture MAY additionally be cited in the module `design.md` amendment. Apply MUST refuse
  while an open attributed entry is not cited, and MUST NOT modify or remove the log.
- **FR-012**: Deterministic validation MUST check a present reflection log read-only for unique
  identifiers, required fields, permitted kind, effect, and status values, an attributed feature
  that resolves, and concerned sources that resolve, reporting each breach as a finding with rule,
  location, and remedy, never rewriting the log, and reporting nothing when no log exists.
- **FR-013**: Recording MUST stay inside the selected root's bounded context for what it reads: an
  entry MAY concern any feature, module, contract, guidance, tool, or file in the project by stable
  ID or path, but the agent MUST NOT open a parent, sibling, or other feature's attempt to record it,
  and MUST write nothing outside the log and the selected root's attempt.
- **FR-014**: An entry MUST NOT contain secrets, credentials, or bulk raw output; it MUST cite the
  evidence location instead, and its problem statement SHOULD stay under 150 words so that a log
  remains reviewable in minutes.
- **FR-015**: The installed phase guidance and the log template MUST carry the recording obligation,
  the log's shape, and the acceptance citation rule, so that any project installed through Spec Kit
  obtains this behavior without a Concorde checkout.
- **FR-016**: The reflection log MUST be a maintained, version-controlled source that no workflow
  operation removes, that acceptance leaves byte-identical, and that this feature does not publish;
  generated sites and reports MAY link to it but MUST NOT treat it as a specification, design
  reference, or contract.
- **FR-017**: In the Concorde project itself, an accepted `guidance` or `tooling` entry MUST be
  recorded as planned framework work or resolved by a framework change, and that change MUST be
  refreshed through the self-hosted installation before it counts as used in Concorde's own
  development evidence.

### Key Entities

- **Reflection Log**: The project's one maintained, version-controlled file at the specification
  root that holds every problem any agent met during any attempt; created by the first recording
  phase, never removed by the workflow.
- **Reflection Entry**: One recorded problem with its identifier, phase, date, attributed feature,
  kind, concerned source, expected-versus-observed statement, effect, suggested improvement, status,
  resolution note, and occurrence history.
- **Attributed Feature**: The stable ID of the feature or sub-feature selected when the entry was
  recorded; the key by which acceptance and phase reports select "the feature's entries".
- **Concerned Source**: The stable ID or path the problem is about — possibly a different feature,
  its design reference or code, a module, a contract, an installed instruction, or a tool.
- **Kind**: The classification that tells the maintainer which authority the problem is about:
  specification, architecture, guidance, tooling, environment, or implementation.
- **Effect**: What the problem did to the work: the agent assumed, worked around, deferred, or was
  blocked.
- **Phase Completion Report**: The existing end-of-phase summary, extended with the entries added
  and the count still open for the feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance fixtures that seed one problem of each of the six kinds into planning
  and implementation runs on two different features, 100% produce an entry with every required
  field in the one project log, attributed to the selected feature, during the phase in which the
  problem was met.
- **SC-002**: The number of command surfaces offered by the workflow is unchanged by this feature,
  and no phase acquires a new approval prompt.
- **SC-003**: A maintainer who has not followed recent attempts finds every open entry for one
  feature, and every entry concerning one module, within two minutes of opening the root module
  summary, and reviews a log of ten entries in under ten minutes.
- **SC-004**: At acceptance, 100% of the feature's entries are presented with their status; 100% of
  its open entries are cited in the accepted design reference; zero attempts are removed while an
  open attributed entry is uncited; and the log is byte-identical before and after apply in 100% of
  fixtures.
- **SC-005**: In fixtures with only non-blocking problems, 100% of phases complete with their
  entries recorded; in fixtures with a blocking problem, 100% of halts have the stop reason recorded
  before the halt.
- **SC-006**: Deterministic validation detects 100% of seeded shape breaches (missing field,
  duplicate identifier, invalid kind, effect, or status, unknown attributed feature, unresolvable
  reference), reports none for a well-formed or absent log, and is byte-equivalent on repeat.
- **SC-007**: Recording changes zero documents other than the log, and zero contracts, views,
  diagrams, or other features' code, in 100% of fixtures.
- **SC-008**: Re-encountering an already recorded problem — from the same or another feature —
  yields zero duplicate entries in 100% of fixtures, and no maintainer-set status or note is
  reversed by an agent.
- **SC-009**: 100% of phase completion reports in fixtures list the entries the phase added and the
  count of open entries attributed to the feature.

## Scope

### In Scope

- The recording obligation in planning, task ordering, implementation, analysis, and convergence.
- The one project-wide log: its location, entry shape, attribution, kinds, effects, statuses, and
  de-duplication rule across features.
- Surfacing of the feature's entries in phase completion reports, analysis, and the root module's
  bounded context.
- Maintainer resolution and dismissal directly in the log.
- Citation of the feature's entries at acceptance and the refusal to remove an attempt while an
  open attributed entry is uncited.
- Deterministic shape validation of a present log.
- The self-application loop for guidance and tooling entries in the Concorde project.

### Out of Scope

- A new command, skill, or slash command for recording, listing, filtering, or resolving entries.
- Automatic resolution of problems by the agent, including editing durable documents or another
  feature's code in response to an entry.
- Per-module or per-feature reflection files, a database, a dashboard, or a published page.
- Automatic archiving or pruning of old entries.
- Judging whether an entry is a faithful account of what happened; that remains a review
  responsibility.
- Sending entries to any external service.

## Assumptions

- The log is a Markdown file with one section per entry so that both humans and agents can read
  and edit it without tooling; its exact layout is fixed by the installed template and the
  reflection-log contract.
- Identifiers are allocated sequentially across the whole log (for example `R-001`, `R-002`) and are
  stable for the life of the project because design references cite them.
- The existing practice of recording rationale and implementation detail in `research.md` and
  `validation.md` continues; the reflection log holds problems, not every decision. An entry may
  point to those files for detail.
- Phase completion reports already exist for every phase in scope; this feature extends their
  content rather than adding a report.
- Deterministic validation already reads every maintained source under the specification root and
  can add one more file there.
- The maintainer reviews the log at the latest at acceptance; the feature does not remind them
  earlier.
- Concurrent appends by two agents are rare; version control, not the workflow, arbitrates them.

## Dependencies

- `feature.concorde.workflow` and its sub-features `plan-delivery`, `execute-and-reconcile`,
  `validate-architecture`, and `accept-milestone`, whose phase behavior this feature extends and whose
  specifications must be reconciled with FR-003, FR-009, FR-011, and FR-012.
- `feature.concorde.workflow.specify-behavior` for the specification review through which a
  `specification` entry is resolved.
- `feature.concorde.workflow.retrieve-bounded-context` for exposing the log's location and open
  counts in the root level's bounded context (US3 scenario 4).
- `feature.concorde.self-host-framework` for refreshing framework changes that resolve `guidance`
  or `tooling` entries in the Concorde project (FR-017).
- `contract.concorde.workflow` for the phase and operation boundary the log crosses, and
  `contract.concorde.spec-kit-platform` for the host phase lifecycle that carries the recording
  obligation.
- The installed template set of the `concorde-core` preset, which will carry the log template.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.record-workflow-reflections`
- **Providing module**: `module.concorde`; the behavior is realized by Spec Kit Integration
  (phase guidance and templates) and Architecture Core (validation, context, and acceptance), both
  visible at this level; the log itself is a root-level maintained source beside `module.md`.
- **Decomposition decision**: atomic. The feature is one obligation with one artifact and one
  citation rule; splitting it by phase would duplicate the entry shape in every child.
- **Feature containment**: none; this feature has no sub-features.
- **Authority split**: this specification owns the log's location, shape, attribution, lifecycle,
  and acceptance citation rule; the workflow sub-features it extends keep ownership of their phase
  behavior and must be reconciled with the requirements above rather than restating them.
- **Observable textual outcome**: the Outcome section.
- **Parent refinement**: none; this is a root-level feature.
- **Representative scenarios**: `record-during-planning-and-implementation`, `review-and-improve`,
  and `carry-lessons-through-acceptance`, drawn as guided views of the core diagram. The root view
  shows this feature as a root feature node; its scenarios are drawn only in the feature's core
  view because the root view's five guided scenario slots are full.
- **Core feature diagram**: `diagrams/workflow-reflection-components.json` (`architecture`,
  `core`).
- **Supplemental diagrams**: none.
- **Contracts**: provides `contract.concorde.workflow`; requires
  `contract.concorde.spec-kit-platform`.
- **Level views**: the root module's diagrams under `specs/concorde/architecture/diagrams/`
  (`level-view.json`).
- **Evidence status**: `unknown`; no implementation exists yet.
