```concorde-document
{
  "id": "document.planning.assessment",
  "owner": "module.planning",
  "main_visible": true
}
```

# Context assessment

## Usage & Contract

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

### Requirements

#### req.planning.assessment-context — Assess only the selected contract

Planning SHALL assess task sufficiency only from the selected Module's complete admitted Spec context.

#### req.planning.assessment-gap — Attribute necessary contract gaps

Planning SHALL report a necessary missing contract with its question, blocked step, needed contract and host-bound target/context provenance.


### Scenarios

#### scenario.planning.assessment-sufficient — The admitted contract supports the task

- GIVEN a selected Module whose dependency declarations agree with its registered relationships
- AND its complete admitted Spec supplies the contracts necessary for the task
- WHEN the fresh context assessor evaluates that task
- THEN it returns sufficient without authored documents, a plan or tasks
- AND the assessment concerns that task and does not prove universal semantic completeness

#### scenario.planning.assessment-gap — A necessary promise is missing

- GIVEN the selected Module's complete admitted Spec lacks a contract needed for the task
- WHEN context assessment reaches the dependent judgment
- THEN it reports spec_incomplete with question, blocked_step and needed_contract and host-bound target/context provenance
- AND the dependent step pauses while independent reasoning may continue
- AND the assessor neither reads implementation contents nor expands the selected context to supply the missing promise
