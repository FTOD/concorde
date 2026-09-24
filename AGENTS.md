# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs under `specs/` before changing
sources. Specs and their paired metadata use English.

## How work is organized

Concorde supports Claude Code and pi. The developer works with a main agent: the Claude Code or pi
session in the primary worktree. The main agent discusses the project, splits work
into tasks (a branch and its worktree each), runs Operations in those worktrees, keeps each task's
decision log and merges delivered task branches. It normally does not edit the project itself.

Workers are headless `claude -p` or `pi -p` processes launched by an Operation host for one bounded task of
one task type (understand, specify, implement, test, review-spec, review-code) under a grant
computed from the task worktree's Specs. Workers never touch Git, never run Operations and never
start agents; their settings deny everything outside the grant.

Developing this checkout itself is direct developer-authorized maintenance, done in a task. Open
one from the primary worktree with
`python3 scripts/concorde.py task open <task> --goal "<goal>" --modules <ids>`, change the sources
in the task's worktree, verify, and commit each verified step on the task branch. Then run
`python3 scripts/concorde.py run validate --task <task>` and `run delivery --task <task>`, merge
the task branch into main, and close it with `task close <task> --merged`. The task worktree lacks
the Git-ignored `.venv`, `docsite/node_modules` and `generated/`; create them there
(`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`) before verifying.

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
