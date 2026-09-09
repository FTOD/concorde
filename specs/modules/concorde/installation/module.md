```concorde-document
{
  "id": "document.specs.modules.concorde.installation.module",
  "targets": [
    "module.installation"
  ],
  "main_visible": true
}
```

# Installation

Install, initialize, configure and upgrade Concorde while preserving user-owned content.

## Features

### feature.installation.install

Installation service. The installer proposes owned file changes and applies accepted current proposals. Initialization creates a Module stub, an explicit registry and a pinned Protocol binding. Build produces assets; installation places and verifies them. Missing business facts remain explicit. Failed application or provisioning restores previously valid owned state.

### feature.installation.self-distribute

Distribute agent surfaces into the source worktree. The installer proposes owned file changes and applies accepted current proposals. Initialization creates a Module stub, an explicit registry and a pinned Protocol binding. Build produces assets; installation places and verifies them. Missing business facts remain explicit. Failed application or provisioning restores previously valid owned state.

## Interfaces

### interface.installation.use

The installer proposes owned file changes and applies accepted current proposals. Initialization creates a Module stub, an explicit registry and a pinned Protocol binding. Build produces assets; installation places and verifies them. Missing business facts remain explicit. Failed application or provisioning restores previously valid owned state.

The [complete interface contract](interfaces.md) defines call shapes, values, effects and errors.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
