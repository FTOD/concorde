# Developing Concorde with Claude Code

These instructions apply to Claude Code only, including when both `CLAUDE.md` and `AGENTS.md` are
loaded. pi follows `AGENTS.md` for its host workflow.

Read [DEVELOPING.md](DEVELOPING.md) in full before working on this source checkout. It contains
shared development rules, preparation, verification, delivery, merge checks and defect handling.

## Main session

For a single task:

1. Open the task from the primary worktree as described in `DEVELOPING.md`.
2. Enter its worktree with EnterWorktree (`path` set to the task worktree). A session is inside
   at most one task at a time.
3. Prepare dependencies and references, change sources, verify and commit each verified step,
   then run validation and delivery, following `DEVELOPING.md`. Run every task command with the
   task worktree's own `python3 scripts/concorde.py`.
4. Leave with ExitWorktree (`action: "keep"`). From the primary worktree, merge with the command
   and both merge checks in `DEVELOPING.md`.

For work split into several tasks, stay in the primary worktree. Before starting each task
session, run `python3 scripts/development/init-references.py` from that task's worktree. Then run
`python3 scripts/concorde.py task session <task> --main <its session name>` from the primary
worktree. Monitor each session's result, read complete error chains, answer escalations within
your authority, and merge delivered tasks with the shared merge checks.

On `merge_busy`, retry. On `merge_conflict`, re-enter the task worktree, merge main into the task
branch, resolve, verify and deliver again; leave with ExitWorktree (`action: "keep"`) before
retrying the checked merge from the primary worktree.

## Task session

If you are already a Concorde task session in your assigned worktree, do the task directly there.
Do not enter another worktree or launch another session. Use that worktree's own
`python3 scripts/concorde.py` and follow the task-session prompt for execution, decision logging,
escalation and reporting. Validate and deliver; leave merging to the main agent.
