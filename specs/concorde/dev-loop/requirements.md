# Development Graph requirements

These precise specifications belong directly to the [Development Graph Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |

## Development Graph

### req.dev-loop.explicit-skip-sticky — Review skips cannot cancel required reviews

A `run_reviews=false` retry SHALL NOT cancel a Spec or code review already required for this change
by an earlier enabled invocation.

### req.dev-loop.repair-edge-only — Code-review repair is the only automatic edge

`review_code -> tasks` SHALL be the development Graph's only automatic revision edge.

### req.dev-loop.non-repair-stops-graph — Other outcomes stop the graph for a decision

Every other non-successful outcome SHALL stop the graph for a human decision or an explicit Spec or
code change.

### req.dev-loop.specify-loop-composition — Spec preparation has one reusable entry

The development Graph SHALL compose concorde-specify-loop for its Spec authoring and review stages.
