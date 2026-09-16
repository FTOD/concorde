# Issue records and reporting

Issues are branch-local problem records, not implementation tasks or flow-control signals. A
reporter classifies a concrete observation as `bug`, `gap` or `limitation`. A bug is a defect,
vulnerability or failure; a gap is an implementation/Spec mismatch, a conflict between Specs, or
a missing necessary contract; a limitation is an internally consistent current behavior whose
capability or usability is insufficient. Prefer gap when an explicit consistency conflict is the
subject of the report. Only gap has a subtype: `implementation-spec-mismatch`, `spec-conflict` or
`missing-contract`. Classification may change with new evidence without replacing the issue.

<a id="entity.reflections.issue-store"></a>

The Issue store owns durable observations and disposition history under `.concorde/issues/`.
Reports contain a title, description, impact, basis, admitted evidence locations and the known
contract owner's Module identity, or null when unknown. The trusted caller supplies invocation,
agent, capability, phase, reporting target, context digest, optional change and HEAD. Reporting
context and contract ownership remain distinct. Creating a record does not require a managed change,
a reproduction verdict, an investigation plan, a repair proposal or human approval.

## Store boundary

`report_issue(root, report, source)` accepts the closed shapes in the issue model. The host, not a
worker parameter, supplies `source`. `report_key` is a reporter-local stable key for retrying the
same observation. `type`, nullable `subtype`, `title`, `description`, `impact`, `basis`, nullable
`owner_target_id`, and `evidence` are required; each evidence item has `path` and `description`.
Strings are nonblank and paths are canonical project-relative POSIX paths. `issue_id` and
`expected_revision` are either both absent for creation or both present for appending an observation.
The caller must separately enforce evidence visibility and reporting authority; a syntactically
safe path is not a grant. Reports are limited to 64 KiB of canonical JSON and records to 16 MiB.
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
duplicate_of=None)` is a trusted host operation, not part of the worker reporting authority.
The caller must authorize disposition and assess the evidence before calling. The store validates
current record bytes, a nonempty note, at least one evidence reference, the actor and a valid
transition. Reasons `resolved`, `duplicate` and `not-actionable` close an open record; `reopened`
reopens a closed record. Duplicate requires another existing open canonical issue; other reasons
cannot carry a duplicate target. Closed records and all their observations remain present.

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
