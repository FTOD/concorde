# Development Flow execution and record contracts

These are the precise implementation agreements and executable Flow specifications owned by the
[Development Flow Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Snapshot](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Task context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Acceptance task](../planning/tasks.md#terminology) | Defined in Making work verifiable. |
| [Reserved task ID](../planning/tasks.md#terminology) | Defined in Making work verifiable. |
| [Review coverage](../review/module.md#terminology) | Defined in Review. |
| [Capability](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Harness](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Delivery](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Development Agent Flow and revision loops {#development-development-agent-flow-and-revision-loops}

A developer supplies intended behavior and constraints for one top-level candidate change.
`concorde-specify-loop` independently routes, authors or revises, and reviews the Spec. It ends
with a completed Spec result, retaining blockers and review evidence in the candidate worktree.
`concorde-dev-loop` calls that capability, then coordinates context assessment, planning, tasks,
implementation and checks. The same task and change can continue from specify-loop into dev-loop
without repeating accepted authoring or current reviews. `specify=false` skips authoring; `run_reviews=false` records review
skips where no earlier requirement exists. The specification flow can complete independently; dev-loop adds its own development lifecycle.
Its successful output is a ready candidate, not an automatic merge.

[Planning task acceptance](../planning/execution-reference.md) and
[Implementation completion](../implementation/execution-reference.md) define the provider boundaries.

#### Explicit task-scope recovery {#development-explicit-task-scope-recovery}

An explicit `repair_task_scope:{tasks_digest}` request repairs this phase error on an existing
incomplete task list. The digest is SHA-256 of canonical JSON bytes (sorted keys, compact
separators, ASCII escaping), prefixed `sha256:`. It must match the current list and admitted intent;
unresolved gaps, a completed list or a pending code-review repair reject the request.
The normal Flow enters tasks after the required Spec review. A fresh task author receives only
its complete Module Spec, plan, prior tasks, reserved IDs and Host-generated `implementation_boundary` feedback.
It preserves software acceptance and returns new incomplete tasks with new IDs. The Host saves the
original list, request digest and implementation revision in task history, invalidates checks and
implementation evidence and continues implementation, validation and independent code review.
After a Protocol binding or Spec revision, required Spec review runs on the current inputs first.
The task author revalidates the preserved plan against that complete current Spec. A meaning
change requiring a new plan returns conflicting or a Spec gap; successful boundary repair binds
the replacement tasks to the current Spec revision and retains the old revision in history.
Replaying a digest already consumed by that target resumes the replacement tasks without
reauthoring them. Invalid or failed author output never replaces the old list. This is an explicit
recovery entry, not another automatic retry edge or authority to edit Specs or bypass a gate.

For an already coordinated list, scope repair preserves its component target set. A changed
component's derived task text is rebound only after the replacement list is accepted; its previous
coordination record remains in task history. The Host clears that component's implementation
completion and the enclosing finalization stamps, while retaining current Spec reconciliation and
unchanged participants. The child's normal loop sees the new intent and obtains fresh review,
planning, tasks, implementation and validation as needed; the Host does not rewrite its old tasks
as complete. Existing component contract gaps must be resolved before rebinding, and a change of
component routing is rejected without replacing the list. Ordinary intent changes outside this
explicit recovery still fail their original stale-context checks.

#### Failure and recovery {#development-failure-and-recovery}

Candidate creation precedes routing. A change ID identifies a worktree, not a completed route.
An unbound handoff resumes router selection using the recorded task and constraints; optional
saved target/focus hints only steer that selection. Older records without a saved target hint
remain valid. Once bound, the recorded owner supplies an omitted target or focus and omitted
constraints, while explicit incompatible intent is rejected. Standalone reviews without a change
ID still route their own review task. Trusted child routes retain their own admitted task context
and cannot replace the root owner. Recovery resolves current contracts and retains all existing
stage, review and readiness gates; it does not add a topology repair transition.

A known prohibition is unsupported, a contradiction is conflicting, a missing runtime value is
invalid input, and tool failure is failed. None automatically means Spec incomplete. A gap names
the unresolved question, blocked step and needed contract; target and snapshot identity accompany it.
Context solving diagnoses from the exact existing collection and never expands permissions.

A Module task may coordinate its own code, direct submodules and explicitly used Modules.
The Module planner sees only the Module collection and derives exact component IDs from its local
dependency metadata and local readable agreements. Before planning, deterministic context solving rejects any
missing direct registry relationship as a Module-owned Spec gap and reports inconsistent entries as
conflicting. Each component
receives its own explicit task, local authoring invocation and fast loop. All affected
consumer/provider contract views must agree before any component implementation begins. Component
ancestry and scope membership never grant extra reads. Successful component revisions are checked
again before Module delivery.

Checks use deterministic argv declared by project configuration. [Harness Module](../harness/module.md) enforces read-only project
access for the entire check process tree and gives each check external temporary/cache/report space;
unsupported enforcement blocks execution. [Development Module](../development/module.md) persists output outside that sandbox, and
raw logs stay out of later Spec-only sessions. A stale Spec, changed task intent, modified
code, failed check or missing completion blocks delivery and preserves the candidate worktree. Resuming a
change reuses its target records and typed artifacts but starts a fresh agent session. The host does not copy unrelated
conversation or free-form predecessor output into context.

#### Candidate lifecycle and review policy {#development-candidate-lifecycle-and-review-policy}

`concorde-dev-loop` calls `concorde-specify-loop` for specify (default `specify=true`; `specify=false` skips Spec authoring
when the target's current Spec already suffices) and Spec review, then runs plan, tasks, implement, deterministic
validation and code review, then verifies readiness. It uses the same public contracts as standalone
capabilities. `run_reviews` defaults to `true`; `run_reviews=false` records an explicit skip for each
review mode instead of running it, and cannot cancel a review already required for this change. Every
invocation ends at ready and never invokes deliver.
It stops on the first non-successful outcome and preserves the change worktree, except that a
code-owning target's blocking code review first attempts a declared, bounded repair. The only
automatic revision edge is `review_code -> tasks`: task authoring receives the current completed
tasks and the blocking `concorde-review-result` as `stage_inputs`, and the resulting repair tasks
and their implementation are checked and code-reviewed again like any other change. This repair is
bounded by a declared `max_repair_iterations` policy recorded per target under
`change["graph"][target_id]["policy"]` in `.concorde/worktree.json`; the same record keeps the
current `repair_iteration`, the last blocking-feedback fingerprint and an attributed history of
selected transitions (development.md's "AI and human feedback", G4). Repeated unchanged blocking
feedback is guarded by code: new records carry the formal `source` value `code-driven` or
`model-driven`, while retaining their descriptive legacy `trigger` label. A repair selected from
review findings is model-driven; unchanged-feedback and limit stops are code-driven. Repeated unchanged blocking
feedback across a repair attempt, or exhausting the declared limit, stops the Flow instead of
retrying forever: the change `status` becomes `waiting` (a human decision or a Spec/code change is
needed) or `limit_exhausted` respectively, and the wire `outcome` remains `conflicting`. Elsewhere, a
Spec gap (`spec_incomplete`) stops the Flow with status `waiting`, a failed deterministic check
stops it with status `failed`, and another blocking/unsupported outcome stops it with status
`blocked`. A human directly changing the Spec or the implementation between invocations resets the
recorded repair count instead of silently continuing a stale repair attempt. Preserving the change
worktree on a stop and resuming a current plan/tasks/implementation phase on a repeat instead of
discarding completed component work otherwise remain unchanged.
Module implementation coordinates independently selected participating component contexts. The host
records each author before launch and after success or blocking. Already authored draft Spec bytes
remain in the candidate when a later component blocks. Cross-component validation runs after every
affected local author finishes; it cannot prevent resuming an incomplete reconciliation. No component
code changes before this agreement. Component development loops report completion to the same owning change.

`concorde-specify-loop` (including when called by `concorde-dev-loop`) skips Spec authoring only after a host-accepted authoring result for
the same target, task, focus and constraints. Standalone review records, including failed or
unrelated reviews, cannot substitute for authoring. A completed Module still revisits its recorded
component coordination: stronger review requirements propagate before completed component work is
reused, and missing or stale component reviews run before readiness.

Standard development requires both reviews for a Module whose entities list implementation files,
regardless of recorded component work; a Module whose entities list no implementation files requires
only Spec review, and its recorded components carry their own code reviews.
`run_reviews` defaults to true and applies to both modes; `run_reviews=false` is the explicit opt-out.
Requirements and the exact review intent are saved per target in the existing worktree state; an
enabled requirement survives retries with run_reviews=false. Skips have separate records and never
satisfy a required gate. A standalone review with a different task/focus/constraints remains a run
artifact and cannot replace another intent's lifecycle-required review. Code review runs after checks
but before the single ready transition; a failed/incomplete/blocking review cannot be bypassed by
standalone validation or delivery.

A repeated loop preserves current plans/tasks and completed components. It reuses a review only after
checking its artifact digest, exact current inputs, successful coverage and absence of blocking
findings/gaps. Changed Spec invalidates its dependent plan/reviews and rebuilds context; changed code
invalidates code review/check evidence. Explicitly required reviews also apply to directly authored
candidates without inventing plans. Review does not edit files, run repair steps or deliver changes.

Common [gap history](../development/execution-reference.md) retains attributed blockers and accepts resolution only after current successful output. The flow stops dependent work until those conditions hold.

A change's `status` may also become `cancelled` or `limit_exhausted` after an executor outcome of
the same name (`execution_cancelled`/`execution_limit`), distinguishing a cancelled or time-limited
agent process from an ordinary `blocked`/`failed` outcome; the candidate is preserved for repair or
resumption in every case. A development loop stopping for a necessary Spec gap, or for blocking
code-review feedback that repeats unchanged across a bounded repair attempt, records status
`waiting` instead of the generic `blocked`: both name a concrete point where a human decision or a
Spec/code change is needed before the loop can usefully resume.
During dev-loop, the initial Module Spec review is local. Component reviews occur in separately coordinated component loops after reconciliation, and all writers finish before final shared-consumer checks.

### Design {#development-design}

#### Development Flow (`development_flow`) {#development-development-flow-development-flow}

The development Flow is the LangGraph Flow `concorde-dev-loop` executes after target admission.
It follows the [Flow Spec convention](../harness/execution-reference.md): nodes execute, edges
route, node labels state the state read and written, and the diagram is kept equal to the
compiled Flow by the configured Flow Spec check. Specified and SpecReviewed belong to the
independently callable specification Flow, which the `specify_loop` node composes; delivery is a
separately invoked capability after `ready`.

State: `output` (the last stage's typed response data, including its outcome), `artifacts`
(review and stage artifact references accumulated across stages under a merge reducer), `result`
(a terminal failure envelope when a guard caught an error), `route`. The candidate record in
`.concorde/worktree.json` carries the durable state every stage reads and advances: the bound
owner and intent, the plan, the task list and history, the implementation digest, check evidence,
review requirements and results, gap history and the per-target graph record with its repair
iteration and last feedback fingerprint. Each stage returns a `Command` naming the next node; a
stop routes to `summarize`, and only `review_code` may select the automatic repair edge back to
`tasks`, bounded by the declared `max_repair_iterations` and the unchanged-feedback rule.

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `initialize` | Deterministic: records the graph policy and enters the Flow. | task, candidate | route |
| `specify_loop` | The specification Flow: Spec authoring (unless `specify=false` or already accepted) and independent Spec review with consumer reuse. Its result also selects where a resumed candidate re-enters. | task, Spec context, candidate | Spec, Spec review evidence, entry stage |
| `plan` | The planning Flow: context assessment, then one planner invocation. | Spec, task | plan |
| `tasks` | One task-author invocation with the plan, reserved task ids and, in a repair round, the blocking review result. | plan, reserved ids, review result | tasks |
| `implement` | One programmer `implementation` invocation, or component coordination for a composite. | tasks, implementation files, Spec | completed tasks, changed files |
| `validate` | Deterministic: Spec validation and configured checks for the owner and every Module sharing a changed file. | candidate | checks, readiness gate |
| `review_code` | Independent code review of the owner and every changed-file peer, each from its own contract, reusing current evidence. | Spec, changed files, tasks | code review results |
| `ready` | Deterministic: verifies current evidence for every affected Module and marks the candidate ready. | evidence, reviews | ready candidate |
| `summarize` | Deterministic: the capability response with review coverage and every artifact reference. | output, artifacts | response |

```mermaid
flowchart TB
    %% flow: development_flow
    accTitle: Development Flow
    accDescr: After initialization the specification Flow runs, then planning, tasks, implementation, validation, code review and readiness in order; a resumed candidate re-enters at the stage its current evidence permits; blocking code review routes back to tasks within the repair budget; every other non-advancing outcome stops at summarize, and a guard-caught error ends the Flow.
    __start__["start"]
    initialize["initialize<br/>in: task, candidate<br/>out: route"]
    specify_loop["specify_loop<br/>in: task, Spec context, candidate<br/>out: Spec, Spec review evidence, entry stage"]
    plan["plan<br/>in: Spec, task<br/>out: plan"]
    tasks["tasks<br/>in: plan, reserved ids, review result<br/>out: tasks"]
    implement["implement<br/>in: tasks, implementation files, Spec<br/>out: completed tasks, changed files"]
    validate["validate<br/>in: candidate<br/>out: checks, readiness gate"]
    review_code["review_code<br/>in: Spec, changed files, tasks<br/>out: code review results"]
    ready["ready<br/>in: evidence, reviews<br/>out: ready candidate"]
    summarize["summarize<br/>in: output, artifacts<br/>out: response"]
    __end__["end"]
    __start__ --> initialize
    initialize -->|admitted| specify_loop
    initialize -->|error| __end__
    specify_loop -->|Spec complete, no current plan| plan
    specify_loop -->|current plan, resume at tasks| tasks
    specify_loop -->|current tasks, resume at implementation| implement
    specify_loop -->|implementation current, resume at validation| validate
    specify_loop -->|Spec gap, blocked or failed| summarize
    specify_loop -->|error| __end__
    plan -->|plan accepted| tasks
    plan -->|gap, conflict or failure| summarize
    plan -->|error| __end__
    tasks -->|tasks accepted| implement
    tasks -->|gap or failure| summarize
    tasks -->|error| __end__
    implement -->|every task complete| validate
    implement -->|gap, blocked or failed| summarize
    implement -->|error| __end__
    validate -->|checks pass, Module lists code| review_code
    validate -->|checks pass, no code to review| ready
    validate -->|checks failed| summarize
    validate -->|error| __end__
    review_code -->|no blocking findings| ready
    review_code -->|blocking findings, feedback changed, repairs left| tasks
    review_code -->|unchanged feedback, limit exhausted, gap or failure| summarize
    review_code -->|error| __end__
    ready -->|candidate ready| summarize
    ready -->|error| __end__
    summarize --> __end__
```

#### AI and human feedback {#development-ai-and-human-feedback}

Author, assessor, planner, task author, implementation and reviewer invocations MUST resolve their
own Capability execution profiles and effective Harnesses. Shared Flow state contains admitted outputs and
feedback, not their private transcripts. Review findings identify the input revision and the
required repair. A code defect selects an implementation repair and another review; a necessary
Spec gap selects a clarification or authorized Spec-authoring path before implementation resumes.

The Flow MUST record which AI finding or human decision selected a transition. Repeated unchanged
blocking feedback waits for new information or stops at the declared limit. Human changes to intent
create a revised task and invalidate dependent plans and evidence. Human acceptance required for
another transition remains explicit; a reviewer cannot grant it. `ready` ends this Flow, while
user-authorized delivery remains a separate capability.

#### Coordinated implementation and final consumer checks {#development-coordinated-implementation-and-final-consumer-checks}

A coordinating Module can have both its own code tasks and separately bound submodule or dependency
tasks. Its original plan and task identity remain intact; local code tasks do not recursively open
a new development loop for the same Module. Each child is specified, planned and implemented from
its own complete Module contract and the implementation files its own entries bind.

Within a coordinated change, nested loops finish explicit code drafts. The enclosing coordinator
waits for all writers, including its own coordination code, before checking the final candidate.
This permits a shared implementation to change without requiring unfinished consumers to pass
prematurely. Finalization checks each recorded component and all affected implementation users in
separate contexts, records current checks/reviews and rejects missing or stale evidence before ready.
The host-only defer_component_checks flag controls this sequencing; it is not a request field or
a way for a caller to bypass final validation or delivery checks.

Once all writers finish, the host performs bounded finalization through each component’s normal
validation and code-review repair loop. A repair that changes shared files invalidates earlier
consumer evidence; finalization repeats for all participants until their implementation revisions
are stable. Incompatible contracts or exhausted repair attempts leave the candidate incomplete.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary flow is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new flow requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
