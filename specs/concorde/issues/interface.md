# Issue interface

The canonical contracts, provenance, record file, store operations and bookkeeping command of
[Issues](module.md). All shapes are closed: unknown fields are refused. Both
contracts below are registered as typed values with version 1 under the name given with them.

## Report

A report is the content of the file the main agent passes to `report --file`, or what another
caller passes to the store directly together with the provenance it vouches for. It is at most
64 KiB as canonical JSON; large logs are referenced by path, not copied.

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
      "origin": {
        "type": "object",
        "additionalProperties": false,
        "required": ["project", "head", "concorde_commit", "task"],
        "properties": {
          "project": {"type": "string", "pattern": "^/"},
          "head": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
          "concorde_commit": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
          "task": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]}
        }
      },
      "error_chain": {"type": "object", "additionalProperties": {}},
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "expected_revision": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    }
  },
  "semantics": "One observation of a concrete problem, registered as typed value concorde-issue-report. report_key is chosen by the reporter and stays the same across retries of the same observation. type bug is a defect or failure, gap an implementation/Spec mismatch, a conflict between Specs or a missing necessary promise, limitation behaviour that is consistent but insufficient; subtype is required for gap and null otherwise. owner_target_id names the Module that owns the broken promise, or null when unknown. evidence paths are canonical project-relative POSIX paths; the report command also requires each to exist in the project, or in the origin project when origin is given. origin, optional, says the observation was made in another project than the one recording it: that project's absolute path, its Git HEAD then, the commit of the Concorde it ran, and the task, each nullable but project. error_chain, optional, is the failure's error chain as one error of the Framework's error contract, checked against it. issue_id and expected_revision are both absent to create an Issue and both present to append to that Issue at exactly that revision. Provenance is never part of a report. The report is at most 64 KiB as canonical JSON.",
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
  "semantics": "The durable name of one accepted report, registered as typed value concorde-issue-receipt. report_id is the digest of the report together with its caller-supplied provenance, so the receipt always names that one immutable report, even after later reports or dispositions of the same Issue. path is the record file of issue_id. A receipt is returned only after the record is on disk. The report command answers {receipt, revision}, where revision is the digest of the record file after the write and is usable as a later expected_revision.",
  "example": {
    "issue_id": "I-0123456789abcdef0123456789abcdef",
    "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md"
  }
}
```

## Provenance

Every report is stored with the provenance of its caller, never taken from the report. The report
command supplies these values:

| Field | Meaning | Value from `report` |
| --- | --- | --- |
| `invocation_id` | the invocation that reported | `cli-` and a random UUID, new for every run |
| `agent` | who reports | `main-agent` |
| `operation` | the Operation or command that reported | `issues` |
| `phase` | the step of that invocation | `report` |
| `target_id` | the reporting Module | the report's `owner_target_id`, or the root Module when it is `null` |
| `context_id` | digest of the reporter's context | SHA-256 digest of the configured registry file's bytes |
| `change_id` | the task, nullable | the `--task` argument, or `null` |
| `head` | the Git `HEAD`, nullable | `git rev-parse --verify HEAD` in the project, or `null` when that fails |

The root Module is the one registered Module that no other Module contains. The fields are free
strings apart from `context_id`; the store records them as given and derives the Issue identity
from `invocation_id` and the report key.

## Record file

The [lifecycle](module.md#lifecycle) explains the state transitions and their meaning to the main
agent; this section fixes their representation and validity rules.

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

These are library operations in `concorde.issues.store`. None launches a model or runs Git. Every
refusal is a Spec error carrying one of the codes under [Errors](#errors) and a message naming the
Issue it concerns; a malformed value is refused with the field it concerns.

| Operation | Behaviour |
| --- | --- |
| `report_issue(root, report, source)` | Validates, then under the lock: returns the existing receipt when the same `(invocation_id, report_key)` already holds identical content; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks that the Issue exists (`unknown_issue`), `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the record and its revision; `invalid_issue` for a malformed identity, `unknown_issue` when absent, `invalid_issue` when malformed or oversized. |
| `list_issues(root, target_id, status)` | Returns summary rows filtered by reporting Module or latest owner and by status, whether or not the owner is a registered Module. An absent directory yields an empty list and is not created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one; `stale_issue` when it is absent. |
| `disposition_record(record, ...)` | Prepares and validates a disposed record without writing. |
| `dispose_issue(root, id, expected_revision, ...)` | Refuses a `duplicate` without `duplicate_of`, naming the Issue itself, or another reason with `duplicate_of` (`invalid_issue`). Under the lock, checks the revision (`stale_issue`), refuses closing a closed Issue (`closed_issue`) and reopening an open one (`open_issue`), and for `duplicate` that the other Issue exists (`unknown_issue`), is open (`invalid_issue`) and, when given, still has `duplicate_revision` (`stale_issue`); appends the disposition and returns the new revision. |

Every write runs under the exclusive lock `.concorde/runs/issues.lock` of the worktree `root`
names, which serializes the writes into that worktree; writes into different worktrees touch
different files and take different locks. It checks the file's previous
digest, publishes a staged file through a file transaction, and syncs the directory before
returning. A failed write is never reported as success. No operation deletes a record file.

