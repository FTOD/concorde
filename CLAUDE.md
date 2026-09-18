# Concorde Source-Checkout Agent Policy

Before any project action, read and follow `AGENTS.md` in this worktree as the canonical policy.
Developing this checkout is direct developer-authorized maintenance in the current worktree; a
Concorde graph (`concorde-dev-loop`, `concorde-specify-loop`, `concorde-main`, `concorde-review`,
`concorde-issues` or a lifecycle Skill) runs on this checkout only when the user
explicitly asks for it, never because a task looks like a development change. A further worktree
exists only when an explicitly requested graph creates it: the host runs the graph in that
candidate worktree and returns its result here, and this session never moves.

In a fresh clone, run `python3 scripts/concorde.py build` once so the Concorde Skills exist, then
`python3 scripts/development/init-references.py` to check out the vendored external references.
The Protocol bundle below is the tracked copy under `.concorde/protocol/`, refreshed by
`python3 scripts/concorde.py protocol-manifest --write --bind-project` after a Protocol change.
@.concorde/protocol/principles.md
