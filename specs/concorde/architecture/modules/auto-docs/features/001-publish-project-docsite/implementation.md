# Feature Implementation: Publish Project Documentation

**Realization status**: Accepted implementation baseline.

## Realization Overview

The Auto-Docs module publishes root `README.md` at `/`, converts validated architecture and feature
sources into hierarchical pages, publishes project guidance from `docs/`, and embeds fresh Archify HTML.

## Module and Feature Collaboration

Source discovery across `README.md`, `docs/`, and `specs/`, view-model construction, Docusaurus
rendering, and production validation collaborate behind the documentation contracts.

## Scenario Realization

A build reads the homepage file and both canonical source trees, verifies diagrams, writes generated
pages, and validates the production site.

## Durable Implementation Decisions

Root `README.md` remains the one-file homepage authority, `docs/` and `specs/` remain the recursive
source trees, generated content is reproducible and non-authoritative, and source provenance remains visible.

## Traceability and Evidence

Auto-Docs unit, integration, contract, and production-build tests cover all three maintained inputs.

## Known Limitations

Perceptual browser review depends on browser availability.
