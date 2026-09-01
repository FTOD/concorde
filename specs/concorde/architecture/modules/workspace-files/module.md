---
id: module.concorde.workspace-files
kind: module
parent: module.concorde
children: []
features:
  - feature.workspace-files.manage-feature-workspace
contracts:
  provided:
    - contract.workspace-files.feature-workspace
    - contract.workspace-files.records
  required: []
---

# Workspace Files

## Responsibility

Define the project files through which Concorde preserves durable intent, current-attempt memory,
selection state, accepted implementation, and workflow reflections.

## Boundary

Workspace Files owns path grammar, file roles, lifetime classes, registration relationships, and
promotion rules. It does not own the coding agent that authors content, the scripts that parse or
validate it, or generated documentation views.

## Structure

Durable files live at the specification root, module roots, and feature roots. Temporal files live
only beneath a selected feature's `attempt/` directory. `.specify/feature.json` holds the current
selection. Generated artifacts are projections and are never accepted back as source.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.workspace-files.manage-feature-workspace` | Skills and Scripts can locate one registered feature workspace, distinguish durable records from temporal attempt memory, and promote an explicitly accepted implementation without ambiguous aliases. | `feature.concorde.workflow`, `feature.concorde.record-workflow-reflections`, `feature.concorde.publish-project-docsite` | [design.md](features/001-manage-feature-workspace/design.md) |

## Contracts

| Contract ID | Role | Counterparty |
|---|---|---|
| `contract.workspace-files.feature-workspace` | provided | Skills, Scripts, Spec Kit lifecycle |
| `contract.workspace-files.records` | provided | Skills, Scripts, and Auto-Docs |

## Submodules

None.

## Representative Scenario

A plan skill resolves `.specify/feature.json`, reads the selected feature's durable `abstract.md` and
`design.md`, and writes `attempt/plan.md`. Later, explicit delivery replaces the durable
`implementation.md` with the invocation-authorized realization and removes only that feature's completed
`attempt/` directory.

## Design Rationale

Files are architectural state, not incidental storage. Making their lifetimes explicit prevents
temporary reasoning from being mistaken for accepted design and prevents generated views from
becoming authorities. The complete file matrix is in the [design reference](design.md).
