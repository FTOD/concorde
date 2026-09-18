# Review execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Review Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Harness](../module.md#terminology) | Defined in Concorde Framework. |
| [Issue](../module.md#terminology) | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology) | Defined in Concorde Framework. |
| [Review coverage](module.md#terminology) | Defined in Review. |
| [Advisory finding](module.md#terminology) | Defined in Review. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Capsule](../harness/module.md#terminology) | Defined in Harness. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Public operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

## Independent review operation {#review-independent-review-operation}

The [Development Module](../development/module.md) owns admission. Its [common invocation envelope](../development/interfaces.md#operation-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/execution-reference.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
`concorde-review` is a public Operation with discover context selection requiring task and review_mode=spec|code, with
optional target/focus routing hints, constraints and current-worktree change_id. A new standalone
request uses Spec-only router discovery to select one owning Module, then starts a fresh
read-only reviewer. A composing operation may supply its trusted bound target without repeating
discovery; a current-change resumption supplies both target_id and change_id. The public launcher
and Studio admit this operation directly. Review runs in the current worktree without creating
a development change or requiring a preexisting Issue record. The host may persist reports and existing
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

Private `concorde-review-stage-context@4` contains a full context snapshot and a
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

The reviewer returns `concorde-review-stage-result@2` bound to context_id, input_digest and mode, with
representative_tasks, issues, answer and status=no_findings|findings|incomplete. Each Issue judgment
carries its accepted immutable receipt, severity=blocking|advisory and affected_task. The [Issues Module](../issues/module.md) reporting
service checks the problem's evidence locations and known contract owner against the admitted
context; final admission rejects unreported, ungranted or duplicate references. The host derives
task blockers from blocking judgments instead of requiring a duplicated gap object. Reports and
answers contain contract-level descriptions/locations, never raw code, patches or logs.

The host rejects mismatched identities, foreign locations, duplicate IDs/tasks, a clean result with
Issue judgments, a findings result without evidence, and completed review without representative tasks.
It rechecks the context, source/input/configuration identities and frozen capsule after execution.
It publishes `concorde-review-result@2` adding target/focus, revision and
semantic_completeness=not_proven. Public response `reviews` contains these typed results, and artifacts
reference saved review reports. Native receipts and failure diagnostics remain separate host records.

| Review state | Skill outcome and progression |
| --- | --- |
| no_findings with nonempty coverage | completed; bounded review succeeded |
| findings, all advisory | completed; Issue references retained for the consumer |
| blocking missing/conflicting contract Issues | spec_incomplete; dependent steps pause |
| other blocking Issues | conflicting; the caller selects bounded repair or a stop |
| incomplete coverage, invalid result or process failure | failed; an incomplete report, never a clean result |
| describe-policy | described with not_run; no execution or persistence |
| run_reviews=false | host records skipped; no reviewer runs |

The table maps review reports to the Review response's domain `outcome`. An interrupted
reviewer still produces an `incomplete` review report and a `failed` Review domain outcome.
The trusted host separately preserves the `cancelled` or `limit_exhausted` execution
classification supplied by the [Harness Module](../harness/module.md), as defined in its
[execution outcomes](../harness/execution-reference.md#execution-outcomes), for the enclosing Graph, persisted candidate lifecycle and final events, following the
[Development boundary](../development/interfaces.md#operation-execution-boundary).
Ordinary reviewer failures remain `failed`.

These execution/lifecycle classifications are not additional values of the published
review-status or common operation-envelope status fields; their existing layouts and values
remain unchanged. An interrupted review never satisfies completion, permits dependent work
to advance or selects an automatic retry.

Every mode and target uses a separate session. A Module whose entities list implementation files
receives its own local code review of those files and the scoped code changes, whether or not it
has recorded component work. A Module with recorded component work additionally requests
cross-target review: the host validates each Module's declared relationship, starts its own reviewer from
its recorded task and admitted collection, then aggregates only typed results; a component's code
never enters the aggregating Module's reviewer. Spec review always assesses the Module itself. A
Module whose entities list no implementation files is reviewed in code mode only through its
recorded components and returns unsupported when it has none. The consumer selects local or recorded-component review only after the required component admission; this provider does not choose development-stage ordering.

#### Scope and feedback relevance {#review-scope-and-feedback-relevance}

`concorde-review` uses separate fresh Spec and code reviewers. Spec review sees the complete owned and directly referenced Specs, task and scoped Spec patches; code review additionally sees only the owning
target's registered implementation files, the files its declared entries currently bind, and scoped
code patches. Neither has project write authority.
A changed file listed by several Modules is reviewed once per listing Module, each from that
Module's own contract: the host selects the peers of a code review from the files of the reviewed
Module that differ from the candidate base, so a shared file the candidate did not touch adds no
peer review, and without a known base revision every covering Module is a peer. A graph-composed
continuation reuses a consumer's revision-bound review when its intent, constraints and admitted
input are unchanged, including the consumer reviews that admitted a Spec candidate before its bytes
were applied; an explicit standalone review is always fresh for the owner and every consumer. Verification declarations in the reviewed files are judged only for scenarios present
in the reviewing Module's admitted context: a test that declares such a scenario without
exercising its steps is a defect, while a declaration naming a scenario outside that context is
assessed by the owning Module's review and is neither a defect nor a gap for the reviewing Module.
A Module never gains a reference to a consumer's documents merely so its reviewer can read them.
Each reviewer resolves its model Operation's execution profile and Harness under read-only permissions.
The host records input versions, coverage, immutable Issue judgments and completion. No-findings,
findings, incomplete, not-run and skipped are distinct, and all conclusions remain task-specific.

The complete collection is the review's information boundary, not an instruction to repair every
independent operation it describes. Representative tasks derive from the admitted request and its
constraints, including necessary dependencies, compatibility and affected consumers. A blocking
finding explains how its contract or behavior defect prevents that task or violates an obligation
the change must preserve. Unchanged contracts can block dependent work, and changed contracts can
introduce regressions beyond the named feature. A request to retain existing independent behavior
does not alone require completing every pre-existing edge-case contract. Concrete independent
defects remain advisory findings with their scope reasoning and uncertainty; they are not erased
or represented as complete contracts. A broad audit can make those same contracts task-relevant.
The reviewer makes this semantic assessment from admitted inputs; the Host neither filters findings
by changed paths nor rewrites their severity. Required coverage, gap and freshness gates still apply.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary graph is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new graph requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
