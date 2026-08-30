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
      - investigate-and-route
      - implement-and-merge
      - install-supported-projections
    output: generated/architecture/workflow-reflection-components.html
evidence_status: partial
canonical_design: specs/concorde/features/005-record-workflow-reflections/design.md
---

# Feature Design: Record and Triage Workflow Reflections

**Read first**: [abstract.md](abstract.md) — the self-contained abstract of this feature. **Accepted
realization**: [implementation.md](implementation.md) — consulted when writing the code or fixing a bug.

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-28

**Revised**: 2026-08-30 — installed subagents turn recorded reflections into reviewed changes

**Status**: Draft

**Input**: User description: "I want a new feature to the project. I want the project to have
self-reflection, or self-improvement, which means, during the planning or implementation stage, if
the agent sees difficulties or problems, the agent should write down these problems. The problem
should be recorded in the files. No extra commands are required." Revision (2026-08-28): "The
reflection files should not be in the feature's implementation folder, it should be global (because
the problems met when trying to implement a feature is usually related to existing implementations
even concerning other features)." Revision (2026-08-30): "Make the specialized reflection
subagents part of Feature 005 and have Concorde installation install the subagent-related parts,
including Codex and Claude projections."

## Outcome

Whenever a coding agent working inside the Concorde workflow — planning an attempt, ordering its
tasks, executing them, analyzing consistency, or converging remaining work — meets a difficulty or
problem it cannot resolve as the specification, the accepted design, the installed guidance, or the
plan expects, it records that problem as a structured entry in the project's one reflection log, a
maintained, version-controlled file at the specification root. It does so through the phases that
already exist, with no new command, without touching any other durable document, and without
stopping work that can continue. Each entry says which feature was being worked on and which source
— in that feature, in another feature's existing implementation, in a module, in the guidance, or in
a tool — the problem is about. An explicit installed triage workflow then lets a maintainer assign
each open entry to a specialized investigator, persist an evidence-backed route and modification
plan, execute eligible plans with specialized implementers in isolated worktrees, and merge only
validated commits from a clean checkout. Concorde installation materializes the shared workflow as
the skills, agent roles, helper, and configuration expected by each supported agent platform, so a
project receives the improvement loop rather than this repository's manual setup. Acceptance still
cites the attempt's entries in the design reference, and the log itself outlives every attempt.

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
- **Between attempts** the maintainer may review entries directly or invoke the installed triage
  workflow. Investigators establish root cause and route each entry to a bounded fast-loop change,
  normal specification work, dismissal, or a blocking human decision. Implementers execute only
  eligible plans through the normal feature workspace and validation rules. The maintainer remains
  the authority for merge and for changing an entry's status or note.
- **At acceptance** the proposal presents the entries recorded for the feature by status; resolved
  entries that shaped the realization are cited among the design reference's decisions, and every
  still-open entry is cited among its known limitations. Acceptance never removes or rewrites the log.

For the Concorde project itself, entries about guidance and tooling are the feedback loop the
constitution's self-application principle asks for: they are the concrete, cumulative list of what
the framework got wrong while developing itself.

Automatic recording adds no phase command surface. Reflection improvement is an explicit installed
skill with `status`, `investigate`, `implement`, and `merge` actions because it is a maintainer-led
review workflow, not an implicit side effect of every delivery phase.

## Core Component Diagram and Supplemental Scenario Views

- **Core decision**: `diagrams/workflow-reflection-components.json` is the `role: core` Archify
  architecture view. It answers: which stable parts record a problem, investigate and route it,
  implement an eligible improvement, validate and merge it, and install that workflow for supported
  agent platforms?
- **Components and crossings**: The view shows Concorde installation, installed workflow surfaces,
  the coding agent and maintainer, the project reflection log, the triage orchestrator, investigator
  agents, reflection plans, isolated implementer worktrees, Speckit Fast Loop, deterministic checks,
  and the accepted realization. Phase and triage crossings into maintained sources are governed by
  `contract.concorde.workflow`; host phase and agent projection behavior is required through
  `contract.concorde.spec-kit-platform`.
