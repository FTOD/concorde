---
name: concorde-taskstoissues
description: "Convert one selected attempt task list into dependency-ordered issues."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-taskstoissues/SKILL.md"
  kind: "skill"
  exposure: "public"
user-invocable: true
disable-model-invocation: false
---
## User Input

```text
$ARGUMENTS
```

# Convert Concorde Tasks to Issues

## Concorde Protocol evolution guard

Before workspace resolution or any external write, if this is the Concorde repository and the task
set changes normative Concorde Protocol semantics, stop without reading an attempt or creating
issues. Report `feature.concorde.evolve-protocol`; one isolated cutover commit, not issue-backed
attempt work, owns that change.

## Workspace gate

Run `python3 scripts/workspace.py --phase taskstoissues` first and require Protocol 13. Use the returned selected feature identity,
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
