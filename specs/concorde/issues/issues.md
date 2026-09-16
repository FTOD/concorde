# Issue records and reporting

Issues are branch-local problem records, not implementation tasks or flow-control signals. A
reporter classifies a concrete observation as `bug`, `gap` or `limitation`. A bug is a defect,
vulnerability or failure; a gap is an implementation/Spec mismatch, a conflict between Specs, or
a missing necessary contract; a limitation is an internally consistent current behavior whose
capability or usability is insufficient. Prefer gap when an explicit consistency conflict is the
subject of the report. Only gap has a subtype: `implementation-spec-mismatch`, `spec-conflict` or
`missing-contract`. Classification may change with new evidence without replacing the issue.

<a id="entity.reflections.issue-store"></a>

The Issue store retains its stable document and entity identities through transfer to the Issues
Module; the legacy identity spelling does not preserve a triage API. It owns durable observations and disposition history under `.concorde/issues/`.
Reports contain a title, description, impact, basis, admitted evidence locations and the known
contract owner's Module identity, or null when unknown. The trusted caller supplies invocation,
agent, capability, phase, reporting target, context digest, optional change and HEAD. Reporting
context and contract ownership remain distinct. Creating a record does not require a managed change,
a reproduction verdict, an investigation plan, a repair proposal or human approval.

## Store boundary

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

Each UTF-8 Markdown file has an identity heading and a single JSON fence containing the version-1
record: `id`, `status`, `reports`, `dispositions` and `schema_version`. The JSON is the sole record
content, not a duplicate prose projection. A report stores its id, timestamp, report payload and
source. Dispositions preserve reason, note, evidence references, actor, timestamp and nullable
duplicate target. Record status must agree with disposition history. Editing an immutable report
without reconciling its digest is invalid; append new observations instead.

## Worker reporting service

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

### scenario.issues.report-authority — Bind reporting without granting arbitrary writes

- GIVEN a worker with a frozen context and host reporting service
- WHEN it reports an admitted observation or attempts foreign evidence, ownership or provenance
- THEN the host saves the admitted observation without granting the worker project writes
- AND foreign evidence, forged provenance and appends to unselected issues are rejected
- AND policy preview launches no reporting service and creates no issue

### scenario.issues.report-independent — Report without ending the task

- GIVEN a worker or question-answering invocation with reporting authority
- WHEN it reports issues and then completes its own task
- THEN the reports remain available and the task can complete successfully
- AND the reporting tool itself neither terminates the worker nor starts a repair

### scenario.issues.report-survives-failure — Retain observations from interrupted work

- GIVEN a worker whose issue report was acknowledged by the host
- WHEN its final result is invalid or its execution is interrupted
- THEN the issue observation remains persisted independently of the failed stage
- AND the failed or incomplete stage is not represented as successful

## Persistence and concurrency

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

## Disposition boundary

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
an agent tool or a general-purpose record editing grant. See [recovery](lifecycle.md#scenario.issues.disposition-recovery).

The store cannot establish semantic truth from an evidence string. Merely not reproducing once,
using a workaround, writing code without validation or completing an unrelated task is not a
resolution. Disposition never substitutes for required review or final candidate verification.
An authorized solving flow may make evidence-grounded dispositions without mandatory human
approval; genuinely unresolved design or product decisions remain for the developer. Solving-flow
admission and verification are separate from this storage boundary.

## Scenarios

### scenario.issues.store-report — Persist and reference classified observations

- GIVEN a host-issued reporting context and a classified issue report
- WHEN the host records it and retries the identical report
- THEN one branch-local issue and one immutable observation exist with the same returned receipt
- AND appending current evidence can revise the classification without changing the original report
- AND querying an absent collection creates no record or directory

### scenario.issues.store-concurrency — Serialize writes without coupling branches

- GIVEN concurrent reports in one worktree and an independent branch copy
- WHEN the host accepts reports and disposes a record in one branch
- THEN accepted observations are not lost or duplicated by identical retries
- AND another branch's copy retains its own disposition until explicit integration

### scenario.issues.store-disposition — Retain evidence-bound disposition history

- GIVEN an open issue with its current byte revision
- WHEN an authorized host supplies a valid disposition with rationale and evidence
- THEN the record is retained with the requested disposition and unchanged original observations
- AND stale revisions, empty evidence, self-duplicates and invalid transitions are rejected

### scenario.issues.store-boundary — Reject malformed and unsafe persistence

- GIVEN a malformed report, unsafe path, corrupted observation or failed publication
- WHEN the host attempts to admit or persist it
- THEN it does not acknowledge successful recording of that invalid operation
- AND existing valid observations remain available without widening file authority
