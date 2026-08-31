---
id: contract.auto-docs.build-manifest
kind: contract
module: module.concorde.auto-docs
role: provided
flow: output
representation:
  kind: custom
  format: JSON
  serialization: JSON
  version: 7
  definition: specs/concorde/features/002-auto-docsite/contracts/build-manifest.schema.json
  schema: specs/concorde/features/002-auto-docsite/contracts/build-manifest.schema.json
  example: specs/concorde/features/002-auto-docsite/contracts/build-manifest.example.json
counterparties:
  - external.project-maintainer
consumers:
  - external.project-maintainer
features:
  - feature.auto-docs.publish-project-docsite
version: 7
evidence:
  tests:
    - docsite/tests/contract/build-manifest.test.ts
evidence_status: verified
---

# Build manifest contract

## Purpose

Provide a deterministic JSON inventory of included pages, explicit exclusions, verified routes,
generator versions, source hashes, and passed checks. The normative schema is
`specs/concorde/features/002-auto-docsite/contracts/build-manifest.schema.json`; its representative example and
complete field semantics live beside it. They are referenced here rather than copied.

## Information

The manifest records generator versions, all four source collections, included page provenance and
routes, deliberate exclusions, rendered routes, and passed deterministic checks. Architecture page
records additionally carry stable entity and declared-view metadata.

## Obligations

- All arrays are stably sorted and all paths are project-relative.
- Feature specification pages carry stable ID, module, and status; feature-implementation pages
  carry durable realization provenance; module-design pages carry the owning module's provenance;
  architecture pages carry stable ID, kind, hierarchy metadata, view source hash, and delivered-view
  route when applicable.
- A successful manifest contains no timestamp and validates against schema version 7.
- Only actual rendered routes enter the verified route inventory.

## Failure Semantics

Failed runs do not emit or promote a success manifest. Unsupported schema versions, absolute paths,
missing fields, unsorted projections, and unverified routes fail publication.

## Compatibility

Incompatible field-meaning changes require a new schema version. Version 7 names
`feature-abstracts`, `features`, and `feature-implementations`, with page kinds `feature-abstract`,
`feature-design`, and `feature-implementation` and companion route fields matching those meanings.
Readers reject unsupported schema versions.

## Evidence

The representative payload and real build output validate against the normative schema in
`docsite/tests/contract/build-manifest.test.ts` and the production-build suite.
