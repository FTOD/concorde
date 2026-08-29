# Feature Implementation: Manage Feature Workspace Files

**Realization status**: Accepted implementation baseline.

## Realization Overview

The workspace adapter resolves the Spec Kit selection into the canonical durable feature root and
its `attempt/` child. Runtime validation checks registration and shape; implementation acceptance
promotes the completed attempt atomically.

## Module and Feature Collaboration

Workspace Files define paths and lifetimes. Skills state phase intent. Scripts resolve, validate,
and apply approved transitions. Documentation reads validated durable sources.

## Scenario Realization

Resolution returns feature kind, stable ID, provider, durable paths, attempt paths and state,
parent/sibling context, and actionable findings. Acceptance additionally returns task/checklist
summaries, exact replacement/removal paths, and a review digest.

## Durable Implementation Decisions

There is no Concorde-owned selection registry, no root temporal alias, and no attempt archive that
could become a second authority. The project reflection log remains durable across attempts.

## Traceability and Evidence

Feature-workspace, nested-feature, selected-phase, implementation-acceptance, reflection, and
source-publication tests cover the realized behavior.

## Known Limitations

The current selection adapter is bounded to explicitly supported Spec Kit selection formats.
