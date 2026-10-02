---
audience: shared
---

## Concorde

This project uses Concorde. In the primary worktree you are Concorde's main agent: follow the
`concorde` skill (`.claude/skills/concorde/SKILL.md`); `concorde` means the
`.concorde/bin/concorde` of the worktree you are in. In short: discuss and agree direction with the
developer; make every change of Spec meaning or code behaviour as a task (`concorde task open`),
never in the primary worktree, except a small change such as a typo or a one-line fix that the
developer approved after you said what you would change and why it is small; hand every task,
even a single one, to a task session (`concorde task session`) after recording its task brief in
the task's decision log, and never work inside a task worktree yourself; wait to be woken, never
polling with `sleep`, preferring the project MCP server `concorde` (the skill's "The project MCP
server": `task_merge` never waits for a lock and `register_wait` wakes you through its channel when
the developer started your session with `--dangerously-load-development-channels
server:concorde`, otherwise it returns a `concorde task wait` command for background Bash); record
every decision you made alone for a task in its decision log, where its task session records its
own decisions and the runs it started that ended other than `ok`; read the whole error chain of
a result or refusal that is not `ok`; a task never asks the developer in place,
so answer the decisions a task session escalates together, deciding what your authority covers and
asking the developer the rest at once, recording each answer with `concorde task answer`; when
ListAgents names your session otherwise than the `--main` you gave your tasks, as after a resume,
first rebind those not ended (`concorde task list --main <former> --state
open,active,delivered,merging`, `concorde task rebind`), read their unanswered reports and send
again each latest recorded answer (the skill's "When your session name changed"); ask the developer only about decisions with major impact,
adding your own link to the chain with `concorde task escalate` instead of summarizing it; merge
delivered task branches without asking, always with `concorde task merge <task>`, never `git
merge`, have the task's session merge the primary branch into its task branch on `merge_conflict`
and, for each open task, after a `concorde update` that asks for it, and finish a merge that a
`merge_incomplete` refusal names with `concorde task merge <task> --resume` (or `--abort`) before
anything else. A session started by `concorde task session` is a task session, not the main
agent: its first prompt says how it works.
