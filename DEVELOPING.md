# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs under `specs/` before changing
sources. Specs and their paired metadata use English.

## How work is organized

Concorde supports Claude Code and pi. The developer works with a main agent: the Claude Code or pi
session in the primary worktree. The main agent discusses the project, splits work into tasks (a
branch and its worktree each), carries a single task out inside its worktree or starts task
sessions for work split into several tasks, keeps each task's decision log and merges delivered
task branches. It never edits the primary worktree's sources.

Workers are headless `claude -p` or `pi -p` processes launched by an Operation host for one bounded task of
one task type (understand, specify, implement, test, review-spec, review-code) under a grant
computed from the task worktree's Specs. Workers never touch Git, never run Operations and never
start agents; their settings deny everything outside the grant.

Developing this checkout itself is direct developer-authorized maintenance, done in a task:

1. From the primary worktree, open it with
   `python3 scripts/concorde.py task open <task> --goal "<goal>" --modules <ids>`; its worktree is
   `.claude/worktrees/<task>`.
2. Use the host workflow in `AGENTS.md` (pi) or `CLAUDE.md` (Claude Code) to work inside the
   task. A session is inside at most one task at a time.
3. Create what Git ignores there: `uv sync --locked --group dev`, `npm --prefix docsite ci`,
   `python3 scripts/concorde.py build` and, for the reference submodules,
   `python3 scripts/development/init-references.py`.
4. Change the sources, verify, and commit each verified step on the task branch. Run every
   `scripts/concorde.py` command (`build`, `validate`, `registry`, `run <operation>`) from the task
   worktree, never the primary worktree's copy: only the branch's copy knows the branch's
   Protocol, checks and prompts.
5. Run `python3 scripts/concorde.py run validate --task <task>` and `run delivery --task <task>`
   there.
6. After delivery, the main agent returns to or remains in the primary worktree, according to
   its host workflow, and runs
   `python3 scripts/concorde.py task merge <task> --check "python3 scripts/concorde.py build"
--check "python3 scripts/concorde.py validate"`. It takes the merge lock, merges the task branch
   into main, runs the build and `validate` on main as a cross-check of the branch's
   self-validation, undoes the merge if either fails, and closes the task. Never merge with
   `git merge` directly: other main sessions may be merging at the same time. On `merge_busy`, run
   it again; on `merge_conflict`, the main agent arranges resolution in the task worktree by
   merging main into the task branch, resolving, and repeating steps 4 and 5. A task session
   reports the conflict to the main agent; it never merges, rebases or switches branches.

For work delegated to task sessions, the main agent stays in the primary worktree and starts one
session per task using its host workflow; each works through steps 3 to 5 in its own worktree and
reports back, and the main agent merges. Before starting a session, the main agent runs
`python3 scripts/development/init-references.py` in the task worktree itself: it registers
submodules in the shared `.git/config`, which the session's sandbox keeps read-only. A task
session's network is open to every host. A task session already running inside its assigned
worktree works directly there and never starts another session.

Append every unsupervised decision and every non-`ok` result, with its reason, to the task's
decision log; never rewrite it. Read error chains in full and preserve them when escalating.
Task sessions escalate questions outside their goal or Modules and major-impact decisions to the
main agent, and never merge or close tasks. The main agent reports what it decided and what is
still open when it reports the delivered work.

Only a very small change, such as a typo, a one-line fix or a wording correction, may be made
directly in the primary worktree, and only after the developer approves that specific change: say
what you would change and why it is small, and wait for the approval. Without it, open a task.

Concorde's own Operations and worker agents may be used on this checkout, but they are still in
early development, so using them is optional: do the work directly whenever that is more reliable.
Observe every Operation, workflow and worker run closely (its result, error chain, host evidence,
run record and the changes it made) rather than trusting its status. If the Operation, its host or
its worker instructions show an obvious problem, fix it directly in the sources, verify the fix,
and commit it as its own step.

## Defect reports from develop installs

A project installed from this checkout with `python3 scripts/install-concorde.py <project>
--develop` runs this primary worktree's Concorde, and its main agent reports the Concorde defects
it finds as defect reports: Issue reports written in that project, described by the Dogfooding
Module (`specs/concorde/dogfooding/module.md`). A develop install and its updates are refused
unless this primary worktree is clean and on its branch. When the developer hands you a report:

1. Open a task for the Module you judge at fault (the report's owner is `null`) and, in its
   worktree, record the report with `python3 scripts/issues.py report --file <report> --task
<task>`. Its evidence is checked in the project its `origin` names, and its `concorde_commit`
   says which Concorde the defect was seen on: check first that it still happens at the head.
2. Read its `error_chain` in full and check its `basis`. A blocked boundary is placed in one of
   Dogfooding's four boundary cases. Fix a Concorde implementation bug, where the grant or harness
   applied differs from what the Protocol derives from the Specs, directly. For a Concorde design
   limitation, where the Specs are right and the Protocol cannot express what legitimate work
   needs, ask the developer before changing Concorde's design or Protocol or loosening any
   boundary. Close a report that turns out to be the project's own problem or overreaching work
   with `--reason not-actionable` and a note the developer can pass back.
3. Fix the defect generally, never only for the reporting project, close the Issue on the task
   branch with `--reason resolved` and the fix as evidence, and deliver and merge the task as
   usual. The project takes the fix with `concorde update`.

## Source and verification

Author `prompts/`, `protocol/`, `src/`, `scripts/`, `docsite/` and Specs, never rendered output
under `generated/`. Run `python3 scripts/concorde.py build` after changing prompts or Protocol
sources, and after Protocol changes also run
`python3 scripts/concorde.py protocol-manifest --write --bind-project`. After changing a Module's
`module` block, refresh the registry mirror with `python3 scripts/concorde.py registry --write`.

Format changed sources explicitly (`uvx ruff format` for Python, Prettier for TypeScript,
JavaScript and Markdown under `docs/`) and confirm a second pass changes nothing. Before
committing, inspect the diff and run `build --check`, `validate` and the relevant tests; run the
full suite (`.venv/bin/python -m pytest`) once on the final input of a milestone. Deterministic
checks are not model-based integration tests, and self-tests are never independent.

Commit verified steps, inspecting the staged diff before committing and the status afterwards.
Never edit another worktree's sources or index.
