---
audience: worker
---

A missing necessary contract, conflicting Specs or an implementation/Spec mismatch is an Issue of
type gap. Use `report_issue` with the matching subtype, concrete observation, impact and evidence.
Do not infer missing obligations from implementation or read outside the admitted context.

Reporting is independent of task control. If an Issue blocks your current stage, put its returned
receipt fields (`issue_id`, `report_id`, `path`) plus `blocked_step` in `blockers`. Do not repeat the
problem text as a second gap object. Nonblocking reports need no blocker. A completed or sufficient
stage has no blockers; a missing necessary contract uses spec_incomplete, a conflicting obligation
can use conflicting, and execution failure remains failed. Continue independent work when possible.

Reviewers instead return `issues`: receipt fields plus `severity` and `affected_task`. There is no
separate review gaps/blockers array and no free-text pairing rule. Collect every independently
assessable finding, then submit the review's actual coverage and completion status. A blocked
judgment does not require abandoning the rest of the review.

References must be receipts from this invocation or explicitly admitted Issue context. Never invent
IDs, borrow another worker's unseen record or relabel a provider's definition as consumer-owned.
A selected provider remains the sole owner of its definitions; report unknown ownership as null.
A repair requires fresh evidence before resuming the affected step. Releasing a task dependency or using a
workaround does not itself resolve the underlying Issue.
