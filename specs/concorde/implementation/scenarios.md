# Implementation scenarios

Concrete situations for `concorde-implement` in the [Implementation Module](module.md). The
Module-wide obligations and the exact checks are in
[programmer admission and completion](programmer.md).

## Normal completion

### scenario.implementation.admitted-work — Every local task is fulfilled

- GIVEN a managed candidate with a current accepted plan and task list for the selected Module
- WHEN the programmer fulfils every local task within the Module's files and returns the complete list
- THEN the Host accepts completion for exactly those tasks, with identities and acceptance unchanged and every task complete
- AND it records the Module's implementation digest in the candidate
- BUT it changes no Spec and does not make the candidate ready

See [preserve task identity and acceptance](programmer.md#req.implementation.admitted-contract).

### scenario.implementation.native-programmer — The native programmer edits the real candidate

- GIVEN current accepted plan and tasks, and any required review feedback and component work, for a selected Module
- WHEN the prepared native programmer uses its write, edit and `run_checks` tools
- THEN the candidate worktree's files change, not copies in the capsule
- AND completion is accepted only after the Host verified the native run and the unchanged inputs
- BUT an incomplete, malformed or foreign answer, a failed or cancelled run, or a changed plan, task list, feedback or Spec accepts no completion, and the edits made so far remain in the candidate

## Refusals

### scenario.implementation.missing-tasks — No task list

- GIVEN a managed candidate whose selected target has an accepted plan but no task list
- WHEN the user session requests implementation
- THEN the Host refuses with `missing_tasks` before starting a programmer
- BUT it invents no tasks and grants no write access for the request

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

## Component work

### scenario.implementation.caller-components — Component work returns to the user session

- GIVEN an accepted task list with local tasks and tasks for another Module of the target's change scope, such as the other participant of a contract whose version the change raises
- WHEN implementation finds no current completed work for that component
- THEN it returns `unsupported` with the component's target and derived task text, without starting any programmer
- AND after the user session completes that work for the component, a retry checks its task text, constraints, completion and current Spec and implementation before the local programmer starts
- AND the component's programmer receives only the component's own files, in the same candidate
- BUT after a later change to the component's Spec or code, its work must be completed again before the parent's next run

### scenario.implementation.component-stale-parent — Component work needs the parent's current plan

- GIVEN the user session requests component work derived from a parent's accepted plan and tasks
- WHEN the parent's Spec has changed since its plan, or the request's task or constraints differ from the derived work
- THEN the request is refused before any component worker starts or any recorded work changes
- AND the user session must plan the parent again before retrying
