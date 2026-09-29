---
audience: shared
---

# Developing Concorde

This is Concorde's own source checkout, not a consumer installation. The `concorde` skill tells you
how to work as the main agent or as a task session here as in any Concorde project; this skill adds
what is particular to developing Concorde itself. In this checkout `concorde` is
`python3 scripts/concorde.py` of the worktree you are in. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs under `specs/` before changing
sources. Specs and their paired metadata use English.

## How work is organized

The developer works with a main agent: the Claude Code session in the primary worktree. For now
the main agent and its task sessions run only on Claude Code, while workers may also run on pi. The
main agent discusses the project, splits work into tasks (a
branch and its worktree each), hands every task to a task session, keeps each task's decision log
and merges delivered task branches. It never edits the primary worktree's sources, except a small
change the developer approved, and never works inside a task worktree.

The work splits into two halves. Coordination (the main agent, tasks and task sessions) decides
what to work on and in which worktree; Execution does the bounded work in one bound workspace and
knows nothing of tasks. `task open` binds each task worktree as a workspace
(`.concorde/workspace.json`), and every run started in that worktree reads the binding instead of
naming the task. Workers are headless `claude -p` or `pi -p` processes launched by an Operation for
one bounded job of one task type (understand, specify, implement, test, review-spec, review-code,
code-to-spec) under a grant computed from the workspace's Specs. Workers never touch Git, never run
Operations and never start agents; their settings deny everything outside the grant. Deterministic
steps (`task-validation`, `delivery`, `scaffold`) are execution commands, not Operations.

Developing this checkout itself is direct developer-authorized maintenance, done in tasks:

1. The main agent opens the task from the primary worktree with
   `python3 scripts/concorde.py task open <task> --goal "<goal>" --modules <ids>`; its worktree is
   `.claude/worktrees/<task>` and its decision log the `decision_log` path the command prints.
2. Before starting the task's session, the main agent runs
   `python3 scripts/development/init-references.py` in the task worktree itself, with that
   worktree's own script: it registers the reference submodules in the shared `.git/config`, which
   the session's sandbox keeps read-only. It records the task's brief in the decision log and starts
   the session with `python3 scripts/concorde.py task session <task> --main <its session name>`
   from the primary worktree.
3. The task session creates what Git ignores in its worktree: `uv sync --locked --group dev`,
   `npm --prefix docsite ci` and `python3 scripts/concorde.py build`.
4. It changes the sources, verifies, and commits each verified step on the task branch. It runs
   every `scripts/concorde.py` command (`build`, `spec-validation`, `registry`, `run <operation>`,
   `task-validation`, `delivery`) from the task worktree, never the primary worktree's copy: only
   the branch's copy knows the branch's Protocol, checks and prompts, and only the task worktree
   holds the workspace binding the runs read.
5. It appends every decision taken without the developer and every non-`ok` result to the decision
   log, then runs `python3 scripts/concorde.py task-validation` and
   `python3 scripts/concorde.py delivery` there, and reports to the main agent.
6. After delivery, the main agent runs, from the primary worktree,
   `python3 scripts/concorde.py task merge <task> --check "python3 scripts/concorde.py build"
--check "python3 scripts/concorde.py spec-validation"`. It takes the merge lock, merges the task
   branch into main, runs the build and `spec-validation` on main as a cross-check of the branch's
   self-validation, undoes the merge if either fails, and closes the task, which stops its Claude
   Code task sessions and removes them from Claude's session list, keeping their transcripts in
   the task's trace. Its `warnings`, like those of `task close`, name a decision log nobody wrote in
   and each task session whose transcript could not be kept or that could not be removed, with the
   reason and the `claude rm <id>` that removes it by hand. The main agent acts on every warning
   and handles `merge_busy`, `workspace_busy`, `merge_conflict`, `merge_incomplete` and
   `merge_diverged` as the `concorde` skill says: on `merge_conflict` it answers the task session
   to merge main into its task branch, resolve, verify and deliver again.

A change of the worker configuration `.concorde/workers.json` alone, made when the developer asks
for other worker models, is committed by itself directly on the primary branch, never while a
`task merge` is unfinished.

Concorde's own Operations and worker agents may be used on this checkout, but they are still in
early development, so using them is optional: do the work directly whenever that is more reliable.
@prompts/dogfooding/common/observe-runs.md
If the Operation, its host or its worker instructions show an obvious problem, fix it directly in
the sources, verify the fix, and commit it as its own step.

## Defect reports from develop installs

A project installed from this checkout with `python3 scripts/install-concorde.py <project>
--develop` runs this primary worktree's Concorde, and its main agent reports the Concorde defects
it finds as defect reports: Issue reports written in that project, described by the Dogfooding
Module (`specs/concorde/dogfooding/module.md`). A develop install and its updates are refused
unless this primary worktree is clean and on its branch. When the developer hands the main agent a
report, the task that fixes it proceeds as follows:

1. The main agent opens a task for the Module it judges at fault (the report's owner is `null`);
   in the task worktree, the task session records the report with
   `python3 scripts/issues.py report --file <report> --task <task>`. Its evidence is checked in the
   project its `origin` names, and its `concorde_commit` says which Concorde the defect was seen on:
   check first that it still happens at the head. Then append a report to the recorded Issue naming
   the Module at fault as its `owner_target_id`, with the Issue's `issue_id` and the
   `expected_revision` that `python3 scripts/issues.py show <id>` prints, since the Issue's owner
   is its latest report's.
2. Read its `error_chain` in full and check its `basis`. A blocked boundary is placed in one of
   Dogfooding's four boundary cases. Fix a Concorde implementation bug, where the grant or harness
   applied differs from what the Protocol derives from the Specs, directly. For a Concorde design
   limitation, where the Specs are right and the Protocol cannot express what legitimate work
   needs, escalate to the developer before changing Concorde's design or Protocol or loosening any
   boundary. Close a report that turns out to be the project's own problem or overreaching work
   with `--reason not-actionable` and a note the developer can pass back.
3. Fix the defect generally, never only for the reporting project, close the Issue on the task
   branch with `--reason resolved` and the fix as evidence, and deliver the task; the main agent
   merges it as usual. The project takes the fix with `concorde update`.

## Source and verification

Author `prompts/`, `protocol/`, `src/`, `scripts/`, `docsite/` and Specs, never rendered output
under `generated/`. Run `python3 scripts/concorde.py build` after changing prompts or Protocol
sources, and after Protocol changes also run
`python3 scripts/concorde.py protocol-manifest --write --bind-project`. After changing a Module's
`module` block, refresh the registry mirror with `python3 scripts/concorde.py registry --write`.

Format changed sources explicitly (`uvx ruff format` for Python, Prettier for TypeScript,
JavaScript and Markdown under `docs/`) and confirm a second pass changes nothing. Before
committing, inspect the diff and run `build --check`, `spec-validation` and the relevant tests; run
the full suite (`.venv/bin/python -m pytest`) once on the final input of a milestone. Deterministic
checks are not model-based integration tests, and self-tests are never independent.

Commit verified steps, inspecting the staged diff before committing and the status afterwards.
Never edit another worktree's sources or index.
