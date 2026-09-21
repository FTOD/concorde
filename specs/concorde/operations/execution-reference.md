# Operation catalog and dispatch contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Operations Module](module.md): the catalog of every Operation, the ownership of each Operation's
behavior and the dispatch that routes an admitted request to its provider. Explanatory topics
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

An **Operation** is an executable entity that can be used as a LangGraph node. It declares its
input State, output State updates, effects and usage conditions. Its implementation can be
ordinary deterministic code, a model invocation or a compiled LangGraph subgraph. These are
implementation choices, not separate entity kinds. A Graph is a graph that composes Operations;
a compiled Graph can itself be used as an Operation node.

**Operation** is the canonical executable identity. The parallel **Agent** executable registry is retired. A worker is a runtime process executing a
model-backed Operation, not another definition of what the Operation does. A model execution
profile records instructions, tools, context/effect limits and timeout on that Operation.
Lowercase _operation_ still describes an ordinary action such as a filesystem or Git operation.
A helper function need not be registered merely because Python permits calling it from a node.

#### State and runtime boundaries {#operations-state-and-runtime-boundaries}

Each entry under `operations/` declares `STATE` and `run(state, runtime)`. The State contract
provides LangGraph input and output schemas. Model nodes consume the admitted task-context fields
and return validated result fields. Existing host-backed graph adapters consume request-data
fields and return a `result` channel containing the complete operation envelope, preserving
blocked, failed, cancelled and successful outcomes rather than flattening them into success data.
`REQUEST` and `RESPONSE` remain the versioned transport schemas of those existing host adapters;
they are not a second executable interface for model nodes.

A node receives only its declared input channels and returns only its output update, never a copy
of the entire parent State. Each graph declares reducers when parallel writers need to merge a
shared channel. Compatible compiled graphs can be embedded directly; incompatible channels require
an explicit adapter. Parent State membership is not permission to read files or implementation
contents. Frozen contexts and the executor's independent permission checks still apply.

Hosts, model launchers and project configuration are trusted `Runtime.context`, not writable State
channels or task-controlled callable objects. Model State validation checks both the wire shape and
the profile's phase, admitted artifacts, outcome and populated result fields. The worker executor
also rechecks its byte-bound instructions and effective authority before launching a process.

The existing `agent` record fields, `concorde-agent-stage-*` wire identities, generated instruction
paths under `generated/agents/`, stable Spec anchors and historical event names are compatibility
spellings. They identify the executing model Operation and do not recreate an Agent registry.

#### Current host adapter {#operations-current-host-adapter}

Each public Operation has exactly one public name in the Pi catalog and launcher entry
`scripts/run-operation.py <public-name>`. Non-public Operations have neither a catalog entry nor
a direct launcher entry. [Distribution Module](../distribution/module.md) owns the ordinary
Operation guidance sources and Pi projection; [Harness](../harness/admission.md) owns shared
admission and this Module owns dispatch. Guidance describes use of the Operation, not the
worker's task context or another executable kind.

| Operation                | Public | Context selection | Deterministic | Uses                                             | Behavior                                                             |
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

The seven model-backed entries named in this table are themselves private, bound Operations
with `DETERMINISTIC=false` and no composed `USES`. Their detailed task State contracts, tools and
effects are defined in [model execution profiles](../harness/execution-reference.md). A bound
model node consumes one host-frozen complete Module context without independently selecting more
Modules. Target selection belongs to the outer caller, not a model router.

#### Operation properties {#operations-operation-properties}

Every Operation declares:

- **PUBLIC**: a boolean; true requires exactly one Pi catalog name and launcher entry.
- **CONTEXT_SELECTION**: `bound` or `none`. Bound consumes a caller-selected context frozen by the host;
  none performs host work without model context.
- **DETERMINISTIC**: a boolean; true means no supported path calls a model, including transitive
  `USES`. It does not promise purity, reproducible filesystem observations or absence of effects.
- **USES**: the directly composed Operation identities. It is the sole composition relation,
  including calls to model nodes. It grants no additional context or write authority.
- **STATE**: the input and output State contract. Runtime schema and effect validation remain
  necessary even when LangGraph accepts the Python type declaration.
- **PROFILE**: optional model execution configuration, or `None`; it has the same identity as its
  Operation and never registers a second executable entity.

