---
id: feature.capabilities.provide-capability-surfaces
kind: feature
module: module.concorde.capabilities
related_features:
  - id: feature.concorde.workflow
    relation: depended_on_by
  - id: feature.lifecycle.standard-development-loop
    relation: depended_on_by
  - id: feature.capabilities.permission-bounded-execution
    relation: depended_on_by
  - id: feature.capabilities.run-deterministic-tools
    relation: depends_on
  - id: feature.understanding.resolve-feature-workspace
    relation: depends_on
  - id: feature.capabilities.maintain-agent-surfaces
    relation: depended_on_by
  - id: feature.distribution.package-concorde
    relation: depended_on_by
interfaces:
  provided:
    - contract.capabilities.agent-surface
    - contract.capabilities.skill-contract
    - contract.capabilities.operation-data
  required:
    - contract.capabilities.tools
    - contract.understanding.feature-workspace
---

# Feature Design: Provide Capability Surfaces

## Outcome and Scope

Users receive one complete public Skill for each Concorde lifecycle choice, while Operations may use
packaged internal effect-declared leaves without exposing implementation entry points. The same
public prompt semantics reach Codex and Claude, and an Operation loads canonical bodies without
copying or flattening them. Projected Operation prompts retain the exact paired path but enter it
through the colocated managed-runtime bootstrap rather than an ambient Python interpreter.

This feature covers leaf Skill source, metadata, Tool crossings, projection, and phase boundaries. It
does not define LangGraph topology, execute an agent model, or own project artifacts.

## Usage

Invoke the smallest public capability that owns the requested phase. The 15 projected leaf Skills
are:

| Capability | Maintained purpose |
|---|---|
| `concorde-constitution` | Create or amend project governance from the complete constitution format. |
| `concorde-init` | Preview/apply root architecture and optionally a separate docsite scaffold. |
| `concorde-context` | Return one bounded module or feature altitude. |
| `concorde-validate` | Return deterministic sorted findings without repair. |
| `concorde-ask` | Answer one grounded workflow/architecture question read-only with source citations. |
| `concorde-specify` | Create or revise one direct complete feature design. |
| `concorde-clarify` | Resolve up to three high-impact ambiguities in that design. |
| `concorde-checklist` | Create a reviewer-owned requirements-quality checklist. |
| `concorde-tasks` | Generate dependency-ordered, test-first executable tasks. |
| `concorde-analyze` | Audit consistency/coverage without mutation. |
| `concorde-implement` | Execute dependency-ready tasks and record canonical passing evidence. |
| `concorde-converge` | Append only genuinely remaining verified work. |
| `concorde-taskstoissues` | Create dependency-aware external issues only with explicit external-write authority. |
| `concorde-fast-loop` | Reconcile one eligible small, already-specified change without an attempt. |
| `concorde-deliver` | Validate and remove exactly one completed attempt. |

Three public Operation skills share that namespace: `concorde-plan` runs bounded context → temporal
author; `concorde-standard-dev-loop` runs the standard lifecycle graph; and
`concorde-reflections-triage` runs only its explicitly selected conditional route. The packaged
`concorde-plan-context` and `concorde-plan-author` leaves are internal Operation inputs and never
project to users. Native deterministic functionality such as `concorde explore` remains a Tool, not
a Skill or Operation.

In a checkout, canonical Skills invoke root `scripts/` and templates. In an installed project,
projected Skills invoke `.concorde/framework/scripts/` and `.concorde/framework/operations/` through
the managed runtime launcher; no shell activation is required.

## Interfaces

### `contract.capabilities.agent-surface` — Installed capability projection

- **Consumer**: Installer, checkout synchronization, Codex, and Claude.
- **Direction**: Canonical public leaf and paired Operation Markdown to integration-native Skill
  files; internal leaves remain framework-only.
- **Entry points**: `skills/<name>/SKILL.md`, `operations/<name>/SKILL.md`,
  `src/concorde/capabilities/skill_assets.py`, and the manifest-declared `scripts/run-operation.py` bootstrap.
- **Inputs**: Package Manifest 2 inventories, canonical metadata/body, integration, installed
  framework prefix, paired Operation entry point, and colocated runtime-launcher path when
  applicable.
- **Outputs**: One regular `.agents/skills/<name>/SKILL.md` or `.claude/skills/<name>/SKILL.md` file
  with source, kind, and entry-point provenance.
