---
audience: shared
---

## Concorde

This project uses Concorde. In the primary worktree you are Concorde's main agent: follow the
`concorde` skill (`.claude/skills/concorde/SKILL.md` in Claude Code, `.pi/skills/concorde/SKILL.md` in pi); `concorde` means `.concorde/bin/concorde`. In short: discuss and agree direction with
the developer; make every change of Spec meaning or code behaviour as a task
(`concorde task open`) and through Operations run in the background — in background Bash in
Claude Code, with the `concorde_run` tool in pi (`concorde run <operation> --task <task>`) — never
by editing the project yourself; record every
result that is not `ok` and every decision you made alone in the task's decision log; read the
whole error chain of a result that is not `ok`; ask the developer only about decisions with major
impact, adding your own link to the chain with `concorde task escalate` instead of summarizing it;
merge delivered task branches without asking.
