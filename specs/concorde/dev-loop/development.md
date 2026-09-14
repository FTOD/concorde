```concorde-document
{
  "id": "document.development.development",
  "owner": "module.dev-loop",
  "main_visible": true
}
```
# Development Agent Flow and revision loops

A developer supplies intended behavior and constraints for one top-level candidate change.
`concorde-specify-loop` independently routes, authors or revises, and reviews the Spec. It ends
with a completed Spec result, retaining blockers and review evidence in the candidate worktree.
`concorde-dev-loop` calls that capability, then coordinates context assessment, planning, tasks,
implementation and checks. The same task and change can continue from specify-loop into dev-loop
without repeating accepted authoring or current reviews. `specify=false` skips authoring; `run_reviews=false` records review
skips where no earlier requirement exists. The specification flow can complete independently; dev-loop adds its own development lifecycle.
Its successful output is a ready candidate, not an automatic merge.

[Planning task acceptance](../planning/tasks.md) and
[Implementation completion](../implementation/implementation.md) define the provider boundaries.

## Explicit task-scope recovery

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

## Stages and outcomes


With reviews enabled, the development loop follows these transitions. Explicit skips retain
their own evidence states; delivery is a separately invoked capability after Ready.
Specified and SpecReviewed belong to the independently callable specify-loop. Its successful
return lets the caller stop with the Spec or lets dev-loop proceed to Planned.

```mermaid
stateDiagram-v2
  accTitle: Development, repair and separately authorized delivery
  accDescr: Development reaches Ready after current checks and configured reviews. Contract gaps wait for a Spec revision and code defects select bounded repair. Separate delivery stages a branch; merging it into the primary branch requires another explicit request.
  [*] --> Specified
  Specified --> SpecReviewed: independent Spec review
  SpecReviewed --> Gap: necessary contract missing
  Gap --> [*]: stop for explicit Spec repair and a fresh invocation
  SpecReviewed --> Planned: review current and context sufficient
  Planned --> Tasks: plan accepted
  Tasks --> Implemented: acceptance fulfilled
  Tasks --> Gap: necessary contract missing
  Implemented --> Checked: checks pass on current bytes
  Checked --> CodeReviewed: independent code review
  CodeReviewed --> Ready: required evidence current and no blockers
  CodeReviewed --> Tasks: code defect needs repair
  Ready --> Delivered: separate delivery verifies and stages a branch
  Delivered --> PrimaryMerged: explicit primary-session merge request
  Implemented --> Failed: checks or execution fail
  Failed --> [*]: stop and preserve candidate
  Delivered --> [*]
  PrimaryMerged --> [*]
```


## AI and human feedback

Author, assessor, planner, task author, implementation and reviewer invocations MUST resolve their
own Agent definitions and effective Harnesses. Shared Flow state contains admitted outputs and
feedback, not their private transcripts. Review findings identify the input revision and the
required repair. A code defect selects an implementation repair and another review; a necessary
Spec gap selects a clarification or authorized Spec-authoring path before implementation resumes.

The Flow MUST record which AI finding or human decision selected a transition. Repeated unchanged
blocking feedback waits for new information or stops at the declared limit. Human changes to intent
create a revised task and invalidate dependent plans and evidence. Human acceptance required for
another transition remains explicit; a reviewer cannot grant it. `ready` ends this Flow, while
user-authorized delivery remains a separate capability.

## Failure and recovery

Candidate creation precedes routing. A change ID identifies a worktree, not a completed route.
An unbound handoff resumes coordinator selection using the recorded task and constraints; optional
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
`concorde-dependencies` declarations. Before planning, deterministic context solving rejects any
missing direct registry relationship as a Module-owned Spec gap and reports inconsistent entries as
conflicting. Each component
receives its own explicit task, local authoring invocation and fast loop. All affected
consumer/provider contract views must agree before any component implementation begins. Component
ancestry and scope membership never grant extra reads. Successful component revisions are checked
again before Module delivery.

Checks use deterministic argv declared by project configuration. Harness enforces read-only project
access for the entire check process tree and gives each check external temporary/cache/report space;
unsupported enforcement blocks execution. Development persists output outside that sandbox, and
raw logs stay out of later Spec-only sessions. A stale Spec, changed task intent, modified
code, failed check or missing completion blocks delivery and preserves the candidate worktree. Resuming a
change reuses its target records and typed artifacts but starts a fresh agent session. The host does not copy unrelated
conversation or free-form predecessor output into context.

## Coordinated implementation and final consumer checks

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

## Candidate lifecycle and review policy

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

Common [gap history](../development/review-and-gaps.md) retains attributed blockers and accepts resolution only after current successful output. The flow stops dependent work until those conditions hold.

A change's `status` may also become `cancelled` or `limit_exhausted` after an executor outcome of
the same name (`execution_cancelled`/`execution_limit`), distinguishing a cancelled or time-limited
agent process from an ordinary `blocked`/`failed` outcome; the candidate is preserved for repair or
resumption in every case. A development loop stopping for a necessary Spec gap, or for blocking
code-review feedback that repeats unchanged across a bounded repair attempt, records status
`waiting` instead of the generic `blocked`: both name a concrete point where a human decision or a
Spec/code change is needed before the loop can usefully resume.
During dev-loop, the initial Module Spec review is local. Component reviews occur in separately coordinated component loops after reconciliation, and all writers finish before final shared-consumer checks.
