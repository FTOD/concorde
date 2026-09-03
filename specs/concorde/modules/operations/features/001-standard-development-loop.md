---
id: feature.operations.standard-development-loop
kind: feature
module: module.concorde.operations
related_features:
  - feature.operations.permission-bounded-planning
  - feature.skills.project-workflow
  - feature.runtime.run-lifecycle-tools
  - feature.concorde.workflow
interfaces:
  provided:
    - contract.operations.standard-development-loop
  required:
    - contract.operations.permission-bounded-execution
    - contract.operations.plan
    - contract.skills.workflow-guidance
    - contract.skills.agent-surface
evidence_status: verified
---

# Feature Design: Run the Standard Development Loop

## Outcome and Scope

A user can invoke one installed Operation skill to run a permission-bounded four-stage LangGraph:
specify → nested plan → tasks → deliver. Its six direct capability occurrences are specify; public
`concorde-plan`; tasks then implement; validate then deliver. The outer graph never names planner
internals. Every direct leaf receives its own immutable policy/configuration before the host executor,
receives exact prior capability results, and prevents all downstream work on failure.

The installed Skill enters the paired graph through `scripts/run-operation.py`, which selects the
installer-verified `.concorde/.venv`; a source checkout selects its root `.venv`. Neither path relies
on shell activation, and a successful installed runtime needs no package-index access.

