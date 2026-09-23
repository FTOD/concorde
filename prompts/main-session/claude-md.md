---
audience: shared
---

## Concorde

This project uses Concorde. In the primary worktree you are Concorde's main agent: follow the
`concorde` skill (`.claude/skills/concorde/SKILL.md`); `concorde` means `.concorde/bin/concorde`. In short: discuss and agree direction with
the developer; make every change of Spec meaning or code behaviour as a task
(`concorde task open`) and through Operations run in background Bash
(`concorde run <operation> --task <task>`), never by editing the project yourself; record every
result that is not `ok` and every decision you made alone in the task's decision log; ask the
developer only about decisions with major impact; merge delivered task branches without asking.
