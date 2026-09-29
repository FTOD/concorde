# Decision log: delivery-requirement-wording

Goal: Correct req.concorde.delivery-separate: the task level may commit verified steps on the task branch, and only the delivery commit that marks the work delivered is the delivery command's

## Brief (main agent, 2026-09-30)

Found by task `evidence-leftovers`; the developer asked to fix it.
`specs/concorde/requirements.md`, `req.concorde.delivery-separate` says: "Changes of a task SHALL
reach the task branch only through the `delivery` execution command, which decides their readiness
itself and commits them only when the workspace is ready." That contradicts Delivery's own Spec
(`specs/concorde/execution/commands/delivery/`, see `concept.delivery-commit`) and the working
method: the task level (task session) commits verified steps on the task branch itself, and only
the commit that marks the work delivered (subject `concorde: deliver <workspace>`) is Delivery's;
Delivery also accepts an already clean, committed workspace. Reword the requirement to state what
is true — e.g. that a task counts as delivered only through a delivery commit made by the
`delivery` command after it decided the whole workspace ready — keeping its identity. Check the
root's scenarios and entry, and the acceptance tests under `tests/concorde/acceptance/` that verify
it, for the same overstatement and fix them within module.concorde; report anything elsewhere.
Delivery's Spec is authoritative; do not change it. Stop every background command you started
before task-validation and delivery.

## Task session (2026-09-30)

- Reworded `req.concorde.delivery-separate` (identity and title kept): a task counts as delivered
  only through a delivery commit, which only `delivery` makes after deciding in the same run that
  the whole workspace is ready; the task level may commit verified steps, which deliver nothing.
  Wording follows Delivery's Spec, which was not changed.
- Same overstatement fixed in two more places of module.concorde: the explanation under
  `req.concorde.workers-no-git` ("Git belongs to the deterministic code around the workers ...
  `delivery` commits") now names the task level's step commits and `delivery`'s delivery commit;
  the root entry's "The life of a task" now says the task session may commit each verified step and
  that the delivery commit alone marks the task delivered. The d2 diagram there was left as is
  (its "Delivery commit" box is still accurate).
- Checked `specs/concorde/scenarios.md` (`scenario.concorde.task-to-merge` expects one delivery
  commit after an `implement` run that leaves its change uncommitted: accurate) and
  `tests/concorde/acceptance/test_flows.py` (asserts the head is a `concorde: deliver t1` commit:
  accurate). No change needed; no test verifies a requirement.
- Outside module.concorde, not changed, reported to the main agent: `prompts/main-session/skill.md:94`
  and `prompts/main-session/task-session.md:32` say `delivery` "commits the result on the task
  branch", the same loose phrasing the root entry had (not wrong, since the task-session prompt
  also says to commit verified steps, but it could name the delivery commit).
- task-validation: ok, ready, no blocking findings, check.concorde.tests passed. delivery: ok, delivery commit ba09a325.

## Closed: merged, 2026-09-29T19:04:38Z
