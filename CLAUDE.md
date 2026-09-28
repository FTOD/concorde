# Developing Concorde with Claude Code

These instructions apply to Claude Code only, including when both `CLAUDE.md` and `AGENTS.md` are
loaded. pi follows `AGENTS.md` for its host workflow.

[DEVELOPING.md](DEVELOPING.md) contains the shared development rules, preparation, verification,
delivery, merge checks and defect handling. Claude Code imports it here, so it is always in
context; follow it in full:

@DEVELOPING.md

The project's terms, which the "Project terms" rule of `DEVELOPING.md` asks you to use exactly as
defined, are loaded from its glossary: @specs/concorde/glossary.json

## Main session

For a single task:

1. Open the task from the primary worktree as described in `DEVELOPING.md`.
2. Enter its worktree with EnterWorktree (`path` set to the task worktree). A session is inside
   at most one task at a time.
3. Prepare dependencies and references, change sources, and verify and commit each verified step,
   following `DEVELOPING.md`. Run every task command with the task worktree's own
   `python3 scripts/concorde.py`.
4. Append to the task's decision log (the path `task open` printed) every decision you took
   without the developer, with its options and reason, and every non-`ok` result with what you
   did about it; reporting them to the developer does not replace the log. Then run validation
   and delivery, in background Bash (`run_in_background`) like every long command.
5. Leave with ExitWorktree (`action: "keep"`). From the primary worktree, merge with the command
   and both merge checks in `DEVELOPING.md`, in background Bash, since its lock waits and checks
   can outlast a foreground call, and act on every warning the merge prints.

For work split into several tasks, stay in the primary worktree. Before starting each task
session, run `python3 scripts/development/init-references.py` from that task's worktree. Then run
`python3 scripts/concorde.py task session <task> --main <its session name>` from the primary
worktree. Each session reports with SendMessage; wait for it instead of polling. Read complete error chains, answer escalations within
your authority, and merge delivered tasks with the shared merge checks.

On `merge_busy`, retry. On `merge_conflict`, re-enter the task worktree, merge main into the task
branch, resolve, verify and deliver again; leave with ExitWorktree (`action: "keep"`) before
retrying the checked merge from the primary worktree. The merge already waits up to `--wait`
seconds for a run of the task, such as a delivery finishing; on `workspace_busy`, retry with a
longer `--wait`. On `merge_incomplete`, finish the interrupted merge the refusal names first, with
`task merge <task> --resume` (or `--abort` when the primary branch is no longer at its merge
commit); bring `merge_diverged` to the developer.

After dispatching tasks to task sessions, show the developer each task's name with its goal in one
line, and report on the tasks by those names.

## Task session

If you are already a Concorde task session in your assigned worktree, do the task directly there.
Do not enter another worktree or launch another session. Use that worktree's own
`python3 scripts/concorde.py` and follow the task-session prompt for execution, decision logging,
escalation and reporting. Validate and deliver; leave merging to the main agent.
