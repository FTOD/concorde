# Concorde Source-Checkout Agent Policy

Before any project action, read and follow `AGENTS.md` in this worktree as the canonical policy.
Developing this checkout is direct developer-authorized maintenance in the current worktree; a
Concorde graph (`concorde-dev-loop`, `concorde-specify-loop`, `concorde-main`, `concorde-review`,
`concorde-reflections-triage` or a lifecycle Skill) runs on this checkout only when the user
explicitly asks for it, never because a task looks like a development change. This checkout's
`.claude/settings.json` refuses native worktree creation (`EnterWorktree`,
worktree-isolated subagents, `git worktree add`, `claude --worktree`). A further worktree exists
only when an explicitly requested graph creates it, followed by a P10 handoff into the new
worktree's own session.

In a fresh clone, run `python3 scripts/concorde.py build` once so the Concorde Skills exist, then
`python3 scripts/development/init-references.py` to check out the vendored external references.
The Protocol bundle below is the tracked copy under `.concorde/protocol/`, refreshed by
`python3 scripts/concorde.py protocol-manifest --write --bind-project` after a Protocol change.
@.concorde/protocol/principles.md
