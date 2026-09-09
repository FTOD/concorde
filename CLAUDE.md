# Concorde Source-Checkout Agent Policy

Before any project action, read and follow `AGENTS.md` in this worktree as the canonical policy.
This checkout's `.claude/settings.json` refuses native worktree creation (`EnterWorktree`,
worktree-isolated subagents, `git worktree add`, `claude --worktree`). Worktrees for changes come
only from Concorde capabilities, followed by a P10 handoff into the new worktree's own session.

In a fresh clone, run `python3 scripts/concorde.py build` once before this import resolves.
@generated/protocol/principles.md
