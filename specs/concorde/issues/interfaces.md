# Issue interface

`concorde-issues-request@1` uses the common invocation envelope and accepts `action` plus optional
`target_id`, `task`, `focus_id`, `constraints`, `change_id`, `issue_id`, `report`, `expected_revision`
and `note`. Actions are `list`, `show`, `report`, `reopen` and `solve`. Unknown fields fail typed
admission. A report field is accepted only by report. A supplied revision must match current bytes. A solve
note supplies explicit developer clarification; a changed clarification restarts the bounded
attempt without silently changing a previously bound development intent.

| Action | Required input | Effect |
| --- | --- | --- |
| list | action | Return current branch records, optionally filtered by target; do not create state. |
| show | issue_id | Return one record without mutation. |
| report | target_id, report | Persist a classified observation through the same scoped host service used by workers; no development candidate is required. |
| reopen | issue_id, note | Reopen a closed Issue with an explicit rationale while retaining history. |
| solve | issue_id | Bind the current record and owning Module, then run the bounded solving lifecycle. |

An append uses `issue_id` and `expected_revision` inside the report. An explicit developer report
may cite an existing non-symlink file under the legacy archive as evidence; ordinary workers gain
no archive read grant from that exception. Reporting includes the known
contract owner or null without replacing the reporting Module. `show`, `reopen` and `solve` resolve
the latest known owner, or the original reporting scope when unknown; a supplied foreign target
cannot transfer ownership or widen a grant. The result is `concorde-issues-response@1`, the common
response with `issues` (complete version-1 records) and nullable `decision`. The common response
carries `blockers`, references to immutable Issue reports with a task-local `blocked_step`.
The response is metadata/evidence, not an instruction to execute another operation.

The worker `report_issue` tool admits `concorde-issue-report@1` and returns `{receipt, revision}`,
where receipt follows `concorde-issue-receipt@1`. [Record semantics](issues.md#store-boundary) define
these values once. Worker final results carry only references to reports accepted in that invocation
or explicitly admitted as stage input. A forged, missing, foreign or repeated reference is rejected.
Review findings are references with `severity` and `affected_task`; the host derives blocking
relations from those judgments, with no second question/contract text to copy verbatim.

The legacy `concorde-reflections-triage` capability and queue helper are retired, not aliases for
Issue solving. `scripts/issues.py archive-reflections` explicitly moves an old queue into
`.concorde/archive/reflections/` without reclassification or disposition. A destination collision,
symlink or unsafe source is refused without deleting either copy. Installation preserves legacy
user data but does not install an active Reflection queue. The archive is outside active validation
and normal worker grants; continued work requires an explicit new Issue citing the old evidence.

## Scenarios

### scenario.issues.inspect — Inspect without starting work

- GIVEN an initialized project, with or without Issue records
- WHEN list or show is requested
- THEN the current records are returned without a model invocation, candidate creation or issue mutation

### scenario.issues.reference — Admit only observed or granted Issue references

- GIVEN a bounded worker with reporting authority and optional admitted repair feedback
- WHEN it submits task blockers or review judgments
- THEN every reference resolves to an observation it reported or was explicitly granted
- AND missing, foreign and fabricated references fail admission without removing saved reports

### scenario.issues.blocker-history — Track dependencies without task-text identity

- GIVEN a candidate with an Issue blocking a Module phase
- WHEN the same work is replanned and a fresh successful assessment releases that dependency
- THEN its stable Issue relation remains in history without depending on old task wording
- AND the Issue itself remains open unless separately disposed with evidence
- AND another Module's blocker is absent from the worker's bounded workspace context

### scenario.issues.archive — Preserve legacy history explicitly

- GIVEN legacy Reflection data and no archive destination
- WHEN the developer explicitly requests archival
- THEN the complete directory is moved without altering its records or relative evidence links
- AND no active Issue is created or marked resolved
- AND conflicting destinations and symlinks are refused without discarding data
