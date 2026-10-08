# Issue interface

This document defines these aspects of [Issues](module.md):

- The canonical contracts.
- The provenance.
- The record file.
- The store operations.
- The bookkeeping command.

All shapes are closed. Unknown fields are refused. Both contracts below are exchanged and checked
as they are, without the envelope of a [typed value](../glossary.json#concept.typed-value).
Their schemas are registered as typed-value types under the name and version given with them.
This registration lets another part's schema embed a report or a receipt by name.

## Report

A report is one of these:

- The content of the file a session passes to `report --file`.
- The object the session passes to the `issue_report` tool.
- What another caller passes to the store directly together with the provenance it vouches for.

It is at most 64 KiB as canonical JSON. Large logs are referenced by path, not copied.
**Canonical JSON** here and below is the sorted, compact JSON of the Kernel's
[typed values](../kernel/contracts.md#typed-values): keys sorted, no whitespace between tokens.

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
  "semantics": "One observation of a concrete problem, whose schema is registered as typed-value type concorde-issue-report. report_key is chosen by the reporter and stays the same across retries of the same observation. tier says who may handle the problem without the level above (the main agent, then the developer): suggestion, advisory, no problem today; obvious-fix, an obvious problem with an obvious fix, which the session fixing it fixes alone; preferred-fix, a simple problem whose best fix of several is clear, which the session fixing it fixes and reports; decision-needed, a problem that is unclear or whose fix is uncertain, which the level above decides; every tier but suggestion is blocking. severity says how much the problem matters while it stands, independently of the tier, most severe first: critical, wrong results, lost or corrupted data, a security exposure or a core flow broken with no workaround; high, a main flow broken or wrong although a workaround exists, or a promise that leads the work relying on it to act wrongly; medium, a secondary flow or an edge case that fails, or a gap that slows the work without misleading it; low, something cosmetic with which nothing goes wrong. description, impact, basis and evidence describe the problem completely enough for whoever the Issue is escalated to by its identity to act on it. type bug is a defect or failure, gap an implementation/Spec mismatch, a conflict between Specs or a missing necessary promise, limitation behaviour that is consistent but insufficient; subtype is required for gap and null otherwise. owner_target_id names the Module that owns the broken promise, or null when unknown. evidence may be empty; its paths are canonical project-relative POSIX paths (nonempty, no leading slash, no backslash, colon or control character, no empty, . or .. component); the report command also requires each to exist in the project, or in the origin project when origin is given. origin, optional, says the observation was made in another project than the one recording it: that project's absolute path, its Git HEAD then, the commit of the Concorde it ran, and the task, each nullable but project. error_chain, optional, is the failure's error chain as one error of the Framework's error contract, checked against it. issue_id and expected_revision are both absent to create an Issue and both present to append to that Issue at exactly that revision. Provenance is never part of a report. The report is at most 64 KiB as canonical JSON.",
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
  "semantics": "The durable name of one accepted report, whose schema is registered as typed-value type concorde-issue-receipt. report_id is the digest of the report together with its caller-supplied provenance, so the receipt always names that one immutable report, even after later reports or dispositions of the same Issue. path is the record file of issue_id where it lies when the receipt is returned: .concorde/issues/<issue_id>.md for an open Issue, .concorde/issues/closed/<issue_id>.md when a repeated report finds the Issue closed since; resolving a receipt accepts either path of its Issue. A receipt is returned only after the record holding the report is committed on the primary branch. The report command answers {receipt, revision}, where revision is the digest of the record file after the write and is usable as a later expected_revision.",
  "example": {
    "issue_id": "I-0123456789abcdef0123456789abcdef",
    "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md"
  }
}
```

## Provenance

Every report is stored with the provenance of its caller. The provenance is never taken from the
report. The report command, and the project MCP server's `issue_report` through it, supply these
values:

| Field | Meaning | Value from `report` |
| --- | --- | --- |
| `invocation_id` | the invocation that reported | `cli-` and a random UUID, new for every run |
| `agent` | who reports | `main-agent` from the command; from `issue_report`, `task-session` in a task worktree bound as a workspace and `main-agent` otherwise |
| `operation` | the [Operation](../glossary.json#concept.operation) or command that reported | `issues` |
| `phase` | the step of that invocation | `report` |
| `target_id` | the reporting [Module](../glossary.json#concept.module) | the report's `owner_target_id`, or, where the spec part is installed, the root Module when it is `null` |
| `context_id` | digest of the reporter's context | SHA-256 digest of the bytes of the reporting worktree's registry where the spec part is installed, and of no bytes otherwise |
| `change_id` | the task, nullable | the `--task` argument, or `null`; from `issue_report`, the workspace the task worktree is bound as, or `null` |
| `head` | the Git `HEAD`, nullable | `git rev-parse --verify HEAD` in the reporting worktree, or `null` when that fails |

A report's **reporting Module** is its provenance `target_id`, the Module its caller vouches for as
reporting it. When the report's owner is `null`, the report command sets the reporting Module to
the root Module. Otherwise, the report command sets the reporting Module to the report's owner.
The root Module is the one registered Module that no other Module contains. Apart from `context_id`,
the fields are free strings. The store records them as given. The store derives the
[Issue](../glossary.json#concept.issue) identity from `invocation_id` and the report key.

When a caller vouches for its own provenance, it gives the whole provenance with
`report --provenance` instead. Such a caller can be an [Operation](../glossary.json#concept.operation)'s
host recording the findings of its run. The caller gives these values:

- Its own `invocation_id`, such as its run's identity.
- `agent` with the value `operation`.
- Its name as `operation`.
- The Module it reviewed as `target_id`.
- The digest of its context.
- Its workspace as `change_id`.

The command then neither checks the report's owner against the primary worktree's registry nor
checks its evidence paths. The caller vouches for the evidence paths like the provenance.
These checks are omitted because a task's run may report on a Module its task adds and on a path
its change removed.

## Record file

The [lifecycle](module.md#lifecycle) explains the state transitions and their meaning to the
[main agent](../glossary.json#concept.main-agent). This section fixes their representation and
validity rules.

An open Issue's record lives at `.concorde/issues/<issue_id>.md` of the primary worktree.
A closed Issue's record lives at `.concorde/issues/closed/<issue_id>.md` of the primary worktree.
The path for the record's status is the record's **place**.
A record committed at the other of these two paths is **misplaced**.
These operations handle a misplaced record as follows:

- Reads accept it.
- Lists accept it.
- Writes accept it.
- `check` reports it.
- `archive` moves it.

Every write leaves the record it writes in its place.
An Issue is committed at one of the two paths at most.
When an Issue is committed at both paths, every read naming it refuses it with `invalid_issue`.
A record file consists of exactly these parts, in order:

- The line `# <issue_id>`.
- A blank line.
- A `json` fence holding the record serialized with two-space indentation.
- The closing fence.

Nothing else may appear in the file. A record is at most 16 MiB.

The record has these fields:

- `schema_version`.
- `id`.
- `status` (`open` or `closed`).
- `reports` (at least one).
- `dispositions`.

The record's `schema_version` has one of these values:

- 4.
- 3 for a record written before severities existed.
- 2 for a record written before tiers existed.

Each entry of `reports` is `{id, created_at, report, source}`.
The entry's `source` is the provenance. The entry's `id` is the digest of `{report, source}`.
Each disposition is `{reason, note, evidence, duplicate_of, actor, created_at}`.
Its `reason` has one of these values:

- `resolved`.
- `duplicate`.
- `not-actionable`.
- `reopened`.

Its `evidence` is a nonempty list of unique strings.
For `duplicate`, its `duplicate_of` is another Issue identity. Otherwise, its `duplicate_of` is
`null`.
Unless the caller of `disposition_record` or `dispose_issue` supplies one, a `created_at` is the
time at which the store accepted that report or disposition.
This default time is UTC as an ISO 8601 string.
`reports` and `dispositions` keep the order in which the store accepted them.
Because `reports` keeps that order, the **latest** report is the last entry of `reports`.

When the last commit of the primary worktree, its `HEAD`, holds a record at one of its two paths,
the record is **committed**.
A record file is **uncommitted** when either condition holds:

- Its state in the primary worktree, staged or not, differs from the committed record.
- No commit holds it.

Reads never see an uncommitted record file.

A record is valid only when:

- Its `id` is `I-` plus the hex form of the UUIDv5 (URL namespace) of its first report's canonical
  JSON `[invocation_id, report_key]`.
- Its `id` matches the file name.
- Every report's `id` matches its content.
- No two reports share an `id` or an `(invocation_id, report_key)` pair.
- Every report is itself a valid report of this Issue under the report rules below.
- Dispositions alternate from open under the disposition rules below.

The report rules are:

- Every report satisfies the [report contract](#contract.issues.report), subject to the
  schema-version exceptions below.
- The first report has no `issue_id`.
- When a later report has an `issue_id`, that report names this Issue.

The schema-version exceptions are:

- A report of a record of `schema_version` 2 may lack its `tier` and its `severity`.
- A report of a record of `schema_version` 3 may lack its `severity`.

The disposition rules are:

- A closing reason occurs only while open.
- `reopened` occurs only while closed.
- `status` equals the state after the last disposition.

When the latest report's owner is `null`, an Issue's owner is that report's reporting Module.
Otherwise, an Issue's owner is the latest report's `owner_target_id`.
An Issue's tier is the latest report's `tier`. An Issue's severity is the latest report's
`severity`. When that report has no tier or severity, the corresponding value is none.
The store creates records of `schema_version` 4. The store never changes a record's version.
Because the store never changes the version, appending a report with a tier and a severity to a
record of version 2 or 3 keeps its version.
The record's revision is the SHA-256 digest of the file's bytes.

## Store operations

These are library operations in `concorde.issues.store`. None launches a model. Each takes the
`root` whose records it reads or writes. `project_root(path)` gives the primary worktree of the
repository `path` lies in. When `path` lies outside a repository, `project_root(path)` refuses with `not_a_repository`.
When a root is not the primary worktree, every write refuses with `not_primary`. This includes a directory inside the
primary worktree. Reads take the committed records of `root`'s `HEAD` from Git
(`git ls-tree` and `git cat-file`), never its files. When `root` lies in no repository, reads
refuse with `not_a_repository`. An unborn `HEAD` holds no records. A record's revision is the
digest of its committed bytes. Writes run Git to commit the record they wrote. They also run Git
to put back uncommitted records. They fail in these ways:

- A refusal by an Issue rule is an `IssueError` carrying these details:
  - One of the codes under [Errors](#errors).
  - A message that states what is wrong.
  When a refusal concerns one stored Issue, it also names that Issue. Such refusals include:
  - A read.
  - An append.
  - A disposition.
  - A publication.
  This includes a record another program created or changed after the store's read and before
  the file transaction checks it. The Kernel's
  [file transaction](../kernel/contracts.md#file-transactions) refuses that record as
  `stale_proposal`. The store reports it as `stale_issue` with these details:
  - The record file's name.
  - The `stale_proposal` as its cause.
  The store excludes other writers by the merge lock alone.
  When a program writes a record without holding the lock, the transaction catches the write only
  up to its check. When a program changes the record between that check and the transaction's
  rename, the transaction overwrites the change. This is as the Kernel's file transactions say.
- When the Kernel's [typed-value](../kernel/contracts.md#typed-values) checks refuse a value,
  they use the Kernel's error and its code `invalid_field`. The error names the field it concerns.
  Such values include a report or disposition that breaks its schema.
  They also include an evidence path that is not a canonical project-relative POSIX path.
  When a path is reached through a symbolic link, the checks refuse it the same way, without a
  field. This applies to these paths:
  - A record path.
  - A directory path.
  - A lock path.
- When the operating system refuses a write inside the file transaction, the refusal is an
  `IssueError` with the transaction's code `system_error`. The error names the record file.
- After the write puts back the record it published, an operating-system error outside the file
  transaction propagates as the operating system's own `OSError`. Such errors include:
  - An error taking the lock.
  - An error syncing the directory after publication.
  - An error from Git failing to list or read the committed records.
- A write fails with an `IssueError` in these cases:
  - When it cannot hold the [merge lock](../glossary.json#concept.merge-lock) within its wait,
    the code is `merge_busy`.
  - When it is made while the
    [unfinished-merge marker](../glossary.json#concept.unfinished-merge-marker) is present, the
    code is `merge_incomplete`.
  - When that marker cannot be read or breaks its contract, the code is
    `unreadable_merge_marker`.
  - When Git refuses its commit, the code is `commit_failed`.
- When a write cannot put back an uncommitted record, the refusal is an `IssueError` with
  `recovery_failed`. This applies to its own record after a failure or one an earlier write left.
  When an Issue's record holds a change no write left, a write of that Issue is an `IssueError`
  with `uncommitted_change`. The error names the record file.

The bookkeeping command reports a Kernel error as `invalid_issue`.
It reports a `system_error` or an `OSError` as `io_error`.

| Operation | Behaviour |
| --- | --- |
| `record_report(root, report, source, wait)` | Records the report as `report_issue` does and returns `{receipt, revision}`, where `revision` is the revision of the record the receipt names as the write left it, or as it found it when it returned an existing receipt, taken under the merge lock. |
| `report_issue(root, report, source, wait)` | Returns the receipt of `record_report`. Validates, then under the merge lock, after recovery: returns the existing receipt when the committed record already holds identical content for the same `(invocation_id, report_key)`, so that receipt names a committed report; fails with `issue_key_conflict` for different content; otherwise creates the record or, for an append, checks that the Issue exists (`unknown_issue`), `expected_revision` (`stale_issue`) and open status (`closed_issue`) and appends. |
| `read_issue(root, id)` | Returns the committed record, at either of its paths, and its revision; `invalid_issue` for a malformed identity, `unknown_issue` when `HEAD` holds it at neither path, even when an uncommitted file does, `invalid_issue` when it is committed at both, malformed, oversized or committed as anything but a regular file. |
| `locate_issue(root, id)` | Returns what `read_issue` returns and the path the record is committed at, refusing as `read_issue` does. |
| `read_record_file(root, path)` | Returns the record file at `path` of `root`, either path of an Issue, as it is on disk, committed or not, and the digest of its bytes, refusing as `read_issue` does and with `invalid_issue` for a path that is neither; the store check alone reads this way. |
| `list_issues(root, target_id, status, tiers, severities, sort)` | Returns one summary row per Issue, sorted by identity unless `sort` says otherwise: `{id, severity, tier, type, subtype, title, status, target_id, owner_target_id, revision}`, where `severity` and `tier` (each `null` without one), `type`, `subtype`, `title` and `owner_target_id` are the latest report's, `target_id` is that report's reporting Module and `revision` the record's. A `target_id` keeps only the Issues whose latest report has that reporting Module or owner, whether or not it is a registered Module; a `status` keeps only the Issues with that status, `invalid_issue` for one that is neither `open` nor `closed`; `tiers` keeps only the Issues whose latest report has one of those tiers, so never one without a tier, `invalid_issue` when it names one that is not a tier; `severities` likewise keeps only the Issues whose latest report has one of those severities, never one without a severity, `invalid_issue` when it names one that is not a severity; `null` for any of them filters nothing, and the filters given combine, an Issue passing each. `sort` `severity` orders the rows most severe first, those of equal severity by tier from `decision-needed` down to `suggestion`, then by the `created_at` of the Issue's first report and by identity, every row without a severity after those with one and every row without a tier after those of its severity with one; `null` keeps the order by identity, and any other value is `invalid_issue`. It lists the committed records alone, all of one commit, from both folders, refusing with `invalid_issue` when an Issue is committed in both; a commit without the directory yields an empty list, and nothing is created. |
| `resolve_report(root, receipt)` | Returns the exact report the receipt names, never the latest one; `stale_issue` when it is absent. |
| `disposition_record(record, ...)` | Prepares and validates a disposed record without writing. |
| `dispose_issue(root, id, expected_revision, reason, note, evidence, actor, duplicate_of, duplicate_revision, created_at, wait)` | Refuses a `duplicate` without `duplicate_of`, naming the Issue itself, or another reason with `duplicate_of` (`invalid_issue`). Under the lock, checks the revision (`stale_issue`), refuses closing a closed Issue (`closed_issue`) and reopening an open one (`open_issue`), and for `duplicate` that the other Issue exists (`unknown_issue`), is open (`invalid_issue`) and, when the caller gives `duplicate_revision`, the revision it read of that other Issue, still has it (`stale_issue`); appends the disposition, moves the record into the place of its new status and returns the new revision. `duplicate_of` and `duplicate_revision` default to `null`; `created_at` defaults to the time of acceptance; the bookkeeping command never gives `duplicate_revision`. |
| `archive_issues(root, wait)` | Under the merge lock, as a write holds it, after recovery: moves every misplaced committed record into its place, its bytes unchanged so its revision stays, refusing with `stale_issue` and moving none when another program changed one of them since it read it, publishing all of them through one file transaction and committing them in one commit as a write commits, and returns `{"moved": [{issue_id, from, to}], "left": [{path, reason}]}`, sorted by identity. It leaves, with the reason, both paths of an Issue committed at both and a misplaced record whose path or place holds a change recovery left. Nothing to move commits nothing. Refuses as a write does. |
| `recover_issues(root, wait)` | Under the merge lock, as a write holds it, runs the recovery below without writing an Issue and returns `{"recovered": [{path, action}], "left": [{path, reason}]}`: each record put back (`action` `restored` to its committed version, or `removed` when no commit holds it) or temporary file removed (`removed`), and each record change left because no write made it, with the reason. Refuses as a write does, with `not_primary`, `merge_busy`, `merge_incomplete`, `unreadable_merge_marker` or `recovery_failed`. |

When a `root` is not the primary worktree, every write refuses it with `not_primary`.
The write then holds the primary worktree's merge lock, `.concorde/locks/merge.lock`.
Tasks' operations hold that same lock:

- Merges.
- Opens.
- Closes.

The write waits for the lock up to `wait` seconds (default 300).
After that wait, it refuses with `merge_busy`, naming the holder.
When a process is handed the lock, it adopts the lock without waiting.
For example, a task merge that closed its task hands the lock to the `concorde issues close`
it starts for each Issue the task resolves.

A write performs the following checks while holding the lock. This applies whether the write
takes the lock or receives it. It reads the Kernel's
[unfinished-merge marker](../kernel/contracts.md#contract.kernel.unfinished-merge)
`.concorde/unfinished-merge.json` of the primary worktree. While the marker is present, the write
refuses with `merge_incomplete`, carrying the Kernel's account of the merge. When the marker cannot
be read or breaks its contract, the write refuses with `unreadable_merge_marker`. The refusal names
the file. This is because that marker may describe a merge.
The write then recovers as below.
When the record it writes holds a change recovery left, the write refuses with
`uncommitted_change`. The write reads the committed record. It checks the record's revision.
It publishes the record at its place through a
[file transaction](../glossary.json#concept.file-transaction):

- When the record is committed there, it publishes over the committed bytes.
- Otherwise, it publishes as a new file.

After publication, a write moving the record checks that its committed path still holds the
bytes it read. When another program changed those bytes, the write refuses with `stale_issue`.
The write keeps that change. Otherwise, the write removes the record from that path.
An archive checks each record it moves in the same way.
The write then syncs both folders.
It commits the record alone on the primary worktree's branch, using these Git commands:

- `git add -f` of its place.
- `git commit --only` of its place and of the path it moved from.

The commit uses the repository's author identity and hooks.
This leaves every other change of the primary worktree as it was.
The commit uses one of these messages:

- `concorde: record Issue <id>`
- `concorde: report to Issue <id>`
- `concorde: close Issue <id> (<reason>)`
- `concorde: reopen Issue <id>`

A blank line and the trailer `Concorde-Issue: <id>` follow the message.
An archive's message is `concorde: archive <n> Issue record(s)`.
It has one such trailer per Issue the archive moved.
When anything fails after publication, the write performs these rollback actions before it refuses:

- It puts back the committed record, or removes the new one from the index and the directory.
- It restores the record it removed from the other folder.

When the primary worktree's `HEAD` is detached or Git refuses the commit, the write refuses
with `commit_failed`. The refusal carries Git's output. Otherwise, the write refuses with the
failure itself.
When any rollback action fails too, the write refuses with `recovery_failed` instead.
The refusal names both failures and the record.
The record stays uncommitted until the next recovery.
A failed write is never reported as success. No operation deletes a committed record.

**Recovery** uses `git status --porcelain --untracked-files=all --ignored` of
`.concorde/issues/` to list these entries there or in its `closed/` folder:

- Every entry named `I-<32 hex digits>.md` whose state differs from `HEAD`.
- Every file transaction temporary `.concorde-write-*`.

It touches no other path.
When `HEAD` holds a record at an entry's path, that record is the entry's **committed record**.
Otherwise, the committed record is the one `HEAD` holds at the Issue's other path.
When `HEAD` holds no record at the entry's path, a move publishes the committed record from the Issue's other path.
A record entry is **left by a write** when all these conditions hold:

- Its file is a regular file.
- Its file reads as a valid record of the Issue its name gives.
- When there is a committed record, the file meets these conditions:
  - It has the same `schema_version`.
  - It begins its `reports` and `dispositions` with the committed ones.
  - When the committed record is committed at the entry's own path, the file differs from that
    record.

When a committed record's file is deleted and its Issue's other path holds an entry with both
properties, the record is also left by a write:

- No commit holds the entry.
- The entry is left by a write.

This is how a write moving the record leaves those entries.
Recovery puts each such record back:

- When `HEAD` holds the entry at its path, recovery uses `git checkout HEAD -- <path>`.
- Otherwise, recovery uses `git rm --cached` and removes the file.

Recovery removes each temporary.
It leaves every other record entry as it is, with the reason:

- The committed record was deleted.
- The file is no regular file.
- The file is no valid record.
- The committed record is not valid.
- The file rewrites what the committed record holds.
- The file equals the committed record at its path while its index entry does not.

It commits nothing.
When something cannot be put back or removed, recovery tries the rest.
It then refuses with `recovery_failed`, naming each failure.

## Bookkeeping command

`python3 scripts/issues.py <action> ... [--root <path>]` works from the worktree `--root` (default
the current directory). The worktree must contain `.concorde/config.json` or
`.concorde/install.json`. The former is the project configuration the spec part writes.
The latter is the receipt of an installation. A project without the spec part has the receipt
alone. Every action but `check` acts on the project's Issues. These are the records of the primary
worktree of the repository `--root` lies in. Outside a repository, every action but `check`
refuses with `not_a_repository`. `check` checks the record files of `--root` itself.
Where the spec part is installed, the command reads the registry `.concorde/specs.json` whenever an
action needs the registered Modules. Where the spec part is not installed, a Module is a plain
label the command never checks. `--task` supplies provenance only. The CLI neither requires nor
looks up that task. In the unified CLI, two commands route to this command:

- `python3 scripts/concorde.py issues` in a source checkout.
- `concorde issues` in an installed project.

The actions live in `concorde.issues.command`. The Issue tools ([below](#mcp-tools)) call the
actions with the same arguments. Therefore, each tool answers exactly what the action prints.
For the same reason, each tool refuses with the same link as the action. The tools are:

- `issue_list`, with `list`'s options.
- `issue_show`.
- `issue_check`, the primary worktree's `check`.
- `issue_report`, with the report as an object `report` or a `file` relative to the session's
  worktree, and `check`.
- `issue_close`.
- `issue_reopen`.

`issue_list` takes these options:

- `status`.
- `module`.
- `tier`, a nonempty list.
- `severity`, a nonempty list.
- `sort`.

The Issue tools' writes never wait for the merge lock (`wait` 0). The tools record the session
as the provenance above says and as a disposition's actor. `recover` and `archive` have no tool.

| Action | Effect and output |
| --- | --- |
| `list [--status open\|closed] [--module <module>] [--tier <tier>]... [--severity <severity>]... [--sort severity]` | `{"issues": [...]}`: the summary rows of `list_issues` with `--status` as `status`, `--module` as `target_id`, the `--tier` and `--severity` values, which may each be repeated, as `tiers` and `severities`, and `--sort` as `sort`; without an option, every Issue by identity |
| `show <id>` | `{"issue": <record>, "revision": <digest>, "path": <the path it is committed at>}` |
| `check` | `{"errors": [...], "notes": [...]}`, exit status 1 when `errors` is nonempty and 0 otherwise |
| `recover` | Runs `recover_issues` on the primary worktree, waiting for the merge lock, and prints its `{"recovered": [...], "left": [...]}` |
| `archive` | Runs `archive_issues` on the primary worktree, waiting for the merge lock, and prints its `{"moved": [...], "left": [...]}` |
| `report --file <report.json> [--task <task-id>]` | Records the report in the file with the provenance above through `record_report` and prints what it returns, `{"receipt": <receipt>, "revision": <digest>}` |
| `report --file <report.json> --provenance <provenance.json>` | Records the report in the file with the provenance in the provenance file, `{invocation_id, agent, operation, phase, target_id, context_id, change_id, head}`, which its caller vouches for, exactly as `record_report` records it for a library caller, and prints what it returns, `{"receipt": <receipt>, "revision": <digest>}` |
| `report --file <report.json> --check` | Runs every check `report` runs on the file, but resolves no reporting Module for a report with an `origin`, records nothing and prints `{"valid": true, "file", "report_key", "reporting_module"}`, `reporting_module` being `null` for a report with an `origin` |
| `close <id> --reason resolved\|duplicate\|not-actionable --note <text> --evidence <item>... [--duplicate-of <id>]` | Closes the open Issue at its current revision, moving its record into `closed/`, and prints `{"issue_id", "status": "closed", "revision", "path"}` |
| `reopen <id> --note <text> --evidence <item>...` | Reopens the closed Issue at its current revision, moving its record back into `.concorde/issues/`, and prints `{"issue_id", "status": "open", "revision", "path"}` |

`report` reads the file as UTF-8 JSON. It validates the file as a
[report](#contract.issues.report), including a given `error_chain` against the Framework's
[error contract](../kernel/tracing/contracts.md#contract.tracing.error).
Where the spec part is installed, a non-`null` `owner_target_id` must be a Module of the primary
worktree's registry. Otherwise, the command takes a non-`null` `owner_target_id` as given.
The Issue keeps its `owner_target_id`. For a report without an `origin`, each evidence path must
exist in the worktree `--root`. For a report with an `origin`, each evidence path must exist in
the origin project. In that case, the refusal names the origin project's path. A report file may
lie outside the project, such as a report another project wrote. When the owner is `null`, the
registry must have exactly one root Module. That root Module becomes the reporting Module.
Where the spec part is not installed, there is no registry to find a root Module.
In that case, the command refuses a `null` owner with `no_reporting_module`.
The refusal's message says the spec part is not installed.
For a report with an `origin`, `--check` resolves no reporting Module, since the project that
records the report resolves it. Such a report can be a
[defect report](../glossary.json#concept.defect-report) checked before it is handed to the
[Concorde repository](../glossary.json#concept.concorde-repository).
For this `--check`, a `null` owner is refused neither way. A named owner is checked as for
recording. For a worktree, the spec part counts as installed exactly when its registry file
`.concorde/specs.json` exists. When that file exists but does not read as the registry, the command
refuses with `unreadable_registry`. A file with `issue_id` and `expected_revision` appends to that
Issue. The revision is the one last printed for the Issue by one of these actions:

- `show`.
- `report`.
- `close`.
- `reopen`.

`close` and `reopen` read the Issue's current revision. They dispose the Issue at exactly that
revision with actor `main-agent`, or the session for the tools. They take neither `--task` nor an
expected-revision argument. Their concurrency check protects the interval from their own read
to publication. It does not protect the interval since the main agent's earlier `show`.
`--evidence` takes one or more items. It may be repeated. The items must be nonblank and distinct.
`--note` must be nonblank. With `--reason duplicate`, `--duplicate-of` is required.
With any other reason, `--duplicate-of` is refused. Before reading the Issue, the command itself
checks these argument rules, like a missing argument or an unknown reason.
The command refuses a violation with `usage`. A `--duplicate-of` naming the Issue being closed
passes these argument rules. The store refuses it with `invalid_issue`.

<a id="disposing-under-a-held-lock"></a>

Code of the issues part and Distribution's project MCP server dispose an Issue through the same
action. Distribution's project MCP server composes the parts' tools. The action is the library
entry of `concorde.issues.command` that `close` and `reopen` run. Every other part runs
`concorde issues close` or `reopen` instead:

```python
dispose(root, issue_id, reason, note, evidence, *, duplicate_of=None, actor="main-agent",
        wait=300) -> dict
```

`reason` is a closing reason, or `reopened` to reopen. `root` is any worktree of the project.
The action checks the argument rules above first. It refuses a violation with `usage`.
It reads the Issue's current revision in the primary worktree. It disposes the Issue there at
that revision as `dispose_issue` does, recording `actor`. It returns what `close` and `reopen`
print, `{"issue_id", "status", "revision", "path"}`. The action raises every refusal as the
command's `Refusal`. Its `code` is the refusal code. Its `link` is the error link below, the one
the command would print. The caller decides what the refusal means for its own work.
The caller supplies the note and evidence its own [Spec](../glossary.json#concept.spec) names.

Every refusal has these effects:

- It prints `{"error": <link>}`.
- It commits nothing.
- It leaves no record a read shows.

A refusal writes nothing of its own either, with one exception. A write refused with
`recovery_failed`, or a process killed while writing, may leave an uncommitted record in the
primary worktree. The next write or `recover` puts that record back, so a refused write may be
repeated. A write runs recovery before it checks its request. That recovery puts back only what
earlier writes left uncommitted. The recovery stays done whatever the request's outcome.
The link is a `component` link of the Framework's
[error chain](../kernel/tracing/contracts.md#contract.tracing.error) with the actor
`Issues (concorde issues)`. Its code is the refusal code. Its detail states what is wrong.
The detail names the relevant item:

- The Issue.
- The report file and field.
- The argument concerned.

For these codes, the link's reason is `environment`:

- `io_error`.
- `merge_busy`.
- `merge_incomplete`.
- `unreadable_merge_marker`.
- `commit_failed`.
- `recovery_failed`.
- `uncommitted_change`.
- `not_a_repository`.

For every other code, the link's reason is `input`. These environment refusals are failures of
the Issue system itself. Each lists this among its options: its
[error chain](../glossary.json#concept.error-chain) is carried in the task's
[decision log](../glossary.json#concept.decision-log) and escalation, or in the run's result.
The option says the error chain is never reported as an Issue. The Issue store raises
`IssueError`, Issues' own error type with its own codes. Each code states the Issue rule it breaks
and its remediation. When a refusal comes from an `IssueError`, the link has these details:

- Its explanation is that rule.
- Its option is that remediation.

When the request is unusable, the exit status is 2. The codes for an unusable request are:

- `usage`.
- `not_a_project`.
- `unreadable_file`.

When the request is refused, the exit status is 1. Every other code denotes a refused request.

`check` reads the registry. It reads every entry of `.concorde/issues/` and of its `closed/` folder
of `--root`, except hidden files such as `.gitignore`. It reads these entries as files on disk
(`read_record_file`), committed or not. Each error names the file. `check` reports these errors:

- An entry other than the `closed` directory itself is not a regular file named
  `I-<32 hex digits>.md`.
- A `closed` is no directory.
- A record does not read as valid.
- A record is misplaced.
- An Issue is recorded in both folders.
- Where the spec part is installed, an open Issue's owner is not a registered Module
  (`<id> names unknown owner <module>`).

For a misplaced record, the error names its status and place. It says to run
`concorde issues archive` in the primary worktree, which moves the record to its place.
For an Issue recorded in both folders, the error names both paths and the repair.
The repair is to keep the record whose reports and dispositions begin with the other's.
It also removes the other record with `git rm` in a commit of its own.
A closed Issue with an unknown owner produces the same text as a note, which does not change the
exit status. Without the spec part, `check` does the following:

- It reads no registry.
- It judges no owner.
- It adds one note saying that the spec part is not installed, so that no owner was checked.

An absent directory passes. Concorde's configuration registers `check` as the
[configured check](../glossary.json#concept.configured-check) `check.issues.store` of
`module.issues`. The configured check has the argument vector
`["{python}", "scripts/issues.py", "check"]` and a 60-second timeout.

## MCP tools

The issues part registers these tools with the
[project MCP server](../glossary.json#concept.project-mcp-server). Each answers as the
[bookkeeping command](#bookkeeping-command)'s action it names. Each refuses with that action's
link. Its writes never wait for the merge lock. Each records the calling session as reporter and
actor. In a task worktree bound as a workspace, it records `task-session` and its task.
Otherwise, it records `main-agent` without a task. Each write tool's description also explains:

- That the write first puts back what a killed Issue write left.
- How its `recovery_failed` refusals are put right.
- How its `uncommitted_change` refusals are put right.

Recovery itself is `concorde issues recover`'s alone.

| Tool | Arguments | Result |
| --- | --- | --- |
| `issue_list` | optional `status` (`open` or `closed`), `module`, `tier` (nonempty list of tiers), `severity` (nonempty list of severities), `sort` (`severity`) | as `concorde issues list` with `--status`, `--module`, `--tier` and `--severity` for each, and `--sort` |
| `issue_show` | `issue` | as `concorde issues show <issue>` |
| `issue_check` | none | as `concorde issues check` in the primary worktree, without its exit status |
| `issue_report` | exactly one of `report`, a [report](#contract.issues.report) as an object, and `file`, a report file's path relative to the session's worktree; optional `check` | as `concorde issues report --file <file> [--check]` run in the session's worktree, never waiting for the merge lock, with the session's provenance: `task-session` and its task in a task worktree bound as a workspace, `main-agent` without a task otherwise; a call naming both or neither of `report` and `file` is refused with `invalid_input` |
| `issue_close` | `issue`, `reason` (`resolved`, `duplicate` or `not-actionable`), `note`, `evidence` (nonempty); optional `duplicate_of` | as `concorde issues close`, never waiting for the merge lock, with the session as actor as for `issue_report` |
| `issue_reopen` | `issue`, `note`, `evidence` (nonempty) | as `concorde issues reopen`, never waiting for the merge lock, with the session as actor |

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
| `no_reporting_module` | a report names no owner and the registry has no single root Module, or the spec part is not installed |
| `missing_evidence` | a report's evidence path does not exist in the project |
| `unreadable_registry` | where the spec part is installed, the registry `.concorde/specs.json` cannot be read |
| `io_error` | a file operation failed |
| `usage` | the arguments do not form a request of the command |
| `invalid_input` | an Issue tool's arguments are not an object, do not match its input schema, or, for `issue_report`, name both or neither of `report` and `file`; the tool refuses the call before running the command |
| `not_a_project` | `--root` has neither `.concorde/config.json` nor `.concorde/install.json` |
| `unreadable_file` | the report file cannot be read as UTF-8 text |
| `not_a_repository` | `--root` lies in no Git repository, whose primary worktree would keep the Issues |
| `not_primary` | a store write names a root that is not the primary worktree |
| `merge_busy` | the merge lock stayed held for the whole wait; the message names its holder |
| `merge_incomplete` | the Kernel's [unfinished-merge marker](../glossary.json#concept.unfinished-merge-marker) is present: a merge into the primary branch is unfinished; the message is the Kernel's account of it, with the commands that finish it |
| `unreadable_merge_marker` | the unfinished-merge marker `.concorde/unfinished-merge.json` cannot be read, is no JSON or breaks its contract, so the write cannot tell whether a merge is unfinished; the message names the file |
| `commit_failed` | the primary worktree's `HEAD` is detached or Git refused the commit of the record, which was put back |
| `recovery_failed` | an uncommitted record, the write's own after a failure or one an earlier write left, could not be put back; it stays uncommitted and no read shows it |
| `uncommitted_change` | the record the write would change differs from its committed version in a way no write leaves; it is left as it is |
