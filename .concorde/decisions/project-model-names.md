# Decision log: project-model-names

Goal: Update worker model ids (gpt-6 -> gpt-6-astra, add gpt-6.1-sol, spec_panel reviewer3 on gpt-6.1-sol), then make the tracked worker configuration name models by install-independent project model names, resolved to each program's local model id through an untracked user-level model map

## Brief (main agent, 2026-09-30)

### The developer's request (verbatim, translated)

"My pi model config changed: gpt-6 became gpt-6-astra, and gpt-6.1-sol was added. Update the ids
in the project, then switch reviewer3's model to gpt-6.1-sol. Also: the model ids are now tracked
by Git as part of the project, but those ids are actually defined by the local pi configuration.
That is a problem. We need a model list independent of the local configuration, and a map, not
tracked by Git, from that model list to the local model ids."

The developer's pi (`~/.pi/agent/models.json`) now offers `local-openai/gpt-6-astra` and
`local-openai/gpt-6.1-sol`; `local-openai/gpt-6` no longer exists (checked with
`python3 scripts/available_models.py --backend pi`).

### Part 1 — first commit, alone

Make the first commit of the task branch change only `.concorde/workers.json`, in the current
schema: `local-openai/gpt-6` -> `local-openai/gpt-6-astra` everywhere (enabled_models, default,
spec_panel reviewer2), add `local-openai/gpt-6.1-sol` to `enabled_models`, and set
`operations.spec_panel.workers.reviewer3.model` to `local-openai/gpt-6.1-sol` (keep its
`reasoning: medium`). The main agent would normally commit this directly on main, but this
background main session is not allowed to edit the primary worktree, so it rides on this task as
its own commit. (Decision by the main agent.)

### Part 2 — the redesign (direction decided by the developer; details decided by the main agent)

1. **Project model names in the tracked file.** `.concorde/workers.json` keeps choosing every
   worker's model and reasoning level (it stays Git-tracked: the developer earlier ruled worker
   model *choices* are tracked), but `enabled_models` and every entry's `model` now hold a
   *project model name* that does not depend on any installation, such as `gpt-6-astra`,
   `gpt-6.1-sol`, `claude-opus-5-5`. Reasoning levels stay in the tracked file. Bump
   `schema_version` (rapid-iteration rule: no migration; an old file is refused with
   `config_invalid` saying how to rewrite it).
2. **An untracked, user-level model map.** A JSON file outside every repository,
   `$XDG_CONFIG_HOME/concorde/models.json` (default `~/.config/concorde/models.json`), maps each
   project model name to the local model id per program, e.g.
   `{"schema_version": 1, "models": {"gpt-6-astra": {"pi": "local-openai/gpt-6-astra"},
   "claude-opus-5-5": {"pi": "anthropic/claude-opus-5-5", "claude": "claude-opus-5-5"}}}`.
   Reason for user level rather than an untracked file in the project: it mirrors the pi and
   Claude Code configuration, which is itself per user; one file then serves the primary worktree,
   every task worktree, unbound checkouts, develop installs and test projects under /tmp without
   copying. A test or e2e harness needs a way to point at its own map (e.g. an environment
   variable naming the file) — your choice of mechanism, spec it.
3. **No fallback.** A worker whose model has no entry for its backend in the map, or a missing or
   malformed map, is refused before launch with a specific error code (e.g. `model_unmapped`,
   `model_map_invalid`) naming the project model name, the backend, the map path and the exact
   entry to add. Never use the project model name itself as the local id. Only the map file is
   read from the user's environment; nothing else about model choice comes from the developer's
   pi or Claude Code settings (standing rule).
4. **Backend switching.** Since a project model name now means the same model on either program,
   drop the rule that an entry choosing a backend starts afresh without inheriting model and level:
   fields inherit uniformly by specificity, and a model the chosen program cannot reach fails with
   the unmapped error. (Decision by the main agent; if you find a concrete reason it is wrong,
   escalate rather than keep the old rule silently.)
5. **Records.** The run record and evidence name both the project model name and the resolved local
   id and backend.
6. **Discovery.** `scripts/available_models.py` should help fill the map (e.g. show local ids and
   which project names already map to them); keep it advisory, no API calls.
7. **Everything that states the old behaviour follows**: Workers Spec (module.md, launch.md,
   scenarios, contracts), the glossary definition of `concept.worker-configuration` and, if it
   meets the glossary admission criterion (not common sense, used by a Module other than its
   owner), a new Workers-owned term for the map (suggested title "Model map"); the main-session
   guidance `prompts/main-session/skill.md` ("Worker models"), `docs/using-concorde.md`, the
   concorde-development skill paragraph on `workers.json` if it needs it, the e2e and dogfood
   scripts that write `workers.json` for test projects (they must also provide a map), tests.
8. **Concorde's own checkout.** Rewrite `.concorde/workers.json` in the new schema with project
   names `gpt-6-astra` (default, medium; reviewer2 high), `gpt-6.1-sol` (reviewer3, medium) and
   `claude-opus-5-5` (reviewer1). You cannot write `~/.config/concorde/models.json` (outside your
   boundary): put the exact content the developer's map needs in your report to the main agent,
   who writes it before merging.

