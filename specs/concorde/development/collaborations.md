# Development collaboration agreements

These are the exact local duties and relied-upon provider guarantees of this Module. The entry
explains the collaboration at a conceptual level; these agreements retain the canonical local
meaning and links to the included providers.

## Dependencies and composition

Development's sole structural parent is `module.concorde`; it has no submodules of its own. Its direct uses distinguish shared services, providers and composing flows.

### Harness

<a id="entity.development.harness"></a><a id="agreement.document.development.module.1"></a>

Prepare each worker with its allowed inputs and tools, and run configured checks through their separate read-only boundary.

This collaboration applies when a capability Flow reaches an Agent invocation, policy preview or configured deterministic check.

- [Freeze and recheck each stage input](../harness/contracts.md#contract.context.selection)
- [Stop rather than widen rejected authority](../harness/requirements.md#req.harness.permission-no-widen)
- [Admit only matching typed completions and enforcement evidence](../harness/execution.md)
- [Preserve finite delegation budgets and cancellation](../harness/graphs-and-loops.md)
- [Require read-only checks and retain raw output privately](../harness/requirements.md#req.harness.check-project-read-only)

### Spec

<a id="entity.development.spec"></a><a id="agreement.document.development.module.2"></a>

Own the project Spec model: the pinned Protocol binding, the explicit registry, structural validation, stable-ID file-set queries and honest initialization.

Select Module descriptors, documents and implementation bindings, and validate Spec structure.

This collaboration applies when routing, binding a target, deriving affected implementation users or recording validation evidence.

- [Find every affected consumer before coordinating work](../spec/contracts.md#registry-stable-id-spec-context-queries)
- [Require source-bound structural evidence without claiming semantic proof](../spec/scenarios.md#scenario.spec.validate-success)

### Issues

<a id="entity.development.issues"></a><a id="agreement.document.development.module.3"></a>

Retain observed problems and their evidence while Development tracks which work depends on them.

This collaboration applies when a developer explicitly records gaps from a change's history.

- [Persist classified observations without controlling work](../issues/scenarios.md#scenario.issues.reference)

### Distribution

<a id="entity.development.distribution"></a><a id="agreement.document.development.module.4"></a>

Supply the current instructions and runtime assets used when Development starts an operation.

This collaboration applies when a developer runtime uses an installed Skill, an invocation requires fresh projections, or delivery verifies an integrated checkout.

- [Use canonical Skill/Agent projections and require a successful deterministic build before integration](../distribution/build.md)
- [Keep installed Skill sources outside bounded Agent context](../distribution/installation.md)

### Planning

<a id="entity.development.planning"></a><a id="agreement.document.development.module.5"></a>

Planning assesses whether a selected Module contract supports a task, creates a revision-bound plan and derives implementation acceptance tasks. It serves admitted composing capabilities with separate assessment, plan and task contracts; no development-loop history is an implicit source of software meaning.

This collaboration applies when the request concerns Planning.

- [Planning contract](../planning/assessment.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Implementation

<a id="entity.development.implementation"></a><a id="agreement.document.development.module.6"></a>

Implementation fulfills an admitted task list within the selected Module implementation grant and reports exact task completion. It serves composing capabilities that supply current plans and tasks, and distinguishes local code writing from separately admitted component coordination.

This collaboration applies when the request concerns Implementation.

- [Implementation contract](../implementation/implementation.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Spec Authoring

<a id="entity.development.spec-authoring"></a><a id="agreement.document.development.module.7"></a>

Spec Authoring proposes complete replacements for the selected Module's owned Spec documents from its complete contract and an explicit task. It serves specification flows and other declared callers; independent review and flow completion belong to their consumers.

This collaboration applies when the request concerns Spec Authoring.

- [Spec Authoring contract](../spec-authoring/authoring.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Review

<a id="entity.development.review"></a><a id="agreement.document.development.module.8"></a>

Review independently evaluates an admitted task against current Module contracts and, in code mode, its separately granted implementation. It serves standalone callers and composing flows with revision-bound coverage, findings and gaps, without repairing or delivering the reviewed work.

This collaboration applies when the request concerns Review.

- [Review contract](../review/review.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Validation

<a id="entity.development.validation"></a><a id="agreement.document.development.module.9"></a>

Validation collects deterministic structural and configured implementation-check evidence for the current candidate and evaluates the applicable readiness gates. It serves explicit validation requests and composing flows; neither a development plan nor dev-loop invocation is universally required.

This collaboration applies when the request concerns Validation.

- [Validation contract](../validation/validation.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Delivery

<a id="entity.development.delivery"></a><a id="agreement.document.development.module.10"></a>

Delivery stages a verified candidate on an independent branch, cleans up its source worktree and separately merges into the primary branch when explicitly authorized. It serves participating outer sessions and consumes current evidence without owning the flow that produced the candidate.

This collaboration applies when the request concerns Delivery.

- [Delivery contract](../delivery/delivery.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Query and Routing

<a id="entity.development.query-routing"></a><a id="agreement.document.development.module.11"></a>

Query and Routing answers questions from explicitly selected complete Module contexts and selects one owning Module for a routed task. It serves the main entry and discovery consumers, preserving caller intent without reading implementation to infer behavior.

This collaboration applies when the request concerns Query and Routing.

- [Query and Routing contract](../query-routing/query-and-routing.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Topology

<a id="entity.development.topology"></a><a id="agreement.document.development.module.12"></a>

Topology designs, prepares and atomically applies changes to registered Module structure and owned definitions. It serves developers evolving ownership, references, dependencies and file bindings through the existing accepted design and application boundaries.

This collaboration applies when the request concerns Topology.

- [Topology contract](../topology/topology.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Development Flow

<a id="entity.development.dev-loop"></a><a id="agreement.document.development.module.13"></a>

Development Flow composes sibling providers to carry one intended change through Spec preparation, planning, tasks, implementation, validation and independent code review to a ready candidate. It owns that sequence, candidate lifecycle, bounded repair and stop policy, while each provider owns its own reusable contract.

This collaboration applies when the request concerns Development Flow.

- [Development Flow contract](../dev-loop/development.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Specification Flow

<a id="entity.development.specify-loop"></a><a id="agreement.document.development.module.14"></a>

Specification Flow composes routing, Spec Authoring and Review to prepare or review one Module contract independently of implementation. It owns Spec-stage ordering, accepted-authoring reuse and Spec-review completion, and returns before planning or readiness.

This collaboration applies when the request concerns Specification Flow.

- [Specification Flow contract](../specify-loop/specify-loop.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.
