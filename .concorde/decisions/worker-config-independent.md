# Decision log: worker-config-independent

Goal: Worker configuration is independent of the developer's own pi settings: models, reasoning levels and a required enabled-models list come only from .concorde/workers.json, and any unresolved or unlisted model is refused

## Brief (main agent `claude session stuck debug`, 2026-09-29)

Background: `pi-worker-default-model` (merged 435784ba) made a pi worker with no configured model
inherit `defaultProvider`, `defaultModel` and `defaultThinkingLevel` from the developer's
`~/.pi/agent/settings.json` (`user_defaults()` in `src/concorde/harness/pi_backend.py`). The main
agent had decided that without the developer. The developer rejected it: **the configuration of
Concorde's workers must be completely independent of the developer's system pi configuration.**
This task reverses that inheritance and adds the rules below.

Developer's decisions (2026-09-29), which this task carries out and does not revisit:
1. **Independent.** No worker's model, reasoning level or model list is read from the developer's
   pi settings (`settings.json`: `defaultProvider`, `defaultModel`, `defaultThinkingLevel`,
   `modelThinkingLevels`, `enabledModels`, …). Remove `user_defaults()` and its
   `pi_settings_invalid` error, scenarios and requirement (`req.workers.pi-user-default`), and
   state the independence in the Workers Spec. The worker's generated pi `settings.json` holds only
   what Concorde itself decides (e.g. `defaultProjectTrust: "never"`).
2. **Credentials and provider definitions still come from the developer's system pi**: `auth.json`
   and `models.json` are copied as before (they say how to reach a model, not which model to use,
   and credentials cannot be tracked). Keep that, and say so in the Spec.
3. **No model resolved → error.** A worker whose configuration resolves no model (no `default`
   model, no Operation or worker entry naming one) is refused before launch with a detailed error
   saying which worker and how to fix `workers.json`. Neither pi's built-in default nor the
   developer's pi default is used.
4. **Enabled models, required, for all workers.** `workers.json` gains a required list of enabled
   models that applies to every worker on both backends (pi and Claude Code). A missing list, a
   `default` model not in it, or any model chosen for an Operation or worker not in it, is an error
   (the whole file is validated at launch as today, `config_invalid` naming the field, or a more
   specific code if you judge it clearer — detailed either way).
5. **Per-model reasoning levels in `workers.json` itself.** A table in `workers.json` gives a
   reasoning level per model; a worker whose resolved entry names a model but no `reasoning` takes
   that model's level from the table. An explicit `reasoning` in the most specific entry wins. The
   developer's pi `modelThinkingLevels` is never read.
6. **This checkout's `.concorde/workers.json`:** default model `local-openai/gpt-6` at reasoning
   `medium` (backend pi); enabled models at least `local-openai/gpt-6` and
   `anthropic/claude-opus-5-5` (both used by `spec_panel` now). Keep the existing `spec_panel`
   entries and `runtime` list.

Main agent's decisions (without the developer, ordinary scope):
- With no reasoning from any entry and no per-model level, the worker uses its program's built-in
  default level (not the developer's setting) — i.e. no `--thinking`/effort flag is passed.
- The main-session guidance (`prompts/main-session/skill.md`, "Worker models", and anything in
  `claude-md.md`) must describe the new rules: `workers.json` is required before any worker runs,
  its default and enabled list, and the per-model levels; replace "Without a file, every worker
  runs on pi with pi's default model". The installer still installs no `workers.json` (it is the
  project's to write); the guidance tells the main agent to write it.
- Test projects prepared by the e2e tool (module.e2e) must get a valid `workers.json` so their
  Operations still run; choose the models from what the e2e tool already configures or accepts,
  with a CLI option if one is needed.

Left to the session: field names and shapes (follow the existing `workers.json` style), whether
enabled-model entries are exact ids or patterns (prefer exact ids unless there is a reason),
error codes and wording, test placement. If another Module turns out to need a change (e.g. the
distribution installer or dogfood scenarios), escalate rather than change it.

Verification: deterministic tests for every rule above; full suite; a live bound `run understand`
in your task worktree that ends ok with this checkout's new `workers.json` (worker model spend is
approved). Record decisions and non-ok results here, deliver and report.

## Task session (Claude Code), 2026-09-29

Decisions taken without the developer, within the brief's "left to the session":

- **Shape of the enabled models and per-model levels: one object.** `enabled_models` is a required
  object keyed by exact model id, each value `{}` or `{"reasoning": "<level>"}`. It is both the
  enabled list (decision 4) and the per-model level table (decision 5), so a level can never be
  given for a model that is not enabled. Exact ids, no patterns: the brief preferred them and
  nothing needed patterns. An empty object is refused like a missing one.
