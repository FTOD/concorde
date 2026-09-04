---
name: concorde-constitution
description: "Create or update the project constitution from provided principles."
---

## User Input

```text
$ARGUMENTS
```

# Maintain the Concorde Project Constitution

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

This leaf Skill is implemented by Concorde and has no Spec Kit runtime dependency.

## Concorde Protocol evolution guard

Before reading templates or writing, if this is the Concorde repository and the requested amendment
changes normative Concorde Protocol semantics, stop without modifying the Constitution. Report
`feature.concorde.evolve-protocol`; that explicitly authorized isolated-worktree cutover reconciles
the Constitution with every other affected authority directly. A governance edit unrelated to
Protocol semantics remains eligible for this Skill.

## Scope guard

Limit this Skill to `.concorde/constitution.md`. Classify feature implementation, refactoring,
building, deployment, or other non-governance requests as deferred intents. Do not execute them.
After the constitution update, report each deferred intent and suggest an appropriate follow-up
Concorde Skill without invoking it.

## Inputs

1. Read `{FRAMEWORK}/templates/constitution-template.md` as the structural reference.
2. If `.concorde/constitution.md` exists, treat it as the maintained authority and preserve still
   applicable project-specific content.
3. Read only the minimum repository documentation needed to resolve missing project facts.
4. Never modify the reference template while using this Skill.

## Workflow

1. Identify every `[ALL_CAPS_IDENTIFIER]` placeholder in the reference or current constitution.
2. Fill values from user input first, then from explicit repository evidence. For genuinely unknown
   governance dates, use `TODO(<FIELD_NAME>): explanation` and disclose it.
3. Apply semantic versioning to `CONSTITUTION_VERSION`:

   - MAJOR for incompatible principle removals or redefinitions;
   - MINOR for a new principle/section or materially expanded governance; and
   - PATCH for non-semantic clarification.

4. Preserve the template's heading hierarchy while adapting the number of principles to the user's
   intent. Make principles declarative, testable, and explicit about rationale.
5. Prepend an HTML-comment Sync Impact Report naming the version change, modified/added/removed
   principles or sections, and any deferred placeholders.
6. Validate that version/report agree, dates use `YYYY-MM-DD`, and no unexplained placeholder remains.
7. Write only `.concorde/constitution.md`.

## Completion report

Report the new version and bump rationale, deferred TODOs, deferred non-governance intents, and a
suggested commit message. Concorde deliberately has no preset, extension-hook, or layered-template
resolution step; the root template is a format reference and the project constitution is authority.
