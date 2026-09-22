# Operations provider agreements

The Operations layer owns responsibility grouping, not its providers' execution grants. These agreements explain when each provider is used and how this layer relies on its result.

## Terminology

| Term                                  | Meaning / definition           |
| ------------------------------------- | ------------------------------ |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology)    | Defined in Concorde Framework. |

## Provider collaborations

### Planning

<a id="entity.concorde.planning"></a><a id="agreement.document.concorde.module.7"></a>

[Planning Module](../planning/module.md) assesses whether a selected Module contract supports a task, creates a revision-bound plan and derives implementation acceptance tasks. It serves admitted composing operations with separate assessment, plan and task contracts; no development-loop history is an implicit source of software meaning.

This collaboration applies when the request concerns Planning.

- [Planning contract](../planning/assessment.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Implementation

<a id="entity.concorde.implementation"></a><a id="agreement.document.concorde.module.8"></a>

[Implementation Module](../implementation/module.md) fulfills an admitted task list within the selected Module implementation grant and reports exact task completion. It serves composing operations that supply current plans and tasks, and distinguishes local code writing from separately admitted component coordination.

This collaboration applies when the request concerns Implementation.

- [Implementation contract](../implementation/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Review

<a id="entity.concorde.review"></a><a id="agreement.document.concorde.module.10"></a>

[Review Module](../review/module.md) independently evaluates an admitted task against current Module contracts and, in code mode, its separately granted implementation. It serves standalone callers and composing graphs with revision-bound coverage, findings and gaps, without repairing or delivering the reviewed work.

This collaboration applies when the request concerns Review.

- [Review contract](../review/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Validation

<a id="entity.concorde.validation"></a><a id="agreement.document.concorde.module.11"></a>

[Validation Module](../validation/module.md) collects deterministic structural and configured implementation-check evidence for the current candidate and evaluates the applicable readiness gates. It serves explicit validation requests and composing graphs; neither a development plan nor automatic development invocation is universally required.

This collaboration applies when the request concerns Validation.

- [Validation contract](../validation/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Delivery

<a id="entity.concorde.delivery"></a><a id="agreement.document.concorde.module.12"></a>

[Delivery Module](../delivery/module.md) stages a verified candidate on an independent branch, cleans up its source worktree and separately merges into the primary branch when explicitly authorized. It serves participating user sessions and Task subagents and consumes current evidence without owning the graph that produced the candidate.

This collaboration applies when the request concerns Delivery.

- [Delivery contract](../delivery/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.
