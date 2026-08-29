---
id: module.concorde.scripts
kind: module
parent: module.concorde
children: []
features:
  - feature.scripts.run-workflow-operations
contracts:
  provided:
    - contract.scripts.operations
  required:
    - contract.scripts.workspace-files
---

# Scripts

## Responsibility

Execute portable workspace routing and deterministic Concorde operations over project files and
return complete structured results to Skills.

## Boundary

Scripts owns launchers, CLI parsing, repository-safe path resolution, initialization proposals,
bounded context, validation, readiness, reflection diagnostics, and implementation acceptance. It
does not own user-facing guidance, agent-authored prose, file-lifetime policy, package installation,
or documentation presentation.

## Structure

This leaf module maps directly to `extensions/concorde/scripts/` and
`extensions/concorde/runtime/concorde/`. The portable shell and PowerShell launchers select Python;
the Python adapters invoke the standard-library runtime. All reads and writes cross the Workspace
Files contract.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.scripts.run-workflow-operations` | Skills can resolve a selected workspace and invoke init, context, validate, readiness, reflection, or acceptance behavior with deterministic structured results. | `feature.concorde.workflow`, `feature.concorde.self-host-framework`, `feature.concorde.record-workflow-reflections` | [design.md](features/001-run-workflow-operations/design.md) |

## Contracts

| Contract ID | Role | Counterparty |
|---|---|---|
| `contract.scripts.operations` | provided | Skills and Documentation |
| `contract.scripts.workspace-files` | required | Workspace Files |

## Submodules

None.

## Representative Scenario

An installed validation skill invokes a portable launcher. Scripts discover the project root, parse
the maintained workspace files, run every deterministic rule, and return a versioned structured
result. They do not edit invalid sources or decide what the maintainer meant.

## Design Rationale

“Scripts” is intentionally concrete: this module is executable support for skills, not an abstract
architecture authority. Protocol and source mapping details are in the
[design reference](design.md).
