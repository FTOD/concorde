---
id: feature.skills.compose-workflow
kind: feature
module: module.concorde.skills
refines:
  - feature.concorde.workflow
  - feature.concorde.record-workflow-reflections
  - feature.concorde.install-with-spec-kit
  - feature.concorde.self-host-framework
scenarios:
  - scenario.skills.compose-and-register
contracts:
  provided:
    - contract.skills.workflow-guidance
    - contract.skills.agent-surface
  required:
    - contract.skills.spec-kit-host
    - contract.skills.script-operations
    - contract.skills.workspace-files
evidence_status: verified
canonical_design: specs/concorde/architecture/modules/skills/features/001-compose-workflow/design.md
---

# Compose Workflow Skills

**Status**: Implemented and verified

## Outcome

A supported Spec Kit project exposes one coherent set of coding-agent skills whose instructions
route every phase to the selected workspace, preserve durable and temporal file boundaries, invoke
deterministic Scripts operations when required, and present approval gates without ambiguity.

## Representative Scenario

`scenario.skills.compose-and-register` starts with the bundle installing the preset and extension.
Spec Kit composes the normal phase commands, registers the Concorde-specific commands, and
materializes both in the active coding-agent integration. A maintainer invokes a plan skill, which
resolves the selected workspace, names `design.md` and `attempt/plan.md`, and requests bounded context
through Scripts before the agent authors the plan.

## Diagram Decision

The root [level view](../../../../diagrams/level-view.json) owns the skill-to-script-to-file
interaction. The installation feature diagrams own package composition. A child diagram would
duplicate those two established views.

## Requirements

- Installed skills MUST be the only user-facing interface for feature work.
- Every path-sensitive normal phase MUST resolve the selected workspace before inherited steps use a path.
- Every skill MUST identify permitted reads, writes, and required script operations.
- Durable intent MUST resolve at the feature root; temporal delivery memory MUST resolve beneath `attempt/`.
- The five Concorde-specific skills MUST preserve intent across supported agent presentations.
- `speckit.concorde.ask` MUST remain read-only and agent-followed, with no runtime subcommand.
- Structured script findings MUST be shown completely; skills MUST NOT infer approval or silently repair sources.
- Release-installed and self-hosted materializations MUST use the same maintained command sources.