`AGENTS` and `CLASS` declarations are rejected. `USES` must name registered entries, be duplicate
free and have no definition cycle in this adapter. Bounded runtime loops and per-target recursive
execution remain graph control flow, not cyclic definition dependencies. Actual ordering, branches,
loops and reducers live in LangGraph, not a duplicate metadata graph. Undeclared composition fails
with `undeclared_operation`; host composition never grants a worker another callable tool.

The single `concorde.operations` metadata inventory records exposure, context selection,
determinism, `public_name`, direct uses, State type identities and optional profile workspace/tools.
`public_name` equals the public Operation's `EXTERNAL_NAME`, and is null for private Operations.
Validation compares it with code and independently checks exact guidance membership. The retired
`skill` key is rejected, not accepted as an alias. This is an explicit project metadata migration;
metadata schema 2 and runtime wire versions retain their existing meanings. There is no independent `concorde.agents` inventory.

### Design {#operations-design}

#### Behavioral ownership and composition limits {#operations-behavioral-ownership-and-composition-limits}

Every Operation, including each model-backed worker, has exactly one canonical behavioral owner.
The owner's Specs explain what the Operation is for, what it takes and returns and when it stops;
this table maps each Operation to its owner and execution adapter. Model-backed local entries and
explicit Studio execution first pass the [admission](../harness/admission.md#graphs-operation-admission-graph-operation-graph) and
[dispatch](#graphs-operation-dispatch-graph-dispatch-graph) Graphs, and every model-backed worker
runs as one [Operation node](../harness/execution-reference.md#host-operation-node-operation-node).

| Operation or action                                                | Canonical behavioral owner                    | Runs as                                                                                                                                                                                                          |
| ------------------------------------------------------------------ | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| context-solve, plan, tasks; context-assessor, planner, task-author | [Planning](../planning/module.md)             | The [planning Graph](../planning/execution-reference.md#plan-planning-graph-plan-graph) for plan; a prepared native Agent for public context-solve; one worker node for tasks                                    |
| implement; programmer                                              | [Implementation](../implementation/module.md) | One local programmer node after checking separately completed component work                                                                                                                                     |
| spec-review, code-review; spec-reviewer, code-reviewer             | [Review](../review/module.md)                 | Target admission, then one reviewer node for the owner and each changed-file peer                                                                                                                                |
| validate                                                           | [Validation](../validation/module.md)         | Direct Host service; explicit Studio node                                                                                                                                                                        |
| deliver                                                            | [Delivery](../delivery/module.md)             | Direct Host service; explicit Studio node                                                                                                                                                                        |
| issues; issue-solver                                               | [Issues](../issues/module.md)                 | The bounded native Issue workflow and flattened independent verification calls |
| init                                                               | [Spec](../spec/initialize.md)                 | Direct Host service; explicit [Studio project Graph](../spec/contracts.md#graphs-project-graph-project-graph)                                                                                                    |
| configure                                                          | [Distribution](../distribution/module.md)     | Direct Host service; explicit Studio project Graph                                                                                                                                                               |

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

For model-backed local entries and explicit Studio execution, Operations dispatches through two LangGraph Graphs: the dispatch Graph and
the target admission Graph it composes. Harness runs its
[admission Graph](../harness/admission.md#graphs-operation-admission-graph-operation-graph) around
them. The composed Graphs a dispatch leaf runs (planning, project and Issues) are specified by their
owning Modules. Each Graph Spec follows the
[Graph Spec convention](../harness/execution-reference.md#graphs-and-loops-graph-specs): its State,
Nodes and Edges are stated in turn, and its diagram is bound to its compiled Graph by `%% graph:`
and kept equal to it by the configured Graph Spec check.

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

Model-backed leaves use the [Operation node](../harness/execution-reference.md#host-operation-node-operation-node)
contract. The seven private model nodes are reached only through declared composition;
appearing in the union dispatch diagram does not expose a public entry. Studio wraps a public entry with invocation validation and displays these same
operation/subgraph factories, rather than defining another business workflow.

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
It runs finite common admission directly, not the dispatch Graph. The retained dispatch node is an
explicit State/Studio adapter which refuses absent native transport; its diagram is not a claim that
native assessment traverses a Graph. Planning now uses the authored two-child native workflow; tasks use the direct native task-author.
