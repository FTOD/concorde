---
id: feature.understanding.initialize-architecture
kind: feature
module: module.concorde.understanding
related_features:
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.concorde.define-project-ontology
    relation: depends_on
interfaces:
  provided:
    - interface.concorde.initialize
  required:
    - contract.capabilities.operation-data
---

# Feature Design: Initialize Architecture

## Outcome and Scope

A maintainer can inspect and explicitly apply a minimal Profile 7 root architecture/control-state scaffold without scripts
inventing product structure or overwriting an existing configured hierarchy.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.understanding.init-skill` | Requests the reviewed initialize propose/apply Tool action. |
| `entity.understanding.initializer` | Generates, validates, and atomically promotes the root `architecture.md` proposal. |
| `module.concorde.capabilities` | Dispatches the initialize Tool through the shared CLI and Tool envelope. |
| `entity.concorde.specification` | Receives the root architecture scaffold only. |
| `entity.concorde.control-state` | Receives Profile 7 configuration with typed Operation settings, reflection defaults, and allocation index. |

## Interfaces

### `interface.concorde.initialize` — Initialize root architecture

- **Consumer**: Maintainer establishing Concorde in a project.
- **Direction**: Skill/Tool request to reviewed proposal or apply result.
- **Entry points**: Leaf Skill `concorde-init` and native `scripts/concorde.py init` Tool in
  source/installed package layouts.
- **Inputs**: Host project root, optional root module ID/name, and explicit `concorde-operation-configuration@1` JSON through `--configuration <file|->`. Product structure is authored later, not invented by the initializer.
- **Outputs**: Digest-bearing proposal or an applied/unchanged structured result with exact artifacts and findings.
- **Obligations**: Preview and apply use the same proposal; existing targets are never silently overwritten.
- **Failures**: Unsafe paths, conflicts, invalid entities/relations, stale proposals, or filesystem failure preserve the project.
- **Compatibility**: Initialization Proposal 4 contains exactly Profile 7 configuration, one root architecture, its Archify system overview, `.concorde/reflections/index.json`, and `.concorde/reflections/config.json`; the project config includes `operation_configuration`. Older/mixed initialization is rejected.
- **Implementing entities**: `entity.understanding.init-skill`, `entity.understanding.initializer`, `module.concorde.capabilities`.

## Usage Scenarios

1. Inspect an unconfigured project and generate a minimal root architecture proposal.
2. Review exact configuration/architecture/reflection files, then explicitly apply the current digest-bound proposal.
3. Run again against an already configured valid project and receive `unchanged` without a blank proposal.

## Related Features

- Configuration depends on `feature.capabilities.provide-capability-surfaces`
  for the common Operation data contract and the explicit migration Tool for existing initialized projects.

- `feature.concorde.workflow` composes this feature as the entry point that establishes a project's
  root architecture before any other lifecycle phase can select a feature.

## Requirements

- **FR-001**: Initialization MUST propose Profile 7 configuration, one valid root `architecture.md` with entity/relation/interaction scaffold, one linked Archify `architecture` system overview of those entities and relationships, a metadata-only reflection allocation index at `.concorde/reflections/index.json`, and shared reflection defaults. The project config MUST contain explicit typed Operation configuration.
- **FR-002**: It MUST NOT invent child modules/features/interfaces or create any feature artifact.
- **FR-003**: Apply MUST accept only a current safe Initialization Proposal 4 and atomically promote exactly its five declared files.
- **FR-004**: Existing configured/partial/conflicting state MUST be diagnosed and never overwritten implicitly.

## Edge Cases

- Configuration exists but the root architecture is missing or malformed.
- The root ID is valid but the target path is a symlink or already owned by unrelated content.

## Concept Completeness and Operation Configuration

Initialization Proposal 4 produces a minimal root boundary scaffold, not a complete domain model.
The initialized project must apply the ontology's concept/relationship review using its own product
evidence before describing the architecture as complete. `operation_configuration` in
`.concorde/config.json` follows `contract.capabilities.operation-data`; missing settings block new
proposal generation. Existing valid roots with these settings return `unchanged`. A valid legacy
root missing only Operation settings is directed to `configure --propose/--apply`; initialization
does not rewrite its architecture. All five proposal files retain exact digest/path checks and
atomic promotion; exact preinstalled reflection settings are retained while missing files are
created, and changed settings reject the whole apply. Source-profile version 7 is unchanged.
