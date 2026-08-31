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
