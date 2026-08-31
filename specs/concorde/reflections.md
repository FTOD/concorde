# Reflections: Concorde

The project's remaining open reflection log: unresolved difficulties or problems coding agents met
while planning or implementing a feature, attributed to that feature and naming the source the
problem concerns. Closed entries are removed by explicit maintainer direction. Grammar:
[reflection-log contract](features/005-record-workflow-reflections/contracts/reflection-log.md).
Kept by hand under constitution B.II until the rule Feature 005 specifies is installed.

### R-005 · The root view cannot draw the feature's crossing into Spec Kit Integration

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: architecture
- **Concerns**: specs/concorde/architecture/diagrams/level-view.json
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
- **Occurrences**:
  - implement 2026-08-30 feature.concorde.record-workflow-reflections — triage confirmed the third
    crossing needs a root-view redesign, not a local correction. Select the root architecture
    through its reviewed lifecycle; compare reordering the feature/Integration/Core columns with a
    supported outer-edge corridor, update the level-view JSON and prose together, and require
    Archify crossing diagnostics, showcase validation, and visual review.

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
  analysis phase in `presets/concorde/commands/speckit.analyze.md`; nothing else changed.
- **Improvement**: Reconcile FR-004 of `feature.concorde.workflow.execute-and-reconcile` (and its
  SC-002 "zero filesystem changes") with this exception through specification review of that root.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-30 feature.concorde.record-workflow-reflections — deferred to the owning
    execute-and-reconcile specification lifecycle because it changes the definition of read-only
    analysis. Reconcile FR-004, SC-002, the abstract surface/rules, and aggregate workflow prose so
    the sole write is append-only `workspace.reflections`; add acceptance evidence that a seeded
    problem changes only `reflections.md` and a no-problem run changes zero bytes.

### R-008 · The Documentation refinement still couples both published hierarchies

- **Phase**: plan
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: specification
- **Concerns**: feature.auto-docs.publish-project-docsite
- **Expected**: The Documentation refinement agrees with root Feature 002 that Architecture follows
  module containment while Features follows only feature identity and explicit feature containment.
- **Observed**: FR-DOC-003 still requires both views to preserve the same module/feature hierarchy
  expressed by source paths and IDs, which would retain module-storage categories in Features.
- **Effect**: deferred
- **Action**: Implemented the maintainer-approved root Feature 002 delta without editing the adjacent
  feature's durable sources; the refinement requires its own later specification review.
- **Improvement**: Revise FR-DOC-003 through the Documentation feature's specify lifecycle so it
  requires independent semantic projections from the shared `specs/` packages.
- **Status**: open
- **Occurrences**:
  - plan 2026-08-29 feature.concorde.publish-project-docsite — the root feature now publishes
    `README.md` at `/`, while FR-DOC-004 and the Documentation module's project-content contract still
    describe exactly two accepted source roots; both require their own owning lifecycle update.
  - implement 2026-08-30 feature.concorde.publish-project-docsite — triage confirmed FR-DOC-003 is
    already reconciled. The remaining change is architectural: revise FR-DOC-004 and bump
    `contract.auto-docs.project-content` from v8 to add root `README.md` as a maintainer-provided
    one-file source root with `/` ownership, then align the Auto-Docs abstract/design/implementation
    and contract tests across all three inputs (`README.md`, `docs/`, and `specs/`).

### R-018 · Feature 002's accepted route placeholder was invalid MDX

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: implementation
- **Concerns**: specs/concorde/features/002-create-project-docsite/implementation.md
- **Expected**: The full docsite gate publishes all accepted feature implementations while validating
  the Accept Milestone terminology migration.
- **Observed**: Feature 002 contained bare `/features/<feature-id>` text; MDX parsed `<feature-id>` as
  an unclosed JSX tag and stopped the production build.
- **Effect**: worked-around
- **Action**: Applied a syntax-only correction by formatting the route and adjacent path tokens as
  code spans; no Feature 002 behavior or architecture changed.
- **Improvement**: Require accepted implementation candidates containing angle-bracket placeholders
  to pass the docsite MDX build before milestone acceptance.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-30 feature.concorde.workflow.accept-milestone — the syntax incident is fixed
    and production publication exercises accepted implementations. Making the docsite build a
    generic milestone-acceptance prerequisite would couple Feature 001 acceptance to Feature 002
    publication; define that cross-feature gate through the owning workflow architecture before
    changing acceptance behavior.

### R-034 · Global identity cleanup conflicts with append-only reflection history

