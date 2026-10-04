---
audience: shared
---

## Worker models

Every worker runs on what the worktree's `.concorde/workers.json` chooses, and only on that.
Concorde never takes a worker's model or reasoning level from your or the developer's own pi or
Claude Code settings. Only credentials and pi's provider definitions come from there. The file is
tracked by Git like the project's code. No worker runs without it. When a run's worktree has no
file, the run fails with `config_missing`. Since the models are the developer's choice, the
installer does not write the file. When the project has no file, take these steps before any
Operation runs:

- Ask the developer which models workers may use and which is the default.
- Then write the file.
- Commit the file alone on the primary branch.

The file names every model by a **project model name** that depends on no installation, such as
`gpt-6-astra` or `claude-opus-5-5`. A project model name uses these characters:

- letters
- digits
- `.`
- `_`
- `-`

The id a program takes, such as pi's `local-openai/gpt-6-astra`, is a fact about one machine.
The id never goes into the file. The **model map** gives each project model name its local id on
`pi`, on `claude` or both. The map is never committed. The map is the developer's own file at one
of these locations:

- `~/.config/concorde/models.json`
- `$XDG_CONFIG_HOME/concorde/`
- the file `CONCORDE_MODEL_MAP` names

```json
{
  "schema_version": 1,
  "models": {
    "gpt-6-astra": {"pi": "local-openai/gpt-6-astra"},
    "claude-opus-5-5": {"pi": "anthropic/claude-opus-5-5", "claude": "claude-opus-5-5"}
  }
}
```

The map belongs to the developer's machine. Only when the developer asks or agrees, write or
change the map. When a model the developer chooses for the file is new, tell the developer the
entry the map needs. Each refusal names the map and the entry to add. The following cases refuse a
worker:

- When the worker's model has no id for its program in the map, the refusal is `model_unmapped`.
- When the map is missing, the refusal is `model_map_missing`.
- When the map is unreadable, the refusal is `model_map_invalid`.

The project model name is never used as the id.

The file holds `schema_version: 2` and the required `enabled_models`. The latter holds every model
a worker may run on by its project model name. Each model is `{}` or has its own `reasoning` level.
Every model an entry names must be enabled. Otherwise, every worker is refused with
`model_not_enabled`. The file holds a `default`. Per Operation, it also holds a `default` under
`operations.<operation>.default`. Per Operation, it holds one entry per **worker id** under
`operations.<operation>.workers.<worker-id>`. A worker id is the name each Operation gives the
workers it launches. Where the execution part is installed, Operations exist. The part providing
the Operations registers their worker ids. Where the method part is installed, its Operations name
their worker ids as follows:

- Most Operations with one worker name theirs `worker`.
- `plan_review` names its worker `reviewer`.
- `spec_review` names its workers `reviewer` and `checker`.

Where the method part is installed, `spec_panel` names its workers as follows:

- `reviewer1` to `reviewer5`
- `architect1`
- `architect2`
- `chair`

Each entry may set these fields:

- a `backend` (`pi` or `claude`)
- a `model`
- a `reasoning` level

The most specific entry that sets a field wins. Unless an entry sets `backend: "claude"`, workers
run on pi. This holds although you run on Claude Code. An entry that only chooses a backend keeps
the model and level it inherits. The map must then give the inherited model an id on that program. When a
worker's entries name no model, the worker is refused with `model_unresolved`. So give the
`default` a model. A worker takes its level from the first applicable source in this order:

1. The entry that chose its model or a more specific one.
2. Its model's own level in `enabled_models`.
3. A less specific entry that sets a level.
4. Its program's built-in default.

Remove a field to inherit it rather than writing null. The file also holds the `limits` of every
worker launch. These limits are:

- `timeout_seconds`
- `max_turns`
- `max_budget_usd`
- `rounds`

The file also holds the `runtime` paths workers may read besides their grant. By default, these
paths are `.venv` and `node_modules`:

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

Only when the developer asks, change worker models by editing the JSON directly and preserving
unrelated entries. There is no editor. When the developer adds a model for a worker, the model goes
into `enabled_models` too. For later work, edit the primary worktree's `.concorde/workers.json`.
Commit that file alone on the primary branch. Where the coordination part is installed, a task
carries the file of its base commit. So a later change on the primary branch never reaches a task
already open. A change of nothing but this file is one of the few changes you commit directly in
the primary worktree. The other such changes are an approved small change and regenerated derived
files. While a `concorde task merge` is unfinished, never commit this file directly in the primary
worktree. A task may change its own models while it works, as any tracked file of its branch.
The change stays with the task. When the task merges, the change reaches the primary branch.
Where the execution part is installed, an unbound run reads the committed file of the commit it
examines. Before an unbound run is to use a change, commit the change.

For suggestions, run `python3 scripts/available_models.py --backend pi` or `--backend claude`,
optionally with `--json`. In an installed project the script is under
`.concorde/framework/scripts/available_models.py`. The script works outside Git. It calls no
inference API. On pi, it lists configured credentialed candidates. Claude's aliases and settings-derived
names are incomplete. They do not prove account access. Each candidate shows the project model
names the map already gives it. The pi listing also names the map's pi ids pi no longer lists.
One example is an id a changed pi configuration renamed. Those are the map entries to update. Discovery failure
or an empty list does not block custom/offline model names. When the developer asks for options,
AI may use these suggestions. If a requested model is already known, edit it directly without a
mandatory question flow.

Workers validate the whole file when a worker launches. The chosen backend must be installed
then. The backend need not be installed to edit the file. The following cases cause configuration
errors:

- A missing program causes `backend_missing`, never fallback.
- A malformed file causes `config_invalid` naming the field.
- A file of `schema_version: 1`, whose models were local ids, is refused saying how to rename them
  and map them.

Where the method part is installed, an Operation whose worker cannot be configured ends `failed`
with `worker_model_unavailable`. The error names one of these:

- the worker
- the file
- the map entry
- the missing program
