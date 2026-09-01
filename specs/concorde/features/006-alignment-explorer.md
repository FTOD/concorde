---
id: feature.concorde.explore-alignment
kind: feature
module: module.concorde
related_features:
  - feature.concorde.define-project-ontology
interfaces:
  provided:
    - contract.concorde.alignment-explorer
  required:
    - contract.understand-anything.knowledge-graph
evidence_status: unknown
---

# Feature Design: Alignment Explorer

## Outcome and Scope

A maintainer can browse module/entity/feature/interface architecture beside implementation-graph
subjects and inspect explicit evidence-qualified alignments, unknowns, and disagreements without mutation.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.runtime` | Loads validated Profile 7 semantic identities and evidence records for projection. |
| `entity.concorde.understand-anything` | Supplies optional pinned implementation knowledge-graph nodes/edges. |
| `entity.concorde.specification` | Supplies module architecture and feature design truth. |

## Interfaces

### `contract.concorde.alignment-explorer` — Evidence-qualified architecture exploration

- **Consumer**: Maintainer or coding agent exploring architecture and specification-to-code agreement.
- **Direction**: Validated specification plus optional implementation graph/evidence to read-only graph bundle/query result.
- **Entry points**: `speckit.concorde.explore` projection/query surface when installed.
- **Inputs**: Profile 7 modules/entities/relations/features/interfaces, pinned UA graph, explicit alignment bases, and current evidence/freshness metadata.
- **Outputs**: Searchable graph with provenance, qualified identities, adapter types, alignments, and unknown/partial/verified/disagrees states.
- **Obligations**: Keep representation distinct from identity, never infer verification from names/similarity, and expose absent/stale evidence truthfully.
- **Failures**: Invalid/stale/incompatible graphs or ambiguous mapping produce findings/unknown state and never rewrite sources.
- **Compatibility**: UA types/edges are adapter vocabulary; recursive Concorde modules and stable entity IDs remain authoritative.
- **Implementing entities**: `entity.concorde.runtime`, `entity.concorde.understand-anything`, `entity.concorde.specification`.
- **Example**: A Concorde `program` may render as UA `concept` plus metadata; the adapter record preserves the original entity ID/type and does not claim equivalence.

### `contract.understand-anything.knowledge-graph` — Required implementation graph

- **Provider**: `external:Egonex-AI/Understand-Anything@ba450c43425f3de6d43daf76526950ad8ca93536`.
- **Consumer**: Alignment Explorer adapter and ontology comparison.
- **Direction**: Read-only graph input to evidence-qualified Concorde projection.
- **Entry points**: UA Graph JSON conforming to the pinned formal `types.ts`/`schema.ts` model.
- **Inputs**: Nodes, directed edges, layers, tours, metadata, graph kind, and source revision/provenance.
- **Outputs**: Parsed implementation subjects/relations available for explicit adapter/alignment records.
- **Obligations**: Preserve upstream IDs/types/directions/provenance and never reinterpret a flat layer as module containment.
- **Failures**: Invalid schema, unsupported type, missing revision, or stale input yields findings/unknown state.
- **Compatibility**: Pinned formal model has 27 node and 38 edge types; drifting narrative counts are non-authoritative.
- **Implementing entities**: `entity.concorde.understand-anything`, `entity.concorde.runtime`.
- **Example**: UA `script` scanner output appears as a `file` node; Concorde preserves its own File/Script role separately.

## Usage Scenarios

1. Browse a module's typed entity/relation graph and follow canonical architecture/feature sources.
2. Overlay a pinned implementation graph and inspect explicit realization/evidence mappings.
3. Filter unknown, partial, verified, or disagreeing subjects without changing sources.

## Requirements

- **FR-001**: Every projected Concorde subject MUST retain stable ID, owning module/feature, canonical path, and Profile 7 kind.
- **FR-002**: UA representation type/edge MUST remain adapter metadata and MUST NOT assert identity/equivalence.
- **FR-003**: Alignments MUST name their evidence basis, revision, freshness, and bounded status; names/similarity alone cannot verify.
- **FR-004**: Missing/stale/incompatible input MUST yield unknown/findings rather than invented agreement or disagreement.
- **FR-005**: Exploration MUST be read-only and reproducible from validated maintained/executable inputs.

## Edge Cases

- A physical file defines a logical service/schema and must remain two correlated entities.
- Unrelated modules reuse a label but retain different stable entity identities.
