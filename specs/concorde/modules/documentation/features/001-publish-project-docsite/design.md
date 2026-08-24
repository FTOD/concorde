# Feature Design: Publish Project Documentation

**Design status**: Accepted implementation baseline.

## Realization Overview

The Documentation module converts validated architecture and feature sources into hierarchical pages and embeds fresh Archify HTML.

## Module and Feature Collaboration

Source discovery, view-model construction, Docusaurus rendering, and production validation collaborate behind the documentation contracts.

## Scenario Realization

A build reads canonical sources, verifies diagrams, writes generated pages, and validates the production site.

## Durable Implementation Decisions

Generated content is reproducible and non-authoritative; source provenance remains visible.

## Traceability and Evidence

Documentation unit, integration, and production-build tests provide evidence.

## Known Limitations

Perceptual browser review depends on browser availability.

