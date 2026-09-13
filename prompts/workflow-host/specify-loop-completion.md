---
audience: ambient
---

This loop authors or revises the selected Module's owned Spec documents, then independently reviews
the complete contract and every affected consumer in separate fresh contexts. It returns `completed`
with artifact references after the selected Spec stages succeed. Explicit review skips remain
visible; completion never claims semantic completeness or implementation readiness.

Blocking findings, incomplete coverage and necessary contract gaps stop advancement. Preserve the
candidate, repair the missing contract and resume with fresh context. Accepted authoring and current
review evidence are retained for the same task. This loop does not plan, author implementation tasks,
write code, run code checks, mark ready or deliver. To continue implementation, invoke
`concorde-dev-loop` in the same change with the same task and constraints; it composes this loop and
then proceeds through planning, tasks, implementation, checks and code review.
