# Distribution scenarios

Concrete situations that show the [requirements](requirements.md) at work.

## Build

### scenario.distribution.build-renders — Render the prompt roots and record them

- GIVEN a checkout whose prompt roots include other prompt files through include lines
- WHEN the developer runs `build`
- THEN each root is written to its path under `generated/` with every include expanded
- AND a `{{name}}` in a prompt is written as the literal `{name}`, while other braces stay as they are
- AND `generated/build-manifest.json` records the digest of every source and output
- AND a following `build --check` reports no differences

### scenario.distribution.build-workflows — Render every workflow for both clients

- GIVEN a workflow catalog with the [brownfield workflow](../glossary.json#concept.brownfield-workflow)
- WHEN the developer runs `build`
- THEN `generated/workflows/claude/concorde-brownfield.js` starts with a `meta` block naming `concorde-brownfield`, followed by the Claude Code step adapter and the procedure
- AND `generated/workflows/pi/brownfield.js` holds the pi step adapter and the same procedure, and `generated/workflows/pi/agents/` the command-runner agents `concorde-step.md` and `concorde-report.md`
- AND the [build manifest](../glossary.json#concept.build-manifest) records all four

### scenario.distribution.build-check-stale — Report a stale build without writing

- GIVEN a checkout whose prompt source changed since the last build
- WHEN the developer runs `build --check`
- THEN the result is `invalid` and names every stale or missing output
- BUT no file under `generated/` changes

### scenario.distribution.build-refuses-unsafe — Refuse an unsafe prompt tree

- GIVEN a prompt file that no root includes, an include cycle, an include of a [Spec](../glossary.json#concept.spec) document or an owned output replaced by a link
- WHEN the developer runs `build`
- THEN the result is `invalid` with a finding naming the problem
- BUT no output is written or removed

### scenario.distribution.build-removes-own-leftover — Remove an output the build no longer produces

- GIVEN an output the previous build wrote and whose prompt root was removed since
- WHEN the developer runs `build`
- THEN the leftover output is removed because its bytes match the previous manifest
- BUT a leftover whose bytes were edited stops the build instead

## Protocol manifest and copy

### scenario.distribution.protocol-manifest-bind — Accept a changed Protocol into this checkout

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest` without flags
- THEN the result is `invalid` and names the assets whose digests differ
- AND running it with `--write --bind-project` rewrites the tracked manifest, binds the configuration to it and refreshes `.concorde/protocol/`

### scenario.distribution.stale-copy-refused — Refuse to copy from a stale build

- GIVEN a package whose Protocol source changed after its last build
- WHEN the [Protocol copy](../glossary.json#concept.protocol-copy) is written into a project
- THEN the copy is refused as a stale build
- BUT the project's existing Protocol copy is unchanged

## Command line

### scenario.distribution.refused-command-line — A refused command line still answers with one envelope

- GIVEN a command line naming an unknown command, or giving a command that prints an envelope, such as `spec-validation` or `grant`, an unknown option, or leaving out one of its required arguments
- WHEN the developer runs `concorde` with it
- THEN exactly one `failed` result envelope is printed
- AND the exit status is nonzero

## Installation

### scenario.distribution.install — Install Concorde into a project

- GIVEN a Git project with Specs and a fresh Concorde package
- WHEN the developer runs the installer on the project
- THEN the project has the Protocol copy under `.concorde/protocol/`, the `concorde` command and the [main-session guidance](../glossary.json#concept.main-session-guidance) as a project skill and a `CLAUDE.md` block
- AND the `d2` release pinned in `concorde.json` for this platform is at `.concorde/tools/d2`, ignored by Git and named in the receipt
- AND installing again with the same pin downloads nothing
- AND `.gitignore` ignores `.claude/worktrees/`, where task worktrees go, and `.concorde/workspace.json`, their [workspace binding](../glossary.json#concept.workspace-binding)
- AND every rendered Claude Code workflow is at `.claude/workflows/concorde-<name>.js`
- AND `.claude/settings.json` allows `Workflow(concorde-brownfield)` and the two `concorde workflow` commands, keeps every setting it had, and the receipt records the added rules
- AND the receipt records the package as `source`, mode `normal`, and `source_commit` `null` for a package outside a Git checkout
- BUT no Spec document, registry or [Protocol binding](../glossary.json#concept.protocol-binding) of the project changed

### scenario.distribution.glossary-import — The CLAUDE.md block imports the project's glossary

- GIVEN a project in which Concorde is installed
- WHEN `concorde init --apply` creates the project's first glossary, or an install or update finds one declared
- THEN the Concorde block of `CLAUDE.md` imports that glossary with `@<path>`, once, so Claude Code loads every term at launch
- BUT before any glossary is declared the block imports nothing, and the rest of `CLAUDE.md` is kept

### scenario.distribution.install-settings-kept — A developer's settings survive the installer

- GIVEN a project whose `.claude/settings.json` has its own permission rules, and a receipt recording a rule the new package no longer ships
- WHEN the installer runs again
- THEN the developer's rules and other settings are unchanged, the missing workflow rules are added and the rule no longer shipped is removed
- BUT a `.claude/settings.json` that is not a JSON object is refused with `settings_invalid` before anything is written

### scenario.distribution.update — Updating Concorde in a project

- GIVEN an initialized project with an open task, installed from a checkout whose Protocol has since changed
- WHEN the developer runs `concorde update`
- THEN the configuration binds the new Protocol copy, the result names the bindings, versions and installed commits before and after and the open task, and `.concorde/update.json` marks the project [Concorde unvalidated](../glossary.json#concept.concorde-unvalidated)
- AND while a Spec is broken, `concorde spec-validation` also reports `CONCORDE-UPDATE-001` and the mark stays
- AND the first validation that passes reports `CONCORDE-UPDATE-002` and removes the mark

### scenario.distribution.install-busy — Concorde is not replaced while it runs

- GIVEN an installed project in which the runner process of an [Operation](../glossary.json#concept.operation) or [execution command](../glossary.json#concept.execution-command) run, or a pi [task-session](../glossary.json#concept.task-session) round's supervisor, is still running
- WHEN the developer installs Concorde again or runs `concorde update`
- THEN the install is refused with `concorde_busy`, naming each running run or round with its process and [progress file](../glossary.json#concept.progress-file)
- BUT the progress file of the running Operation's worker is not named as a run of its own
- BUT nothing in the project changes
- AND once the run has finished, the same install succeeds

### scenario.distribution.install-refusal-link — A refused install answers with an error link

- GIVEN an installer run on a directory that does not exist, or `concorde update` in a project whose receipt names no checkout
- WHEN the command refuses
- THEN it prints `{"error": <link>}` with a link of the Framework's error contract, whose actor is the installer or `concorde update`, whose code is `invalid_project` or `update_source_missing`, and whose reason is `input`
- AND it exits with status 1

### scenario.distribution.own-python — Concorde ignores the caller's Python

- GIVEN a project where Concorde is installed
- AND a caller whose `python3` on `PATH` fails and whose `PYTHONPATH` names a package called `concorde` that fails on import
- WHEN the caller runs `.concorde/bin/concorde task list`
- THEN it prints the project's empty task list `[]` and exits with status 0, run by the interpreter of `.concorde/framework/python/`
- AND the receipt names that environment, the interpreter it was made from and its version
- BUT an installer given an interpreter older than Python 3.11 is refused with `python_too_old`

### scenario.distribution.python-dependencies — Concorde's own environment gets its locked dependencies

- GIVEN a Concorde checkout whose `uv.lock` locks its runtime dependencies, and `uv` on `PATH`
- WHEN the installer runs
- THEN it exports the lock's runtime part, without the development group, to `.concorde/framework/requirements.txt`
- AND installs exactly those hashed versions into `.concorde/framework/python/` and checks that the environment imports LangGraph
- AND the receipt names the requirements file, the digest of the lock and the number of packages
- BUT without `uv` it is refused with `uv_missing`, a failing step with `python_dependencies_failed` and the step's output, and with `--without-dependencies` the receipt's `dependencies` is `null`

### scenario.distribution.task-worktree-command — The command works in a task worktree

- GIVEN a project where Concorde is installed and committed, and a linked worktree of it, which has no Framework copy of its own
- WHEN `.concorde/bin/concorde task list` of the linked worktree runs
- THEN it runs the primary worktree's Framework copy, prints the empty task list `[]` and exits with status 0

### scenario.distribution.install-d2-refused — A d2 archive that cannot be trusted installs nothing

- GIVEN a fresh Concorde package whose `concorde.json` pins a `d2` release
- WHEN the installer runs and the downloaded archive does not match the pinned SHA-256, or the download fails
- THEN the installer refuses with `d2_digest_mismatch` or `d2_unavailable`, naming the URL and the reason
- AND nothing is written into the project
- BUT with `--without-d2` the installer places everything else and leaves `d2` to the developer

### scenario.distribution.install-pi — Install for a pi main session as well

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde with `--pi`
- THEN the locked [pi runtime](../glossary.json#concept.pi-runtime) is placed under `.concorde/tools/pi-runtime/` with `npm ci --ignore-scripts` from the package's lockfile, as in every install
- AND the [run view](../glossary.json#concept.run-view) is placed as `.pi/extensions/concorde/` and the skill as `.pi/skills/concorde/SKILL.md`
- AND every rendered pi [workflow script](../glossary.json#concept.workflow-script) is under `.concorde/workflows/pi/` and the command-runner agents `concorde-step` and `concorde-report` under `.pi/agents/`
- AND a second install with the same lockfile does not run npm again
- BUT without npm the install is refused before anything else is written

### scenario.distribution.pi-runtime-default — Every install places the runtime pi workers run in

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde without `--pi`
- THEN the locked pi runtime is placed under `.concorde/tools/pi-runtime/`, since workers run on pi unless configured otherwise
- AND no file of the pi main session is placed, and the receipt records `pi` false and `pi_runtime` true
- BUT with `--without-pi-runtime` the runtime is left out, npm is not needed, and the receipt records `pi_runtime` false

### scenario.distribution.update-pi — An update adds the pi runtime and, on request, the pi files

- GIVEN a project installed without the pi runtime by an installer that did not record the choice
- WHEN the developer runs `concorde update`
- THEN the pi runtime is placed and the receipt records `pi_runtime` true, while no file of the pi main session is placed
- AND `concorde update --pi` places the pi main session's files, and later updates keep both
- BUT an install made with `--without-pi-runtime` stays without the runtime after an update
