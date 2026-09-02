---
id: feature.operations.standard-development-loop
kind: feature
module: module.concorde.operations
related_features:
  - feature.skills.project-workflow
  - feature.runtime.run-lifecycle-tools
  - feature.concorde.workflow
interfaces:
  provided:
    - contract.operations.standard-development-loop
  required:
    - contract.skills.workflow-guidance
    - contract.skills.agent-surface
evidence_status: verified
---

# Feature Design: Run the Standard Development Loop

## Outcome and Scope

A user can invoke one installed Operation skill to run a LangGraph development loop whose controlled
stages are specify -> plan -> tasks -> deliver. Each stage resolves complete canonical leaf Skills,
receives accumulated prior results, and prevents downstream execution when its executor fails.

The Operation composes six leaf Skills without copying their prompts: specify; plan; tasks then
implement; validate then deliver. It provides graph topology and state control, not autonomous
authorization, model execution, or bypasses around any leaf Skill gate.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.operations.standard-dev-loop` | Declares four ordered stages and their six leaf Skills. |
| `entity.operations.standard-dev-loop-skill` | Installs the Operation to users and documents invocation, ordering, and failure behavior. |
| `entity.operations.runtime` | Loads canonical Skills, builds LangGraph state/nodes/edges, and injects the host executor. |
| `entity.operations.definition` | Represents exact stage names and ordered Skill bundles. |
| `entity.operations.state` | Carries the request and append-only prior stage results. |
| `entity.operations.langgraph` | Compiles and invokes the graph through its public API. |
| `entity.operations.coding-agent` | Executes each resolved leaf Skill under its own authority contract. |

## Interfaces

### `contract.operations.standard-development-loop` — Paired four-stage LangGraph

- **Consumer**: Maintainer, installed coding-agent integration, Operation tests, or a host supplying a
  stage executor.
- **Direction**: Development request plus executor to ordered leaf Skill invocations and accumulated
  stage results.
- **Entry points**: Installed `concorde-standard-dev-loop` Skill;
  `operations/concorde-standard-dev-loop/operation.py`; and
  `build_standard_dev_loop(executor, framework_prefix=...)`.
- **Inputs**: Request string, package/framework root, canonical leaf Skill inventory, injected executor,
  and initial empty result state.
- **Outputs**: Compiled LangGraph and ordered results for `specify`, `plan`, `tasks`, and `deliver`.
- **Obligations**: Resolve Skill bodies from canonical sources; preserve stage and within-stage Skill
  order; pass prior results without mutation; enforce an initially empty result list; keep every leaf
  Skill's authorization and validation gates intact; stop downstream nodes on executor failure.
- **Failures**: Invalid or missing pair metadata, unknown/non-leaf Skill, unsafe package root,
  unavailable LangGraph dependency, invalid initial state, non-string executor result, or executor
  exception stops construction/invocation with no fabricated completion.
- **Compatibility**: Concorde 2.0.0 uses LangGraph `>=1.2,<2`; Package Manifest 2 requires one exact
  `operation.py`/`SKILL.md` pair and exposes the Operation through the shared agent Skill namespace.
- **Implementing entities**: `entity.operations.standard-dev-loop`,
  `entity.operations.standard-dev-loop-skill`, `entity.operations.runtime`,
  `entity.operations.definition`, `entity.operations.state`, and `entity.operations.langgraph`.
- **Example**: `python3 operations/concorde-standard-dev-loop/operation.py "Add audit logging"`
  records specify, plan, tasks, and deliver in order; an installed user normally invokes the paired
  `concorde-standard-dev-loop` Skill, which resolves its framework-local Python entry point.

## Usage Scenarios

### Run the successful standard loop

1. Load `concorde-specify` for `specify`.
2. Load `concorde-plan` for `plan`.
3. Load `concorde-tasks` then `concorde-implement` for `tasks`.
4. Load `concorde-validate` then `concorde-deliver` for `deliver`.
5. Return four ordered stage results, each able to inspect but not mutate prior results.

### Stop on failure

If the executor raises during `plan`, LangGraph exposes that failure; neither `tasks` nor `deliver`
runs, and no success state is synthesized.

## Requirements

- **FR-001**: The Operation MUST expose exactly the ordered stage path `START -> specify -> plan ->
  tasks -> deliver -> END`.
- **FR-002**: Stage bundles MUST be `specify=[concorde-specify]`,
  `plan=[concorde-plan]`, `tasks=[concorde-tasks, concorde-implement]`, and
  `deliver=[concorde-validate, concorde-deliver]`.
- **FR-003**: Every stage MUST resolve complete leaf Skill prompts from the canonical `skills/`
  inventory without duplicating prompt text in Operation sources.
- **FR-004**: The graph MUST carry the original request and append one typed result per completed
  stage while preserving immutable prior-stage order for the executor.
- **FR-005**: Executor exceptions and invalid outputs MUST prevent every downstream stage.
- **FR-006**: The Operation MUST remain importable without LangGraph; only graph construction may
  require the optional dependency and must report its absence explicitly.
- **FR-007**: The paired Operation skill MUST be projected to Codex and Claude and invoke the installed
  framework-local Python graph.

## Success Criteria

- **SC-001**: Real LangGraph invocation visits exactly four stages and six canonical leaf Skills in
  declared order.
- **SC-002**: Source, installed, and projected Operation-pair tests agree on Python/Markdown pairing,
  declared Skill membership, and entry-point provenance.
- **SC-003**: A failure injected at any stage prevents all later visits while retaining completed
  prior results.
- **SC-004**: Base Runtime/Tool imports and package installation succeed without importing LangGraph.

## Edge Cases

- Package Manifest 2 declares an Operation but either pair file is missing or contains an extra
  canonical file.
- Operation Markdown and Python declare different Skill membership or order.
- A graph is invoked with pre-populated initial stage results.
- An executor returns a non-string value or mutates external state before failing; the graph reports
  failure but cannot undo effects outside its contract.
