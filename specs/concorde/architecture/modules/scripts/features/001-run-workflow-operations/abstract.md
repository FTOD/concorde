# Run Workflow Operations

`feature.scripts.run-workflow-operations` · specified at `module.concorde.scripts` · about three minutes.

## Purpose

Give skills a safe, deterministic mechanism for workspace routing and operations over project files.

## Functionality

- Resolves the selected feature and phase paths.
- Proposes and applies approved root initialization.
- Returns one bounded architectural level.
- Validates maintained sources without mutation.
- Reports readiness and reflection state.
- Promotes an explicitly accepted implementation atomically.

## Structure

Portable shell and PowerShell launchers locate Python. Python adapters invoke the standard-library
runtime under `extensions/concorde/runtime/concorde/`. Every operation returns a structured result;
the parent [level view](../../../../diagrams/level-view.json) shows the Skills and Workspace Files boundaries.

## Logic

1. A skill invokes a launcher or the workspace adapter.
2. Scripts discover the project root and validate requested paths.
3. The operation reads the relevant Workspace Files.
4. Read-only operations return results; write operations return a proposal first.
5. Approved writes verify the digest and apply atomically.

## Read Next

- [Feature design](design.md)
- [Scripts module](../../module.md)
- [Operations contract](../../architecture/contracts/operations/contract.md)
