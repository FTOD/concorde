# Developing Concorde with pi

These instructions apply to pi only, including when both `AGENTS.md` and `CLAUDE.md` are loaded.
Claude Code follows `CLAUDE.md` for its host workflow.

Read [DEVELOPING.md](DEVELOPING.md) in full before working on this source checkout; pi does not
import files named in `AGENTS.md`, so open it with the read tool. It contains shared development
rules, preparation, verification, delivery, merge checks and defect handling. Also read
`specs/concorde/glossary.json`: the "Project terms" rule of `DEVELOPING.md` asks you to use every
term exactly as the glossary defines it.

## Main session

Stay in the primary worktree. Open a task as described in `DEVELOPING.md`, then start a Concorde
task session in its worktree even for a single task. pi has no EnterWorktree or ExitWorktree tool;
a shell `cd` changes only that command's working directory, not the session's context.

1. Open the task from the primary worktree and obtain its path with
   `python3 scripts/concorde.py task show <task>`.
2. Before starting the session, run `python3 scripts/development/init-references.py` from that
   task worktree, using its own script. The task session cannot register submodules in the shared
   Git configuration.
3. Use `concorde_task_session`, which wakes you when each round ends. The checkout's
   `.pi/settings.json` loads Concorde's pi extension from `src/concorde/main_session/`, so the
   tool is there once pi trusts the project. Without it, run
   `CONCORDE_CLIENT=pi python3 scripts/concorde.py task session <task> --main <its session name>`
   from the primary worktree, and `--answer` on the same command for a subsequent round.
4. Wait for each round without polling: the extension wakes you with its outcome; without it,
   run `CONCORDE_CLIENT=pi python3 scripts/concorde.py task session <task> --wait` in bash with no
   timeout, which returns once the round has ended. Never loop over `sleep` and status files or
   `task show`. Read any escalation's complete chain with
   `python3 scripts/concorde.py task show <task>`. Append to the task's decision log (the path
   `task open` printed) every decision you take without the developer, answer escalations within
   your authority, and have the session finish validation and delivery.
5. After delivery, inspect the result and merge from the primary worktree with the command and
   both merge checks in `DEVELOPING.md`, run in bash with no timeout, and act on every warning the
   merge prints.

For several tasks, start one session per task and coordinate their results from the primary
worktree. Do not edit task sources from the primary pi session or treat shell `cd` as entering a
task. If a merge conflicts, the main agent arranges the Git resolution in the task worktree,
then resumes its task session for verification and delivery before retrying the checked merge.

## Task session

If you are already a Concorde task session in your assigned worktree, do the task directly there.
Do not launch another session. Use that worktree's own `python3 scripts/concorde.py`, run commands
and Operations in foreground Bash with no timeout, and follow the task-session prompt for decision logging,
escalation and the final `concorde_report`. Validate and deliver; leave merging to the main agent.
