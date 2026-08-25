---
description: Harden a completed Concorde implementation attempt into the durable feature design.
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Compact the selected feature's completed implementation attempt into its permanent `design.md`, then
remove the temporal `implementation/` directory. This is an explicit milestone operation. Checked
tasks and every existing item under `implementation/checklists/` establish eligibility; they do not
grant approval.

## Workflow

1. From the target project root, invoke
   `.specify/extensions/concorde/scripts/bash/concorde.sh feature harden --propose` (or the installed
   PowerShell launcher on PowerShell projects). Pass a user-supplied stable feature ID or canonical
   feature-root path before `--propose`; otherwise use the selected feature.
2. Read the returned `proposal_path`, `task_summary`, and `checklist_summary` directly. Stop on any
   status other than `eligible` and present every finding. Never repair, check off, delete, or
   reinterpret tasks or `implementation/checklists/*.md` merely to make the feature eligible.
3. Read only the returned feature root, its `spec.md` and current `design.md`, relevant maintained
   architecture/contracts, every artifact under its `implementation/` directory, and the code/tests
   cited by those sources. Draft a complete current feature design with these exact sections:
   `Realization Overview`, `Module and Feature Collaboration`, `Scenario Realization`,
   `Durable Implementation Decisions`, `Traceability and Evidence`, and `Known Limitations`.
4. Keep the design feature-oriented: explain how related modules/features and their contracts realize
   the feature. Reference module architecture instead of redefining module responsibilities,
   boundaries, contracts, or one-level organization. Retain durable decisions and useful evidence
   links; omit transient task ordering, discarded alternatives, and raw validation logs.
5. Write the candidate to the exact project-contained `proposal_path` returned by the runtime. The JSON
   must conform to the installed Feature Workspace Protocol and contain:
   - `proposal_version: 1` and `operation: "feature.harden"`;
   - the resolved stable feature ID as `target`;
   - the exact returned `source_digest`;
   - `design.path` equal to the returned `workspace.feature_design` and `design.content` equal to the
     complete candidate Markdown; and
   - `remove` containing exactly the returned `workspace.implementation_dir`.
6. Present the entire candidate design, exact removal target, and retained `spec.md`, architecture,
   code, and test authorities. Ask for explicit approval of this exact proposal. Do not treat silence,
   prior milestone acceptance, passing validation, or checked tasks as approval.
7. Only after approval, invoke the same installed launcher with
   `feature harden --apply --proposal <returned-project-relative-proposal-path>`. Present the complete
   normative result, including stale-digest conflicts, warnings, removed artifacts, and design
   digests.

## Safety Invariants

- Do not edit `design.md` directly; only the approved runtime apply promotes the candidate.
- Do not remove individual implementation files, keep a second archived attempt below the feature
  root, or target any path outside the selected feature.
- Do not modify `spec.md`, module architecture, code, tests, or generated projections during
  hardening.
- On any conflict or failure, stop and preserve the proposal for review. Never retry apply against a
  changed digest without regenerating and re-presenting the proposal.

## Completion Report

Report the feature ID, durable design path, resulting design digest, removed implementation artifact
count, retained authorities, findings, and whether the feature now has no active implementation
workspace.
