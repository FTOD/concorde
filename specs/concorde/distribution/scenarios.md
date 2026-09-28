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

### scenario.distribution.build-keeps-edited-leftover — Keep a leftover output edited by hand

- GIVEN an output the previous build wrote, whose prompt root was removed since and whose bytes were edited after that build
- WHEN the developer runs `build`
- THEN the build stops with an error naming the edited output
- BUT the edited output is kept as it is

## Protocol manifest and copy

### scenario.distribution.protocol-manifest-bind — Accept a changed Protocol into this checkout

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest --write --bind-project`
- THEN the tracked manifest is rewritten with the new digests
- AND the configuration is bound to it and `.concorde/protocol/` is refreshed

### scenario.distribution.protocol-manifest-report — Report a changed Protocol

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest` without flags
- THEN the result is `invalid` and names the assets whose digests differ

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
- AND `.gitignore` ignores `.claude/worktrees/`, where task worktrees go, and `.concorde/workspace.json`, their [workspace binding](../glossary.json#concept.workspace-binding)
- AND every rendered Claude Code workflow is at `.claude/workflows/concorde-<name>.js`
- AND `.claude/settings.json` allows `Workflow(concorde-brownfield)` and the two `concorde workflow` commands, keeps every setting it had, and the receipt records the added rules
- AND the receipt records the package as `source`, mode `normal`, and `source_commit` `null` for a package outside a Git checkout
- BUT no Spec document, registry or [Protocol binding](../glossary.json#concept.protocol-binding) of the project changed

### scenario.distribution.install-repeat — Installing again repeats no download

- GIVEN a project in which Concorde was installed with the pinned `d2` and the locked pi runtime
- WHEN the developer runs the installer again with the same package
- THEN the `d2` release is not downloaded again and `npm` does not run again
- AND `CLAUDE.md` still holds exactly one Concorde block

### scenario.distribution.install-docsite-template — An installed Concorde can scaffold a docsite

- GIVEN a fresh Concorde package whose `docsite/` holds the template beside files the template inventory leaves out
- WHEN the developer installs it into a project, initializes the project's Specs and runs `concorde docsite --propose`
- THEN `.concorde/framework/docsite/` holds exactly the template files [Views](../spec-tooling/views/module.md)' inventory selects, `scaffold/` included
- AND the proposal succeeds, listing the template files, a new `docsite/site.json` and, with `--github-pages`, the deployment workflow

### scenario.distribution.install-docsite-template-refused — An unsafe docsite template installs nothing

- GIVEN a Concorde package whose `docsite/` template contains a symbolic link
- WHEN the developer installs it into a project
- THEN the install is refused with `invalid_docsite_template`, naming the link, whose reason is `input`
- BUT nothing is written into the project

### scenario.distribution.glossary-import — The CLAUDE.md block imports the project's glossary

- GIVEN a project in which Concorde is installed
- WHEN `concorde init --apply` creates the project's first glossary, or an install or update finds one declared
- THEN the Concorde block of `CLAUDE.md` imports that glossary with `@<path>`, once, so Claude Code loads every term at launch
- AND the rest of `CLAUDE.md` is kept

### scenario.distribution.glossary-import-none — The CLAUDE.md block imports nothing before a glossary

- GIVEN a project whose `CLAUDE.md` has content of its own and which declares no glossary yet
- WHEN the developer installs Concorde
- THEN the Concorde block of `CLAUDE.md` imports no glossary
- AND the rest of `CLAUDE.md` is kept

### scenario.distribution.install-settings-kept — A developer's settings survive the installer

- GIVEN a project whose `.claude/settings.json` has its own permission rules, and a receipt recording a rule the new package no longer ships
- WHEN the installer runs again
- THEN the developer's rules and other settings are unchanged, the missing workflow rules are added and the rule no longer shipped is removed

### scenario.distribution.install-settings-invalid — Unusable settings refuse the install

- GIVEN a project whose `.claude/settings.json` is not a JSON object
- WHEN the installer runs
- THEN it is refused with `settings_invalid`
- BUT nothing is written, not even a workflow the project lacks

### scenario.distribution.update — Updating Concorde in a project

- GIVEN an initialized project with an open task, installed from a checkout whose Protocol has since changed
- WHEN the developer runs `concorde update`
- THEN the configuration binds the new Protocol copy, the result names the bindings, versions and installed commits before and after and the open task, and `.concorde/update.json` marks the project Concorde unvalidated
- AND the result asks for the primary branch to be merged into the open task

### scenario.distribution.update-unvalidated-reported — Validation reports an update not yet validated

- GIVEN a project that `concorde update` marked Concorde unvalidated
- AND one of its Specs is broken
- WHEN the developer runs `concorde spec-validation` in the primary worktree
- THEN the result is `invalid` and reports `CONCORDE-UPDATE-001` beside the Spec's own findings
- AND `.concorde/update.json` stays

### scenario.distribution.update-unvalidated-cleared — The first clean validation clears the mark

- GIVEN a project that `concorde update` marked Concorde unvalidated
- AND its Specs validate
- WHEN the developer runs `concorde spec-validation` in the primary worktree
- THEN the result is `success` and reports `CONCORDE-UPDATE-002`
- AND `.concorde/update.json` is removed

### scenario.distribution.install-busy — Concorde is not replaced while it runs

- GIVEN an installed project in which the runner of an [Operation](../glossary.json#concept.operation) or [execution command](../glossary.json#concept.execution-command) run still holds its [run lock](../glossary.json#concept.run-lock), or a pi [task-session](../glossary.json#concept.task-session) round's supervisor is still running
- AND its [run store](../glossary.json#concept.run-store) also holds the [progress file](../glossary.json#concept.progress-file) of the running Operation's worker and a run whose run lock nobody holds
- WHEN the developer installs Concorde again or runs `concorde update`
- THEN the install is refused with `concorde_busy`, naming each running run or round with its process and progress file
- BUT neither the worker's progress file nor the run whose run lock nobody holds is named, whatever process its recorded identifier names
- AND nothing in the project changes

### scenario.distribution.install-after-runs-end — Concorde is replaced once nothing runs

- GIVEN an installed project whose run store holds a finished run, a run whose run lock nobody holds although its recorded process identifier names a live process, and the progress file of an Operation's worker
- AND no pi task-session round's supervisor is running
- WHEN the developer installs Concorde again
- THEN the install succeeds

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
- AND uv created that environment for the Python requirement `concorde.json` names, and the receipt names the environment, the requirement, the interpreter uv chose and its version

### scenario.distribution.install-python-env-failed — No interpreter fits Concorde's Python requirement

- GIVEN a Concorde package whose Python requirement no interpreter on the machine satisfies
- AND uv may not download one
- WHEN the developer runs the installer
- THEN the install is refused with `python_env_failed`, carrying uv's output

### scenario.distribution.install-programs-missing — A missing program refuses the install before anything is written

- GIVEN a machine without `uv` on `PATH`, or without `npm` while the pi runtime is still to be placed
- WHEN the developer runs the installer on a project
- THEN the install is refused with `uv_missing` or `npm_missing`
- BUT nothing is written into the project, not even `d2`

### scenario.distribution.python-dependencies — Concorde's own environment gets its locked dependencies

- GIVEN a Concorde checkout whose `uv.lock` locks its runtime dependencies, and `uv` on `PATH`
- WHEN the installer runs
- THEN it exports the lock's runtime part, without the development group, to `.concorde/framework/requirements.txt`
- AND installs exactly those hashed versions into `.concorde/framework/python/` and checks that the environment imports LangGraph
- AND the receipt names the requirements file, the digest of the lock and the number of packages

### scenario.distribution.python-dependencies-failed — A failing dependency step refuses the install

- GIVEN a Concorde checkout and `uv` on `PATH`
- WHEN the installer runs and a step installing the Python dependencies fails
- THEN the install is refused with `python_dependencies_failed`, carrying the step's output

### scenario.distribution.python-dependencies-skipped — Install without the Python dependencies

- GIVEN a Concorde checkout and `uv` on `PATH`
- WHEN the developer runs the installer with `--without-dependencies`
- THEN the receipt's `dependencies` is `null`

### scenario.distribution.task-worktree-command — The command works in a task worktree

- GIVEN a project where Concorde is installed and committed, and a linked worktree of it, which has no Framework copy of its own
- WHEN `.concorde/bin/concorde task list` of the linked worktree runs
- THEN it runs the primary worktree's Framework copy, prints the empty task list `[]` and exits with status 0

### scenario.distribution.install-d2-refused — A d2 archive that cannot be trusted installs nothing

- GIVEN a fresh Concorde package whose `concorde.json` pins a `d2` release
- WHEN the installer runs and the downloaded archive does not match the pinned SHA-256, or the download fails
- THEN the installer refuses with `d2_digest_mismatch` or `d2_unavailable`, naming the URL and the reason
- AND nothing is written into the project

### scenario.distribution.install-without-d2 — Install without d2

- GIVEN a fresh Concorde package whose `concorde.json` pins a `d2` release
- WHEN the developer runs the installer with `--without-d2`
- THEN the install succeeds and the receipt names no `d2`
- BUT no `d2` is placed under `.concorde/tools/`, leaving it to the developer

### scenario.distribution.install-pi — Install for a pi main session as well

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde with `--pi`
- THEN the locked pi runtime is placed under `.concorde/tools/pi-runtime/` with `npm ci --ignore-scripts` from the package's lockfile, as in every install
- AND the [run view](../glossary.json#concept.run-view) is placed as `.pi/extensions/concorde/` and the skill as `.pi/skills/concorde/SKILL.md`
- AND every rendered pi [workflow script](../glossary.json#concept.workflow-script) is under `.concorde/workflows/pi/` and the command-runner agents `concorde-step` and `concorde-report` under `.pi/agents/`

### scenario.distribution.pi-runtime-default — Every install places the runtime pi workers run in

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde without `--pi`
- THEN the locked pi runtime is placed under `.concorde/tools/pi-runtime/`, since workers run on pi unless configured otherwise
- AND no file of the pi main session is placed, and the receipt records `pi` false and `pi_runtime` true

### scenario.distribution.install-without-pi-runtime — Install without the pi runtime

- GIVEN a project and a machine without npm
- WHEN the developer installs Concorde with `--without-pi-runtime`
- THEN the install succeeds without the runtime under `.concorde/tools/pi-runtime/`
- AND the receipt records `pi_runtime` false

### scenario.distribution.update-pi — An update adds the pi runtime and, on request, the pi files

- GIVEN a project installed without the pi runtime by an installer that did not record the choice
- WHEN the developer runs `concorde update`
- THEN the pi runtime is placed and the receipt records `pi_runtime` true
- BUT no file of the pi main session is placed

### scenario.distribution.update-add-pi — An update adds the pi main session's files on request

- GIVEN a project installed without the pi main session's files
- WHEN the developer runs `concorde update --pi`
- THEN the skill `.pi/skills/concorde/SKILL.md` and the pi workflow scripts under `.concorde/workflows/pi/` are placed
- AND the receipt records `pi` true

### scenario.distribution.update-keeps-pi-choices — An update keeps the recorded pi choices

- GIVEN a project whose receipt records whether the pi main session's files and the pi runtime were installed
- WHEN the developer runs `concorde update` without `--pi`
- THEN the update installs what the receipt records: the pi files and the runtime when both were chosen, without placing the runtime a second time
- AND an install made with `--without-pi-runtime` stays without the runtime
