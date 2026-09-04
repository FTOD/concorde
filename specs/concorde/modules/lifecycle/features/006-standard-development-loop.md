---
id: feature.lifecycle.standard-development-loop
kind: feature
module: module.concorde.lifecycle
related_features:
  - id: feature.capabilities.permission-bounded-execution
    relation: depends_on
  - id: feature.lifecycle.plan-attempt
    relation: composes
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.capabilities.run-deterministic-tools
    relation: depends_on
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.concorde.evolve-protocol
    relation: relates_to
interfaces:
  provided:
    - contract.lifecycle.standard-development-loop
  required:
    - contract.capabilities.operation-data
    - contract.capabilities.permission-bounded-execution
    - contract.lifecycle.plan
    - contract.capabilities.skill-contract
    - contract.capabilities.agent-surface
---

# Feature Design: Run the Standard Development Loop

## Outcome and Scope

A user can invoke one installed Operation skill to run a permission-bounded four-stage LangGraph:
specify → nested plan → tasks → deliver. Its six direct capability occurrences are specify; public
`concorde-plan`; tasks then implement; validate then deliver. The outer graph never names planner
internals. Every direct leaf receives its own immutable policy/configuration and host Protocol 13
receipt, returns Capability Completion Envelope 1, receives only validated prior successes, and
prevents all downstream work on transport or semantic failure.

The installed Skill enters the paired graph through `scripts/run-operation.py`, which selects the
installer-verified `.concorde/.venv`; a source checkout selects its root `.venv`. Neither path relies
on shell activation, and a successful installed runtime needs no package-index access.

The Operation provides topology/state/failure control and policy handoff. Native Codex/Claude or
approved outer isolation enforces the paths; LangGraph and prompts do not.

The Operation is a normal-feature lifecycle only. In the Concorde repository, a request that changes
normative Concorde Protocol semantics is rejected before graph construction and routed to the root
isolated-worktree Protocol-evolution feature.

Before actual graph execution, the outer agent establishes one linked worktree at the primary
worktree's exact committed `HEAD` and runs all four stages there. Policy description may remain
read-only in the primary checkout. The execution entry point rejects the primary worktree unless the
maintainer supplied the explicit primary-mutation override.

## Target Standard Loop Data Types

These are target domain types for `contract.lifecycle.standard-development-loop` under
`contract.capabilities.operation-data`; the executable graph still uses the CLI/string request ABI.
Every value uses the common TypedValue wrapper, with required fields unless stated otherwise.

| Type ID @1 | `data` fields / JSON types | Meaning and constraints |
|---|---|---|
| `concorde-standard-dev-loop-context` | `feature_path` (string), `request` (nonempty string), optional `constraints` (array of nonempty strings, default `[]`) | One canonical direct feature path and task intent. Specification may author a planned path; the host must resolve its authored stable ID before plan. Configuration is inherited separately. |
| `concorde-standard-dev-loop-result` | `feature_id` (string), `feature_path` (string), `completed_capabilities` (array of strings), `delivery` (DeliveryOutcome) | Only produced after all six direct capabilities succeed. Order is exactly specify, plan, tasks, implement, validate, deliver using their `concorde-*` names. Child planner internals are not included. |
| `DeliveryOutcome` | `status` (constant `delivered`), `attempt_dir` (string), `retained_source_digest` (SHA-256 string) | Historical path of the removed selected attempt and current retained-source evidence. The path is not a live ArtifactRef. |

| Producer → consumer | Field mapping and gate |
|---|---|
| Specify → parent host | Re-resolve the authored `feature_path` into a stable feature ID and current workspace; never carry a guessed ID from the planned filename. |
| Parent → Plan | Construct `concorde-plan-context@1` by copying `feature_path`, `request`, `constraints` from the original input. Pass the already bound worktree and configuration through the host. |
| Plan → Tasks | Validate `concorde-plan-result@1`; map `feature_id`, `feature_path`, `attempt_dir`, `source_digest`, and the `plan.md`/`tasks.md` ArtifactRefs into the task-generation context. |
| Tasks → Implement | Rehash the updated `tasks.md` and other consumed attempt files; retain selected feature identity and only mapped task/plan refs. Old plan-stage task digests are no longer current. |
| Implement → Validate | Resolve the changed source/test/spec set and current evidence in the same workspace; test completion is not inferred from task prose. |
| Validate → Deliver | Pass the actual successful validation evidence; obtain a fresh Delivery Proposal 9 through the existing delivery contract and verify its current digest before cleanup. |
| Deliver → Parent | Return DeliveryOutcome and the six completed public/direct capability identities; never return removed attempt files as live refs. |

