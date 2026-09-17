# Context assessment

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound capability in the [current adapter inventory](../development/capabilities.md).
Only a declared in-process composition can call it; direct Skill/CLI invocation is rejected.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`context-solve` returns a task-specific sufficiency assessment without authored artifacts.
Before its fresh context assessor invocation, the host compares local dependency
declarations to registered relationships: a missing direct promise is an owned Spec gap;
malformed, duplicate, unknown or unrelated entries are conflicting. Neither injects an undeclared
relationship inventory into the worker. The assessor uses only the admitted Spec and never fetches
code or another context to fill a gap.

Outcomes are sufficient, spec_incomplete, unsupported, conflicting or failed. A prohibition is
unsupported, a contradiction conflicting, a known missing runtime field invalid input, and an
execution failure failed. Gaps identify question, blocked_step and needed_contract, with host-bound
target/context provenance. The caller pauses the dependent step and may continue independent work.
Reassessment after an explicit contract repair uses fresh inputs; an unchanged blocked step stays
blocked. Successful assessment resolves historical phase gaps only after any associated authored
output has passed host acceptance. It proves no universal completeness.

## Precise specifications

The Planning Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
