# Issue interface

The exact shapes, storage format, store operations and solve bookkeeping of the Issues Module. The
[entry](module.md) and [Solving an Issue](solving.md) explain why these exist; this document is
what an implementer or a reviewer checks the code against. All shapes are closed: unknown fields
are rejected.

## Capability request and response

`concorde-issues-request` carries:

| Field | Type | Used by |
| --- | --- | --- |
| `action` | `list`, `show`, `report`, `reopen` or `solve` | all |
| `target_id` | Module identity | `report` (required); `list` (filter); others must equal the bound owner if given |
| `task`, `focus_id`, `constraints`, `change_id` | the common task fields | `solve` |
| `issue_id` | `I-` and 32 lowercase hex digits | `show`, `reopen`, `solve` (required) |
| `report` | an Issue report, below | `report` only |
| `expected_revision` | SHA-256 digest | `show`, `reopen`, `solve`; refused when it differs from the file |
| `note` | nonblank string | `reopen` (required rationale); `solve` (developer clarification) |

Binding happens before a worktree is chosen. For `show`, `reopen` and `solve` the Host reads the
record and its revision, sets `target_id` to the latest report's `owner_target_id`, or to its
reporting `target_id` when the owner is `null`, and refuses a different supplied `target_id` with
`permission_denied`. `reopen` and `solve` refuse a schema-1 record with
`unsupported_issue_version`. When `task` is absent for `solve`, the Host writes one from the
latest report's title, description and impact.

`concorde-issues-response` is the common capability response plus:

| Field | Meaning |
| --- | --- |
| `issues` | complete records returned by the action: all matching records for `list`, the one record otherwise |
| `decision` | `null` for bookkeeping; for `solve`, the solver action or a stop reason: `already-closed`, `needs-decision`, `limit-exhausted`, `blocked`, `failed` or `verification-failed` |

`blockers` in the common response is the list of Blockers the last solver or reviewer returned.

## Issue report, provenance and receipt

A report (`concorde-issue-report`):

| Field | Rule |
| --- | --- |
| `report_key` | reporter-chosen key, stable across retries of the same observation |
| `type` | `bug`, `gap` or `limitation` |
| `subtype` | for `gap` exactly one of `implementation-spec-mismatch`, `spec-conflict`, `missing-contract`; otherwise `null` |
| `title`, `description`, `impact`, `basis` | nonblank strings |
| `owner_target_id` | Module that owns the broken promise, or `null` when unknown |
| `evidence` | list of `{path, description}`; paths are canonical project-relative POSIX paths |
| `issue_id`, `expected_revision` | both absent to create an Issue, both present to append to one |

A report is at most 64 KiB as canonical JSON. Large logs are referenced by path, not copied.

