---
id: feature.understanding.initialize-architecture
kind: feature
module: module.concorde.understanding
related_features:
  - feature.concorde.workflow
interfaces:
  provided:
    - interface.concorde.initialize
  required: []
evidence_status: partial
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
| `entity.concorde.control-state` | Receives Profile 7 configuration and `.concorde/reflections/index.json`. |

## Interfaces

### `interface.concorde.initialize` — Initialize root architecture

- **Consumer**: Maintainer establishing Concorde in a project.
- **Direction**: Skill/Tool request to reviewed proposal or apply result.
- **Entry points**: Leaf Skill `concorde-init` and native `scripts/concorde.py init` Tool in
  source/installed package layouts.
- **Inputs**: Project root, proposed root module ID, responsibility, boundary, and optional initial modules/features.
- **Outputs**: Digest-bearing proposal or an applied/unchanged structured result with exact artifacts and findings.
- **Obligations**: Preview and apply use the same proposal; existing targets are never silently overwritten.
- **Failures**: Unsafe paths, conflicts, invalid entities/relations, stale proposals, or filesystem failure preserve the project.
- **Compatibility**: Initialization Proposal 3 contains exactly Profile 7 configuration, one root architecture, its Archify system overview, and `.concorde/reflections/index.json`; older/mixed initialization is rejected.
- **Implementing entities**: `entity.understanding.init-skill`, `entity.understanding.initializer`, `module.concorde.capabilities`.

## Usage Scenarios

1. Inspect an unconfigured project and generate a minimal root architecture proposal.
2. Review exact configuration/architecture/reflection files, then explicitly apply the current digest-bound proposal.
3. Run again against an already configured valid project and receive `unchanged` without a blank proposal.

## Related Features

- `feature.concorde.workflow` composes this feature as the entry point that establishes a project's
  root architecture before any other lifecycle phase can select a feature.

## Requirements

- **FR-001**: Initialization MUST propose Profile 7 configuration, one valid root `architecture.md` with entity/relation/interaction scaffold, one linked Archify `architecture` system overview of those entities and relationships, and a metadata-only reflection allocation index at `.concorde/reflections/index.json`.
- **FR-002**: It MUST NOT invent child modules/features/interfaces or create any feature artifact.
- **FR-003**: Apply MUST accept only a current safe Initialization Proposal 3 and atomically promote exactly its four declared files.
- **FR-004**: Existing configured/partial/conflicting state MUST be diagnosed and never overwritten implicitly.

## Edge Cases

- Configuration exists but the root architecture is missing or malformed.
- The root ID is valid but the target path is a symlink or already owned by unrelated content.
