# Reflections: Concorde

<!-- concorde-reflection-high-water: R-047 -->

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
- **Intervention**: 需要你决定是否允许把旧版 Claude reflection 配置迁移到新配置；未获批准前只能保留回滚并继续使用当前 canonical 配置。
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
- **Intervention**: 需要你提供或批准受支持的浏览器运行环境；结构校验可以自动完成，但最终视觉验收不能由无浏览器的 agent 代替。
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
- **Intervention**: 需要你决定是否允许刷新非当前 active integration，以及是否接受该集成的安装面成为维护范围。
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
- **Intervention**: 需要你确认 `module_design`/`implementation.md` 的最终公开术语；确认后可由 specification workflow 自动改写子规范和 abstract。
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
- **Intervention**: 需要你决定规划阶段是否允许提出 durable contract 变更，以及由哪个 feature 拥有该 contract；agent 不能替你改变跨模块契约所有权。
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
- **Intervention**: 需要你选择 inactive integration 的支持范围（完整 materialization、只读 preview，或暂不支持）；这是安装/发行边界，不应由 agent 猜测。
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
- **Intervention**: 需要你确认是否把 allocate→append→bounded validation 提升为所有 reflection writer 的强制协议；它会改变运行时、队列工具和多个 Skill 的公共契约，不能作为无审查的小修复直接实施。
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
- **Intervention**: 需要你决定允许哪一种受控临时目录清理方式（managed cleanup、保留并过期回收，或人工清理）；agent 不应扩大删除权限。
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
- **Intervention**: 需要你确认哪些 hook effect 属于允许的 centralized reflection write；确认后实现和验证可自动化完成。
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
- **Intervention**: 需要你批准 inactive Codex projection 的写入范围；这是权限边界决策，不能由 LangGraph 或 agent 隐式放宽。
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
- **Intervention**: 需要你在真实 inventory 出现后确认是否继续采用 Understand Anything 适配词汇；这是架构映射取舍，不能仅凭当前 prototype 定案。
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
- **Intervention**: 需要你批准一次跨 feature/module 的 migration workspace 及其 ownership 清单；没有该授权，agent 只能逐 feature 工作。
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
- **Intervention**: 需要你决定是否在下一版引入 `interface.*` 重命名及 external-interface registry，并接受由此产生的兼容性迁移成本。
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
- **Intervention**: 需要你在 ontology 稳定后确认哪些实体/关系视图属于必须交付的架构证据；生成工具本身可自动执行。
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
- **Intervention**: 需要你选择 Manifest 11 的字段迁移策略和兼容窗口（rename、双写、或 breaking cutover）；这会影响下游消费者。
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
- **Intervention**: 需要你决定是否向上游 Spec Kit 提交 typed `feature_path` 兼容提案，以及是否承担上游迁移协调。
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
- **Intervention**: 需要你批准 source/target 两套 temporal path 同时存在的迁移协议；否则 agent 只能执行当前一次性 bootstrap workaround。
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
- **Intervention**: 需要你决定发布版本与 tag 的切分点；版本号是对外兼容承诺，不能由 agent 根据本地未发布提交自行推断。
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
- **Intervention**: 需要你决定哪些 control-state 文件纳入 `.concorde` 统一边界；这是仓库治理范围的选择，需维护者明确授权。
- **Occurrences**:
  - plan 2026-09-01 feature.concorde.define-project-ontology — initialization currently creates only configuration and root architecture; the new control boundary requires a third reflection-log file and a versioned proposal contract.
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
- **Intervention**: 需要你批准 source-profile migration 的原子性、回滚和旧路径删除策略；这些会决定是否允许自动迁移生产中的 control state。
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
- **Intervention**: 需要你在有真实使用数据后选择是否增加 browser projection 或标准 alignment 格式；当前应保持 JSON 原型，避免过早锁定接口。
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
- **Intervention**: 需要你选择默认安全边界：自动 materialize tracked+untracked snapshot，还是强制显式 snapshot commit；这决定 implementer 能看到哪些输入。
- **Status**: open
