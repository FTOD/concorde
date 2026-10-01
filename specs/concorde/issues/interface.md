# Issue interface

The canonical contracts, provenance, record file, store operations and bookkeeping command of
[Issues](module.md). All shapes are closed: unknown fields are refused. Both contracts below are
registered as [typed values](../glossary.json#concept.typed-value) with their version under the
name given with them.

## Report

A report is the content of the file a session passes to `report --file`, the object it passes to
the [project MCP server](../glossary.json#concept.project-mcp-server)'s `issue_report`, or what another caller passes to the store directly
together with the provenance it vouches for. It is at most 64 KiB as canonical JSON; large logs are referenced by path, not copied.
**Canonical JSON** here and below is the sorted, compact JSON that Spec core's
[`canonical`](../spec-tooling/spec/contracts.md#typed-values) writes: keys sorted, no whitespace
between tokens.

```concorde-contract
{
  "id": "contract.issues.report",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["report_key", "tier", "type", "subtype", "title", "description", "impact",
                 "basis", "owner_target_id", "evidence"],
    "properties": {
      "report_key": {"type": "string", "minLength": 1},
      "tier": {"enum": ["suggestion", "obvious-fix", "preferred-fix", "decision-needed"]},
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
  "semantics": "One observation of a concrete problem, registered as typed value concorde-issue-report. report_key is chosen by the reporter and stays the same across retries of the same observation. tier says who may handle the problem without the level above (the main agent, then the developer): suggestion, advisory, no problem today; obvious-fix, an obvious problem with an obvious fix, which the session fixing it fixes alone; preferred-fix, a simple problem whose best fix of several is clear, which the session fixing it fixes and reports; decision-needed, a problem that is unclear or whose fix is uncertain, which the level above decides; every tier but suggestion is blocking. description, impact, basis and evidence describe the problem completely enough for whoever the Issue is escalated to by its identity to act on it. type bug is a defect or failure, gap an implementation/Spec mismatch, a conflict between Specs or a missing necessary promise, limitation behaviour that is consistent but insufficient; subtype is required for gap and null otherwise. owner_target_id names the Module that owns the broken promise, or null when unknown. evidence may be empty; its paths are canonical project-relative POSIX paths (nonempty, no leading slash, no backslash, colon or control character, no empty, . or .. component); the report command also requires each to exist in the project, or in the origin project when origin is given. origin, optional, says the observation was made in another project than the one recording it: that project's absolute path, its Git HEAD then, the commit of the Concorde it ran, and the task, each nullable but project. error_chain, optional, is the failure's error chain as one error of the Framework's error contract, checked against it. issue_id and expected_revision are both absent to create an Issue and both present to append to that Issue at exactly that revision. Provenance is never part of a report. The report is at most 64 KiB as canonical JSON.",
  "example": {
    "report_key": "retry-count-unspecified",
    "tier": "decision-needed",
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
command, and the project MCP server's `issue_report` through it, supply these values:

| Field | Meaning | Value from `report` |
| --- | --- | --- |
| `invocation_id` | the invocation that reported | `cli-` and a random UUID, new for every run |
| `agent` | who reports | `main-agent` from the command; from `issue_report`, `task-session` in a task worktree bound as a workspace and `main-agent` otherwise |
| `operation` | the [Operation](../glossary.json#concept.operation) or command that reported | `issues` |
| `phase` | the step of that invocation | `report` |
| `target_id` | the reporting [Module](../glossary.json#concept.module) | the report's `owner_target_id`, or the root Module when it is `null` |
| `context_id` | digest of the reporter's context | SHA-256 digest of the bytes of the reporting worktree's registry |
| `change_id` | the task, nullable | the `--task` argument, or `null`; from `issue_report`, the workspace the task worktree is bound as, or `null` |
| `head` | the Git `HEAD`, nullable | `git rev-parse --verify HEAD` in the reporting worktree, or `null` when that fails |

A report's **reporting Module** is its provenance `target_id`, the Module its caller vouches for as
reporting it; the report command sets it to the report's owner, or to the root Module when the
owner is `null`. The root Module is the one registered Module that no other Module contains. The
fields are free
strings apart from `context_id`; the store records them as given and derives the
[Issue](../glossary.json#concept.issue) identity from `invocation_id` and the report key.

## Record file

The [lifecycle](module.md#lifecycle) explains the state transitions and their meaning to the main
agent; this section fixes their representation and validity rules.

A record lives at `.concorde/issues/<issue_id>.md` of the primary worktree and is exactly: the line `# <issue_id>`, a blank
line, a `json` fence holding the record serialized with two-space indentation, and the closing
fence. Nothing else may appear in the file. A record is at most 16 MiB.

The record has `schema_version` 3, or 2 for a record written before tiers existed, `id`, `status` (`open` or `closed`), `reports` (at least one)
and `dispositions`. Each entry of `reports` is `{id, created_at, report, source}`, with `source`
the provenance and `id` the digest of `{report, source}`. Each disposition is
`{reason, note, evidence, duplicate_of, actor, created_at}`, where `reason` is `resolved`,
`duplicate`, `not-actionable` or `reopened`, `evidence` is a nonempty list of unique strings and
`duplicate_of` is another Issue identity for `duplicate` and `null` otherwise. A `created_at` is
the UTC time, as an ISO 8601 string, at which the store accepted that report or disposition, unless
the caller of `disposition_record` or `dispose_issue` supplies one. `reports` and `dispositions`
keep the order in which they were accepted, so the **latest** report is the last entry of
`reports`.

A record is valid only when:

- its `id` is `I-` plus the hex form of the UUIDv5 (URL namespace) of the canonical JSON
  `[invocation_id, report_key]` of its first report, and it matches the file name;
- every report's `id` matches its content, and no two reports share an `id` or an
  `(invocation_id, report_key)` pair;
- every report is itself a valid report of this Issue: it satisfies the
  [report contract](#contract.issues.report), except that a report of a record of
  `schema_version` 2 may lack its `tier`, the first report has no `issue_id`, and a later
  report that has one names this Issue;
- dispositions alternate from open: a closing reason only while open, `reopened` only while
  closed, and `status` equals the state after the last disposition.

An Issue's owner is the latest report's `owner_target_id`, or that report's reporting Module when
the owner is `null`, and its tier the latest report's `tier`, or none when that report has none. The
store creates records of `schema_version` 3 and never changes a record's version, so appending a
tiered report to a record of version 2 keeps it version 2. Its revision is the SHA-256 digest of the file's bytes.

## Store operations

These are library operations in `concorde.issues.store`. None launches a model. Each takes the
`root` whose records it reads or writes; `project_root(path)` gives the primary worktree of the
repository `path` lies in, refusing with `not_a_repository` outside one, and every write refuses
any other root with `not_primary`. Only writes run Git, to commit the record they wrote. They
fail in these ways:

- a refusal by an Issue rule is an `IssueError` carrying one of the codes under [Errors](#errors)
  and a message that states what is wrong; a refusal that concerns one stored Issue, such as a
  read, an append, a disposition or a publication, also names that Issue; this includes a record
  that another program created or changed between the store's read and its publication, which
  the [file transaction](../spec-tooling/spec/contracts.md#file-transactions) refuses as
  `stale_proposal` and the store reports as `stale_issue`, naming the record file and keeping the
  `stale_proposal` as its cause;
- a value that Spec core's [typed-value](../spec-tooling/spec/contracts.md#typed-values) checks
  refuse, such as a report or disposition that breaks its schema or an evidence path that is not a
  canonical project-relative POSIX path, is refused by Spec core with `TypedDataError` and its
  code `invalid_field`, naming the field it concerns; a record, directory or lock path reached
  through a symbolic link is refused the same way, without a field;
- a write the operating system refuses inside the file transaction fails with the transaction's
  `system_error`;
- an operating-system error outside the file transaction, such as reading a record, taking the
  lock or syncing the directory after publication, propagates as the operating system's own
  `OSError`;
- a write that cannot hold the [merge lock](../glossary.json#concept.merge-lock) within its wait, is made while a task's merge is
  unfinished, or whose commit Git refuses is an `IssueError` with `merge_busy`,
  `merge_incomplete` or `commit_failed`.

The bookkeeping command reports a `TypedDataError` as `invalid_issue`, and a `system_error` or an
`OSError` as `io_error`.

| Operation | Behaviour |
| --- | --- |
| `report_issue(root, report, source, wait, locked)` | Validates, then under the merge lock: returns the existing receipt when the same `(invocation_id, report_key)` already holds identical content; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks that the Issue exists (`unknown_issue`), `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the record and its revision; `invalid_issue` for a malformed identity, `unknown_issue` when absent, `invalid_issue` when malformed or oversized. |
| `list_issues(root, target_id, status, tiers)` | Returns one summary row per Issue, sorted by identity: `{id, tier, type, subtype, title, status, target_id, owner_target_id, revision}`, where `tier` (or `null` without one), `type`, `subtype`, `title` and `owner_target_id` are the latest report's, `target_id` is that report's reporting Module and `revision` the record's. A `target_id` keeps only the Issues whose latest report has that reporting Module or owner, whether or not it is a registered Module; a `status` keeps only the Issues with that status, `invalid_issue` for one that is neither `open` nor `closed`; `tiers` keeps only the Issues whose latest report has one of those tiers, so never one without a tier, `invalid_issue` when it names one that is not a tier; `null` for any of them filters nothing, and the filters given combine, an Issue passing each. An absent directory yields an empty list and is not created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one; `stale_issue` when it is absent. |
| `disposition_record(record, ...)` | Prepares and validates a disposed record without writing. |
| `dispose_issue(root, id, expected_revision, reason, note, evidence, actor, duplicate_of, duplicate_revision, created_at, wait, locked)` | Refuses a `duplicate` without `duplicate_of`, naming the Issue itself, or another reason with `duplicate_of` (`invalid_issue`). Under the lock, checks the revision (`stale_issue`), refuses closing a closed Issue (`closed_issue`) and reopening an open one (`open_issue`), and for `duplicate` that the other Issue exists (`unknown_issue`), is open (`invalid_issue`) and, when the caller gives `duplicate_revision`, the revision it read of that other Issue, still has it (`stale_issue`); appends the disposition and returns the new revision. `duplicate_of` and `duplicate_revision` default to `null`; `created_at` defaults to the time of acceptance; the bookkeeping command never gives `duplicate_revision`. |

Every write refuses a `root` that is not the primary worktree (`not_primary`), then holds the
primary worktree's merge lock, `.concorde/locks/merge.lock`, the one Tasks' merges, opens and closes
hold, waiting for it up to `wait` seconds (default 300) and refusing with `merge_busy`, naming the
holder, after that; `locked` says the caller holds it already, as a task merge closing the Issues its
task resolves does, and then neither waits nor checks for a merge. Holding it, a write refuses with
`merge_incomplete` while a task is stored `merging`, checks the file's previous digest, publishes a
staged file through a [file transaction](../glossary.json#concept.file-transaction), syncs the
directory and commits the record alone on the primary worktree's branch: `git add -f` of its path
and `git commit --only` of that path, with the repository's author identity and hooks, which leaves
every other change of the primary worktree as it was, and the message `concorde: record Issue <id>`,
`concorde: report to Issue <id>`, `concorde: close Issue <id> (<reason>)` or
`concorde: reopen Issue <id>`, a blank line and the trailer `Concorde-Issue: <id>`. When the
primary worktree's `HEAD` is detached or Git refuses the commit, the write puts back the committed
record, or removes the new one, and refuses with `commit_failed`, carrying Git's output. A failed
write is never reported as success. No operation deletes a record file.

## Bookkeeping command

`python3 scripts/issues.py <action> ... [--root <path>]` works from the worktree `--root` (default
the current directory), which must contain `.concorde/config.json`. Every action but `check` acts on
the project's Issues, the records of the primary worktree of the repository `--root` lies in, and
refuses with `not_a_repository` outside one; `check` checks the record files of `--root` itself.
The command reads the registry `.concorde/specs.json` whenever an action needs the registered
Modules. `--task` supplies provenance only; the CLI neither requires nor looks up that task. In the
unified CLI, `python3 scripts/concorde.py issues` in a source checkout and `concorde issues` in an
installed project route to this command. The actions live in `concorde.issues.command`, which the
project MCP server's Issue tools call with the same arguments, so each tool answers exactly what the
action prints and refuses with the same link: `issue_list` (`status`, `module` and `tier`, a
nonempty list, as `list`'s options), `issue_show`, `issue_check` (the
primary worktree's `check`), `issue_report` (the report as an object `report` or a `file` relative to
the session's worktree, and `check`), `issue_close` and `issue_reopen`. Their writes never wait for
the merge lock (`wait` 0), and they record the session as the provenance above says and as a
disposition's actor.

| Action | Effect and output |
| --- | --- |
| `list [--status open\|closed] [--module <module>] [--tier <tier>]...` | `{"issues": [...]}`: the summary rows of `list_issues` with `--status` as `status`, `--module` as `target_id` and the `--tier` values, which may be repeated, as `tiers`; without an option, every Issue |
| `show <id>` | `{"issue": <record>, "revision": <digest>}` |
| `check` | `{"errors": [...], "notes": [...]}`, exit status 1 when `errors` is nonempty and 0 otherwise |
| `report --file <report.json> [--task <task-id>]` | Records the report in the file with the provenance above and prints `{"receipt": <receipt>, "revision": <digest>}` |
| `report --file <report.json> --check` | Runs every check `report` runs on the file, records nothing and prints `{"valid": true, "file", "report_key", "reporting_module"}` |
| `close <id> --reason resolved\|duplicate\|not-actionable --note <text> --evidence <item>... [--duplicate-of <id>]` | Closes the open Issue at its current revision and prints `{"issue_id", "status": "closed", "revision"}` |
| `reopen <id> --note <text> --evidence <item>...` | Reopens the closed Issue at its current revision and prints `{"issue_id", "status": "open", "revision"}` |

`report` reads the file as UTF-8 JSON and validates it as a [report](#contract.issues.report),
including a given `error_chain` against the Framework's
[error contract](../tracing/contracts.md#contract.tracing.error). Its `owner_target_id`, when not `null`,
must be a Module of the primary worktree's registry, which keeps the Issue, and each evidence path
must exist in the worktree `--root` or, for a report with an `origin`, in the origin project, whose
path the refusal then names. A report file may lie outside
the project, such as a report another project wrote. When the owner is `null` the registry must have
exactly one root Module, which becomes the reporting Module. A file with `issue_id` and
`expected_revision` appends to that Issue; the revision is the one `show`, `report`, `close` or
`reopen` last printed for it.

`close` and `reopen` read the Issue's current revision and dispose it at exactly that revision with
actor `main-agent`, or the session for the tools. They take neither `--task` nor an expected-revision argument; their concurrency
check protects the interval from their own read to publication, not the interval since the main
agent's earlier `show`. `--evidence` takes one or more items and may be repeated; the items must be
nonblank and distinct, and `--note` must be nonblank. `--duplicate-of` is required with
`--reason duplicate` and refused with any other reason. The command checks these argument rules,
like a missing argument or an unknown reason, itself before it reads the Issue, and refuses a
violation with `usage`; a `--duplicate-of` naming the Issue being closed passes them and is
refused by the store with `invalid_issue`.

Every refusal prints `{"error": <link>}` and writes nothing. The link is a `component` link of
the Framework's [error chain](../tracing/contracts.md#contract.tracing.error) with the actor
`Issues (concorde issues)`: its code is the refusal code, its detail names the Issue, the report
file and field, or the argument concerned and states what is wrong, and its reason is
`environment` for `io_error`, `merge_busy`, `merge_incomplete`, `commit_failed` and
`not_a_repository`, and `input` for every other code. These environment refusals are failures of
the Issue system itself: each lists among its options that its [error chain](../glossary.json#concept.error-chain) is carried in the task's
[decision log](../glossary.json#concept.decision-log) and escalation, or in the run's result, and never reported as an Issue. The Issue store raises `IssueError`,
a subclass of Spec tooling's [error type](../spec-tooling/spec/errors.md) with its own registered
codes; when a refusal comes from one, the link's explanation is the Issue rule that error states
it breaks, and its option is the error's remediation. The exit status is 2 when the
request is unusable (codes `usage`, `not_a_project`, `unreadable_file`) and 1 when the request is
refused (every other code).

`check` reads the registry and every entry of `.concorde/issues/` except hidden files
such as `.gitignore`. Each error names the file: an entry that is not a regular file named
`I-<32 hex digits>.md`, a record that does not read as valid, or an open Issue whose owner is not a
registered Module (`<id> names unknown owner <module>`). A closed Issue with an unknown owner
produces the same text as a note, which does not change the exit status. An absent directory passes.
Concorde's configuration registers it as the
[configured check](../glossary.json#concept.configured-check) `check.issues.store` of
`module.issues`, with the argument vector `["{python}", "scripts/issues.py", "check"]` and a
60-second timeout.

## Errors

| Code | Meaning |
| --- | --- |
| `unknown_issue` | the named Issue, or the Issue a duplicate names, does not exist |
| `invalid_issue` | a malformed identity, a malformed, oversized or inconsistent report or record, or an invalid disposition |
| `issue_key_conflict` | a report key reused for different content |
| `stale_issue` | the record changed since the caller's revision, or a receipt names a report the record does not hold, so the record is not the one the receipt was issued from |
| `closed_issue` | an append to, or a closing of, a closed Issue |
| `open_issue` | a reopening of an open Issue |
| `unknown_owner` | a report's `owner_target_id` is not a registered Module |
| `no_reporting_module` | a report names no owner and the registry has no single root Module |
| `missing_evidence` | a report's evidence path does not exist in the project |
| `unreadable_registry` | the registry `.concorde/specs.json` cannot be read |
| `io_error` | a file operation failed |
| `usage` | the arguments do not form a request of the command |
| `not_a_project` | `--root` has no `.concorde/config.json` |
| `unreadable_file` | the report file cannot be read as UTF-8 text |
| `not_a_repository` | `--root` lies in no Git repository, whose primary worktree would keep the Issues |
| `not_primary` | a store write names a root that is not the primary worktree |
| `merge_busy` | the merge lock stayed held for the whole wait; the message names its holder |
| `merge_incomplete` | a task's merge into the primary branch is unfinished; the message is Tasks' account of it |
| `commit_failed` | the primary worktree's `HEAD` is detached or Git refused the commit of the record, which was put back |
