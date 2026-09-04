---
id: feature.understanding.bound-planning-context
kind: feature
module: module.concorde.understanding
related_features:
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.lifecycle.plan-attempt
    relation: depended_on_by
  - id: feature.capabilities.permission-bounded-execution
    relation: depended_on_by
  - id: feature.understanding.resolve-feature-workspace
    relation: refines
interfaces:
  provided:
    - contract.understanding.planning-context
  required:
    - contract.capabilities.operation-data
---

# Feature Design: Bound Planning Context

## Outcome and Scope

A planning Operation resolves an exact, permission-bounded context for one selected feature before any
agent starts: the complete selected feature and its providing module's owned architecture/
implementation/test locators, its attempt paths, and the direct feature files that own its explicitly
required interfaces, each with a reason trace, plus an explicit deny list for everything else. A
maintainer can therefore invoke planning without granting ambient access to every module's private
architecture and implementation.

## Target Planning Context Payload

The current `resolve_planning_context` returns an in-process `PlanningContext` record. The target
serialized `concorde-planning-context@1` extends `contract.understanding.planning-context` using the
common TypedValue/ArtifactRef forms from `contract.capabilities.operation-data`. It is host-resolved
data, not a caller-supplied replacement for workspace or permission receipts.

| Required `data` field | JSON type | Meaning |
|---|---|---|
| `feature_id` | string | Exact stable authored feature ID resolved from `feature_path`. |
| `feature_path` | string | Existing canonical direct feature file relative to the host project root. |
| `module_id` | string | Providing module's stable ID. |
| `module_architecture` | ArtifactRef | Providing module's architecture file with identity and current byte digest. |
| `attempt_dir` | string | Canonical `.concorde/attempts/<feature_id>` path, whether or not the attempt exists yet. |
| `source_digest` | SHA-256 string | Digest of admitted planning inputs under this contract's source-digest semantics. |
| `owned_artifacts` | array of ArtifactRef | Selected feature and bounded owned source/test files, plus admitted governance/ancestry inputs; no foreign implementation bodies. |
| `provider_features` | array of ProviderFeature | Exactly the required-interface provider feature files with reasons, or `[]`. |
| `denied_paths` | array of strings | Canonical project-relative excluded paths; `[]` is valid. These explain exclusions, not enforce them. |

`ProviderFeature` has exactly `feature_id` (stable string), `artifact` (ArtifactRef to the provider
feature file), and `interface_ids` (nonempty unique array of required interface IDs explaining why
the body is admitted). Array entries and artifact IDs are unique; no untyped payload or directory
snapshot is embedded. The source digest and host receipt cover membership as well as bytes, so a
new/removed relevant file invalidates a stale context. Existing authority and dependency-exclusion
rules above remain binding.

The producer receives `concorde-plan-context@1.data.feature_path`, resolves its canonical identity and
bounded artifact set, and emits this typed payload. The plan author receives it unchanged under
`concorde-plan-author-context@1.data.planning_context`, alongside the original task. It must match
the host workspace and current inputs before authorship. Missing refs, changed bytes or membership,
wrong feature identity, or unsupported type/version block the author; they never broaden reads.

The serialization adapter and typed dispatch are pending runtime work. Existing structured Python
fields and receipts provide source evidence for this design, but do not yet expose this wire type.

## Target Contract Examples

### Resolved planning context

The minimal fixture has no foreign providers. The real host computes digests and bound membership.

Illustrative fixture IDs/digests describe the wire shape; they are not live execution receipts.

```json
{
  "type_id": "concorde-planning-context",
  "schema_version": 1,
  "data": {
    "feature_id": "feature.example.search",
    "feature_path": "specs/example/features/001-search.md",
    "module_id": "module.example",
    "module_architecture": {
      "id": "module.example",
      "path": "specs/example/architecture.md",
      "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    "attempt_dir": ".concorde/attempts/feature.example.search",
    "source_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "owned_artifacts": [
      {
        "id": "feature.example.search",
        "path": "specs/example/features/001-search.md",
        "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ],
    "provider_features": [],
    "denied_paths": []
  }
}
```

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.understanding.planning-context-data` | Defines target serialized context fields separately from caller input and host authority. |
| `entity.understanding.workspace-resolver` | Supplies the Protocol 13 feature/module/ancestry result that planning-context narrows. |
| `entity.understanding.planning-context` | Resolves owned and required-interface paths, reason traces, and denies from Protocol 13 and `interfaces.required`. |
| `entity.understanding.plan-context-skill` | Reports the resolved context receipt for one selected planning attempt. |
| `entity.understanding.protocol13` | Defines the workspace fields the context receipt extends without redefining. |
| `entity.concorde.specification` | Supplies the selected feature's and provider features' architecture/design sources. |
| `module.concorde.lifecycle` | Consumes the context receipt in its plan Operation and plan-author leaf. |
| `module.concorde.capabilities` | Consumes the context receipt to compile enforced read/write/deny policy. |

## Interfaces

### `contract.understanding.planning-context` — Permission-bounded planning context receipt

- **Consumer**: The plan Operation and its plan-author leaf (`module.concorde.lifecycle`) and the
  capability policy compiler (`module.concorde.capabilities`).
- **Direction**: Feature Workspace Protocol 13 plus the selected feature's `interfaces.required`
  ownership to one context receipt.
- **Entry points**: `src/concorde/understanding/planning_context.py#resolve_planning_context`; internal leaf Skill
  `concorde-plan-context`.