## Bookkeeping command

`python3 scripts/issues.py <action> ... [--root <path>]` works on the project at `--root` (default
the current directory), which must contain `.concorde/config.json`. The command reads the registry
that configuration names whenever an action needs the registered Modules. The main-session
workflow puts writes in a task worktree and passes `--task` on reports; the CLI itself does not
require or look up that task. `--task` supplies provenance only and does not select a worktree.
`--root`, or the current directory when omitted, selects the records that every action reads or
writes. In the unified CLI, `python3 scripts/concorde.py issues` in a source checkout and
`concorde issues` in an installed project route to this command.

| Action | Effect and output |
| --- | --- |
| `list` | `{"issues": [...]}`: the summary rows of `list_issues`, unfiltered |
| `show <id>` | `{"issue": <record>, "revision": <digest>}` |
| `check` | `{"errors": [...], "notes": [...]}`, exit status 1 when `errors` is nonempty and 0 otherwise |
| `report --file <report.json> [--task <task-id>]` | Records the report in the file with the provenance above and prints `{"receipt": <receipt>, "revision": <digest>}` |
| `report --file <report.json> --check` | Runs every check `report` runs on the file, records nothing and prints `{"valid": true, "file", "report_key", "reporting_module"}` |
| `close <id> --reason resolved\|duplicate\|not-actionable --note <text> --evidence <item>... [--duplicate-of <id>]` | Closes the open Issue at its current revision and prints `{"issue_id", "status": "closed", "revision"}` |
| `reopen <id> --note <text> --evidence <item>...` | Reopens the closed Issue at its current revision and prints `{"issue_id", "status": "open", "revision"}` |

`report` reads the file as UTF-8 JSON and validates it as a
[report](#contract.issues.report), including a given `error_chain` against the Framework's
[error contract](../contracts.md#contract.concorde.error). Its `owner_target_id`, when not `null`,
must be a registered Module, and each evidence path must exist in the project or, for a report with
an `origin`, in the origin project, whose path the refusal then names. A report file may lie
outside the project, such as a report another project wrote. When the owner is `null` the registry must
have exactly one root Module, which becomes the reporting Module. A file with `issue_id` and
`expected_revision` appends to that Issue; the revision is the one `show`, `report`, `close` or
`reopen` last printed for it.

`close` and `reopen` read the Issue's current revision and dispose it at exactly that revision with
actor `main-agent`. They take neither `--task` nor an expected-revision argument; their concurrency
check protects the interval from their own read to publication, not the interval since the main
agent's earlier `show`. `--evidence` takes one or more items and may be repeated; the items must be
nonblank and distinct, and `--note` must be nonblank. `--duplicate-of` is required with
`--reason duplicate` and refused with any other reason.

Every refusal prints `{"error": <link>}` and writes nothing. The link is a `component` link of
the Framework's [error chain](../contracts.md#contract.concorde.error) with the actor
`Issues (concorde issues)`: its code is the refusal code, its detail names the Issue, the report
file and field, or the argument concerned and states what is wrong, and its reason is
`environment` for `io_error` and `input` for every other code. The Issue store raises `IssueError`,
a subclass of Spec tooling's [error type](../spec-tooling/spec/errors.md) with its own registered
codes; when a refusal comes from one, the link's explanation is that error's reason (the Issue rule
it breaks) and its option is the error's remediation. The exit status is 2 when the
request is unusable (codes `usage`, `not_a_project`, `unreadable_file`) and 1 when the request is
refused (every other code).

`check` reads the configured registry and every entry of `.concorde/issues/` except hidden files
such as `.gitignore`. Each error names the file: an entry that is not a regular file named
`I-<32 hex digits>.md`, a record that does not read as valid, or an open Issue whose owner is not a
registered Module (`<id> names unknown owner <module>`). A closed Issue with an unknown owner
produces the same text as a note, which does not change the exit status. An absent directory
passes. Concorde's configuration registers it as the configured check `check.issues.store` of
`module.issues`, with the argument vector `["{python}", "scripts/issues.py", "check"]` and a
60-second timeout.

## Errors

| Code | Meaning |
| --- | --- |
| `unknown_issue` | the named Issue, or the Issue a duplicate names, does not exist |
| `invalid_issue` | a malformed identity, a malformed, oversized or inconsistent report or record, or an invalid disposition |
| `issue_key_conflict` | a report key reused for different content |
| `stale_issue` | the record changed since the caller's revision, or a receipt names no report |
| `closed_issue` | an append to, or a closing of, a closed Issue |
| `open_issue` | a reopening of an open Issue |
| `unknown_owner` | a report's `owner_target_id` is not a registered Module |
| `no_reporting_module` | a report names no owner and the registry has no single root Module |
| `missing_evidence` | a report's evidence path does not exist in the project |
| `unreadable_registry` | the configured registry cannot be read |
| `io_error` | a file operation failed |
| `usage` | the arguments do not form a request of the command |
| `not_a_project` | `--root` has no `.concorde/config.json` |
| `unreadable_file` | the report file cannot be read as UTF-8 text |
