---
audience: shared
---

## Issues

The primary worktree keeps the project's Issues, its durable records of concrete problems.
Read and write them with these tools of the project MCP server:

- `issue_list`
- `issue_show`
- `issue_report`
- `issue_close`
- `issue_reopen`

These tools record you as the task session of your task. The `concorde issues` command does the
same from your shell. It also does the same for the runs you start.
A problem you find that this task will not fix is worth an Issue. First read the Issues of the
Module concerned with `issue_list` filtered by `module` and `status` `open`.
When the problem may have been fixed before, include `closed` in the filter. Never read the
whole project's list. Use `issue_show` for a possible match.
When an Issue already tracks the problem, append to that Issue rather than create another.
Use its `issue_id` and the `expected_revision` that `issue_show` printed.
Every report states the problem completely with these fields:

- `description`
- `impact`
- `basis`
- `evidence`

Every report carries its `tier`, which says who may handle it:

- `suggestion`: no problem today.
- `obvious-fix`: an obvious problem with an obvious fix.
- `preferred-fix`: several fixes, one clearly better.
- `decision-needed`: the problem is unclear or its fix uncertain.

Every report also carries its `severity`, which says how much it matters:

- `critical`: any of these problems:
  - Wrong results.
  - Lost data.
  - A security hole.
  - A core flow broken with no workaround.
- `high`: a main flow broken or wrong with a workaround.
- `medium`: a secondary flow or an edge case.
- `low`: cosmetic. Nothing goes wrong.

For an Issue your task is to fix, handle it by its tier. Such an Issue is named in your task
brief or found by a review you ran. Handle the tiers as follows:

- Fix an `obvious-fix` Issue yourself.
- Fix a `preferred-fix` Issue with the better fix. Say in your report which fix you chose and why.
- Never settle a `decision-needed` Issue. Escalate it with these details:
  - Its identity.
  - The options.
  - Your recommendation.

A `suggestion` blocks nothing.
Never close an Issue you fixed. Add it to your task with `concorde task resolve <task> <issue>…`.
Once the fix is on the primary branch, the task's merge closes the Issue.
Say in your report which Issues the task resolves.

**After a review.** Where the method part is installed, these tools report every finding themselves:

- `spec_review`
- `spec_panel`
- `code_review`

Where the method part is installed, each finding is an Issue of the Module it concerns.
Where the method part is installed, the tools' result names:

- Each finding's Issue (`issue`).
- The earlier Issues that still stand (`earlier_issues.carried`).
- The earlier Issues that the review found resolved (`earlier_issues.resolved`).

Handle each by its tier as above. For an Issue the review lists as resolved, follow these rules:

- When your task fixed it, add it to your task with `concorde task resolve`.
- Otherwise, close it with `issue_close` as `resolved`. Use the review's run as evidence.

When an Issue tool's refusal has reason `environment`, the refusal is a failure of the Issue system itself.
Such refusals include:

- `merge_busy` while a merge holds the lock.
- `merge_incomplete`
- `commit_failed`
- `recovery_failed`
- `uncommitted_change`

Never report such a refusal as an Issue because it is a failure of the Issue system itself.
Record it in the decision log. For a busy merge lock, wait with
`concorde task wait --lock merge` in background Bash. Then write again.
For any other such refusal, escalate with `--error-file` naming a file holding its error.
`recovery_failed` and `uncommitted_change` concern an Issue record in the primary worktree.
The main agent puts that record right with `concorde issues recover` or by reverting the record.
Never run that recovery yourself. Never touch that record yourself.
