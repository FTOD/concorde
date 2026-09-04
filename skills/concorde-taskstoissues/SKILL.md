---
name: concorde-taskstoissues
description: "Convert one selected attempt task list into dependency-ordered issues."
scripts:
  py: scripts/workspace.py --phase taskstoissues
---

## User Input

```text
$ARGUMENTS
```

# Convert Concorde Tasks to Issues

## Isolated worktree gate

After applying any Protocol-evolution guard, read-only inspection may remain in the primary
worktree. Before planning, selection persistence, attempt/checklist/reflection creation, an external
mutation, or any other write, unless the maintainer explicitly authorizes primary-worktree mutation
for this request, resolve only the primary worktree's committed `HEAD`, create a unique branch and
linked worktree at that exact commit, and continue the complete request there. If already in an
isolated worktree, stay there and do not create a nested worktree. Treat every staged, unstaged,
untracked, or ignored primary-worktree path as another programmer's state: never use it as input,
stash it, copy it, commit it, reset it, clean it, or otherwise import or alter it. If required input
is absent from committed `HEAD`, stop and report the missing input. `--allow-primary-worktree` is
valid only after an explicit instruction to modify the primary worktree; a generic task request is
not that authorization. A non-Git checkout likewise requires explicit current-directory mutation
authorization.

## Concorde Protocol evolution guard

Before workspace resolution or any external write, if this is the Concorde repository and the task
set changes normative Concorde Protocol semantics, stop without reading an attempt or creating
issues. Report `feature.concorde.evolve-protocol`; one isolated cutover commit, not issue-backed
attempt work, owns that change.

## Workspace gate

Run `{SCRIPT}` first and require Protocol 13. Use the returned selected feature identity,
`feature_path`, `module_architecture`, bounded summaries, `attempt_dir`, `tasks`, `plan`, and
`validation`. Reject a missing or empty task list. Never resolve a root-level copy or inspect another
attempt.

## Conversion

1. Read the task list, plan, and only enough design/architecture context to preserve trace meaning.
2. Group tasks only when they share one independently reviewable outcome and compatible file
   ownership. Preserve stable task IDs, requirement/acceptance traces, exact paths, dependencies,
   `[P]` opportunities, test-first order, and evidence commands.
3. Every issue body states:

   - feature ID and providing module;
   - task IDs and trace tokens;
   - architecture entities/interfaces affected;
   - exact owned paths and non-ownership boundaries;
   - dependency/blocking issues;
   - acceptance checks and evidence expectations; and
   - whether module architecture or feature-file reconciliation is required.

4. Do not copy temporal research logs or reflection entries into issues. Link the selected attempt
   paths when the issue system supports repository links.
5. Do not create issues until the user invocation and available integration clearly authorize the
   external write. When no issue integration is available, return a dependency-ordered issue plan in
   Markdown without mutating local files.
6. Never change task markers, design, architecture, code, tests, validation evidence, or selection.

Report issue identifiers/links when created, otherwise the proposed issue plan, plus task coverage
and dependencies.