- **Obligations**: Require globally unique safe names; validate exposure/effects and mixed acyclic
  capability topology; resolve only declared tokens; preserve bodies; filter internal leaves;
  distinguish source/kind/entry-point role; route Operations through the managed launcher while
  retaining their paired path; reject extras, symlinks, collisions, or unpaired Operations.
- **Failures**: Invalid exposure/effects, manifest drift, internal projection, unsafe source/target,
  unknown/cyclic capability, unresolved token, or output/role collision blocks projection.
- **Compatibility**: Package Manifest 2 and Concorde 2.1.0 contain 17 packaged leaves and three
  Operations but expose exactly 15 public leaves plus three Operations, with no legacy reader/alias.
- **Implementing entities**: `entity.concorde.package-manifest`, `entity.capabilities.skill-sources`,
  `entity.capabilities.operation-sources`, `entity.capabilities.projector`, and
  `entity.capabilities.operation-launcher`.
- **Example**: `operations/concorde-plan/SKILL.md` projects to
  `.agents/skills/concorde-plan/SKILL.md` with `kind: operation`/entry-point provenance, while
  `concorde-plan-context` and `concorde-plan-author` do not project; its command is
  `python3 .concorde/framework/scripts/run-operation.py
  .concorde/framework/operations/concorde-plan/operation.py ...`.

### `contract.capabilities.skill-contract` — Leaf phase behavior

- **Consumer**: Maintainers, coding agents, and paired Operations.
- **Direction**: User or Operation input plus bounded project context to one phase result and its
  explicitly authorized effects.
- **Entry points**: The 17 Package Manifest 2 leaf Skills under `skills/` (15 public, two internal).
- **Inputs**: User intent, Protocol 13 context when path-sensitive, complete canonical prompt, and
  only the maintained/temporal/executable sources that prompt authorizes. A direct invocation runs
  its workspace Tool; an Operation-composed invocation instead receives the host's canonical,
  digest-bound Protocol 13 receipt, which satisfies that same gate without reopening global resolver
  inputs inside the narrower leaf sandbox.
- **Outputs**: Direct invocation returns its conversational result, explicit Tool results, evidence,
  and only phase-authorized changes. Operation invocation returns Capability Completion Envelope 1:
  bound identity/digests, semantic `success | failed`, usable output, limitations, and non-empty gate
  evidence.
- **Obligations**: Preserve complete prompt/phase boundaries; keep public leaves independently
  invocable and internal leaves Operation-only; declare exact effects when composed; invoke Tools
  explicitly; preserve the committed-base isolated-worktree gate in every mutating source/projection;
  accept a trusted Operation workspace receipt as the completed Protocol 13 gate; never rerun the
  broad resolver from a narrower leaf policy; report every mandatory gate in the completion envelope;
  surface failures/evidence limits; contain no multi-Skill graph.
- **Failures**: Workspace/tool failure, missing authority, invalid project state, denied permission,
  or unmet phase gate stops that Skill without fallback to another source.
- **Compatibility**: Protocol 13, Delivery Proposal 9, and Capability Completion Envelope 1 use Tool
  terminology. Stable public names are `concorde-*`; retired dotted prompt identities are not
  aliases. Direct conversational invocation remains unchanged; the envelope is required only when a
  real agent process is composed by an Operation.
- **Implementing entities**: `entity.capabilities.skill-prompt`,
  `entity.capabilities.completion-envelope`, `entity.concorde.coding-agent`,
  `module.concorde.understanding`, `module.concorde.lifecycle`, and `module.concorde.reflections`.
- **Example**: The plan Operation launches internal read-only context then temporal author leaves
  with distinct effect-derived policies.


### Target Operation Data Contract

### `contract.capabilities.operation-data` — Separate configuration and typed runtime data

- **Consumer**: Operation authors, agent Skill adapters, nested Operation dispatchers, and project init.
- **Direction**: Initialized configuration plus typed caller input to one typed domain result.
- **Entry points**: Target Python boundary `run(configuration, runtime_input, *, host_context)`;
  a target process adapter reads one UTF-8 JSON invocation from stdin and writes one JSON result to
  stdout. Logs use stderr. Domain fields are not positional arguments or individual CLI flags.
- **Inputs**: One `concorde-operation-invocation@1` containing separate `configuration` and `input`
  values as defined below. The installed Skill loads project configuration; callers supply runtime
  input. The trusted host checks that the submitted configuration matches its project snapshot.
- **Outputs**: One `concorde-operation-result@1`, whose `output` type is fixed by the selected
  Operation. Host execution/completion receipts remain separate validation evidence.
