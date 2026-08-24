---
name: "speckit-concorde-feature-harden"
description: "Harden a completed Concorde implementation attempt into durable design after explicit review and approval."
metadata:
  author: "concorde"
  source: "extensions/concorde/commands/speckit.concorde.feature.harden.md"
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Compact the selected feature's completed implementation attempt into its permanent `design.md`, then
remove the temporal `implementation/` directory. This is an explicit milestone operation. Checked
tasks establish eligibility; they do not grant approval.

## Workflow

1. From the target project root, invoke
   `.specify/extensions/concorde/scripts/bash/concorde.sh feature harden --propose` (or the installed
   PowerShell launcher on PowerShell projects). Pass a user-supplied stable feature ID or canonical
   feature-root path before `--propose`; otherwise use the selected feature.
2. Stop on any status other than `eligible`. Present every finding. Never repair, check off, delete,
   or reinterpret tasks merely to make the feature eligible.
3. Read only the returned feature root, its `spec.md` and current `design.md`, relevant maintained
   architecture/contracts, every artifact under its `implementation/` directory, and the code/tests
   cited by those sources. Draft a complete current feature design with these exact sections:
   `Realization Overview`, `Module and Feature Collaboration`, `Scenario Realization`,
   `Durable Implementation Decisions`, `Traceability and Evidence`, and `Known Limitations`.
4. Keep the design feature-oriented: explain how related modules/features and their contracts realize
   the feature. Reference module architecture instead of redefining module responsibilities,
   boundaries, contracts, or one-level organization. Retain durable decisions and useful evidence
   links; omit transient task ordering, discarded alternatives, and raw validation logs.
5. Write the candidate to the exact project-contained proposal path returned by the runtime. The JSON
   must conform to the installed Feature Workspace Protocol and contain the returned target, source
   digest, durable design path/content, and exactly one implementation-directory removal target.
6. Present the entire candidate design, exact removal target, and retained authorities. Ask for
   explicit approval of this exact proposal. Silence, checked tasks, passing validation, or prior
   milestone acceptance are not approval.
7. Only after approval, invoke the same installed launcher with
   `feature harden --apply --proposal <returned-project-relative-proposal-path>`. Present the complete
   normative result, including stale-digest conflicts, warnings, removed artifacts, and design
   digests.

## Safety Invariants

- Do not edit `design.md` directly; only the approved runtime apply promotes the candidate.
- Do not remove individual implementation files, keep an archived attempt below the feature root, or
  target any path outside the selected feature.
- Do not modify `spec.md`, module architecture, code, tests, or generated projections during hardening.
- On conflict or failure, stop. Never retry apply against changed sources without regenerating and
  re-presenting the proposal.

## Completion Report

Report the feature ID, durable design path, resulting design digest, removed artifact count, retained
authorities, findings, and whether the feature now has no active implementation workspace.
