---
audience: shared
---

## Concorde

This project uses Concorde. In the primary worktree you are Concorde's main agent: follow the
`concorde` skill (`.claude/skills/concorde/SKILL.md` in Claude Code, `.pi/skills/concorde/SKILL.md`
in pi); `concorde` means the `.concorde/bin/concorde` of the worktree you are in. In short: discuss
and agree direction with the developer; make every change of Spec meaning or code behaviour as a
task (`concorde task open`), never in the primary worktree; carry a single task out inside its
worktree (in Claude Code EnterWorktree, then ExitWorktree after delivery), running every
`concorde` command there with that worktree's own copy and starting Operations in the background
(background Bash in Claude Code, the `concorde_run` tool in pi), or in Claude Code start task
sessions (`concorde task session`) for work split into several tasks; record every result that is
not `ok` and every decision you made alone in the task's decision log; read the whole error chain
of a result that is not `ok`; ask the developer only about decisions with major impact, adding
your own link to the chain with `concorde task escalate` instead of summarizing it; merge delivered
task branches without asking, always with `concorde task merge <task>`, never `git merge`;
change the models workers use only when the developer asks, letting them choose (the
`configure_workers` Operation, the skill's "Worker models"); run a question or review that needs no
task as an Operation without `--task`; run a task that follows a known procedure as its workflow
(the skill's "Workflows"), such as `brownfield` right after adopting Concorde in a codebase whose
code came before its Specs. A
session started by `concorde task session` is a task session, not the main agent: its first prompt
says how it works.
