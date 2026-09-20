# Review execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Review Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term                                                    | Meaning / definition           |
| ------------------------------------------------------- | ------------------------------ |
| [Spec](../module.md#terminology)                        | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology)                    | Defined in Concorde Framework. |
| [Worker](../module.md#terminology)                      | Defined in Concorde Framework. |
| [Host](../module.md#terminology)                        | Defined in Concorde Framework. |
| [Grant](../module.md#terminology)                       | Defined in Concorde Framework. |
| [Harness](../module.md#terminology)                     | Defined in Concorde Framework. |
| [Issue](../module.md#terminology)                       | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology)                     | Defined in Concorde Framework. |
| [Review coverage](module.md#terminology)                | Defined in Review.             |
| [Advisory finding](module.md#terminology)               | Defined in Review.             |
| [Candidate](../module.md#terminology)                   | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology)                    | Defined in Concorde Framework. |
| [Capsule](../harness/module.md#terminology)             | Defined in Harness.            |
| [Snapshot](../module.md#terminology)                    | Defined in Concorde Framework. |
| [Graph](../module.md#terminology)                       | Defined in Concorde Framework. |
| [Operation](../module.md#terminology)                   | Defined in Concorde Framework. |
| [Public operation](../operations/module.md#terminology) | Defined in Operations.         |
| [Skill](../module.md#terminology)                       | Defined in Concorde Framework. |

## Independent review operation {#review-independent-review-operation}

[Harness admission](../harness/admission.md) owns the entry. Its [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
`concorde-spec-review` and `concorde-code-review` are separate public Operations requiring an explicit
Module target_id and task, optional same-owner focus_id, constraints and current-worktree change_id.
The host deterministically resolves that selection; no router, inferred owner or context expansion
precedes the fresh reviewer. Their closed request schemas have no review_mode field. Each entry
selects only its own reviewer; the retired concorde-review operation and its request/response types
have no alias. The public launcher
and Studio admit this operation directly. Review runs in the current worktree without creating
a development change or requiring a preexisting Issue record. The host may persist reports and existing
change evidence, but reviewers receive no project write authority.
Spec review uses the complete admitted owned and directly referenced Specs, Protocol/kind rules, task and scoped changes to any document included in that context. Code review uses those
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
`concorde-review-input@1` with review_mode, input_digest, revision and changes. review_mode remains
an internal evidence discriminator fixed by the selected Operation, never a public request selector.
Each change is
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

| Review state                                           | Skill outcome and progression                            |
| ------------------------------------------------------ | -------------------------------------------------------- |
| no_findings with nonempty coverage                     | completed; bounded review succeeded                      |
| findings, all advisory                                 | completed; Issue references retained for the consumer    |
| blocking missing/conflicting contract Issues           | spec_incomplete; dependent steps pause                   |
| other blocking Issues                                  | conflicting; the caller selects bounded repair or a stop |
| incomplete coverage, invalid result or process failure | failed; an incomplete report, never a clean result       |
| describe-policy                                        | described with not_run; no execution or persistence      |

The table maps review reports to the Review response's domain `outcome`. An interrupted
reviewer still produces an `incomplete` review report and a `failed` Review domain outcome.
The trusted host separately preserves the `cancelled` or `limit_exhausted` execution
classification supplied by the [Harness Module](../harness/module.md), as defined in its
[execution outcomes](../harness/execution-reference.md#execution-outcomes), for the enclosing Graph, persisted candidate lifecycle and final events, following the
[admission boundary](../harness/admission.md#operation-execution-boundary).
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
recorded components and returns unsupported when it has none. Explicit component membership comes from accepted component_revisions and the corresponding parent tasks, not retired coordination workflow records. Each component uses the task derived from those accepted tasks and the caller constraints. Current aggregate evidence requires the exact component/changed-file peer set, matching intent, complete coverage, nonblocking findings and intact current report bytes. Aggregate records additionally bind the parent's complete current Spec and target/task/focus/constraints; changed parent inputs during aggregation reject acceptance, and later changes invalidate reuse. A code-free parent has no invented local code-review artifact; its selected requirement is discharged only by that complete nonempty aggregate. Review never refreshes implementation completion. The consumer selects local or recorded-component review only after the required component admission; this provider does not choose development-stage ordering.

#### Scope and feedback relevance {#review-scope-and-feedback-relevance}

`concorde-spec-review` and `concorde-code-review` each use their own fresh reviewer. Spec review sees the complete owned and directly referenced Specs, task and scoped Spec patches; code review additionally sees only the owning
target's registered implementation files, the files its declared entries currently bind, and scoped
code patches. Neither has project write authority.
A changed file listed by several Modules is reviewed once per listing Module, each from that
Module's own contract: the host selects the peers of a code review from the files of the reviewed
Module that differ from the candidate base, so a shared file the candidate did not touch adds no
peer review, and without a known base revision every covering Module is a peer. Explicit review is
always fresh for the owner and every consumer; later checks admit only current revision-bound evidence.
Verification declarations in the reviewed files are judged only for scenarios present
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

#### Mandatory terminology semantic coverage

Every Spec review enumerates imported terminology across all admitted reading documents, including
unchanged and directly referenced units. For each local restatement, compare its meaning with its
direct canonical definition in the granted complete defining unit. Different wording is permitted;
text equality is not a requirement. Assess scope, conditions, constraints, exceptions and obligation
strength, and detect consumer-specific behavior incorrectly presented as common meaning. Source-only
rows require canonical-source checks but have no local restatement to compare. An intermediate
restatement is not a canonical source, and no link grants additional context.

The reviewer records terminology coverage in representative_tasks and summarizes checked term/source
locations, semantic differences and unresolved comparisons in answer. No imported restatements is an
explicit coverage outcome, not an omitted check. Concrete differences are reported once through
report_issue with both locations and normal task-relevance severity. Missing or ambiguous necessary
meaning is an attributed gap; unfinished required comparisons produce incomplete coverage rather
than a clean conclusion. Model review is bounded semantic evidence, not a deterministic proof of
equivalence, and structural validation does not substitute for this check.

#### Reference changes and affected consumers {#review-reference-changes-and-affected-consumers}

Before review/readiness, compute affected Spec consumers from the union of old and candidate
one-level contexts. A provider document edit, ownership transfer, changed reference or changed
provider document inventory invalidates each affected context and dependent plan/review. Changed
code additionally uses the independent listing reverse index. A reference is never a code grant.
Review attribution follows the [canonical review-result interface](review-result.md). The calling
agent selects provider repairs and edits the owned Spec, paired metadata and registry directly;
included-file read scope never grants a bounded worker authority to write the provider definition.
The host retains old and current consumers for evidence rechecks. Direct edits are not reviews and
do not refresh plans, review records or readiness. Planning and task admission that requires Spec
review checks the complete current owner/consumer scope, not only the owner report.

A public review matching the managed target's accepted intent records that selected mode as required
before execution. A failed or stale selected review therefore cannot be bypassed by validation;
unrelated review questions do not change the accepted intent or downgrade existing requirements.
When task authoring explicitly selects repair_review, it must identify the current host-recorded
blocking code review, with matching artifact bytes, target/focus, task/constraints, input digest,
completed coverage and resolvable Issue receipts. Replaced reports, forged digests, incomplete
coverage and changed code, Specs or instructions fail admission. Implementation rechecks the same
feedback before using it; a replacement plan or non-review task list clears old repair feedback
without clearing review requirements or inventing successful evidence.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Its behavior is realized in
its own package `src/concorde/review/`, bound by its adapter entity together with its `operations/` declaration; this Spec boundary
does not itself create an Agent grant or configurable arbitrary graph; public exposure is explicit in the catalog. Host admission, phase
artifacts and permissions remain mandatory. A new graph requires declared composition and an
implementation of its sequencing, artifact admission, recovery and completion policies before it
can execute. [Harness admission](../harness/admission.md) realizes the common entry and invocation
host, and [Operations](../operations/execution-reference.md#graphs-dispatch-graphs) the dispatch
that reaches this provider.
