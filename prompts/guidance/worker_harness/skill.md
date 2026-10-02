---
audience: shared
---

## Worker models

Every worker runs on what the worktree's `.concorde/workers.json` chooses, and only on that:
Concorde never takes a worker's model or reasoning level from your or the developer's own pi or
Claude Code settings; only credentials and pi's provider definitions come from there. The file is
tracked by Git like the project's code, and no worker runs without it: a run whose worktree has
none fails with `config_missing`. The installer does not write it, since the models are the
developer's choice: when the project has none, ask the developer which models workers may use and
which is the default, then write the file and commit it alone on the primary branch before any
Operation runs.

The file names every model by a **project model name** that depends on no installation, such as
`gpt-6-astra` or `claude-opus-5-5`: letters, digits, `.`, `_` and `-`. The id a program takes, such
as pi's `local-openai/gpt-6-astra`, is a fact about one machine and never goes into the file: the
**model map**, the developer's own `~/.config/concorde/models.json` (or `$XDG_CONFIG_HOME/concorde/`,
or the file `CONCORDE_MODEL_MAP` names), gives each project model name its local id on `pi`, on
`claude` or both, and is never committed:

```json
{
  "schema_version": 1,
  "models": {
    "gpt-6-astra": {"pi": "local-openai/gpt-6-astra"},
    "claude-opus-5-5": {"pi": "anthropic/claude-opus-5-5", "claude": "claude-opus-5-5"}
  }
}
```

The map belongs to the developer's machine, so write or change it only when the developer asks or
agrees, and when a model they choose for the file is new, tell them the entry the map needs. A
worker whose model has no id for its program in the map is refused with `model_unmapped`, a
missing map with `model_map_missing` and an unreadable one with `model_map_invalid`, each naming
the map and the entry to add; the project model name is never used as the id.

The file holds `schema_version: 2` and the required `enabled_models`, every model a worker may
run on by its project model name, each `{}` or with its own `reasoning` level. Every model an entry
names must be enabled, or every worker is refused with `model_not_enabled`. The file holds a `default`
and, per Operation, a `default` and one entry per **worker id** under
`operations.<operation>.default` and `operations.<operation>.workers.<worker-id>`: the name each
Operation gives the workers it launches, `worker` for most Operations with one worker, `reviewer`
for `plan_review`, `reviewer` and `checker` for `spec_review`, `reviewer1` to `reviewer5`,
`architect1`, `architect2` and `chair` for `spec_panel`. Each entry
may set a `backend` (`pi` or `claude`), a `model` and a `reasoning` level, and the most specific
entry that sets a field wins. Workers run on pi, although you run on Claude Code, unless an entry sets
`backend: "claude"`; an entry that only chooses a backend keeps the model and level it inherits,
which the map must then give an id on that program. A worker whose entries name no model is refused with
`model_unresolved`, so give the `default` a model. A worker takes the level set by the entry that
chose its model or a more specific one, otherwise its model's own level in `enabled_models`,
otherwise one a less specific entry sets, otherwise its program's built-in default. Remove a field
to inherit it rather than writing null. The file also holds the `limits` of every worker launch
(`timeout_seconds`, `max_turns`, `max_budget_usd`, `rounds`) and the `runtime` paths workers may
read besides their grant (by default `.venv` and `node_modules`):

```json
{
  "schema_version": 2,
  "enabled_models": {"gpt-6-astra": {"reasoning": "medium"}, "claude-opus-5-5": {}},
  "default": {"model": "gpt-6-astra"},
  "operations": {
    "spec_panel": {"workers": {"chair": {"backend": "claude", "model": "claude-opus-5-5"}}}
  }
}
```

Where the coordination part is installed, a task carries the file of its base commit, so a later
change on the primary branch never reaches a task already open. Change worker models only when the developer asks, by editing the JSON
directly and preserving unrelated entries; there is no editor. A model the developer adds for a
worker goes into `enabled_models` too. For future tasks, edit the primary
worktree's `.concorde/workers.json` and commit that file alone on the primary branch: a change of
nothing but this file is one of the few changes you commit directly in the primary worktree, beside
an approved small change and regenerated derived files, never while a
`concorde task merge` is unfinished. A task may change its own models while it works, as any
tracked file of its branch; the change stays with the task and reaches the primary branch when the
task merges. An unbound run reads the committed file of the commit it examines, so commit a
change before an unbound run is to use it.

For suggestions, run `python3 scripts/available_models.py --backend pi` or `--backend claude`,
optionally with `--json`. In an installed project the script is under
`.concorde/framework/scripts/available_models.py`. It works outside Git and calls no inference
API: pi lists configured credentialed candidates; Claude's aliases and settings-derived names
are incomplete and do not prove account access. Each candidate shows the project model names the
map already gives it, and pi's listing also names the map's pi ids pi no longer lists, such as one
a changed pi configuration renamed: those are the map entries to update. Discovery failure or an empty list does not block
custom/offline model names. AI may use these suggestions when the developer asks for options;
if a requested model is already known, edit it directly without a mandatory question flow.

Workers validate the whole file when a worker launches. The chosen backend must be installed then,
but need not be installed to edit the file. A missing program causes `backend_missing`, never
fallback, and a malformed file `config_invalid` naming the field; a file of `schema_version: 1`,
whose models were local ids, is refused saying how to rename them and map them. An Operation whose
worker cannot be configured ends `failed` with `worker_model_unavailable`, naming the worker, file,
map entry or missing program.
