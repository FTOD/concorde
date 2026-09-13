```concorde-document
{
  "id": "document.review.review",
  "owner": "module.review",
  "main_visible": true
}
```

# Independent review capability

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
`concorde-review` is a public Capability with discover context selection requiring task and review_mode=spec|code, with
optional target/focus routing hints, constraints and current-worktree change_id. A new standalone
request uses Spec-only coordinator discovery to select one owning Module, then starts a fresh
read-only reviewer. A composing capability may supply its trusted bound target without repeating
discovery; a current-change resumption supplies both target_id and change_id. The public launcher
and Studio admit this capability directly. Review runs in the current worktree without creating
a development change or requiring a Reflection record. The host may persist reports and existing
change evidence, but reviewers receive no project write authority.
Spec mode uses the complete admitted owned and directly referenced Specs, Protocol/kind rules, task and scoped changes to any document included in that context. Code mode uses those
contracts, the target's exact current registered implementation-file enumeration and scoped code
changes. Both roles have empty write grants, no network/credentials, fresh sessions, and empty
predecessor input. Code review does not reuse implement's writable policy.

The host compares the candidate's current bytes, including uncommitted and untracked owned files,
against this managed change's recorded base_commit; an unmanaged Git checkout uses its current HEAD.
An unversioned root has null baseline/head and its current granted files are new input. History is
read only from that repository's Git objects and scoped to the current target grant. No other worktree
supplies content. Deleted files under a current grant appear as scoped changes; removed or unrelated
grants never expose their old contents. Full admitted current documents always accompany Spec review,
even when a focus or patch names only a small portion.

Private `concorde-review-stage-context@2` contains a full context snapshot and a
`concorde-review-input@1` with review_mode, input_digest, revision and changes. Each change is
`{path, patch}`; binary changes carry only digest markers. The revision has spec_digest,
nullable implementation_digest, nullable baseline and nullable head. spec_digest binds the selected
target descriptor, ownership, explicit references, all inclusion reasons, pinned Protocol and ordered
complete document byte digests, including referenced provider documents. Code mode additionally
binds every currently enumerated implementation path/byte digest. input_digest covers these values,
scoped changes, absolute current worktree/branch, target/focus, task/constraints/change identity,
initialized configuration, canonical
reviewer instructions/effects and host review/context/permission/executor runtime bytes. Context ID
additionally records the actual frozen lifecycle observation. Lifecycle phase changes alone do not
invalidate an otherwise identical task review; changed relevant input does. Old result artifacts
remain audit history and cannot pass a current gate.

The reviewer returns `concorde-review-stage-result@1` bound to context_id, input_digest and mode, with
representative_tasks, findings, gaps, answer and status=no_findings|findings|incomplete. A finding
has unique id, severity=blocking|advisory, target_id, document (an exact admitted Markdown path),
contract, location={path,line}, problem and affected_task. line is a positive integer or null.
Its contract document must be in the complete collection, and its location must be admitted Spec or
code/change scope. A blocking Spec finding requires a gap with blocked_step=affected_task and
needed_contract=contract. Gap target/context provenance is verified and filled by the host. Missing
contracts during code review also use gaps; a concrete code defect can block without a Spec gap.
Findings and answers contain contract-level descriptions/locations, never raw code, patches or logs.

The host rejects mismatched identities, foreign locations, duplicate IDs/tasks, a clean result with
findings/gaps, a findings result without evidence, and completed review without representative tasks.
It rechecks the context, source/input/configuration identities and frozen capsule after execution.
It publishes `concorde-review-result@1` adding target/focus, revision and
semantic_completeness=not_proven. Public response `reviews` contains these typed results, and artifacts
reference saved review reports. Native receipts and failure diagnostics remain separate host records.

| Review state | Skill outcome and progression |
|---|---|
| no_findings with nonempty coverage | completed; bounded review succeeded |
| findings, all advisory and no gaps | completed; findings retained for the consumer |
| concrete necessary gaps | spec_incomplete; dependent steps pause |
| blocking code findings without gaps | conflicting; dependent steps pause |
| incomplete coverage, invalid result or process failure | failed; an incomplete report, never a clean result |
| describe-policy | described with not_run; no execution or persistence |
| run_reviews=false | host records skipped; no reviewer runs |

Every mode and target uses a separate session. A Module with recorded component work can request
cross-target review: the host validates each Module's declared relationship, starts its own reviewer from
its recorded task and admitted collection, then aggregates only typed results. Spec review also
assesses the Module itself; code review never gives the Module code. A Module without recorded
component work returns unsupported for code review. The consumer selects local or recorded-component review only after the required component admission; this provider does not choose development-stage ordering.

## Scope and feedback relevance

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
