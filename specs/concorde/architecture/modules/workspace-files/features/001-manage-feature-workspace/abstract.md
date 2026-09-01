# Manage Feature Workspace Files

`feature.workspace-files.manage-feature-workspace` · specified at
`module.concorde.workspace-files` · about three minutes.

## Purpose

Make accepted intent, current-attempt memory, and generated projections impossible to confuse.

## Functionality

- Registers features beneath their providing module or parent feature.
- Uses one Spec Kit-owned selected-feature pointer.
- Keeps durable intent and accepted realization at the feature root.
- Keeps current delivery memory beneath `attempt/`.
- Keeps workflow reflections in the one durable project log.
- Promotes a reviewed implementation only through explicit acceptance.

## Structure

The canonical feature root contains `abstract.md`, `design.md`, and `implementation.md`. The optional
`attempt/` child contains planning, tasks, research, contracts, checklists, and other current-attempt
artifacts. Generated views live outside the source hierarchy. The parent
[level view](../../../../diagrams/level-view.json) shows both file-access paths.

## Logic

1. Spec Kit records the selected feature root.
2. Skills ask Scripts to resolve and validate that root.
3. Each phase receives exact durable and temporal paths.
4. The agent reads and writes only phase-authorized files.
5. Delivery promotes the generated realization and removes the completed attempt.

## Read Next

- [Feature design](design.md)
- [Workspace Files module](../../module.md)
- [Root file matrix](../../../../../design.md#workspace-file-model)
