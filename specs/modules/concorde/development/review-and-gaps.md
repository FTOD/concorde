```concorde-document
{
  "id": "document.development.review-and-gaps",
  "targets": [
    "module.development"
  ],
  "main_visible": true
}
```
# AI review feedback and gap handling


`concorde-review` uses separate fresh Spec and code reviewers. Spec review sees the complete Target
Spec and Shared Specs, task and scoped Spec patches; code review additionally sees only the owning
target's registered implementation files and scoped code patches. Neither has project write authority.
Each reviewer resolves a separate Agent definition and Harness under read-only permissions.
The host records input versions, coverage, concrete findings, gaps and completion. No-findings,
findings, incomplete, not-run and skipped are distinct, and all conclusions remain task-specific.

Development defaults `run_reviews` to true: Spec review follows authoring and precedes planning;
code review follows implementation/checks and precedes ready. An explicit `run_reviews=false`
records each skip. Once required, a review cannot be disabled by a resumed fast loop. Blocking contract gaps or
behavior findings prevent advancement until the Graph admits a repair or clarification path; advisory
findings remain available through result artifacts. AI feedback identifies the reviewed revision and
can select only the transitions allowed by the Graph. It cannot grant human acceptance or wider permissions.
Module changes review their own Spec before planning, then each affected component's full Spec and
code in that component's own session. Host aggregation carries only their typed results.

Any necessary missing/ambiguous contract encountered during explanation, planning, task authoring or
implementation uses the same gap fields. Queries report gaps; development records and deduplicates
them by target/task/phase/question/blocked step/needed contract in the existing change state, with
Spec revision and observed contexts. Unrelated work cannot erase unresolved gaps. Retrying an unchanged
blocked step waits for its contract repair. After a Spec change, a fresh successful assessment resolves
that step's old gaps and retains history. Spec authoring can itself supply the repair. A durable gap
can be discovered through reflections-triage `status` gap_records and explicitly captured by
`record-gaps` using those returned IDs; capture does not resolve the gap,
change its owner, approve a fix or start implementation.

Review results are invalidated by changed relevant Spec, registered code, task/focus/constraints,
configuration, role instructions or host review runtime, candidate HEAD/base/change identity, or
scoped patches. Required evidence is rechecked at readiness/delivery, using the same worktree
lifecycle. A failed process or incomplete review never becomes an empty successful review.

Read-only reflection investigation receives the selected Module contract and explicitly granted
code files. It receives no write permission for those files.
Code-writing tasks separately receive the Module's own listed implementation files, with write
authority limited to exactly those paths.
