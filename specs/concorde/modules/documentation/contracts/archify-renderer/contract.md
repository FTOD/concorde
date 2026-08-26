---
id: contract.documentation.archify-renderer
kind: contract
module: module.concorde.documentation
role: required
flow: bidirectional
counterparties:
  - external.archify
representation:
  kind: standard
  format: Archify architecture JSON and standalone HTML
  version: "2.14.0"
  definition: specs/concorde/architecture.json
features:
  - feature.documentation.publish-project-docsite
evidence_status: verified
---

# Archify Renderer Contract

## Purpose

Render each declared maintained architecture view into deterministic standalone HTML.

## Information

The commonly adopted Archify format exchanges schema version, diagram metadata, components,
boundaries, connections, named views, output path, and quality profile; generated HTML carries the
interactive visual projection.

## Obligations

Documentation supplies valid maintained JSON, an explicit safe output candidate, showcase quality,
and preserved source provenance. The build verifies the Archify package identity and compatibility,
runs deterministic validation, and invokes delivery in stable source order. Archify returns a
self-contained rendering and deterministic validation receipt without changing the source.

Raw renderer receipts may contain absolute process-local paths. Documentation verifies their type,
source digest, artifact digest, 9/9 showcase checks, and zero errors/warnings, but retains only
normalized project-relative provenance and content hashes in durable or published evidence.

## Failure Semantics

Missing or incompatible renderer packages, unsafe or duplicate outputs, renderer errors or warnings,
and malformed or disagreeing receipts remain visible and stop publication before stale HTML can be
consumed. A failed set preserves the last complete delivery and published site.

## Compatibility

This contract targets Archify 2.14.0 and its architecture, workflow, sequence, data-flow, and
lifecycle schemas. Incompatible package, schema, CLI, or receipt changes require coordinated source,
adapter, contract, and test updates.

## Evidence

Both views pass the nine automated Archify showcase checks and retain deterministic delivery and
provenance evidence.
