# Issue interface

The canonical contracts, provenance, record file, store operations, reporting service and
bookkeeping command of [Issues](module.md). All shapes are closed: unknown fields are refused. Both
contracts below are registered as typed values with version 1 under the name given with them.

## Report

A report is what a reporter submits to its reporting service, or what a host-side caller passes to
the store directly with the provenance it vouches for. It is at most 64 KiB as canonical JSON;
large logs are referenced by path, not copied.

```concorde-contract
{
  "id": "contract.issues.report",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["report_key", "type", "subtype", "title", "description", "impact", "basis",
                 "owner_target_id", "evidence"],
    "properties": {
      "report_key": {"type": "string", "minLength": 1},
      "type": {"enum": ["bug", "gap", "limitation"]},
      "subtype": {
        "anyOf": [
          {"enum": ["implementation-spec-mismatch", "spec-conflict", "missing-contract"]},
          {"type": "null"}
        ]
      },
      "title": {"type": "string", "minLength": 1},
      "description": {"type": "string", "minLength": 1},
      "impact": {"type": "string", "minLength": 1},
      "basis": {"type": "string", "minLength": 1},
      "owner_target_id": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
      "evidence": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["path", "description"],
          "properties": {
            "path": {"type": "string", "minLength": 1},
            "description": {"type": "string", "minLength": 1}
          }
        }
      },
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "expected_revision": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    }
  },
  "semantics": "One observation of a concrete problem, registered as typed value concorde-issue-report. report_key is chosen by the reporter and stays the same across retries of the same observation. type bug is a defect or failure, gap an implementation/Spec mismatch, a conflict between Specs or a missing necessary promise, limitation behaviour that is consistent but insufficient; subtype is required for gap and null otherwise. owner_target_id names the Module that owns the broken promise, or null when unknown. evidence paths are canonical project-relative POSIX paths within the reporter's admitted evidence paths. issue_id and expected_revision are both absent to create an Issue and both present to append to that Issue at exactly that revision. Provenance is never part of a report. The report is at most 64 KiB as canonical JSON.",
  "example": {
    "report_key": "retry-count-unspecified",
    "type": "gap",
    "subtype": "missing-contract",
    "title": "Retry limit is not specified",
    "description": "No Spec of module.payments states how often a failed payment is retried.",
    "impact": "Planning cannot choose a retry limit without inventing a promise.",
    "basis": "The Module entry and its requirements describe retries but give no limit.",
    "owner_target_id": "module.payments",
    "evidence": [
      {"path": "specs/payments/module.md", "description": "Retry section without a limit"}
    ]
  }
}
```

## Receipt

```concorde-contract
{
  "id": "contract.issues.receipt",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["issue_id", "report_id", "path"],
    "properties": {
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "report_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
      "path": {"type": "string", "pattern": "^\\.concorde/issues/I-[0-9a-f]{32}\\.md$"}
    }
  },
  "semantics": "The durable name of one accepted report, registered as typed value concorde-issue-receipt. report_id is the digest of the report together with its caller-supplied provenance, so the receipt always names that one immutable report, even after later reports or dispositions of the same Issue. path is the record file of issue_id. A receipt is returned only after the record is on disk. The reporting service answers {receipt, revision}, where revision is the digest of the record file after the write and is usable as a later expected_revision.",
  "example": {
    "issue_id": "I-0123456789abcdef0123456789abcdef",
    "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md"
  }
}
```

## Provenance

The caller of the reporting service supplies the provenance of every report, never the reporter:

| Field | Meaning |
| --- | --- |
| `invocation_id` | the invocation the reporter belongs to, such as an Operation run |
| `agent` | who reports, such as a worker's task type, `host`, `main-agent` or `developer` |
| `operation` | the Operation the invocation runs, or a caller-chosen name outside Operations |
| `phase` | the step of that invocation |
| `target_id` | the reporting Module |
| `context_id` | digest of the reporter's context |
| `change_id`, `head` | the task and Git `HEAD`, each nullable |

These fields are free strings apart from `context_id`; the store records them as given and derives
the Issue identity from `invocation_id` and the report key.

## Record file

A record lives at `.concorde/issues/<issue_id>.md` and is exactly: the line `# <issue_id>`, a blank
line, a `json` fence holding the record serialized with two-space indentation, and the closing
fence. Nothing else may appear in the file. A record is at most 16 MiB.

The record has `schema_version: 2`, `id`, `status` (`open` or `closed`), `reports` (at least one)
and `dispositions`. Each entry of `reports` is `{id, created_at, report, source}`, with `source`
the provenance and `id` the digest of `{report, source}`. Each disposition is
`{reason, note, evidence, duplicate_of, actor, created_at}`, where `reason` is `resolved`,
`duplicate`, `not-actionable` or `reopened`, `evidence` is a nonempty list of unique strings and
`duplicate_of` is another Issue identity for `duplicate` and `null` otherwise.