- **Inputs**: Selected stable feature ID, its Protocol 13 workspace result, its `interfaces.required`
  set, and the project's Profile 7 module/feature ownership.
- **Outputs**: One context receipt naming the selected feature, its providing architecture, owned
  implementation/test locators, attempt paths, the exact required-interface provider feature paths
  each with a reason trace, an explicit denied-path list, and a workspace digest.
- **Obligations**: Include the complete selected feature plus providing-module owned implementation/
  test locators; include only dependency feature bodies that deterministically own an interface listed
  in `interfaces.required`, each carrying that interface ID as its reason trace; exclude dependency
  module architecture/source/tests/attempts, descendant-module internals, unrelated feature bodies,
  and every other attempt; resolve an exact path collision between a parent providing-module locator
  and required-provider private context by removing that path from owned implementation context while
  retaining the deny.
- **Failures**: Ambiguous provider-interface ownership, a missing feature/architecture owner, an
  unresolved selected feature/module authority collision, or an admitted provider feature collision
  fails closed and returns no context receipt.
- **Compatibility**: This receipt is additive to Feature Workspace Protocol 13 and MUST NOT redefine
  Protocol 13's own fields; it carries no independent schema version of its own.
- **Implementing entities**: `entity.understanding.planning-context`,
  `entity.understanding.workspace-resolver`, `entity.understanding.plan-context-skill`,
  `entity.understanding.protocol13`.
- **Example**: The planning author receives read access to `specs/payments/features/001-charge.md`,
  its own module architecture/owned locators, and an explicit provider feature such as
  `specs/ledger/features/002-record-entry.md` with reason trace `contract.ledger.record-entry`; the
  denied-path list names the ledger module's architecture, source, tests, and other attempts.

## Usage Scenarios

### User Story 1 — Plan through published feature boundaries (Priority: P1)

A maintainer invokes one planning Operation without granting it ambient access to every module's
architecture and implementation.

**Why this priority**: Module hierarchy is useful only when consumers can depend on published feature
promises without understanding private module internals.

**Independent Test**: In a two-module fixture, run the planning-context resolution and assert that the
selected module's owned context and the explicitly required dependency feature file are readable,
while the dependency module's architecture, source, tests, descendants, and unrelated features are
denied.

**Acceptance Scenarios**:

1. **Given** a selected feature that requires an interface provided by another module's feature,
   **When** planning context is resolved, **Then** that provider feature specification is included
   with a reason trace and the provider module's private internals are excluded.
2. **Given** only an incidental or unrelated feature reference, **When** context is resolved, **Then**
   the reference remains a summary and its body is not readable by the planning agent.

## Related Features

- The target typed boundary depends on `feature.capabilities.provide-capability-surfaces` for
  `contract.capabilities.operation-data`; executable adoption is a separately identified runtime gap.


- `feature.lifecycle.plan-attempt` depends on this feature's context receipt before its plan-author
  leaf writes any temporal plan artifact.
- `feature.capabilities.permission-bounded-execution` depends on this feature's owned locators,
  reason-traced provider paths, denied-path list, and workspace digest to compile enforced
  read/write/deny policy.
- `feature.understanding.resolve-feature-workspace` is depended on by this feature for the Protocol 13
  workspace result that planning-context narrows to owned and required-interface paths.

## Requirements

- **FR-001**: Planning context MUST include the complete selected feature, providing-module
  architecture and owned implementation/test locators, and only dependency feature bodies that
  deterministically own an interface listed in the selected feature's `interfaces.required` set;
  every inclusion MUST carry the required-interface ID as its reason trace.
- **FR-002**: Planning context MUST exclude dependency module architecture/source/tests/attempts,
  descendant-module internals, unrelated feature bodies, and every other attempt. An exact path
  collision between a parent providing-module locator and required-provider private context MUST be
  resolved by removing that path from owned implementation context while retaining the deny; a
  selected feature/module authority or admitted provider feature collision MUST still fail closed.

## Edge Cases

- The selected feature is new and has no stable-ID attempt until specification persists its ID.
- One related feature provides several interfaces, but only a subset is required by the selected
  feature; the context receipt names the exact interface reasons while permission is granted to the
  single owning feature file.
- A source locator crosses into another module or points through a symlink; context resolution
  rejects it instead of treating the broad executable root as authority.
- A related feature that does not own one of the selected feature's required interfaces remains a
  summary/navigation reference and its body is not added to the readable set.
- If a parent providing module's entity locator exactly names a required provider module's private
  architecture or implementation path, the provider-private deny takes precedence and that exact
  locator is removed from owned implementation context; the published provider feature remains
  readable.
- A task that truly changes a dependency module must select that module's feature in a separate
  lifecycle rather than widening the current planner's read or write boundary silently.

## Success Criteria

- **SC-001**: A two-module planning fixture proves 100% of justified dependency feature files are
  readable and 100% of dependency private architecture/source/test/attempt paths are denied.
