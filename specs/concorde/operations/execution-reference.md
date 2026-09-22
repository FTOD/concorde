# Operation catalog and dispatch contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Operations Module](module.md): explicit StateGraph composition, the compatibility capability
inventory and the dispatch that routes an admitted request to its business provider. Explanatory topics
introduce their purposes; exact identities, limits and transitions are retained here as the single
detailed contract.

## Terminology

| Term                                               | Meaning / definition                           |
| -------------------------------------------------- | ---------------------------------------------- |
| [Operation](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Public operation](module.md#terminology)          | Defined in Operations.                         |
| [Internal operation](module.md#terminology)        | Defined in Operations.                         |
| [Host](../module.md#terminology)                   | Defined in Concorde Framework.                 |
| [Graph](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Worker](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Worker profile](../harness/module.md#terminology) | Defined in Harness.                            |
| [Pi integration](../module.md#terminology)         | Defined in Concorde Framework.                 |
| [Context](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Grant](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Snapshot](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Spec context](../harness/context.md#terminology)  | Defined in What information a worker receives. |
| [Task context](../harness/context.md#terminology)  | Defined in What information a worker receives. |
| [Candidate](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Worktree](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Ready](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Evidence](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Issue](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Blocker](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Disposition](../issues/lifecycle.md#terminology)  | Defined in Solving a recorded problem.         |
| [Review coverage](../review/module.md#terminology) | Defined in Review.                             |

## Operation registry {#operations-operation-registry}

An **Agent** is a callable native Pi role, a **Workflow** an authored pi-subagents composition,
an **Operation** an explicitly selected StateGraph flow, and a **Host service** a finite non-model
action. Module ownership, context inclusion and these executable kinds remain independent.
`operations/` and the eleven public `concorde-*` request/response names are compatibility spellings,
not a mandate to execute every capability as a LangGraph node.

Agents owns the [canonical Agent definitions](../agents/roles.md), which carry `PROFILE` and
`KIND="agent"` with no `STATE`/`run` model-operation aliases. This Module inventories public
`CAPABILITIES`, `WORKFLOWS`, `HOST_TOOLS` and separately selected `STATE_OPERATIONS`. Public capability modules retain
the finite Python request/response adapter, `STATE` and `run` for wire compatibility. Those adapters
do not schedule cognition: the Pi entry prepares real native calls or authored workflows.

#### State and runtime boundaries {#operations-state-and-runtime-boundaries}

Only an explicitly selected StateGraph Operation exposes typed graph input/output channels and
trusted Runtime services. Its native launch/admission callable is supplied by the embedding; missing
service refuses. State cannot inject that callable or widen authority. A node projects declared
inputs and returns only its output update; the parent owns channel mapping and reducers. Optional
Graph composition is not a mirror of native workflow branches or a fallback for native failure.

Native Agents instead receive the Host-frozen task/context and native `outputSchema`. Their
`structured_output` is a proposal; stage gates are unaccepted; independent Host correlation and
currentness/business checks precede persistence. Tool ceilings and prompt-level file policy are
distinct. Compatibility `WorkerProfile`, `WorkerBinding`, wire identities and generated/agents paths
retain their contract/binding meaning without retiring the canonical Agent inventory.

#### Current host adapter {#operations-current-host-adapter}

Each public capability has exactly one public name in the Pi catalog and launcher entry
`scripts/run-operation.py <public-name>`. Non-public Operations have neither a catalog entry nor
a direct launcher entry. [Distribution Module](../distribution/module.md) owns the ordinary
capability guidance sources and Pi projection; [Harness](../harness/admission.md) owns shared
admission and this Module owns dispatch. Guidance describes use of the capability and its actual kind, not the
worker's task context.

| Compatibility capability | Public | Context selection | Deterministic | Uses                                             | Behavior                                                             |
| ------------------------ | ------ | ----------------- | ------------- | ------------------------------------------------ | -------------------------------------------------------------------- |
| issues                   | true   | bound             | false         | issue-solver, spec-review, code-review, validate | Inspect, report, reopen or solve a selected Issue without delivery   |
| init                     | true   | none              | true          | —                                                | Propose and apply explicit initialization                            |
| configure                | true   | none              | true          | —                                                | Apply model settings and explicit Protocol acceptance                |
| validate                 | true   | none              | true          | —                                                | Run deterministic checks and record readiness                        |
| deliver                  | true   | none              | true          | —                                                | Stage a candidate and clean up; merge only when explicitly requested |
| spec-review, code-review | true   | bound             | false         | spec-reviewer, code-reviewer                     | Read-only independent review with version-bound findings             |
| context-solve            | true   | bound             | false         | context-assessor                                 | Assess information sufficiency without context expansion             |
| plan                     | true   | bound             | false         | context-assessor, planner                        | Assess sufficiency, generate and persist a plan                      |
| tasks                    | true   | bound             | false         | task-author                                      | Derive acceptance tasks from the accepted plan                       |
| implement                | true   | bound             | false         | programmer                                       | Fulfil local tasks after caller-selected component work              |

The roles used by these adapters are defined once in [Agents](../agents/roles.md). Adapter `USES`
references those definitions; it does not own another role inventory or grant another context.

#### Operation properties {#operations-operation-properties}

Inventory entries declare `KIND`, `PUBLIC`, `CONTEXT_SELECTION`, `DETERMINISTIC`, `USES`, `PROFILE`
and `EXTERNAL_NAME`. `KIND` distinguishes `agent-entry`, `workflow` and `host` in the
compatibility adapter inventory; roles themselves belong to Agents. `PUBLIC` controls the eleven catalog/launcher names. `bound` means a
caller-selected context; `none` means Host work without model context. Determinism covers all
supported paths and transitive collaborators, not filesystem purity. `USES` records declared
collaborators, grants no file authority, has no duplicate or unknown entries and no definition cycle.

Domain Agent definitions have a profile and no `STATE`/`run`; public `agent-entry` adapters have
no role profile and retain `STATE`/`run` only for finite wire compatibility. Separately selected StateGraph Operations declare actual typed graph channels. Native
branches/loops belong in authored pi-subagents workflows; optional graph ordering/reducers belong
in StateGraph. A per-adapter `AGENTS` or obsolete `CLASS` declaration is not supported. The
canonical role inventory is `agents.AGENTS`, not a second Operations catalog.

The `concorde.operations` paired metadata records kind, exposure, context selection, determinism,
public name, direct uses, nullable State and profile. It matches compatibility adapter code exactly and excludes roles. The Agents-owned
`concorde.agents` metadata checks role family, distribution and registration independently. The retired `skill` key remains rejected. Catalog schema 2
is distinct from metadata schema 2 and the versioned request/result wire envelopes.

### Design {#operations-design}

#### Behavioral ownership and composition limits {#operations-behavioral-ownership-and-composition-limits}

Every capability has one canonical business owner; every role has one canonical definition in Agents. Native preparation and finite
request dispatch use common admission; no admission/dispatch Graph executes under these public
paths. Optional StateGraph Operations are explicitly selected through Harness's Operation API.

| Capability or role | Canonical behavioral owner | Execution |
| --- | --- | --- |
| context-solve, plan, tasks | [Planning](../planning/module.md) | Direct native assessor/task-author or authored assessor-then-planner workflow |
| implement | [Implementation](../implementation/module.md) | Direct native programmer after finite admission |
| spec-review, code-review | [Review](../review/module.md) | Authored native scope workflow |
| issues | [Issues](../issues/module.md) | Finite bookkeeping or bounded native decision/verification workflow |
| validate, deliver | [Validation](../validation/module.md), [Delivery](../delivery/module.md) | Finite Host services |
| init, configure | [Spec](../spec/initialize.md), [Distribution](../distribution/module.md) | Finite Host services |

Module ownership is distinct from node composition. `USES` is the executable composition relation;
registry `uses` describes Module responsibility dependencies. Shared model execution support does
not merge provider contracts. Every phase, target and independent review retains a fresh invocation
and its own grant. Only admitted structured artifacts cross node boundaries.

### Precise specifications {#operations-precise-specifications}

The Operations Module owns the exact obligations in [requirements](requirements.md) and
[scenarios](scenarios.md). The request and response types each Operation admits are listed with
[Harness's wire contracts](../harness/admission.md#operation-requests-and-responses).

## Dispatch Graphs {#graphs-dispatch-graphs}

### Design {#graphs-design}

Dispatch and target admission are finite Host services. The old Graph anchors below remain
addressable migration records, not current executable wrappers. Native workflows define their
actual model-call order; only separately selected StateGraphs have executable Graph Specs.

Public compatibility entries retain their request/response names without implying Graph execution:

| Public entry | Backend after finite admission |
| --- | --- |
| `concorde-issues` | Finite bookkeeping or bounded native decide/verify/decide/close/validate workflow. |
| `concorde-spec-review`, `concorde-code-review` | Authored native scope workflow with independently admitted terminal reviewers. |
| `concorde-plan` | Native assessor then planner workflow; Host persistence. |
| `concorde-context-solve`, `concorde-tasks`, `concorde-implement` | A fresh native terminal Agent; independent Host acceptance. |
| `concorde-init`, `concorde-configure`, `concorde-validate`, `concorde-deliver` | Finite deterministic Host services. |

Optional StateGraph Operations and Studio are explicit separate selections, not backends implicitly
chosen by these entries.

Native leaves use the canonical Agent profile and prepared native boundary. Studio displays the
separately selected genuine Operation graph, not public capability or workflow mirrors.

#### Operation dispatch Graph (`dispatch_graph`) {#graphs-operation-dispatch-graph-dispatch-graph}

This former runtime wrapper is retired. Native Agent/Workflow and finite Host services execute
the capability directly; no LangGraph mirror is claimed. The explicit optional StateGraph boundary
is [Terminal Agent Operation](../harness/execution-reference.md#host-operation-node-operation-node).


#### Target admission Graph (`target_graph`) {#graphs-target-admission-graph-target-graph}

This former runtime wrapper is retired. Native Agent/Workflow and finite Host services execute
the capability directly; no LangGraph mirror is claimed. The explicit optional StateGraph boundary
is [Terminal Agent Operation](../harness/execution-reference.md#host-operation-node-operation-node).


## Context selection participation

<a id="participation.document.operations.execution-reference.1"></a>

**Interface participation.** This Module has the required role for `contract.context.selection` version 3 with `module.harness`.

**When this applies.** When target admission binds a Module-bound invocation, before assessment,
planning, authoring or review for the selected Module.

**Relied-upon guarantee.** [Selection](../harness/contracts.md#contract.context.selection) determines the complete admitted contract and its original owners.

**Local obligation.** Supply the explicit Module and task; stop dependent transitions on gaps or stale context, and never treat included provider definitions as writable local Specs.

### Public context-assessment backend

Public context-solve prepares a real native context-assessor Agent and independently admits its
single-run result as specified by [Harness](../harness/execution-reference.md#native-context-assessor).
It runs finite common admission directly, not the dispatch Graph. Bare public Python execution refuses absent native transport; no dispatch or Studio Graph fallback
is selected. Planning now uses the authored two-child native workflow; tasks use the direct native task-author.

### Failure propagation across executable kinds

Dispatch, native workflows and explicitly selected StateGraph Operations preserve Harness's
[causal execution feedback](../harness/execution-reference.md#execution-feedback). Each parent adds
its operation/step context without replacing lower-level causes or treating an unaccepted proposal
as completion. A failed child stops dependent work; its native execution outcome remains separate
from any earlier durable domain receipt. Host refusals, invalid proposals and transport/observation
failures return to the caller, not to an automatic retry or alternate backend.
