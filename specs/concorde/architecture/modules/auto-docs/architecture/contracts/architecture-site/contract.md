---
id: contract.auto-docs.architecture-site
kind: contract
module: module.concorde.auto-docs
role: provided
flow: output
representation:
  kind: standard
  format: HTML Living Standard
  version: living-standard
  definition: https://html.spec.whatwg.org/
counterparties:
  - external.project-maintainer
consumers:
  - external.project-maintainer
features:
  - feature.auto-docs.publish-project-docsite
version: 3
evidence:
  tests:
    - docsite/tests/integration/production-build.test.ts
evidence_status: verified
---

# Published project site contract

## Purpose

Provide static HTML, CSS, JavaScript, assets, local search data, and a build manifest as one browsable,
read-only project view. The route, provenance, accessibility, failure, and compatibility guarantees
are defined in `specs/concorde/features/002-auto-docsite/contracts/published-site.md`.

## Information

The output carries static HTML, CSS, JavaScript, search data, source provenance, the versioned build
manifest, and sandboxed delivered Archify views where architecture sources declare them.

## Obligations

- `/` links to distinct Architecture, Documentation, and Features collections.
- `/architecture/**`, `/docs/**`, and `/features/**` each project one canonical source per page.
- The self-hosting `/docs` landing page provides a progressive path to the quick start, framework
  overview, project ontology, specification model, project structure, Concorde workflow, and command
  reference; those guides retain working links to their canonical Architecture or Features
  authorities.
- Architecture pages expose stable ID, kind, hierarchy metadata, source provenance, and declared
  sandboxed Archify views; module design reference pages expose their owning module and source
  provenance; feature specification pages expose ID, module, and status, while feature
  implementation pages expose durable source provenance.
- Cross-collection links and local discovery span all three route spaces.
- Failed publication never replaces the last successfully promoted site.

## Failure Semantics

Source, link, route, rendering, search, manifest, or promotion failure makes the candidate
unpublishable. This version publishes accepted implementations within `/features` and module
design references within `/architecture`; its three route bases remain stable within contract
version 3, and the manifest schema version is owned by `contract.auto-docs.build-manifest`
(schema version 5).

## Compatibility

The Architecture, Documentation, and Features route bases remain stable within contract version 3;
the build-manifest schema version follows its own contract. Adding the named self-hosting pages
within `/docs` or new page kinds within an existing route space is compatible; removing a route
space or provenance field is breaking.

## Evidence

Production-build, accessibility, route-inventory, and repeatability tests are maintained under
`docsite/tests/`; their requirement mapping is recorded in `specs/concorde/features/002-auto-docsite/design.md`.
