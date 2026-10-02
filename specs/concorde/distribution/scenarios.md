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

### scenario.distribution.build-skills — Render every skill with its front matter

- GIVEN a checkout with the prompt roots `prompts/main-session/skill.md` and `prompts/development/skill.md`
- WHEN the developer runs `build`
- THEN `generated/skills/concorde/SKILL.md` and `generated/skills/concorde-development/SKILL.md` each start with front matter naming the skill and describing it in a double-quoted string
- AND each continues with the render of its prompt root, byte for byte
- AND the [build manifest](../glossary.json#concept.build-manifest) records both

### scenario.distribution.build-workflows — Render every workflow for Claude Code

- GIVEN a workflow catalog whose only workflow is the [brownfield workflow](../glossary.json#concept.brownfield-workflow)
- WHEN the developer runs `build`
- THEN `generated/workflows/claude/concorde-brownfield.js` starts with a `meta` block naming `concorde-brownfield`, followed by the Claude Code step adapter and the procedure
- AND it is the only workflow render under `generated/workflows/`
- AND the [build manifest](../glossary.json#concept.build-manifest) records it

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

### scenario.distribution.build-refuses-repeated-include — Refuse a prompt reached twice

- GIVEN a prompt root that includes two prompts, each of which includes the same third prompt with its own values
- WHEN the developer runs `build`
- THEN the build is refused, naming the third prompt and both include chains from the root that reach it
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

### scenario.distribution.build-refuses-name-conflict — Refuse a name two parts register

- GIVEN a checkout in which two parts' [registrations](../glossary.json#concept.part-registration) register the same command
- WHEN the developer runs `build`
- THEN the build stops with an error naming the command and both parts
- AND nothing is resolved by the order of the parts

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

### scenario.distribution.protocol-manifest-single-flag — Write or bind alone

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest --bind-project`
- THEN the result is `failed` with `protocol_mismatch`, the configuration is bound to the tracked manifest and `.concorde/protocol/` is left as it was
- AND when the developer then runs `protocol-manifest --write`, the tracked manifest is rewritten with the new digests, its result names the changed assets and the configuration's binding is unchanged

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

### scenario.distribution.composed-from-installed-parts — The command offers the installed parts

- GIVEN a project whose receipt names the parts installed, and one whose receipt names none
- WHEN the developer asks `concorde --help` for its commands, or the project MCP server lists its tools
- THEN the first offers exactly the distribution commands and the commands of the parts its receipt names, and the tools they register whose required parts are installed
- AND the second offers the commands of every part of the package

### scenario.distribution.part-missing — A command or tool of a part not installed names the part

- GIVEN a project installed without the issues and execution parts
- WHEN the developer runs `concorde issues list` or `concorde run spec_review`, or a session calls the project MCP server's `issue_list`
- THEN each is refused with `{"error": <link>}` whose code is `part_missing`, naming the part the command or tool belongs to and how to install it
- AND the command exits with status 1

## Installation

### scenario.distribution.install — Install Concorde into a project

- GIVEN a Git project that is not initialized, so that it has no Specs, and a fresh Concorde package
- WHEN the developer runs the installer on the project
- THEN the project has the Protocol copy under `.concorde/protocol/`, the `concorde` command and the [main-session guidance](../glossary.json#concept.main-session-guidance) as a project skill and a `CLAUDE.md` block
- AND the `d2` release pinned in `concorde.json` for this platform is at `.concorde/tools/d2`, ignored by Git and named in the receipt
- AND `.gitignore` ignores `.claude/worktrees/`, where task worktrees go, and `.concorde/workspace.json`, their [workspace binding](../glossary.json#concept.workspace-binding)
- AND every rendered Claude Code workflow is at `.claude/workflows/concorde-<name>.js`
- AND `.claude/settings.json` allows `Workflow(concorde-brownfield)`, `mcp__concorde__workflow_step` and `Bash(.concorde/bin/concorde workflow report:*)`, keeps every setting it had, and the receipt records the added rules
- AND the installer prints the receipt as its [install result](contracts.md#contract.distribution.install-result) and exits with status 0
- AND the receipt records the package as `source`, mode `normal`, and `source_commit` `null` for a package outside a Git checkout
- AND nothing is placed under `.pi/`, no `AGENTS.md` is created, and a project's own `AGENTS.md` is left as it is and not listed under `amended`
- BUT no Spec document, registry or project configuration with its [Protocol binding](../glossary.json#concept.protocol-binding) is created, which only initialization creates

### scenario.distribution.install-repeat — Installing again repeats no download

- GIVEN a project in which Concorde was installed with the pinned `d2` and the locked pi runtime
- WHEN the developer runs the installer again with the same package
- THEN the `d2` release is not downloaded again and `npm` does not run again, the runtime placed first staying in place
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

### scenario.distribution.glossary-import-failed — A glossary import that cannot be written after init

- GIVEN a project in which Concorde is installed and whose `CLAUDE.md` cannot be written
- WHEN `concorde init --apply` creates the project's first glossary
- THEN the result is `failed` with `guidance_failed`, keeping the initialization's result and naming the operating system's error, and the project is initialized
- AND once `CLAUDE.md` can be written, `concorde update` adds the glossary import to the Concorde block

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

### scenario.distribution.install-project-mcp — The installer registers the project MCP server

- GIVEN a project whose `.mcp.json` registers a server of its own
- WHEN the installer runs
- THEN `.mcp.json` also registers `concorde` as `.concorde/bin/concorde project-mcp`, the project's own server is unchanged, and the receipt lists `.mcp.json` under `amended`
- AND installing again leaves the file as it is

### scenario.distribution.install-mcp-config-invalid — An unusable `.mcp.json` refuses the install

- GIVEN a project whose `.mcp.json` is not a JSON object
- WHEN the installer runs
- THEN it is refused with `mcp_config_invalid`
- BUT nothing is written, not even a workflow the project lacks

### scenario.distribution.update — Updating Concorde in a project

- GIVEN an initialized project with an open task, installed from a checkout whose Protocol has since changed
- WHEN the developer runs `concorde update`
- THEN the configuration binds the new Protocol copy, the [update result](contracts.md#contract.distribution.update-result) names the bindings, versions and installed commits before and after and the open task, and `.concorde/update.json` marks the project Concorde unvalidated
- AND the result asks for the primary branch to be merged into the open task

### scenario.distribution.update-marked-again — Updating again before a validation

- GIVEN a project that an update from an older Concorde marked Concorde unvalidated, rebinding its Protocol, and that has not validated since
- WHEN the developer runs `concorde update` again and it fails before writing its mark
- THEN the earlier mark is as it was
- AND once the developer runs `concorde update` again and it succeeds, the mark names the older Concorde's version, installed commit and Protocol binding as the ones before and this update's as the ones after

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

### scenario.distribution.install-busy — An install is refused while a run holds its run lock

- GIVEN an installed project in which the runner of an [Operation](../glossary.json#concept.operation) or [execution command](../glossary.json#concept.execution-command) run still holds its [run lock](../glossary.json#concept.run-lock)
- AND a bound run still waiting for its workspace's lock holds its run lock, with its [run progress file](../glossary.json#concept.run-progress-file) in the lobby
- AND its [run store](../glossary.json#concept.run-store) also holds the [progress file](../glossary.json#concept.progress-file) of the running Operation's worker and a run whose run lock nobody holds
- WHEN the developer installs Concorde again or runs `concorde update`
- THEN the install is refused with `concorde_busy`, naming each running run with its run lock, the process holding it and its progress file
- BUT neither the worker's progress file nor the run whose run lock nobody holds is named, whatever process its recorded identifier names
- AND nothing in the project changes

### scenario.distribution.install-after-runs-end — Concorde is replaced once no run holds its run lock

- GIVEN an installed project whose run store holds a finished run, a run whose run lock nobody holds although its recorded process identifier names a live process, and the progress file of an Operation's worker
- WHEN the developer installs Concorde again
- THEN the install succeeds

### scenario.distribution.install-refusal-link — A refused install answers with an error link

- GIVEN an installer run on a directory that does not exist, or `concorde update` in a project whose receipt names no checkout
- WHEN the command refuses
- THEN it prints `{"error": <link>}` with a link of the Framework's error contract, whose actor is the installer or `concorde update`, whose code is `invalid_project` or `update_source_missing`, and whose reason is `input`
- AND it exits with status 1

### scenario.distribution.install-write-failed — A write that fails after the first write is refused

- GIVEN a project in which the installer cannot write the project skill, because a file stands where its folder `.claude/skills/concorde/` goes
- WHEN the developer runs the installer
- THEN the install is refused with `install_failed`, naming the operating system's error, whose reason is `environment`
- AND the Protocol copy and Framework copy placed before stay in place, while no receipt is written
- AND once the file is moved away, running the installer again completes the install and writes the receipt

### scenario.distribution.update-mark-failed — An update that fails after its receipt is completed by running it again

- GIVEN an installed project in which `concorde update` cannot write its mark, because a directory stands at `.concorde/update.json`
- WHEN the developer runs `concorde update`
- THEN the update is refused with `install_failed`, naming the operating system's error
- AND the receipt already names the new install, while the project is not marked Concorde unvalidated
- AND once the directory is removed, running the update again marks the project Concorde unvalidated

### scenario.distribution.own-python — Concorde ignores the caller's Python

- GIVEN a project where Concorde is installed and that has no task, open or ended
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

- GIVEN a project where Concorde is installed and committed, that has no task, open or ended, and a linked worktree of it, which has no Framework copy of its own
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

### scenario.distribution.pi-runtime-default — Every install places the runtime pi workers run in

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde
- THEN the locked pi runtime is placed under `.concorde/tools/pi-runtime/`, since workers run on pi unless configured otherwise
- AND the receipt records `pi_runtime` true
- BUT no file of a pi main session is placed, since the [main agent](../glossary.json#concept.main-agent) runs on Claude Code

### scenario.distribution.install-without-pi-runtime — Install without the pi runtime

- GIVEN a project and a machine without npm
- WHEN the developer installs Concorde with `--without-pi-runtime`
- THEN the install succeeds without the runtime under `.concorde/tools/pi-runtime/`
- AND the receipt records `pi_runtime` false

### scenario.distribution.update-pi-runtime — An update adds the pi runtime

- GIVEN a project installed without the pi runtime by an installer that did not record the choice
- WHEN the developer runs `concorde update`
- THEN the pi runtime is placed and the receipt records `pi_runtime` true
- AND the next `concorde update` keeps the runtime without installing it again

### scenario.distribution.install-later-files-bound — Files a later install adds stay bound

- GIVEN a project in which Concorde was installed and then initialized, so that its installation realization binds the files installed then
- WHEN the developer installs Concorde again, or runs `concorde update`, with a Concorde that installs more files, such as a workflow an older Concorde did not install
- THEN every file the receipt names outside `.concorde/` that the install added is an exact entry of the installation realization
- AND once the files are committed, `concorde spec-validation` reports no `CHK.binds.unbound` for them
- BUT a project that is not initialized gets no Spec, and installing again with nothing new leaves the Specs unchanged

### scenario.distribution.install-binding-failed — A failed binding is reported and the install kept

- GIVEN an initialized project in which Spec core refuses to bind the installation, for instance because writing the root [Module](../glossary.json#concept.module)'s metadata fails
- WHEN the developer installs Concorde
- THEN the install succeeds with the new receipt in place, and its result carries Spec core's error under `binding_error`, naming the file concerned
- BUT the receipt written to `.concorde/install.json` holds no `binding_error`

### scenario.distribution.update-keeps-pi-runtime-choice — An update keeps a runtime left out

- GIVEN a project installed with `--without-pi-runtime`, whose receipt records `pi_runtime` false
- WHEN the developer runs `concorde update`
- THEN the update succeeds without the pi runtime, even on a machine without npm, and the receipt still records `pi_runtime` false
