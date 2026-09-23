# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs under `specs/` before changing
sources. Specs and their paired metadata use English. The accepted refactor design is
`docs/design/concorde-refactor.md`; where a Spec and that document differ, the Spec wins.

## How work is organized

Concorde supports only Claude Code in this version. The developer works with a main agent: the
Claude Code session in the primary worktree. The main agent discusses the project, splits work
into tasks (a branch and its worktree each), runs Operations in those worktrees, keeps each task's
decision log and merges delivered task branches. It normally does not edit the project itself.

Workers are headless `claude -p` processes launched by an Operation host for one bounded task of
one task type (understand, specify, implement, test, review-spec, review-code) under a grant
computed from the task worktree's Specs. Workers never touch Git, never run Operations and never
start agents; their settings deny everything outside the grant.

Developing this checkout itself is direct developer-authorized maintenance: change sources in this
worktree, verify, and commit each verified step. Do not run Concorde's own Operations on this
checkout unless the developer explicitly asks for it.

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
