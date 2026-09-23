# Programmer admission and completion

The exact mechanics behind the [Implementation entry](module.md): what the Host checks before the
programmer starts, what the programmer receives, how its answer is accepted, the typed component
work of the response, and the requirements and scenarios of Implementation.

## Admission

Preparing `concorde-implement` in `execute` mode runs, in order, and stops at the first failure
without starting a model:

1. The required Spec review check of Review: refused with `review_required`.
2. The pending-gap check of Planning for the `implementation` step: outcome `spec_incomplete` with
   the recorded blockers.
3. The candidate check: `missing_change` without a managed candidate; `stale_context` when the
   Module's Spec revision differs from the plan's; `incompatible_handoff` when the request's task or
   constraints differ from the plan's; `missing_tasks` when the task list is empty.
4. The task split: every task must target a Module in the Module's change scope, else
   `permission_denied`. Tasks for other Modules are grouped by target into component work.
5. The component check: for each component, the change record must hold that component's work with
   the component task derived from its tasks by the implementation task contract, the owner's
   constraints, the component's current Spec revision, a nonempty all-complete task list and the
   component's current implementation digest. Otherwise the answer is outcome `unsupported` with the
   `components` field listing every component that failed the check.
6. The project check: the whole project's Specs must pass Spec tooling's structural checks, else
   `incompatible_contracts`.
7. The binding check: local tasks with no implementation files bound by the Module give
   `unsupported_target`.

When there are no local tasks and every component is current, the Host records completion at once
without a programmer.

## What the programmer receives

The programmer call is bound to the target Module and to every other Module that binds one of the
target's files; its Spec context is the union of their Spec contexts. Its stage inputs are the
accepted plan and the local tasks as one `concorde-implementation-task` value, plus, after a review
repair, the verified review result and the context of the Issues it cites. The capsule index adds:

- `native_workspace`: the absolute path of the candidate worktree;
- `intended_write_paths`: the absolute paths of the target Module's realization entries;
- `file_scope_enforcement: "prompt-level"` and a note that file, network and credential limits are
  instructions, not an operating-system boundary.

The programmer's tools are those of its Agent definition, including `write`, `edit`, `bash` and
`run_checks`, and no delegation. `run_checks` takes no arguments and runs the Module's configured
checks through Check execution, with a timeout derived from the configured check timeouts.

## Acceptance

The native driver first applies the checks of every native step: the run completed without
interruption, the proposal was submitted for this invocation and matches the programmer's output
schema, and the prepared inputs are unchanged. For the programmer the Module's implementation files
may change during the run, while the Spec, registry, configuration, plan, tasks and review feedback
must stay as prepared. The review feedback is checked before the run and taken as fixed afterwards.

The hook then requires the answer's `tasks` to equal the local tasks exactly, each with
`complete: true`, and every realization entry that is not pending to exist. Otherwise the answer is
`incomplete_tasks`.

On acceptance the Host marks every task of the list complete, stores the Module's
`implementation_digest`, empties `checks`, drops the repair review, records the components'
revisions when there was component work, sets `phase: implementation` and `status: completed`, and
updates the `implementation` step's pending gaps with no blockers.

## Response

The response of `concorde-implement` is the common Operation response plus one field:

| Field | Meaning |
| --- | --- |
| `components` | an array, empty unless the outcome is `unsupported` because of component work; each entry is `{"target_id", "task"}`, the component Module and its component task derived by the [implementation task contract](../planning/workflow.md#contract.planning.implementation-task) |

The user session calls Planning and Implementation for each entry with exactly that `target_id`,
`task` and the owner's constraints.

## Requirements

### req.implementation.admitted-contract — Preserve task identity and acceptance

Implementation SHALL accept completion only for the exact admitted local tasks, with their identity, target, description and acceptance unchanged.

### req.implementation.write-scope — Only the Module's own files are intended

Implementation SHALL name only the selected Module's realization entries as the programmer's intended write paths.

### req.implementation.shared-file-binding — A shared file binds every binder

Implementation SHALL bind a programmer call to every Module that binds one of the selected Module's files.

### req.implementation.components-return — Component work goes back to the caller

Implementation SHALL return component work that lacks current completed evidence in the typed `components` field instead of starting any worker for it.

### req.implementation.materialized-files — Listed files exist

Implementation SHALL refuse completion while a non-pending file that the Module's realizations list does not exist.

### req.implementation.no-readiness — Completion is not readiness

Accepting task completion SHALL NOT run checks or reviews, make the candidate ready, or deliver it.

## Scenarios

### scenario.implementation.admitted-work — Every local task is fulfilled

- GIVEN a managed candidate with a current accepted plan and task list for the selected Module
- WHEN the programmer fulfils every local task within the Module's files and returns the complete list
- THEN the Host accepts completion for exactly those tasks, with identities and acceptance unchanged and every task complete
- AND it records the Module's implementation digest in the candidate
- BUT it changes no Spec and does not make the candidate ready

See [preserve task identity and acceptance](#req.implementation.admitted-contract).

### scenario.implementation.native-programmer — The native programmer edits the real candidate

- GIVEN current accepted plan and tasks for a selected Module, and any required review feedback
- WHEN the prepared native programmer uses its write, edit and `run_checks` tools and returns every task complete
- THEN the candidate worktree's files change, not copies in the capsule
- AND completion is accepted after the Host verified the native run and the unchanged inputs

### scenario.implementation.changed-inputs — Changed inputs accept no completion

- GIVEN a programmer run for a current accepted task list
- WHEN the plan, task list, review feedback or Spec changes before the answer is accepted
- THEN the Host accepts no completion
- AND the edits made so far remain in the candidate

### scenario.implementation.missing-tasks — No task list

- GIVEN a managed candidate whose selected target has an accepted plan but no task list
- WHEN the user session requests implementation
- THEN the Host refuses with `missing_tasks` before starting a programmer
- BUT it invents no tasks

### scenario.implementation.incomplete-output — The answer does not complete every task

- GIVEN a programmer run for a current accepted task list
- WHEN its answer omits a local task, changes one, or leaves one incomplete
- THEN the Host reports `incomplete_tasks` instead of accepting completion
- AND the code changes made so far remain in the candidate for inspection
- BUT the candidate does not become ready

### scenario.implementation.failed-execution — A failed run leaves edits and no completion

- GIVEN a programmer run that has made edits in the Module's files
- WHEN the run fails or is cancelled before its answer is accepted
- THEN no task completion is recorded and the edits are not rolled back
- AND the candidate and its recorded progress stay available for inspection
- AND a later attempt admits the current plan, tasks and context afresh in a new run, with no wider permission

### scenario.implementation.caller-components — Component work returns as a typed field

- GIVEN an accepted task list with local tasks and tasks for another Module of the target's change scope, such as the other participant of a contract whose version the change raises
- WHEN implementation finds no current completed work for that component
- THEN it returns outcome `unsupported` with a `components` entry naming the component's target and its derived component task
- BUT it starts no programmer

### scenario.implementation.components-current — Current component work lets the local programmer run

- GIVEN an accepted task list whose component work the user session completed in the same candidate with the derived component task and the owner's constraints
- WHEN `concorde-implement` is requested for the owner again
- THEN the Host finds each component's work complete and current for its Spec and implementation
- AND the programmer runs for the local tasks only
- AND acceptance records the components' revisions

### scenario.implementation.components-only — Only component work needs no programmer

- GIVEN an accepted task list with no local tasks whose component work is complete and current
- WHEN `concorde-implement` is requested for the owner
- THEN the Host records task completion without starting a programmer

### scenario.implementation.components-stale — Changed component work must be completed again

- GIVEN an owner whose component work was completed
- WHEN the component's Spec or code changes before the owner's next implementation run
- THEN `concorde-implement` returns the component again in the `components` field
- BUT the owner's programmer does not start

### scenario.implementation.shared-file — A programmer that may write a shared file is bound to every binder

- GIVEN a selected Module that binds a file another Module also binds
- WHEN the Host prepares the programmer for the selected Module
- THEN the programmer call is bound to both Modules and receives both Spec contexts
- AND its intended write paths are only the selected Module's realization entries
