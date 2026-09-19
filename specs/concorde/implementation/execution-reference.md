# Implementation execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Implementation Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Acceptance task](../planning/tasks.md#terminology) | Defined in Making work verifiable. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Entity](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |

## Implementation operation {#implementation-implementation-operation}

[Harness admission](../harness/admission.md) owns the entry. Its [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound operation in the [current adapter inventory](../operations/execution-reference.md#operations-current-host-adapter).
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

### Coordination Graphs

A composite Module's implementation runs the component coordination Graph, which finishes with
the shared candidate stabilization Graph. Each Graph Spec follows the
[Graph Spec convention](../harness/execution-reference.md#graphs-and-loops-graph-specs): its
State, Nodes and Edges are stated in turn, and its diagram is bound to its compiled Graph by
`%% graph:` and kept equal to it by the configured Graph Spec check.

#### Component coordination Graph (`coordination_graph`) {#graphs-component-coordination-graph-coordination-graph}

A composite Module's implementation runs this Graph when its tasks name submodules or used Modules.

**State.** `output` (a blocking result, or none while the Graph advances), `route`; the candidate's
target record carries the coordination table (per component: task, Spec and implementation
status, digests, gaps) and the local task list.

**Nodes.** The work-item nodes run the [Sequential work items Graph](../harness/execution-reference.md#host-sequential-work-items-graph-batch-graph).

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `reconcile_specs` | Sequential work items: each component runs `concorde-specify` from its own contract until its Spec is current. | component tasks, component Specs | reconciled Specs, coordination table |
| `validate_specs` | Deterministic repository validation across every participant's contract. | Spec collections | validation, phase |
| `implement_components` | Sequential work items: each component runs its own development Graph (`specify=false`) in this candidate. | component tasks, component grants | component implementations, review artifacts |
| `implement_local` | One programmer `implementation` invocation for the composite's own tasks. | local tasks, local files | completed local tasks |
| `finalize_components` | The stabilization Graph (below): every participant's final checks and reviews until the shared candidate is stable. | candidate | component revisions, evidence |
| `record_completion` | Deterministic: tasks marked complete, component revisions and implementation digest recorded. | coordination table | completed target record |

**Edges.** After every step a conditional edge reads `output`: a step that recorded a blocking
result ends the Graph with it, and a step that left `output` empty advances to the next step, so
the steps run strictly in the order of the table. `record_completion` always ends the Graph.

```mermaid
flowchart TB
    %% graph: coordination_graph
    accTitle: Component coordination Graph
    accDescr: Component Specs are reconciled and validated, components and local code are implemented, and every participant is finalized until stable before completion is recorded; a blocked step ends the Graph with that result.
    __start__["start"]
    reconcile_specs["reconcile_specs<br/>in: component tasks, component Specs<br/>out: reconciled Specs, coordination table"]
    validate_specs["validate_specs<br/>in: Spec collections<br/>out: validation, phase"]
    implement_components["implement_components<br/>in: component tasks, component grants<br/>out: component implementations, review artifacts"]
    implement_local["implement_local<br/>in: local tasks, local files<br/>out: completed local tasks"]
    finalize_components["finalize_components<br/>in: candidate<br/>out: component revisions, evidence"]
    record_completion["record_completion<br/>in: coordination table<br/>out: completed target record"]
    __end__["end"]
    __start__ --> reconcile_specs
    reconcile_specs -->|every component Spec current| validate_specs
    reconcile_specs -->|component blocked| __end__
    validate_specs -->|contracts consistent| implement_components
    validate_specs -->|incompatible contracts| __end__
    implement_components -->|components implemented| implement_local
    implement_components -->|component blocked| __end__
    implement_local -->|local tasks complete| finalize_components
    implement_local -->|local work blocked| __end__
    finalize_components -->|candidate stable| record_completion
    finalize_components -->|verification failed| __end__
    record_completion --> __end__
```

#### Shared candidate stabilization Graph (`stabilization_graph`) {#graphs-shared-candidate-stabilization-graph-stabilization-graph}

**State.** `output` (a failed participant's result), `route`; the enclosing coordination holds the
participant set and a bounded remaining-round counter, because a later participant's repair can
stale an earlier participant's evidence.

**Nodes.**

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `snapshot` | Deterministic: digest of every participant's implementation before this round; an exhausted round budget fails. | participant implementations | round digest |
| `verify_components` | Sequential work items: each participant's final development Graph (`specify=false`, `finalize_components`) runs its checks and required reviews. | participant records | evidence, review artifacts |
| `check_stability` | Deterministic: the candidate digest after verification equals the round digest. | round digest, participant implementations | route |

**Edges.** `snapshot` always continues to `verify_components`. After verification a conditional
edge reads `output`: a failed participant ends the Graph, otherwise `check_stability` runs.
`check_stability` writes `route`: when verification changed the candidate the round repeats from
`snapshot`, and when it did not the Graph ends. The round budget checked in `snapshot` bounds the
loop.

```mermaid
flowchart TB
    %% graph: stabilization_graph
    accTitle: Shared candidate stabilization Graph
    accDescr: Each round snapshots the candidate, verifies every participant and repeats while a repair changed the candidate; a failed participant ends the Graph.
    __start__["start"]
    snapshot["snapshot<br/>in: participant implementations<br/>out: round digest"]
    verify_components["verify_components<br/>in: participant records<br/>out: evidence, review artifacts"]
    check_stability["check_stability<br/>in: round digest, participant implementations<br/>out: route"]
    __end__["end"]
    __start__ --> snapshot
    snapshot --> verify_components
    verify_components -->|every participant verified| check_stability
    verify_components -->|participant failed| __end__
    check_stability -->|candidate changed| snapshot
    check_stability -->|candidate stable| __end__
```

### Precise specifications {#implementation-precise-specifications}

The Implementation Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Its behavior is realized in
its own package `src/concorde/implementation/`, bound by its adapter entity together with its `operations/` declaration; this Spec boundary
creates no public Skill, Agent grant or configurable arbitrary graph. Host admission, phase
artifacts and permissions remain mandatory. A new graph requires declared composition and an
implementation of its sequencing, artifact admission, recovery and completion policies before it
can execute. [Harness admission](../harness/admission.md) realizes the common entry and invocation
host, and [Operations](../operations/execution-reference.md#graphs-dispatch-graphs) the dispatch
that reaches this provider.
