---
name: concorde-clarify
description: "Clarify underspecified behavior in one direct feature file."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-clarify/SKILL.md"
  kind: "skill"
  exposure: "public"
---
## User Input

```text
$ARGUMENTS
```

# Clarify a Concorde Feature

Clarification resolves material ambiguity in the selected feature's direct Markdown file. It does not
invent architecture, inspect unrelated attempts, or write code.

## Workspace gate

Run `python3 scripts/workspace.py --phase clarify` first. Require Protocol 13 and `resolved`/`selected` status. Use only the returned
`feature_path`, `module_architecture`, `feature_id`, `providing_module`, bounded
`module_ancestry`, bounded `related_features`, `checklists_dir`, and process paths. Treat ancestry and
related-feature summaries as navigation; open a related design only when the ambiguity directly
concerns that feature's declared interface.

## Clarification workflow

1. Read the complete selected feature file and the providing module architecture sections that define
   referenced entities, relationships, interactions, and feature inventory.
2. Build an internal coverage map for outcome/scope, consumers, successful usage, edge/failure
   behavior, interface shapes and obligations, compatibility, architecture entity references,
   related-feature semantics (each entry's typed relation and its explanation), requirements,
   assumptions, and measurable evidence.
3. Rank gaps by implementation or validation risk. Ask at most five concise questions, one at a
   time, each with a recommended answer or a short constrained choice. Do not ask stylistic or
   already-resolved questions.
4. After each answer, update the owning section of the file at `feature_path` immediately. Preserve stable IDs and
   unrelated text. If an answer changes an interface, reconcile front matter, the full embedded
   interface definition, usage/failures, requirements, and Architecture Zoom together.
5. If an answer reveals that an entity's identity/type/ownership or a module relationship must
   change, do not redefine it in the feature. Report the exact module architecture reconciliation
   required and keep the feature reference consistent with current architecture until that change is
   reviewed.
6. Re-evaluate the existing built-in requirements checklist at the returned path when present. Do
   not alter reviewer-owned custom checklist judgments.

## Completion gate

Verify all edited interface IDs and architecture references resolve, no placeholder or clarification
marker remains for the answered areas, the representative usage still follows the interface, and
only the selected feature file plus permitted built-in checklist state changed. Run deterministic Concorde
validation for the selected feature when available.

Concorde has no extension-hook phase. Complete only the selected feature clarification and its
requirements checklist, then report the changed authorities.

Report questions answered, sections changed, remaining deferred ambiguities, architecture follow-up,
checklist state, and validation result.
