# Implementation execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Implementation Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term                                                      | Meaning / definition                           |
| --------------------------------------------------------- | ---------------------------------------------- |
| [Spec](../module.md#terminology)                          | Defined in Concorde Framework.                 |
| [Module](../module.md#terminology)                        | Defined in Concorde Framework.                 |
| [Worker](../module.md#terminology)                        | Defined in Concorde Framework.                 |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.                 |
| [Grant](../module.md#terminology)                         | Defined in Concorde Framework.                 |
| [Candidate](../module.md#terminology)                     | Defined in Concorde Framework.                 |
| [Ready](../module.md#terminology)                         | Defined in Concorde Framework.                 |
| [Acceptance task](../planning/tasks.md#terminology)       | Defined in Making work verifiable.             |
| [Spec context](../harness/context.md#terminology)         | Defined in What information a worker receives. |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations.                         |
| [Pi integration](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Graph](../module.md#terminology)                         | Defined in Concorde Framework.                 |
| [Entity](../module.md#terminology)                        | Defined in Concorde Framework.                 |
| [Evidence](../module.md#terminology)                      | Defined in Concorde Framework.                 |

## Implementation operation {#implementation-implementation-operation}

[Harness admission](../harness/admission.md) owns the entry. Its [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a public, explicitly target-bound operation in the [current adapter inventory](../operations/execution-reference.md#operations-current-host-adapter).
The calling agent selects this Operation through the Pi `concorde` tool; its `run` action
prepares an exact direct native programmer call through finite Host admission. Main invokes the
returned call unchanged, then inspects independent Host acceptance attached to the native result. The tool's `describe` action returns
the Operation guidance and request schema without executing it.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`implement` requires current authored tasks and their accepted plan in a
concorde-implementation-task@1. Missing tasks are missing_tasks; stale artifacts or mismatched
intent stop admission. A fresh programmer receives the complete selected
Spec and contents of the files its own entities bind. Only those implementation paths are intended writable;
registered Specs, registry, entity declarations and configuration are not. Network and credentials
are prohibited by model policy, not OS confinement of native broad tools. Optional concorde-review-result@2 is admitted only after the host verifies the
current explicitly selected review feedback; structural validity does not authorize repair.

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

#### Caller-selected component work {#implementation-component-coordination-and-current-adapter-limit}

Tasks may name the selected Module, its direct children or declared used Modules. Implementation
checks those identities deterministically. It does not author Specs, schedule child development or
repair shared contracts. Missing component completion returns `unsupported` with each exact target
and derived task intent, so the calling agent can select the necessary Operations and perform any
Spec, paired metadata or registry edits directly.

A separately selected component request requires a current accepted parent plan and Spec/registration
revision, and must match the derived parent task intent and constraints;
that admission preserves the root change owner and grants only the selected component's own context.
When retried, implementation accepts component completion only for that same intent, current Spec
and implementation revision and complete tasks. It validates shared contract structure before its
own programmer runs, records component revisions and exact local completion, and leaves checks,
independent review, readiness and delivery to explicit later calls. A subsequent participant edit
invalidates dependent evidence rather than starting an automatic stabilization loop.

### Precise specifications {#implementation-precise-specifications}

The Implementation Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Its behavior is realized in
its own package `src/concorde/implementation/`, bound by its adapter entity together with its `operations/` declaration; this Spec boundary
does not itself create an Agent grant or configurable arbitrary graph; public exposure is explicit in the catalog. Host admission, phase
artifacts and permissions remain mandatory. A new graph requires declared composition and an
implementation of its sequencing, artifact admission, recovery and completion policies before it
can execute. [Harness admission](../harness/admission.md) realizes the common entry and invocation
host, and [Operations](../operations/execution-reference.md#graphs-dispatch-graphs) the dispatch
that reaches this provider.

## Native implementation boundary

Public implement has no Graph/Pi-RPC fallback. Shared finite preparation validates current plan/tasks,
intent, required Spec review, exact selected feedback and separately completed component revisions
before any native launch. Missing components return selectable work without launching a programmer.
A code-free parent with current separately completed components can finish deterministically.

The actual code workspace is `native_workspace` in the frozen index; `intended_write_paths` are
absolute candidate file/directory roots. The capsule cwd is only discovery/context delivery. No
implementation copies are used as the destination of writes. Specs, metadata, registry, configuration,
other worktrees, governing integration and unrelated paths remain excluded by explicit model policy.
The native Agent is terminal; file bounds and network/credential abstention are not OS restrictions.
`run_checks` accepts no command/path arguments, uses the existing Host configured-check service and
its enforced read-only subprocess boundary, and honors configured check timeouts/cancellation.

Expected implementation content/new-file changes do not invalidate the frozen input identity:
acceptance validates against the issued snapshot and rechecks its immutable contracts/listing entries,
registry/configuration, exact plan/tasks/intent/feedback and component evidence, while allowing the
selected implementation bytes/file membership to change. Explicit feedback is checked before launch;
its expected code repair does not make that frozen feedback spuriously stale afterward. Newly changed
feedback records, contracts or task state still reject. Returned task IDs/targets/descriptions/
acceptance must be exact, complete and materialized. Native failure/cancellation or invalid output
leaves partial edits but never accepts completion or triggers review/readiness/delivery/integration.
