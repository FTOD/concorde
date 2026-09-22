# Callable role contracts

These implementation specifications define role interaction, not a second copy of domain artifact schemas or acceptance predicates.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Domain role](module.md#terminology) | Defined in Agents. |
| [Outer task role](module.md#terminology) | Defined in Agents. |
| [Registration](module.md#terminology) | Defined in Agents. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |

## Inventory and compatibility

`agents.DOMAIN_AGENTS` selects the seven canonical domain modules. Their `PROFILE` is the existing Harness `WorkerProfile`, with unchanged stage wire identities, effects, tools and timeout. `agents.OUTER_PROFILES` defines the two task roles with prompt, tools, explicit extensions, source-only flag and optional acceptance role. It has no domain context/result or stage schema. `agents.AGENTS` is the derived nine-name source discovery inventory; installed packages omit the
source-only profile implementation and therefore expose eight roles, with only tester statically
registered as an outer task role. Main has no profile or inventory entry.

The single `concorde.agents` metadata array has exact fields `id`, `family` (`domain` or `outer`), `scope` (`distributed` or `source-only`), `registration` (`invocation` or `project`) and `source` (canonical instruction path). Package validation compares it with the actual definitions and rejects duplicates, missing roles and drift. Domain profiles and their contracts are checked separately by Harness. The `concorde.operations` metadata now describes only compatibility public adapters, not Agents. This is an explicit source/metadata ownership migration, not a wire or catalog version change.

Domain bare, underscored, hyphenated and `concorde-`-prefixed lookup keeps its previous identity. Public `concorde-*` names, `operation_id`, request/result types, generated/agents paths and WorkerProfile/WorkerBinding remain compatibility surfaces. The domain source path changes to `agents/<role>/spec.md`, invalidating byte-bound builds and bindings. No duplicate `operations/<role>` definitions or model-operation aliases remain. `operations/` public adapters retain finite `STATE`/`run` wire compatibility; only explicitly selected StateGraphs are Operations.

## Common domain invocation contract

Each domain invocation is fresh, terminal and bound to one complete selected Module context, its task/constraints, Protocol and phase-admitted artifacts. Scenario focus does not trim complete paired Specs. Instructions are not project knowledge. Harness supplies the context index and the exact native invocation ID; roles use admitted paths only and do not reselect context, inherit prior conversation or treat retrieved text as replacement authority.

All seven roles have read/search tools and scoped `report_issue`; only programmer has native write/edit/shell tools. Programmer and code-reviewer may use fixed Host `run_checks`; code-reviewer's historical profile shell ceiling is narrowed away by native admission. No role has delegation tools. File, network and credential restrictions are model policy, not OS confinement or proof of exclusive reads. The configured-check subprocess boundary is separately enforced by Harness.

A domain role returns native `structured_output` with the issued identity and its typed result. This is a proposal; a passing stage-only gate is not Host acceptance. The role reports actual outcomes and genuine immutable Issue receipts, not invented evidence. Invalid output, stale input, cancellation, timeout and failed execution remain failures even after earlier progress. Dependent work stops while independently useful work may continue inside the grant. Repetition is a fresh re-admitted invocation; the role never retries by widening authority. Harness preserves causal errors and durable receipts under its existing contracts.

## context-assessor

Use this read-only domain role through `concorde-context-solve` or as plan's first workflow step to decide whether an explicit task has sufficient specified meaning. Input is the complete Spec-only context and task for phase `context-solve`; implementation names are visible but contents and external source investigation are not. It returns a sufficiency judgment, or an attributed missing promise, prohibition or contradiction, with no plan, tasks or documents. Its work completes when that judgment is supported by admitted Specs, not when the overall change is ready. Gaps report the question and blocked work rather than searching outside context. Reassessment after repair needs fresh inputs. [Planning assessment](../planning/assessment.md) owns outcome semantics and acceptance.

## planner

Use this read-only domain role only after accepted sufficiency in the native plan workflow. Input is complete selected Specs, declared external references, task/constraints and optionally an admitted prior plan; never implementation contents. It returns an actionable contract-level plan and no tasks or document replacements. It may identify declared component work but cannot schedule it or acquire component code. Completion is a plan suitable for task authoring, subject to [Planning's plan contract](../planning/plan.md); empty/stale/invalid output cannot replace accepted state. Missing necessary meaning stops dependent planning, and a revised request starts a fresh planner rather than continuing hidden conversation.

## task-author

Use this read-only domain role through `concorde-tasks` to turn an accepted current plan into implementation acceptance tasks. Input includes complete Specs, declared references, the plan and reserved historical IDs; optional prior tasks and selected feedback require the domain's repair admission. No code contents are admitted. Output is a nonempty list of new, initially incomplete tasks, not a new plan, implementation or Spec edits. It defines acceptance the programmer can fulfill inside its grant, without requiring later review/readiness to have happened first. Missing IDs or changed intended behavior are gaps/conflicts, not reasons to invent metadata. [Planning task rules](../planning/tasks.md) own collisions, history, repair and acceptance; each replacement is a fresh admitted invocation.

## programmer

Use this domain role through `concorde-implement` for current accepted local tasks after required component admission. Input includes complete Specs, admitted references, accepted plan/tasks, optional current selected feedback and the selected Module's implementation contents. It writes only intended bound implementation paths in the actual candidate, not capsule copies; Specs, metadata, registry, configuration, governing integration and other worktrees stay outside its write authority. Read/search, write/edit/shell and fixed Host checks do not grant network, credentials, delegation, commit or delivery. It returns exact task identities/acceptance with honest completion and concrete check/deferred-check evidence. Missing external test inputs are not passing tests; actual unfulfilled obligations stay incomplete. Failed/cancelled work may leave partial edits. [Implementation](../implementation/execution-reference.md#implementation-implementation-operation) owns fulfillment and recovery; retry re-admits actual current work rather than assuming rollback.

## spec-reviewer

Use this read-only domain role in the Spec review workflow to assess complete specifications and design for the requested task. Input includes complete owned/referenced paired Specs, Protocol, task and scoped Spec changes, with no implementation contents or author conversation. It checks representative tasks and mandatory terminology semantic consistency; wording equality is not required. It returns coverage, supported Issue references and no-findings/findings/incomplete, not repairs. Missing canonical meaning stops dependent judgments; unexamined comparisons remain incomplete. A fresh reviewer is used for every selected owner/consumer context. [Review](../review/execution-reference.md#review-independent-review-operation) owns coverage selection, exact result admission and aggregation.

## code-reviewer

Use this read-only domain role in the code review workflow to compare granted implementation and scoped changes against the complete selected contract. Input additionally includes the declared read-only implementation subset and references, never programmer reasoning or another reviewer's files. Its native tools are read/search and fixed Host checks, not shell/write/edit/delegation. It reports concrete contract defects, exact check outcomes, representative coverage and supported Issue judgments, without raw code/patch/log copies or repairs. Unavailable evidence is unknown, not a pass. Every affected consumer retains its own fresh context, even for shared files. [Review result](../review/review-result.md) owns findings and completion semantics; failed, incomplete and stale evidence cannot become clean review on retry.

## issue-solver

Use this read-only domain role only when the caller requests solving a selected Issue. Input is complete Spec-only context and the Host-selected current Issue revision, bounded feedback/verification, clarification and admitted duplicate candidates; the report is an observation, not new product authority. It returns one bounded next-action decision and rationale with no documents, plan or tasks. Needed implementation or Spec edits return to the caller; verification is requested from fresh reviewers, not performed by this role. It never reads implementation, closes Issues or fabricates resolution from unrelated passing tests. Unsettled choices return a precise developer decision; execution failures remain distinct. [Issues lifecycle](../issues/lifecycle.md) owns decision/disposition evidence and bounded repetition. Each decision step is a new terminal invocation.

## maintenance-worker

Use this source-only outer task Agent for explicitly authorized Concorde source maintenance in its assigned registered candidate. Input is main's frozen goal, stage, file/tool authority, current brief and evidence, not a domain stage envelope. It reads principles and complete affected paired Specs, then directly reconciles authorized source, metadata and registry. Its tools are read/search, bash, edit and write plus explicitly selected source observation/lifecycle assets; it receives no Concorde catalog or delegation tool. It does not create/move worktrees, write primary/foreign status or runs, launch tester, merge, push or clean up.

Output is verified committed candidate work when authorized, exact HEAD/dirty state, input-bound commands/results, artifacts, residual risks and next step. Self-checks are not independent acceptance. It preserves causal failures and reports meaningful changes through native supervisor with current task memory; it stops dependent work for a decision instead of inventing causes. Within an unfinished coherent stage the same author continues through feedback. New prompts do not govern its frozen launch. A completed stage hands off durably and stops before main releases exact ownership. Source-only scope prohibits consumer registration; [outer collaboration](outer.md) defines the common handoff policy.

## tester

Use this outer task Agent when main selects targeted or full independent testing, in either source or consumer work. Input is exact scope/reason, tested revision, candidate-local Pi entry/catalog/runtime provenance, relevant complete paired Specs and the actual task/tool grant. It begins fresh with no author conversation, inherited catalog or Skills. Read/search tools remain read-only; commands use only `test_command` with enforced read-only governing artifacts and disposable external scratch. It cannot repair sources, profiles or runtime, delegate, move worktrees or integrate.

Output records independent observations, commands, failures, skipped/unknown checks, retained evidence and residual risks against exact inputs. It distinguishes scripted fixtures from live model execution and source selection from actual loading. Selected nonsecret reports and bounded output must be exported through Harness before scratch cleanup; a scratch filename alone is not durable evidence. Export failure is reported alongside the original failure. Missing/stale local assets or unavailable isolation blocks testing without fallback. Failures return to main, never self-repair; a later testing round is a fresh tester after an exact stopped-owner handoff. Distribution registers only generic tester in consumers and preserves user-file collision boundaries.

## Domain task-profile bindings

Each worker fulfils exactly one task contract. The table uses these typed pairs: **stage** =
`concorde-agent-stage-context` / `concorde-agent-stage-result`, **review** =
`concorde-review-stage-context` / `concorde-review-stage-result`.

| Worker           | Pair and phase/action | Admitted stage artifacts                                                                                                                                               | Result and authority                                                                                |
| ---------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| spec-reviewer    | review; spec-review   | none                                                                                                                                                                   | Independent Spec findings; no author artifacts or writes                                            |
| context-assessor | stage; context-solve  | none                                                                                                                                                                   | Sufficient, incomplete, unsupported or conflicting assessment; no authored artifacts                |
| planner          | stage; plan           | optional concorde-plan-artifact                                                                                                                                        | Plan only; external references readable; no source contents or writes                               |
| task-author      | stage; tasks          | required concorde-plan-artifact and concorde-task-identity-constraints; optional concorde-implementation-task, concorde-review-result and concorde-task-scope-feedback | Implementation acceptance tasks with new IDs outside the reserved set; no source contents or writes |
| programmer       | stage; implementation | required concorde-implementation-task; optional concorde-review-result                                                                                                 | Fulfilled tasks only; may write the selected Module's listed implementation paths                   |
| code-reviewer    | review; code-review   | none                                                                                                                                                                   | Independent code findings; authorized code read-only                                                |
| issue-solver     | stage; issue-solve    | required concorde-issue-selection                                                                                                                                      | Bounded next action or disposition; Spec-only, no project writes                                    |