- **Supplemental decisions**: None. The scenario order is short and described below; the stable
  component split and its installation boundary are the material relationship to visualize.
- **Generated view**: `generated/architecture/workflow-reflection-components.html`.

The diagram supplements this specification. It does not replace the project-level interaction
architecture in `specs/concorde/architecture/diagrams/level-view.json` or redefine the modules that
realize the workflow. The project view shows shared module interactions; this feature's three
behavioral journeys are drawn only in its own core view.

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

### User Story 3 - Triage Reflections with Specialized Agents (Priority: P1)

As a maintainer, I can invoke one installed reflection-triage workflow that assigns open entries to
specialized investigators, gives me a concrete route and modification plan for each entry, executes
eligible plans with specialized implementers in isolated worktrees, and merges validated commits
only when I ask, so that recorded problems become controlled project improvements instead of an
ever-growing backlog.

**Why this priority**: Recording without an execution path identifies debt but does not close the
feedback loop. Specialized read-heavy investigation followed by bounded implementation keeps
expensive diagnosis separate from repeatable changes and preserves maintainer control.

**Independent Test**: Install Concorde into fresh projects for the Claude and Codex integrations,
seed five open entries that route respectively to `fast-loop`, `specify`, `dismiss`, `blocked`, and
a second fast-loop change owned by another feature, then run status, investigation, implementation,
and merge. Verify that each integration exposes the same four actions and plan semantics; every
entry gets exactly one evidence-backed plan; only eligible plans are implemented; different feature
groups use separate worktrees and branches; each successful plan has one commit; merge requires a
clean maintainer checkout and reruns validation; non-implementation routes remain for human action;
and the reflection log's statuses and notes remain maintainer-owned.

**Acceptance Scenarios**:

1. **Given** a project installed with a supported agent integration, **When** installation
   completes, **Then** that integration exposes a reflection-triage entry point, investigator and
   implementer roles, deterministic queue support, and shared workflow configuration without the
   maintainer manually copying repository-local agent files.
2. **Given** open and already planned entries, **When** the maintainer requests `status`, **Then**
   the workflow reports the ordered queue and plan-state counts without modifying the log, plans,
   source tree, or selected feature.
3. **Given** unplanned open entries, **When** the maintainer requests investigation, **Then** the
   orchestrator dispatches at most the configured investigator concurrency, gives exactly one entry
   to each investigator, waits for the entire wave, and persists one plan whose route is exactly
   `fast-loop`, `specify`, `dismiss`, or `blocked`, retrying a missing result at most once.
4. **Given** ready `fast-loop` plans, **When** implementation is requested, **Then** the orchestrator
   checks for overlapping uncommitted work, groups plans by the feature that owns the change, creates
   one isolated worktree and branch per group, supplies the full plans to a specialized implementer,
   runs Speckit Fast Loop and the plan's validation, and records one commit per successful plan.
5. **Given** a plan routed to `specify`, `dismiss`, or `blocked`, **When** implementation is
   requested, **Then** the workflow does not implement it and reports the specification proposal,
   dismissal rationale, or exact human decision that remains.
6. **Given** implemented branches and a clean maintainer checkout, **When** merge is requested,
   **Then** the workflow merges each branch one at a time, stops safely on conflict, runs the
   repository validation required by the plans, removes only successfully merged worktrees and
   branches, marks their plans merged, and suggests—but never applies—the corresponding reflection
   status and note changes.
7. **Given** an investigator or implementer failure, **When** the wave finishes, **Then** successful
   results remain usable, the failed entry or plan is reported with actionable evidence, and no
   unvalidated partial change is merged.

---

### User Story 4 - Review Reflections and Improve the Project (Priority: P2)

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

### User Story 5 - Carry the Attempt's Lessons Through Acceptance (Priority: P2)

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

