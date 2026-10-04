# Validation scenarios

Concrete situations that show the [requirements](requirements.md) of [Validation](module.md). The
readiness is defined in the [contracts](contracts.md).

## Deciding readiness

### scenario.validation.ready — A complete workspace is ready

- GIVEN a task worktree bound to the workspace `severity`, whose changes are bound by `module.issues`, whose Specs have no structural error and whose checks pass
- WHEN the task level runs `concorde task-validation` there
- THEN the result has kind `command`, the workspace `severity`, no worker and status `ok`, and its output is a readiness with `ready` true
- AND the readiness records the input measurement and one passed [check result](../../glossary.json#concept.check-result) per [configured check](../../glossary.json#concept.configured-check) of `module.issues`
- AND nothing in the workspace changed

### scenario.validation.not-ready — Every blocker is reported in one run

- GIVEN a workspace with a broken [Spec](../../glossary.json#concept.spec) link, a new file bound by no [Module](../../glossary.json#concept.module), a failing check of a changed Module and a changed project glossary
- WHEN `task-validation` runs
- THEN the result has status `blocked` and the readiness has `ready` false
- AND `blocking` holds a structural finding, an unbound finding and a check finding
- AND the summary names each finding with its location and message
- BUT a changed project glossary is accounted for like a Spec document, never an unbound finding
- AND the error's `not_deliverable` link, of level `command`, has one cause per finding, the check's with its exit code and the end of its log

### scenario.validation.warnings — Warnings do not block

- GIVEN a workspace whose only findings are structural warnings, such as missing scenario coverage
- WHEN `task-validation` runs
- THEN the readiness has `ready` true and lists the warnings

### scenario.validation.unloadable — Specs that cannot be loaded

- GIVEN a workspace whose Specs cannot be loaded
- WHEN `task-validation` runs
- THEN the run begins, and the result has status `blocked` and a readiness with `ready` false
- AND its `load` finding names the file and the loader's error, in the readiness and as the cause of the result's error
- AND no configured check is run

### scenario.validation.shared-file — A shared file runs every binder's checks

- GIVEN a changed file bound by `module.spec` and `module.views`
- WHEN `task-validation` runs
- THEN the configured checks of both Modules are run

### scenario.validation.submodule-reference — A vendored reference is accounted for

- GIVEN a workspace that adds two submodules, one of which a Module includes a directory of as `external`
- WHEN `task-validation` runs
- THEN the included submodule's gitlink is no blocking finding
- BUT the other submodule's gitlink is reported as `unbound`

### scenario.validation.submodule-content — A file changed inside a submodule is not measured

- GIVEN a workspace with a submodule
- WHEN a file inside the submodule's own worktree changes
- THEN the submodule is no changed path and the workspace has no uncommitted change

### scenario.validation.submodule-commit — Moving a submodule's commit is a change

- GIVEN a workspace with a submodule
- WHEN the submodule is moved to another commit
- THEN the submodule is a changed path and an uncommitted change

### scenario.validation.sandbox-placeholder — A sandbox's placeholder file is not measured

- GIVEN a workspace with an uncommitted change
- AND an untracked empty `.bashrc` with no write bits and one link, the placeholder Claude Code's Bash sandbox creates before it mounts `/dev/null` there
- AND an untracked empty `notes/empty.txt` with write bits and an untracked read-only `notes/frozen.txt` with content, which the task created
- WHEN `task-validation` runs
- THEN `.bashrc` is no changed path and no blocking finding, and it alone is no uncommitted change
- BUT `notes/empty.txt` and `notes/frozen.txt` are changed paths, each reported as `unbound`

### scenario.validation.mode-change — A changed file mode changes the input digest

- GIVEN a workspace with a changed regular file
- WHEN only the file's execute bit is set and the inputs are measured again
- THEN the file's entry records the mode `100755` instead of `100644`, with the same content digest
- AND the input digest differs from the one measured before

### scenario.validation.checks-configuration — A changed check command changes the configuration digest

- GIVEN a workspace whose Module A has a checks file `.concorde/checks/module.a.json`
- WHEN the check's `argv` in that file changes and the inputs are measured again
- THEN the configuration digest differs from the one measured before, as it would for a changed `.concorde/config.json`
- AND so does the input digest

### scenario.validation.non-utf8-path — A path that is not UTF-8 is recorded losslessly

- GIVEN a workspace with a new file `src/a/caf<0xE9>.py`, whose name holds a byte that is no part of valid UTF-8, under a directory Module A binds, and a new file `stray<0xFF>.txt` bound by no Module
- WHEN `task-validation` runs
- THEN the changed paths are recorded as `"src/a/caf\351.py"` and `"stray\377.txt"`, each naming exactly its file, and measuring again yields the same input digest
- AND the first is accounted for by Module A's binding, the second is reported as `unbound` under its recorded path

## Failures

### scenario.validation.inputs-changed — The worktree changes during the run

- GIVEN a `task-validation` run whose checks are running
- WHEN a file of the workspace that the input measurement covers changes and is still changed when the run remeasures its inputs
- THEN the result has status `failed` with `inputs_changed`
- AND no readiness is issued
- AND when a configured check noticed the change, the error's cause is Check execution's `stale_evidence` link

### scenario.validation.wrong-branch — The workspace is not on its bound branch

- GIVEN a workspace whose head is detached or on another branch than the one its binding names
- WHEN `task-validation` runs
- THEN the result has status `failed` with the code `wrong_branch` and the reason `permission`
- AND no check is run

### scenario.validation.unbound — Readiness needs a bound workspace

- GIVEN a worktree without a [workspace binding](../../glossary.json#concept.workspace-binding), such as the primary worktree
- WHEN `concorde task-validation` is run there
- THEN no step runs and the result is `failed`, with `workspace` and `output` null and a `refused` link whose cause is `binding_required`, reason `scope`
- AND the result is saved in that worktree's own [run store](../../glossary.json#concept.run-store), `.concorde/unbound/<run-id>/`

### scenario.validation.sandbox-unavailable — Checks cannot be bounded

- GIVEN a host where the [read-only check boundary](../../glossary.json#concept.read-only-check-boundary) cannot be established
- WHEN `task-validation` reaches its checks
- THEN the result has status `failed` with the code `checks_unavailable` and the reason `environment`
- AND the error's cause is Check execution's `check_sandbox_unavailable` link
- AND no check runs outside the boundary