The table specifies data obligations for existing leaf interfaces; it does not invent new public
Operations for tasks, implementation, validation, or delivery. Their concrete typed adapters must
be reconciled with those owning interfaces during runtime migration. Any missing, incompatible,
cross-feature, stale, or failed producer result prevents its consumer. A JSON list of all prior
capability output strings is not a conforming handoff.

```json
{
  "type_id": "concorde-standard-dev-loop-context",
  "schema_version": 1,
  "data": {
    "feature_path": "specs/concorde/modules/lifecycle/features/002-plan-attempt.md",
    "request": "Implement the approved planning feature change",
    "constraints": []
  }
}
```

## Target Contract Examples

### Completed loop

The removed attempt path records an outcome; it is no longer a live ArtifactRef.

Illustrative fixture IDs/digests describe the wire shape; they are not live execution receipts.

```json
{
  "type_id": "concorde-standard-dev-loop-result",
  "schema_version": 1,
  "data": {
    "feature_id": "feature.example.search",
    "feature_path": "specs/example/features/001-search.md",
    "completed_capabilities": [
      "concorde-specify",
      "concorde-plan",
      "concorde-tasks",
      "concorde-implement",
      "concorde-validate",
      "concorde-deliver"
    ],
    "delivery": {
      "status": "delivered",
      "attempt_dir": ".concorde/attempts/feature.example.search",
      "retained_source_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  }
}
```

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.lifecycle.standard-loop-input` | Defines target task fields mapped into the nested plan input. |
| `entity.lifecycle.standard-loop-result` | Defines the final domain result after validated cleanup. |
| `entity.lifecycle.plan-result` | Supplies typed feature/attempt refs for downstream tasks and implementation. |
| `entity.lifecycle.standard-dev-loop` | Declares four stages, six direct capabilities, and exact occurrence bindings. |
| `entity.lifecycle.standard-dev-loop-skill` | Installs the public Operation and documents nested planning/policy behavior. |
| `module.concorde.capabilities` | Loads canonical direct capability bodies/effects, preserves opaque nesting, attaches per-leaf launches, compiles policy, and builds the LangGraph. |
| `entity.lifecycle.plan-operation` | Executes bounded context → author behind one public nested identity. |
| `entity.lifecycle.specify-skill` | Runs specification as the first direct stage. |
| `entity.lifecycle.tasks-skill` | Runs task generation as part of the tasks/implement stage. |
| `entity.lifecycle.implement-skill` | Runs implementation as part of the tasks/implement stage. |
| `entity.lifecycle.deliver-skill` | Runs delivery as the closing occurrence of the validate/deliver stage. |
| `module.concorde.understanding` | Runs the validate leaf as the opening occurrence of the validate/deliver stage. |
| `entity.concorde.coding-agent` | Enforces and executes each direct leaf launch. |

## Interfaces

### `contract.lifecycle.standard-development-loop` — Paired four-stage nested LangGraph

- **Consumer**: Maintainer, installed coding-agent integration, Operation tests, or a host supplying
  direct capability and nested-operation dispatchers.
- **Direction**: Development request plus integration/enforcement context to ordered capability
  invocations, receipts, and accumulated results.
- **Entry points**: Installed `concorde-standard-dev-loop` Skill through the colocated managed-runtime
  bootstrap;
  `operations/concorde-standard-dev-loop/operation.py`; and
  `build_standard_dev_loop(executor, project_root=..., integration=...)`.
- **Inputs**: Normal-feature request, committed-base isolated-worktree identity (or explicit primary override), package/framework root, selected Protocol 13 feature context, Codex/Claude
  integration, verified managed interpreter, exact direct capability inventory/bindings, leaf
  effects, and injected executor.
- **Outputs**: Ordered results for six direct capability occurrences grouped under `specify`, `plan`,
  `tasks`, and `deliver`; every real leaf result includes validated completion and enforcement
  receipts, while describe/test injection may retain an explicitly unreceipted string sentinel.
- **Obligations**: Resolve canonical bodies/effects; preserve stage and occurrence order; expose only
  public `concorde-plan` to the outer graph; pass exact immutable prior results; compile one
  narrowing default-deny policy per leaf; require a non-null launch factory and explicit enforcing
  nested dispatcher; start with no results; admit only a successful identity-bound completion; stop
  on any runtime, direct, nested, transport, lifecycle, or semantic failure; perform
  no dependency installation or package-index access during invocation; require isolation before
  the first mutating occurrence; exclude primary dirty state; and reject normative
  Concorde Protocol evolution before any graph node or workspace mutation.
- **Failures**: Missing/corrupt managed interpreter, invalid/missing pair metadata, cycle, unknown
  capability/effect, binding mismatch, unsafe path, unavailable enforcement, invalid
  input/result/completion/receipt, unavailable/mismatched LangGraph, or executor exception stops
  construction/invocation without fabricated completion.
- **Compatibility**: Concorde 2.1.0, Package Manifest 2, installed LangGraph `1.2.11` (runtime API
  range `>=1.2,<2`), and source-root/installed-managed venv layouts; the public four-stage contract
  remains stable while `concorde-plan` is one nested Operation.
- **Implementing entities**: `entity.lifecycle.standard-dev-loop`,
  `entity.lifecycle.standard-dev-loop-skill`, `module.concorde.capabilities`,
  `entity.lifecycle.plan-operation`.
- **Example**: `python3 scripts/run-operation.py
  operations/concorde-standard-dev-loop/operation.py "Add audit logging" --framework-prefix .`
  reports six outer occurrences from a checkout; installed projections use the same bootstrap under
  `.concorde/framework` and its inner graph alone launches context/author.

## Related Features

- The target typed boundary depends on `feature.capabilities.provide-capability-surfaces` for
  `contract.capabilities.operation-data`; executable adoption is a separately identified runtime gap.


- `feature.capabilities.permission-bounded-execution` supplies the per-leaf enforcement contract every
  direct occurrence in this Operation launches under.
- `feature.lifecycle.plan-attempt` supplies the public nested planning Operation this graph dispatches
  opaquely as its second stage.
- `feature.capabilities.provide-capability-surfaces` supplies the canonical leaf/Operation bodies,
  effects, and Codex/Claude projection this graph composes and installs through.
- `feature.capabilities.run-deterministic-tools` supplies the deterministic Tools individual composed
  leaves invoke during their phase.
- `feature.concorde.workflow` consumes the public four-stage lifecycle as the umbrella's primary
  end-to-end path.
- `feature.concorde.evolve-protocol` owns the Concorde-repository-only changes this normal Operation
  must reject before graph construction.

## Usage Scenarios

### Run the successful standard loop

1. Launch `concorde-specify` with its own leaf policy.
2. Dispatch public nested `concorde-plan`; its graph launches the internal context leaf owned by
   `module.concorde.understanding`, then the internal plan-author leaf.
3. Launch `concorde-tasks`, then `concorde-implement`, each with distinct write authority.
4. Launch the validate leaf owned by `module.concorde.understanding`, then `concorde-deliver`, each
   with distinct authority.
5. Return six ordered direct results while preserving the public four-stage grouping.

### Stop on failure

If policy resolution or the nested planner fails, no tasks/deliver capability runs. If any later leaf
fails or returns an invalid/stale receipt, remaining occurrences stop.

### Reject Protocol evolution

If the Concorde repository request changes normative Concorde Protocol semantics, do not construct
or invoke this graph and do not select a feature or create an attempt. Name
`feature.concorde.evolve-protocol` and its isolated-worktree cutover instead.

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
- **FR-010**: A normative Concorde Protocol semantic change MUST be rejected before graph
  construction, selection, or attempt mutation and routed to `feature.concorde.evolve-protocol`.
- **FR-011**: Actual Operation execution MUST reject the primary worktree by default and run specify,
  plan/attempt creation, tasks/implementation, validation, and delivery in one linked worktree from
  committed primary `HEAD`; only an explicit maintainer-authorized override may permit primary mutation.
- **FR-012**: Every real direct leaf MUST receive a host Protocol 13 receipt and MUST return a valid
  Capability Completion Envelope 1; only `status: success`, passed gates, no limitations, and matching
  launch/workspace/bootstrap identities may append a `CapabilityResult`.
- **FR-013**: Exit-zero semantic failure, malformed/stale completion, native lifecycle failure, or a
  missing completion MUST prevent the current occurrence and every later direct or nested occurrence
  from entering state.

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
- **SC-005**: Completion-envelope tests prove a zero-exit failed gate and every malformed/stale result
  stop the graph, while a recoverable command failure followed by validated success may continue.

## Edge Cases

- Pair Markdown/Python capabilities or occurrence bindings disagree.
- An outer graph references an internal planner leaf or a nested Operation cycle.
- Two same-stage leaves request different writes; each receives only its own effects.
- A native sandbox is unavailable and no verified equivalent outer boundary exists.
- Graph input contains prior results, an executor returns a non-string/unreceipted result, or a
  nested failure attempts to continue downstream.
- A client transport exits zero after reporting an unmet mandatory gate; the failed completion is
  never retained as a prior result.
- The projected Skill is correct but `.concorde/.venv` was removed or corrupted after installation;
  the bootstrap fails with an actionable repair path rather than falling back to ambient Python.
- A request appears small or backward compatible but changes normative Concorde Protocol semantics;
  the standard loop remains ineligible and performs no completed prefix.
