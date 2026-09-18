# Concorde Framework collaboration agreements

These are the exact local duties and relied-upon provider guarantees of this Module. The entry
explains the collaboration at a conceptual level; these agreements retain the canonical local
meaning and links to the included providers.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Operation](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Protocol binding](spec/values.md#terminology) | Defined in Identities and versions. |
| [Registry](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec context](harness/context.md#terminology) | Defined in What information a worker receives. |
| [Implementation context](harness/context.md#terminology) | Defined in What information a worker receives. |
| [Skill](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Issue](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Disposition](issues/lifecycle.md#terminology) | Defined in Solving a recorded problem. |
| [Delivery](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Local collaboration agreements

These entries describe the seven children registered for this Module from the Framework's own perspective. Each child's complete contract is its own registered collection; these promises are only what the composition relies on.

### Spec

<a id="entity.concorde.spec"></a><a id="agreement.document.concorde.module.1"></a>

The [Spec Module](spec/module.md) owns the project Spec model: the pinned Protocol binding, the explicit registry, structural validation, stable-ID file-set queries and honest initialization.

This collaboration applies when any entry must identify a Module, resolve its documents and entity file bindings, or initialize a project.

- [Use deterministic identity and context resolution for routing](spec/contracts.md#registry-stable-id-spec-context-queries)
- [Require structural validation before bounded work](spec/scenarios.md#scenario.spec.validate-success)
- [Begin with an honest pinned stub when creating a project](spec/scenarios.md#project-initialization)

### Harness

<a id="entity.concorde.harness"></a><a id="agreement.document.concorde.module.2"></a>

The [Harness Module](harness/module.md) configures and runs every Agent invocation: freezes its context kinds, binds its Agent and Harness definition, compiles its effective permissions, launches its Pi worker and coordinates it through LangGraph control flow.

This collaboration applies when an entry needs an Agent to reason or act.

- [Freeze the selected contract before invocation](harness/contracts.md#contract.context.selection)
- [Keep invocation authority bounded](harness/requirements.md#req.harness.permission-no-widen)
- [Require typed completion before reporting success](harness/requirements.md#req.harness.execute-exit-insufficient)
- [Compose inspectable bounded control flow](harness/graphs-and-loops.md)

### Development

<a id="entity.concorde.development"></a><a id="agreement.document.concorde.module.3"></a>

The [Development Module](development/module.md) supplies common operation admission, dispatch, typed outcomes and host-owned state mechanics.

Whenever an operation enters or resumes through the common boundary.

- [Admit typed requests, preserve current worktree binding and distinct outcomes](development/interfaces.md#operation-execution-boundary)

### Issues

<a id="entity.concorde.issues"></a><a id="agreement.document.concorde.module.4"></a>

The [Issues Module](issues/module.md) retains, investigates and resolves explicitly attributed project feedback and persistent gaps.

This collaboration applies when a developer works with recorded feedback.

- [Report and reference classified problems without changing task control](issues/interfaces.md)
- [Solve with bounded authority and evidence-grounded disposition](issues/lifecycle.md)

### Distribution

<a id="entity.concorde.distribution"></a><a id="agreement.document.concorde.module.5"></a>

The [Distribution Module](distribution/module.md) owns Skill sources and shared invocation instructions, builds authored projections, installs and configures owned integrations, provisions the managed runtime and keeps a source checkout's own projections bound to the worktree that built them.

This collaboration applies when a project adopts, updates or configures the Framework, or when built assets must be current.

- [Preserve user-owned content during installation](distribution/installation.md)
- [Require valid provisioning evidence](distribution/runtime.md)
- [Reject stale projections before execution](distribution/build.md)

### Views

<a id="entity.concorde.views"></a><a id="agreement.document.concorde.module.6"></a>

The [Views Module](views/module.md) publishes registered Module Specs as a navigable documentation site and opens an existing raw code graph with the verified installed viewer.

This collaboration applies when a developer wants to read Specs or inspect the code graph.

- [Publish one canonical definition with owner and inclusion provenance](views/scenarios.md#scenario.views.publish-reference-link)
- [Keep project contracts unchanged during viewing](views/viewer.md)

### Operations

<a id="entity.concorde.operations"></a><a id="operations-collaboration"></a>

The [Operations Module](operations/module.md) groups the responsibilities that provide reusable and composed Operations. This collaboration applies when a developer selects behavior such as planning, authoring, development or delivery. The Framework relies on the [complete Operation contract](operations/module.md#design), supplies explicit intent to the common Host, and preserves each provider's blocked, failed, ready and delivered outcomes rather than treating a composed result as universal success. Module containment does not grant context or execution authority.
