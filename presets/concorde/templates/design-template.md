## Concorde Feature Profile

<!--
  This file is the feature's complete durable specification. It lives directly at
  <providing-module>/features/<NNN-name>.md. A feature is never a hierarchy container.

  Front matter must declare:

  id: feature.<namespace>.<outcome>
  kind: feature
  module: module.<namespace>[.<module>]
  related_features: []
  interfaces:
    provided: []
    required: []
  evidence_status: unknown

  Use stable related-feature IDs for composition, refinement, or dependency. Put structural entity
  identity and ownership in the providing module's architecture.md; this feature file references those
  entities and adds only feature-specific behavior. Source code is the implementation authority and
  tests/deterministic checks are evidence.
-->

**Outcome**: [One observable result for a consumer.]

**Scope**: [What this capability includes and excludes.]

## Interfaces

<!--
  Define every externally meaningful machine, human-workflow, or generated-artifact interface here.
  Existing stable contract.* IDs may be retained as interface identities. Do not create separate
  interface documents beside this feature file.
-->

### `[interface.stable.id]` — [Interface name]

- **Consumer and direction**: [consumer]; [input, output, or bidirectional from the provider]
- **Entry points**: [architecture entity IDs or a named human workflow]
- **Inputs**: [shape, meaning, and explicit empty input when applicable]
- **Outputs**: [shape, meaning, and explicit empty output when applicable]
- **Obligations**: [provider and consumer invariants]
- **Failures**: [externally visible failure modes and handling]
- **Compatibility**: [versioning and migration expectations]
- **Example**: [representative use, especially for custom serialized behavior]
- **Implementing entities**: [stable entity IDs from module architecture]

## Usage

[Give a representative successful use, then the important edge and failure cases. Scenarios are
examples; testable requirements below remain authoritative.]

## Architecture Zoom

<!--
  Name only entities visible from the providing module architecture or its permitted ancestry.
  Explain their roles, ordered/conditional collaboration, and interface boundary. Do not redefine
  entity type, ownership, locator, or module structure. Architecture-owned diagrams may be linked as
  explanatory views; the feature owns no diagram source. Every linked maintained diagram keeps
  `meta.legend.mode: hidden` in its owning module source.
-->

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.<qualified.id>` | [Feature-specific role.] | [Typed relation or ordered collaboration.] |

## Related Features

[For every `related_features` ID, state whether this feature composes, refines, or depends on it and
why. Write `None.` when the list is empty.]
