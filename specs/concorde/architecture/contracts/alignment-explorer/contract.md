---
id: contract.concorde.alignment-explorer
kind: contract
module: module.concorde
role: provided
flow: output
representation:
  kind: custom
  format: Concorde Alignment Explorer Bundle
  version: "1"
  definition: specs/concorde/architecture/contracts/alignment-explorer/alignment-explorer.schema.json
examples:
  - specs/concorde/architecture/contracts/alignment-explorer/alignment-explorer.example.json
counterparties:
  - external.developer
consumers:
  - external.developer
features:
  - feature.concorde.explore-alignment
evidence_status: unknown
---

# Concorde Alignment Explorer Contract

## Purpose

Provide the read-only `speckit.concorde.explore` experience—materialized as `/concorde-explore` or
`$speckit-concorde-explore`—and a machine-readable bundle that combines a compatible Understand
Anything graph with Concorde ontology, provenance, relation, coverage, freshness, and evidence-state
records.

## Information

The bundle carries its schema, ontology source/version, complete input provenance, one graph
conforming to `contract.understand-anything.knowledge-graph`, canonical Concorde and cross-ontology
relationship records that cannot be preserved on upstream edges, per-subject alignment records, and
summary counts. Terminology and relationship semantics come from the shared
[project ontology](../../../../../docs/ontology.md).

The interactive representation supports browsing, search, filters, focus, source links, state
explanations, and stale/input diagnostics. The serialized bundle is normative for information
exchange; visual layout is a disposable presentation choice.

## Obligations

- The provider preserves Concorde semantic kind, stable identity, authority, lifecycle, and source
  provenance independently of Understand Anything adapter representation types.
- Every alignment record uses `unknown`, `partial`, `verified`, or `disagrees`, exposes all coverage
  dimensions, and names the deterministic basis for any non-unknown state.
- `verified` requires current positive deterministic evidence; stale, absent, ambiguous, or
  model-suggested data never appears verified.
- Every bundle records the Concorde source digest, implementation revision, upstream repository and
  revision, graph version, ontology source/version, and analysis time.
- `speckit.concorde.explore` remains read-only and links back to canonical sources; materialized
  surfaces use `/concorde-explore` or `$speckit-concorde-explore`, never bare `/explore`; the bundle
  and interface never become project intent.
- Consumers may filter or summarize records but must not discard uncertainty or provenance when
  presenting alignment.

## Failure Semantics

Invalid maintained sources prevent a trustworthy current bundle. Missing or incompatible
implementation graphs permit specification-only browsing with explicit `unknown` alignment. Stale
provenance, ontology drift, unresolved references, invalid bundle/schema data, or unavailable source
targets are shown as diagnostics and prevent affected records from appearing current or verified.

## Compatibility

Version 1 permits additive optional display hints and record fields that do not change existing
meaning. Removing a required field, changing evidence-state or coverage semantics, changing identity
or authority interpretation, or changing the embedded upstream compatibility profile requires a new
major contract version and ontology migration guidance.

## Evidence

The schema and example are maintained with the draft feature. No explorer implementation or
behavioral evidence has been accepted, so evidence is `unknown`.
