---
name: speckit-concorde-validate
description: Deterministically validate Concorde architecture sources
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: concorde:commands/speckit.concorde.validate.md
---

# Validate Concorde

Run the installed project-relative launcher with optional target `$ARGUMENTS`:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh validate $ARGUMENTS --format json`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 validate $ARGUMENTS --format json`

Present the canonical status, complete sorted findings, source digest, and summary. Do not hide errors,
modify maintained sources, or reinterpret `unknown` evidence as agreement. Preserve exit codes:
success 0, invalid 1, conflict 2, and failed 3.

Validate feature containment independently from adjacent-module refinement: canonical two-level
paths, unique IDs, bidirectional parent registration, module inheritance, child absence from the
module top-level registry, no cycles, no third level, safe selection, and isolated durable/temporal
roots must all produce actionable containment or layout findings.

Present the document-model rules by their stable IDs. Module summary shape
(`CONCORDE-SUMMARY-001` through `CONCORDE-SUMMARY-004`): `module.md` has the required sections
`Responsibility`, `Boundary`, `Structure`, `Features`, `Contracts`, `Submodules`,
`Representative Scenario`, and `Design Rationale`; `Structure` links at least one of the level's
architecture diagrams under `architecture/diagrams/` or records a leaf rationale; each inventory
section holds a Markdown table or `None.`; and the summary links its adjacent `design.md`. The
reading budget is `CONCORDE-SUMMARY-005`, a WARNING that never changes the status. A missing, empty,
or symlinked module `design.md` is `CONCORDE-MODULE-002`. Module package layout: a diagram under
`architecture/diagrams/` that no `module.md`, `design.md`, or reflection-log link references is
`CONCORDE-VIEW-006`; a Profile 3 remnant (`architecture.json`, `contracts/`, or `modules/` directly
at a module root, or a `view`/`architecture_view` front-matter field) is `CONCORDE-LAYOUT-010`; a
child module not beneath its parent's `architecture/modules/` is `CONCORDE-LAYOUT-011`. Feature-root
trio: a missing feature `implementation.md` is `CONCORDE-LAYOUT-005`, legacy feature-root
`spec.md`/`tldr.md` names are `CONCORDE-LAYOUT-007`, a legacy `implementation/` attempt directory is
`CONCORDE-LAYOUT-008`, and a
missing `abstract.md` is `CONCORDE-LAYOUT-009`. Feature abstract shape (`CONCORDE-ABSTRACT-001` through
`CONCORDE-ABSTRACT-003`): exactly the sections `Purpose`, `Functionality`, `Structure`, `Logic`, and
`Read Next` in order; `Structure` links a maintained diagram, a level view under the module's
`architecture/diagrams/`, or a delivered architecture view, or contains a ```text sketch; and `Logic` cites only `FR-NNN` identifiers defined
in the adjacent `design.md` (and at least one when the design defines any). The abstract reading budget
(3,000 body words) is `CONCORDE-ABSTRACT-004`, a WARNING that never changes the status. Project
reflection log (`reflections.md` directly inside the specification root; absent is not a breach):
`CONCORDE-REFLECT-001` for an entry heading that is not `### R-NNN · title` or a missing or empty
required field, `CONCORDE-REFLECT-002` for a duplicate identifier, `CONCORDE-REFLECT-003` for a
`Kind`, `Effect`, `Status`, or `Phase` outside the fixed vocabularies or a non-open status without a
`Note`, and `CONCORDE-REFLECT-004` for a `Feature` that is not a known feature or a `Concerns` that
is neither a known stable ID nor an existing project-relative path.