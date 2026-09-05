---
id: feature.lifecycle.plan-attempt
kind: feature
module: module.concorde.lifecycle
related_features:
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.lifecycle.specify-behavior
    relation: depends_on
  - id: feature.lifecycle.execute-and-reconcile
    relation: depended_on_by
  - id: feature.lifecycle.standard-development-loop
    relation: composed_by
  - id: feature.understanding.bound-planning-context
    relation: depends_on
  - id: feature.capabilities.permission-bounded-execution
    relation: depends_on
  - id: feature.reflections.record-and-triage
    relation: relates_to
interfaces:
  provided:
    - interface.concorde.plan
    - contract.lifecycle.plan
  required:
    - contract.capabilities.operation-data
    - contract.understanding.planning-context
    - contract.capabilities.permission-bounded-execution
---

# Feature Design: Plan One Attempt

## Outcome and Scope

A maintainer invokes the public `concorde-plan` Operation to resolve a read-only bounded planning
context, then turn the selected feature, providing architecture/owned code/tests, exact
required-interface provider feature specifications, and known reflections into one temporal plan and
dependency-ordered task scaffold without dependency internals. Before context or attempt authorship,
the acting agent must enter one linked worktree at the primary worktree's exact committed `HEAD`.

Context resolution is delegated whole to `module.concorde.understanding` through
`contract.understanding.planning-context` and always precedes authorship; the plan author never
resolves provider ownership itself. The author's only durable write target is the selected attempt
plus authorized per-file reflections — durable feature, architecture, code, test, and generated
sources stay byte-identical. Both the Operation's own launch and every leaf it composes are
permission-bounded through `module.concorde.capabilities` via
`contract.capabilities.permission-bounded-execution`.

## Contract Examples

### Author input and public planning output

The author receives both task and resolved context. The public result contains only the contracted fields.

Illustrative fixture IDs/digests describe the wire shape; they are not live execution receipts.

```json
{
  "type_id": "concorde-plan-author-context",
  "schema_version": 1,
  "data": {
    "task": {
      "type_id": "concorde-plan-context",
      "schema_version": 1,
      "data": {
        "feature_path": "specs/example/features/001-search.md",
        "request": "Plan the approved search change",
        "constraints": []
      }
    },
    "planning_context": {
      "type_id": "concorde-planning-context",
      "schema_version": 1,
      "data": {
        "feature_id": "feature.example.search",
        "feature_path": "specs/example/features/001-search.md",
        "module_id": "module.example",
        "module_architecture": {
          "id": "module.example",
          "path": "specs/example/architecture.md",
          "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "attempt_dir": ".concorde/attempts/feature.example.search",
        "source_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "owned_artifacts": [
          {
            "id": "feature.example.search",
            "path": "specs/example/features/001-search.md",
            "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ],
        "provider_features": [],
        "denied_paths": []
      }
    }
  }
}
```

