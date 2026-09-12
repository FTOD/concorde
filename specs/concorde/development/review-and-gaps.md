```concorde-document
{
  "id": "document.development.review-and-gaps",
  "owner": "module.development",
  "main_visible": true
}
```
# AI review feedback and gap handling


`concorde-review` uses separate fresh Spec and code reviewers. Spec review sees the complete owned and directly referenced Specs, task and scoped Spec patches; code review additionally sees only the owning
target's registered implementation files, the files its declared entries currently bind, and scoped
code patches. Neither has project write authority.
Each reviewer resolves a separate Agent definition and Harness under read-only permissions.
The host records input versions, coverage, concrete findings, gaps and completion. No-findings,
findings, incomplete, not-run and skipped are distinct, and all conclusions remain task-specific.

The complete collection is the review's information boundary, not an instruction to repair every
independent capability it describes. Representative tasks derive from the admitted request and its
constraints, including necessary dependencies, compatibility and affected consumers. A blocking
finding explains how its contract or behavior defect prevents that task or violates an obligation
the change must preserve. Unchanged contracts can block dependent work, and changed contracts can
introduce regressions beyond the named feature. A request to retain existing independent behavior
does not alone require completing every pre-existing edge-case contract. Concrete independent
defects remain advisory findings with their scope reasoning and uncertainty; they are not erased
or represented as complete contracts. A broad audit can make those same contracts task-relevant.
The reviewer makes this semantic assessment from admitted inputs; the Host neither filters findings
by changed paths nor rewrites their severity. Required coverage, gap and freshness gates still apply.

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
that step's old gaps and retains history. Changed admitted review inputs, including reviewer
instructions, also permits fresh review without first erasing its old gaps. Only an accepted,
completed review without gaps or blocking findings resolves that phase's old gaps from a different
review input digest; failed or incomplete reassessment leaves them open, and a repeated gap records
its new observation and review input digest on that gap's own history entry. Lifecycle status,
snapshot context IDs and replacement of the latest review record do not change that identity.
An unchanged-input standalone review may report its own findings but cannot resolve the required
gap. Legacy gap entries without a recorded review input digest retain their Spec-revision gate;
the Host does not infer their original identity from a mutable latest-review record. Unchanged
review inputs still wait, and other phases' prerequisite gaps remain gates.
Spec authoring can itself supply the repair. A durable gap
can be discovered through reflections-triage `status` gap_records and explicitly captured by
`record-gaps` using those returned IDs; capture does not resolve the gap,
change its owner, approve a fix or start implementation.

Review results are invalidated by changed relevant Spec, registered code, task/focus/constraints,
configuration, role instructions or host review runtime, candidate HEAD/base/change identity, or
scoped patches. Required evidence is rechecked at readiness/delivery, using the same worktree
lifecycle. A failed process or incomplete review never becomes an empty successful review.

Read-only reflection investigation receives the selected Module contract and explicitly granted
code files. It receives no write permission for those files.
Code-writing tasks separately receive the Module's own listed implementation entries, with write
authority limited to exactly those paths: an exact file, or the whole directory a directory prefix
names, so a new file below it needs no separate declaration.

The review input identity includes the selected Agent/Mode binding digest. Changes to the mode
contract, common or selected instructions, authority ceiling or recorded build invalidate review
evidence. Sharing a definition with an author does not admit the author conversation or artifacts.

Canonical interface edits invalidate review for the owner and each old/candidate context consumer,
including those that reference the whole provider Module. Each reviewer retains foreign definition
ownership and assesses local reliance/obligations. Repairing that definition belongs to its sole
owner; inclusion grants no write permission or provider code. Reference-only changes also require
fresh evidence even when the complete file set is unchanged.
