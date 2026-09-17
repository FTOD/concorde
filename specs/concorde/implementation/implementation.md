# Implementation capability

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound capability in the [current adapter inventory](../development/capabilities.md).
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
persists accepted progress and returns artifact references in concorde-implement-response@2.
Authorized code edits can remain after failed execution; recovery inspects preserved progress and
re-admits current context rather than claiming rollback or rerunning with wider grants.

A listed test does not grant its transitive imports, fixtures or repository configuration to the
programmer. Tests requiring inputs outside that invocation's grant are repository-level Host
verification. The programmer records the attempted command and concrete missing inputs, continues
independent work, and distinguishes this deferral from a passing test and from an implementation
defect. For acceptance qualified by the granted runtime, deferred repository-level execution does
not prevent completion of otherwise fulfilled implementation and test obligations. An actual
defect or missing implementation obligation remains incomplete; Host checks still gate readiness.

## Design

### Component coordination and current adapter limit

A selected Module may contain local code tasks and tasks for its direct children or used Modules.
Local tasks retain their original plan and identity; they do not recursively invoke a new loop for
the same Module. Each participant has a separately selected complete contract and grant. All affected
provider/consumer Spec views must agree before component code changes; incomplete reconciliation
remains inspectable. Component ancestry supplies no extra file access.

The current adapter delegates component lifecycle scheduling and final shared-consumer checks to
its existing enclosing development Flow. That flow's ready, defer_component_checks and bounded
repair policies are not implementation completion conditions. Reusing this provider for a different
coordinated flow requires a declared implementation adapter for its component scheduling and evidence
handoffs; no arbitrary scheduler input or additional callable entry is introduced here. The local
task contract is independently reusable under current host admission. Missing contracts stop the
dependent task; an actual implementation defect remains incomplete; cancellation and limits retain
their separate execution outcomes.

## Precise specifications

The Implementation Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
