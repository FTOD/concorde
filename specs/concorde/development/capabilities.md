# Capability registry

A **Capability** is an executable entity that can be used as a LangGraph node. It declares its
input State, output State updates, effects and usage conditions. Its implementation can be
ordinary deterministic code, a model invocation or a compiled LangGraph subgraph. These are
implementation choices, not separate entity kinds. A Flow is a graph that composes Capabilities;
a compiled Flow can itself be used as a Capability node.

**Capability** is the canonical executable identity. The former **Operation** name and the
parallel **Agent** executable registry are retired. A worker is a runtime process executing a
model-backed Capability, not another definition of what the Capability does. A model execution
profile records instructions, tools, context/effect limits, children and timeout on that Capability.
Lowercase *operation* still describes an ordinary action such as a filesystem or Git operation.
A helper function need not be registered merely because Python permits calling it from a node.

### State and runtime boundaries

Each entry under `capabilities/` declares `STATE` and `run(state, runtime)`. The State contract
provides LangGraph input and output schemas. Model nodes consume the admitted task-context fields
and return validated result fields. Existing host-backed graph adapters consume request-data
fields and return a `result` channel containing the complete capability envelope, preserving
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
spellings. They identify the executing model Capability and do not recreate an Agent registry.

### Current host adapter

Each public Capability has exactly one Skill invoking `scripts/run-capability.py <skill>`.
Non-public Capabilities have no Skill or direct launcher entry. Distribution owns the Skill
sources and projection; Development owns shared admission and dispatch. A Skill is an instruction
artifact for the developer's external runtime, not the worker's task context or a node kind.

| Capability | Public | Context selection | Deterministic | Uses | Behavior |
| --- | --- | --- | --- | --- | --- |
| main | true | discover | false | answerer, router, topology-designer, topology-author | Answer from selected Specs or prepare and apply accepted topology |
| dev-loop | true | discover | false | router, specify-loop, review, plan, tasks, implement, validate | Develop one change to a ready candidate |
| specify-loop | true | discover | false | router, specify, review | Complete Spec authoring and review before implementation |
| issues | true | bound | false | issue-solver, dev-loop, specify, review, validate | Inspect, report, reopen or solve a selected Issue without delivery |
| init | true | none | true | — | Propose and apply explicit initialization |
| configure | true | none | true | — | Apply model settings and explicit Protocol acceptance |
| validate | true | none | true | — | Run deterministic checks and record readiness |
| deliver | true | none | true | — | Stage a candidate and clean up; merge only when explicitly requested |
| specify | false | bound | false | spec-author | Author the bound target's Spec replacements |
| review | true | discover | false | router, spec-reviewer, code-reviewer | Read-only independent review with version-bound findings |
| context-solve | false | bound | false | context-assessor | Assess information sufficiency without context expansion |
| plan | false | bound | false | context-assessor, planner | Assess sufficiency, generate and persist a plan |
| tasks | false | bound | false | task-author | Derive acceptance tasks from the accepted plan |
| implement | false | bound | false | programmer | Fulfil tasks or coordinate participating components |

The twelve model-backed entries named in this table are themselves private, bound Capabilities
with `DETERMINISTIC=false` and no composed `USES`. Their detailed task State contracts, tools and
effects are defined in [model execution profiles](../harness/agents-and-harnesses.md). A bound
model node can consume a host-frozen discovery context without independently selecting more
Modules. Routing is explicit composition, not an implicit dependency added by a naming convention.

### Capability properties

Every Capability declares:

- **PUBLIC**: a boolean; true requires exactly one public Skill and launcher entry.
- **CONTEXT_SELECTION**: `discover`, `bound` or `none`. Discovery selects complete Module contexts;
  bound consumes an already selected/frozen context; none performs host work without model context.
- **DETERMINISTIC**: a boolean; true means no supported path calls a model, including transitive
  `USES`. It does not promise purity, reproducible filesystem observations or absence of effects.
- **USES**: the directly composed Capability identities. It is the sole composition relation,
  including calls to model nodes. It grants no additional context or write authority.
- **STATE**: the input and output State contract. Runtime schema and effect validation remain
  necessary even when LangGraph accepts the Python type declaration.
- **PROFILE**: optional model execution configuration, or `None`; it has the same identity as its
  Capability and never registers a second executable entity.

`AGENTS` and `CLASS` declarations are rejected. `USES` must name registered entries, be duplicate
free and have no definition cycle in this adapter. Bounded runtime loops and per-target recursive
execution remain graph control flow, not cyclic definition dependencies. Actual ordering, branches,
loops and reducers live in LangGraph, not a duplicate metadata graph. Undeclared composition fails
with `undeclared_capability`; host composition never grants a worker another callable tool.

The single `concorde.capabilities` metadata inventory records exposure, context selection,
determinism, Skill mapping, direct uses, State type identities and optional profile workspace/tools/
children. Validation compares it with code. There is no independent `concorde.agents` inventory.

## Design

### Behavioral ownership and composition limits

| Capability or action | Canonical behavioral owner |
| --- | --- |
| context-solve, plan, tasks | [Planning](../planning/module.md) |
| implement | [Implementation](../implementation/module.md) |
| specify | [Spec Authoring](../spec-authoring/module.md) |
| review | [Review](../review/module.md) |
| validate | [Validation](../validation/module.md) |
| deliver | [Delivery](../delivery/module.md) |
| main ask and routing | [Query and Routing](../query-routing/module.md) |
| main topology actions | [Topology](../topology/module.md) |
| dev-loop | [Development Flow](../dev-loop/module.md) |
| specify-loop | [Specification Flow](../specify-loop/module.md) |

Module ownership is distinct from node composition. `USES` is the executable composition relation;
registry `uses` describes Module responsibility dependencies. Shared model execution support does
not merge provider contracts. Every phase, target and independent review retains a fresh invocation
and its own grant. Only admitted structured artifacts cross node boundaries.

## Precise specifications

The Development Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
