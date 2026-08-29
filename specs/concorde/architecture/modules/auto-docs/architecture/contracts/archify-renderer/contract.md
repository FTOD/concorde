---
id: contract.auto-docs.archify-renderer
kind: contract
module: module.concorde.auto-docs
role: required
flow: bidirectional
counterparties:
  - external.archify
representation:
  kind: standard
  format: Archify architecture JSON and standalone HTML
  version: "2.16.0-dev.0"
  definition: specs/concorde/architecture/diagrams/level-view.json
features:
  - feature.auto-docs.publish-project-docsite
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

Auto-Docs supplies the officially installed and `skills-lock.json`-pinned project-local Archify skill, valid maintained JSON,
an explicit safe output candidate, showcase quality, and preserved source provenance. The build
resolves `.agents/skills/archify`, verifies package identity and compatibility, runs deterministic
validation, and invokes delivery in stable source order. Archify returns a self-contained rendering
and deterministic validation receipt without changing the source.

Raw renderer receipts may contain absolute process-local paths. Auto-Docs verifies their type,
source digest, artifact digest, 9/9 showcase checks, and zero errors/warnings, but retains only
normalized project-relative provenance and content hashes in durable or published evidence.

## Failure Semantics

Missing or incompatible renderer packages, unsafe or duplicate outputs, renderer errors or warnings,
and malformed or disagreeing receipts remain visible and stop publication before stale HTML can be
consumed. A failed set preserves the last complete delivery and published site.

## Compatibility

This contract targets the installed Archify 2.16 skill (`package.json` version `2.16.0-dev.0`) and its
architecture, workflow, sequence, data-flow, and lifecycle schemas. Incompatible package, schema,
CLI, or receipt changes require coordinated source, adapter, contract, and test updates.

## Evidence

All nine declared views pass the nine automated Archify 2.16 showcase checks and retain
deterministic delivery and provenance evidence.
