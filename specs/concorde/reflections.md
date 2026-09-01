# Reflections: Concorde

The project's remaining open reflection log: unresolved difficulties or problems coding agents met
while planning or implementing a feature, attributed to that feature and naming the source the
problem concerns. Closed entries are removed by explicit maintainer direction. Grammar:
[reflection-log contract](features/005-auto-reflections/contracts/reflection-log.md).
Ordinary recording appends entries/occurrences; explicit rename or documentation reconciliation may
rewrite existing content while preserving stable valid `R-NNN` identifiers and contract shape.

### R-001 · Feature diagram output path escaped the generated boundary
- **Phase**: implement
- **Date**: 2026-08-31
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: guidance
- **Concerns**: presets/concorde/commands/speckit.specify.md
- **Expected**: A declared feature diagram output is a generated HTML path accepted by Auto-Docs.
- **Observed**: The specification and plan placed the output beside maintained JSON, while Auto-Docs requires a unique HTML path beneath `generated/`.
- **Effect**: worked-around
- **Action**: Returned the output-path correction to the specification authority before delivery and added contract evidence before resuming implementation.
- **Improvement**: Specify and plan guidance should explicitly require `generated/` output paths and validate the declaration before implementation.
- **Status**: open

### R-002 · Self-host refresh could not adopt legacy Claude state
- **Phase**: implement
- **Date**: 2026-08-31
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: tooling
- **Concerns**: scripts/development/self-host-concorde.py
- **Expected**: A reviewed self-host proposal refreshes owned installed surfaces atomically or reports a recoverable conflict.
- **Observed**: Apply rolled back because legacy `.claude/reflections.config.json` state could not be adopted into the new projection receipt.
- **Effect**: deferred
- **Action**: Preserved the rollback and continued with canonical preset/extension sources without overwriting or migrating the unrelated legacy state.
- **Improvement**: Provide an explicit reviewed adoption/migration path for legacy reflection configuration before agent-asset verification.
- **Status**: open
