# Reflections: Example Project

Problems met during any attempt on any feature. One entry per problem; update `Occurrences` on
re-encounter, from whichever feature meets it again.

### R-001 · Health-check timeout is unspecified

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.example.api.health-check
- **Kind**: specification
- **Concerns**: specs/example/modules/api/features/002-add-health-check/spec.md#functional-requirements
- **Expected**: FR-002 defines how long a dependency probe may take before the check reports degraded.
- **Observed**: No timeout is stated; two readings (fail fast, wait for the slowest probe) lead to
  different contracts.
- **Effect**: assumed
- **Action**: Planned a 2-second probe budget and recorded it in research.md D3.
- **Improvement**: State the probe budget in FR-002 through specification review.
- **Status**: resolved
- **Note**: Clarified on 2026-08-29; FR-002 now states the 2-second budget.

### R-002 · Existing invoke code ignores the status contract's `degraded` value

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.example.api.health-check
- **Kind**: implementation
- **Concerns**: feature.example.api.invoke
- **Expected**: The invoke feature's design reference says every status value of `contract.example.api`
  is handled.
- **Observed**: `src/api/invoke.py` treats anything but `ok` as an error, so a `degraded` health
  check fails the request.
- **Effect**: worked-around
- **Action**: Health check reports `ok` with a warning field until invoke is fixed; did not edit
  the invoke feature's code or design reference.
- **Improvement**: Open an attempt on `feature.example.api.invoke` to handle `degraded`.
- **Status**: open
- **Occurrences**:
  - analyze 2026-08-30 feature.example.api.health-check — analysis reported the same gap for
    `examples/degraded.json`.
