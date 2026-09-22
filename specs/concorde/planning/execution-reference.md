# Planning execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Planning Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term                                                      | Meaning / definition                                      |
| --------------------------------------------------------- | --------------------------------------------------------- |
| [Spec](../module.md#terminology)                          | Defined in Concorde Framework.                            |
| [Module](../module.md#terminology)                        | Defined in Concorde Framework.                            |
| [Worker](../module.md#terminology)                        | Defined in Concorde Framework.                            |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.                            |
| [Candidate](../module.md#terminology)                     | Defined in Concorde Framework.                            |
| [Ready](../module.md#terminology)                         | Defined in Concorde Framework.                            |
| [Grant](../module.md#terminology)                         | Defined in Concorde Framework.                            |
| [Spec context](../harness/context.md#terminology)         | Defined in What information a worker receives.            |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations.                                    |
| [Pi integration](../module.md#terminology)                | Defined in Concorde Framework.                            |
| [Graph](../module.md#terminology)                         | Defined in Concorde Framework.                            |
| [Task sufficiency](assessment.md#terminology)             | Defined in Is the specification sufficient for this task? |
| [Acceptance task](tasks.md#terminology)                   | Defined in Making work verifiable.                        |
| [Reserved task ID](tasks.md#terminology)                  | Defined in Making work verifiable.                        |
| [Evidence](../module.md#terminology)                      | Defined in Concorde Framework.                            |
| [Delivery](../module.md#terminology)                      | Defined in Concorde Framework.                            |

## Context assessment {#assessment-context-assessment}

[Harness admission](../harness/admission.md) owns the entry. Its [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a public, explicitly target-bound operation in the [current adapter inventory](../operations/execution-reference.md#operations-current-host-adapter).
The calling agent selects context assessment through the Pi `concorde` tool. Its `run` action
performs finite preparation and returns the exact native `subagent` call, not a completed assessment.
The result hook accepts only independently correlated successful single-run metadata and current
Host predicates; `details.concorde_context.accepted` distinguishes acceptance from proposal/staging.
The [native boundary](../harness/execution-reference.md#native-context-assessor) defines transport.
Bare CLI/Studio execution without this Pi boundary reports `native_required`, never Pi-RPC fallback. The tool's `describe` action returns
the Operation guidance and request schema without executing it.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`context-solve` returns a task-specific sufficiency assessment without authored artifacts.
Before its fresh context assessor invocation, the host compares local dependency
declarations to registered relationships: a missing direct promise is an owned Spec gap;
malformed, duplicate, unknown or unrelated entries are conflicting. Neither injects an undeclared
relationship inventory into the worker. The assessor uses only the admitted Spec and never fetches
code or another context to fill a gap.

Outcomes are sufficient, spec_incomplete, unsupported, conflicting or failed. A prohibition is
unsupported, a contradiction conflicting, a known missing runtime field invalid input, and an
execution failure failed. Gaps identify question, blocked_step and needed_contract, with host-bound
target/context provenance. The caller pauses the dependent step and may continue independent work.
Reassessment of retained phases uses fresh accepted phase output; an unchanged blocked step stays blocked.
A fresh accepted sufficient assessment for the exact accepted target, task, focus and constraints
may supersede a correctly attributed historical `specify` task relation because that author
prerequisite has been removed. This includes unknown original revisions and non-contract failures
of that obsolete execution; it does not infer a historical byte change or successful repair.
The host retains the original relation, receipt, contexts, source evidence and failed outcome,
marks only its prerequisite status `superseded`, and records the current assessment context,
Spec revision and reason `retired_author_prerequisite`. The assessment proves current task
sufficiency, not that the old author succeeded or its Issue was fixed. An edit alone, unrelated
intent, malformed attribution, stale, failed, insufficient or gap-reporting assessment cannot
supersede it. A current contract gap remains blocking. This neither closes its Issue nor refreshes
required review, checks or retained plan/tasks/implementation/review relations, which need their
own accepted current output. Current integrity and permission failures remain failures.
Assessment proves no universal completeness.

### Precise specifications {#assessment-precise-specifications}

The Planning Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Planning operation {#plan-planning-operation}

The [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a public, explicitly target-bound operation in the [current adapter inventory](../operations/execution-reference.md#operations-current-host-adapter).
The calling agent selects this entry through the Pi `concorde` tool; its `run` action prepares
the exact native call rather than claiming model completion. The tool's `describe` action returns
the Operation guidance and request schema without executing it.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`plan` shares dependency-stop and result identity/outcome predicates with the native public
[assessment](execution-reference.md). Its two model invocations are ordered by the native workflow below. Only a sufficient result admits a
fresh planner invocation. Its optional concorde-plan-artifact is an explicitly admitted
prior plan, not a predecessor conversation. The accepted output is a nonempty plan bound to the
selected contract revision and intent. The host stores the target plan and returns artifact references
in concorde-plan-response@3; the worker has no direct project writes. No task list, implementation,
review or readiness is produced by planning.

A coordinating plan identifies local work and exact direct child/used-Module IDs from its local
dependency declarations. It states their required behavior without pretending to read their code;
separately selected component work needs each component's complete contract and its own grant.
Empty or invalid plans are rejected without replacing accepted state. Gaps, conflicting contracts,
unsupported work, stale context and failed execution stop dependent planning. Relevant Spec or
intent changes invalidate reuse; a repeated consumer invocation may reuse only current accepted
artifacts. Planning can be consumed by any declared caller satisfying these preconditions, without
depending on a development workflow.

### Design {#plan-design}

#### Native planning workflow {#plan-planning-graph-plan-graph}

Public plan is an authored native pi-subagents workflow, not a Python Graph or a suspended
provider stack. The Pi `concorde` tool's run action admits the request and managed candidate,
requires current Spec review when configured, freezes the assessor and returns an exact named
workflow call. Main invokes that call with async execution. The resource is registered against the
actual Pi session, has one issued ticket and three exact fixed Host-command grants, and is disposed
when its terminal result is observed or the session shuts down. Shutdown also invalidates future
Host advancement and sends the exact owned run to the supported native stop channel; disposing a
resource alone is not treated as revocation of an already admitted workflow. No model/task text becomes a shell
command or resource authority. Native fanout ceilings remain unchanged.

The authored steps in `pi/workflows/plan.js` are:

1. Fixed Host binding/preflight waits for the actual asynchronous launch receipt, independently
   checks current inputs/assets and resolves the exact capsule file Agent through public preflight.
2. One fresh context-assessor runs natively with a plain stage-only gate. Native failure, detached,
   paused, interrupted, missing metadata or rejected gate stops without launching the planner.
3. Fixed Host advancement correlates native terminal status, metadata, saved proposal and gate
   control. An accepted insufficient assessment ends with its business-blocked result. Only accepted
   sufficiency prepares and preflights the separate planner against still-current assessed inputs.
   If acceptance resolves an earlier gap, the finite transition uses the Host-recorded post-effect
   workspace context, while rechecking the same assessed contracts, registry, configuration, role
   binding and exact semantic candidate state. It does not mistake its own accepted lifecycle
   effects for an external input change.
4. One fresh native planner runs with its own complete Specs and declared external references.
5. Fixed Host finalization requires exact two-child coverage and independent planner completion,
   then re-admits inputs and persists only a nonempty valid plan through the shared domain service.

There is no shadow planning Graph. The old `plan_graph` factory is retired. Bare public Python/Studio capability invocations refuse absent native transport; there are no
planning State/Studio adapters or parallel legacy model backends.
Tests of domain predicates may supply explicit staged doubles through a test-only adapter; those
are not evidence of native dispatch.

The owning hook binds the actual workflow directory/run to the issued descriptor atomically.
The caller polls `concorde` with operation plan and action `result`; the response separates native
execution state from Host `accepted` and its typed business result. A launch receipt is not
acceptance. Accepted business blockers do not imply a persisted plan. A later stopped enclosing
workflow does not erase effects already committed after independently observed child completion.
No automatic retry/replay follows uncertain persistence.

Native finite services preserve common primary/candidate binding, assigned-candidate reuse and
primary-owned durable run/status records. The capsule is a worker cwd, never project/status
ownership. Candidate-input identity covers all semantic lifecycle/intent/target state; only the
observational run list and its revision counter are excluded because each finite admission records
its own run. Spec/metadata/registry/configuration/role/intent and delivered reference bytes are
rechecked. Stale or failed results leave previously accepted plan/tasks intact. A new accepted plan
retains task history and clears dependent tasks/checks/coordination as before.

### Precise specifications {#plan-precise-specifications}

The Planning Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Task authoring operation {#tasks-task-authoring-operation}

The [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a public, explicitly target-bound operation in the [current adapter inventory](../operations/execution-reference.md#operations-current-host-adapter).
The calling agent selects this entry through the Pi `concorde` tool; its `run` action prepares
the exact native call rather than claiming model completion. The tool's `describe` action returns
the Operation guidance and request schema without executing it.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`tasks` is a direct native task-author Agent, with the same proposal/staging/independent acceptance
boundary as context-solve and no coordinating model or Graph. Its exact call uses the Host-issued
capsule and immutable accepted-plan inputs. `tasks` requires a current managed change and accepted nonempty plan. Missing state is
missing_change; an absent plan is missing_plan. A fresh task author invocation receives
concorde-plan-artifact@1 and concorde-task-identity-constraints@1, even when the reservation list
is empty. Optional prior tasks and semantic scope/review feedback require explicit repair admission.
The [transport shapes](../spec/contracts.md#values-task-authoring-transport-values) are canonical there.

Task acceptance describes software behavior and implementation evidence within the programmer's
granted files and runtime. Host production/scaffold/export validation, independent reviews,
readiness, commit and delivery remain later responsibilities. Tasks support those checks through
implementation and tests; they never require the later steps to have finished first. Full software
acceptance stays in the plan and tasks, and all configured validation and required reviews still run.

Every fresh task author receives `concorde-task-identity-constraints@1` with a sorted, unique
`reserved_task_ids` list: all IDs from that target's retained task history, plus the current list
when scope or code-review repair replaces it. This input is required even when empty and survives
replanning through the retained history. It reserves identities without adding historical software
obligations. The Host rejects a collision with the specific IDs before accepting the new list;
it never rewrites author output or clears history to admit it.

The result is a nonempty list of internally unique, initially incomplete tasks, disjoint from
reserved IDs, each carrying id, target_id, description, acceptance and complete. The host accepts
and persists the list as a concorde-implementation-task@1 with its plan; it returns artifact
references through concorde-tasks-response@3. The author cannot complete tasks or mutate project files.

For scope recovery the explicit `repair_task_scope` request selects the exact current incomplete
task list by digest. It requires a current accepted plan, including its Spec revision and intent;
even a meaning-preserving Spec or metadata edit requires explicit replanning first. Repair cannot
silently rebind the old plan to new contract bytes. The task author receives the plan, prior list,
reserved IDs and the fixed implementation_boundary feedback, preserving software acceptance. A semantic change requiring a
new plan returns conflicting or a gap. Failed, malformed or colliding output never replaces the
old list or discards history. For review repair, only verified current blocking code feedback may
be supplied. The caller explicitly supplies repair_review as an ArtifactRef. The host verifies its digest,
current same-target/task input identity, blocking code findings and nonempty coverage before admission.
The caller owns ordering and invalidation, while this provider owns admissible input and new tasks.

### Precise specifications {#tasks-precise-specifications}

The Planning Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Realization and reuse limits

This Module is a child of Operations; its consumers, including Agents, need not be its structural siblings. Its behavior is realized in
its own package `src/concorde/planning/`, bound by its adapter entity together with its `operations/` declaration; this Spec boundary
does not itself create an Agent grant or configurable arbitrary graph; public exposure is explicit in the catalog. Host admission, phase
artifacts and permissions remain mandatory. A new graph requires declared composition and an
implementation of its sequencing, artifact admission, recovery and completion policies before it
can execute. [Harness admission](../harness/admission.md) realizes the common entry and invocation
host, and [Operations](../operations/execution-reference.md#graphs-dispatch-graphs) the dispatch
that reaches this provider.
