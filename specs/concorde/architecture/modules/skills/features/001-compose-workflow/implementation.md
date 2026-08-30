# Feature Implementation: Compose Workflow Skills

**Realization status**: Accepted implementation baseline.

## Realization Overview

The `concorde` preset supplies nine normal-phase command layers and the templates used by those
phases. The `concorde` extension supplies five Concorde-specific command definitions. Spec Kit
materializes the resolved sources as agent-native skills or slash commands.

## Module and Feature Collaboration

Skills consume workspace paths from Workspace Files and structured operations from Scripts.
Distribution packages the preset and extension but does not alter their workflow meaning.

## Scenario Realization

Composition resolves command precedence, materializes the winning layer, and verifies that installed
artifacts refer to the installed launchers and selected-workspace adapter rather than to checkout-local paths.

## Durable Implementation Decisions

The ask skill is deliberately agent-followed. Normal phases route before inherited root-path logic.
No installed presentation becomes a second maintained source.

## Traceability and Evidence

Preset composition, installed command-surface, skills-mode, slash-command, release-artifact, and
self-hosting tests cover the realized paths.

## Known Limitations

Compatibility remains bounded to explicitly tested Spec Kit and agent-integration versions.
