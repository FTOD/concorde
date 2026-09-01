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
- **Occurrences**:
  - implement 2026-09-01 feature.concorde.workflow.plan-delivery — inherited parent core and module level views were freshly delivered and structurally validated, but both visual checks skipped for the same unavailable browser.
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
- **Occurrences**:
  - plan 2026-09-01 feature.concorde.workflow.plan-delivery — `docs/commands.md` still names the former accept stage and `concorde-impl-accept` command after the delivery rename.
- **Status**: open

### R-007 · Plan Delivery still names the module reference as implementation
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: specification
- **Concerns**: specs/concorde/features/001-concorde-workflow/subfeatures/006-plan-delivery/design.md
- **Expected**: Child planning requirements use the inherited `Module design reference` term and its canonical module `design.md` path.
- **Observed**: Acceptance scenario 3 and FR-008 still call that level reference `implementation.md`, while the parent ontology and Protocol v9 expose it as `module_design`.
- **Effect**: assumed
- **Action**: Planned against the parent ontology and returned `workspace.module_design` path without editing the selected feature specification.
- **Improvement**: Reconcile the child specification and abstract through their owning specification workflow before claiming terminology completeness.
- **Status**: open

### R-008 · Bounded level view retains the former accept label
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: architecture
- **Concerns**: specs/concorde/architecture/diagrams/level-view.json
- **Expected**: The inherited level view uses the canonical `deliver` operation introduced by the workflow ontology.
- **Observed**: The Skills-to-Scripts-to-Workspace connection still ends with `accept`, although the maintained command and current parent workflow use `deliver`.
- **Effect**: worked-around
- **Action**: Kept the inherited view read-only, used `deliver` in the plan, and recorded the discrepancy for the architecture owner.
- **Improvement**: Reconcile and redeliver the level view through its owning architecture workflow, then add a stale-operation label check.
- **Status**: open

### R-009 · Planning guidance writes contracts outside temporal attempt memory
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: guidance
- **Concerns**: presets/concorde/commands/speckit.plan.md
- **Expected**: Planning keeps proposed contract work in the selected attempt and schedules any durable contract mutation for implementation.
- **Observed**: The plan command directs Phase 1 to write feature-root `contracts/`, although child FR-007 and parent FR-015 prohibit planning from updating durable sources and the module reference classifies `attempt/contracts/**` as temporal.
- **Effect**: worked-around
- **Action**: Created no child contract for this milestone and planned to reconcile the maintained command/template guidance with temporal contract proposals.
- **Improvement**: Add `attempt/contracts/` to the planning model and require tasks to promote reviewed contract deltas with code, evidence, and compatibility updates.
- **Status**: open

### R-010 · Focused contract test overfit equivalent bounded-context wording
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: implementation
- **Concerns**: tests/concorde/contract/test_plan_delivery.py
- **Expected**: The focused test verifies that planning and tasks never load sibling feature bodies implicitly.
- **Observed**: The first passing candidate used the existing precise phrase `sibling design/implementation body`, while the new assertion required the less precise token `sibling bodies`.
- **Effect**: worked-around
- **Action**: Kept the command's stronger wording and aligned the test with that exact semantic invariant.
- **Improvement**: Prefer stable normative phrases over newly invented shorthand when adding prose-contract assertions.
- **Status**: open

### R-011 · Partial Codex projection backup exposed lower-layer skills
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: tooling
- **Concerns**: presets/concorde/preset.yml
- **Expected**: Refreshing the three changed Codex skills preserves every other Concorde preset winner while Claude remains the configured integration.
- **Observed**: The first cross-integration refresh backed up only three generated skills; removing the temporary Codex preset exposed lower-layer `analyze` and `specify` skills, causing two full-suite failures.
- **Effect**: worked-around
- **Action**: Rematerialized Codex through the public preset path, preserved the complete ten-skill preset set, restored Claude, and verified current self-host state before rerunning tests.
- **Improvement**: Provide an integration-scoped materialization command or preserve the complete owned preset surface whenever switching inactive integrations.
- **Status**: open

### R-012 · Reflection concern initially used an unresolved command string
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: implementation
- **Concerns**: specs/concorde/reflections.md
- **Expected**: Every reflection `Concerns` value resolves to a stable project ID or existing project-relative path.
- **Observed**: The first record of the Codex projection problem named the triggering command rather than the maintained preset path, and deterministic validation rejected it.
- **Effect**: worked-around
- **Action**: Replaced the unresolved command string with `presets/concorde/preset.yml` and reran reflection validation.
- **Improvement**: Validate each new reflection entry immediately after append, before starting the full suite.
- **Status**: open

### R-013 · Execution policy retained temporary projection backups
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: environment
- **Concerns**: .gitignore
- **Expected**: Temporary inactive-integration projection backups under `/tmp` are removed after both generated surfaces are verified.
- **Observed**: The execution policy rejected the explicit cleanup command even though both targets were validated temporary directories outside the repository.
- **Effect**: deferred
- **Action**: Left the temporary backups outside the project; no maintained, generated, or installed repository artifact depends on them.
- **Improvement**: Provide a policy-compatible managed temporary-directory cleanup operation for generated projection workflows.
- **Status**: open