- **Obligations**: Validate type/version/fields before effects, bind the configuration and host
  workspace, validate domain output before handing it on, and keep nested operations opaque.
- **Failures**: Unknown type/version/field, invalid field or configuration, selection mismatch,
  incompatible handoff, stale reference, or invalid semantic completion blocks downstream work.
  Failure after execution may leave partial authorized artifacts; no automatic rollback is implied.
- **Compatibility**: **Target design, not the current executable ABI.** Package Manifest 2 currently
  invokes paired graph parsers with CLI arguments. Runtime adoption requires one explicit executable
  cutover of parsers, schemas, dispatch, init/config, projected Operation Skills, and tests. It must
  not silently reinterpret old arguments or fall back from malformed JSON to prose.
- **Example**: The complete planning invocation below carries integration configuration separately
  from `feature_path` and task intent.
- **Implementing entities**: `entity.capabilities.operation-pair`,
  `entity.capabilities.operation-launcher`, `entity.capabilities.operation-runtime`,
  `entity.capabilities.operation-data-contract`, and `module.concorde.understanding`.

- **Field definitions**: The following sections define the target serialized contract.

#### Type identity and field rules

A **TypedValue** is exactly `{ "type_id": string, "schema_version": integer, "data": object }`.
`(type_id, schema_version)` resolves exactly one field definition; it does not select executable code.
`operation_id` selects a registered Operation. The internal Skill named `concorde-plan-context` and
the payload type with that spelling occupy separate namespaces. Moving a script does not rename a
type. Version 1 rejects unknown fields and versions; incompatible changes increment the version and
update producer/consumer bindings together. Optional fields have only the defaults stated below;
null is rejected unless explicitly allowed. All listed fields are required unless marked optional.

The common version-1 objects are:

| Object | Fields / JSON types | Meaning and constraints |
|---|---|---|
| `concorde-operation-invocation@1` | `type_id` (constant), `schema_version` (1), `operation_id` (registered string), `mode` (`describe-policy` or `execute`), `configuration` (TypedValue), `input` (TypedValue) | A transport envelope, not a TypedValue itself. The registered Operation fixes the input/output types. No other fields are accepted. |
| `concorde-operation-configuration@1.data` | `integration` (`codex` or `claude`), `enforcement` (`native` or `outer`) | Both explicitly configured during init; no per-script default. `outer` requires independently verified host enforcement. Neither setting grants filesystem or external-action authority. |
| `concorde-operation-result@1` | `type_id` (constant), `schema_version` (1), `operation_id` (registered string, or null before resolution), `invocation_id` (nonempty host-issued string), `mode` (same as request, or null before decoding), `status` (`succeeded`, `described`, `blocked`, or `failed`), `output` (TypedValue or null), `errors` (Error array) | A transport envelope. `succeeded` requires execute mode, the registered domain output type, no errors, and valid completion evidence. `described` requires describe-policy mode, null output, and no errors; it never satisfies a data dependency. Blocked/failed results have null output and at least one error. Null operation/mode is allowed only when rejection occurs before those fields can be resolved. |
| `Error` | `code` (string), `field` (JSON Pointer string), `message` (nonempty string), optional `stage` (string, absent outside a stage) | Codes: `invalid_json`, `unknown_type`, `unsupported_version`, `invalid_field`, `configuration_mismatch`, `workspace_mismatch`, `stale_reference`, `incompatible_handoff`, `execution_failed`. Use the empty pointer for a whole-request error. |
| `ArtifactRef` | `id` (nonempty stable artifact string), `path` (nonempty project-relative POSIX string), `digest` (`sha256:` plus 64 lowercase hex digits) | No absolute/drive path, parent traversal, or symlink. Consumer rechecks bytes and existing permission rights; a reference grants no read access. Directory inventories use refs to individual files. An absent/deleted artifact is not a live reference. |

The host derives project/framework roots, stable feature identity, attempt paths, source digest,
invocation identity, policy, and execution receipts. They are not accepted from arbitrary caller
fields. A resolved context payload may report those facts, but the host validates it against its
own resolver/receipt before use. Domain data never substitutes for a permission receipt.

#### Project configuration lifecycle

The target location is `.concorde/config.json` under a new `operation_configuration` key containing
the configuration TypedValue. Existing `profile_version`, `root_module_id`, and
`specification_root` keep their meanings. The initializer proposes the selected integration and
enforcement setting together with the project config; apply establishes them once. Existing
projects need an explicit configuration proposal instead of implicit defaults or silent overwrite.
Until that implementation exists, current init creates only the existing source-profile settings.

