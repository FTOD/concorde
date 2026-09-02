---
name: concorde-checklist
description: "Generate a requirements-quality checklist for one direct feature file."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-checklist/SKILL.md"
  kind: "skill"
  exposure: "public"
user-invocable: true
disable-model-invocation: false
---
# Checklist Purpose: Unit Tests for English

Generate a reviewer-owned checklist that evaluates whether the selected feature requirements are
complete, precise, consistent, and reviewable. It does not test product behavior and does not mark
implementation complete.

## Workspace gate

Run `python3 scripts/workspace.py --phase checklist` first and require a successful Protocol 13 workspace. Use the returned
`feature_path`, `module_architecture`, bounded ancestry/related-feature summaries, and exact
`checklists_dir`. Never derive a checklist path from the feature source or read another attempt.

## Workflow

1. Read the feature file and only the architecture sections needed to resolve its interfaces and
   Architecture Zoom. Consider `$ARGUMENTS` as the checklist's focus and risk context.
2. Read `./templates/checklist-template.md` as the checklist format reference.
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
