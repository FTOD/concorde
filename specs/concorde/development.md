# Development environment

The root [Module](glossary.json#concept.module) binds the files that set up development of this
checkout: the Python project and lock, the pytest configuration and its evidence plugin, the
reference initializer, the Claude Code documentation fetcher, the docsite type check and the pi
project settings that load Concorde's own pi extension here. These
promises concern how Concorde's own tests and checks run, not what Concorde offers a consumer
project.

## Test evidence

### req.concorde.test-evidence — Test runs record why and on what they ran

The pytest evidence plugin SHALL record each run's reason, scope, phase, attempt and input fingerprints in its JSON report.

Each option has its own default: an omitted `--reason` records `manual`, an omitted `--scope` or
`--phase` `unspecified` and an omitted `--attempt` `1`. The report is written only to the file
`--json=PATH` names, for example
`.venv/bin/python -m pytest tests/concorde/spec --scope=targeted --json=report.json`. It keeps
discovery, queueing and execution times apart and never presents summed parallel test time as
elapsed time.

### scenario.concorde.test-timing — Test runs record reasons and input identity

- GIVEN pytest arguments with or without `--reason`, `--scope`, `--phase`, `--attempt` and `--prior`
- WHEN the suite runs with `--json` reporting
- THEN the report records the reason, scope, phase, attempt, prior run and fingerprints of the tests, inputs, runtime, locks and environment
- AND discovery, queueing, execution and total elapsed times are reported separately
- BUT summed parallel test time is never reported as elapsed time

## External references

The third-party documentation and source that Modules include as `external` live under
`references/`. The Claude Code documentation is tracked as plain files, refreshed by
`scripts/development/fetch-claude-code-docs.py`. The pi, pi-subagents, sandbox-runtime,
pi-packages, swe-bench, langgraph and langgraph-docs references are Git submodules pinned in
`.gitmodules` to the versions Concorde was built against, each with a sparse-checkout pattern
(`concorde-sparse`) that keeps only the documentation and source a reader needs. `langgraph` is
the LangGraph release `uv.lock` locks, and `langgraph-docs` the LangChain documentation
repository, whose LangGraph pages match that release; when the lock moves to another LangGraph
release, both move with it. `scripts/development/init-references.py` checks them out,
without their media, at exactly the recorded commits.

## Agent instructions

A session in this checkout, main agent or task session, works as in any Concorde project, plus the
rules for developing Concorde itself. Both come as skills the build renders: `concorde`, the
[main-session guidance](glossary.json#concept.main-session-guidance) the installer places in every
project, and `concorde-development`, rendered from `prompts/development/skill.md`, which includes
Dogfooding's rule for observing runs. Skills load on demand, so `CLAUDE.md` and `AGENTS.md` keep a
short part that is always in context: the instruction to load both skills before any work, the core
rules of the main agent and of a task session, and in `CLAUDE.md` the import of the glossary.
Claude Code finds the skills through `.claude/skills/<name>`, links into `generated/skills/`, and pi
through the `skills` of `.pi/settings.json`; in a worktree not built yet, the instructions say to
build first and to read the rendered files directly.

### scenario.concorde.development-skills — Sessions in this checkout load both skills

- GIVEN this checkout, its primary worktree or a task worktree, after a build
- WHEN a Claude Code or pi session starts there
- THEN `CLAUDE.md` and `AGENTS.md` tell it to load the `concorde` and `concorde-development` skills before any work
- AND `.pi/settings.json` lists `generated/skills/concorde` and `generated/skills/concorde-development`, which hold the rendered skills
- AND `concorde-development` states Dogfooding's rule for observing runs word for word

## pi main sessions

A pi session in this checkout is a [main agent](glossary.json#concept.main-agent) like one in an
installed project, and needs the same [run view](glossary.json#concept.run-view) to be woken when a
run or a [task session](glossary.json#concept.task-session)'s round ends instead of polling for it. This
checkout has no installed copy of the extension, so `.pi/settings.json` loads the source,
`src/concorde/main_session/pi_extension.ts` with the modules beside it, as a project extension of
every worktree of the checkout once pi trusts the project. The extension runs the worktree's
`python3 scripts/concorde.py` when no installed `concorde` exists, and leaves its run view off in
a task session; workers run with `--no-extensions` and never load it.

### scenario.concorde.pi-extension-in-checkout — pi sessions in this checkout get the run view

- GIVEN this checkout, its primary worktree or a task worktree
- WHEN a pi session starts there and trusts the project
- THEN `.pi/settings.json` loads `src/concorde/main_session/pi_extension.ts`, the same source the installer copies into a project, with the modules it imports beside it
- AND the session has the `concorde_run` and `concorde_task_session` tools, which wake it when a run or round ends

## Docsite type check

### scenario.concorde.check-docsite-external — The docsite type check works on a disposable copy

- GIVEN this checkout with its docsite
- WHEN `scripts/development/check-docsite-types.py` runs
- THEN it copies the docsite to a temporary directory, derives the sidebar from the project registry there and runs the TypeScript compiler on the copy
- AND dependency installation and generated files stay inside that copy
- AND the command returns the compiler's exit status and removes the copy