- **Phase**: plan
- **Date**: 2026-08-30
- **Feature**: feature.concorde.install-with-spec-kit
- **Kind**: specification
- **Concerns**: feature.concorde.record-workflow-reflections
- **Expected**: The maintainer-requested preset rename leaves no tracked path or content using the
  retired preset identifier.
- **Observed**: The project reflection log contains historical occurrences while its normal agent
  contract is append-only and prohibits rewriting existing entries.
- **Effect**: worked-around
- **Action**: Treat the maintainer's explicit project-wide rename as authorization for a
  terminology-only rewrite that preserves every entry ID, field, status, note, occurrence, and
  meaning.
- **Improvement**: Define how an explicitly approved global terminology or identifier migration may
  reconcile historical reflection text without weakening ordinary append-only agent behavior.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-30 feature.concorde.install-with-spec-kit — deferred to Feature 005's owning
    specification/contract lifecycle. Define a maintainer-approved terminology-migration exception
    with explicit authorization, an exact old/new mapping, preservation of entry IDs/fields/statuses
    and meaning, plus an appended audit occurrence; reconcile command guidance and parser/contract
    tests together without weakening ordinary append-only behavior.
  - implement 2026-08-31 feature.concorde.install-with-spec-kit — the maintainer explicitly directed
    removal of every closed reflection before committing the triage fixes. That authorization makes
    this pruning valid for the current change, but it reinforces the need for a durable contract rule
    distinguishing maintainer-directed cleanup from ordinary agent append-only behavior.

### R-035 · One package rename crosses several durable feature authorities

- **Phase**: plan
- **Date**: 2026-08-30
- **Feature**: feature.concorde.install-with-spec-kit
- **Kind**: architecture
- **Concerns**: module.concorde
- **Expected**: Feature 003 owns package identity and can keep every project reference synchronized
  with its renamed preset.
- **Observed**: The identity is repeated in accepted realizations and required sources owned by the
  workflow, release, self-hosting, and reflection features, while normal selected-root guidance
  prohibits editing another feature's durable body.
- **Effect**: worked-around
- **Action**: Use the root-level placement and the maintainer's explicit all-project instruction to
  reconcile referential terminology across those sources without changing their independently owned
  behavior; only Feature 003 receives a new accepted realization through this attempt.
- **Improvement**: Add a reviewed coordinated-migration procedure for one authoritative identity
  change that requires non-behavioral reference updates across several durable feature documents.
- **Status**: open
- **Occurrences**:
  - plan 2026-08-30 feature.concorde.workflow.fast-loop — the relaxed policy changes the selected
    child and parent aggregate workflow authorities plus project contracts and views; used the
    maintainer's explicit all-related-sources instruction for one coordinated attempt while keeping
    every independently owned behavior change explicit and reviewable.
  - implement 2026-08-30 feature.concorde.install-with-spec-kit — deferred to a reviewed root-level
    architecture procedure. It must name the owning feature authorities, approved migration scope,
    update ordering, behavioral versus referential changes, validation evidence, and which feature
    owns acceptance; changing those rules crosses several durable specifications and is not a local
    package-rename patch.

### R-041 · Relaxed contract eligibility still requires architecture review

- **Phase**: plan
- **Date**: 2026-08-30
- **Feature**: feature.concorde.workflow.fast-loop
- **Kind**: specification
- **Concerns**: feature.concorde.workflow.fast-loop
- **Expected**: Inter-module contract and maintained-diagram changes may use fast-loop when module
  responsibilities and dependency direction remain stable, while all constitutional architecture
  review obligations remain explicit.
- **Observed**: The first relaxed specification made contract and diagram changes eligible but did
  not state that AI-authored architecture edits still require exact maintainer review before they
  become project intent under constitution A.V.
- **Effect**: worked-around
- **Action**: Returned to specification and added a review-pending outcome and completion-report
  requirement for fast loops that edit maintained architecture sources.
- **Improvement**: Make policy relaxations that widen direct architecture authoring explicitly check
  constitutional review timing before planning begins.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-30 feature.concorde.workflow.fast-loop — deferred to the owning
    `feature.concorde.workflow.specify-behavior` lifecycle. Specify an early quality check that
    identifies widened AI architecture authoring and requires exact maintainer-review timing before
    planning; reconcile its design/abstract, specify command, design template, workflow guide, tests,
    and generated projections together. That feature still has a placeholder realization and active
    attempt artifacts, so fast-loop is ineligible.
