---
id: module.concorde.operations
kind: module
parent: module.concorde
modules: []
features:
  - feature.operations.standard-development-loop
  - feature.operations.permission-bounded-planning
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-operations-system-overview.html
---

# Architecture: Operations

## Responsibility

Provide paired LangGraph control graphs that compose canonical direct Skills or public Operations
into stateful workflows and enforce one least-privilege Codex/Claude launch boundary per leaf.

## Boundary

Operations owns the shared graph runtime, trusted planning-context resolver, normalized policy/native
configuration compiler, injectable coding-agent process launcher, and each exact
`operations/<name>/{operation.py,SKILL.md}` pair. Python owns executable topology and occurrence
bindings; paired Markdown owns public invocation/behavior. Operations loads leaf prompts/effects from
Skills and Protocol 13 roles from Workspace, but does not duplicate prompts, define Runtime Tool
algorithms, provision the installed virtual environment, implement LangGraph/Codex/Claude sandboxes,
or treat prompt text as enforcement.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.operations.runtime` | program | Resolves ordered direct capabilities and bindings, builds lazy LangGraphs, attaches one immutable launch specification per leaf, preserves nested Operation opacity, and accumulates per-capability results. | `src/concorde/operation_runtime.py` |
| `entity.operations.definition` | type | Ordered unique stages plus exact direct capability occurrences and narrowing agent/effect bindings. | `src/concorde/operation_runtime.py#OperationBinding` |
| `entity.operations.state` | type | Original request plus append-only ordered capability results and optional enforcement receipts. | `src/concorde/operation_runtime.py#OperationState` |
| `entity.operations.permission-context` | program | Resolves selected/providing-module paths and exact project-owned required-interface feature specifications, skips explicitly external required providers, and denies provider internals, symlinks, escapes, and other attempts. | `src/concorde/planning_context.py#resolve_planning_context` |
| `entity.operations.policy-compiler` | program | Compiles leaf effects and occurrence bindings into canonical normalized policies plus Codex permission profiles or Claude strict-sandbox settings. | `src/concorde/operation_permissions.py` |
| `entity.operations.process-launcher` | program | Performs version/enforcement preflight and injectable `codex exec`/`claude -p` process handoff with structured receipts and no permissive retry. | `src/concorde/operation_executor.py#AgentProcessExecutor` |
| `entity.operations.plan` | program | Public two-stage context → author planning LangGraph over two internal leaves. | `operations/concorde-plan/operation.py` |
| `entity.operations.plan-skill` | document | Installed public planning invocation/policy/failure contract paired with the planning graph. | `operations/concorde-plan/SKILL.md` |
| `entity.operations.standard-dev-loop` | program | Four-stage specify → nested plan → tasks → deliver LangGraph over six direct public capabilities. | `operations/concorde-standard-dev-loop/operation.py` |
| `entity.operations.standard-dev-loop-skill` | document | Installed invocation, ordering, nested-planner, and failure contract paired with the standard graph. | `operations/concorde-standard-dev-loop/SKILL.md` |
| `entity.operations.reflections-triage` | program | Action/route-conditional investigation, planning/fast-loop, worktree implementation, and validation LangGraph. | `operations/concorde-reflections-triage/operation.py` |
| `entity.operations.reflections-triage-skill` | document | Installed reflection-triage/v5 branch/policy contract paired with its graph. | `operations/concorde-reflections-triage/SKILL.md` |
| `entity.operations.langgraph` | external-system | Graph runtime imported lazily for topology and pinned into the isolated environment by every successful native installation. | `external:langchain-ai/langgraph@1.2.11` |
| `entity.operations.coding-agent` | external-system | Codex/Claude host whose native or approved outer sandbox enforces each immutable launch specification. | `external:coding-agent` |
| `entity.operations.tests` | test | Topology, policy/path/parity, process-receipt, installation, projection, and fail-closed evidence. | `tests/concorde` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.operations.plan` | `implements` | `entity.operations.definition` | Declares exact context → author internal-leaf occurrences and bindings. |
| `entity.operations.standard-dev-loop` | `implements` | `entity.operations.definition` | Declares four public stages with opaque nested `concorde-plan`. |
| `entity.operations.reflections-triage` | `implements` | `entity.operations.definition` | Declares the complete static capability inventory and selects only action/route-reachable occurrences. |
| `entity.operations.plan-skill` | `documents` | `entity.operations.plan` | Supplies the public planning invocation/failure contract. |
| `entity.operations.standard-dev-loop-skill` | `documents` | `entity.operations.standard-dev-loop` | Supplies the public standard-loop contract. |
| `entity.operations.reflections-triage-skill` | `documents` | `entity.operations.reflections-triage` | Supplies the conditional triage contract. |
| `entity.operations.runtime` | `reads_from` | `module.concorde.skills` | Loads canonical direct capability bodies, exposure, and leaf effects. |
| `entity.operations.runtime` | `calls` | `entity.operations.permission-context` | Obtains exact project-relative role paths and source digest before planning launches. |
| `entity.operations.runtime` | `calls` | `entity.operations.policy-compiler` | Produces one normalized/native policy per direct leaf occurrence. |
| `entity.operations.runtime` | `calls` | `entity.operations.process-launcher` | Hands an immutable leaf launch to the optional real process executor. |
| `entity.operations.runtime` | `calls` | `entity.operations.langgraph` | Compiles ordered state/nodes/edges only when graph construction is requested. |
| `entity.operations.standard-dev-loop` | `calls` | `entity.operations.runtime` | Builds the standard graph without embedding prompts or planner internals. |
| `entity.operations.standard-dev-loop` | `composes` | `entity.operations.plan` | Uses only the public planning Operation identity and opaque result. |
| `entity.operations.reflections-triage` | `calls` | `entity.operations.runtime` | Builds only the branch reachable for the explicit action/route. |
| `entity.operations.reflections-triage` | `composes` | `entity.operations.plan` | Uses public planning only on the plan route. |
| `entity.operations.plan` | `calls` | `entity.operations.permission-context` | Resolves project provider feature bodies only for exact required-interface reasons and grants no extra body for an explicit external provider. |
| `entity.operations.policy-compiler` | `configures` | `entity.operations.coding-agent` | Renders equivalent default-deny Codex/Claude/outer boundaries. |
| `entity.operations.process-launcher` | `calls` | `entity.operations.coding-agent` | Starts a supported CLI only after enforcement/version/digest preflight. |
| `entity.operations.plan` | `tested_by` | `entity.operations.tests` | Real LangGraph and sentinel tests prove order, bounded context, writes, and failure stopping. |
| `entity.operations.standard-dev-loop` | `tested_by` | `entity.operations.tests` | Nested/non-union tests prove public opacity and per-leaf handoff. |
| `entity.operations.reflections-triage` | `tested_by` | `entity.operations.tests` | Branch tests prove status/investigate/fast-loop/plan exclusivity and worktree scope. |

## Relationship Types

| Predicate | Direction and meaning |
|---|---|
| `composes` | From a controlling Operation to a direct canonical Skill or public Operation whose identity/result it sequences without taking ownership or flattening internals. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.operations.invoke` | User invokes an installed Operation skill. | Enter the pair through the standard-library bootstrap and verified `.concorde/.venv`; resolve Protocol 13 roles; validate acyclic literal topology/effects/bindings; for each leaf compile normalized/native policy and prove enforcement; append its result/receipt; dispatch a nested Operation only by its public pair/result; stop on failure. | Ordered capability results without package-index access, or explicit runtime/pre-launch/executor failure with no downstream invocation. | `contract.operations.permission-bounded-execution`, `contract.operations.standard-development-loop`, `contract.skills.workflow-guidance` |
| `interaction.operations.plan` | User or outer Operation invokes `concorde-plan`. | Resolve selected/module/owned paths and exact required-interface feature bodies; run read-only context leaf; pass its result to author; permit only attempt/reflection writes. | Temporal plan artifacts or a bounded named failure with durable sources unchanged. | `contract.operations.plan`, `contract.workspace.feature-workspace` |
| `interaction.operations.install` | Installer or checkout sync projects capabilities. | Validate every exact pair/effect/topology/binding/cycle; package 17 leaves, three pairs, and the pinned dependency; omit two internal leaves; project 15 public leaves plus three Operations through the managed launcher; native install verifies each pair in `.concorde/.venv`. | Both agents receive the same 18 public capabilities while framework internals remain installed and every successfully installed Operation has an offline-capable runtime. | `contract.skills.agent-surface` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.operations.standard-development-loop` | Run specify, nested bounded planning, tasks/implementation, and validation/delivery as one controlled four-stage Operation. |
| `feature.operations.permission-bounded-planning` | Enforce least-privilege Codex/Claude launches for every direct leaf and plan through published dependency feature specifications. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of these
  principal entities and directed relationships.
- Direct capability topology is literal, mixed Skill/Operation, order-preserving, and acyclic;
  parents never flatten nested Operation internals.
- Graph construction fails before execution when any direct leaf lacks a non-null launch factory or
  any nested Operation lacks an explicit enforcing dispatcher; a factory result must be frozen and
  non-null before the leaf executor is called.
- Leaf effects remain owned by canonical Skill metadata. Occurrence bindings and effective
  configuration may narrow but never widen them; multi-leaf stages receive distinct policies.
- Workspace Protocol 13 and interface ownership resolve concrete paths before an agent starts.
  Related-feature summaries alone grant no body or implementation access.
- Codex uses a digest-named permission profile without legacy `sandbox_mode`; Claude uses restricted
  `dontAsk` plus strict OS sandbox settings; verified outer isolation is the only unavailable-native fallback.
- The process executor is real and injectable; tests record exact argv/settings/receipts and never
  call a paid/live model.
- Three public Operations and 15 public leaves project to both agents; two planner leaves remain
  packaged internal implementation capabilities.
- LangGraph remains lazy so base deterministic Tool imports and installation preview are
  dependency-free. Explicit apply provisions the pinned version into `.concorde/.venv`; after a
  successful install it is guaranteed rather than optional, and Operation startup stays offline.
