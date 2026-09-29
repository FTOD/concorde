# Decision log: task-less-operations

Goal: Operations without a task (project scope: deterministic or read-only workers), configure_workers as such an Operation, and worker model configuration keyed by Operation and worker role

## Closed: merged, 2026-09-25T03:08:02Z

## Decisions made without the developer (2026-09-25)

- Task-optional Operations: understand, spec_review, code_review (needs --base without a task),
  configure_workers. test, specify, implement, validate and delivery stay task-required.
- A run without a task works on the worktree it was started in (normally the primary), writes no
  task record, admits only --input runs that also had no task, and the host itself refuses
  specify/implement workers (project_scope_write) regardless of the provider.
- configure_workers lives in the Operations package (it needs the catalog to check Operation and
  role names); Workers keeps detection, discovery and the file format and knows no Operation names.
- The `concorde workers` command was removed; configure_workers is the only interface.
- Config schema version 2: default -> operations.<op> -> operations.<op>.roles.<role>; task-type
  keys removed (rapid iteration, no migration). Only spec_review declares two roles today.
- A configure_workers run with --task is recorded in the task record like any run of the task.
