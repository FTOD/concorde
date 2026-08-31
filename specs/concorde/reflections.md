# Reflections: Concorde

The project's remaining open reflection log: unresolved difficulties or problems coding agents met
while planning or implementing a feature, attributed to that feature and naming the source the
problem concerns. Closed entries are removed by explicit maintainer direction. Grammar:
[reflection-log contract](features/005-record-workflow-reflections/contracts/reflection-log.md).
Ordinary recording appends entries/occurrences; explicit rename or documentation reconciliation may
rewrite existing content while preserving stable valid `R-NNN` identifiers and contract shape.

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
