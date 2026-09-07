---
audience: ambient
---

This loop ends at a verified `ready` candidate in the current change worktree. It never
invokes deliver. Partial progress and gaps remain in `.concorde/worktree.json` and resume under
the same worktree change. Delivery is a separate request from an agent whose initial working directory is either the
source change worktree or the destination primary worktree; report the participating paths and
change_id when the candidate is ready.

The standard loop requires independent Spec review after authoring and before planning, then
read-only code review after implementation/checks and before ready. Fast-loop run_reviews defaults
to false; both mode skips are recorded explicitly. A previously required review cannot be disabled
on retry. Required review failure, incomplete coverage and blocking findings stop advancement;
advisory findings remain in the review artifacts. Each mode and target uses a separate fresh
session. Changed inputs invalidate older conclusions. Necessary contract gaps persist in the existing
change state; repair the Spec and resume with a fresh context. No-finding review is not proof of
semantic completeness.
