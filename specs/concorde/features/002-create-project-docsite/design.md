# Feature Design: Publish Project Docsite

**Design status**: Accepted implementation baseline.

## Realization Overview

The documentation module reads validated Concorde sources, builds hierarchical Docusaurus pages for
architecture, project documents, feature specifications, and permanent feature designs, embeds
declared Archify deliveries, and serves a read-only project view.

## Module and Feature Collaboration

Architecture Core supplies validated maintained sources; Documentation transforms them without mutation.

## Scenario Realization

A build validates sources, generates indexes/pages, embeds fresh diagrams, and emits the static site.

## Durable Implementation Decisions

Canonical sources remain authoritative; `spec.md` and `design.md` are published while temporal
`implementation/` Markdown remains excluded. Generated pages retain provenance and fail on stale or invalid inputs.

## Traceability and Evidence

Feature publication tests and `implementation/validation.md` record the accepted automated evidence.

## Known Limitations

Browser perceptual evidence remains environment-dependent.
