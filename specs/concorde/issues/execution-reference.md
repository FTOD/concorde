# Issues execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Issues Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term                                              | Meaning / definition                           |
| ------------------------------------------------- | ---------------------------------------------- |
| [Issue](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Blocker](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Candidate](../module.md#terminology)             | Defined in Concorde Framework.                 |
| [Evidence](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Disposition](lifecycle.md#terminology)           | Defined in Solving a recorded problem.         |
| [Worker](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Host](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Grant](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Spec](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Ready](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Delivery](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Worktree](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Graph](../module.md#terminology)                 | Defined in Concorde Framework.                 |

## Issue records and reporting {#issues-issue-records-and-reporting}

Issues are branch-local problem records, not implementation tasks or graph-control signals. A
reporter classifies a concrete observation as `bug`, `gap` or `limitation`. A bug is a defect,
vulnerability or failure; a gap is an implementation/Spec mismatch, a conflict between Specs, or
a missing necessary contract; a limitation is an internally consistent current behavior whose
operation or usability is insufficient. Prefer gap when an explicit consistency conflict is the
subject of the report. Only gap has a subtype: `implementation-spec-mismatch`, `spec-conflict` or
`missing-contract`. Classification may change with new evidence without replacing the issue.

<a id="entity.reflections.issue-store"></a>

The Issue store retains its stable document and entity identities through transfer to the Issues
Module; the legacy identity spelling does not preserve a triage API. It owns durable observations and disposition history under `.concorde/issues/`.
Reports contain a title, description, impact, basis, admitted evidence locations and the known
contract owner's Module identity, or null when unknown. The trusted caller supplies invocation,
agent, operation, phase, reporting target, context digest, optional change and HEAD. Reporting
context and contract ownership remain distinct. Creating a record does not require a managed change,
a reproduction verdict, an investigation plan, a repair proposal or human approval.

### Store boundary {#issues-store-boundary}

`concorde-issue-report@1` and `concorde-issue-receipt@1` publish the report and receipt shapes
below. `report_issue(root, report, source)` accepts the closed shapes in the issue model. The host, not a
worker parameter, supplies `source`. `report_key` is a reporter-local stable key for retrying the
same observation. `type`, nullable `subtype`, `title`, `description`, `impact`, `basis`, nullable
`owner_target_id`, and `evidence` are required; each evidence item has `path` and `description`.
Strings are nonblank and paths are canonical project-relative POSIX paths. `issue_id` and
`expected_revision` are either both absent for creation or both present for appending an observation.
The caller must separately enforce evidence visibility and reporting authority; a syntactically
safe path is not a grant. Repository validation parses every active Issue, rejects corrupted
records with `CONCORDE-ISSUE-001`, and includes record byte digests in its source identity. Historical
provenance does not require a former owner to remain in the current registry. Reports are limited
to 64 KiB of canonical JSON and records to 16 MiB.
Reference evidence instead of copying large logs or secrets.

An identity has the form `I-` followed by 32 lowercase hexadecimal characters. The host allocates
it from the trusted unique invocation identity and report key without a branch-local counter.
The returned receipt is `{issue_id, report_id, path}`. `report_id` binds the exact accepted report
and its host-issued provenance. The receipt refers to that immutable observation even if a later
report reclassifies the issue or its disposition changes. Repeating identical input returns the
same receipt; reusing a key with different input fails without replacing the earlier observation.
Similarity alone never merges reports. An explicit append targets one existing open issue and
requires its current exact-byte SHA-256 revision; a completed append's retry remains idempotent.

`read_issue(root, id)` returns the record and its current byte revision. `list_issues(root,
target_id=None, status=None)` returns metadata, optionally filtered by reporting target or current
known owner and by open/closed state. Reads of an absent collection return an empty list and create
nothing. Unknown identities, malformed records, mismatched digests and symlink paths are rejected.
`resolve_report(root, receipt)` retrieves the immutable observation rather than silently using the
latest issue description. These host library operations neither launch a model nor execute Git.

Each UTF-8 Markdown file has an identity heading and a single JSON fence containing the version-2
record: `id`, `status`, `reports`, `dispositions` and `schema_version`. The JSON is the sole record
content, not a duplicate prose projection. A report stores its id, timestamp, report payload and
source. Dispositions preserve reason, note, evidence references, actor, timestamp and nullable
duplicate target. Record status must agree with disposition history. Editing an immutable report
without reconciling its digest is invalid; append new observations instead.

Schema 2 uses `operation` in host-issued provenance. Historical schema-1 records retain the old
`capability` storage field and remain readable, with their exact bytes, identities and observation
digests unchanged. This is historical evidence support, not a current wire alias. Append,
disposition, rendering as current data and disposition recovery refuse schema 1 with
`unsupported_issue_version`. To continue work, explicitly create a new current Issue with evidence
referencing the historical record; do not rewrite old observations or claim they were resolved.
Unknown versions and corrupted historical records remain invalid.

### Worker reporting service {#issues-worker-reporting-service}

`IssueReporter` binds the project root, source identity, admitted contract owners, evidence paths
and explicitly selected issue identities before a worker starts. The `report_issue` worker tool
sends only a report and receives `{receipt, revision}`: the immutable observation receipt plus the
current record byte digest, so an admitted follow-up can supply `expected_revision`. The receipt
identity stays unchanged on an identical retry; the current revision may change after later reports
or dispositions. It cannot supply provenance, choose a
filesystem root or change issue disposition. An owner outside the admitted Spec context or an
evidence path outside the phase's admitted Spec/code/change locations is refused. Unknown ownership
is represented by null. A worker may append only to an explicitly admitted issue or one it already
reported in the same invocation. Helper children return observations to their parent for verification
and do not receive the reporting tool.

Reporting is nonterminating and has no implicit effect on the stage outcome. In particular, a
worker can report multiple nonblocking gaps and still complete its task. Final blockers and review judgments reference immutable receipts; their task-local effects remain
separate from the problem content and disposition. A pure question can explicitly report an Issue without receiving code or Spec write
authority; a query of stored Issue metadata and a policy preview do not create observations.
Already accepted reports survive malformed final results, process failure, cancellation and time
limits. The host emits `issue_reported` receipts even when the worker fails; these events do not
establish stage completion. The host never rolls back accepted reports merely because a later
`submit_result` fails.

### Persistence and concurrency {#issues-persistence-and-concurrency}

A host-local file lock under `.concorde/runs/` serializes read-modify-write transactions in the
current worktree. A staged file is flushed and atomically renamed, and the containing directory is
synced before success is acknowledged. A write failure is not reported as success; after an
uncertain acknowledgement the same key may be retried safely. Current-byte checks reject stale
appends and dispositions instead of overwriting concurrent changes. Query operations do not take
creation locks or create directories. Record writes do not set candidate phase, task outcome,
validation evidence, review results or gap resolution.

The issue files are ordinary Git-versioned project records. Separate worktrees or clones retain
independent records until changes are explicitly integrated. Reports from independent invocations
have distinct identities; no mutable high-water index creates a cross-branch allocation conflict.
Closing a record in a candidate means solved or disposed in that branch, not in primary. A success
receipt establishes persistence in the worktree, not a Git commit, backup or completed delivery.

### Disposition boundary {#issues-disposition-boundary}

`dispose_issue(root, id, expected_revision, reason=..., note=..., evidence=..., actor=...,
duplicate_of=None, duplicate_revision=None, created_at=None)` is a trusted host operation, not part
of the worker reporting authority. The optional timestamp is issued by the host when it prepares
exact transaction bytes; it is not a worker-supplied report field.
The caller must authorize disposition and assess the evidence before calling. The store validates
current record bytes, a nonempty note, at least one evidence reference, the actor and a valid
transition. Reasons `resolved`, `duplicate` and `not-actionable` close an open record; `reopened`
reopens a closed record. Duplicate requires another existing open canonical issue; a supplied duplicate revision is
rechecked inside the same lock as the disposition, and solving always supplies that revision. Other reasons
cannot carry a duplicate target. Closed records and all their observations remain present.

`disposition_record(record, ...)` prepares and validates a copied record without writing. The
solving host uses its exact timestamp/content for a write-ahead journal and subsequent publication.
`restore_issue(root, id, original_bytes, expected_revision)` is a separate trusted recovery
operation: under the same store lock it restores a valid open before-image only over the exact
expected closing revision, or does nothing when that before-image is already present. Other bytes
are stale, not permission to overwrite. The caller must bind both images and their digests to its
own pending transaction and invalidate any readiness receipt before restoring. Neither helper is
an agent tool or a general-purpose record editing grant. See [recovery](scenarios.md#scenario.issues.disposition-recovery).

The store cannot establish semantic truth from an evidence string. Merely not reproducing once,
using a workaround, writing code without validation or completing an unrelated task is not a
resolution. Disposition never substitutes for required review or final candidate verification.
An authorized solving graph may make evidence-grounded dispositions without mandatory human
approval; genuinely unresolved design or product decisions remain for the developer. Solving-graph
admission and verification are separate from this storage boundary.

### Precise specifications {#issues-precise-specifications}

The Issues Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Attributed Issue blockers and host history {#review-and-gaps-attributed-issue-blockers-and-host-history}

A problem is recorded once as an Issue, through the [Issues Module](module.md) host reporting service. Its reporter classifies
it as bug, gap or limitation and supplies evidence within its admitted context. A missing necessary
contract is gap/missing-contract; conflicting contracts and implementation/Spec mismatches have
their respective gap subtypes. Classification alone does not stop a worker or start a repair.

Stage results carry `blockers`: an immutable Issue receipt and a task-local blocked_step. A worker
can report several nonblocking problems and still complete its work; completed/sufficient results
cannot simultaneously claim blockers. Necessary missing contracts use spec_incomplete, other
blocking contradictions can use conflicting, and execution failures remain failed. The [Review Module](../review/module.md) owns
[its independent judgments](../review/execution-reference.md), which reference Issues with severity and
affected_task rather than repeating problem text in findings and gaps.

The host retains candidate `issue_blockers` keyed by change, accepted work scope, Module, phase and Issue identity.
Task text is an observation label, never the problem identity or join key. Root and registered
component/review intents select stable candidate scopes; unrelated standalone work gets its own
scope and cannot block or clear the accepted candidate task. Each relation keeps its exact
report reference, phase input revision, observed contexts and source-ownership/inclusion evidence.
Coordinators forward those references rather than creating another problem or copying it under a
new owner. Replanning cannot strand a dependency solely because its task wording changed.

An unchanged necessary-contract dependency waits for repair. Fresh successful phase assessment
can release the phase's earlier relations after the relevant inputs change; review evidence uses
its independently bound review input identity. Missing original review identity is never inferred
from a later mutable review record. Ordinary code-review defect feedback uses explicitly selected task repair and fresh review
rather than the unchanged-contract wait rule. A completed fresh code review can
release such a dependency even when it corrects an earlier judgment without further code changes.
Failed, incomplete and unrelated assessments cannot erase unresolved dependencies. The retired
`specify` phase is not an executable prerequisite: an accepted current same-intent context
assessment can supersede its correctly attributed obsolete task relation under
[Planning's reassessment rules](../planning/execution-reference.md#assessment-context-assessment),
including missing original revisions and non-contract failures of that retired execution.
Supersession records current sufficiency and retirement of the prerequisite, never old author
success, repaired historical defects or Issue closure. Original attribution and failed observations
stay in history; other retained phases still need their own accepted reassessment. No bytes changing, Issue disposition or unrelated successful review clears a relation.

Releasing a relation means the current work no longer depends on that problem. It does not close
its Issue, imply delivery or erase history. A workaround can therefore permit work to continue
while the original problem remains open. Issue disposition belongs to an explicitly authorized
solving decision with evidence. Neither an open Issue elsewhere in the project nor an advisory
report is a blanket gate on readiness.

Target-bound snapshots expose only their Module's blocker references, never another Module's
problem text. Selecting context receives no implicit Issue file grant. A reporter's known provider owner remains distinct from the consumer task and context
that encountered the problem. Fixing that provider requires the caller's explicit Spec-edit authority or a separately selected implementation boundary. No problem record permits reading outside the admitted context.

Reports are acknowledged during execution and survive cancellation, timeout or invalid final
output. These observations do not establish review coverage or stage success. Description-only
previews launch no reporter. Spec-only workers may explicitly report an Issue, but have no code/Spec write authority. The former two-step gap-history-to-Reflection capture path is removed.

Review inputs remain bound to Spec, code, task/focus/constraints, configuration, worker instructions,
Protocol/build binding, candidate identity and scoped patches. Changed relevant inputs invalidate
required evidence. A report received after preliminary checks changes deliverable metadata; the
ready node refreshes deterministic validation when the Issue collection changed, then rechecks all
ordinary completion gates. It never rewrites a review as passed because an Issue was closed.

The [Issue interface](interfaces.md) owns report, inspection, reopening and solving semantics.
The host passes host-bound gap provenance, retains history and treats capture as a link to
feedback, never as resolution or approval to implement.

## Issue solving lifecycle {#lifecycle-issue-solving-lifecycle}

One solve request selects one Issue and freezes its exact byte revision before preparing work. A
new host-created candidate receives exactly that selected record, even if it is not yet committed;
other local changes are not copied or committed. The solve request is then relayed to that
candidate's own launcher and its result returned to the requesting session, which stays in the
primary worktree. Current-worktree bookkeeping operations never create candidates. Repeating solve on an ordinarily closed Issue reports its existing
disposition, but a candidate-local pending disposition must be recovered before that fast path.

The solver receives the problem and impact plus its complete Module Spec. It chooses whether to
return needed development or Spec repair to the caller, obtain Issue-specific verification, record
a reasoned disposition or identify a precise need for a developer decision. No mandatory triage, reproduction pass or separate investigation
plan precedes every repair. A bug with enough information can return clear implementation intent to the caller; a
code-free Spec gap can return direct contract-edit intent without an implementation investigation. Decisions do not
acquire another Module's context or permissions.

A `develop` or `spec-repair` decision returns `unsupported` with the selected target, intended
behavior and rationale, preserving the open Issue and decision history. The graph executes no
planning, implementation or Spec authoring for that decision. The caller chooses retained
Operations, performs authorized Spec/metadata/registry edits and explicitly retries with current
inputs. Neither a return-to-caller response nor direct editing fabricates verification evidence.
Six decision invocations is the limit per unchanged input state, counted before launch, with history
retained even after cancellation. A fresh external Spec/code change permits a new bounded attempt.
No unbounded nested Issue repair is implied.

Resolution requires fresh Issue-specific independent Spec review and, for a code-owning Module,
code review. A successful unrelated check, single non-reproduction or workaround is not enough.
`duplicate` requires an explicitly admitted current open candidate, with semantic equivalence
explained by the solver. `not-actionable` requires a contract-grounded rationale. These dispositions
need no mandatory human approval. Unsettled product/design choices use `needs-decision` and preserve
the open Issue; execution errors and iteration limits remain distinguishable.

A disposition is written before final ordinary validation. Before publishing that write, the host
saves and syncs a candidate-local write-ahead journal with the change/Issue identities, exact open
before-image, exact intended closed after-image and both byte digests. The prepared timestamp is
reused for publication so a lost write acknowledgement cannot make the after-image unknowable.
The journal remains pending until final validation and the completed checkpoint are saved together.
It is host bookkeeping, never worker input, an implementation grant or a second problem record.

A retry in the owning worktree checks the journal before considering an Issue already closed.
Only the journal's exact before- or after-image is admitted for recovery; the original frozen
selection may be retried across this own write. The host first invalidates any old ready receipt,
then restores its exact before-image under the Issue-store lock, clears stale verification and
continues through fresh solving and validation. Already-restored bytes are a no-op, so a second
interruption during rollback remains recoverable. Attempt counts are retained unless the normal
changed-input or explicit-clarification rule resets them. Recovery never creates another candidate
or moves into another worktree. An older unfinished solver close with no trustworthy journal is
rejected for explicit reconciliation rather than guessed complete or rolled back speculatively.

Ready evidence includes the disposition and all required candidate checks/reviews. On failed final
validation the runtime restores only its own unchanged Issue write, leaves implementation progress
inspectable and does not claim ready. A corrupt journal or a concurrent Issue edit prevents
restoration and is reported rather than overwritten, including an independent developer reopening.
A lost completion checkpoint after validation still requires recovery, not an already-closed success.
Candidate-local completion does not mean primary was changed; delivery remains separately authorized.

### Design {#lifecycle-design}

#### Issue Graph (`issue_graph`) {#lifecycle-issue-graph-issue-graph}

This former runtime wrapper is retired. Native Agent/Workflow and finite Host services execute
the capability directly; no LangGraph mirror is claimed. The explicit optional StateGraph boundary
is [Terminal Agent Operation](../harness/execution-reference.md#host-operation-node-operation-node).


#### Issue verification Graph (`issue_verification_graph`) {#lifecycle-issue-verification-graph-issue-verification-graph}

This former runtime wrapper is retired. Native Agent/Workflow and finite Host services execute
the capability directly; no LangGraph mirror is claimed. The explicit optional StateGraph boundary
is [Terminal Agent Operation](../harness/execution-reference.md#host-operation-node-operation-node).


### Precise specifications {#lifecycle-precise-specifications}

The Issues Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.


## Native bounded solving

Public solve prepares a session-bound `concorde.issue.<ticket>` native workflow. The authored workflow
owns at most six decision iterations. Each iteration has three fixed Host steps, below the native
32-grant ceiling: prepare decision (persisting attempt first), admit decision/prepare verification,
and admit verification. Host steps never launch models. Develop/spec-repair/needs-decision return to
main without automatic changes. Verify/resolved require fresh Issue-specific and ordinary Spec/code
scope reviews; those terminal calls are flattened into the same native workflow, never nested scripts.
Only actual successful native execution plus independent current evidence can authorize disposition.

Dynamic review scope uses root-owned deterministic slots and the single `issueCall` constructor for
Host preflight and authored workflow calls. Host-issued root/iteration/group/member identity determines
canonical paths, role and fixed gate-lookup command. Exclusive bindings hold exact descriptors/calls,
context/input and preflight digests; guessed names/counts are not authority. Preparation and preflight
finish before a small closed canonical versioned counts/route DTO permits model launch. That DTO is
bounded to2048ASCII bytes, below the native4KiB stdout preview; mixed/truncated/oversized output refuses.
There is no new review-count limit or per-reviewer Host grant. Actual native budgets remain limits.

Issue revision, duplicate identities and Spec/code inputs are rechecked at each finite transition.
The primary solution record remains authoritative; scratch carries only JSON for the live invocation.
Model callbacks/stacks are not serialized. The exact original Issue bytes reconstruct the before-image,
including JSON ordering, so disposition bytes must match the write-ahead journal exactly. The existing
journal is persisted before close, final deterministic validation runs after close, and failure restores
the original Issue. Interrupted/uncertain closure keeps the journal for explicit safe recovery; cancellation
or missing acknowledgement never erases a durable disposition. Delivery/integration remain separate.

The legacy Issue Graph, verification Graph and legacy reviewer/batch execution path are retired.
`IssueSolve` supplies shared finite predicates/journal services; no public native failure selects an old
RPC/Graph backend. Optional StateGraph Operations are a separate explicit interface.


Issue decision and verification reviewer slots share Harness's self-contained native proposal
schema with direct native roles. The native `value` wrapper must retain valid reference roots;
SDK argument validation precedes tool execution and independent Host proposal/currentness gates.
A valid bounded decision explicitly supplies context_id, outcome, answer, blockers, documents,
plan and tasks plus its closed issue_decision. Empty plan is a string, while documents/tasks are
arrays; omitted fields and additional decision keys are rejected, not synthesized by the Host.
