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
2. Enter the worktree with EnterWorktree (`path` set to it). A session is inside at most one task
   at a time.
3. Create what Git ignores there: `uv sync --locked --group dev`, `npm --prefix docsite ci`,
   `python3 scripts/concorde.py build` and, for the reference submodules,
   `python3 scripts/development/init-references.py`.
4. Change the sources, verify, and commit each verified step on the task branch. Run every
   `scripts/concorde.py` command (`build`, `validate`, `registry`, `run <operation>`) from the task
   worktree, never the primary worktree's copy: only the branch's copy knows the branch's
   Protocol, checks and prompts.
5. Run `python3 scripts/concorde.py run validate --task <task>` and `run delivery --task <task>`
   there.
6. Leave with ExitWorktree (`action: "keep"`) and, from the primary worktree, run
   `python3 scripts/concorde.py task merge <task> --check "python3 scripts/concorde.py build"
   --check "python3 scripts/concorde.py validate"`. It takes the merge lock, merges the task branch
   into main, runs the build and `validate` on main as a cross-check of the branch's
   self-validation, undoes the merge if either fails, and closes the task. Never merge with
   `git merge` directly: other main sessions may be merging at the same time. On `merge_busy`, run
   it again; on `merge_conflict`, re-enter the task worktree, merge main into the task branch,
   resolve, and repeat steps 4 and 5.

For work split into several tasks, the main agent stays in the primary worktree and starts one task
session per task with `python3 scripts/concorde.py task session <task> --main <its session name>`;
each works through steps 3 to 5 in its own worktree and reports back, and the main agent merges.
Before starting a session, the main agent runs `python3 scripts/development/init-references.py` in
the task worktree itself: it registers submodules in the shared `.git/config`, which the session's
sandbox keeps read-only. A task session's network is open to every host.

Only a very small change, such as a typo, a one-line fix or a wording correction, may be made
directly in the primary worktree, and only after the developer approves that specific change: say
what you would change and why it is small, and wait for the approval. Without it, open a task.

Concorde's own Operations and worker agents may be used on this checkout, but they are still in
early development, so using them is optional: do the work directly whenever that is more reliable.
When you do run an Operation or a worker, observe the run closely (its result, error chain, host
evidence, run record and the changes it made) rather than trusting its status. If the Operation,
its host or its worker instructions show an obvious problem, fix it directly in the sources, verify
the fix, and commit it as its own step.

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
