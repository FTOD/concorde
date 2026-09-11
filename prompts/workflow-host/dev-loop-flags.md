---
audience: ambient
---

Optional `specify` (default true) and `run_reviews` (default true) flags select the loop shape.
`specify:false` skips Spec authoring for this pass, exactly like the former fast loop.
`run_reviews:false` records an explicit skip for each review mode instead of running it. A review
requirement already recorded for this change cannot be disabled by a later `run_reviews:false`;
every skip and every required review remains visible in the change record.

To repair an existing incomplete task list that incorrectly requires later Host validation,
review or commit before implementation can finish, pass `repair_task_scope:{tasks_digest:...}`.
The digest is `sha256:` plus SHA-256 of the UTF-8 canonical JSON task list (sorted keys, compact
separators, ASCII escaping as in Python `json.dumps`). The Host binds that exact list, supplies only semantic phase
feedback and the admitted plan/tasks to a fresh task author, preserves history and then runs
implementation, validation and required reviews normally. It preserves software acceptance and
does not edit the plan, complete tasks, grant permissions or skip checks. Replaying a consumed
digest resumes the replacement list; stale digests and unresolved gaps are rejected.
