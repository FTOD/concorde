---
audience: shared
---

## Runs

Two kinds of run work on a workspace. A workspace is a worktree whose `.concorde/workspace.json`
binds it, such as a task worktree. An **Operation** (`concorde run <operation>`) launches AI workers
under a grant. An **execution command** is deterministic. It launches none. Where the method part
is installed, Method's execution commands include these examples:

- `concorde task-validation`
- `concorde delivery`
- `concorde scaffold`

Both kinds of run are recorded the same way. One workspace runs one of them at a time. A second
run is refused with `workspace_busy`. When started with `--wait <seconds>`, a run waits for the
workspace inside its own process instead. A run may take longer than a foreground Bash call is
allowed. A timeout kills it half done. So start each run in background Bash
(`run_in_background`). Background Bash wakes you when the run ends.

Each run prints one JSON run result. The run saves the result in its own folder in the workspace
folder its binding names. For a task's workspace, the result is at
`.concorde/tasks/<task>/workspace/runs/<run-id>/result.json` of the primary worktree. An unbound
run's result is in `.concorde/unbound/<run-id>/`. You can read the result there too.

## Read results

Exit statuses have these meanings:

- 0 means `ok`.
- 1 means `blocked` or `failed`.
- 2 means the command line was wrong (the reason is on standard error).

In a result, `host_evidence` holds facts the host observed itself. These facts cover the following:

- grant
- audit
- checks
- rounds

The `worker` field holds the worker's own claims. Trust evidence over claims.

When a result is not `ok`, it carries an **error chain** in `error`. The top link is the
Operation's or the execution command's. Below it, the chain includes these links, down to where
the error started:

- the worker run
- the worker's own report
- the failing checks
- Git or Spec findings

Read the whole chain before deciding. Standard error shows the same chain as indented text.

## Unbound runs

Where the method part is installed, some Operations also run **unbound**, in a worktree without a
binding such as the primary worktree. These Operations are:

- `understand`
- `survey`
- `spec_review`
- `spec_panel`
- `code_review` (a change review with `--base`, a Module review without)

They work on a throwaway checkout of that worktree's `HEAD`, with the Modules you name in
`--modules`. A task merged there meanwhile therefore does not disturb them. They do not examine
uncommitted changes. Their result has `workspace` null. The result names the examined commit as
`commit`. Since an unbound run launches only reading workers, these Operations change no Spec or
code. For a question or a review that does not justify a task, use these Operations. Understanding
a Module before you agree a change with the developer is one example. An `--input` of such a run
must be unbound too.

An unbound run belongs to no task. When an unbound run is not `ok`, show the developer its whole
error chain as rendered, from the command's standard error, never a summary of it. When the failure
leads to work and the coordination part is installed, open a task for that work. Under the same
conditions, escalate in that task with
`--error-file .concorde/unbound/<run-id>/result.json` (of the primary worktree). This records the
unbound run's chain under your link in the task. The `--run` option names only runs of the task's
own workspace.
