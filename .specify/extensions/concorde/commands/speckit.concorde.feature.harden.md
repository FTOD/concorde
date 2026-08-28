---
description: Harden a completed Concorde implementation attempt into the durable feature implementation.
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Compact the selected feature or immediate sub-feature's completed implementation attempt into its permanent `implementation.md`, then
remove the temporal `implementation/` directory. The first accepted milestone writes
`implementation.md` in full; each later milestone completes it. When the attempt produced
implementation detail or rationale worth keeping, the same reviewed proposal may amend the providing
module's `design.md`. This is an explicit milestone operation. Checked
tasks and every existing item under `implementation/checklists/` establish eligibility; they do not
grant approval.

Protocol v4 classifies the selected lifecycle root. For a sub-feature, parent durable paths and
sibling summaries are read-only retained authorities. Apply may update only the selected child's
`implementation.md`, optionally the providing module's `design.md`, and remove only that child's
complete `implementation/`; parent, siblings, their attempts, and every `module.md` remain
byte-identical.

## Workflow

1. From the target project root, invoke
   `.specify/extensions/concorde/scripts/bash/concorde.sh feature harden --propose` (or the installed
   PowerShell launcher on PowerShell projects). Pass a user-supplied stable feature ID or canonical
   feature-root path before `--propose`; otherwise use the selected feature.
2. Read the returned `proposal_path`, `task_summary`, and `checklist_summary` directly. Stop on any
   status other than `eligible` and present every finding. Never repair, check off, delete, or
   reinterpret tasks or `implementation/checklists/*.md` merely to make the feature eligible. An
   eligible result also exposes `workspace.feature_implementation`, `workspace.module_summary`,
   `workspace.module_design`, and a `source_digest` that covers the current module `design.md`; never
   derive or guess those paths.
3. Read only the returned feature root, its `spec.md` and current `implementation.md`, the providing
   module's `module.md` and current `design.md`, relevant maintained
   architecture/contracts, every artifact under its `implementation/` directory, and the code/tests
   cited by those sources. Draft a complete current `implementation.md` with these exact sections:
   `Realization Overview`, `Module and Feature Collaboration`, `Scenario Realization`,
   `Durable Implementation Decisions`, `Traceability and Evidence`, and `Known Limitations`.
4. Keep the realization feature-oriented: explain how related modules/features and their contracts realize
   the feature. Reference module architecture instead of redefining module responsibilities,
   boundaries, contracts, or one-level organization. Retain durable decisions and useful evidence
   links; omit transient task ordering and raw validation logs. Alternatives and module-level
   rationale belong in the module `design.md` amendment, not here.
5. When the attempt produced implementation detail, rationale, alternatives, or decisions worth
   keeping at module level, draft a FULL replacement of the providing module's `design.md` (its path
   is `workspace.module_design`). Add that material under the reference's stable headings
   (`Implementation Notes`, `Design Rationale`, `Alternatives Considered`, `Decision Log`), keep
   everything already recorded, and do not restate facts owned by `module.md`, the level view, or
   contracts. Skip the amendment when nothing module-level was learned.
6. Write the candidate to the exact project-contained `proposal_path` returned by the runtime. The JSON
   must conform to the installed Feature Workspace Protocol and contain:
   - `proposal_version: 2` and `operation: "feature.harden"`;
   - the resolved stable feature ID as `target`;
   - the exact returned `source_digest`;
   - `implementation.path` equal to the returned `workspace.feature_implementation` and
     `implementation.content` equal to the complete candidate Markdown;
   - optionally `module_design.path` equal to the returned `workspace.module_design` and
     `module_design.content` equal to the complete replacement Markdown; and
   - `remove` containing exactly the returned `workspace.implementation_dir`.
7. BEFORE asking for approval, present the entire candidate `implementation.md`, the `design.md`
   amendment shown as a DIFF against the current reference (or state that none is proposed), the
   exact cleanup manifest (the removal target), and the retained `spec.md`, `module.md`,
   architecture, code, and test authorities. Ask for explicit approval of this exact proposal.
   Silence is not approval; neither are prior milestone acceptance, passing validation, or checked
   tasks and checklists.
8. Only after the maintainer's explicit yes, invoke the same installed launcher with
   `feature harden --apply --proposal <returned-project-relative-proposal-path>`. Never invoke
   `--apply` without that yes. Present the complete
   normative result, including stale-digest conflicts, warnings, removed artifacts, and the
   implementation and module-design digests.

## Safety Invariants

- Do not edit `implementation.md` or any module `design.md` directly; only the approved runtime
  apply promotes the candidate and its amendment atomically.
- Do not remove individual implementation files, keep a second archived attempt below the selected
  root, or target a parent, sibling, child, or any path outside the selected lifecycle root.
- Do not modify `spec.md`, `module.md`, module architecture, code, tests, or generated projections
  during hardening. Never create or amend a feature-root `design.md`.
- On any conflict or failure, stop and preserve the proposal for review. Never retry apply against a
  changed digest without regenerating and re-presenting the proposal.
- Apply rejects, and you must never propose, an amendment targeting `module.md`, another level's
  `design.md`, or a feature-root `design.md`. It also rejects a proposal whose digest is stale
  because the module `design.md` changed after proposal mode.

## Completion Report

Report the feature ID, durable implementation path, prior and resulting implementation digests, prior
and resulting module design digests (null when not amended), removed implementation artifact
count, retained authorities, findings, and whether the feature now has no active implementation
workspace.
