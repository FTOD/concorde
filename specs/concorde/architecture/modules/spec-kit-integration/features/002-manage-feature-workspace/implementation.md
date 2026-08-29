# Feature Implementation: Manage Feature Workspace

**Realization status**: Accepted implementation baseline.

## Realization Overview

The Integration workspace service places features under providing modules, creates the permanent
specification/design pair, persists one selected root, derives durable and temporal phase paths, and
applies explicitly approved acceptance proposals.

## Module and Feature Collaboration

Feature placement uses Architecture Core context; selection uses Spec Kit's project-local feature record; normal phases consume derived paths.

## Scenario Realization

Creation proposes ownership and paths, specification establishes the feature root, selection routes
later phases, and acceptance promotes the reviewed completed attempt into root `implementation.md` before
removing `attempt/`.

## Durable Implementation Decisions

Concorde maintains no second registry or root-level temporal aliases. Acceptance is digest-bound,
task-gated, bounded to the selected feature, and rollback-safe.

## Traceability and Evidence

Workspace unit, contract, integration, and acceptance tests provide evidence.

## Known Limitations

Only one active implementation attempt is supported per feature.
