---
audience: ambient
---

This loop ends at a verified `ready` candidate in the current change worktree. It never
invokes deliver. Partial progress and gaps remain in `.concorde/worktree.json` and resume under
the same worktree change. Delivery is a separate request from an agent whose initial working directory is either the
source change worktree or the destination primary worktree; report the participating paths and
change_id when the candidate is ready. Delivery creates an independent branch and removes the
candidate worktree by default. Only an explicit user request permits a separate final merge by
the primary worktree's sole writing agent; other agents must use linked worktrees.

When enabled, the loop requires independent Spec review after authoring and before planning, then
read-only code review after implementation/checks and before ready. A skipped review is recorded
explicitly rather than run. A review already required for this change cannot be disabled by a
later request. Required review failure, incomplete coverage and blocking findings stop advancement;
advisory findings remain in the review artifacts. Each mode and target uses a separate fresh
session. Changed inputs invalidate older conclusions. Necessary contract gaps persist in the existing
change state; repair the Spec and resume with a fresh context. No-finding review is not proof of
semantic completeness.
