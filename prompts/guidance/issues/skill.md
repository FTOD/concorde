---
audience: shared
---

## Issues

Issues are the project's durable records of concrete problems: the primary worktree keeps them, and
every session and run sees the same Issues at once. Manage them through the project MCP server's
Issue tools, which answer as `concorde issues` does: `issue_list` (a row per Issue with its severity and tier,
open and closed, filtered by `status`, `module`, `tier` and `severity`, and with `sort` `severity`
most severe first) and `issue_show` to read,
`issue_report`, `issue_close` and `issue_reopen` to write, and `issue_check` to check the records. A task session reaches the same Issues, through these tools or
the `concorde issues` command, as the runs it starts do. No Issue is created or closed behind your back, apart from a
review Operation that reports the problems it finds, where the method part is installed, and a task
merge that closes the Issues its task resolves, where the coordination part is; there is no
automatic Issue notification.

**Recording.** A problem the current task will not fix, such as a Spec gap a worker reported about
another Module, is worth an Issue for later work. Read first the Issues it could duplicate, those of
the Module concerned, with `issue_list` filtered by `module` and `status` `open` (and `closed` too
when the problem may have been fixed before), never the whole project's list, and `issue_show` for a
possible match: append to the Issue that already tracks the problem, with its `issue_id` and the
`expected_revision` that `issue_show` printed, instead of creating another; reopen a closed match
before appending a new observation. Repeating a creation creates another Issue, even with the same
report key. A report states the problem completely, `description`, `impact`, `basis` and `evidence`, because whoever it is
escalated to acts on its identity alone, and carries its `tier`, who may handle it:

| Tier | The problem | Who handles it |
| --- | --- | --- |
| `suggestion` | none today, only a suggestion | nobody need; it blocks nothing |
| `obvious-fix` | obvious, and so is its fix | the task session fixing it, alone |
| `preferred-fix` | simple, with several fixes of which one is clearly better | the task session fixing it, which reports the fix it chose to you |
| `decision-needed` | unclear, or its fix is uncertain | you decide, or put it to the developer, before anyone fixes it |

and its `severity`, how much the problem matters whoever handles it, most severe first:

| Severity | The problem's consequence |
| --- | --- |
| `critical` | wrong results, lost or corrupted data, a security hole, or a core flow broken with no workaround |
| `high` | a main flow broken or wrong with a workaround, or a promise that misleads the work relying on it |
| `medium` | a secondary flow or an edge case fails, or a gap that slows the work without misleading it |
| `low` | cosmetic, such as wording, naming or layout; nothing goes wrong |

**Fixing.** Recording and fixing are separate: a review Operation only reports, and fixing is later
work of a task. Choose what to fix first from `issue_list` with `status` `open` and `sort`
`severity`, which puts the most severe Issues first, then by tier, `decision-needed` first. Solve an Issue like any other work: where the coordination part is installed, open a task for
the Issue's current Module and name the Issues it fixes,
`concorde task open <task> … --resolves <issue>[,<issue>…]`, or later `task_resolve`. Tell its session in the task brief which tier each Issue has: it fixes `obvious-fix` and
`preferred-fix` Issues itself, reporting the fix it chose for a `preferred-fix` one, and escalates a
`decision-needed` Issue, naming it by its identity, for you to decide or to put to the developer.
Where the method part is installed, a review
(`spec_review`, `spec_panel`, `code_review`) reports each of its findings as an Issue with the severity and tier
its reviewer or chair gave it, and lists in its result the earlier Issues that still stand and those it found
resolved; the task session fixes the first by their tier in later `specify` or `implement` work and
closes the resolved ones, through its task when the task fixed them. Starting, fixing or delivering
the task changes no Issue; once `task merge` has merged it and its
checks passed, the merge closes each Issue the task resolves as `resolved` with the merge commit as
evidence and lists them as `resolved`, and names in its warnings any it could not close. A task that
ends without merging closes none. Close an Issue by hand with `issue_close` only for another reason,
`duplicate` (with `duplicate_of`, another open Issue) or `not-actionable`, or when it was fixed
without such a task; for recurrence use `issue_reopen`, which keeps every report and disposition.
Check that the evidence supports every decision: the store checks its form, not its truth. On
`stale_issue`, read the record again and reconsider before retrying.

**When the Issue system fails.** Never record a failure of the Issue system itself, a refusal of the
Issue tools or command whose reason is `environment`, such as `merge_busy`, `merge_incomplete`,
`commit_failed`, `recovery_failed` or `uncommitted_change`, as an Issue: an Issue system that failed
cannot be trusted to record its own failure. Treat it as any other failure of a task, its error
chain in the task's decision log and escalation. When you met the failure for no task, such as on an
Issue you recorded while discussing the project, there is no decision log or escalation to carry it:
show the developer its whole error chain at once, as rendered, never a summary of it, and open a
task only when the failure leads to work. `merge_busy` means another process holds the merge lock
that every Issue write takes, such as another Issue write or, where the coordination part is
installed, a merge, task open or close: there, `register_wait` for the merge lock and write again
once it is released; without that part only another Issue write holds it, for moments, so write
again shortly after. `recovery_failed` means a record an Issue write published could not be put back and
stays uncommitted in the primary worktree, shown by no read: fix the cause the refusal names, such
as a stale `index.lock` or a refusing commit hook, then run `concorde issues recover` (it has no MCP
tool), which puts it back, and write again. `uncommitted_change` means the record of the Issue you
wrote holds a change no Issue write made, such as an edit by hand, which the Issue system neither
overwrites nor discards: inspect it with `git diff` in the primary worktree, revert it, and write
again; writes of other Issues are not held up. Never commit such a record by hand.
