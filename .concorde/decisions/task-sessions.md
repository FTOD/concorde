# Decision log: task-sessions

Goal: Run each task inside its own worktree with that worktree's Concorde code: task worktrees under .claude/worktrees/<task>, a session enters one task at a time, and the main session may start sandboxed task sessions (claude --bg) for complex multi-task work; they edit directly, decide inside their task and escalate the rest
