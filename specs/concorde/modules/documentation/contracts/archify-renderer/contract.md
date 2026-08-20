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
  version: "1"
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

Documentation supplies valid maintained JSON and preserves source provenance. Archify returns a
self-contained rendering and deterministic validation receipt without changing the source.

## Failure Semantics

Renderer errors and warnings remain visible and stop publication of the affected view.

## Compatibility

This contract targets the Archify architecture schema used by the checked-in root and Documentation
views. Incompatible schema changes require coordinated source and renderer updates.

## Evidence

Both views pass the nine automated Archify showcase checks. Browser visual review remains separately
tracked as manual evidence.