- **Level resolution order.** The level is the one set by the entry that chose the model or a
  more specific entry; otherwise the model's own level in `enabled_models`; otherwise a level a
  less specific entry sets; otherwise none (no `--thinking`/`--effort`, the program's built-in
  default, per the main agent's decision). This satisfies decision 5 ("an explicit reasoning in the
  most specific entry wins"; a worker whose resolved entry names a model but no reasoning takes the
  model's level) and keeps today's inheritance when the model has no level of its own. A model's
  own level is validated against the backend of every configured scope that takes it.
- **Error codes.** `config_missing` (no `.concorde/workers.json`; previously a missing file meant
  "run on defaults"), `model_unresolved` (no entry names a model for the worker, naming the
  worker and the entries its model may come from), `model_not_enabled` (an entry names a model
  outside `enabled_models`, naming the entry path, the model and the enabled list),
  `config_invalid` for a missing or empty `enabled_models` and malformed entries. All reach the
  Operation as causes of `worker_model_unavailable` through the existing `HANDLING` table.
- **Removed** `user_defaults()`, `DEFAULT_FIELDS` and `pi_settings_invalid` from
  `src/concorde/harness/pi_backend.py`, `req.workers.pi-user-default`, and the scenarios
  `scenario.workers.pi-user-default` and `scenario.workers.pi-settings-invalid` (a malformed user
  settings file no longer matters, since it is never read). Added
  `req.workers.pi-settings-independent`, `req.workers.configured-model` and the scenarios
  `pi-settings-independent`, `model-levels`, `model-unresolved`, `model-not-enabled` and
  `config-missing`; updated `backend-configured`, `backend-default`, `model-refused` and
  `limits-configured`. The glossary definition of Worker configuration now says the file is
  required and the only source of a worker's model and level, with the enabled models.
- **This checkout's `.concorde/workers.json`**: `enabled_models` `local-openai/gpt-6` and
  `anthropic/claude-opus-5-5` (no own levels), `default` `{backend: pi, model: local-openai/gpt-6,
  reasoning: medium}`; the `spec_panel` entries and `runtime` list are unchanged. The level is on the
  default rather than in the table so that `spec_panel`'s `reviewer1` (opus, no level) keeps
  `medium` too.
- Test fixtures that run fake workers (`tests/concorde/support/operation_project.py`,
  `test_runner.py`, `test_panel.py`) now write an `enabled_models` and a model.
- Not changed, outside the task's Modules: the Operations Spec (`specs/concorde/execution/
  operations/`) and `src/concorde/execution/context.py`, whose `worker_model_unavailable` link and
  options already cover the new causes generically ("correct <file> as the error says and commit
  it").

- **Non-ok result:** live `run understand` `r-20260929T122018-understand-ab587245` ended `failed`
  with `audit_violation`: the write audit attributed to the worker six main-session files that I
  (the task session) edited in the task worktree while the run was going. The worker itself
  reported ok and its run record shows it launched on pi with `local-openai/gpt-6` at `medium`
  (`worker-model` evidence: "backend from default"), so the new configuration worked. My error:
  I will not edit the worktree while a bound run is going, and I rerun the live check at the end.

## Escalated to the main agent, 2026-09-29T12:25:39Z

- **task-session** task session (task worker-config-independent): `docs_stale_worker_configuration`
  docs/using-concorde.md, section 'Choose the worker models' (bound to the root Module module.concorde, outside this task's Modules), now describes the old rules: its example workers.json has no enabled_models and would be refused (config_invalid), and it does not say that the file is required before any worker runs (config_missing), that every model an entry names must be enabled (model_not_enabled), that a worker without a model is refused (model_unresolved), that a model may carry its own level in enabled_models, or that nothing is read from the developer's own pi/Claude Code settings besides auth.json and models.json (its last paragraph is still true). The Workers Spec and the main-session guidance of this task already state the new rules, so the change is a documentation update of about one paragraph plus the example.
  Not handled here (decision): the file belongs to module.concorde, which is not among this task's Modules (module.workers, module.main-session, module.e2e); the brief says to escalate rather than change another Module
  Options: add module.concorde to this task and let the task session update the section before delivery (or in a second delivery); open a small follow-up task for module.concorde to update docs/using-concorde.md; leave the user docs stale for now
  Recommendation: open a small follow-up task for module.concorde (or approve it as a small change in the primary worktree after this merge): the docs example would fail as written, so it should not stay stale long

```json
{
  "level": "task-session",
  "actor": "task session (task worker-config-independent)",
  "code": "docs_stale_worker_configuration",
  "detail": "docs/using-concorde.md, section 'Choose the worker models' (bound to the root Module module.concorde, outside this task's Modules), now describes the old rules: its example workers.json has no enabled_models and would be refused (config_invalid), and it does not say that the file is required before any worker runs (config_missing), that every model an entry names must be enabled (model_not_enabled), that a worker without a model is refused (model_unresolved), that a model may carry its own level in enabled_models, or that nothing is read from the developer's own pi/Claude Code settings besides auth.json and models.json (its last paragraph is still true). The Workers Spec and the main-session guidance of this task already state the new rules, so the change is a documentation update of about one paragraph plus the example.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the file belongs to module.concorde, which is not among this task's Modules (module.workers, module.main-session, module.e2e); the brief says to escalate rather than change another Module"
  },
  "options": [
    "add module.concorde to this task and let the task session update the section before delivery (or in a second delivery)",
    "open a small follow-up task for module.concorde to update docs/using-concorde.md",
    "leave the user docs stale for now"
  ],
  "recommendation": "open a small follow-up task for module.concorde (or approve it as a small change in the primary worktree after this merge): the docs example would fail as written, so it should not stay stale long",
  "causes": []
}
```

## Escalated to the main agent, 2026-09-29T12:25:48Z

- **task-session** task session (task worker-config-independent): `dogfood_prepare_no_worker_configuration`
  scripts/e2e/dogfood.py prepare (module.dogfood-scenarios, outside this task's Modules) clones this checkout, makes a develop install into a SWE-bench project, runs init and commits, but writes no .concorde/workers.json. Since this task, no worker runs without that file, so any Operation a dogfood session starts in the project fails with worker_model_unavailable caused by config_missing, which a scenario would then misread as the injected fault or as a new defect. The fix is one call before the project's 'Adopt Concorde (develop install)' commit, reusing module.e2e's new e2e.worker_configuration() (this checkout's enabled models, defaults, Operation entries and limits, or one --worker-model), plus a line in the dogfood Spec. I have not checked which of the scenarios' sessions actually launch workers (write-hook-rw-directories concerns the write hook, which a task session exercises without workers).
  Not handled here (decision): dogfood.py belongs to module.dogfood-scenarios, which is not among this task's Modules; the brief says to escalate rather than change another Module
  Options: add module.dogfood-scenarios to this task and let the task session make the one-call change with a test; open a follow-up task for module.dogfood-scenarios; leave it until a dogfood scenario needs workers
  Recommendation: open a follow-up task for module.dogfood-scenarios together with the docs update, or add it to this task if you prefer one merge

```json
{
  "level": "task-session",
  "actor": "task session (task worker-config-independent)",
  "code": "dogfood_prepare_no_worker_configuration",
  "detail": "scripts/e2e/dogfood.py prepare (module.dogfood-scenarios, outside this task's Modules) clones this checkout, makes a develop install into a SWE-bench project, runs init and commits, but writes no .concorde/workers.json. Since this task, no worker runs without that file, so any Operation a dogfood session starts in the project fails with worker_model_unavailable caused by config_missing, which a scenario would then misread as the injected fault or as a new defect. The fix is one call before the project's 'Adopt Concorde (develop install)' commit, reusing module.e2e's new e2e.worker_configuration() (this checkout's enabled models, defaults, Operation entries and limits, or one --worker-model), plus a line in the dogfood Spec. I have not checked which of the scenarios' sessions actually launch workers (write-hook-rw-directories concerns the write hook, which a task session exercises without workers).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "dogfood.py belongs to module.dogfood-scenarios, which is not among this task's Modules; the brief says to escalate rather than change another Module"
  },
  "options": [
    "add module.dogfood-scenarios to this task and let the task session make the one-call change with a test",
    "open a follow-up task for module.dogfood-scenarios",
    "leave it until a dogfood scenario needs workers"
  ],
  "recommendation": "open a follow-up task for module.dogfood-scenarios together with the docs update, or add it to this task if you prefer one merge",
  "causes": []
}
```

- Live check: `run understand` `r-20260929T122513-understand-161119e7` ended `ok`, worker on pi with `local-openai/gpt-6` at `medium` (backend from default). Full suite: 808 passed, 4 skipped.

- Delivered: `task-validation` ready; `delivery` ok, commit d86f8856be2d with .concorde/evidence/worker-config-independent/1.json. Escalations 1 (stale docs/using-concorde.md, module.concorde) and 2 (dogfood prepare writes no workers.json, module.dogfood-scenarios) are open for the main agent.

## Closed: merged, 2026-09-29T12:39:23Z
