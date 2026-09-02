# Reflections: Concorde

<!-- concorde-reflection-high-water: R-045 -->

The project's remaining open reflection log: unresolved difficulties, prototype choices, or problems
coding agents met while planning or implementing a feature, attributed to that feature and naming the
source the reflection concerns. The grammar and workflow are defined by the embedded interface in
[Record and Triage Workflow Reflections](../../specs/concorde/features/005-auto-reflections.md#interfaces).
New entries use the tracked high-water allocator; repeated retained problems append occurrences.
Validated merged-small fast-loop entries are removed automatically, while other routes require
explicit maintainer disposition. Explicit rename or documentation reconciliation may rewrite existing
content while preserving stable valid `R-NNN` identifiers and contract shape.

### R-002 · Self-host refresh could not adopt legacy Claude state
- **Phase**: implement
- **Date**: 2026-08-31
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: tooling
- **Concerns**: scripts/development/sync-agent-surfaces.py
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
- **Concerns**: specs/concorde/architecture.md
- **Expected**: Archify visual-check captures containment and light/dark screenshots for every changed delivered workflow view.
- **Observed**: All three sources passed 9/9 showcase validation and HTML delivery, but visual-check skipped because Chrome/Chromium is unavailable.
- **Effect**: deferred
- **Action**: Preserved the deterministic delivery receipts and marked browser containment and perceptual review pending.
- **Improvement**: Provide Chrome/Chromium in the development validation environment or set `ARCHIFY_CHROME` to a supported executable.
- **Occurrences**:
  - implement 2026-09-01 feature.concorde.workflow.plan-delivery — inherited parent core and module level views were freshly delivered and structurally validated, but both visual checks skipped for the same unavailable browser.
  - implement 2026-09-01 feature.concorde.workflow.execute-and-reconcile — inherited parent core and module level views again passed showcase delivery, while both visual checks skipped for the unavailable browser.
- **Status**: open

### R-004 · Temporary Codex self-host refresh hit registry mismatch
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: tooling
- **Concerns**: scripts/development/sync-agent-surfaces.py
- **Expected**: Temporarily selecting Codex lets self-host refresh that integration while preserving the current Claude materialization.
- **Observed**: Codex preflight succeeded, but apply detected Spec Kit registry entries that did not match the temporary composition and rolled back the owned scope.
- **Effect**: worked-around
- **Action**: Kept the rollback, used public component materialization for Codex, then restored and reverified the configured Claude integration.
- **Improvement**: Let self-host explicitly refresh an inactive installed integration without temporarily changing the project's active integration.
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
  - plan 2026-09-01 feature.concorde.workflow.execute-and-reconcile — the selected abstract still names the former accept step after the canonical delivery rename.
- **Status**: open

### R-007 · Plan Delivery still names the module reference as implementation
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: specification
- **Concerns**: specs/concorde/features/013-plan-delivery.md
- **Expected**: Child planning requirements use the inherited `Module design reference` term and its canonical module `design.md` path.
- **Observed**: Acceptance scenario 3 and FR-008 still call that level reference `implementation.md`, while the parent ontology and Protocol v9 expose it as `module_design`.
- **Effect**: assumed
- **Action**: Planned against the parent ontology and returned `workspace.module_design` path without editing the selected feature specification.
- **Improvement**: Reconcile the child specification and abstract through their owning specification workflow before claiming terminology completeness.
- **Occurrences**:
  - plan 2026-09-01 feature.concorde.workflow.execute-and-reconcile — FR-007/FR-008 and the abstract still call the inherited module design reference `implementation.md`.
- **Status**: open

### R-009 · Planning guidance writes contracts outside temporal attempt memory
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: guidance
- **Concerns**: skills/concorde-plan-author/SKILL.md
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
- **Occurrences**:
  - implement 2026-09-01 feature.concorde.workflow.execute-and-reconcile — the new handoff test required lowercase `failed verification` while the contract correctly began the sentence with `Failed verification`.
  - implement 2026-09-02 feature.concorde.explore-alignment — the first focused documentation marker required shorthand `concorde explore` while the README already carried the exact `scripts/concorde.py ... explore` invocation; the guide now also names the shorthand operation for discoverability.
  - implement 2026-09-02 feature.concorde.explore-alignment — the integrated gate found the projection unit test still expected the former coarse `entity.concorde.runtime` zoom participant after durable reconciliation introduced the concrete `entity.concorde.alignment-explorer`; the assertion now follows the selected feature's current entity.
  - implement 2026-09-02 feature.concorde.explore-alignment — the first final stale-language scan matched the unrelated fast-loop sentence `no accepted-realization prerequisite exists`; the alignment audit was narrowed to feature-006-owned/interface/public surfaces so negated historical terminology elsewhere is not misclassified.
- **Status**: open

### R-011 · Partial Codex projection backup exposed lower-layer skills
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.plan-delivery
- **Kind**: tooling
- **Concerns**: feature.skills.project-workflow
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
- **Concerns**: .concorde/reflections/log.md
- **Expected**: Every reflection `Concerns` value resolves to a stable project ID or existing project-relative path.
- **Observed**: The first record of the Codex projection problem named the triggering command rather than the maintained preset path, and deterministic validation rejected it.
- **Effect**: worked-around
- **Action**: Replaced the unresolved command string with the then-canonical package path and reran reflection validation; the concern now follows `feature.skills.project-workflow` after native migration.
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

### R-015 · Analysis hooks were outside the declared mutation audit
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.execute-and-reconcile
- **Kind**: guidance
- **Concerns**: skills/concorde-analyze/SKILL.md
- **Expected**: The complete analysis surface preserves every file except a required centralized reflection record.
- **Observed**: Mandatory before/after hooks were executed without first requiring the same read-only-except-reflection contract, so a mutating hook could violate the phase promise.
- **Effect**: worked-around
- **Action**: Required hook contract compatibility before invocation and included after-hooks in the same mutation budget.
- **Improvement**: Add a reusable hook-effect declaration and deterministic compatibility check to every read-only command surface.
- **Status**: open

### R-017 · Self-host rollback needed write access to inactive Codex surfaces
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.workflow.execute-and-reconcile
- **Kind**: environment
- **Concerns**: scripts/development/sync-agent-surfaces.py
- **Expected**: Refreshing configured Claude preserves and verifies the already materialized inactive Codex skill set atomically.
- **Observed**: The first sandboxed apply could not rewrite `.agents/skills` during inactive-integration restoration, so verification failed and rollback could not restore those paths exactly.
- **Effect**: worked-around
- **Action**: Re-ran the same current proposal with approved write access; apply completed and both integration assets verified.
- **Improvement**: Declare inactive-integration projection paths as required self-host write scope before the transaction begins.
- **Status**: open

### R-018 · Understand Anything is an adapter vocabulary, not the module ontology
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: docs/ontology.md
- **Expected**: The referenced Understand Anything model supplies reusable entity and relationship definitions for the requested recursive module architecture.
- **Observed**: Its formal schema has useful code/system node and directed-edge vocabularies, but `module` is only a broad package type, `Layer` is flat, scripts normalize to files, programs are absent, and physical definition files can be conflated with logical services or schemas.
- **Effect**: assumed
- **Action**: Used the formal upstream schema as an adapter vocabulary, kept Concorde modules recursive, separated stable entity identity from code locator and physical file from logical entity, introduced Program, and limited the prototype inventory to architecture-significant entities.
- **Improvement**: Reassess the preferred type/role mapping after the prototype has real module inventories and adapter evidence.
- **Status**: open

### R-019 · One selected-root lifecycle must migrate every related feature
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: guidance
- **Concerns**: operations/concorde-plan/SKILL.md
- **Expected**: A selected feature attempt writes only inside one lifecycle root and treats other feature bodies as read-only authorities.
- **Observed**: The requested source-profile migration is not coherent unless all twenty-four feature designs, six module packages, runtime, guidance, fixtures, and projections change together; a partial migration cannot be loaded or validated by either profile.
- **Effect**: worked-around
- **Action**: Anchored one explicitly authorized repository-wide attempt at the ontology feature and will enumerate every cross-root mutation as a traced task with full-suite evidence.
- **Improvement**: Add an explicit migration-workspace kind for reviewed source-profile changes that legitimately own a declared set of related feature and module authorities.
- **Status**: open

### R-020 · Prototype preserves contract identities while moving interface ownership
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: specs/concorde/features/007-project-ontology.md
- **Expected**: Every contract becomes an interface inside exactly one feature design, including shared platform dependencies.
- **Observed**: Several `contract.*` identities are consumed by many features or describe an external platform rather than a capability Concorde provides; renaming and splitting them in the same prototype would add compatibility churn without improving ownership.
- **Effect**: assumed
- **Action**: Preserved stable `contract.*` IDs as interface identities, embeds each provided interface in one owning feature, and lets consuming features reference that identity as required.
- **Improvement**: Evaluate `interface.*` names and an explicit external-interface registry after feature ownership and consumers are validated in the new profile.
- **Status**: open

### R-021 · Canonical and installed guidance already differ before migration
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: tooling
- **Concerns**: scripts/development/sync-agent-surfaces.py
- **Expected**: Checked-in canonical preset/extension sources and installed Spec Kit/Codex/Claude projections have one reproducible current composition.
- **Observed**: The clean checkout contains source-only diagram-output checks in plan/specify guidance that are absent from the installed projection, so blindly treating installed files as the edit baseline would discard newer requirements.
- **Effect**: worked-around
- **Action**: Will edit authoritative package sources first, preserve the newer source-only checks where still applicable, then regenerate and verify every installed projection through self-hosting.
- **Improvement**: Make clean-tree self-host freshness a deterministic pre-plan gate for framework source-profile migrations.
- **Status**: open

### R-023 · Existing diagrams encode the removed source profile
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: specs/concorde/architecture.md
- **Expected**: Maintained diagrams supplement each module's current typed entities and relationships without becoming a second authority.
- **Observed**: All eleven existing sources were organized as module summaries, feature component views, subfeature flows, contract crossings, and durable-trio lifecycles; relabeling paths would preserve a materially false Profile 4 model.
- **Effect**: deferred
- **Action**: Retired the stale sources for the prototype and kept complete textual entity, relationship, and interaction tables as module authority; Profile 5 keeps diagrams optional.
- **Improvement**: Generate and visually review fresh module-owned entity/relationship views from the validated Profile 5 model after the ontology stabilizes.
- **Status**: open

### R-024 · Manifest status temporarily falls back to evidence status
- **Phase**: implement
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: specs/concorde/modules/auto-docs/features/001-publish-project-docsite.md
- **Expected**: Build Manifest 10 feature records expose the requested `status` field with one unambiguous Profile 5 meaning.
- **Observed**: Profile 5 front matter retains `evidence_status`, while most concise feature designs no longer carry a separate body lifecycle Status; both concepts cannot be represented faithfully by one field.
- **Effect**: assumed
- **Action**: Auto-Docs reads a legacy body Status when present and otherwise maps `evidence_status` into Manifest 10 `status`, documenting the temporary semantic overlap.
- **Improvement**: Rename/split the field in Manifest 11 after consumers can migrate to explicit lifecycle and evidence fields.
- **Status**: open

### R-029 · Feature wrapper directory has no remaining durable meaning
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: specs/concorde/features/007-project-ontology.md
- **Expected**: The filesystem hierarchy reflects meaningful ontology and separates durable specification from temporal workflow state.
- **Observed**: After Profile 5, each feature wrapper contains only `design.md` when inactive; nesting `attempt/` beside it is the sole reason the directory exists.
- **Effect**: assumed
- **Action**: Chose direct `features/<NNN-name>.md` authorities and separate module-level `attempts/<NNN-name>/` workspaces, with basename used only as a deterministic storage key.
- **Improvement**: Reassess the basename mapping if feature renames or concurrent attempts become common enough to justify ID-addressed attempt storage.
- **Status**: open

### R-030 · Spec Kit selection vocabulary assumes a feature directory
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: guidance
- **Concerns**: src/concorde/feature_workspace.py
- **Expected**: Selection names the canonical feature authority without embedding a removed storage concept.
- **Observed**: Current `.concorde/feature.json` and Protocol 10 expose `feature_directory`, but a direct feature file has no unique directory of its own.
- **Effect**: assumed
- **Action**: Protocol 11 uses `feature_path` and the selection record stores that direct Markdown path; no dual-layout/dual-key compatibility remains after cutover.
- **Improvement**: Propose a typed feature-path selection field upstream in Spec Kit so host and extension terminology converge.
- **Status**: open

### R-031 · Proposal 8 and Manifest 10 do not need path-only version bumps
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: src/concorde/delivery.py
- **Expected**: Serialized protocols change version only when their accepted fields or semantics change.
- **Observed**: Feature/attempt paths change under Profile 6 and Protocol 11, but Proposal 8 still binds target/digest/one remove path and Manifest 10 still records semantic pages/routes/provenance.
- **Effect**: assumed
- **Action**: Bump the source profile and workspace protocol only; retain Delivery Proposal 8 and Build Manifest 10, with old path proposals naturally stale or invalid.
- **Improvement**: Add an explicit compatibility decision table to future cross-protocol migration plans.
- **Status**: open

### R-032 · The active attempt must bootstrap from its old location
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: tooling
- **Concerns**: specs/concorde/features/007-project-ontology.md
- **Expected**: Planning and implementation use the target module-level attempt path throughout the lifecycle.
- **Observed**: Protocol 10 must resolve the current feature-directory attempt until Protocol 11 exists, while final delivery requires that same attempt under `specs/concorde/attempts/007-project-ontology/`.
- **Effect**: worked-around
- **Action**: Author plan/tasks/evidence in the current returned attempt, implement Protocol 11 first, then move the complete active attempt and selection together before final validation/delivery.
- **Improvement**: Add an explicit migration-attempt workspace that can declare source and target temporal paths during source-profile transitions.
- **Status**: open

### R-033 · Unreleased component versions still need a clear breaking boundary
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: concorde.json
- **Expected**: Installed artifacts communicate the Profile 6 / Protocol 11 compatibility boundary through their component versions.
- **Observed**: The prior Profile 5 work is still uncommitted and only v0.1 is tagged, so either extending pending 0.6.0 or bumping again is mechanically possible.
- **Effect**: assumed
- **Action**: Chose preset/extension/bundle 0.7.0 and docsite 0.5.0 so the direct-file breaking boundary is explicit in manifests, catalogs, receipts, and generator provenance.
- **Improvement**: Align feature delivery, commits, and release tags so future planning can distinguish unreleased work from a published compatibility boundary deterministically.
- **Status**: open

### R-034 · Workflow state is still split across specification and control trees
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: specs/concorde/modules/workspace/architecture.md
- **Expected**: The specification tree contains only durable module architecture, feature intent, and explanatory sources, while project workflow state has one obvious owner.
- **Observed**: Attempts and the reflection log live under `specs/`, but reflection triage configuration, plans, and worktrees already live under `.concorde/reflections/`, splitting one process concern across two authorities.
- **Effect**: assumed
- **Action**: Move active attempts and the tracked reflection authority into `.concorde/`; keep the log and active attempt reviewable while plans/worktrees remain ignored.
- **Improvement**: Reassess whether other project-control records should adopt one declared `.concorde` schema after this prototype proves the boundary.
- **Occurrences**:
  - plan 2026-09-01 feature.concorde.define-project-ontology — initialization currently creates only configuration and root architecture; the new control boundary requires a third reflection-log file and a versioned proposal contract.
- **Status**: open

### R-035 · Filename-derived attempts undermine stable feature identity
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: architecture
- **Concerns**: src/concorde/feature_workspace.py
- **Expected**: An active attempt remains bound to the same semantic feature when its navigation filename or providing module path changes.
- **Observed**: Protocol 11 derives attempts from the feature basename, so a harmless file rename looks like an orphaned old attempt plus a new empty workspace.
- **Effect**: assumed
- **Action**: Key `.concorde/attempts/` by the exact globally unique, path-safe `feature.*` ID and reject unsafe IDs or stable-ID changes with active work.
- **Improvement**: Add an explicit attempt-instance identifier only if concurrent attempts for one feature become a supported workflow.
- **Occurrences**:
  - plan 2026-09-01 feature.concorde.define-project-ontology — a planned feature has no trustworthy stable ID before its file exists, so initial specification resolution cannot derive an attempt from the filename.
- **Status**: open

### R-036 · The control-state migration must bootstrap through paths it removes
- **Phase**: plan
- **Date**: 2026-09-01
- **Feature**: feature.concorde.define-project-ontology
- **Kind**: tooling
- **Concerns**: src/concorde/feature_workspace.py
- **Expected**: Every lifecycle phase writes only paths returned by the active workspace protocol.
- **Observed**: Protocol 11 can create this attempt only below `specs/concorde/attempts/` and can record planning reflections only in `specs/concorde/reflections.md`, while final Protocol 12 must reject both locations.
- **Effect**: worked-around
- **Action**: Author specification/planning/tasks through Protocol 11, implement Protocol 12 first,
  hash and move the complete attempt and reflection log exactly, then apply only explicitly mapped
  internal-path rebases before final evidence and delivery.
- **Improvement**: Define a first-class source-profile migration operation that binds old and new control-state paths without a hand-managed bootstrap sequence.
- **Occurrences**:
  - implement 2026-09-01 feature.concorde.define-project-ontology — the pre/post attempt-tree aggregate included absolute project-relative path prefixes, so relocation changed that aggregate despite same-filesystem rename; future cutovers need a saved relative-path manifest before mutation.
- **Status**: open

### R-044 · Alignment exploration needs a concrete prototype entry point
- **Phase**: plan
- **Date**: 2026-09-02
- **Feature**: feature.concorde.explore-alignment
- **Kind**: architecture
- **Concerns**: feature.concorde.explore-alignment
- **Expected**: The feature identifies a concrete read-only projection/query entry point and an executable representation for explicit alignment evidence.
- **Observed**: The maintained interface intentionally says only `Future read-only Alignment Explorer projection/query API`, while the checked-in JSON fixtures are untested, reference a missing schema path, and still encode removed ontology concepts.
- **Effect**: assumed
- **Action**: Use a native `concorde explore` JSON operation plus a versioned, revision-bound alignment sidecar; keep it distinct from conversational `concorde-*` commands and prohibit name/similarity-derived verification.
- **Improvement**: Reassess whether a browser projection or a broadly adopted alignment format should supplement the JSON operation after real project usage establishes stable query and evidence needs.
- **Status**: open

### R-045 · Stash-based worktree snapshot omitted untracked attempt sources
- **Phase**: implement
- **Date**: 2026-09-02
- **Feature**: feature.operations.permission-bounded-planning
- **Kind**: tooling
- **Concerns**: operations/concorde-reflections-triage/SKILL.md
- **Expected**: An isolated implementation worktree created from the authorized main-checkout snapshot contains both tracked edits and untracked selected feature/attempt sources before Protocol 13 runs.
- **Observed**: Branching from the primary Git stash merge commit restored tracked edits but omitted the stash's untracked-file parent, so the implement workspace gate could not resolve the new feature or attempt.
- **Effect**: worked-around
- **Action**: Cherry-picked the exact untracked-files stash parent into the isolated feature branch, re-ran Protocol 13, and confirmed the requirements checklist was 28/28 before implementation continued.
- **Improvement**: Add a deterministic isolated-worktree bootstrap helper that materializes and verifies the complete tracked-plus-untracked authorized snapshot, or require an explicit snapshot commit, before dispatching an implementer.
- **Status**: open
