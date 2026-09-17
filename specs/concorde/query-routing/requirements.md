# Query and Routing requirements

These precise specifications belong directly to the [Query and Routing Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Query and Routing

### req.development.global-discovery — Discovery workers discover complete Module contexts

A Capability with discover context selection SHALL use a discovery-phase worker to discover complete Module Spec contexts.

### req.development.routing-hint-not-context — Routing hints only steer selection

A target or focus hint SHALL only steer selection.

### req.development.routing-hint-no-grant — Routing hints never grant context

A target or focus hint SHALL NOT itself grant context or replace explicit resolution.
