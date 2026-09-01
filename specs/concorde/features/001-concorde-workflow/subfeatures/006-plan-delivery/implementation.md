# Feature Implementation: Plan Delivery

**Feature**: `feature.concorde.workflow.plan-delivery`

**Realization status**: Accepted first milestone for bounded implementation planning, dependency-ordered task generation, and separately authorized task-to-issue projection under Feature Workspace Protocol v9.

## Realization Overview

Plan Delivery is realized by three agent-followed Spec Kit phase surfaces: `speckit.plan`, `speckit.tasks`, and `speckit.taskstoissues`. Each surface begins with the installed Concorde workspace adapter and consumes its Protocol v9 result as the sole selected-root path authority. The phases share one active `attempt/`; they do not create root-level plan, task, or checklist copies.

Planning treats the selected `abstract.md` as orientation only, `design.md` as required behavior, and feature `implementation.md` as the accepted realization baseline. The placeholder is handled explicitly as no accepted baseline. The providing module's `module.md` is bounded architecture context, while module `design.md` is opened only for a specific implementation or rationale question and cited when used.

## Module and Feature Collaboration

`module.concorde.skills` supplies the three maintained command modifications plus the plan and task template addenda. `module.concorde.scripts` supplies deterministic selected-workspace resolution. `module.concorde.workspace-files` supplies the durable/temporal path model, selection state, parent aggregate context, sibling summaries, and attempt lifetime. `module.concorde.distribution` materializes equivalent Codex and Claude presentations from the maintained preset.

The inherited `contract.concorde.workflow` now defines the Plan Delivery handoff across implementation plans, proposed contract deltas, task lists, and issue projections. The required `contract.concorde.spec-kit-platform` remains the host for preset composition and the normal phase lifecycle. No new runtime service, storage boundary, module dependency, or child-owned contract was introduced.

## Scenario Realization

### Build an implementation plan

The plan surface resolves the selected top-level feature or immediate sub-feature before hooks or artifact access. It reads the durable sources through returned paths, carries the complete parent durable trio only as aggregate child context, leaves sibling bodies and every parent/sibling attempt unopened, resolves research decisions, and writes the plan, research, data model, quickstart, validation memory, and any proposed contract delta under the selected attempt. A durable feature-root contract is never written by planning.

### Generate executable tasks

The tasks surface reads the feature specification, accepted baseline or placeholder, plan artifacts, durable contracts, and optional attempt-local contract proposals. It emits strict checklist tasks grouped by user story, supplies dependency ordering and parallel opportunities, and gives each task a requirement ID, acceptance-outcome token, or named plan-section trace for setup mechanics. Architecture, contracts, validation, documentation, generated freshness, and evidence work are made explicit when applicable.

### Project tasks into external issues

The issue surface runs only after an explicit `speckit.taskstoissues` invocation and only against the GitHub repository matching the configured remote. It parses the authoritative task-file order and dependency graph, deduplicates complete task IDs across open and closed issues, and creates only missing issues. Every body carries the selected feature/root, source task path, story or phase, exact scope, prerequisite task IDs and issue links, and trace tokens. Missing dependency issues, unknown/cyclic references, a mismatched remote, or ambiguous scope stop external writes. Issue creation never edits task checkboxes or implies implementation completion.

## Durable Implementation Decisions

- Protocol v9 selected-workspace resolution remains the only deterministic routing mechanism; planning itself stays agent-followed.
- Orientation, required behavior, and accepted realization are separate inputs. A placeholder baseline is represented as no accepted baseline rather than inferred implementation.
- Proposed interface changes are temporal under `attempt/contracts/`. Tasks apply reviewed deltas together with compatibility, schema/example, code, test, evidence, and documentation work.
- Task traceability is explicit rather than inferred only from story grouping. Dependency order remains visible in both the task list and external issue projection.
- Task-to-issue conversion is a projection: `attempt/tasks.md` stays authoritative, external writes require the command invocation, and issue metadata preserves identity, order, dependencies, and scope.
- The parent core Archify architecture view plus the module level view are sufficient. This child owns no duplicate diagram. Both inherited sources use hidden legends.
- Maintained preset sources are authoritative; `.specify/presets`, Codex skills, and Claude skills are generated/materialized presentations.

## Traceability and Evidence

Required behavior and acceptance outcomes are in the adjacent `design.md`. Phase semantics are maintained in `presets/concorde/commands/speckit.plan.md`, `speckit.tasks.md`, and `speckit.taskstoissues.md`; shared template constraints are in `presets/concorde/templates/plan-template.md` and `tasks-template.md`; the handoff contract is in the parent workflow's `contracts/agent-commands.md`; public usage is in `docs/commands.md`.

Focused evidence is in `tests/concorde/contract/test_plan_delivery.py`, `tests/concorde/integration/test_plan_delivery_workspace.py`, and the installed composition assertions in `tests/concorde/acceptance/test_workspace_composition.py`. Thirteen focused/materialization tests passed. The complete Concorde Python suite passed 333 tests. Deterministic Concorde validation passed with zero findings. The docsite passed TypeScript, 19 test files and 85 tests, validation of 118 pages with zero errors, and the optimized production build.

The inherited parent core view and module level view each passed all nine Archify showcase checks with zero errors and zero warnings and were freshly delivered. The parent feature publication test passed automatic diagram embedding. Configured Claude self-host state is current, and both Claude and Codex agent-assets verify successfully.

## Known Limitations

- Live GitHub issue creation is intentionally not exercised by deterministic repository tests; the maintained command contract is verified without external mutation.
- Task quality and semantic requirement coverage still depend on the coding agent following the maintained phase instructions; tests prove the contract and fixtures, not every future generated task list.
- Browser containment and light/dark perceptual review of the inherited views remain pending because Chrome/Chromium is unavailable in this environment. Showcase validation does not substitute for visual inspection.

## Implementation Detail

The common workspace gate names `workspace.feature_abstract`, `workspace.feature_design`, `workspace.feature_implementation`, `workspace.parent_context`, `workspace.siblings`, `workspace.module_summary`, `workspace.module_design`, and attempt paths explicitly. For a sub-feature the three `parent_context.feature_*` paths are aggregate-only inputs, and the prohibition on implicit sibling bodies and parent/sibling attempts is carried into all three installed presentations.

The task-to-issue procedure first builds a task graph, then maps existing issue URLs, then creates missing issues in task-file order. A dependent issue is never created while a prerequisite lacks an existing or newly created issue. Created, skipped, and failed task IDs are reported in the same order, and neither deduplication nor creation mutates the source task list.