Provenance is supplied by the Host, never by the reporter: `invocation_id`, `agent`, `operation`,
`phase`, `target_id` (the reporting Module), `context_id` (digest of the reporter's context),
`change_id` and `head` (both nullable).

A receipt (`concorde-issue-receipt`) is `{issue_id, report_id, path}`. `report_id` is the digest of
`{report, source}` and always names that one immutable report, even after later reports or
dispositions. The worker tool `report_issue` returns `{receipt, revision}`, where `revision` is the
record file's current digest, usable as a later `expected_revision`.

A Blocker is a receipt plus `blocked_step`. A review Finding's Issue reference is a receipt plus
`severity` (`blocking` or `advisory`) and `affected_task`; each blocking reference becomes the
Blocker `{receipt, blocked_step: affected_task}`.

## Record file

A record lives at `.concorde/issues/<issue_id>.md` and is exactly: the line `# <issue_id>`, a blank
line, a `json` fence holding the record serialized with two-space indentation, and the closing
fence. Nothing else may appear in the file. A record is at most 16 MiB.

The record (schema version 2) has `schema_version: 2`, `id`, `status` (`open` or `closed`),
`reports` (at least one) and `dispositions`. Each entry of `reports` is
`{id, created_at, report, source}` with `id` equal to the digest of `{report, source}`. Each
disposition is `{reason, note, evidence, duplicate_of, actor, created_at}`, where `reason` is
`resolved`, `duplicate`, `not-actionable` or `reopened`, `evidence` is a nonempty list of unique
strings and `duplicate_of` is another Issue identity for `duplicate` and `null` otherwise.

A record is valid only when:

- its `id` is `I-` plus the hex form of the UUIDv5 (URL namespace) of the canonical JSON
  `[invocation_id, report_key]` of its first report, and it matches the file name;
- every report's `id` matches its content, and no two reports share an `id` or an
  `(invocation_id, report_key)` pair;
- dispositions alternate from open: a closing reason only while open, `reopened` only while
  closed, and `status` equals the state after the last disposition.

A schema-1 record is identical except that provenance carries `capability` in place of
`operation`. It is readable with its exact bytes; every write to it fails with
`unsupported_issue_version`.

## Store operations

These are Host library operations. None launches a model or runs Git.

| Operation | Behaviour |
| --- | --- |
| `report_issue(root, report, source)` | Validates, then under the lock: returns the existing receipt when the same `(invocation_id, report_key)` already holds identical content; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the record and its revision; `unknown_issue` when absent, `invalid_issue` when malformed or oversized. |
| `list_issues(root, target_id, status)` | Returns summary rows filtered by reporting Module or latest owner and by status. An absent directory yields an empty list and is not created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one. |
| `dispose_issue(root, id, expected_revision, ...)` | Under the lock, checks the revision, and for `duplicate` that the other Issue exists, is open and, when given, still has `duplicate_revision`; appends the disposition and returns the new revision. |
| `disposition_record(record, ...)` | Prepares and validates the disposed record without writing. |
| `restore_issue(root, id, original, expected_revision)` | Under the lock, writes the open `original` bytes only over exactly `expected_revision`; does nothing if `original` is already on disk; otherwise `stale_issue`. |

Every write runs under an exclusive file lock at `.concorde/runs/issues.lock`, checks the file's
previous digest, writes a staged file that is synced and atomically renamed, and syncs the
directory before returning. A failed write is never reported as success.

## Reporting service

The Host binds one reporting service per worker run from the frozen context before the worker
starts:

- **admitted owners**: the bound Module, the Modules it uses, and the owner of every selected Spec
  document. The reporting Module must be among them.
- **evidence paths**: every selected Spec document path, every implementation artifact in the
  snapshot and every path in the review patch given to the worker.
- **selected Issues**: Issues named by the task's `concorde-issue-selection` input, and Issues whose
  reports arrive as `concorde-issue-context` input.

A report naming an owner outside the admitted owners, or evidence outside the evidence paths, or
appending to an Issue that is neither selected nor reported earlier in the same run, fails with
`permission_denied`. For the developer's `report` action the agent is `developer`, the phase is
`report`, and evidence may also name existing files under `.concorde/archive/reflections/`.

A stage result may reference only receipts reported in the same run or received as admitted input,
each at most once; otherwise it fails with `permission_denied` or `invalid_completion`. The input
`concorde-issue-context` gives a worker the `description`, `impact` and `basis` of each referenced
report, never the whole record.

## Solve state

Inside the candidate, the change record holds `issue_solutions[<issue_id>]`:

| Field | Meaning |
| --- | --- |
| `revision` | the selected Issue's revision when the solve began |
| `attempts` | solver launches for the current `inputs`; at most 6 |
| `inputs` | digest of the Module's Spec revision and implementation-file digest |
| `clarification` | the last `note` supplied with `solve` |
| `history` | one `{context_id, decision, inputs}` per accepted solver decision |
| `verified_inputs`, `verification` | the inputs a completed verification covered and the reviews' input digests |
| `status` | `active`, `closing`, `verifying-candidate`, `completed`, `verification-failed` or a stop reason |
| `pending_disposition` | the closing journal while a close is unfinished |
| `disposition`, `closed_revision` | set when the solve completed |

`attempts` returns to 0 when `inputs` differ from the stored value or a new `clarification` is
given. The attempt count is saved before each solver launch.

The closing journal is `{schema_version: 1, change_id, issue_id, before, before_digest, after,
after_digest}`. It is valid only when both digests match their texts, both texts parse as records
of this Issue, `before` is open, `after` is closed and equals `before` plus exactly one disposition
whose actor is `concorde-issue-solver`, and `before_digest` equals the solve's `revision`. An
invalid journal fails with `invalid_worktree_state`. The prepared `created_at` is reused for the
actual write, so the written bytes equal `after`.

## Native solve workflow

`pi/workflows/issues.js` runs up to six iterations `i` of three Host steps and the model calls
between them:

1. Host step `next-i` prepares solver slot `d-i`, or finishes.
2. Model call `d-i` runs the Issue solver.
3. Host step `decision-i` admits the decision, then finishes (hand-back, stop or close plus
   validation) or prepares review slots `v-i-g-m` for groups `g` 0 to 3 (Issue-specific Spec,
   Issue-specific code, ordinary Spec, ordinary code; a Module without implementation files uses
   groups 0 and 2).
4. Model calls `v-i-g-m` run the reviewers, in order.
5. Host step `verified-i` admits every review together and returns to step 1, or finishes.

Each Host step answers with one line of JSON with exactly the keys `groups`, `iteration`, `route`,
`schema_version`, `ticket`, in that order: `schema_version` 1, the workflow's `ticket`, the current
`iteration`, `route` in `decide`, `verify` or `finished`, and `groups` as four non-negative review
counts. The line is ASCII and at most 2048 bytes; the script rejects anything else. A step whose
name, iteration or phase does not match the saved session state is refused as a duplicate or stale
step. A model call is accepted only when the native runtime reports a single successful,
non-detached, non-interrupted child whose staged proposal carries this workflow's ticket and slot.
When the workflow finishes, the Host saves the result for the user session to poll and a copy under
`.concorde/runs/<invocation_id>/native-issue.json`.
