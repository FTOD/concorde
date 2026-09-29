# Decision log: worker-config-followups

Goal: The user document and dogfood scenario preparation follow the required worker configuration: docs/using-concorde.md describes workers.json with enabled_models, and dogfood prepare writes a valid workers.json

## Brief (main agent `claude session stuck debug`, 2026-09-29)

Origin: task `worker-config-independent` (merged 7ae70d2b; decision log in
`.concorde/history/worker-config-independent/decisions.md`) made `.concorde/workers.json` required,
with a required `enabled_models` object (exact model ids, each `{}` or `{"reasoning": level}`),
and refusals `config_missing`, `model_not_enabled`, `model_unresolved` under
`worker_model_unavailable`. Worker configuration is independent of the developer's own pi
settings (only pi's `auth.json` and `models.json` are copied). Its session escalated two
out-of-scope follow-ups; the main agent answers both by this task (decision without the
developer, ordinary scope: both only bring other Modules in line with the merged change):

1. `docs_stale_worker_configuration`: `docs/using-concorde.md`, section "Choose the worker
   models" (module.concorde), shows a `workers.json` without `enabled_models`, which would be
   refused, and does not say the file is required, explain the refusals or the per-model levels.
   Bring it in line with the Workers Spec and the main-session skill's "Worker models" section.
   Format with Prettier as the development skill says.
2. `dogfood_prepare_no_worker_configuration`: `scripts/e2e/dogfood.py prepare`
   (module.dogfood-scenarios) writes no `workers.json`, so a worker a dogfood session starts fails
   with `config_missing`. Call `e2e.worker_configuration()` (added in `scripts/e2e/e2e.py`) before
   its adopt commit, as `e2e.py prepare` does, with the same `--worker-model` option if that fits,
   and state it in the dogfood Spec with a scenario and a test.

Left to the session: wording, test placement. Verify with the relevant tests, build --check and
spec-validation, deliver and report.

## Task session decisions (2026-09-29)

- **The configuration is passed in, not computed in `dogfood.py`.** `worker_configuration()` lives
  in `scripts/e2e/e2e.py`, which imports `dogfood.py`; importing `e2e` back would be circular. So
  `dogfood.prepare` takes the configuration as a required `workers` argument and writes it as
  `.concorde/workers.json` before its adopt commit, and `e2e.py`'s `dogfood prepare` computes it
  with `worker_configuration(--worker-model)` first, failing before anything is cloned, as
  `e2e.py prepare` does. This touches `scripts/e2e/e2e.py` (module.e2e, not a task Module) in
  its `dogfood` call site, its usage docstring and one new `--worker-model` option of
  `dogfood prepare`; the brief asks for exactly that call and option, so I took it as within the
  task rather than escalating. module.e2e's Spec is unchanged: the option is described in the
  dogfood Spec's usage, which is where `dogfood prepare` is documented.
- `dogfood.json` records `worker_models` (the enabled models), like `e2e.py prepare`'s result.
- Dogfood Spec: the sentence saying the preparation writes no worker configuration is replaced;
  the preparation paragraph says what it writes and why (`config_missing` otherwise), and the new
  `scenario.dogfood-scenarios.worker-configuration` is verified by
  `test_the_project_gets_a_worker_configuration_before_its_adopt_commit` in
  `tests/concorde/e2e/test_dogfood.py`.
- User document: "Choose the worker models" rewritten to say the file is required and not written
  by the installer or init, to explain `enabled_models` with per-model levels and the level
  precedence, with the Workers Spec's example, and to list the refusals under
  `worker_model_unavailable` (`config_missing`, `model_not_enabled`, `model_unresolved`,
  `config_invalid`, `backend_missing`). The install section also says the installer does not write
  the file and links there. Formatted with `npx prettier@3` (docsite has no Prettier binary);
  Python formatted with ruff (`UV_TOOL_DIR` in `$TMPDIR`, since the sandbox keeps uv's tool dir
  read-only).
- Verified: tests/concorde/e2e (dogfood, e2e), full suite (809 passed, 4 skipped), build --check,
  spec-validation (no findings), task-validation ready (it counts module.e2e among the changed
  Modules, no blocking findings). Delivered as 5606610c on concorde/worker-config-followups.

## Closed: merged, 2026-09-29T12:47:34Z
