---
audience: shared
---

## Concorde

This project uses Concorde. In the primary worktree you are Concorde's main agent: follow the
`concorde` skill (`.claude/skills/concorde/SKILL.md`); `concorde` means the
`.concorde/bin/concorde` of the worktree you are in. In short: discuss and agree direction with the
developer, using every project term exactly as its glossary defines it (the skill's "Project
terms"); make every change of Spec meaning or code behaviour as a task (`concorde task open`),
never in the primary worktree, except a small change such as a typo or a one-line fix that the
developer approved after you said what you would change and why it is small; hand every task,
even a single one, to a task session (`concorde task session`) after recording its brief in the
task's decision log, and never work inside a task worktree yourself; wait to be woken, never
polling with `sleep`, preferring the project MCP server `concorde` (the skill's "The project MCP
server": `task_merge` never waits for a lock and `register_wait` wakes you through its channel when
the developer started your session with `--dangerously-load-development-channels
server:concorde`, otherwise it returns a `concorde task wait` command for background Bash); run a question or review that needs no task as an unbound Operation in the
primary worktree, started in background Bash; record every result of a task's runs that is not `ok` and every decision you made alone in the task's decision log;
read the whole error chain of a result that is not `ok`; a task never asks the developer in place,
so answer the decisions a task session escalates together, deciding what your authority covers and
asking the developer the rest at once, recording each answer with `concorde task answer`; when
ListAgents names your session otherwise than the `--main` you gave your tasks, as after a resume,
first rebind those not ended (`concorde task list --main <former> --state
open,active,delivered,merging`, `concorde task rebind`) and read
their unanswered reports (the skill's "When your session name changed"); ask the developer only about decisions with major impact,
adding your own link to the chain with `concorde task escalate` instead of summarizing it, and show
the developer the whole rendered chain of an unbound run that is not `ok`; merge delivered task
branches without asking, always with `concorde task merge <task>`, never `git merge`, have the
task's session merge the primary branch into its task branch on `merge_conflict`, and finish a
merge that a `merge_incomplete` refusal names with `concorde task merge <task> --resume` (or
`--abort`) before anything else; run workers only on the models the tracked
`.concorde/workers.json` enables and chooses, never on anyone's own Claude Code or pi settings,
naming each by a project model name that the developer's untracked model map resolves to each
program's local id, and when the project has no such file ask the developer for its models before
any Operation runs;
change the models workers use only when the developer asks, by editing that file directly: commit
a change of that file alone on the primary branch for future tasks, or change it in a task that is
to use it (the skill's "Worker models"); run a task that follows a known procedure as its workflow (the skill's "Workflows"), such
as `brownfield` right after adopting Concorde in a codebase whose code came before its Specs. A
session started by `concorde task session` is a task session, not the main agent: its first prompt
says how it works.
