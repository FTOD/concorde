# Concorde Framework collaboration agreements

These are the exact local duties and relied-upon provider guarantees of this Module. The entry
explains the collaboration at a conceptual level; these agreements retain the canonical local
meaning and links to the included providers.

## Local collaboration agreements

These entries describe the sixteen children registered for this Module from the Framework's own perspective. Each child's complete contract is its own registered collection; these promises are only what the composition relies on.

### Spec

<a id="entity.concorde.spec"></a><a id="agreement.document.concorde.module.1"></a>

Owns the project Spec model: the pinned Protocol binding, the explicit registry, structural validation, stable-ID file-set queries and honest initialization.

This collaboration applies when any entry must identify a Module, resolve its documents and entity file bindings, or initialize a project.

- [Use deterministic identity and context resolution for routing](spec/contracts.md#registry-stable-id-spec-context-queries)
- [Require structural validation before bounded work](spec/scenarios.md#scenario.spec.validate-success)
- [Begin with an honest pinned stub when creating a project](spec/scenarios.md#project-initialization)

### Harness

<a id="entity.concorde.harness"></a><a id="agreement.document.concorde.module.2"></a>

Configures and runs every Agent invocation: freezes its context kinds, binds its Agent and Harness definition, compiles its effective permissions, launches its Pi worker and coordinates it through LangGraph control flow.

This collaboration applies when an entry needs an Agent to reason or act.

- [Freeze the selected contract before invocation](harness/contracts.md#contract.context.selection)
- [Keep invocation authority bounded](harness/requirements.md#req.harness.permission-no-widen)
- [Require typed completion before reporting success](harness/requirements.md#req.harness.execute-exit-insufficient)
- [Compose inspectable bounded control flow](harness/graphs-and-loops.md)

### Development

<a id="entity.concorde.development"></a><a id="agreement.document.concorde.module.3"></a>

Supply common capability admission, dispatch, typed outcomes and host-owned state mechanics.

Whenever a capability enters or resumes through the common boundary.

- [Admit typed requests, preserve current worktree binding and distinct outcomes](development/interfaces.md#capability-execution-boundary)

### Issues

<a id="entity.concorde.issues"></a><a id="agreement.document.concorde.module.4"></a>

Retains, investigates and resolves explicitly attributed project feedback and persistent gaps.

This collaboration applies when a developer works with recorded feedback.

- [Report and reference classified problems without changing task control](issues/interfaces.md)
- [Solve with bounded authority and evidence-grounded disposition](issues/lifecycle.md)

### Distribution

<a id="entity.concorde.distribution"></a><a id="agreement.document.concorde.module.5"></a>

Owns Skill sources and shared invocation instructions, builds authored projections, installs and configures owned integrations, provisions the managed runtime and keeps a source checkout's own projections bound to the worktree that built them.

This collaboration applies when a project adopts, updates or configures the Framework, or when built assets must be current.

- [Preserve user-owned content during installation](distribution/installation.md)
- [Require valid provisioning evidence](distribution/runtime.md)
- [Reject stale projections before execution](distribution/build.md)

### Views

<a id="entity.concorde.views"></a><a id="agreement.document.concorde.module.6"></a>

Publishes registered Module Specs as a navigable documentation site and opens an existing raw code graph with the verified installed viewer.

This collaboration applies when a developer wants to read Specs or inspect the code graph.

- [Publish one canonical definition with owner and inclusion provenance](views/scenarios.md#scenario.views.publish-reference-link)
- [Keep project contracts unchanged during viewing](views/viewer.md)

### Planning

<a id="entity.concorde.planning"></a><a id="agreement.document.concorde.module.7"></a>

Planning assesses whether a selected Module contract supports a task, creates a revision-bound plan and derives implementation acceptance tasks. It serves admitted composing capabilities with separate assessment, plan and task contracts; no development-loop history is an implicit source of software meaning.

This collaboration applies when the request concerns Planning.

- [Planning contract](planning/assessment.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Implementation

<a id="entity.concorde.implementation"></a><a id="agreement.document.concorde.module.8"></a>

Implementation fulfills an admitted task list within the selected Module implementation grant and reports exact task completion. It serves composing capabilities that supply current plans and tasks, and distinguishes local code writing from separately admitted component coordination.

This collaboration applies when the request concerns Implementation.

- [Implementation contract](implementation/implementation.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Spec Authoring

<a id="entity.concorde.spec-authoring"></a><a id="agreement.document.concorde.module.9"></a>

Spec Authoring proposes complete replacements for the selected Module's owned Spec documents from its complete contract and an explicit task. It serves specification flows and other declared callers; independent review and flow completion belong to their consumers.

This collaboration applies when the request concerns Spec Authoring.

- [Spec Authoring contract](spec-authoring/authoring.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Review

<a id="entity.concorde.review"></a><a id="agreement.document.concorde.module.10"></a>

Review independently evaluates an admitted task against current Module contracts and, in code mode, its separately granted implementation. It serves standalone callers and composing flows with revision-bound coverage, findings and gaps, without repairing or delivering the reviewed work.

This collaboration applies when the request concerns Review.

- [Review contract](review/review.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Validation

<a id="entity.concorde.validation"></a><a id="agreement.document.concorde.module.11"></a>

Validation collects deterministic structural and configured implementation-check evidence for the current candidate and evaluates the applicable readiness gates. It serves explicit validation requests and composing flows; neither a development plan nor dev-loop invocation is universally required.

This collaboration applies when the request concerns Validation.

- [Validation contract](validation/validation.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Delivery

<a id="entity.concorde.delivery"></a><a id="agreement.document.concorde.module.12"></a>

Delivery stages a verified candidate on an independent branch, cleans up its source worktree and separately merges into the primary branch when explicitly authorized. It serves participating outer sessions and consumes current evidence without owning the flow that produced the candidate.

This collaboration applies when the request concerns Delivery.

- [Delivery contract](delivery/delivery.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Query and Routing

<a id="entity.concorde.query-routing"></a><a id="agreement.document.concorde.module.13"></a>

Query and Routing answers questions from explicitly selected complete Module contexts and selects one owning Module for a routed task. It serves the main entry and discovery consumers, preserving caller intent without reading implementation to infer behavior.

This collaboration applies when the request concerns Query and Routing.

- [Query and Routing contract](query-routing/query-and-routing.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Topology

<a id="entity.concorde.topology"></a><a id="agreement.document.concorde.module.14"></a>

Topology designs, prepares and atomically applies changes to registered Module structure and owned definitions. It serves developers evolving ownership, references, dependencies and file bindings through the existing accepted design and application boundaries.

This collaboration applies when the request concerns Topology.

- [Topology contract](topology/topology.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Development Flow

<a id="entity.concorde.dev-loop"></a><a id="agreement.document.concorde.module.15"></a>

Development Flow composes sibling providers to carry one intended change through Spec preparation, planning, tasks, implementation, validation and independent code review to a ready candidate. It owns that sequence, candidate lifecycle, bounded repair and stop policy, while each provider owns its own reusable contract.

This collaboration applies when the request concerns Development Flow.

- [Development Flow contract](dev-loop/development.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

### Specification Flow

<a id="entity.concorde.specify-loop"></a><a id="agreement.document.concorde.module.16"></a>

Specification Flow composes routing, Spec Authoring and Review to prepare or review one Module contract independently of implementation. It owns Spec-stage ordering, accepted-authoring reuse and Spec-review completion, and returns before planning or readiness.

This collaboration applies when the request concerns Specification Flow.

- [Specification Flow contract](specify-loop/specify-loop.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.
