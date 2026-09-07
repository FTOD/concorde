---
audience: ambient
---

When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns a handoff. Open a new agent in the returned worktree before continuing;
never carry this conversation or its worktree-owned Skills across that boundary. Report Spec gaps
or blocked execution as returned; do not work around the boundary. Non-implementation agents never
receive implementation code or raw test logs.
