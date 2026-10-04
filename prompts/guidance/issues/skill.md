---
audience: shared
---

## Issues

Issues are the project's durable records of concrete problems. The primary worktree keeps them.
Every session and run sees the same Issues at once. Manage them through the project MCP server's
Issue tools. These tools answer as `concorde issues` does:

- Read with `issue_list` and `issue_show`.
- Write with `issue_report`.
- Write with `issue_close`.
- Write with `issue_reopen`.
- Check the records with `issue_check`.

`issue_list` returns a row per Issue with its severity and tier, open and closed. It filters by:

- `status`
- `module`
- `tier`
- `severity`

With `sort` `severity`, it puts the most severe Issues first. A task session reaches the same Issues
as the runs it starts do, through these tools or the `concorde issues` command.
No Issue is created or closed behind your back, apart from these exceptions:

- Where the method part is installed, a review Operation reports the problems it finds.
- Where the coordination part is installed, a task merge closes the Issues its task resolves.

There is no automatic Issue notification.

**Recording.** A problem the current task will not fix is worth an Issue for later work.
One such problem is a Spec gap a worker reported about another Module.
First read the Issues the problem could duplicate: those of the Module concerned.
When checking for duplicates before recording a problem, never read the whole project's list.
Use `issue_list` filtered by `module` and `status` `open`.
When the problem may have been fixed before, include `closed` too. Use `issue_show` for a possible
match. Instead of creating another Issue, append to the Issue that already tracks the problem.
Use its `issue_id` and the `expected_revision` that `issue_show` printed.
Before appending a new observation to a closed match, reopen it.
Repeating a creation creates another Issue, even with the same report key.
A report states the problem completely because whoever it is escalated to acts on its identity
alone. The report states:

- `description`
- `impact`
- `basis`
- `evidence`

The report carries its `tier`, which says who may handle it:

| Tier | The problem | Who handles it |
| --- | --- | --- |
| `suggestion` | none today, only a suggestion | nobody need; it blocks nothing |
| `obvious-fix` | obvious, and so is its fix | the task session fixing it, alone |
| `preferred-fix` | simple, with several fixes of which one is clearly better | the task session fixing it, which reports the fix it chose to you |
| `decision-needed` | unclear, or its fix is uncertain | you decide, or put it to the developer, before anyone fixes it |

The report also carries its `severity`. This says how much the problem matters whoever handles it,
most severe first:

| Severity | The problem's consequence |
| --- | --- |
| `critical` | wrong results, lost or corrupted data, a security hole, or a core flow broken with no workaround |
| `high` | a main flow broken or wrong with a workaround, or a promise that misleads the work relying on it |
| `medium` | a secondary flow or an edge case fails, or a gap that slows the work without misleading it |
| `low` | cosmetic, such as wording, naming or layout; nothing goes wrong |

**Fixing.** Recording and fixing are separate. A review Operation only reports.
Fixing is later work of a task. Choose what to fix first from `issue_list` with `status` `open` and
`sort` `severity`. This puts the most severe Issues first, then orders by tier, with
`decision-needed` first. Solve an Issue like any other work.
Where the coordination part is installed, open a task for the Issue's current Module.
Where the coordination part is installed, name the Issues it fixes with
`concorde task open <task> … --resolves <issue>[,<issue>…]`, or later
`task_resolve`. Tell its session in the task brief which tier each Issue has.
The session handles Issues by tier:

- It fixes `obvious-fix` Issues itself.
- It fixes `preferred-fix` Issues itself. It reports the fix it chose.
- It escalates a `decision-needed` Issue by its identity for you to decide or to put to the developer.

Where the method part is installed, these reviews report each finding as an Issue:

- `spec_review`
- `spec_panel`
- `code_review`

Where the method part is installed, each Issue carries the severity and tier its reviewer or chair gave it.
Where the method part is installed, the review lists these earlier Issues in its result:

- Those that still stand.
- Those it found resolved.

Where the method part is installed, the task session fixes the Issues that still stand by their tier
in later `specify` or `implement` work.
Where the method part is installed, the task session closes the resolved Issues.
When the method part is installed and the task fixed them, the session closes them through its task.
None of these steps changes an Issue:

- Starting the task.
- Fixing the task.
- Delivering the task.

Once `task merge` merges the task and its checks pass, the merge does the following:

- It closes each Issue the task resolves as `resolved` with the merge commit as evidence.
- It lists those Issues as `resolved`.
- It names in its warnings any Issues it could not close.

A task that ends without merging closes none. Close an Issue by hand with `issue_close` only in
these cases:

- The reason is `duplicate`, with `duplicate_of` naming another open Issue.
- The reason is `not-actionable`.
- The Issue was fixed without such a task.

For recurrence, use `issue_reopen`, which keeps every report and disposition.
Check that the evidence supports every decision. The store checks its form, not its truth.
On `stale_issue`, take these steps before retrying:

- Read the record again.
- Reconsider.

**When the Issue system fails.** Never record a failure of the Issue system itself as an Issue.
Such a failure is a refusal of the Issue tools or command whose reason is `environment`.
Examples include:

- `merge_busy`
- `merge_incomplete`
- `commit_failed`
- `recovery_failed`
- `uncommitted_change`

The reason is that an Issue system that failed cannot be trusted to record its own failure.
Treat it as any other failure of a task, with its error chain in the task's decision log and
escalation. When you met the failure for no task, there is no decision log or escalation to carry
it. One such case is an Issue you recorded while discussing the project.
When you met the failure for no task, show the developer its whole error chain at once, as rendered, never a summary of it.
Open a task only when the failure leads to work.

`merge_busy` means another process holds the merge lock that every Issue write takes.
Another Issue write can hold it. Where the coordination part is installed, these operations can
also hold it:

- A merge.
- A task open.
- A task close.

Where that part is installed, use `register_wait` for the merge lock.
Where that part is installed, once the lock is released, write again.
Without that part, only another Issue write holds the lock,
for moments. For that reason, write again shortly after.

`recovery_failed` means a record an Issue write published could not be put back.
The record stays uncommitted in the primary worktree. No read shows it.
Fix the cause the refusal names, such as a stale `index.lock` or a refusing commit hook.
Then run `concorde issues recover`, which puts the record back. The recover command has no MCP tool.
Then write again.

`uncommitted_change` means the record of the Issue you wrote holds a change no Issue write made,
such as an edit by hand. The Issue system neither overwrites nor discards that change.
Take these steps:

- Inspect the change with `git diff` in the primary worktree.
- Revert the change.
- Write again.

Writes of other Issues are not held up. Never commit such a record by hand.
