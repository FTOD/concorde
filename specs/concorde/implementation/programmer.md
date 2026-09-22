# Programmer admission and completion

The exact mechanics behind the [Implementation entry](module.md): what the Host checks before the
programmer starts, what the programmer receives, how its answer is accepted, and the Module-wide
obligations of Implementation.

## Admission

Preparing `concorde-implement` runs, in order:

1. The required Spec review check: refused with `review_required` when the candidate requires a
   Spec review of the Module and none is current.
2. The gap check: a gap still recorded, unchanged, for the implementation step returns
   `spec_incomplete` without starting a model.
3. The candidate check: `missing_change` without a managed candidate; `stale_context` when the
   Module's Spec revision differs from the plan's; `incompatible_handoff` when the request's task or
   constraints differ from the plan's; `missing_tasks` when the task list is empty.
4. The task split: every task must target the Module, a Module it uses or a direct child, else
   `permission_denied`. Tasks for other Modules are grouped by target into component work.
5. The component check: for each component, the change record must hold that component's work with
   the task text derived from its tasks, the same constraints, the component's current Spec
   revision, a nonempty all-complete task list and the component's current implementation digest.
   Otherwise the answer is `unsupported`, listing each component as `{"target_id", "task"}`.
6. The project check: the whole project's Specs must validate, else `incompatible_contracts`.
7. The binding check: local tasks with no implementation files bound by the Module give
   `unsupported_target`.

The derived task text of a component is its tasks' descriptions, each followed by
`Acceptance:` and its acceptance condition, separated by blank lines. When there are no local tasks
and every component is current, the Host records completion at once without a programmer.

## What the programmer receives

The programmer's inputs are the accepted plan and the local tasks as one
`concorde-implementation-task` value, plus, after a review repair, the verified review result and
the context of the Issues it cites. The capsule index adds:

- `native_workspace`: the absolute path of the candidate worktree;
- `intended_write_paths`: the absolute paths of the Module's realization entries;
- `file_scope_enforcement: "prompt-level"` and a note that network and credential use are limited
  by instruction, not by the operating system.

The programmer has no delegation tools. Its `run_checks` tool takes no arguments and runs the
Module's configured checks through the Host's check service, with a timeout derived from the
configured check timeouts.

## Acceptance

The Host first applies the checks of every native step: the run completed without interruption,
the proposal was submitted through the capture extension for this invocation and matches the
programmer's output schema, and the prepared inputs are unchanged. For the programmer, the Module's
implementation files may change during the run, while the Spec, registry, configuration, plan,
tasks and review feedback must stay as prepared. The review feedback is checked before the run and
taken as fixed afterwards.

The answer's `tasks` must equal the local tasks exactly, each with `complete: true`. Every
realization entry that is not pending must exist. Otherwise the answer is `incomplete_tasks`.

On acceptance the Host marks every task of the list complete, stores the Module's
`implementation_digest`, empties `checks`, drops the repair review, records component revisions
when there was component work, and sets `phase: implementation` and `status: completed`.

## Requirements

### req.implementation.admitted-contract — Preserve task identity and acceptance

Implementation SHALL accept completion only for the exact admitted local tasks, with their identity, target, description and acceptance unchanged.

### req.implementation.write-scope — Only the Module's own files

Implementation SHALL name only the selected Module's realization entries as the programmer's intended write paths.

### req.implementation.components-return — Component work goes back to the caller

Implementation SHALL return component work that lacks current completed evidence to the caller instead of starting any worker for it.

### req.implementation.materialized-files — Listed files exist

Implementation SHALL refuse completion while a non-pending file that the Module's realizations list does not exist.

### req.implementation.no-readiness — Completion is not readiness

Accepting task completion SHALL NOT run checks or reviews, make the candidate ready, or deliver it.
