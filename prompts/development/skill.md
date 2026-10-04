---
audience: shared
---

# Developing Concorde

This is Concorde's own source checkout, not a consumer installation. The `concorde` skill tells you
how to work as the main agent or as a task session here as in any Concorde project.
This skill adds what is particular to developing Concorde itself. In this checkout `concorde` is
`python3 scripts/concorde.py` of the worktree you are in. Before changing sources, read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs under `specs/`.
Specs and their paired metadata use English.

## How work is organized

The developer works with a main agent: the Claude Code session in the primary worktree. For now
the main agent and its task sessions run only on Claude Code. For now, workers may also run on pi.
The main agent does the following:

- Discusses the project.
- Splits work into tasks (a branch and its worktree each).
- Hands every task to a task session.
- Keeps each task's decision log.
- Merges delivered task branches.

Except for a small change the developer approved, it never edits the primary worktree's sources.
It never works inside a task worktree.

The work splits into two halves. Coordination decides what to work on and in which worktree.
Coordination includes the following:

- The main agent.
- Tasks.
- Task sessions.

Execution does the bounded work in one bound workspace. It knows nothing of tasks.
`task open` binds each task worktree as a workspace (`.concorde/workspace.json`).
Every run started in that worktree reads the binding instead of naming the task.
Workers are headless `claude -p` or `pi -p` processes launched by an Operation.
Each worker performs one bounded job of one task type under a grant computed from the workspace's
Specs. The task types are:

- understand
- specify
- implement
- test
- review-spec
- review-code
- code-to-spec
- review-architecture

Workers never touch Git. Workers never run Operations. Workers never start agents.
Their settings deny everything outside the grant. The following deterministic steps are execution
commands, not Operations:

- `task-validation`
- `delivery`
- `scaffold`

Developing this checkout itself is direct developer-authorized maintenance, done in tasks:

1. The main agent opens the task from the primary worktree with
   `python3 scripts/concorde.py task open <task> --goal "<goal>" --modules <ids>`.
   Its worktree is `.claude/worktrees/<task>`.
   Its decision log is the `decision_log` path the command prints.
2. The main agent records the task brief in the decision log.
   It then starts the session from the primary worktree with
   `python3 scripts/concorde.py task session <task> --main <its session name>`.
3. The task session creates what Git ignores in its worktree with these commands, in order:

   - `python3 scripts/development/init-references.py`
   - `uv sync --locked --group dev`
   - `npm --prefix docsite ci`
   - `python3 scripts/concorde.py build`

   The first script registers in the shared `.git/config` each reference submodule not registered
   yet. It then checks them all out.
   When another worktree's preparation writes `.git/config` meanwhile, the script refuses before
   checking out anything. The refusal names the submodule and `config.lock`.
   Once that command ends, run the script again. Never delete the lock.
4. The task session changes the sources and verifies them. It commits each verified step on the
   task branch. It runs every `scripts/concorde.py` command from the task worktree, never the
   primary worktree's copy. These commands include:

   - `build`
   - `spec-validation`
   - `registry`
   - `run <operation>`
   - `task-validation`
   - `delivery`

   Only the branch's copy knows the branch's Protocol, checks and prompts. Only the task worktree
   holds the workspace binding the runs read.
5. The task session appends every decision taken without the developer and every non-`ok` result
   to the decision log. It then runs `python3 scripts/concorde.py task-validation` there.
   It then runs `python3 scripts/concorde.py delivery` there. It reports to the main agent.
6. After delivery, the main agent runs, from the primary worktree,
   `python3 scripts/concorde.py task merge <task> --check "python3 scripts/concorde.py build"
--check "python3 scripts/concorde.py spec-validation"`.
   The command performs these steps:

   - Takes the merge lock.
   - Merges the task branch into main.
   - Runs the build and `spec-validation` on main as a cross-check of the branch's self-validation.
   - If either fails, undoes the merge.
   - Closes the task.

   Closing the task stops its Claude Code task sessions. It removes them from Claude's session
   list, keeping their transcripts in the task's trace.
   Like those of `task close`, its `warnings` name a decision log nobody wrote in.
   They also name each task session whose transcript could not be kept or that could not be removed.
   Each such warning gives the reason and the `claude rm <id>` that removes the session by hand.
   The main agent acts on every warning. It handles the following as the `concorde` skill says:

   - `merge_busy`
   - `workspace_busy`
   - `merge_conflict`
   - `merge_incomplete`
   - `merge_diverged`

   On `merge_conflict`, it answers the task session to do the following:

   - Merge main into its task branch.
   - Resolve.
   - Verify.
   - Deliver again.

