---
audience: shared
---

## Issues

The project's Issues, its durable records of concrete problems, are kept by the primary worktree:
read and write them with the project MCP server's `issue_list`, `issue_show`, `issue_report`,
`issue_close` and `issue_reopen`, which record you as the task session of your task; the
`concorde issues` command does the same from your shell, as it does for the runs you start. A problem
you find that this task will not fix is worth an Issue: first read the Issues of the Module concerned with
`issue_list` filtered by `module` and `status` `open` (and `closed` when it may have been fixed
before), never the whole project's list, and `issue_show` for a possible match, and append to the
Issue that already tracks it, with its `issue_id` and the `expected_revision` `issue_show` printed,
rather than create another. Every report states the problem completely (`description`, `impact`,
`basis`, `evidence`) and carries its `tier`, who may handle it: `suggestion` (no problem today),
`obvious-fix` (an obvious problem with an obvious fix), `preferred-fix` (several fixes, one clearly
better) or `decision-needed` (the problem is unclear or its fix uncertain); and its `severity`, how
much it matters: `critical` (wrong results, lost data, a security hole or a core flow broken with no
workaround), `high` (a main flow broken or wrong with a workaround), `medium` (a secondary flow or
an edge case) or `low` (cosmetic; nothing goes wrong).

An Issue your task is to fix, named in your task brief or found by a review you ran, you handle by
its tier: fix an `obvious-fix` Issue yourself; fix a `preferred-fix` Issue with the better fix and
say in your report which fix you chose and why; never settle a `decision-needed` Issue: escalate it,
naming it by its identity, with the options and your recommendation. A `suggestion` blocks nothing.
Never close an Issue you fixed: add it to your task with `concorde task resolve <task> <issue>…`,
and the task's merge closes it once the fix is on the primary branch. Say in your report which
Issues the task resolves.

**After a review.** Where the method part is installed, `spec_review`, `spec_panel` and
`code_review` report every finding themselves, as an Issue of the Module it concerns, and their
result names each finding's Issue (`issue`), the earlier Issues that still stand
(`earlier_issues.carried`) and those the review found resolved (`earlier_issues.resolved`). Handle
each by its tier as above. An Issue the review lists as resolved you add to your task with
`concorde task resolve` when your task fixed it, and otherwise close with `issue_close` as
`resolved`, the review's run as evidence.

A refusal of the Issue tools whose reason is `environment`, such as `merge_busy` while a merge holds
the lock, `merge_incomplete`, `commit_failed`, `recovery_failed` or `uncommitted_change`, is a
failure of the Issue system itself: never report it as an Issue. Record it in the decision log; wait
for a busy merge lock with `concorde task wait --lock merge` in background Bash and write again;
escalate any other with `--error-file` naming a file holding its error. `recovery_failed` and
`uncommitted_change` concern an Issue record in the primary worktree, which the main agent puts
right with `concorde issues recover` or by reverting the record: never run that recovery or touch
the record yourself.
