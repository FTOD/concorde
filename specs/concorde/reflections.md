# Reflections: Concorde

The project's one reflection log: every difficulty or problem a coding agent met while planning or
implementing any feature, attributed to the feature being worked on and naming the source the
problem concerns. Grammar:
[reflection-log contract](features/005-record-workflow-reflections/contracts/reflection-log.md).
Kept by hand under constitution B.II until the rule Feature 005 specifies is installed.

### R-001 · Self-hosting cannot refresh the Claude integration used by this checkout

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: tooling
- **Concerns**: feature.concorde.self-host-framework
- **Expected**: `scripts/development/self-host-concorde.py status` reports the freshness of this
  checkout's installed Concorde surfaces so a framework change can be refreshed and counted as used.
- **Observed**: Status returns `unknown` with `CONCORDE-SELF-HOST-005: Integration 'claude' has no
  self-hosting surface evidence in protocol v1`; `.specify/integration.json` selects `claude`.
- **Effect**: worked-around
- **Action**: Planned the refresh through Spec Kit's public development-mode install plus the
  installed-surface byte-equality test (Feature 005 research D7) instead of the self-hosting tool.
- **Improvement**: Extend Feature 004's surface evidence and drift check to the Claude integration.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-28 feature.concorde.record-workflow-reflections — refreshed the mirrors with
    `specify preset remove concorde-core` + `specify preset add --dev … --priority 10` and
    `specify extension add … --dev --force` (plain `preset add` refuses an installed preset); byte
    equality proven by `diff -r` and `test_installed_command_surfaces`; a new agent session is
    still required before the refreshed skills are active.

### R-002 · Plan and tasks guidance disagree on whether an attempt may edit `module.md`

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: guidance
- **Concerns**: presets/concorde-core/templates/tasks-template.md
- **Expected**: One rule for module-summary edits during an attempt.
- **Observed**: The tasks append layer says to include tasks that update "module registrations" and
  the "current-level Archify JSON", and also says not to generate a task that edits "any module
  `module.md`"; the plan append layer forbids editing `tldr.md`, `spec.md`, the feature
  `design.md`, and a module `design.md` but not `module.md`.
- **Effect**: assumed
- **Action**: Planned the `architecture.json` change as an implementation task and the `module.md`
  prose reconciliation as a maintainer-approved edit presented before it is applied (research D8).
- **Improvement**: State in both append layers that a level view and a module summary may change
  inside an attempt only as a reviewed architecture change presented for approval.
- **Status**: open

### R-003 · The specification contradicted the root view once the maintainer's request landed

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: specification
- **Concerns**: specs/concorde/features/005-record-workflow-reflections/spec.md#concorde-architecture-alignment
- **Expected**: The alignment section describes the root view's relationship to the feature
  durably.
- **Observed**: It stated the root view "is not amended by this specification; drawing this feature
  in the root view is planned work", which becomes false when research D8 adds the node, and an
  attempt may not edit `spec.md`.
- **Effect**: deferred
- **Action**: Left `spec.md` unchanged during planning; the 2026-08-28 specification revision
  (R-004) reworded the bullet to "the root view shows this feature as a root feature node".
- **Improvement**: Keep alignment prose descriptive of the intended end state, not of pending work.
- **Status**: resolved
- **Note**: Resolved on 2026-08-28 by the specification revision that accompanied R-004; the
  `module.md` "not yet drawn" sentence is still reconciled by task T036.

### R-004 · A per-attempt log could not hold problems about other features' implementations

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: specification
- **Concerns**: specs/concorde/features/005-record-workflow-reflections/spec.md#functional-requirements
- **Expected**: FR-003 placed the reflection log inside each attempt's `implementation/`
  directory, removed at hardening with a per-entry disposition.
- **Observed**: The maintainer pointed out that problems met while implementing a feature usually
  concern existing implementations, often of other features; a per-attempt file scatters the same
  problem across roots and deletes it with the attempt.
- **Effect**: worked-around
- **Action**: Revised the specification, TL;DR, plan, research, data model, contract, quickstart,
  and tasks on 2026-08-28: one project-wide log at the specification root, entries attributed to
  the selected feature with a free `Concerns` target, no removal at hardening, and a citation rule
  instead of dispositions; moved this attempt's entries here.
- **Improvement**: When a record serves cross-feature review, specify it at the level where all
  the things it can concern are visible (the root), not at the feature.
- **Status**: resolved
- **Note**: Resolved by the 2026-08-28 revision of Feature 005 (spec.md "Revised" line).

### R-005 · The root view cannot draw the feature's crossing into Spec Kit Integration

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: architecture
- **Concerns**: specs/concorde/architecture.json
- **Expected**: Research D8 planned three governed crossings for the new root feature node: from
  the coding agent, into Spec Kit Integration (guidance and log path), and into Architecture Core.
- **Observed**: With Architecture Core placed between the feature column and Spec Kit Integration,
  every route from the new node up to Integration crosses the existing workflow → Architecture Core
  edge or the Integration → Core corridor; Archify showcase validation reports proper crossings and
  ambiguous corridors for each variant tried.
- **Effect**: worked-around
- **Action**: Drew two crossings (agent → feature over `contract.concorde.workflow`, feature →
  Architecture Core over `contract.core.architecture-services`) and stated Integration's guidance
  role in the feature's sublabel and the root card; the feature's own core diagram shows all parts.
- **Improvement**: Reconsider the root view's column order (features, then Integration, then Core)
  or allow Archify to route around the right edge so both realizing modules can be drawn.
- **Status**: open

### R-006 · Analysis is specified as strictly read-only but must record problems

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: specification
- **Concerns**: feature.concorde.workflow.execute-and-reconcile
- **Expected**: FR-001 of this feature requires recording through the analysis phase, while FR-004
  of the execute-and-reconcile sub-feature and the `speckit.analyze` instruction make analysis
  strictly read-only.
- **Observed**: Both cannot hold literally; the analysis instruction had to name one exception.
- **Effect**: assumed
- **Action**: Made appending to the project reflection log the single permitted write of the
  analysis phase in `presets/concorde-core/commands/speckit.analyze.md`; nothing else changed.
- **Improvement**: Reconcile FR-004 of `feature.concorde.workflow.execute-and-reconcile` (and its
  SC-002 "zero filesystem changes") with this exception through specification review of that root.
- **Status**: open

### R-007 · The docsite rejects TL;DR links to the contract, its example, and the project log

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: tooling
- **Concerns**: docsite/plugins/concorde-content/validation.ts
- **Expected**: `npm run validate` and `npm run build` accept the feature page; the TL;DR's Read
  Next links point readers at the log grammar, the example, and the actual project log.
- **Observed**: The docsite reports `link.target.excluded` for the three links in `tldr.md`
  (`contracts/reflection-log.md`, `contracts/examples/reflections.md`, `../../reflections.md`)
  because those files are non-canonical Spec Kit artifacts that the site does not publish, and the
  build stops; sibling TL;DRs avoid this by naming such files in backticks instead of linking.
- **Effect**: blocked
- **Action**: Halted task T039 (docsite freshness). The fix is a three-line change to `tldr.md`
  (link → backtick path), which implementation may not make; presented to the maintainer for
  approval as a specification-tier edit.
- **Improvement**: Let the specify guidance say that a TL;DR may link only to published canonical
  sources, or let the docsite publish feature contracts and the project log as repository assets.
- **Status**: open

