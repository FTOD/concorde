# Reflection triage

Protocol: `reflection-triage/v3`.

You are the parent orchestrator in the maintainer's checkout. Shared configuration is
`.concorde/reflections/config.json`; plans are under `.concorde/reflections/plans/`; worktrees are
under `.concorde/reflections/worktrees/`. Use the installed deterministic helper at
`.concorde/framework/scripts/reflections_queue.py`; in a Concorde source checkout use
`scripts/reflections_queue.py`. Never edit reflection `Status` or `Note`. Before appending any
genuine new reflection, run the helper with `--allocate-id`, use only
its `allocated_id`, and never derive an ID from the remaining entries. `.concorde/reflections/log.md`
is the sole persisted reflection record. Plans may key coordination by `R-NNN` but must not copy
entry fields, status, notes, occurrences, or prose.

## Actions

- `status`: run the helper with `--json`, report the ordered open queue and plan counts, and stop
  without mutation. Empty input means `status`.
- `investigate` `[N | R-NNN ...]`: select unplanned open entries, dispatch at most configured
  investigator concurrency with exactly one entry per reflection-investigator, wait for the entire
  wave, validate and persist each returned plan in the parent checkout, retry missing output once,
  and report every result.
- `implement`: read plans through the helper; select only ready `fast-loop` routes; reject overlap
  with maintainer changes; group by `implement_in`; create one explicit Git worktree/branch per
  group; dispatch at most configured implementer concurrency with the absolute worktree path and full
  plan text; wait for all results; and update only plan evidence/status through the helper.
- `merge`: require a clean tracked checkout; merge implemented branches one at a time; abort and
  stop on conflict; run the plans' repository/documentation validation; remove only successfully
  merged worktrees/branches; set only their plan status to `merged`; then invoke `--remove-merged`
  for each validated `fast-loop` plan whose effort is `small`. This exact removal occurs without a
  maintainer Status/Note. If removal fails, preserve the log and report the retryable error. Plans
  with another route or effort retain maintainer disposition and receive suggested status/note changes.

## Routes and plan lifecycle

Investigation chooses exactly one route: `fast-loop`, `specify`, `dismiss`, or `blocked`.
Only `fast-loop` is implementation eligible. Plan statuses are `proposed`, `approved`, `hold`,
`rejected`, `implemented`, `ineligible`, `failed`, and `merged`.

Automatic log removal is restricted to a matching open entry whose plan is `fast-loop`, `small`,
and `merged` with a commit reachable from `HEAD`. `specify`, `dismiss`, `blocked`, non-small,
unmerged, ineligible, and failed plans retain maintainer disposition.

The parent is the only plan-file writer. Never run parallel implementers in the main checkout and
never maintain a second Claude- or Codex-specific queue.
