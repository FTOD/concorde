# Feature Implementation: Execute and Reconcile

**Feature**: `feature.concorde.workflow.execute-and-reconcile`

**Realization status**: Accepted first milestone for evidence-backed task execution, non-repairing consistency analysis, and append-only remaining-work convergence under Feature Workspace Protocol v9.

## Realization Overview

Execute and Reconcile is realized by three agent-followed Spec Kit phase surfaces: `speckit.implement`, `speckit.analyze`, and `speckit.converge`. Every surface begins with the installed Concorde workspace adapter and uses its Protocol v9 result as the sole selected-root and attempt path authority. A top-level feature and an immediate sub-feature use the same attempt model; a child receives its parent durable trio only as aggregate context and never loads sibling bodies or parent/sibling attempts implicitly.

Implementation reads the feature `implementation.md` as the accepted realization baseline, with the placeholder represented explicitly as no accepted baseline. It executes dependency-ready tasks, records compact verification evidence inside the attempt, and changes a task marker to completed only after a proportionate check passes. Analysis compares durable intent, accepted realization, the active plan/tasks, attempt evidence, and constitution without repairing them. Convergence assesses current code and evidence and appends only genuine remaining work.

## Module and Feature Collaboration

`module.concorde.skills` owns the maintained implement/analyze/converge command modifications. `module.concorde.scripts` supplies deterministic selected-workspace routing, while `module.concorde.workspace-files` supplies the durable trio, attempt paths, task state, validation evidence, centralized reflection path, parent aggregate context, and bounded sibling summaries. `module.concorde.distribution` materializes equivalent Codex and Claude presentations from the maintained preset.

The inherited `contract.concorde.workflow` defines the Execute and Reconcile handoff: implementation execution and attempt evidence, categorized analysis results and mutation budget, convergence findings/results, and failure stops. `contract.concorde.spec-kit-platform` remains the host lifecycle. No new executor service, storage boundary, module dependency, or child contract was introduced.

## Scenario Realization

### Execute tasks with evidence

The implementation surface validates every checklist, parses task dependencies, and works phase by phase. Before a task changes to `[X]`, `attempt/validation.md` records its task/requirement trace, verification command or check, outcome, relevant artifact, and material limitation. Missing evidence, a skipped required check, or failed verification leaves the task unchecked. Pre/post SHA-256 evidence covers the selected durable trio, returned parent trio, module summary/reference, and canonical bounded sibling-summary JSON; unexpected drift stops execution and becomes a centralized problem record. Project setup mutations are allowed only when the selected plan or executable task puts the detected tool in scope.

### Analyze without repairing

The analysis surface builds inventories for requirements, user actions, accepted realization, plan decisions, tasks, constitution rules, attempt evidence, and selected-root reflection state. Every finding uses one primary category: absent evidence, disagreement, ambiguity, duplication, or coverage gap. An abstract/specification disagreement names the disagreeing statement and prevailing `design.md` requirement. Analysis changes only a required centralized reflection record; a clean run changes zero files. Mandatory before/after hooks must declare the same read-only-except-reflection contract before invocation.

### Converge remaining work

The convergence surface compares current code and attempt evidence with the specification, accepted baseline, plan, tasks, and constitution. Findings use `missing`, `partial`, `contradicts`, or `unrequested` gap types. Before retaining one, convergence compares its source, paths, and outcome with every existing unchecked and completed task and suppresses semantic duplicates. Actionable work is appended as one next-numbered Convergence phase with new stable task IDs; all existing bytes and markers are preserved. When nothing remains, `tasks.md` stays byte-for-byte unchanged and no empty header is emitted. Specification-owned diagram declaration/role/prose problems are recorded and routed to their owner rather than turned into forbidden tasks that edit `design.md`.

## Durable Implementation Decisions

- Protocol v9 remains the sole deterministic routing mechanism; arbitrary implementation and semantic reconciliation remain agent-followed.
- Task completion is evidence-backed. Test existence or intent alone never authorizes `[X]`; the selected attempt persists the actual check and its limitation.
- Protected-authority hashes make the phase's negative write boundary observable without opening sibling bodies.
- Analysis is read-only except for genuine centralized reflection recording. Its exact taxonomy keeps absence, disagreement, ambiguity, duplication, and coverage distinct.
- Analysis hooks participate in the same mutation budget and are refused before invocation when their maintained contract is incompatible.
- Convergence is evidence-qualified and append-only. It preserves completed history, suppresses semantic duplicates, and is idempotent on a converged state.
- Durable diagram-authority defects are routed to specification/architecture ownership; convergence appends only already-authorized implementation/evidence work.
- Maintained preset sources are authoritative; `.specify/presets`, Codex skills, and Claude skills are generated presentations.
- The parent's core architecture view and module level view are sufficient; this child owns no duplicate diagram.

## Traceability and Evidence

Required behavior and acceptance outcomes are in the adjacent `design.md`. Maintained phase semantics are in `presets/concorde/commands/speckit.implement.md`, `speckit.analyze.md`, and `speckit.converge.md`. The cross-phase handoff is in the parent workflow's `contracts/agent-commands.md`, and public usage is in `docs/commands.md`.

Focused evidence is in `tests/concorde/contract/test_execute_reconcile.py`, `tests/concorde/integration/test_execute_reconcile_workspace.py`, and installed composition assertions in `tests/concorde/acceptance/test_workspace_composition.py`. Thirty-one focused feature, reflection, and materialization tests passed. The full Concorde Python suite passed 342 tests. Deterministic Concorde validation passed with zero findings. The docsite passed TypeScript, 19 test files and 85 tests, validation of 118 pages with zero errors, and the optimized production build.

The inherited parent core view and module level view each passed all nine Archify showcase checks with zero errors and zero warnings and were freshly delivered. Parent feature-page embedding passed five tests. Configured Claude self-host state is current, and both Claude and Codex agent assets verify successfully.

## Known Limitations

- Arbitrary product-task execution and semantic finding/deduplication quality still depend on coding-agent judgment; maintained contracts and tests bound that judgment but do not replace it with a universal runtime.
- Hook compatibility is enforced through maintained instruction/contract review rather than a typed deterministic hook-effect schema.
- Browser containment and light/dark perceptual review of inherited views remain pending because Chrome/Chromium is unavailable. Showcase validation does not substitute for visual inspection.

## Implementation Detail

The implementation evidence record is compact and task-indexed: task ID/trace, verification command or check, `passed`/`failed`/`skipped` outcome, relevant artifact path, and material limitation. Only `passed` evidence for the proportionate required check permits task completion. Aggregate validation and protected-authority digests live in the same attempt file so analysis, convergence, and delivery can inspect one temporal evidence source.

Convergence computes the maximum task ID and highest existing phase, but it never rewrites either. A new phase is appended only after semantic comparison against all current tasks and evidence. A completed task can yield new work only when current evidence shows failure, regression, or incomplete scope.
