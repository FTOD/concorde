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

### R-003 · Browser visual review unavailable for delivery diagrams
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: environment
- **Concerns**: specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json
- **Expected**: Archify visual-check captures containment and light/dark screenshots for every changed delivered workflow view.
- **Observed**: All three sources passed 9/9 showcase validation and HTML delivery, but visual-check skipped because Chrome/Chromium is unavailable.
- **Effect**: deferred
- **Action**: Preserved the deterministic delivery receipts and marked browser containment and perceptual review pending.
- **Improvement**: Provide Chrome/Chromium in the development validation environment or set `ARCHIFY_CHROME` to a supported executable.
- **Status**: open

### R-004 · Temporary Codex self-host refresh hit registry mismatch
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: tooling
- **Concerns**: scripts/development/self-host-concorde.py
- **Expected**: Temporarily selecting Codex lets self-host refresh that integration while preserving the current Claude materialization.
- **Observed**: Codex preflight succeeded, but apply detected Spec Kit registry entries that did not match the temporary composition and rolled back the owned scope.
- **Effect**: worked-around
- **Action**: Kept the rollback, used public component materialization for Codex, then restored and reverified the configured Claude integration.
- **Improvement**: Let self-host explicitly refresh an inactive installed integration without temporarily changing the project's active integration.
- **Status**: open

### R-005 · Protocol rename left three stale test and contract references
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: implementation
- **Concerns**: specs/concorde/architecture/modules/workspace-files/architecture/contracts/feature-workspace/contract.md
- **Expected**: Protocol v9 tests and contract examples resolve only the renamed delivery surfaces.
- **Observed**: The first full suite found one schema-v8 assertion and two removed example filenames still referenced by the Workspace Files contract.
- **Effect**: worked-around
- **Action**: Updated the assertion, contract representation version, and both example paths before rerunning affected and full tests.
- **Improvement**: Extend the delivery terminology contract to inventory protocol-version assertions and contract example paths, not only command tokens.
- **Status**: open

### R-006 · Documentation gate caught MDX alias syntax and stale command expectation
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: implementation
- **Concerns**: docsite/tests/integration/framework-guides.test.ts
- **Expected**: Updated terminology tables and framework-guide tests compile and recognize only the delivery command.
- **Observed**: The first documentation gate rejected a non-self-closing alias line break and still expected the former command in one test.
- **Effect**: worked-around
- **Action**: Used MDX-safe `<br />` syntax accepted by the ontology parser and updated the command inventory assertion before rebuilding.
- **Improvement**: Add MDX compilation of terminology aliases and the canonical extension command inventory to focused pre-docsite tests.
- **Status**: open