Every invocation loads one complete project configuration; version 1 has no per-call or per-Operation
override merge. The host snapshots and binds it with the work context, and all nested calls inherit
that snapshot. A later project edit applies only to new runs. No runtime input may supply integration,
framework location, credentials, sandbox grants, or an authorization override. Install-time
integration selection and reflection-triage settings are separate existing authorities until the
runtime migration explicitly reconciles them.

#### Complete target example

The following is the JSON a future Skill/host adapter would send on the Python entry point's stdin.
It is not a command supported by the current launcher.

```json
{
  "type_id": "concorde-operation-invocation",
  "schema_version": 1,
  "operation_id": "concorde-plan",
  "mode": "execute",
  "configuration": {
    "type_id": "concorde-operation-configuration",
    "schema_version": 1,
    "data": {"integration": "codex", "enforcement": "native"}
  },
  "input": {
    "type_id": "concorde-plan-context",
    "schema_version": 1,
    "data": {
      "feature_path": "specs/example/features/001-search.md",
      "request": "Plan the approved search change",
      "constraints": []
    }
  }
}
```

#### Target result example

This illustrative result shows the wrapper/domain distinction; its fixture digests are not live
execution evidence. Real hosts must additionally validate completion and workspace receipts.

```json
{
  "type_id": "concorde-operation-result",
  "schema_version": 1,
  "operation_id": "concorde-plan",
  "invocation_id": "example-invocation-1",
  "mode": "execute",
  "status": "succeeded",
  "output": {
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
  },
  "errors": []
}
```

#### Rejected handoff example

An otherwise valid planning invocation with `input.schema_version: 2` has no supported input
binding. The host emits the following blocked result before launching either planning stage:

```json
{
  "type_id": "concorde-operation-result",
  "schema_version": 1,
  "operation_id": "concorde-plan",
  "invocation_id": "example-rejected-invocation",
  "mode": "execute",
  "status": "blocked",
  "output": null,
  "errors": [{
    "code": "unsupported_version",
    "field": "/input/schema_version",
    "message": "concorde-plan-context requires schema_version 1"
  }]
}
```

#### Domain type ownership and handoff validation

