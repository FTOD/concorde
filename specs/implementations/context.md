```concorde-document
{
  "id": "document.implementation.context",
  "targets": [
    "implementation.context"
  ],
  "main_visible": false
}
```

# Context resolution implementation

`implementation.context` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.harness`.

## Responsibility

Realize the four context kinds of the Harness Module as immutable canonical snapshots: single-Module resolution for bounded stages, global discovery assembly for the coordinator, topology-author context and the rechecks that reject drift.

## Bound files

- `src/concorde/specification/context.py`
- `tests/concorde/specification/test_boundaries.py`
- `tests/concorde/specification/test_scoped_protocol.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/context.py` | Freezes Spec context, the phase-appropriate implementation context, task context and instructions into `ContextSnapshot`, `DiscoveryContext` and `TopologyAuthorContext`; rechecks them against the current repository; validates stage results against a snapshot. |
| `tests/concorde/specification/test_scoped_protocol.py` | Exercises phase-specific membership, focus, shared documents, discovery pools, stale contexts and Protocol binding. |
| `tests/concorde/specification/test_boundaries.py` | Exercises the information boundary between Spec-only phases and code phases. |

## Implementation interfaces, dependencies and constraints

`resolve_context` reads the selected Module through `SpecRepository`, orders its registered documents into Target Spec and Shared Specs, appends the Protocol rule bundle from the current build, and freezes task, constraints, admitted `stage_inputs`, instructions and the workspace observation. Only `phase == "implementation"` without a review-result input appends the Implementation Spec bodies, and only implementation and code-review phases list bound-file artifacts with digests; this realizes the Protocol's implementation context and its declared read-only subset. `resolve_discovery_context` deduplicates complete document and diagram bodies into sorted pools with per-Module references. `recheck_context`, `recheck_discovery_context` and `recheck_topology_author_context` reconstruct the same inputs and raise `SpecError/stale_context` on any difference. Dependencies are the registry, typed-value validation, canonical JSON, digests and the worktree lifecycle observation.

Capability context is not yet a snapshot field: no registered Agent admits a Capability reference today, so the frozen closure contains the other three kinds only. Materializing admitted Capability and Tool contracts in the snapshot record, with their identities in the context digest, is pending implementation work that must not widen any existing grant.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Cases must cover local Feature/Interface focus, shared membership, absent implementation bodies in planning, present bodies and file digests in implementation, file references only in code review, changed document or diagram bytes, malformed or foreign stage inputs, stale Protocol binding and deduplicated discovery pools.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
