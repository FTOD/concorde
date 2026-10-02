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
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["report_key", "tier", "severity", "type", "subtype", "title", "description",
                 "impact", "basis", "owner_target_id", "evidence"],
    "properties": {
      "report_key": {"type": "string", "minLength": 1},
      "tier": {"enum": ["suggestion", "obvious-fix", "preferred-fix", "decision-needed"]},
      "severity": {"enum": ["critical", "high", "medium", "low"]},
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
  "semantics": "One observation of a concrete problem, registered as typed value concorde-issue-report. report_key is chosen by the reporter and stays the same across retries of the same observation. tier says who may handle the problem without the level above (the main agent, then the developer): suggestion, advisory, no problem today; obvious-fix, an obvious problem with an obvious fix, which the session fixing it fixes alone; preferred-fix, a simple problem whose best fix of several is clear, which the session fixing it fixes and reports; decision-needed, a problem that is unclear or whose fix is uncertain, which the level above decides; every tier but suggestion is blocking. severity says how much the problem matters while it stands, independently of the tier, most severe first: critical, wrong results, lost or corrupted data, a security exposure or a core flow broken with no workaround; high, a main flow broken or wrong although a workaround exists, or a promise that leads the work relying on it to act wrongly; medium, a secondary flow or an edge case that fails, or a gap that slows the work without misleading it; low, something cosmetic with which nothing goes wrong. description, impact, basis and evidence describe the problem completely enough for whoever the Issue is escalated to by its identity to act on it. type bug is a defect or failure, gap an implementation/Spec mismatch, a conflict between Specs or a missing necessary promise, limitation behaviour that is consistent but insufficient; subtype is required for gap and null otherwise. owner_target_id names the Module that owns the broken promise, or null when unknown. evidence may be empty; its paths are canonical project-relative POSIX paths (nonempty, no leading slash, no backslash, colon or control character, no empty, . or .. component); the report command also requires each to exist in the project, or in the origin project when origin is given. origin, optional, says the observation was made in another project than the one recording it: that project's absolute path, its Git HEAD then, the commit of the Concorde it ran, and the task, each nullable but project. error_chain, optional, is the failure's error chain as one error of the Framework's error contract, checked against it. issue_id and expected_revision are both absent to create an Issue and both present to append to that Issue at exactly that revision. Provenance is never part of a report. The report is at most 64 KiB as canonical JSON.",
  "example": {
    "report_key": "retry-count-unspecified",
    "tier": "decision-needed",
    "severity": "high",
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
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["issue_id", "report_id", "path"],
    "properties": {
      "issue_id": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
      "report_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
      "path": {"type": "string", "pattern": "^\\.concorde/issues/(closed/)?I-[0-9a-f]{32}\\.md$"}
    }
  },
  "semantics": "The durable name of one accepted report, registered as typed value concorde-issue-receipt. report_id is the digest of the report together with its caller-supplied provenance, so the receipt always names that one immutable report, even after later reports or dispositions of the same Issue. path is the record file of issue_id where it lies when the receipt is returned: .concorde/issues/<issue_id>.md for an open Issue, .concorde/issues/closed/<issue_id>.md when a repeated report finds the Issue closed since; resolving a receipt accepts either path of its Issue. A receipt is returned only after the record holding the report is committed on the primary branch. The report command answers {receipt, revision}, where revision is the digest of the record file after the write and is usable as a later expected_revision.",
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

The [lifecycle](module.md#lifecycle) explains the state transitions and their meaning to the
[main agent](../glossary.json#concept.main-agent); this section fixes their representation and
validity rules.

An open Issue's record lives at `.concorde/issues/<issue_id>.md` of the primary worktree and a closed
one's at `.concorde/issues/closed/<issue_id>.md`, the record's **place**. A record committed at the
other of these two paths is **misplaced**; reads, lists and writes accept it, every write leaves the
record it writes in its place, `check` reports it and `archive` moves it. An Issue is committed at
one of the two paths at most; one committed at both is refused with `invalid_issue` by every read
naming it. A record file is exactly: the line `# <issue_id>`, a blank
line, a `json` fence holding the record serialized with two-space indentation, and the closing
fence. Nothing else may appear in the file. A record is at most 16 MiB.

The record has `schema_version` 4, 3 for a record written before severities existed or 2 for one
written before tiers existed, `id`, `status` (`open` or `closed`), `reports` (at least one)
and `dispositions`. Each entry of `reports` is `{id, created_at, report, source}`, with `source`
the provenance and `id` the digest of `{report, source}`. Each disposition is
`{reason, note, evidence, duplicate_of, actor, created_at}`, where `reason` is `resolved`,
`duplicate`, `not-actionable` or `reopened`, `evidence` is a nonempty list of unique strings and
`duplicate_of` is another Issue identity for `duplicate` and `null` otherwise. A `created_at` is
the UTC time, as an ISO 8601 string, at which the store accepted that report or disposition, unless
the caller of `disposition_record` or `dispose_issue` supplies one. `reports` and `dispositions`
keep the order in which they were accepted, so the **latest** report is the last entry of
`reports`.

A record is **committed** when the last commit of the primary worktree, its `HEAD`, holds it at one
of its two paths. A record file whose state in the primary worktree, staged or not, differs from the committed
one, or that no commit holds, is **uncommitted**; reads never see it.

A record is valid only when:

- its `id` is `I-` plus the hex form of the UUIDv5 (URL namespace) of the canonical JSON
  `[invocation_id, report_key]` of its first report, and it matches the file name;
- every report's `id` matches its content, and no two reports share an `id` or an
  `(invocation_id, report_key)` pair;
- every report is itself a valid report of this Issue: it satisfies the
  [report contract](#contract.issues.report), except that a report of a record of
  `schema_version` 2 may lack its `tier` and its `severity` and a report of a record of
  `schema_version` 3 its `severity`, the first report has no `issue_id`, and a later
  report that has one names this Issue;
- dispositions alternate from open: a closing reason only while open, `reopened` only while
  closed, and `status` equals the state after the last disposition.

An Issue's owner is the latest report's `owner_target_id`, or that report's reporting Module when
the owner is `null`, its tier the latest report's `tier` and its severity the latest report's `severity`, each none when
that report has none. The store creates records of `schema_version` 4 and never changes a record's
version, so appending a report with a tier and a severity to a record of version 2 or 3 keeps its
version. Its revision is the SHA-256 digest of the file's bytes.

## Store operations

These are library operations in `concorde.issues.store`. None launches a model. Each takes the
`root` whose records it reads or writes; `project_root(path)` gives the primary worktree of the
repository `path` lies in, refusing with `not_a_repository` outside one, and every write refuses
any other root with `not_primary`. Reads take the committed records of `root`'s `HEAD` from Git
(`git ls-tree` and `git cat-file`), never its files, refusing with `not_a_repository` when `root`
lies in no repository; an unborn `HEAD` holds no records. A record's revision is the digest of
its committed bytes. Writes run Git to commit the record they wrote and to put back uncommitted
records. They fail in these ways:

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
- an operating-system error outside the file transaction, such as taking the lock, syncing the
  directory after publication or Git failing to list or read the committed records, propagates as
  the operating system's own `OSError`, after the write put back the record it had published;
- a write that cannot hold the [merge lock](../glossary.json#concept.merge-lock) within its wait, is made while a task's merge is
  unfinished, or whose commit Git refuses is an `IssueError` with `merge_busy`,
  `merge_incomplete` or `commit_failed`;
- a write that cannot put back an uncommitted record, its own after a failure or one an earlier
  write left, is an `IssueError` with `recovery_failed`, and a write of an Issue whose record holds
  a change no write left is an `IssueError` with `uncommitted_change`, naming the record file.

The bookkeeping command reports a `TypedDataError` as `invalid_issue`, and a `system_error` or an
`OSError` as `io_error`.

| Operation | Behaviour |
| --- | --- |
| `report_issue(root, report, source, wait, locked)` | Validates, then under the merge lock, after recovery: returns the existing receipt when the committed record already holds identical content for the same `(invocation_id, report_key)`, so that receipt names a committed report; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks that the Issue exists (`unknown_issue`), `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the committed record, at either of its paths, and its revision; `invalid_issue` for a malformed identity, `unknown_issue` when `HEAD` holds it at neither path, even when an uncommitted file does, `invalid_issue` when it is committed at both, malformed, oversized or committed as anything but a regular file. |
| `locate_issue(root, id)` | Returns what `read_issue` returns and the path the record is committed at, refusing as `read_issue` does. |
| `read_record_file(root, path)` | Returns the record file at `path` of `root`, either path of an Issue, as it is on disk, committed or not, and the digest of its bytes, refusing as `read_issue` does and with `invalid_issue` for a path that is neither; the store check alone reads this way. |
| `list_issues(root, target_id, status, tiers, severities, sort)` | Returns one summary row per Issue, sorted by identity unless `sort` says otherwise: `{id, severity, tier, type, subtype, title, status, target_id, owner_target_id, revision}`, where `severity` and `tier` (each `null` without one), `type`, `subtype`, `title` and `owner_target_id` are the latest report's, `target_id` is that report's reporting Module and `revision` the record's. A `target_id` keeps only the Issues whose latest report has that reporting Module or owner, whether or not it is a registered Module; a `status` keeps only the Issues with that status, `invalid_issue` for one that is neither `open` nor `closed`; `tiers` keeps only the Issues whose latest report has one of those tiers, so never one without a tier, `invalid_issue` when it names one that is not a tier; `severities` likewise keeps only the Issues whose latest report has one of those severities, never one without a severity, `invalid_issue` when it names one that is not a severity; `null` for any of them filters nothing, and the filters given combine, an Issue passing each. `sort` `severity` orders the rows most severe first, those of equal severity by tier from `decision-needed` down to `suggestion`, then by the `created_at` of the Issue's first report and by identity, every row without a severity after those with one and every row without a tier after those of its severity with one; `null` keeps the order by identity, and any other value is `invalid_issue`. It lists the committed records alone, all of one commit, from both folders, refusing with `invalid_issue` when an Issue is committed in both; a commit without the directory yields an empty list, and nothing is created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one; `stale_issue` when it is absent. |
| `disposition_record(record, ...)` | Prepares and validates a disposed record without writing. |
| `dispose_issue(root, id, expected_revision, reason, note, evidence, actor, duplicate_of, duplicate_revision, created_at, wait, locked)` | Refuses a `duplicate` without `duplicate_of`, naming the Issue itself, or another reason with `duplicate_of` (`invalid_issue`). Under the lock, checks the revision (`stale_issue`), refuses closing a closed Issue (`closed_issue`) and reopening an open one (`open_issue`), and for `duplicate` that the other Issue exists (`unknown_issue`), is open (`invalid_issue`) and, when the caller gives `duplicate_revision`, the revision it read of that other Issue, still has it (`stale_issue`); appends the disposition, moves the record into the place of its new status and returns the new revision. `duplicate_of` and `duplicate_revision` default to `null`; `created_at` defaults to the time of acceptance; the bookkeeping command never gives `duplicate_revision`. |
| `archive_issues(root, wait, locked)` | Under the merge lock, as a write holds it, after recovery: moves every misplaced committed record into its place, its bytes unchanged so its revision stays, publishing all of them through one file transaction and committing them in one commit as a write commits, and returns `{"moved": [{issue_id, from, to}], "left": [{path, reason}]}`, sorted by identity. It leaves, with the reason, both paths of an Issue committed at both and a misplaced record whose path or place holds a change recovery left. Nothing to move commits nothing. Refuses as a write does. |
| `recover_issues(root, wait, locked)` | Under the merge lock, as a write holds it, runs the recovery below without writing an Issue and returns `{"recovered": [{path, action}], "left": [{path, reason}]}`: each record put back (`action` `restored` to its committed version, or `removed` when no commit holds it) or temporary file removed (`removed`), and each record change left because no write made it, with the reason. Refuses as a write does, with `not_primary`, `merge_busy`, `merge_incomplete` or `recovery_failed`. |

Every write refuses a `root` that is not the primary worktree (`not_primary`), then holds the
primary worktree's merge lock, `.concorde/locks/merge.lock`, the one Tasks' merges, opens and closes
hold, waiting for it up to `wait` seconds (default 300) and refusing with `merge_busy`, naming the
holder, after that; `locked` says the caller holds it already, as a task merge closing the Issues its
task resolves does once it has closed the task, and then the write neither takes nor waits for it.
Holding it, whether it took it or its caller holds it, a write refuses with `merge_incomplete` while
a task is stored `merging`, recovers as below, refuses with
`uncommitted_change` when the record it writes holds a change recovery left, reads the committed
record and checks its revision, and publishes the record at its place through a
[file transaction](../glossary.json#concept.file-transaction): over the committed bytes when it is
committed there, and otherwise as a new file, after which a write moving the record checks that the
path it is committed at still holds the bytes it read, refusing with `stale_issue` and keeping that
change when another program changed them, and removes it. The write then syncs both folders and
commits the record alone on the primary worktree's branch: `git add -f` of its place and
`git commit --only` of its place and of the path it moved from, with the repository's author
identity and hooks, which leaves every other change of the primary worktree as it was, and the
message `concorde: record Issue <id>`, `concorde: report to Issue <id>`,
`concorde: close Issue <id> (<reason>)` or `concorde: reopen Issue <id>`, a blank line and the
trailer `Concorde-Issue: <id>`; an archive's message is `concorde: archive <n> Issue record(s)`
with one such trailer per Issue it moved. When anything fails after publication, the write puts
back the committed record, or removes the new one from the index and the directory, and restores
the record it removed from the other folder, before it refuses: with `commit_failed`, carrying Git's output, when
the primary worktree's `HEAD` is detached or Git refuses the commit, and otherwise with the
failure itself. When that putting back fails too, it refuses with `recovery_failed` instead,
naming both failures and the record, which stays uncommitted until the next recovery. A failed
write is never reported as success. No operation deletes a committed record.

**Recovery** lists, with `git status --porcelain --untracked-files=all --ignored` of
`.concorde/issues/`, every entry of it or of its `closed/` folder named `I-<32 hex digits>.md` whose
state differs from `HEAD` and every file transaction temporary `.concorde-write-*` there; it touches
no other path. The **committed record** of an entry is the one `HEAD` holds at its path or, when it
holds none there, at the Issue's other path, from which a move publishes it. A record entry is
**left by a write** when its file is a regular file that reads as a valid record of the Issue its
name gives and, when there is a committed record, has the same `schema_version`, begins its
`reports` and `dispositions` with the committed ones and, when that record is committed at the
entry's own path, differs from it. A committed record whose file was deleted is left by a write too
when the Issue's other path holds an entry no commit holds that is left by a write, as a write
moving the record leaves them. Recovery puts each such record
back, with `git checkout HEAD -- <path>` when `HEAD` holds it and otherwise with
`git rm --cached` and the file's removal, and removes each temporary. It leaves every other record
entry as it is, with the reason: the committed record was deleted, the file is no regular file,
it is no valid record, the committed record is not valid, it rewrites what the committed record
holds, or the file equals the committed record at its path while its index entry does not. It
commits nothing. When something cannot be put back or removed, it tries the rest and refuses with
`recovery_failed`, naming each failure.

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
action prints and refuses with the same link: `issue_list` (`status`, `module`, `tier` and `severity`,
each of the last two a nonempty list, and `sort`, as `list`'s options), `issue_show`, `issue_check` (the
primary worktree's `check`), `issue_report` (the report as an object `report` or a `file` relative to
the session's worktree, and `check`), `issue_close` and `issue_reopen`. Their writes never wait for
the merge lock (`wait` 0), and they record the session as the provenance above says and as a
disposition's actor. `recover` and `archive` have no tool.

| Action | Effect and output |
| --- | --- |
| `list [--status open\|closed] [--module <module>] [--tier <tier>]... [--severity <severity>]... [--sort severity]` | `{"issues": [...]}`: the summary rows of `list_issues` with `--status` as `status`, `--module` as `target_id`, the `--tier` and `--severity` values, which may each be repeated, as `tiers` and `severities`, and `--sort` as `sort`; without an option, every Issue by identity |
| `show <id>` | `{"issue": <record>, "revision": <digest>, "path": <the path it is committed at>}` |
| `check` | `{"errors": [...], "notes": [...]}`, exit status 1 when `errors` is nonempty and 0 otherwise |
| `recover` | Runs `recover_issues` on the primary worktree, waiting for the merge lock, and prints its `{"recovered": [...], "left": [...]}` |
| `archive` | Runs `archive_issues` on the primary worktree, waiting for the merge lock, and prints its `{"moved": [...], "left": [...]}` |
| `report --file <report.json> [--task <task-id>]` | Records the report in the file with the provenance above and prints `{"receipt": <receipt>, "revision": <digest>}` |
| `report --file <report.json> --check` | Runs every check `report` runs on the file, records nothing and prints `{"valid": true, "file", "report_key", "reporting_module"}` |
| `close <id> --reason resolved\|duplicate\|not-actionable --note <text> --evidence <item>... [--duplicate-of <id>]` | Closes the open Issue at its current revision, moving its record into `closed/`, and prints `{"issue_id", "status": "closed", "revision", "path"}` |
| `reopen <id> --note <text> --evidence <item>...` | Reopens the closed Issue at its current revision, moving its record back into `.concorde/issues/`, and prints `{"issue_id", "status": "open", "revision", "path"}` |

`report` reads the file as UTF-8 JSON and validates it as a [report](#contract.issues.report),
including a given `error_chain` against the Framework's
[error contract](../kernel/tracing/contracts.md#contract.tracing.error). Its `owner_target_id`, when not `null`,
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

<a id="disposing-under-a-held-lock"></a>

Code of other Modules disposes an Issue through the same action, the library entry of
`concorde.issues.command` that `close` and `reopen` run:

```python
dispose(root, issue_id, reason, note, evidence, *, duplicate_of=None, actor="main-agent",
        wait=300, locked=False) -> dict
```

`reason` is a closing reason, or `reopened` to reopen, `root` any worktree of the project, and the
argument rules
above are checked first, a violation refused with `usage`. It reads the Issue's current revision in
the primary worktree, disposes it there at that revision as `dispose_issue` does, recording `actor`,
and returns what `close` and `reopen` print, `{"issue_id", "status", "revision", "path"}`. With `locked`
its caller holds the merge lock itself, as a task merge closing the Issues its task resolves does
once it has closed the task: the write neither takes nor waits for the lock, and is still refused
with `merge_incomplete` while a task is stored `merging`. Every refusal is raised as the command's
`Refusal`, whose `code` is the refusal code and whose `link` is the error link below, the one the
command would print; its caller decides what the refusal means for its own work, as
[Tasks](../coordination/tasks/module.md) does with a closure its merge could not make, and supplies
the note and evidence its own [Spec](../glossary.json#concept.spec) names.

Every refusal prints `{"error": <link>}`, commits nothing and leaves no record a read shows. It
writes nothing either, with one exception: a write refused with `recovery_failed`, or a process
killed while writing, may leave an uncommitted record in the primary worktree, which the next
write or `recover` puts back, so a refused write may be repeated. The link is a `component` link of
the Framework's [error chain](../kernel/tracing/contracts.md#contract.tracing.error) with the actor
`Issues (concorde issues)`: its code is the refusal code, its detail names the Issue, the report
file and field, or the argument concerned and states what is wrong, and its reason is
`environment` for `io_error`, `merge_busy`, `merge_incomplete`, `commit_failed`,
`recovery_failed`, `uncommitted_change` and `not_a_repository`, and `input` for every other code. These environment refusals are failures of
the Issue system itself: each lists among its options that its [error chain](../glossary.json#concept.error-chain) is carried in the task's
[decision log](../glossary.json#concept.decision-log) and escalation, or in the run's result, and never reported as an Issue. The Issue store raises `IssueError`,
a subclass of Spec tooling's [error type](../spec-tooling/spec/errors.md) with its own registered
codes; when a refusal comes from one, the link's explanation is the Issue rule that error states
it breaks, and its option is the error's remediation. The exit status is 2 when the
request is unusable (codes `usage`, `not_a_project`, `unreadable_file`) and 1 when the request is
refused (every other code).

`check` reads the registry and every entry of `.concorde/issues/` and of its `closed/` folder of
`--root` except hidden files such as `.gitignore`, as files on disk (`read_record_file`), committed
or not. Each error names the file: an entry that is not a regular file named
`I-<32 hex digits>.md`, other than the `closed` directory itself, a `closed` that is no directory, a
record that does not read as valid, a misplaced record, naming its status and place and saying
to run `concorde issues archive` in the primary worktree, which moves it there, an Issue recorded
in both folders, naming both paths and the repair, to keep the record whose reports and
dispositions begin with the other's and remove the other with `git rm` in a commit of its own, or
an open Issue whose owner is not a registered Module (`<id> names unknown owner <module>`). A closed Issue with an unknown owner
produces the same text as a note, which does not change the exit status. An absent directory passes.
Concorde's configuration registers it as the
[configured check](../glossary.json#concept.configured-check) `check.issues.store` of
`module.issues`, with the argument vector `["{python}", "scripts/issues.py", "check"]` and a
60-second timeout.

## Errors

| Code | Meaning |
| --- | --- |
| `unknown_issue` | the named Issue, or the Issue a duplicate names, does not exist |
| `invalid_issue` | a malformed identity, a malformed, oversized or inconsistent report or record, an Issue committed in both folders, or an invalid disposition |
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
| `recovery_failed` | an uncommitted record, the write's own after a failure or one an earlier write left, could not be put back; it stays uncommitted and no read shows it |
| `uncommitted_change` | the record the write would change differs from its committed version in a way no write leaves; it is left as it is |