### User Story 6 - Detect a Malformed Log Deterministically (Priority: P3)

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
- Two investigators finish with the same proposed identifier: the orchestrator serializes plan
  persistence and rejects the duplicate result rather than overwriting either plan.
- Two eligible plans affect the same feature or file: they stay in one ordered implementer group;
  they are never dispatched to competing worktrees.
- The active agent platform supports subagents but not declarative worktree isolation: the
  orchestrator creates the Git worktree explicitly and gives the implementer its exact path.
- A requested agent model is unavailable: installation keeps the role portable and lets the
  platform inherit a supported default; triage reports an unavailable explicitly configured model
  rather than silently selecting an unrelated one.
- A project has local edits in the feature or files named by a ready plan: implementation skips the
  affected group and leaves those edits untouched.
- A worktree implementation succeeds but final repository validation fails after merge: the
  workflow stops, preserves evidence and remaining branches, and does not mark affected reflection
  entries resolved.
- Concorde is installed for more than one supported agent integration in the same project: both
  projections use the same reflection log, queue semantics, and plan state rather than maintaining
  divergent backlogs.
- A project adopting Concorde never meets a problem worth recording: no log exists and validation
  reports nothing.
- The log grows over years: entries stay short (FR-014); a maintainer may move `resolved` and
  `dismissed` entries under an `## Archive` heading in the same file, which validation still checks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST let a coding agent record difficulties and problems through the
  existing planning, task-ordering, implementation, analysis, and convergence phases. Automatic
  recording MUST NOT introduce a new phase command, a new approval step, or a runtime dependency on
  the Concorde checkout; the explicit triage workflow defined below is a separate maintainer action.
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
- **FR-018**: Concorde MUST provide one explicit reflection-triage workflow with the actions
  `status`, `investigate`, `implement`, and `merge`. `status` MUST be read-only; the other actions
  MUST preserve the phase and maintainer authorities defined by this feature.
- **FR-019**: The triage workflow MUST use two specialized roles: an investigator that handles
  exactly one entry and establishes root cause, ownership, route, files, validation, risks, and
  scope; and an implementer that executes complete eligible plans without redesigning them. The
  roles MAY use different model and reasoning defaults, but model choice MUST remain replaceable by
  the installed platform or project configuration.
- **FR-020**: Every investigation MUST produce one plan with the entry identifier and title; route
  `fast-loop`, `specify`, `dismiss`, or `blocked`; lifecycle status; recorded-under and
  implement-in feature identifiers and directories; affected files; documentation impact; effort;
  problem and root-cause evidence; ordered change; exact validation; and risks and exclusions. A
  non-`fast-loop` route MUST contain the proposal, rationale, or blocking question and MUST NOT be
  auto-implemented.
- **FR-021**: Investigation MUST dispatch no more than the configured concurrency, assign exactly
  one open entry to each investigator, wait for every result in a wave, verify that each plan exists
  and has a route, retry a missing plan at most once, and report every success or failure without
  allowing one failed result to erase another successful result.
- **FR-022**: Implementation MUST select only ready `fast-loop` plans according to the configured
  approval policy, reject overlap with uncommitted maintainer work, group compatible plans by the
  feature that owns the change, preserve configured order within a group, and dispatch no more than
  the configured implementer concurrency.
- **FR-023**: Each implementer group MUST run in its own Git worktree and branch, receive the full
  plan text, select the owning Concorde feature, use Speckit Fast Loop for each plan, run the plan's
  validation and the repository-wide checks required by its changes, create one commit per
  successful plan, revert only that plan's edits on bounded failure, and return branch, worktree,
  commit, file, and follow-up-reflection evidence.
- **FR-024**: Merge MUST require a clean maintainer checkout, merge implemented branches one at a
  time, abort and stop on conflict, rerun applicable deterministic repository and documentation
  checks, remove only successfully merged worktrees and branches, and move only their plan records
  to `merged`. It MUST never edit the reflection log's maintainer-owned `Status` or `Note`; it MUST
  instead report suggested updates with the resolving commits.
