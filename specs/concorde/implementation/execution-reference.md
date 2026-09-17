# Implementation execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Implementation Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Acceptance task](../planning/tasks.md#terminology) | Defined in Making work verifiable. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Internal operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Entity](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Implementation operation {#implementation-implementation-operation}

The [Development Module](../development/module.md) owns admission. Its [common invocation envelope](../development/interfaces.md#operation-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/execution-reference.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound operation in the [current adapter inventory](../development/execution-reference.md).
Only a declared in-process composition can call it; direct Skill/CLI invocation is rejected.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`implement` requires current authored tasks and their accepted plan in a
concorde-implementation-task@1. Missing tasks are missing_tasks; stale artifacts or mismatched
intent stop admission. A fresh programmer receives the complete selected
Spec and contents of the files its own entities bind. Only those implementation paths are writable;
registered Specs, registry, entity declarations and configuration are not. Network and credentials
remain disabled. Optional concorde-review-result@2 is admitted only after the host verifies the
current dev-loop repair round; structural validity does not authorize repair.

The worker returns every exact admitted task with unchanged identity and acceptance, marked complete
only when fulfilled. Missing or incomplete tasks produce incomplete_tasks, never ready. The host
persists accepted progress and returns artifact references in concorde-implement-response@3.
Authorized code edits can remain after failed execution; recovery inspects preserved progress and
re-admits current context rather than claiming rollback or rerunning with wider grants.

A listed test does not grant its transitive imports, fixtures or repository configuration to the
programmer. Tests requiring inputs outside that invocation's grant are repository-level Host
verification. The programmer records the attempted command and concrete missing inputs, continues
independent work, and distinguishes this deferral from a passing test and from an implementation
defect. For acceptance qualified by the granted runtime, deferred repository-level execution does
not prevent completion of otherwise fulfilled implementation and test obligations. An actual
defect or missing implementation obligation remains incomplete; Host checks still gate readiness.

### Design {#implementation-design}

#### Component coordination and current adapter limit {#implementation-component-coordination-and-current-adapter-limit}

A selected Module may contain local code tasks and tasks for its direct children or used Modules.
Local tasks retain their original plan and identity; they do not recursively invoke a new loop for
the same Module. Each participant has a separately selected complete contract and grant. All affected
provider/consumer Spec views must agree before component code changes; incomplete reconciliation
remains inspectable. Component ancestry supplies no extra file access.

The current adapter delegates component lifecycle scheduling and final shared-consumer checks to
its existing enclosing development Graph. That graph's ready, defer_component_checks and bounded
repair policies are not implementation completion conditions. Reusing this provider for a different
coordinated graph requires a declared implementation adapter for its component scheduling and evidence
handoffs; no arbitrary scheduler input or additional callable entry is introduced here. The local
task contract is independently reusable under current host admission. Missing contracts stop the
dependent task; an actual implementation defect remains incomplete; cancellation and limits retain
their separate execution outcomes.

### Precise specifications {#implementation-precise-specifications}

The Implementation Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary graph is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new graph requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
