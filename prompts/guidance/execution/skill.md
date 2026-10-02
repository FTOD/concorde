---
audience: shared
---

## Runs

Two kinds of run work on a workspace, a worktree whose `.concorde/workspace.json` binds it, such as
a task worktree: an **Operation** (`concorde run <operation>`) launches AI workers under a grant;
an **execution command**, such as Method's `concorde task-validation`, `concorde delivery` and
`concorde scaffold` where the method part is installed, is deterministic and launches none. Both
are recorded the same way, and one workspace runs one of them at a time: a second is refused with
`workspace_busy`; started with `--wait <seconds>`, a run waits for the workspace inside its own
process instead. Start each run in background Bash (`run_in_background`), which wakes you when it
ends, since a run may take longer than a foreground Bash call is allowed and a timeout kills it
half done.

Each run prints one JSON run result and saves it in its own folder in the workspace folder its
binding names, for a task's workspace `.concorde/tasks/<task>/workspace/runs/<run-id>/result.json`
of the primary worktree (an unbound run's in `.concorde/unbound/<run-id>/`), where you can read it
too.

## Read results

Exit status 0 means `ok`, 1 means `blocked` or `failed`, 2 means the command line was wrong (the
reason is on standard error). In a result, `host_evidence` holds facts the host observed itself
(grant, audit, checks, rounds); `worker` holds the worker's own claims. Trust evidence over claims.

Every result that is not `ok` carries an **error chain** in `error`. The top link is the
Operation's or the execution command's; below it come the worker run, the worker's own report, the
failing checks, Git or Spec findings, down to where the error started. Read the whole chain before
deciding. Standard error shows the same chain as indented text.

## Unbound runs

Some Operations also run **unbound**, in a worktree without a binding such as the primary
worktree: where the method part is installed, `understand`, `survey`, `spec_review`, `spec_panel`
and `code_review` (a change review with `--base`, a Module review without).
They work on a throwaway checkout of that worktree's `HEAD`, with the Modules you name in
`--modules`, so a task merged there meanwhile does not disturb them and uncommitted changes are not
examined; their result has `workspace` null and names the examined commit as `commit`, and they
change no Spec or code, since an unbound run launches only reading workers. Use
them for a question or a review that does not justify a task, such as understanding a Module before
you agree a change with the developer. An `--input` of such a run must be unbound too.

An unbound run belongs to no task: when one is not `ok`, show the developer its whole error chain
as rendered, from the command's standard error, never a summary of it. When the failure leads to
work and the coordination part is installed, open a task for that work and escalate in it with
`--error-file .concorde/unbound/<run-id>/result.json` (of the primary worktree), which records
the unbound run's chain under your link in the task; `--run` names only runs of the task's own
workspace.
