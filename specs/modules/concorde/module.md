```concorde-document
{
  "id": "document.concorde.system",
  "targets": [
    "module.concorde"
  ],
  "main_visible": true
}
```

# Concorde Framework

Turn specified intent into inspectable changes, and distribute the tools and views needed to work with those changes.

## Features

### feature.concorde.provide

Concorde Framework. Developers use installed concorde-* Skills and deterministic CLI entry points. Requests carry a task and constraints; results distinguish completion, missing contracts, failure and an inspectable candidate. Installation supplies the accepted rule assets; workflows coordinate work; publication and the viewer support inspection.

### feature.concorde.develop

Develop a specified change. Developers use installed concorde-* Skills and deterministic CLI entry points. Requests carry a task and constraints; results distinguish completion, missing contracts, failure and an inspectable candidate. Installation supplies the accepted rule assets; workflows coordinate work; publication and the viewer support inspection.

### feature.concorde.inspect

Inspect project knowledge. Developers use installed concorde-* Skills and deterministic CLI entry points. Requests carry a task and constraints; results distinguish completion, missing contracts, failure and an inspectable candidate. Installation supplies the accepted rule assets; workflows coordinate work; publication and the viewer support inspection.

### feature.concorde.adopt

Adopt the Framework. Developers use installed concorde-* Skills and deterministic CLI entry points. Requests carry a task and constraints; results distinguish completion, missing contracts, failure and an inspectable candidate. Installation supplies the accepted rule assets; workflows coordinate work; publication and the viewer support inspection.

## Interfaces

### interface.concorde.use

Developers use installed concorde-* Skills and deterministic CLI entry points. Requests carry a task and constraints; results distinguish completion, missing contracts, failure and an inspectable candidate. Installation supplies the accepted rule assets; workflows coordinate work; publication and the viewer support inspection.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
