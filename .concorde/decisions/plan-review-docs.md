# Decision log: plan-review-docs

Goal: List the optional plan_review Operation in docs/README.md and docs/using-concorde.md, matching how the other Operations are described there

## Brief (main agent, 2026-09-30)

The developer asked to add the `plan_review` Operation, merged in task `plan-review` (merge
251f0d69), to the user documents `docs/README.md` and `docs/using-concorde.md`, which still omit
it. Describe it as the Specs now state it (Understanding's `module.md`, the Operations catalog, the
main-session guidance): optional, bound-only, `concorde run plan_review --plan <file> [--input
<run>] [--accept <F> "<how>"]… [--reject <F> "<why>"]…`, one read-only `reviewer` worker whose
model comes from `.concorde/workers.json`, iterations led by the task session until the verdict is
`accepted`, and that the plan file is deleted before `task-validation`. Match the style and depth
the documents give the other Operations; change nothing else. Format Markdown under `docs/` with
Prettier. Documentation only: no Spec meaning or code change; escalate if one seems needed.

## Task session (2026-09-30)

- `docs/README.md`: `plan_review` added to step 2 of "One task from idea to merge" as optional, and
  a row in the Operation table after `understand`. The row leaves out "needs a task" so the table
  keeps its width; the unbound list below step 4 already omits `plan_review`.
- `docs/using-concorde.md`: a `plan_review --plan plan.md --input <plan-run-id>` line in the
  example commands, a table row, a paragraph after the review-memory paragraph (optional, plan
  written by the task session, one read-only `reviewer` whose model comes from
  `.concorde/workers.json`, iterations with `--input`/`--accept`/`--reject` until `accepted`,
  maintained disagreements to the main agent, plan file deleted before `task-validation`, never
  unbound), and `plan_review` in the "typical task" sentence. "Operations outside a task" left
  unchanged, since `plan_review` does not belong to that list.
- No Spec or code change was needed. Prettier check, `build --check` and `spec-validation` pass.
- `task-validation` `r-20260930T102329-task_validation-6d3577a7` failed with `checks_unavailable`
  / `check_sandbox_unavailable` (check.concorde.tests): the worktree had no `.venv`. Ran
  `uv sync --locked --group dev`; `task-validation` `r-20260930T102359-task_validation-cf4c6e34`
  ready, check.concorde.tests passed.
- `delivery` `r-20260930T102435-delivery-84328c0c` ok: delivery commit `1849465c` on
  `concorde/plan-review-docs`.
- Report to the main agent not sent: SendMessage to `concorde-d1` failed with "No agent named
  'concorde-d1' is reachable", and ListAgents does not list that session, so the report stays in
  this log and in the session's final output.

## Closed: merged, 2026-09-30T11:41:55Z