- **FR-025**: One platform-neutral configuration and deterministic queue helper MUST govern the log
  location, plan location, ordering, investigator and implementer concurrency, approval policy, skip
  list, plan lifecycle, queue selection, and plan metadata updates. Multiple installed agent
  projections in one project MUST share these semantics and state.
- **FR-026**: Concorde installation MUST materialize the triage skill, both specialized roles,
  shared helper, and default configuration for every supported agent integration with native
  subagent support, using that integration's required file formats and locations. Installation and
  upgrade MUST be deterministic and idempotent, MUST include the artifacts in release manifests and
  integrity checks, and MUST remove or replace superseded Concorde-owned projections without
  deleting maintainer-owned plan state or configuration overrides.
- **FR-027**: Investigator work MUST be read-only except for its single plan result; implementer
  writes MUST be confined to its assigned worktree and planned file set. Every child agent MUST
  inherit or narrow the parent permission boundary, and a platform that cannot provide the required
  isolation MUST stop with an actionable diagnostic rather than run parallel writes in the main
  checkout.

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
- **Reflection Plan**: The durable-for-triage proposal associated with one entry, including its
  route, lifecycle status, owning feature, bounded file set, evidence, change steps, validation, and
  implementation branch and commit when applicable.
- **Investigator Role**: A specialized read-heavy subagent that handles exactly one entry and
  produces a plan without changing project sources.
- **Implementer Role**: A specialized execution subagent that receives complete plans for one
  owning feature, works only in its assigned worktree, invokes Speckit Fast Loop, validates, and
  commits one plan at a time.
- **Triage Configuration**: The project-level shared policy for queue order, plan state, agent
  concurrency, approval, and skipped entries, independent of any one agent-platform projection.
- **Agent Projection**: The platform-specific installed representation of the shared triage skill
  and roles, such as the formats consumed by Claude or Codex.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance fixtures that seed one problem of each of the six kinds into planning
  and implementation runs on two different features, 100% produce an entry with every required
  field in the one project log, attributed to the selected feature, during the phase in which the
  problem was met.
- **SC-002**: The number of automatic phase command surfaces is unchanged, no phase acquires a new
  approval prompt, and installed projects expose exactly one explicit reflection-triage entry point.
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
- **SC-010**: Fresh-install fixtures for Claude and Codex contain 100% of the required triage skill,
  role, helper, and default configuration artifacts; a repeated installation produces a
  byte-equivalent managed surface and preserves project-owned triage state.
- **SC-011**: In a queue of ten open entries with configured investigator concurrency of three,
  no more than three investigators run at once, every entry receives exactly one plan or one
  actionable failure, and no successful plan is lost when another investigator fails.
- **SC-012**: In fixtures containing every route, 100% of ready `fast-loop` plans and 0% of
  `specify`, `dismiss`, or `blocked` plans reach an implementer; every successful plan has exactly
  one commit and every failed plan leaves its worktree clean of that plan's edits.
- **SC-013**: In fixtures with two owning features and implementer concurrency of two, the workflow
  uses two distinct worktrees and branches, produces no cross-group file collision, and merges only
  after the maintainer checkout and required validation gates pass.
- **SC-014**: Across Claude and Codex projections, identical log and plan fixtures produce the same
  ordered queue, route lifecycle, eligibility decisions, and merge report fields in 100% of
  contract tests.

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
- The installed reflection-triage workflow, its investigator and implementer roles, plan contract,
  shared queue/configuration support, bounded concurrency, worktree isolation, merge gate, and
  failure reporting.
- Platform-specific Claude and Codex projections of the shared workflow, installed and upgraded
  through Concorde's normal distribution mechanism.

### Out of Scope

- A new command, skill, or slash command for automatic recording or direct status changes in the
  log; the explicit triage skill orchestrates plans and commits but never resolves entries itself.
- Automatically implementing `specify`, `dismiss`, or `blocked` routes, or changing durable intent
  and another feature's accepted sources outside the workflow that owns them.
