# Decision log: pi-task-sessions

Goal: Support task sessions in pi: a pi main session starts pi task sessions (same program as the main session, same pi configuration) that run in rounds of headless pi -p under Concorde's task-session boundary (write/edit confined to the task worktree and decision log, bash in sandbox-runtime), report through a structured concorde_report tool, and are resumed with the main agent's answer; a supervisor records progress and failures as error chains and the pi main extension shows and wakes on them

## Closed: merged, 2026-09-26T04:18:16Z
