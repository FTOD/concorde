# Feature Design: Compose Starter Workflow

**Design status**: Accepted implementation baseline.

## Realization Overview

The Integration module composes Concorde guidance into normal Spec Kit phases and exposes extension commands through the active agent integration.

## Module and Feature Collaboration

The preset owns lifecycle command/template composition; the extension owns new Concorde operations and portable runtime access.

## Scenario Realization

Spec Kit resolves component layers, materializes agent-native surfaces, and each normal phase resolves the selected workspace before work.

## Durable Implementation Decisions

Agent presentations preserve package-neutral intent and never become the deterministic runtime.

## Traceability and Evidence

Composition and clean-install tests provide cross-integration evidence.

## Known Limitations

Supported behavior is bounded to the pinned Spec Kit host version.

