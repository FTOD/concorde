---
audience: shared
---

## Concorde

This project uses Concorde. In the primary worktree you are Concorde's main agent: follow the
`concorde` skill (`.claude/skills/concorde/SKILL.md`). Here, `concorde` means the
`.concorde/bin/concorde` of the worktree you are in.

In short:

- Discuss and agree direction with the developer.
- Make every change of Spec meaning or code behaviour as a task (`concorde task open`), never in the
  primary worktree, except an approved small change. Such a change can be a typo or a one-line fix.
  The developer must approve it after you say what you would change and why it is small.
- After recording its task brief in the task's decision log, hand every task, even a single one, to
  a task session (`concorde task session`). Never work inside a task worktree yourself.
- Wait to be woken, never polling with `sleep`. Prefer the project MCP server `concorde` (the
  skill's "The project MCP server"). Its `task_merge` never waits for a lock. When the developer
  started your session with `--dangerously-load-development-channels server:concorde`,
  `register_wait` wakes you through its channel. Otherwise, it returns a `concorde task wait`
  command for background Bash.
- Record every decision you made alone for a task in its decision log. There, its task session
  records its own decisions and the runs it started that ended other than `ok`.
- When a result or refusal is not `ok`, read its whole error chain.
- Since a task never asks the developer in place, answer the decisions a task session escalates
  together. Decide what your authority covers and ask the developer the rest at once, recording each
  answer with `concorde task answer`.
- When ListAgents names your session otherwise than the `--main` you gave your tasks, as after a
  resume, first rebind those not ended. Use
  `concorde task list --main <former> --state open,active,delivered,merging` and
  `concorde task rebind`. Then read their unanswered reports and send again each latest recorded
  answer (the skill's "When your session name changed").
- Ask the developer only about decisions with major impact. Add your own link to the chain with
  `concorde task escalate` instead of summarizing it.
- Merge delivered task branches without asking, always with `concorde task merge <task>`, never
  `git merge`.
- On `merge_conflict`, have the task's session merge the primary branch into its task branch. Also
  do this for each open task after a `concorde update` that asks for it.
- Before anything else, finish a merge that a `merge_incomplete` refusal names with
  `concorde task merge <task> --resume` (or `--abort`).

A session started by `concorde task session` is a task session, not the main agent. Its first
prompt says how it works.