A record is valid only when:

- its `id` is `I-` plus the hex form of the UUIDv5 (URL namespace) of the canonical JSON
  `[invocation_id, report_key]` of its first report, and it matches the file name;
- every report's `id` matches its content, and no two reports share an `id` or an
  `(invocation_id, report_key)` pair;
- every report is itself a valid report of this Issue;
- dispositions alternate from open: a closing reason only while open, `reopened` only while
  closed, and `status` equals the state after the last disposition.

An Issue's owner is the latest report's `owner_target_id`, or that report's reporting Module when
the owner is `null`. Its revision is the SHA-256 digest of the file's bytes.

## Store operations

These are library operations for host-side callers. None launches a model or runs Git.

| Operation | Behaviour |
| --- | --- |
| `report_issue(root, report, source)` | Validates, then under the lock: returns the existing receipt when the same `(invocation_id, report_key)` already holds identical content; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the record and its revision; `unknown_issue` when absent, `invalid_issue` when malformed or oversized. |
| `list_issues(root, target_id, status)` | Returns summary rows filtered by reporting Module or latest owner and by status, whether or not the owner is a registered Module. An absent directory yields an empty list and is not created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one; `stale_issue` when it is absent. |
| `disposition_record(record, ...)` | Prepares and validates a disposed record without writing. |
| `dispose_issue(root, id, expected_revision, ...)` | Under the lock, checks the revision (`stale_issue`), and for `duplicate` that the other Issue exists, is open and, when given, still has `duplicate_revision`; appends the disposition and returns the new revision. |
| `restore_issue(root, id, original, expected_revision)` | Under the lock, writes the open `original` bytes only over exactly `expected_revision`; does nothing when `original` is already on disk; otherwise `stale_issue`. |

Every write runs under the exclusive lock `.concorde/runs/issues.lock` of the worktree `root`
names, which serializes the writes into that worktree; writes into different worktrees touch
different files and take different locks. It checks the file's previous
digest, publishes a staged file through a file transaction, and syncs the directory before
returning. A failed write is never reported as success. No operation deletes a record file.

## Reporting service

A caller binds one reporting service for one reporter before the reporter starts, with:

- **provenance**, as above; its `target_id` must be among the admitted owners;
- **admitted owners**: the Modules the reporter may name as `owner_target_id`;
- **evidence paths**: the files the reporter may cite;
- **selected Issues**: the Issues the reporter may append to, besides those it created itself
  through the same service;
- **admitted receipts**: the receipts the reporter was given, kept for a later reference check.

The caller derives these limits from what the reporter is working on, for example the task's bound
Modules as owners and their Spec and implementation files as evidence paths. No command or
Operation binds a reporting service in this version.

A report naming an owner outside the admitted owners, evidence outside the evidence paths, or an
append to an Issue neither selected nor created earlier by the same service fails with
`permission_denied`. The service answers `{receipt, revision}`.

A reference check, kept from the previous design and unused in this version, accepts in a result
only receipts the service created or admitted, each at most once (`permission_denied`,
`invalid_completion`), and resolves each to its exact report (`stale_issue`).

## Bookkeeping command

`python3 scripts/issues.py <action> [<id>] [--root <path>]` works on the project at `--root`
(default the current directory) and refuses, with exit status 2 and `{"error": …}`, a directory
without `.concorde/config.json`, a `show` without an Issue identity, an identity given to another
action, or an unreadable record.

| Action | Output |
| --- | --- |
| `list` | `{"issues": [...]}`: the summary rows of `list_issues`, unfiltered |
| `show <id>` | `{"issue": <record>, "revision": <digest>}` |
| `check` | `{"errors": [...], "notes": [...]}`, exit status 1 when `errors` is nonempty and 0 otherwise |

`check` reads the configured registry and every entry of `.concorde/issues/` except hidden files
such as `.gitignore`. Each error names the file: an entry that is not a regular file named
`I-<32 hex digits>.md`, a record that does not read as valid, or an open Issue whose owner is not a
registered Module (`<id> names unknown owner <module>`). A closed Issue with an unknown owner
produces the same text as a note, which does not change the exit status. An absent directory
passes. Concorde's configuration registers it as the configured check `check.issues.store` of
`module.issues`, with the argument vector `["{python}", "scripts/issues.py", "check"]` and a
60-second timeout.

The command records no report and no disposition.

## Errors

| Code | Meaning |
| --- | --- |
| `unknown_issue` | the named Issue does not exist |
| `invalid_issue` | a malformed, oversized or inconsistent report or record |
| `issue_key_conflict` | a report key reused for different content |
| `stale_issue` | the record changed since the caller's revision, or a receipt names no report |
| `closed_issue` | an append to a closed Issue |
| `permission_denied` | an owner, evidence path, append or reference outside the reporter's limits |
| `invalid_completion` | a result references the same report twice |
