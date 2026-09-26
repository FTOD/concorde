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

- GIVEN a workflow catalog with the brownfield workflow
- WHEN the developer runs `build`
- THEN `generated/workflows/claude/concorde-brownfield.js` starts with a `meta` block naming `concorde-brownfield`, followed by the Claude Code step adapter and the procedure
- AND `generated/workflows/pi/brownfield.js` holds the pi step adapter and the same procedure, and `generated/workflows/pi/agents/` the command-runner agents `concorde-step.md` and `concorde-report.md`
- AND the build manifest records all four

### scenario.distribution.build-check-stale — Report a stale build without writing

- GIVEN a checkout whose prompt source changed since the last build
- WHEN the developer runs `build --check`
- THEN the result is `invalid` and names every stale or missing output
- BUT no file under `generated/` changes

### scenario.distribution.build-refuses-unsafe — Refuse an unsafe prompt tree

- GIVEN a prompt file that no root includes, an include cycle, an include of a Spec document or an owned output replaced by a link
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
- WHEN the Protocol copy is written into a project
- THEN the copy is refused as a stale build
- BUT the project's existing Protocol copy is unchanged

## Command line

### scenario.distribution.refused-command-line — A refused command line still answers with one envelope

- GIVEN a command line with an unknown option or a missing required argument
- WHEN the developer runs `concorde`
- THEN exactly one `failed` result envelope is printed
- AND the exit status is nonzero

## Installation

### scenario.distribution.install — Install Concorde into a project

- GIVEN a Git project with Specs and a fresh Concorde package
- WHEN the developer runs the installer on the project
- THEN the project has the Protocol copy under `.concorde/protocol/`, the `concorde` command and the main-session guidance as a project skill and a `CLAUDE.md` block
- AND the `d2` release pinned in `concorde.json` for this platform is at `.concorde/tools/d2`, ignored by Git and named in the receipt
- AND installing again with the same pin downloads nothing
- AND `.gitignore` ignores `.claude/worktrees/`, where task worktrees go
- AND every rendered Claude Code workflow is at `.claude/workflows/concorde-<name>.js`
- AND `.claude/settings.json` allows `Workflow(concorde-brownfield)` and the two `concorde workflow` commands, keeps every setting it had, and the receipt records the added rules
- AND the receipt records the package as `source`, mode `normal`, and `source_commit` `null` for a package outside a Git checkout
- BUT no Spec document, registry or Protocol binding of the project changed

### scenario.distribution.install-settings-kept — A developer's settings survive the installer

- GIVEN a project whose `.claude/settings.json` has its own permission rules, and a receipt recording a rule the new package no longer ships
- WHEN the installer runs again
- THEN the developer's rules and other settings are unchanged, the missing workflow rules are added and the rule no longer shipped is removed
- BUT a `.claude/settings.json` that is not a JSON object is refused with `settings_invalid` before anything is written

### scenario.distribution.update — Updating Concorde in a project

- GIVEN an initialized project with an open task, installed from a checkout whose Protocol has since changed
- WHEN the developer runs `concorde update`
- THEN the configuration binds the new Protocol copy, the result names the bindings, versions and installed commits before and after and the open task, and `.concorde/update.json` marks the project Concorde unvalidated
- AND while a Spec is broken, `concorde validate` also reports `CONCORDE-UPDATE-001` and the mark stays
- AND the first validation that passes reports `CONCORDE-UPDATE-002` and removes the mark

### scenario.distribution.install-busy — Concorde is not replaced while it runs

- GIVEN an installed project in which an Operation run's host process or a pi task-session round's supervisor is still running
- WHEN the developer installs Concorde again or runs `concorde update`
- THEN the install is refused with `concorde_busy`, naming each running run or round with its process and progress file
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
- WHEN the caller runs `.concorde/bin/concorde`
- THEN it answers as usual, run by the interpreter of `.concorde/framework/python/`
- AND the receipt names that environment, the interpreter it was made from and its version
- BUT an installer given an interpreter older than Python 3.11 is refused with `python_too_old`

### scenario.distribution.task-worktree-command — The command works in a task worktree

- GIVEN a project where Concorde is installed and committed, and a linked worktree of it, which has no Framework copy of its own
- WHEN `.concorde/bin/concorde` of the linked worktree runs
- THEN it runs the primary worktree's Framework copy and answers as usual

### scenario.distribution.install-d2-refused — A d2 archive that cannot be trusted installs nothing

- GIVEN a fresh Concorde package whose `concorde.json` pins a `d2` release
- WHEN the installer runs and the downloaded archive does not match the pinned SHA-256, or the download fails
- THEN the installer refuses with `d2_digest_mismatch` or `d2_unavailable`, naming the URL and the reason
- AND nothing is written into the project
- BUT with `--without-d2` the installer places everything else and leaves `d2` to the developer

### scenario.distribution.install-pi — Install for pi as well

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde with `--pi`
- THEN the locked pi runtime is placed under `.concorde/tools/pi-runtime/` with `npm ci --ignore-scripts` from the package's lockfile
- AND the run view is placed as `.pi/extensions/concorde/` and the skill as `.pi/skills/concorde/SKILL.md`
- AND every rendered pi workflow script is under `.concorde/workflows/pi/` and the command-runner agents `concorde-step` and `concorde-report` under `.pi/agents/`
- AND a second install with the same lockfile does not run npm again
- BUT without npm the install is refused before anything else is written
