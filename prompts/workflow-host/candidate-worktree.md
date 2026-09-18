---
audience: ambient
---

A mutating request from the primary worktree runs in a candidate worktree the host creates from
the committed base; this session stays where it is and receives that candidate's result, whose
workspace names the candidate's path, branch and change_id. Continue the same change from here
with that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps
or blocked execution as returned; do not work around the boundary. Non-implementation agents never
receive implementation code or raw test logs.