```json
{
  "type_id": "concorde-plan-result",
  "schema_version": 1,
  "data": {
    "feature_id": "feature.example.search",
    "feature_path": "specs/example/features/001-search.md",
    "attempt_dir": ".concorde/attempts/feature.example.search",
    "source_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "artifacts": [
      {
        "id": "attempt:feature.example.search:plan.md",
        "path": ".concorde/attempts/feature.example.search/plan.md",
        "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      {
        "id": "attempt:feature.example.search:tasks.md",
        "path": ".concorde/attempts/feature.example.search/tasks.md",
        "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ]
  }
}
```

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.lifecycle.plan-input` | Defines the caller task fields independently of project configuration. |
| `entity.lifecycle.plan-author-input` | Defines the explicit task plus resolved-context handoff. |
| `entity.lifecycle.plan-result` | Defines the public result parents may consume without planner internals. |
| `entity.lifecycle.plan-operation` | Owns the public context → author graph and keeps the internal context leaf and plan author behind one stable identity. |
| `entity.lifecycle.plan-operation-skill` | Documents and installs the public planning invocation, policy, and failure contract. |
| `entity.lifecycle.plan-author-skill` | Authors the temporal plan, research, data model, quickstart, and initial tasks from the resolved context. |
| `module.concorde.understanding` | Resolves the permission-bounded planning context — selected feature, owned implementation, and exact required-interface provider feature specifications — before authorship begins. |
| `module.concorde.capabilities` | Compiles and enforces one immutable least-privilege launch for the Operation and each leaf it composes. |
| `entity.lifecycle.attempt` | Receives the authored plan, research, and task artifacts; the author's only durable write target besides authorized reflections. |
| `entity.concorde.coding-agent` | Executes the enforced context and author launches without exceeding their declared boundaries. |

## Interfaces

### `interface.concorde.plan` — Create an implementation attempt

- **Consumer**: Maintainer and coding agent preparing a reviewed feature change.
- **Direction**: Durable feature/architecture/code context to a separate stable-ID control plan and tasks.
- **Entry points**: Paired Operation `concorde-plan`, public leaf `concorde-tasks`, and optional
  `concorde-taskstoissues`.
- **Inputs**: Committed-base isolated-worktree identity (or explicit primary override), `feature_path`, providing architecture/owned locators, module ancestry/related summaries,
  exact `interfaces.required` owner feature specs/reasons, selected attempt, constitution/reflections.
- **Outputs**: `.concorde/attempts/<stable-feature-id>/plan.md`, research/data model/quickstart, and dependency-ordered tasks with exact traces/paths.
- **Obligations**: Run read-only context before author; include dependency bodies only for unique
  required-interface ownership; deny dependency architecture/source/tests/attempts; write only the
  selected attempt/authorized reflection; map every affected authority and preserve durable bytes;
  never use or transfer primary-worktree dirty state.
- **Failures**: Context/policy/enforcement mismatch, ambiguous provider, Constitution violation,
  unresolved clarification, missing ownership, or incomplete trace coverage stops authorship.
- **Compatibility**: `concorde-plan` is a paired Operation; no leaf alias remains.
- **Implementing entities**: `entity.lifecycle.plan-operation`, `entity.lifecycle.tasks-skill`,
  `entity.lifecycle.taskstoissues-skill`, `module.concorde.understanding`, `entity.concorde.coding-agent`.

### `contract.lifecycle.plan` — Permission-bounded planning LangGraph

- **Consumer**: Maintainer or standard-development Operation preparing one selected feature change.
- **Direction**: Complete planning request to bounded context resolution followed by temporal plan
  authorship.
- **Entry points**: Installed `concorde-plan` Operation skill and its paired
  `operations/concorde-plan/operation.py` graph.
- **Inputs**: Selected stable feature, request/constraints, Workspace Protocol 13 result, published
  dependency feature interfaces, providing-module owned architecture/code/test locators,
  constitution, reflections, and existing selected attempt.
- **Outputs**: Ordered context and plan stage results plus temporal plan/research/quickstart/data-model
  artifacts only when useful.
- **Obligations**: Compose at least two canonical leaf Skills without copying their prompts; resolve
  dependency bodies only when they own an explicitly required interface; deny dependency internals;
  preserve durable and executable sources; and make the plan author's write set exactly the selected
  attempt plus authorized reflection occurrences.
- **Failures**: Ambiguous provider interface, missing feature/architecture ownership, unavailable
  enforcement, context-policy mismatch, constitution violation, or unexpected durable mutation
  stops planning and leaves downstream Operations unrun.
- **Compatibility**: `concorde-plan` remains the public capability name and is a paired Operation; the
  former planning prompt lives as the internal `concorde-plan-author` leaf and no same-name
  compatibility alias remains.
- **Example**: `concorde-plan "Add idempotent capture"` runs a read-only context stage through
  `module.concorde.understanding`, then a plan author stage whose prior result names the exact
  feature-spec and owned implementation boundary.
- **Implementing entities**: `entity.lifecycle.plan-operation`, `entity.lifecycle.plan-operation-skill`,
  `entity.lifecycle.plan-author-skill`, `module.concorde.understanding`, `module.concorde.capabilities`,
  `entity.concorde.coding-agent`.

## Planning Data Types

These field definitions extend `contract.lifecycle.plan` for the implemented
`contract.capabilities.operation-data` transport. The paired Python entry point delegates to the
shared host service. Each value uses the common TypedValue wrapper; fields below are required
except the stated defaults.

| Type ID @1 | `data` field | JSON type | Meaning / constraints |
|---|---|---|---|
| `concorde-plan-context` | `feature_path` | string | Existing canonical project-relative direct feature file. Required explicitly at the typed boundary; an adapter may resolve selection before constructing it. Never a stable ID inferred from the filename. |
| `concorde-plan-context` | `request` | nonempty string | Planning objective; it carries intent, not hidden key/value configuration. |
| `concorde-plan-context` | `constraints` | array of nonempty strings | Optional, defaults to `[]`; task restrictions may narrow but never grant authority. |
| `concorde-plan-context` | `source_artifacts` | array of ArtifactRef | Optional, defaults to `[]`; explicit supporting source refs within the admitted owned/provider context or selected-feature reflection document/plan. Exact ID, owner, path, digest, and existing read policy are checked. |
| `concorde-plan-author-context` | `task` | TypedValue `concorde-plan-context@1` | Original caller input, preserved as structured data. |
| `concorde-plan-author-context` | `planning_context` | TypedValue `concorde-planning-context@1` | Exact validated context from Understanding, with field semantics in its providing feature. |
| `concorde-plan-result` | `feature_id` | string | Stable authored `feature.*` identity from the host workspace. |
| `concorde-plan-result` | `feature_path` | string | Same selected canonical feature file as the invocation. |
| `concorde-plan-result` | `attempt_dir` | string | Exactly `.concorde/attempts/<feature_id>`; host-derived and checked before use. |
| `concorde-plan-result` | `source_digest` | SHA-256 string | The admitted planning source digest; not a digest of newly written attempt files. |
| `concorde-plan-result` | `artifacts` | array of ArtifactRef | Unique refs to authored attempt files, including `plan.md` and initial `tasks.md`; optional research/data-model/quickstart appear only when created. IDs follow `attempt:<feature_id>:<attempt-relative-path>`. |

`concorde-plan-context` is a data type ID here. It is not the identity of an invocation of the internal
Skill with the same spelling. `concorde-planning-context` is a different type: resolved information
produced by Understanding, not caller arguments.

```json
{
  "type_id": "concorde-plan-context",
  "schema_version": 1,
  "data": {
    "feature_path": "specs/concorde/modules/lifecycle/features/002-plan-attempt.md",
    "request": "Plan explicit producer-to-consumer data contracts",
    "constraints": ["Keep durable source files unchanged during planning"]
  }
}
```

The mapping is explicit: the context provider receives `task.data.feature_path`; the host retains the
complete task while resolving context. The author receives `{task, planning_context}` after feature
identity, source digest, references, and policy are checked. The plan Operation exposes only the
validated `concorde-plan-result` to its parent, not the internal context/author result list. Standard
loop and triage callers copy `feature_path`, `request`, and `constraints` into the plan input.
Triage also includes its selected reflection document/plan refs as `source_artifacts`. They inherit the host configuration/worktree unchanged. They consume result identity, source digest,
attempt path, and artifact refs to prepare tasks/implementation; they do not infer those from prose.

Missing input, wrong type/version, unknown fields, a non-feature path, ambiguous provider, stale
context, or a result for another feature prevents the next stage. Refs into a completed attempt
expire when delivery removes it. A future caller must not retry a partially failed author solely
because a plan file exists; it must inspect the failed result and current attempt state.

## Related Features

- The typed boundary depends on `feature.capabilities.provide-capability-surfaces` for
  `contract.capabilities.operation-data`; executable adoption is a separately identified runtime gap.


- `feature.lifecycle.specify-behavior` produces the durable feature file this phase turns into a
  temporal attempt.
- `feature.lifecycle.execute-and-reconcile` consumes the plan and dependency-ordered tasks this phase
  authors.
- `feature.lifecycle.standard-development-loop` nests this Operation as its opaque planning stage
  between specify and tasks/implement.
- `feature.understanding.bound-planning-context` provides `contract.understanding.planning-context`,
  the exact read-only context this Operation's first stage consumes; ownership and exclusion rules for
  dependency bodies are defined there, not duplicated here.
- `feature.capabilities.permission-bounded-execution` provides
  `contract.capabilities.permission-bounded-execution`, the policy compiler and enforced launch every
  leaf in this Operation receives.
- `feature.reflections.record-and-triage` receives the per-file reflection documents the plan author
  records for unresolved problems.

## User Scenarios & Testing

### User Story 1 — Plan through published feature boundaries (Priority: P1)

A maintainer invokes `concorde-plan` without granting it ambient access to every module's architecture
and implementation; the Operation consumes `contract.understanding.planning-context` as a bounded
read-only input rather than resolving provider ownership itself.

**Why this priority**: Module hierarchy is useful only when consumers can depend on published feature
promises without understanding private module internals.

**Independent Test**: In a two-module fixture, invoke `concorde-plan` and assert that the selected
feature's owned context and the explicitly required dependency feature file are readable by the author
stage, while the dependency module's architecture, source, tests, descendants, and unrelated features
remain denied.

**Acceptance Scenarios**:

1. **Given** a selected feature that requires an interface provided by another module's feature,
   **When** `module.concorde.understanding` resolves planning context, **Then** `entity.lifecycle.plan-operation`
   receives that provider feature specification with a reason trace before the author leaf runs.
2. **Given** the resolved context, **When** `entity.lifecycle.plan-author-skill` executes, **Then** its
   only durable writes land in the selected attempt plus authorized reflections, and context
   resolution has already completed before authorship starts.

### Author the plan

1. Resolve context and research unknowns against providing architecture/owned code/tests and exact
   published dependency feature promises.
2. Produce data/interface delta and runnable quickstart artifacts only when useful.
3. Generate test-first, dependency-ordered, independently verifiable tasks with exact ownership/paths.

## Requirements

- **FR-001**: Planning MUST treat the direct feature file and module architecture as intent and code/tests as current realization/evidence.
- **FR-002**: Plan/research/data model/quickstart/task/checklist files MUST remain under `.concorde/attempts/<stable-feature-id>/`.
- **FR-003**: Tasks MUST cover each requirement, changed interface/entity, code/test path, projection, migration, and validation consequence.
- **FR-004**: Planning MUST preserve durable sources/code and record each unresolved problem in one `.concorde/reflections/pending/R-NNN.md` without performing triage.
- **FR-005**: The public `concorde-plan` capability MUST be a paired LangGraph Operation that dispatches
  `module.concorde.understanding`'s bounded planning-context leaf before its own internal
  plan-authoring leaf, in that order.
- **FR-006**: The plan-authoring invocation MUST write only the selected attempt artifacts plus an
  authorized per-file reflection occurrence and MUST leave durable feature, architecture, code, test,
  package, and generated sources byte-identical.
- **FR-007**: Planning and attempt creation MUST begin only after the agent enters a unique linked
  worktree at committed primary `HEAD`, unless the maintainer explicitly authorizes primary mutation;
  missing committed input MUST stop instead of being recovered from a stash or dirty primary path.

## Success Criteria

- **SC-001**: `concorde-plan` runs a real two-stage LangGraph in order, passes the context result to
  the plan author, prevents the author stage after a context failure, and remains installable for both
  integrations.

## Edge Cases

- Code has an architecturally significant entity missing from architecture.
- A required interface change affects several features/modules and expands the declared task ownership set.
- An incidental related feature remains a summary and never grants body access.
