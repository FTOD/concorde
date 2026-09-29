# Decision log: project-config

Goal: Hard-code the registry path .concorde/specs.json and drop the registry field of .concorde/config.json; replace the untracked .concorde/worker-models.json and the workers section of .concorde/config.json with one Git-tracked .concorde/workers.json (backend, model and reasoning per worker, the worker limits and runtime paths); remove the configure-workers command and the pi model picker; a models-only change may be committed directly on the primary branch and a task's model changes are kept when it merges.

## 2026-09-29 — main agent, design decided without the developer

The developer decided: hard-code the registry path; one Git-tracked `.concorde/workers.json` for
worker models and limits; remove `configure-workers` (editing the JSON directly is fine); a
models-only change may be committed directly on the primary branch; a task may change models and
that change is kept on merge. The details below were chosen by the main agent.

1. **`runtime` moves into `workers.json` too.** Earlier the main agent proposed keeping `runtime`
   beside `python` because only it had to stay tracked; with `workers.json` tracked, the whole
   `workers` section of `config.json` moves, as the developer first proposed. `config.json` keeps
   `profile_version`, `protocol` and `python`; profile 19.
2. **Shape**: `{"schema_version": 1, "default", "operations", "limits": {timeout_seconds,
   max_turns, max_budget_usd, rounds}, "runtime": [...]}`; the model part keeps its current
   shape. A missing file means defaults. Workers validates the whole file when a worker launches.
3. **Moved fields are refused by name.** `registry`, `workers` and `checks` left in `config.json`
   each get an error naming where the setting lives now (no migration shim).
4. **Read from the worktree the run works in.** An unbound run now takes the worker
   configuration from its checkout of HEAD, like every other input, instead of from the
   uncommitted file of the worktree it started in; a models change must be committed (which the
   developer allows directly on the primary branch) before unbound runs use it.
5. **`task open` no longer copies anything**: the task branch carries the file from its base
   commit, which gives the earlier "fixed when the task opens" rule through Git.
6. **The pi model picker goes with `configure-workers`**, since it only opened that editor; the
   model discovery script `scripts/available_models.py` stays for suggestions.
7. **The Concorde checkout's own `.concorde/workers.json`** is created from the primary
   worktree's current untracked `worker-models.json` (copied into this task at open) plus the
   `workers.runtime` of `config.json`, so no choice is lost.

## 2026-09-29 — main agent, further decisions and results

- The glossary term "Worker model configuration" became **Worker configuration**
  (`concept.worker-configuration`), since the file now also holds limits and runtime paths; its
  realization in Workers is titled "Configuration reader" so that the term and the realization
  do not share a title (CHK.node.title). The concepts `configure-workers` and `Model picker` were
  removed with what they named.
- A leftover `.concorde/worker-models.json` without `.concorde/workers.json` is refused with
  `config_invalid` rather than ignored, so a project's earlier model choices never silently fall
  back to defaults; this is an error, not a migration shim.
- Test fixtures that choose the fake Claude Code for workers now commit `.concorde/workers.json`,
  since a task no longer receives an uncommitted copy.
- DEVELOPING.md gained the exception that a change of `.concorde/workers.json` alone, asked for by
  the developer, is committed directly on the primary branch.
- Open for after the merge: the primary worktree still has the untracked
  `.concorde/worker-models.json`, whose content this task moved into the tracked
  `.concorde/workers.json`; once the merge lands and the ignore rule is gone it will show as
  untracked and must be deleted.
- Results: full pytest suite 683 passed / 4 skipped; `build --check` and `spec-validation`
  success; `task-validation` ready with all 23 configured checks passed.

## 2026-09-29 — non-ok: first merge refused with check_failed

`task merge project-config` merged, then found `.concorde/worker-models.json` untracked in the
primary worktree (the merged `.gitignore` no longer ignores it) and undid the merge, leaving main
at 8d0d5d9a and the task delivered. This was the expected leftover noted above. The main agent
compared it with the task's `.concorde/workers.json` (identical `default`/`operations`), kept a
copy in its scratchpad, deleted it from the primary worktree and merged again.

## Closed: merged, 2026-09-28T18:46:15Z
