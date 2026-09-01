---
name: speckit-clarify
description: Clarify underspecified behavior in one direct feature file.
argument-hint: "Optional areas to clarify in the spec"
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:concorde
user-invocable: true
disable-model-invocation: false
---

# Speckit Clarify Skill

## User Input

```text
$ARGUMENTS
```

# Clarify a Concorde Feature

Clarification resolves material ambiguity in the selected feature's direct Markdown file. It does not
invent architecture, inspect unrelated attempts, or write code.

## Workspace gate

Run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase clarify` first. Require Protocol 12 and `resolved`/`selected` status. Use only the returned
`feature_path`, `module_architecture`, `feature_id`, `providing_module`, bounded
`module_ancestry`, bounded `related_features`, `checklists_dir`, and process paths. Treat ancestry and
related-feature summaries as navigation; open a related design only when the ambiguity directly
concerns that feature's declared interface.

## Clarification workflow

1. Read the complete selected feature file and the providing module architecture sections that define
   referenced entities, relationships, interactions, and feature inventory.
2. Build an internal coverage map for outcome/scope, consumers, successful usage, edge/failure
   behavior, interface shapes and obligations, compatibility, architecture entity references,
   related-feature semantics, requirements, assumptions, and measurable evidence.
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

Process enabled unconditional `after_clarify` hooks from `.specify/extensions.yml`; mandatory hooks
run and gate completion, optional hooks are presented, and conditional hooks are left to the hook
executor.

Report questions answered, sections changed, remaining deferred ambiguities, architecture follow-up,
checklist state, and validation result.
