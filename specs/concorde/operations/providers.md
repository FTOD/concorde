# Operations provider agreements

The Operations layer owns responsibility grouping, not its providers' execution grants. These agreements explain when each provider is used and how this layer relies on its result.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Operation](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

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

### Spec Authoring

<a id="entity.concorde.spec-authoring"></a><a id="agreement.document.concorde.module.9"></a>

[Spec Authoring](../spec-authoring/module.md) proposes complete replacements for the selected Module's owned Spec documents from its complete contract and an explicit task. It serves specification graphs and other declared callers; independent review and graph completion belong to their consumers.

This collaboration applies when the request concerns Spec Authoring.

- [Spec Authoring contract](../spec-authoring/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Review

<a id="entity.concorde.review"></a><a id="agreement.document.concorde.module.10"></a>

[Review Module](../review/module.md) independently evaluates an admitted task against current Module contracts and, in code mode, its separately granted implementation. It serves standalone callers and composing graphs with revision-bound coverage, findings and gaps, without repairing or delivering the reviewed work.

This collaboration applies when the request concerns Review.

- [Review contract](../review/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Validation

<a id="entity.concorde.validation"></a><a id="agreement.document.concorde.module.11"></a>

[Validation Module](../validation/module.md) collects deterministic structural and configured implementation-check evidence for the current candidate and evaluates the applicable readiness gates. It serves explicit validation requests and composing graphs; neither a development plan nor dev-loop invocation is universally required.

This collaboration applies when the request concerns Validation.

- [Validation contract](../validation/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Delivery

<a id="entity.concorde.delivery"></a><a id="agreement.document.concorde.module.12"></a>

[Delivery Module](../delivery/module.md) stages a verified candidate on an independent branch, cleans up its source worktree and separately merges into the primary branch when explicitly authorized. It serves participating outer sessions and consumes current evidence without owning the graph that produced the candidate.

This collaboration applies when the request concerns Delivery.

- [Delivery contract](../delivery/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Query and Routing

<a id="entity.concorde.query-routing"></a><a id="agreement.document.concorde.module.13"></a>

[Query and Routing](../query-routing/module.md) answers questions from explicitly selected complete Module contexts and selects one owning Module for a routed task. It serves the main entry and discovery consumers, preserving caller intent without reading implementation to infer behavior.

This collaboration applies when the request concerns Query and Routing.

- [Query and Routing contract](../query-routing/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Topology

<a id="entity.concorde.topology"></a><a id="agreement.document.concorde.module.14"></a>

[Topology Module](../topology/module.md) designs, prepares and atomically applies changes to registered Module structure and owned definitions. It serves developers evolving ownership, references, dependencies and file bindings through the existing accepted design and application boundaries.

This collaboration applies when the request concerns Topology.

- [Topology contract](../topology/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Development Graph

<a id="entity.concorde.dev-loop"></a><a id="agreement.document.concorde.module.15"></a>

[Development Graph](../dev-loop/module.md) composes sibling providers to carry one intended change through Spec preparation, planning, tasks, implementation, validation and independent code review to a ready candidate. It owns that sequence, candidate lifecycle, bounded repair and stop policy, while each provider owns its own reusable contract.

This collaboration applies when the request concerns Development Graph.

- [Development Graph contract](../dev-loop/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Specification Graph

<a id="entity.concorde.specify-loop"></a><a id="agreement.document.concorde.module.16"></a>

[Specification Graph](../specify-loop/module.md) composes routing, Spec Authoring and Review to prepare or review one Module contract independently of implementation. It owns Spec-stage ordering, accepted-authoring reuse and Spec-review completion, and returns before planning or readiness.

This collaboration applies when the request concerns Specification Graph.

- [Specification Graph contract](../specify-loop/module.md#usage); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.