- Per-module or per-feature reflection files, a database, a dashboard, or a published page.
- Automatic archiving or pruning of old entries.
- Judging whether an entry is a faithful account of what happened; that remains a review
  responsibility.
- Sending entries to any external service.
- Guaranteeing identical model names or native worktree features across agent platforms; the shared
  role contract and observable workflow are portable, while projections use supported local
  capabilities.

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
- The maintainer reviews the log at the latest at acceptance and may invoke triage earlier; the
  feature does not schedule triage automatically.
- Concurrent appends by two agents are rare; version control, not the workflow, arbitrates them.
- The host agent platform exposes bounded subagent delegation and can run Git and the existing
  project validation commands; when native worktree isolation is absent, the orchestrator creates
  ordinary Git worktrees explicitly.
- The shared triage configuration supplies portable defaults, while a maintainer may override
  model and concurrency choices without changing the role contract.

## Dependencies

- `feature.concorde.workflow` and its sub-features `plan-delivery`, `execute-and-reconcile`,
  `validate-architecture`, and `accept-milestone`, whose phase behavior this feature extends and whose
  specifications must be reconciled with FR-003, FR-009, FR-011, and FR-012.
- `feature.concorde.workflow.specify-behavior` for the specification review through which a
  `specification` entry is resolved.
- `feature.concorde.workflow.retrieve-bounded-context` for exposing the log's location and open
  counts in the root level's bounded context (US4 scenario 4).
- `feature.concorde.install-with-spec-kit` for manifesting, releasing, installing, upgrading,
  and integrity-checking the shared triage assets and each supported agent projection (FR-026).
- `feature.concorde.self-host-framework` for refreshing framework changes that resolve `guidance`
  or `tooling` entries in the Concorde project (FR-017).
- `contract.concorde.workflow` for the phase and operation boundary the log crosses, and
  `contract.concorde.spec-kit-platform` for the host phase lifecycle that carries the recording
  obligation.
- The installed template set of the `concorde` preset, which will carry the log template.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.record-workflow-reflections`
- **Providing module**: `module.concorde`; the behavior is realized by Skills (phase guidance,
  templates, triage orchestration, and platform agent projections) and Scripts (validation,
  context, acceptance, and deterministic queue support), both visible at this level; the log itself
  is a root-level maintained source beside `module.md`. Feature 003 carries the installation
  boundary without owning the reflection behavior.
- **Decomposition decision**: atomic. Recording, plan semantics, specialized roles, and merge
  safety form one improvement lifecycle around one project log; splitting the roles into separate
  features would duplicate the queue and plan contract.
- **Feature containment**: none; this feature has no sub-features.
- **Authority split**: this specification owns the log's location, shape, attribution, lifecycle,
  triage actions, agent-role behavior, plan semantics, and acceptance citation rule. Workflow
  sub-features keep ownership of their phases, Speckit Fast Loop keeps ownership of eligibility and
  bounded implementation, and Feature 003 keeps ownership of generic installation and distribution
  mechanics.
- **Observable textual outcome**: the Outcome section.
- **Parent refinement**: none; this is a project-level feature.
- **Representative scenarios**: `record-during-planning-and-implementation`,
  `investigate-and-route`, `implement-and-merge`, and `install-supported-projections`, drawn as
  guided views of the feature's core diagram. The project-level interaction view intentionally
  shows module responsibilities and flows rather than drawing project-level features as peer
  components.
- **Core feature diagram**: `diagrams/workflow-reflection-components.json` (`architecture`,
  `core`).
- **Supplemental diagrams**: none.
- **Contracts**: provides `contract.concorde.workflow`; requires
  `contract.concorde.spec-kit-platform`.
- **Level views**: the project module's diagrams under `specs/concorde/architecture/diagrams/`
  (`level-view.json`).
- **Evidence status**: `partial`; automatic recording has an accepted realization, while installed
  triage roles and projections are the delta proposed by this revision.
