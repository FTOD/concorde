---
id: module.concorde.skills
kind: module
parent: module.concorde
children: []
features:
  - feature.skills.compose-workflow
contracts:
  provided:
    - contract.skills.agent-surface
    - contract.skills.workflow-guidance
  required:
    - contract.skills.spec-kit-host
    - contract.skills.script-operations
    - contract.skills.workspace-files
---

# Skills

## Responsibility

Present every user-visible Concorde workflow as coding-agent instructions and compose those
instructions into Spec Kit's normal feature lifecycle.

## Boundary

Skills owns command prose, phase guidance, template composition, and the mapping from user intent to
named script operations and workspace files. It does not own deterministic operation semantics,
workspace file formats, coding-agent behavior, or Spec Kit internals.

## Structure

This leaf module is implemented by the command and template sources under `presets/concorde-core/`
and `extensions/concorde/commands/`. Spec Kit materializes those sources into agent-native skills or
slash commands. There is deliberately no second UI.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.skills.compose-workflow` | A maintainer can invoke the normal and Concorde-specific skills with consistent workspace routing, file guidance, approval gates, and result presentation. | `feature.concorde.workflow`, `feature.concorde.record-workflow-reflections`, `feature.concorde.install-with-spec-kit` | [design.md](features/001-compose-workflow/design.md) |

## Contracts

| Contract ID | Role | Counterparty |
|---|---|---|
| `contract.skills.agent-surface` | provided | Supported coding-agent integration and maintainer |
| `contract.skills.workflow-guidance` | provided | Spec Kit lifecycle commands |
| `contract.skills.spec-kit-host` | required | Spec Kit |
| `contract.skills.script-operations` | required | Scripts |
| `contract.skills.workspace-files` | required | Workspace Files |

## Submodules

None.

## Representative Scenario

A maintainer invokes a plan skill. The skill resolves the selected feature, names the durable design
files and temporal `attempt/plan.md` target, requests bounded context through Scripts when needed,
and instructs the coding agent to write the plan. The skill presents structured findings but never
reimplements the script or file rules.

## Design Rationale

Skills are a first-class module because they are the product surface the user actually sees. The
package source and installed materialization are kept distinct in the [design reference](design.md).