When the developer asks for other worker models, a change of the worker configuration
`.concorde/workers.json` alone is committed by itself directly on the primary branch.
This never happens while a `task merge` is unfinished.
The file names models by project model names. The developer's own model map,
`~/.config/concorde/models.json`, gives each its local pi or Claude Code id.
The model map is never committed, so a model renamed in the developer's pi configuration changes
only the map. Tests never read that map.
`tests/__init__.py` points `CONCORDE_MODEL_MAP` at `tests/concorde/support/models.json`.

Concorde's own Operations and worker agents may be used on this checkout.
They are still in early development, so using them is optional.
Whenever direct work is more reliable, do the work directly.
@prompts/dogfooding/common/observe-runs.md
If any of the following shows an obvious problem, fix it directly in the sources:

- The Operation.
- Its host.
- Its worker instructions.

Verify the fix. Commit it as its own step.

## Defect reports from develop installs

A project installed from this checkout with `python3 scripts/install-concorde.py <project>
--develop` runs this primary worktree's Concorde.
Its main agent reports the Concorde defects it finds as defect reports: Issue reports written in
that project. The Dogfooding Module (`specs/concorde/dogfooding/module.md`) describes them.
Unless this primary worktree is clean and on its branch, a develop install and its updates are
refused. When the developer hands the main agent a report, the task that fixes it proceeds as
follows:

1. In the primary worktree, the main agent records the report as an Issue with either of these:

   - The project MCP server's `issue_report` (`file` naming the report).
   - `python3 scripts/issues.py report --file <report>`.

   It opens a task for the Module it judges at fault with `--resolves <issue>`.
   The report's owner is `null`. Its evidence is checked in the project its `origin` names.
   Its `concorde_commit` says which Concorde the defect was seen on.
   Check first that it still happens at the head.
   Then append a report to the recorded Issue with the following, since the
   Issue's owner is its latest report's:

   - The Module at fault as its `owner_target_id`.
   - The Issue's `issue_id`.
   - The `expected_revision` that `issue_show` prints.

2. Read its `error_chain` in full. Check its `basis`.
   A blocked boundary is placed in one of Dogfooding's four boundary cases.
   When the applied grant or harness differs from what the Protocol derives from the Specs, fix
   the Concorde implementation bug directly.
   A Concorde design limitation has the following conditions:

   - The Specs are right.
   - The Protocol cannot express what legitimate work needs.

   For a Concorde design limitation, escalate to the developer before any of the following:

   - Changing Concorde's design.
   - Changing its Protocol.
   - Loosening any boundary.

   If a report turns out to be the project's own problem or overreaching work, close it with
   `--reason not-actionable` and a note the developer can pass back.
3. Fix the defect generally, never only for the reporting project. Deliver the task.
   The main agent merges it as usual. This merge closes the Issue as resolved.
   The project takes the fix with `concorde update`.

## Source and verification

Author the following, never rendered output under `generated/`:

- `prompts/`
- `protocol/`
- `src/`
- `scripts/`
- `docsite/`
- Specs

After changing prompts or Protocol sources, run `python3 scripts/concorde.py build`.
After Protocol changes, also run
`python3 scripts/concorde.py protocol-manifest --write --bind-project`.
After changing a Module's `module` block, refresh the registry mirror with
`python3 scripts/concorde.py registry --write`.

Write the Markdown under `prompts/` in the Spec Protocol's sentence style
(`.concorde/protocol/kinds/module.md`, chapter *Sentence style*), as the Specs are written. This is
Concorde's own requirement, not a Protocol rule. Models read prompts.
Short sentences with one fact each serve a model as they serve a person. Run
`python3 scripts/development/check-style.py` with the changed prompts, or with no path for all of
`prompts/`. It reports the same style problems that `spec-validation` reports for the Specs. A
change adds no new problem to the prompts it touches. The script measures the Protocol's chapters
under `protocol/` too.

Format changed sources explicitly with the applicable formatter:

- `uvx ruff format` for Python.
- Prettier for TypeScript.
- Prettier for JavaScript.
- Prettier for Markdown under `docs/`.

Confirm a second pass changes nothing. Before committing, inspect the diff.
Before committing, run the following:

- `build --check`
- `spec-validation`
- The relevant tests.

Run the full suite (`.venv/bin/python -m pytest`) once on the final input of a milestone.
Deterministic checks are not model-based integration tests. Self-tests are never independent.

Commit verified steps. Before committing, inspect the staged diff. Afterwards, inspect the status.
Never edit another worktree's sources or index.
