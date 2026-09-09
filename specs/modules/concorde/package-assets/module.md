```concorde-document
{
  "id": "document.specs.modules.concorde.package-assets.module",
  "targets": [
    "module.package-assets"
  ],
  "main_visible": true
}
```

# Package assets

Build deterministic Agent, Skill, Protocol, schema and documentation assets from authored sources.

## Features

### feature.package-assets.provide

Package assets. build renders assets; write_build writes owned projections; check_build compares without changing the worktree. verify_fresh detects changed authoring sources. Module and Implementation kind definitions are distributed together. Generated assets are derived outputs and are never independent authoring sources.

## Interfaces

### api.assets.render

build renders assets; write_build writes owned projections; check_build compares without changing the worktree. verify_fresh detects changed authoring sources. Module and Implementation kind definitions are distributed together. Generated assets are derived outputs and are never independent authoring sources.

The [complete interface contract](interfaces.md) defines call shapes, values, effects and errors.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