The Operation provides topology/state/failure control and policy handoff. Native Codex/Claude or
approved outer isolation enforces the paths; LangGraph and prompts do not.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.operations.standard-dev-loop` | Declares four stages, six direct capabilities, and exact occurrence bindings. |
| `entity.operations.standard-dev-loop-skill` | Installs the public Operation and documents nested planning/policy behavior. |
| `entity.operations.runtime` | Loads canonical direct capabilities, preserves opaque nesting, attaches per-leaf launches, and builds LangGraph. |
| `entity.operations.definition` | Represents stage/capability order plus narrowing bindings. |
| `entity.operations.state` | Carries request and append-only per-capability results/receipts. |
| `entity.operations.policy-compiler` | Compiles distinct normalized/native policies for direct leaves. |
| `entity.operations.plan` | Executes bounded context → author behind one public nested identity. |
| `entity.operations.langgraph` | Compiles and invokes the graph through its public API. |
| `entity.operations.coding-agent` | Enforces and executes each direct leaf launch. |

## Interfaces

### `contract.operations.standard-development-loop` — Paired four-stage nested LangGraph

- **Consumer**: Maintainer, installed coding-agent integration, Operation tests, or a host supplying
  direct capability and nested-operation dispatchers.
- **Direction**: Development request plus integration/enforcement context to ordered capability
  invocations, receipts, and accumulated results.
- **Entry points**: Installed `concorde-standard-dev-loop` Skill through the colocated managed-runtime
  bootstrap;
  `operations/concorde-standard-dev-loop/operation.py`; and
  `build_standard_dev_loop(executor, project_root=..., integration=...)`.
- **Inputs**: Request, package/framework root, selected Protocol 13 feature context, Codex/Claude
  integration, verified managed interpreter, exact direct capability inventory/bindings, leaf
  effects, and injected executor.
- **Outputs**: Ordered results for six direct capability occurrences grouped under `specify`, `plan`,
  `tasks`, and `deliver`; leaf results may include enforcement receipts.
- **Obligations**: Resolve canonical bodies/effects; preserve stage and occurrence order; expose only
  public `concorde-plan` to the outer graph; pass exact immutable prior results; compile one
  narrowing default-deny policy per leaf; require a non-null launch factory and explicit enforcing
  nested dispatcher; start with no results; stop on any runtime, direct, or nested failure; perform
  no dependency installation or package-index access during invocation.
- **Failures**: Missing/corrupt managed interpreter, invalid/missing pair metadata, cycle, unknown
  capability/effect, binding mismatch, unsafe path, unavailable enforcement, invalid
  input/result/receipt, unavailable/mismatched LangGraph, or executor exception stops
  construction/invocation without fabricated completion.
- **Compatibility**: Concorde 2.1.0, Package Manifest 2, installed LangGraph `1.2.11` (runtime API
  range `>=1.2,<2`), and source-root/installed-managed venv layouts; the public four-stage contract
  remains stable while `concorde-plan` is one nested Operation.
- **Implementing entities**: `entity.operations.standard-dev-loop`,
  `entity.operations.standard-dev-loop-skill`, `entity.operations.runtime`,
  `entity.operations.definition`, `entity.operations.state`, `entity.operations.policy-compiler`,
  `entity.operations.plan`, and `entity.operations.langgraph`.
- **Example**: `python3 scripts/run-operation.py
  operations/concorde-standard-dev-loop/operation.py "Add audit logging" --framework-prefix .`
  reports six outer occurrences from a checkout; installed projections use the same bootstrap under
  `.concorde/framework` and its inner graph alone launches context/author.

## Usage Scenarios

### Run the successful standard loop

1. Launch `concorde-specify` with its own leaf policy.
2. Dispatch public nested `concorde-plan`; its graph launches internal context then author policies.
3. Launch `concorde-tasks`, then `concorde-implement`, each with distinct write authority.
4. Launch `concorde-validate`, then `concorde-deliver`, each with distinct authority.
5. Return six ordered direct results while preserving the public four-stage grouping.

### Stop on failure

If policy resolution or the nested planner fails, no tasks/deliver capability runs. If any later leaf
fails or returns an invalid/stale receipt, remaining occurrences stop.

## Requirements

- **FR-001**: The Operation MUST expose exactly `START → specify → plan → tasks → deliver → END`.
- **FR-002**: Direct bundles MUST be `specify=[concorde-specify]`,
  `plan=[concorde-plan Operation]`, `tasks=[concorde-tasks, concorde-implement]`, and
  `deliver=[concorde-validate, concorde-deliver]` without private planner leaves.
- **FR-003**: Every direct capability MUST resolve its complete canonical source; parent sources MUST
  NOT duplicate prompts or flatten nested Operation topology.
- **FR-004**: State MUST preserve the original request and append one typed result per completed
  occurrence in exact order, including same-stage prior results.
- **FR-005**: Every direct leaf MUST receive one exact narrowing policy/configuration; stage-wide
  permission unions are invalid.
- **FR-006**: Executor/policy/receipt/nested failures MUST prevent every downstream occurrence.
- **FR-007**: Base Tool import and installation preview MUST remain LangGraph-independent until graph
  construction; successful explicit installation MUST provide the pinned dependency, while a
  missing/corrupt source or installed runtime fails explicitly.
- **FR-008**: Both agent integrations MUST project the same public Operation through the managed
  bootstrap and installed paired Python while internal planner leaves remain unprojected.
- **FR-009**: Invocation after successful installation MUST execute from `.concorde/.venv` without
  dependency resolution, download, package-index access, or use of a project root `.venv`.

## Success Criteria

- **SC-001**: Real LangGraph invocation visits exactly four stages and six direct public capabilities
  in declared order, with one opaque planner occurrence.
- **SC-002**: Source/installed/projection tests agree on pair, capability/binding literals,
  entry-point provenance, managed interpreter identity, and public/internal filtering.
- **SC-003**: A failure at any direct or inner planner occurrence prevents the correct later nodes
  while retaining only completed prior results.
- **SC-004**: Policy tests prove tasks/implement and validate/deliver receive distinct non-union
  digests; base imports/preview do not eagerly import LangGraph; installed runtime checks and a real
  graph invocation pass with package-index access disabled.

## Related Features

- `feature.operations.permission-bounded-planning` supplies the per-leaf enforcement and public
  nested planning contracts.
- `feature.skills.project-workflow` supplies canonical public/internal leaf bodies and effects.
- `feature.runtime.run-lifecycle-tools` supplies deterministic Tools invoked inside leaves.
- `feature.concorde.workflow` consumes the public four-stage lifecycle.

## Edge Cases

- Pair Markdown/Python capabilities or occurrence bindings disagree.
- An outer graph references an internal planner leaf or a nested Operation cycle.
- Two same-stage leaves request different writes; each receives only its own effects.
- A native sandbox is unavailable and no verified equivalent outer boundary exists.
- Graph input contains prior results, an executor returns a non-string/unreceipted result, or a
  nested failure attempts to continue downstream.
- The projected Skill is correct but `.concorde/.venv` was removed or corrupted after installation;
  the bootstrap fails with an actionable repair path rather than falling back to ambient Python.
