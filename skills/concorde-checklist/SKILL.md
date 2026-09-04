---
name: concorde-checklist
description: "Generate a requirements-quality checklist for one direct feature file."
scripts:
  py: scripts/workspace.py --phase checklist
---

# Checklist Purpose: Unit Tests for English

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

Generate a reviewer-owned checklist that evaluates whether the selected feature requirements are
complete, precise, consistent, and reviewable. It does not test product behavior and does not mark
implementation complete.

## Concorde Protocol evolution guard

Before workspace resolution, if this is the Concorde repository and the request belongs to a
normative Concorde Protocol semantic change, stop without creating checklist or attempt state. Name
`feature.concorde.evolve-protocol`; its isolated-worktree cutover uses Git review and target
validation rather than a temporal Concorde checklist.

## Workspace gate

Run `{SCRIPT}` first and require a successful Protocol 13 workspace. Use the returned
`feature_path`, `module_architecture`, bounded ancestry/related-feature summaries, and exact
`checklists_dir`. Never derive a checklist path from the feature source or read another attempt.

## Workflow

1. Read the feature file and only the architecture sections needed to resolve its interfaces and
   Architecture Zoom. Consider `$ARGUMENTS` as the checklist's focus and risk context.
2. Read `{FRAMEWORK}/templates/checklist-template.md` as the checklist format reference.
3. Choose a short descriptive filename under the returned `checklists_dir`; never overwrite another
   reviewer checklist unless the user explicitly names it for revision.
4. Write 10–20 questions about requirement quality, not runtime outcomes. Cover where relevant:

   - outcome and scope boundaries;
   - successful, edge, and failure usage;
   - interface consumers/direction, entry points, shapes, obligations, failures, compatibility, and
     implementing entity references;
   - Architecture Zoom resolution and non-redefinition;
   - related-feature semantics and cross-module boundaries;
   - testability, measurable evidence, assumptions, and ambiguity; and
   - consistency between front matter, interfaces, scenarios, requirements, and success criteria.

5. Each item cites a design section or uses `[Gap]`, `[Ambiguity]`, `[Conflict]`, or `[Assumption]`.
   Avoid questions answerable only by executing code.
6. Leave all new items unchecked. `[x]` means a reviewer judged the requirement-quality criterion
   satisfied; it never means implementation work is done.

## Report

Return the checklist path, item count, focus areas, and reminder that the checklist is reviewer-owned.
This phase changes no feature file, module architecture, code, tests, or selection state.
