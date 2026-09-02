---
id: module.concorde.operations
kind: module
parent: module.concorde
modules: []
features:
  - feature.operations.standard-development-loop
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-operations-system-overview.html
---

# Architecture: Operations

## Responsibility

Provide paired LangGraph control graphs that compose canonical leaf Skills into stateful, installed
workflows with explicit stages, ordering, accumulated results, and failure boundaries.

## Boundary

Operations owns the shared graph runtime and each exact
`operations/<name>/{operation.py,SKILL.md}` pair. Python owns executable topology; paired Markdown
owns user invocation and behavioral expectations. Operations load leaf prompts from the Skills
module and may cause those Skills to invoke Runtime Tools, but do not duplicate Skill bodies, define
Tool algorithms, or own coding-agent/model execution.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.operations.runtime` | program | Resolves canonical leaf Skills into stages and compiles an injected executor through LangGraph. | `src/concorde/operation_runtime.py` |
| `entity.operations.definition` | type | Ordered unique stage names mapped to ordered tuples of canonical leaf Skill names. | `src/concorde/operation_runtime.py#OperationDefinition` |
| `entity.operations.state` | type | Request plus append-only ordered stage results passed through a graph. | `src/concorde/operation_runtime.py#OperationState` |
| `entity.operations.standard-dev-loop` | program | Four-stage specify -> plan -> tasks -> deliver LangGraph. | `operations/concorde-standard-dev-loop/operation.py` |
| `entity.operations.standard-dev-loop-skill` | document | Installed invocation and failure contract paired with the standard development graph. | `operations/concorde-standard-dev-loop/SKILL.md` |
| `entity.operations.reflections-triage` | program | Investigation, routing, implementation, and validation LangGraph for reflection work. | `operations/concorde-reflections-triage/operation.py` |
| `entity.operations.reflections-triage-skill` | document | Installed reflection-triage/v4 invocation contract paired with its graph. | `operations/concorde-reflections-triage/SKILL.md` |
| `entity.operations.langgraph` | external-system | Optional graph runtime used to compile and invoke Operation topology. | `external:langchain-ai/langgraph@1.x` |
| `entity.operations.coding-agent` | external-system | Host that faithfully executes each resolved leaf Skill and returns explicit stage results. | `external:coding-agent` |
| `entity.operations.tests` | test | Pairing, loading, real-graph, stage-order, state, failure, installation, and projection evidence. | `tests/concorde` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.operations.standard-dev-loop` | `implements` | `entity.operations.definition` | Declares the exact four-stage development topology and Skill membership. |
| `entity.operations.reflections-triage` | `implements` | `entity.operations.definition` | Declares reflection investigation, routing, implementation, and validation stages. |
| `entity.operations.standard-dev-loop-skill` | `documents` | `entity.operations.standard-dev-loop` | Supplies the required user-facing invocation/failure contract for that Python graph. |
| `entity.operations.reflections-triage-skill` | `documents` | `entity.operations.reflections-triage` | Supplies the required user-facing invocation/failure contract for that Python graph. |
| `entity.operations.runtime` | `reads_from` | `module.concorde.skills` | Loads complete canonical leaf Skill prompts by declared safe name. |
| `entity.operations.runtime` | `calls` | `entity.operations.langgraph` | Compiles state, nodes, and ordered edges through the public graph API. |
| `entity.operations.standard-dev-loop` | `calls` | `entity.operations.runtime` | Resolves stages and builds the standard graph without embedding prompts. |
| `entity.operations.reflections-triage` | `calls` | `entity.operations.runtime` | Resolves stages and builds the triage graph without embedding prompts. |
| `entity.operations.coding-agent` | `implements` | `entity.operations.definition` | Executes resolved Skills in graph order and exposes failures to the graph caller. |
| `entity.operations.standard-dev-loop` | `tested_by` | `entity.operations.tests` | Real LangGraph and injected-executor tests establish ordering, state, and failure behavior. |
| `entity.operations.reflections-triage` | `tested_by` | `entity.operations.tests` | Pair and graph tests establish its declared Skill membership and controls. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.operations.invoke` | User invokes an installed Operation skill. | Resolve the paired Python entry point; validate declared Skills; load canonical leaf prompts; compile LangGraph; execute nodes through the host; append stage results. | Controlled multi-Skill result or an explicit failure before downstream nodes run. | `contract.operations.standard-development-loop`, `contract.skills.agent-surface`, `contract.skills.workflow-guidance` |
| `interaction.operations.install` | Installer or checkout sync projects capabilities. | Validate each exact Python/Markdown pair and its declared stage membership; copy the pair into the framework; project its Markdown into the agent Skill namespace. | User receives an Operation as a Skill while its execution authority remains paired and inspectable. | `contract.skills.agent-surface` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.operations.standard-development-loop` | Run specify, plan, tasks/implement, and validate/deliver as one controlled four-stage LangGraph over canonical leaf Skills. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Operation is reserved for LangGraph composition of two or more leaf Skills; deterministic native
  actions remain Runtime Tools.
- Every Operation is exactly one `operation.py` execution authority plus one associated `SKILL.md`
  user contract, installed together under the framework.
- The paired Markdown projects into the same global agent Skill namespace as leaf Skills.
- Python declares stage membership and topology; Operation Markdown declares the same Skills for
  deterministic pairing checks and user orientation.
- Operations resolve canonical leaf Skill bodies at runtime and never embed or generate copies.
- LangGraph remains optional and lazy so importing and installing base Tools is dependency-free.
