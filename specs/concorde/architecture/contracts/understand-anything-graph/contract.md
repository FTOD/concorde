---
id: contract.understand-anything.knowledge-graph
kind: contract
module: module.concorde
role: required
flow: input
representation:
  kind: custom
  format: Understand Anything Knowledge Graph compatibility profile
  version: ba450c43425f3de6d43daf76526950ad8ca93536
  definition: specs/concorde/architecture/contracts/understand-anything-graph/knowledge-graph.schema.json
examples:
  - specs/concorde/architecture/contracts/understand-anything-graph/knowledge-graph.example.json
counterparties:
  - external.understand-anything
providers:
  - external.understand-anything
consumers:
  - module.concorde
features:
  - feature.concorde.explore-alignment
evidence_status: partial
---

# Understand Anything Knowledge Graph Contract

## Purpose

Accept the pinned Understand Anything graph envelope and its formal node/edge registries as the
implementation-side input to Alignment Explorer without treating upstream graph types as Concorde
semantics.

## Information

The input carries project and analyzed-revision metadata, a graph kind, nodes, typed relationships,
layers, and tours. The compatibility schema enumerates the 27 node types and 38 edge types present at
upstream commit `ba450c43425f3de6d43daf76526950ad8ca93536`. Projected Concorde nodes may carry
the namespaced `concordeMeta` object because the pinned upstream node validator preserves additional
node fields.

The upstream source is
[Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything/tree/ba450c43425f3de6d43daf76526950ad8ca93536).
The local schema is a checked-in interoperability profile so Concorde can validate examples and drift
deterministically.

## Obligations

- The provider supplies the graph kind, project metadata, graph version, analyzed commit, nodes,
  edges, layers, and tours in the pinned vocabulary.
- Every edge endpoint and layer/tour node reference resolves to a supplied node.
- Normalization or auto-correction issues remain available to the consumer and cannot silently become
  alignment evidence.
- The consumer preserves upstream types as adapter representation metadata, applies the shared
  [project ontology](../../../../../docs/ontology.md) separately, and never infers Concorde authority
  from an upstream type alone.
- The consumer records the exact upstream and analyzed revisions in every derived projection.

## Failure Semantics

Missing/invalid project metadata, malformed collections, unresolved references, unknown formal types,
an incompatible graph kind, or a registry/alias/pass-through change makes the affected graph
unavailable for current alignment. `/explore` may fall back to specification-only browsing, but the
implementation coverage and alignment state remain explicitly unknown.

## Compatibility

The contract is pinned by upstream commit, not by repository `main`. Advancing the pin requires a
reviewed registry and shared-ontology diff. Additive pass-through node metadata is compatible; changing or
removing a formal type, category, graph-kind alias, required field, or pass-through behavior is
incompatible until the ontology, profile, examples, and tests are reconciled.

## Evidence

The 27 node values and 38 edge values were verified against the pinned upstream `types.ts` and
`schema.ts`. Integration and drift evidence do not yet exist, so contract evidence remains `partial`.