| Operation / boundary | Input type @1 | Output type @1 | Field-definition authority |
|---|---|---|---|
| `concorde-plan` | `concorde-plan-context` | `concorde-plan-result` | [Planning](../../lifecycle/features/002-plan-attempt.md#target-planning-data-types) |
| Planning context provider | `concorde-plan-context` | `concorde-planning-context` | [Bounded context](../../understanding/features/007-bound-planning-context.md#target-planning-context-payload) |
| Internal plan author | `concorde-plan-author-context` | `concorde-plan-result` | [Planning](../../lifecycle/features/002-plan-attempt.md#target-planning-data-types) |
| `concorde-standard-dev-loop` | `concorde-standard-dev-loop-context` | `concorde-standard-dev-loop-result` | [Standard loop](../../lifecycle/features/006-standard-development-loop.md#target-standard-loop-data-types) |
| `concorde-reflections-triage` | `concorde-reflections-triage-context` | `concorde-reflections-triage-result` | [Reflection triage](../../reflections/features/001-record-and-triage-reflections.md#target-triage-data-types) |

This table specifies types; `concorde.json` remains the current executable capability inventory.
Before a consumer runs, its host resolves the declared output-to-input mapping, checks both versions,
validates all required fields and references, and verifies feature/worktree identity. It forwards
only the mapped data. The parent receives a nested Operation's domain result, never a JSON string
of the child's internal `CapabilityResult` list. Existing `CapabilityResult.output: str`, prompt
`prior_results`, and native completion checks are the current implementation baseline, not evidence
of target-domain conformance.

Runtime migration evidence must cover configuration load/snapshot inheritance, wrong-operation
types, missing fields, old versions, unknown fields, stale/cross-feature refs, child failures, and a
complete standard-loop/triage → plan → context/author → parent round trip. Schema-valid data alone
must never advance a failed or unreceipted execution.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.capabilities.operation-data-contract` | Defines target JSON envelopes and type/version admission separately from domain field ownership. |
| `entity.capabilities.skill-sources` | Owns one canonical directory per leaf Skill. |
| `entity.capabilities.operation-sources` | Owns one canonical Python/Markdown pair per Operation. |
| `entity.capabilities.skill-prompt` | Supplies a complete public/internal leaf contract with exposure/effects. |
| `entity.capabilities.completion-envelope` | Makes Operation-hosted phase completion explicit and machine-validated. |
| `entity.capabilities.projector` | Validates and renders public leaves plus paired Operation skills while filtering internals. |
| `entity.concorde.coding-agent` | Executes the installed prompt within its declared boundary. |
| `entity.concorde.package-manifest` | Declares the exact leaf inventory and shared capability namespace. |

## Related Features

- `feature.concorde.workflow` composes every projected capability into the end-to-end lifecycle.
- `feature.lifecycle.standard-development-loop` composes six of these public leaves plus the nested
  planning Operation into one graph.
- `feature.capabilities.permission-bounded-execution` enforces a least-privilege launch for every leaf
  and Operation this feature projects.
- `feature.capabilities.run-deterministic-tools` supplies the Tool contract every leaf Skill invokes
  for deterministic actions.
- `feature.understanding.resolve-feature-workspace` supplies the Protocol 13 context every
  path-sensitive Skill resolves before other reads.
- `feature.capabilities.maintain-agent-surfaces` refreshes this repository's own checkout projection
  using the same projector.
- `feature.distribution.package-concorde` installs the same projected inventory into a target
  project.

## Usage Scenarios

1. A maintainer invokes one installed public leaf Skill directly and receives bounded phase behavior.
2. An Operation resolves a public or internal canonical leaf authority, supplies accumulated
   state, and receives an equivalent phase result.
3. Checkout synchronization and installation render identical source semantics for Codex and Claude.

## Requirements

- **FR-001**: Every path-sensitive Skill MUST resolve Protocol 13 before other project artifact reads.
- **FR-002**: Each Package Manifest 2 leaf MUST have exactly one canonical `skills/<name>/SKILL.md`,
  one globally unique name, and explicit public/internal exposure; Operation-composed leaves MUST
  declare exact effects.
- **FR-003**: A public leaf MUST remain independently invocable, an internal leaf MUST remain
  unprojected, and no leaf may declare/implement LangGraph topology over multiple Skills.
- **FR-004**: Projection MUST preserve prompt semantics and add source/kind/entry-point provenance
  deterministically for Codex and Claude; every Operation invocation MUST pass the paired path
  through the source/installed managed-runtime bootstrap.
- **FR-005**: Operations MUST load canonical leaf bodies/effects and MUST NOT embed copies or flatten
  internal/nested capability bodies in Python or Markdown.
- **FR-006**: Every canonical and projected Skill/Operation that can mutate project or external
  state MUST require a linked worktree at committed primary `HEAD` by default, exclude primary dirty
  state, and name `--allow-primary-worktree` only as an explicit maintainer-authorized override.
- **FR-007**: An Operation-composed path-sensitive leaf MUST accept the host's canonical Protocol 13
  receipt as its completed workspace gate, MUST NOT rerun the broader workspace resolver inside its
  narrowed sandbox, and MUST receive the exact declared script entry point as framework authority.
- **FR-008**: Every real agent-process leaf MUST return Capability Completion Envelope 1 with exact
  launch/workspace/bootstrap identity, semantic status, output, limitations, and non-empty unique
  gate evidence; process exit or free-form prose alone MUST NOT establish completion.
- **FR-009**: A failed mandatory gate MUST produce a failed envelope. A successful envelope MUST
  report no limitation and no failed gate; only a host-validated success may become an Operation
  capability result.

## Success Criteria

- **SC-001**: Both integrations expose exactly 15 public leaves plus three Operation skills, package
  two internal planner leaves, and have no cross-kind/role collision.
- **SC-002**: Source/projection parity and installed workflow tests prove that leaf Skill semantics and
  Tool entry points are equivalent across supported integrations and that Operation prompts select
  the intended managed venv without activation.
- **SC-003**: Injected Codex/Claude executor tests prove success, explicit failure at exit zero,
  malformed/stale completion, recoverable tool failure, and downstream stopping without a live model.

## Edge Cases

- A Skill directory name and declared `name` differ.
- A leaf Skill declares an Operation token or contains multi-Skill graph topology.
- A paired Operation uses the same public name as a leaf Skill.
- A Skill declares a Tool script that does not resolve inside the installed framework.
- An Operation projection resolves its pair but bypasses or cannot resolve the colocated bootstrap.
- An Operation already carries a validated workspace receipt; rerunning Protocol 13 would require
  global inputs outside the leaf's bounded context and is forbidden.
- A client exits zero after a mandatory gate fails; the failed completion envelope prevents state
  admission and every downstream occurrence.
