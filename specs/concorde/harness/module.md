# Harness

## Purpose

The Harness Module admits every operation request at one common boundary, then prepares and runs each worker the request needs with a defined task, information and permissions, and checks the result. It also runs configured checks in a separate read-only environment. Other Modules rely on it to execute work without treating an agent answer as permission for unrelated actions.

## Terminology

| Term                                              | Meaning / definition                                                                                                                                                                                                                                                  |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Worker profile                                    | The instructions and maximum tools, workspace and effects available to a kind of worker; a particular job can be narrower.                                                                                                                                            |
| Tool gate                                         | The checks applied inside the agent process before a model-requested tool runs.                                                                                                                                                                                       |
| Worker sandbox                                    | The operating-system boundary around a worker process: the host filesystem read-only with the developer's secret locations, agent-client state and other worktrees masked, the grant and run directory writable, a private temporary directory and process namespace. |
| Capsule                                           | A temporary workspace containing the documents admitted for one Spec-only worker invocation.                                                                                                                                                                          |
| [Worker](../module.md#terminology)                | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Harness](../module.md#terminology)               | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Context](../module.md#terminology)               | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Grant](../module.md#terminology)                 | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Snapshot](../module.md#terminology)              | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Operation](../module.md#terminology)             | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Host](../module.md#terminology)                  | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Graph](../module.md#terminology)                 | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Candidate](../module.md#terminology)             | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Worktree](../module.md#terminology)              | Defined in Concorde Framework.                                                                                                                                                                                                                                        |
| [Spec context](context.md#terminology)            | Defined in What information a worker receives.                                                                                                                                                                                                                        |
| [Implementation context](context.md#terminology)  | Defined in What information a worker receives.                                                                                                                                                                                                                        |
| [Resource context](context.md#terminology)        | Defined in What information a worker receives.                                                                                                                                                                                                                        |
| [Task context](context.md#terminology)            | Defined in What information a worker receives.                                                                                                                                                                                                                        |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions.                                                                                                                                                                                                                                   |

## Usage

Every public operation request first passes [Operation admission](host.md): it checks the request
and configuration, binds the worktree the request was started in, relays a consumer-project mutation
from primary into a host-created candidate, and hands the admitted request to the
[Operations dispatch](../operations/module.md). The request's result envelope always keeps
admission, domain and execution outcomes apart. Source-primary mutations instead stop for a fresh
catalog-free writer in an assigned candidate and a separate sibling tester; relay is not a
self-maintenance exception.

A calling workflow gives the Harness Module one worker job or one configured check. Harness fixes the allowed
inputs and permissions, starts the job, and validates its matching result before the caller proceeds.
Spec-only workers receive specification information; code access is a separate phase-specific choice.

For example, a planner can describe a change without reading source. A programmer later receives
accepted tasks and allowed code files; a reviewer receives read-only inputs in a fresh conversation.
The workers share accepted artifacts, not all of each other's knowledge or authority.

Failures, cancellation, time limits and changed inputs stop dependent execution. Authorized code edits
may remain after failure and require inspection. Every worker process runs inside the worker sandbox,
so an authorized shell command is bounded too: it can write only the grant, cannot read the
developer's secrets or other worktrees, and never sees the host's temporary files. **The network is
not restricted, the masked secret locations are a fixed list, and the sandbox requires Linux with
bubblewrap; an unavailable sandbox refuses the launch.** Configured checks use a separate read-only
boundary of the same kind. Read [execution](execution.md) for these limits before relying on
isolation. Policy preview shows access without running an agent.

## Design

<a id="entity.harness.agent-model"></a><a id="entity.harness.agent-definitions"></a><a id="entity.harness.typed-values"></a>

The Operation and Harness model defines a worker's task contract, effects, workspace, tools and
timeout. The Model execution profiles service combines the authored role and Python profile into a reproducible
WorkerBinding, using fresh instructions supplied by [Distribution Module](../distribution/module.md). The Typed values layer validates the
contracts and handoffs; knowing a type or worker name does not itself grant access. This keeps
instruction identity separate from the project knowledge a worker may read.

<a id="entity.harness.context"></a><a id="entity.harness.permissions"></a>

Context resolution freezes the selected Module's complete document units, implementation names,
external references and admitted task artifacts. Both reading and metadata source bytes participate
in identity. The Permissions compiler intersects declared effects with host authority for that phase; metadata
never becomes writable merely because a programmer can change the implementation it names.
A changed binding, source member or reference selection requires a fresh context.

<a id="entity.harness.agent-execution"></a><a id="entity.harness.pi-worker-runtime"></a><a id="entity.harness.pi"></a>

Worker execution independently rechecks the binding and grant before asking the Pi worker runtime
to start a fresh Pi RPC process. Its extension gates terminal worker tool calls. Workers do their admitted node work directly;
only the LangGraph/host schedules other work. One matching submitted
result is required, not merely a successful exit. Cancellation, time limits and invalid completion
remain distinct. The Pi process runs inside the worker sandbox derived from the same grant, so the
tool gate bounds what the model may ask and the sandbox bounds what the process can reach;
[execution](execution-reference.md#execution-design) details both boundaries and what they leave open.

Operation admission, explained in [preparing and coordinating work](host.md), uses the same request, workspace and configuration checks before dispatch selects a provider.
Deterministic Host tools run those services directly; model-backed entries and explicit Studio
adapters use the [admission Graph](admission.md#graphs-operation-admission-graph-operation-graph). Keeping admission in the Module that also
binds workers means the same boundary decides which request may run, in which workspace and with
which configuration, and later decides what each of its workers may read and write.

<a id="entity.harness.studio"></a><a id="entity.harness.worktree-lifecycle"></a><a id="entity.harness.langgraph"></a>

LangGraph Graph-API [Host Graphs](host.md) compose deterministic steps and worker invocations.
Studio inspects and observes those same executable graphs rather than a separate schematic model.
Worktree lifecycle binds candidate identity, phase and progress and checks the mutation boundary.
Only admitted typed artifacts cross stages; a model decision cannot advance lifecycle state or
broaden another invocation's permission.

### Flow overview

This conceptual view shows the common boundary around an Operation, not its executable node
catalog. Admission fixes which request may run and where; each worker then receives its own
narrow grant. A successful process exit alone is not an accepted result. The Host preserves the
difference between a business stop, invalid output and execution failure when reporting back.

For exact State channels, node inputs/outputs and routing, open the full
[Operation admission Graph Spec](admission.md#graphs-operation-admission-graph-operation-graph).
The [Operation node Graph Spec](execution-reference.md#host-operation-node-operation-node) defines
one embedded worker's input/output boundary; the
[Sequential work items Graph Spec](execution-reference.md#host-sequential-work-items-graph-batch-graph)
defines how repeated reviews or component jobs stop at the first blocking item. Neither grants
one item another item's context.

```mermaid
flowchart LR
    accTitle: Operation admission and execution flow overview
    accDescr: Check the request, workspace and configuration before dispatching the selected behavior. Workers receive separate bounded invocations as needed. Return the admitted result or a precise stop without widening authority.
    request["Receive an Operation request"]
    admit["Check request, workspace and configuration"]
    execute["Run the selected behavior with bounded invocations"]
    finish["Return accepted output or an explicit stop"]
    request -->|enter the common boundary| admit
    admit -->|admitted in the correct workspace| execute
    admit -->|rejected or unavailable boundary| finish
    execute -->|validate results and preserve failure distinctions| finish
```

## Relationships

Each invocation is the unit of work this Module executes. Its Spec context is the selected
Module's complete one-level owned/reference context; its implementation context is the
Protocol-defined set of files the Module's own entities bind — every phase sees their names, only
the programmer and code reviewer see authorized contents; its resource context is
its worker's tools together with the Module's declared external references, whose readable files
reach the planner, task author, programmer and code reviewer read-only; its task context is the
task, constraints, stage artifacts and lifecycle metadata. The frozen closure is never empty and its
identity covers every admitted byte.

A worker definition binds its role Spec, one task contract, a workspace kind, tools and timeout.
Resolution yields an `WorkerBinding` that every invocation carries and the executor reverifies.
Permissions are compiled purely from the contract's effects and host authority, guarded by the
isolated-worktree check before any unsafe mutation, and handed to the Pi worker runtime, whose
extension gates every tool call of the terminal worker and whose sandbox confines the
process to that same grant. Model-backed control flow remains a LangGraph Graph; deterministic Host tools need no compiled
Graph for local admission or dispatch. Failures never retry with broader
permissions, and a settled process alone never establishes completion.

```mermaid
flowchart TB
    accTitle: Harness entities and relationships
    accDescr: The Operation and Harness model defines the worker profile and contract records that Model execution profiles bind and that Worker execution runs. Model execution profiles resolve a verified binding for Worker execution and render instructions through Distribution. Permissions compiles the effective policy for Worker execution, guarded by an isolated Worktree lifecycle boundary. Context resolution supplies Spec, implementation and task context to Worker execution, resolves documents and file listings from Spec, and admits Protocol assets rendered by Distribution. Typed values validates the typed records Context resolution freezes and Worker execution admits. Studio starts or observes the same operation host as Worker execution. Operation admission binds candidate workspaces through Worktree lifecycle, validates envelopes and requests through Typed values and hands admitted requests to the Operations dispatch. Worker execution launches each worker through the Pi worker runtime, which runs it in RPC mode on Pi without worker delegation.
    agentModel["Operation and Harness model"]
    agentDefs["Model execution profiles"]
    permissions["Permissions"]
    execution["Worker execution"]
    context["Context resolution"]
    typedValues["Typed values"]
    worktree["Worktree lifecycle"]
    studio["Studio"]
    admission["Operation admission"]
    operations["Operations"]
    spec["Spec"]
    distribution["Distribution"]
    langgraph["LangGraph"]
    piRuntime["Pi worker runtime"]
    pi["Pi"]
    agentModel -->|defines worker profile and contract records for| agentDefs
    agentModel -->|supplies profile, contract, WorkerBinding and selection records to| execution
    agentModel -->|declares maximum effects for| permissions
    agentModel -->|supplies the host environment allowlist to| piRuntime
    agentDefs -->|resolves a verified WorkerBinding for| execution
    agentDefs -->|renders instructions and attests freshness through| distribution
    permissions -->|compiles the effective policy for| execution
    worktree -->|verifies an isolated mutation boundary for| permissions
    context -->|supplies Spec, implementation and task context to| execution
    context -->|resolves documents, identities and entity file listings from| spec
    context -->|admits Protocol assets rendered by| distribution
    context -->|freezes typed stage inputs and records through| typedValues
    context -->|supplies the declared reference documentation of| langgraph
    execution -->|validates typed results and schemas through| typedValues
    execution -->|schedules worker nodes and Studio graphs with| langgraph
    execution -->|launches each worker through| piRuntime
    studio -->|starts or observes the same operation host as| execution
    admission -->|binds candidate workspaces through| worktree
    admission -->|hands admitted requests to the dispatch of| operations
    admission -->|validates envelopes and requests through| typedValues
    piRuntime -->|runs each worker in RPC mode on| pi
```

## Reading by responsibility

The following topics explain how to use each Harness boundary. Their exact requirements and
acceptance cases belong to the Harness Module's [requirements](requirements.md) and
[scenarios](scenarios.md), rather than to the topic pages.

### Context freezing

Realized by `resolve_context` and its recheck; see
[context](context.md).

### Operation profile and Harness binding

Realized by `worker_profile` and `resolve_worker`; see [Agents and Harnesses](agents-and-harnesses.md)
and [runtime values](runtime-values.md).

### Permission compilation

Realized by `compile_policy` and the worktree boundary check; see [permissions](permissions.md).

### Operation admission

Realized by `run_operation`, `operation_graph_nodes`, `bind_worktree` and `json_main`; see
[host](host.md) and the [admission contracts](admission.md).

### Worker execution

Realized by `launch_worker`, the one launch sequence every model-backed stage runs through,
`WorkerExecutor` and the Pi worker runtime; see [execution](execution.md) and [host](host.md).

The deterministic check executor's read-only filesystem, scratch, result, unavailable-backend and
process-lifetime cases are defined in [Harness scenarios](scenarios.md#scenario.harness.check-read-only).
The Pi RPC client, worker launch, tool gate and terminal worker scenarios are defined in
[Harness scenarios](scenarios.md#scenario.harness.pi-worker-launch). See [every tool call is
gated](requirements.md#req.harness.worker-gate), [a capsule grants only its own snapshot](requirements.md#req.harness.capsule-closed),
[closed process inputs](requirements.md#req.harness.process-inputs-closed), [workers cannot delegate](requirements.md#req.harness.delegation-one-level) and [only the submitted result leaves the
worker](requirements.md#req.harness.worker-single-result).

### Typed value validation

Realized by `typed`, `validate_typed`, `json_schema`, `decode`, `canonical` and the schema
evaluator; see [typed values](typed-values.md).

## Local collaboration agreements

These entries describe the exact direct providers registered for this Module. They state
relied-upon behavior from this Module's perspective without importing another Module's documents.

### Spec

<a id="entity.harness.spec"></a><a id="agreement.document.harness.module.1"></a>

The [Spec Module](../spec/module.md) owns the project Spec model: the pinned Protocol binding, the explicit registry, structural validation, stable-ID file-set queries and honest initialization.

Admit the registry and resolve identities, document collections, entity file listings and file ownership.

This collaboration applies when freezing any context kind or checking a target, focus or binding.

- [Resolve the full one-level context and own implementation bindings; rebuild snapshots after changes](../spec/contracts.md#registry-stable-id-spec-context-queries)

### Operations

<a id="entity.harness.operations"></a><a id="agreement.document.harness.module.3"></a>

The [Operations Module](../operations/module.md) owns the catalog of every Operation and the dispatch that routes an admitted request to its provider.

Admit only registered public entries and declared composition, then dispatch each admitted request through the direct Host-tool path or its declared Graph adapter.

This collaboration applies when admission executes an admitted request or checks a child Operation against its parent's declared composition.

- [Operation catalog](../operations/execution-reference.md#operations-operation-registry); refuse unknown and non-public entries with `unknown_operation` and undeclared composition with `undeclared_operation`, never routing by name outside the catalog.
- [Dispatch Graph](../operations/execution-reference.md#graphs-operation-dispatch-graph-dispatch-graph); adopt its typed output, or a relayed candidate's complete envelope, as the invocation's result.

### Distribution

<a id="entity.harness.distribution"></a><a id="agreement.document.harness.module.2"></a>

Build authored projections, install and configure owned integrations, provision the managed runtime and keep a source checkout's own projections bound to the worktree that built them.

Render Agent instructions and Protocol assets from authored sources and attest their freshness.

This collaboration applies when resolving an Agent binding, admitting the Protocol rule bundle,
or preparing consumer worktree execution. Harness admits the explicit invoking package, bootstraps
only its newly created consumer candidate, and verifies/reuses local installations on resume and
installed entry admission. It relies on Distribution's ownership-preserving complete-install
[service](../distribution/contracts.md#local-installation-service); failure blocks before a worker,
retains the candidate and requires explicit installation recovery. The host keeps the target
quiescent; receipt verification supplies no task, Protocol acceptance or lifecycle authority.

- [Load only fresh, source-traceable instructions and pinned rule assets](../distribution/build.md)

## Unresolved information

- Resource context carries only the Module's declared external references and each worker's
  profile tools today: no worker admits an Operation or Tool reference beyond them, so those
  contracts are not yet snapshot fields. Materializing them in the snapshot record, with their
  identities in the context digest, is pending implementation work that must not widen any grant.
- The worker sandbox does not restrict the network, because Pi must reach its model provider.
  Anything the process can read, including the workspace, can therefore leave the sandbox over the
  network. Closing this needs a private network namespace in which only the credential proxy
  below is reachable; that is pending.
- The provider credentials the worker itself uses are readable inside the sandbox: the run
  directory holds the copied `auth.json` and `models.json`, and the Pi process environment carries
  the provider key variables, which the gate unsets only for each shell command. A shell command
  can read that copy and, with the shared network, send it out. The pending credential broker
  keeps the real credentials on the host: a loopback proxy that adds the authorization and
  performs the OAuth refresh, with the run's `models.json` pointing Pi at the proxy under a
  placeholder key, so no real credential enters the sandbox.
- The sandbox's secret masks are the fixed list `MASKED_HOME_PATHS`, not a discovery of every
  credential a developer keeps; a secret stored elsewhere under the home directory stays readable.
  Toolchains under the home directory stay readable on purpose, so workers can run tests.
- A pending write entry becomes an empty placeholder file or directory in the candidate before
  the launch and is removed only if the worker left it empty; a placeholder is the price of an
  exact write boundary for a path that does not exist yet.
- The sandbox requires Linux with a trusted system bubblewrap and refuses every worker launch
  elsewhere; there is no unconfined fallback and no backend for another platform yet.
- A relayed consumer candidate executes only its own verified installation and managed interpreter.
  Source candidates require their own fresh private build and local environment instead; no host
  installs an ambient shim into a source checkout. Durable usage, results and logs remain only in
  primary-owned `.concorde/runs/`, with candidate source/runtime provenance. The requesting session
  receives the result and diagnostics; Studio in primary shows relay as one node. A host interrupt
  gives the launcher thirty seconds to cancel its worker before killing it. Missing or stale resumed
  installation requires explicit supported installer recovery, not silent reinstallation or fallback.
- Checks run by `run_checks` use the configured-check executor, but the worker receives only the tail
  of each check's log; whether a longer or structured report is needed is unresolved.

The Harness implements Protocol 10 ownership/reference resolution and independently versioned context handoffs. See [context migration status](context.md#implementation-status).
Referenced definitions remain read-only and do not enter local entity/file grants.

## Precise specifications

The Harness Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