### Left to the task session

Names of error codes, of the environment variable and of the map's fields; file layout of the
code; whether the map key order is model-then-backend (suggested) — record each choice here.
Escalate together only what changes a promise beyond the above.

### Process

Create what Git ignores (`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`),
format, `build --check`, `spec-validation`, relevant tests, then the full pytest suite once on the
final input; `registry --write` if a module block changes; `task-validation` and `delivery`; report
to the main agent with SendMessage, including the map content from item 8.

## Task session decisions (2026-09-30)

- **Part 1 committed alone** as 9709727b (`.concorde/workers.json` only, schema 1): gpt-6 -> gpt-6-astra, gpt-6.1-sol added, reviewer3 on gpt-6.1-sol at medium.
- **Names and codes.** Map variable `CONCORDE_MODEL_MAP` (an absolute path; a relative one is refused with `model_map_invalid`); default path `$XDG_CONFIG_HOME/concorde/models.json` when XDG_CONFIG_HOME is absolute, else `~/.config/concorde/models.json` (XDG spec ignores relative values). Map layout model-then-backend: `{"schema_version": 1, "models": {"<name>": {"pi": "<id>", "claude": "<id>"}}}`, each model at least one id, only `pi`/`claude` keys. Error codes: `model_map_missing`, `model_map_invalid`, `model_unmapped` (reason `environment` in the Operation's link, since the map is the machine's). Reason: a missing map and a malformed one need different repairs, so two codes, mirroring `config_missing`/`config_invalid`.
- **Project model name syntax** is `[A-Za-z0-9][A-Za-z0-9._-]*`, checked on `enabled_models` keys (entries must name enabled models) and on map keys. Reason: it keeps a program's own id such as `local-openai/gpt-6` from standing in for a project name, so a schema-1 file whose version is merely bumped is refused rather than silently mapped. Schema 1 is refused with `config_invalid` saying how to rename, bump and map.
- **Records.** Tracing's node metadata keep `model` = the project model name (Tracing's "as configured" meaning, no Tracing change); the local id and the map path go into Workers' own worker-run-trace content, `local_model` and `model_map` (contract.workers.worker-run-trace version 3). `WorkerRequest.model` is the project name (recorded only), the new `local_model` is what `--model` receives; backends pass nothing when `local_model` is unset (only direct test callers do that).
- **Outside the task's Modules, required by brief item 5 and item 7:** `src/concorde/execution/context.py` (module.execution: passes `local_model`/`model_map` to Workers, extends the `worker-model` evidence detail to "model <name> as <local id> (model map <path>)", and for map errors offers the map repair instead of the file repair); `specs/concorde/execution/operations/workers.md` and `scenarios.md` (module.operations: evidence and error-table text); `tests/concorde/execution/test_runner.py` and `tests/concorde/spec_review/test_panel.py` (schema 2 fixtures). Decided myself: the evidence lives in Execution's code and Operations' Spec, so item 5 cannot be met inside the listed Modules; the changes add no promise beyond the brief.
- **Backend switching** (item 4) implemented as briefed: fields inherit uniformly. Found no reason against it; one consequence: a pi-only level (`off`, `minimal`) inherited by a worker switched to Claude Code is now refused with `config_invalid` where the old reset avoided it — the refusal names the entry, so kept.
- **Tests never read the developer's map:** `tests/__init__.py` sets `CONCORDE_MODEL_MAP` to the new tracked `tests/concorde/support/models.json` (bound to module.concorde's development environment); map tests pass their own environment.
- **e2e/dogfood:** the test projects' sessions inherit the developer's environment, so the user-level map serves them (brief item 2's reason); `--worker-model` now takes a project model name, and `prepare`/`dogfood prepare` refuse up front (`model_unmapped`, `model_map_missing`, …) a configuration the map cannot resolve for every worker of every Operation, through the new `models.check_mapped`. No per-test-project map is written.
- **Discovery:** each candidate lists `project_models` (map names mapping to it on that backend); `model_map` reports the map path, its refusal (never raised) and, for pi's complete listing, `unlisted` map ids pi does not list.
- **Glossary:** added `concept.model-map` (Workers); "project model name" explained in the worker configuration's definition and Workers' Spec rather than as its own term.
- **Also removed** from Distribution's module.md the stale sentence "Worker configuration defaults to a human terminal editor…" (the editor was removed earlier); added `req.concorde.worker-models-install-independent` and `req.main-session.model-map-developers`.
- **Verification:** full pytest 788 passed, 4 skipped; build --check, spec-validation clean; task-validation ready (24 checks passed); delivered as afba03e5.
- **Open for the main agent:** before merging, write the developer's `~/.config/concorde/models.json` (content in the report); until it exists every worker of the primary worktree fails with `model_map_missing`.

## Closed: merged, 2026-09-29T20:31:12Z
