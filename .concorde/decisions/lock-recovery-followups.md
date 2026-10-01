# Decision log: lock-recovery-followups

Goal: Close the follow-ups of the lock and Issue-recovery tasks: task open refuses a worktree outside .claude/worktrees, task merge recovers Issue write leftovers before its primary audit, Tracing's lock texts match the per-call MCP server and the workflow lock's close, and main-session guidance and Issue tools know Issue recovery

## Brief (main agent, 2026-10-02)

Five small follow-ups, grouped into one task by the main agent because each is a preferred-fix
or obvious-fix Issue in Modules no running task changes. Read each with
`python3 scripts/concorde.py issues show <id>` first, fix it as its tier says, and report the fix
you chose for each preferred-fix one:

- I-6adb5521ad3a5c55a39350c714193f22 (module.tasks, medium, preferred-fix): `task open --path`
  can place a task worktree outside `.claude/worktrees/`. The developer decided on 2026-10-01
  that every worktree workers run in lives under the primary worktree's `.claude/worktrees/`;
  task worker-git-isolation, running in parallel, makes worker launches refuse any other
  placement. Make `task open` refuse such a path (or drop the option), naming the rule.
- I-7f0b88c134525f939c7c2aed819e8984 (module.tasks, medium, preferred-fix): task merge should
  recover Issue write leftovers (`recover_issues(primary, locked=True)`, from task
  issue-write-recovery, merged 8c4426eb) before its primary_dirty audit.
- I-1a34e4cc427154d493985a20431262ea and I-69624b561d515152854b98adce317251 (module.tracing,
  low, obvious-fix): Tracing's lock texts must say that task_merge's call process, not the
  long-lived server, takes and hands on the locks (mcp-fresh-code, a3d61208), and that close
  holds the workflow lock and a waiting step is refused (workflow-lock-before-records, e4e1f7e5).
- I-539ca8e057db5d859ff5995066608904 (module.main-session, medium, preferred-fix): the
  main-session guidance and Issue tools should know `concorde issues recover`, recovery_failed
  and uncommitted_change.

Do not change the worker placement rule itself or module.workers, module.harness,
module.execution, module.e2e or module.dogfood-scenarios, which worker-git-isolation is
changing. Escalate anything that needs a decision or another Module.

## Task session decisions (2026-10-02)

- I-6adb5521 (preferred-fix): dropped `task open --path` rather than restricting it. Under the
  developer's placement rule the only admitted place is `.claude/worktrees/` of the primary
  worktree, where the default `.claude/worktrees/<task-id>` already lies; another name inside it
  buys nothing, and the MCP `task_open` never offered the option. An old `--path` is now refused by
  the parser as `invalid_command`; the Tasks Spec (module, contracts, requirements) states the one
  placement and the rule. `path_exists` now says to remove the path or choose another identity.
- I-7f0b88c1 (preferred-fix): `task merge` (new merges only, not `--resume`/`--abort`) runs
  `recover_issues(primary, locked=True)` under the merge lock after `mergeable` and before the
  `primary_dirty` check. A recovery failure or records it left do not refuse by themselves: the
  paths stay dirty and `primary_dirty`'s detail names what recovery left (changed by no Issue
  write: inspect and revert) or its failure (fix, then `concorde issues recover`). No new error
  code. Recovered records are not reported, as an Issue write's own recovery reports none.
  `req.tasks.refusal-inert` gains the exception that a refused merge keeps what its Issue recovery
  put back. `--resume` is left without recovery: while a task is `merging`, Issue writes are refused
  with `merge_incomplete`, so none can leave a record then.
- I-1a34e4cc, I-69624b56 (obvious-fix): Tracing's hand-on text names the `task_merge` call's
  process, which execs into `concorde task merge`; the contracts' "Handing a lock on" now covers a
  hand-on by exec. Workflow lock rows name step/report and close (also the close ending a merge),
  and that a waiting step/report takes the removed file and is refused.
- I-539ca8e0 (preferred-fix): guidance (skill.md merge audit and "When the Issue system fails",
  task-session.md Issues) names `recovery_failed`, `uncommitted_change` and `concorde issues
  recover`; task sessions leave both to the main agent. No `issue_recover` MCP tool: module.issues
  says `recover` is the command's alone, and that Module is not this task's. Instead the three
  Issue write tools' descriptions say what recovery does and how both refusals are put right. New
  `req.main-session.issues-recovery` and `scenario.main-session.issue-recovery`.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T16:25:30Z

Task lock-recovery-followups delivered: delivery commit 0a497c80 on concorde/lock-recovery-followups (work commit 4fa9073e). task-validation ready, nothing blocking; build, build --check and spec-validation pass; full suite 895 passed, 4 skipped. Resolves (added with task resolve): I-6adb5521, I-7f0b88c1, I-1a34e4cc, I-69624b56, I-539ca8e0.

Fixes, with the fix I chose for each preferred-fix one:
- I-6adb5521 (preferred-fix): dropped `task open --path` instead of restricting it. The only allowed placement is under .claude/worktrees/, and the default .claude/worktrees/<task-id> is already there, so another name inside it buys nothing; MCP task_open never offered the option. An old --path is now refused by the parser as invalid_command. The Tasks Spec (module, contracts, req.tasks.one-worktree/worktree-ignored) states the one placement and the rule. path_exists now says to remove the path or choose another identity.
- I-7f0b88c1 (preferred-fix): a new `task merge` runs recover_issues(primary, locked=True) under the merge lock, after the mergeable checks and before primary_dirty. No new error code: what recovery left (records changed by no Issue write) or its failure is named in primary_dirty's detail, with how to put it right. Recovered records are not reported, as an Issue write's own recovery reports none. --resume/--abort do not recover: while a task is merging, Issue writes are refused with merge_incomplete, so none can leave a record then. req.tasks.refusal-inert gains the exception that a refused merge keeps what its recovery put back; Tasks' uses of module.issues now relies on req.issues.uncommitted-recovered. New scenario.tasks.merge-recovers-issue-records with a test.
- I-1a34e4cc, I-69624b56 (obvious-fix): Tracing now says the task_merge call's process takes the locks and hands them on by exec into `concorde task merge`; the long-lived server takes none. The contracts' "Handing a lock on" now covers a hand-on by exec. Both workflow lock rows name step/report and close (also the close that ends a merge), and say a step or report that waited for the lock takes the removed file and is refused.
- I-539ca8e0 (preferred-fix): skill.md (merge audit, "When the Issue system fails") and task-session.md now name recovery_failed, uncommitted_change and `concorde issues recover`; task sessions leave both to the main agent. I added no issue_recover MCP tool, because module.issues states `recover` is the command's alone and that Module is not this task's. Instead the descriptions of issue_report/issue_close/issue_reopen say what recovery does and how each refusal is put right. New req.main-session.issues-recovery, scenario.main-session.issue-recovery and a test.

Nothing escalated, nothing open. If you want recover as an MCP tool, that is a module.issues change for another task.

## Closed: merged, 2026-10-01T16:25:50Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 0a497c803d3875cf57b59664a4d4c0f6fc6952ba into main and closed it as merged. Nobody answers a report after that.
