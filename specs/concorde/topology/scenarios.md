# Topology scenarios

These precise specifications belong directly to the [Topology Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Composition](../spec/registry.md#terminology) | Defined in Registry. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Implementation binding](../spec/registry.md#terminology) | Defined in Registry. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Topology

### scenario.development.topology-design — Design a candidate registry

- GIVEN a change to identities, composition, dependencies, document ownership and references or file listings
- WHEN `concorde-main` runs `design-topology`
- THEN it admits exact registry metadata and the Module kind definition, withholds implementation file contents, and returns a digest-bound candidate registry, local Spec tasks, migration constraints and acceptance conditions
- AND no project file changes

### scenario.development.topology-accept — Accept a design and author local Specs

- GIVEN a developer accepts a topology design
- WHEN `concorde-main` runs `accept-topology`
- THEN it rechecks the complete discovery context, starts a fresh target-local Spec author for each affected Module, and validates their combined output against an in-memory registry and document overlay
- AND the full authored documents are stored only in a before-digest-bound application artifact, and the public response exposes only its ArtifactRef

### scenario.development.topology-apply — Apply a reviewed artifact

- GIVEN a developer accepts the exact prepared application artifact
- WHEN `concorde-main` runs `apply-topology`
- THEN it atomically applies the reviewed registry and document replacements together
- AND successful application updates the accepted structure and sources in the same transaction

### scenario.development.topology-stale — Stale or conflicting input is rejected

- GIVEN the registry, Protocol or a candidate's shared document bytes changed since the design was produced, or a non-owner proposes a provider document replacement or affected-consumer compatibility remains unresolved
- WHEN `accept-topology` or `apply-topology` processes that input
- THEN the host rejects the mutation and leaves the pre-existing project files unchanged
- AND no target author ever writes a project file directly

See [owner authoring and consumer agreement](requirements.md#req.development.shared-document-agreement).

The detailed contract is [Accepted atomic topology](execution-reference.md#topology-topology-evolution-agent-graph).
