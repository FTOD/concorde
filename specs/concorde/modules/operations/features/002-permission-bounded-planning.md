---
id: feature.operations.permission-bounded-planning
kind: feature
module: module.concorde.operations
related_features:
  - feature.operations.standard-development-loop
  - feature.skills.project-workflow
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.record-workflow-reflections
interfaces:
  provided:
    - contract.operations.permission-bounded-execution
    - contract.operations.plan
  required:
    - contract.skills.workflow-guidance
    - contract.skills.agent-surface
    - contract.workspace.feature-workspace
evidence_status: verified
---

# Feature Design: Permission-Bounded Planning Operations

**Created**: 2026-09-02

**Input**: Restrict every LangGraph Operation through Codex sandbox/permission profiles or Claude
permission rules plus sandbox enforcement. Promote planning from one leaf Skill into an Operation,
and preserve module abstraction so a planner uses dependency feature specifications rather than the
dependency modules' private architecture or implementation.

## Outcome and Scope

**Outcome**: A workflow host can launch every Codex or Claude agent selected by a Concorde Operation
with a validated least-privilege filesystem policy, and a maintainer can invoke `concorde-plan` as a
permission-bounded Operation that sees the selected feature, its own implementation context, and
only the exact dependency feature specifications needed at module boundaries.

**In scope**:

- One integration-neutral, fail-closed permission policy on every Operation and every composed leaf
  Skill invocation.
- Deterministic compilation of that policy into Codex permission-profile configuration and Claude
  permission rules plus sandbox settings.
- Concrete read/write/deny paths resolved from Workspace Protocol 13 and stable feature/interface
  relationships before an agent starts.
- A paired `concorde-plan` LangGraph Operation composed from a read-only planning-context leaf and a
  temporal plan-authoring leaf.
- Migration of existing standard-development and reflection-triage Operations to the same policy
  contract, including their installed Codex and Claude projections.
- Optional outer OS/container isolation when the selected integration cannot enforce the declared
  boundary itself.

**Out of scope**:

- Implementing LangGraph scheduling, Codex, Claude Code, container runtimes, or their security
  mechanisms inside Concorde.
- Granting network, credential, destructive, or external-write authority merely because an
  Operation requests it.
- Letting a planner inspect a dependency module's private architecture, source, tests, attempts, or
  descendant modules when its published feature specification is sufficient.
- Treating prompt instructions as file-permission enforcement.

## Usage

A maintainer selects one feature and invokes `concorde-plan`. The Operation first resolves an exact
planning context: the selected feature, its providing architecture and owned implementation
locators, its attempt paths, and the direct feature files that own its explicitly required
interfaces. It then launches the plan author under a policy that can read only that context,
write only the selected attempt and the centralized reflection log, and cannot mutate durable
architecture, feature, source, or test files.

The same host can invoke the standard development or reflection-triage Operation. Before each direct
leaf Skill invocation, the runtime supplies one immutable launch specification containing the
chosen integration, prompt/prior results, normalized policy, native configuration, and digests. The
injectable process executor version-checks `codex exec` or restricted `claude -p`, scrubs ambient
secret variables, and returns a matching enforcement receipt; tests inject the runner and never call
a live model.

### Edge and failure cases

- An Operation with no permission policy, a missing stage/Skill binding, an unsafe or unresolved
  path, or a write path outside the leaf Skill's authority is invalid and does not launch an agent.
- If Codex permission profiles are unavailable or rejected, the host may use an equivalently narrow
  Codex sandbox or outer OS/container boundary; otherwise execution stops.
- Claude execution stops when its sandbox cannot initialize, and it may not retry a denied command
  outside the sandbox.
- User, project, or managed configuration may narrow an Operation policy, but a less restrictive
  layer may not widen it. A conflict stops the affected invocation.
- A related feature that does not own one of the selected feature's required interfaces remains a summary/navigation
  reference and its body is not added to the readable set.
- A task that truly changes a dependency module must select that module's feature in a separate
  lifecycle rather than widening the current planner's read or write boundary silently.

## Edge Cases

- The selected feature is new and has no stable-ID attempt until specification persists its ID.
- One related feature provides several interfaces, but only a subset is required by the selected
  feature; the context receipt names the exact interface reasons while permission is granted to the
  single owning feature file.
- A source locator crosses into another module or points through a symlink; policy resolution rejects
  it instead of treating the broad executable root as authority.
- A user-level Codex or Claude setting is stricter than the Operation policy; the stricter effective
  boundary wins and a required denied action fails explicitly.
- A host supports LangGraph but neither a compatible native agent sandbox nor an approved outer
  isolation layer; graph construction may succeed, but agent launch fails before the first Skill.
- Two Skills share one LangGraph stage but require different write sets; each receives its own agent
  launch policy and neither receives the other Skill's rights.

## User Scenarios & Testing

### User Story 1 — Enforce every Operation launch (Priority: P1)

A workflow host runs any manifested Operation and obtains one validated launch configuration per
composed leaf Skill, with exact allowed reads, writes, denies, network posture, and enforcement
requirements.

**Why this priority**: Without host-enforced permissions, every higher-level workflow inherits the
full ambient filesystem authority of its agent process.

**Independent Test**: Load every Operation from Package Manifest 2, resolve a fixture workspace,
compile Codex and Claude launch configurations, and prove undeclared reads/writes are rejected while
declared paths remain usable.

**Acceptance Scenarios**:

1. **Given** a valid Operation and selected feature, **When** its next Skill is scheduled, **Then**
   the executor receives a concrete policy and integration configuration before any agent starts.
2. **Given** an incomplete, unsafe, wider-than-authorized, or unenforceable policy, **When** the host
   prepares the invocation, **Then** it fails closed and no downstream stage or agent runs.

### User Story 2 — Plan through published feature boundaries (Priority: P1)

A maintainer invokes one planning Operation without granting it ambient access to every module's
architecture and implementation.

**Why this priority**: Module hierarchy is useful only when consumers can depend on published
feature promises without understanding private module internals.

**Independent Test**: In a two-module fixture, run the planning-context stage and assert that the
selected module's owned context and the explicitly required dependency feature file are readable,
while the dependency module's architecture, source, tests, descendants, and unrelated features are
denied.

**Acceptance Scenarios**:

1. **Given** a selected feature that requires an interface provided by another module's feature,
   **When** planning context is resolved, **Then** that provider feature specification is included
   with a reason trace and the provider module's private internals are excluded.
2. **Given** only an incidental or unrelated feature reference, **When** context is resolved, **Then**
   the reference remains a summary and its body is not readable by the planning agent.

### User Story 3 — Preserve Codex and Claude parity (Priority: P2)

A maintainer receives equivalent effective file boundaries whether an Operation launches Codex or
Claude Code.

**Why this priority**: Integration-specific syntax must not change Concorde's authority model.

**Independent Test**: Compile one normalized policy to both integrations and compare canonical
effective read/write/deny sets before validating their native configuration shapes.

**Acceptance Scenario**:

1. **Given** the same normalized policy, **When** Codex and Claude configurations are rendered,
   **Then** both deny undeclared paths, allow the same declared paths, disable ambient network by
   default, and fail rather than falling back to an unconfined process.

## Interfaces

### `contract.operations.permission-bounded-execution` — Compile and enforce an Operation launch

- **Consumer**: Paired Concorde Operations, workflow hosts, Codex/Claude executors, capability
  validators, installers, and Operation integration tests.
- **Direction**: Operation definition plus resolved workspace authority to one immutable normalized
  policy and integration-native launch configuration per composed leaf Skill.
- **Entry points**: Shared Operation runtime, each `operations/<name>/operation.py` policy declaration,
  and the injected executor contract.
- **Inputs**: Operation/stage/Skill identity; selected integration; project root; Protocol 13 feature,
  architecture, ancestry-summary, related-feature-summary, attempt, reflection, and executable
  context; declared path roles; network posture; and optional outer-sandbox requirement.
- **Outputs**: Canonical read/write/deny path sets; Codex named permission-profile/config selection;
  Claude `permissions` rules and strict sandbox settings; enforcement status; and an immutable launch
  specification attached to the Skill invocation.
- **Obligations**: Resolve real project-relative non-symlink paths; apply deny-before-allow semantics;
  keep writes a subset of the Skill's declared mutation authority; disable network unless explicitly
  required; scrub ambient credential access; reject profile widening; and prevent launch unless one
  supported enforcement layer covers every declared path rule.
- **Failures**: Missing policy coverage, duplicate or mismatched Skill bindings, path escape,
  symlink/unsafe root, unavailable native sandbox without an approved outer equivalent, unsupported
  integration, configuration widening, or executor refusal stops the invocation and all downstream
  nodes.
- **Compatibility**: Codex uses a selected named permission profile when supported and otherwise an
  equivalently restrictive sandbox/outer boundary. Claude uses permission rules together with an
  enabled sandbox, `failIfUnavailable`, and no unsandboxed retry. Native syntax may evolve while the
  normalized policy and fail-closed semantics remain stable.
- **Example**: The planning author receives read access to
  `specs/payments/features/001-charge.md`, its own module architecture/owned locators, and an explicit
  provider feature such as `specs/ledger/features/002-record-entry.md`; it receives write access only
  to `.concorde/attempts/feature.payments.charge/**` and `.concorde/reflections/log.md`.
- **Implementing entities**: `entity.operations.runtime`, `entity.operations.definition`,
  `entity.operations.state`, `entity.operations.permission-context`,
  `entity.operations.policy-compiler`, `entity.operations.process-launcher`, and
  `entity.operations.coding-agent`.

### `contract.operations.plan` — Permission-bounded planning LangGraph

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
- **Compatibility**: `concorde-plan` remains the public capability name but changes from a leaf Skill
  to a paired Operation. The former planning prompt moves to a uniquely named leaf capability and no
  same-name compatibility alias remains.
- **Example**: `concorde-plan "Add idempotent capture"` runs a read-only context stage, then a plan
  author stage whose prior result names the exact feature-spec and owned implementation boundary.
- **Implementing entities**: `entity.operations.plan`, `entity.operations.plan-skill`,
  `entity.operations.runtime`, `entity.operations.permission-context`,
  `entity.operations.policy-compiler`, `entity.operations.process-launcher`,
  `entity.operations.definition`, `entity.operations.state`, and
  `entity.operations.coding-agent`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.operations.runtime` | Validates direct capability/binding coverage and supplies immutable leaf launch specifications. | Preserves nested opacity and passes exact prior capability results. |
| `entity.operations.definition` | Carries exact stage, occurrence, capability, agent, and narrowing bindings. | Prevents undeclared, duplicated, widened, or order-mismatched execution. |
| `entity.operations.state` | Carries request plus prior bounded capability results/receipts. | Lets the planning author consume the context result without reopening unrelated sources. |
| `entity.operations.permission-context` | Resolves Protocol 13 and interface ownership into concrete paths/reasons/denies. | Includes provider feature promises while excluding provider internals and other attempts. |
| `entity.operations.policy-compiler` | Freezes normalized policy and Codex/Claude/outer configurations. | Proves native effective-set parity and narrowing-only composition. |
| `entity.operations.process-launcher` | Performs injectable real CLI preflight/execution. | Starts only after digest/enforcement/version checks and returns a structured receipt. |
| `entity.operations.plan` | Owns the public context → author graph. | Keeps two internal leaves behind one stable public Operation identity. |
| `entity.operations.plan-skill` | Documents and projects the public planner. | Resolves the installed paired entry point for both integrations. |
| `entity.operations.coding-agent` | Enforces the selected Codex, Claude, or outer sandbox configuration. | Applies native boundaries while model transport remains outside project network authority. |
| `entity.operations.standard-dev-loop` | Migrates the existing lifecycle graph to per-Skill launch policies. | Invokes planning through the same bounded contract and retains downstream failure boundaries. |
| `entity.operations.reflections-triage` | Migrates investigation and implementation agents to explicit policies. | Keeps investigators read-only and implementers scoped to isolated worktrees. |

## Related Features

- `feature.operations.standard-development-loop` is refined by adding per-Skill launch policies and
  composing the new public planning Operation semantics without bypassing its context gate.
- `feature.skills.project-workflow` is depended on for complete canonical leaf prompts and Codex/Claude
  projection; this feature changes the planning capability's kind and adds the leaf capabilities the
  new Operation composes.
- `feature.concorde.workflow.plan-delivery` is refined so external module dependencies are consumed
  through their feature specifications while planning artifacts remain temporal.
- `feature.concorde.record-workflow-reflections` is refined so its investigator/implementer launches
  use the same explicit policy and isolated-worktree enforcement.

## Requirements

### Functional Requirements

- **FR-001**: Every manifested Operation MUST declare one permission binding for every composed leaf
  Skill occurrence, and deterministic validation MUST reject missing, duplicate, unknown, or
  stage/order-mismatched bindings.
- **FR-002**: The shared Operation runtime MUST reject graph construction without a leaf launch
  factory and MUST give the executor a non-null immutable launch specification
  containing the selected integration, normalized read/write/deny paths, network posture, native
  configuration, Skill body, and prior stage results before that Skill executes.
- **FR-003**: Path resolution MUST use Protocol 13 authorities and real project-relative paths,
  reject escapes/symlinks/unknown tokens, and deny all undeclared project paths by default.
- **FR-004**: A leaf invocation's writable paths MUST be limited to that leaf Skill's declared
  mutation authority; a stage containing several Skills MUST NOT grant their union to every Skill.
- **FR-005**: Codex compilation MUST select a named permission profile with explicit
  `read`/`write`/`deny` filesystem rules and non-interactive approval behavior, or require an
  equivalently restrictive supported sandbox/outer boundary.
- **FR-006**: Claude compilation MUST produce scoped permission rules and enable filesystem/network
  sandboxing with hard failure when unavailable and no unsandboxed retry; deny rules MUST take
  precedence over ask/allow rules.
- **FR-007**: Native/user/managed policy may narrow but MUST NOT widen the normalized Operation
  policy, and an executor unable to prove the effective boundary MUST fail before agent launch.
- **FR-008**: The public `concorde-plan` capability MUST be a paired LangGraph Operation that composes
  a read-only planning-context leaf and a separate temporal plan-authoring leaf in that order.
- **FR-009**: Planning context MUST include the complete selected feature, providing-module
  architecture and owned implementation/test locators, and only dependency feature bodies that
  deterministically own an interface listed in the selected feature's `interfaces.required` set;
  every inclusion MUST carry the required-interface ID as its reason trace.
- **FR-010**: Planning context MUST exclude dependency module architecture/source/tests/attempts,
  descendant-module internals, unrelated feature bodies, and every other attempt.
- **FR-011**: The plan-authoring invocation MUST write only the selected attempt artifacts plus an
  authorized centralized reflection occurrence and MUST leave durable feature, architecture, code,
  test, package, and generated sources byte-identical.
- **FR-012**: Standard-development and reflection-triage Operations MUST adopt the same per-Skill
  policy contract without weakening their current order, state, worktree isolation, or downstream
  failure behavior.
- **FR-013**: Installation and checkout synchronization MUST project the new Operation/leaf inventory
  and its Codex/Claude configuration semantics with no cross-kind name collision or legacy alias.
- **FR-014**: An Operation MUST be able to compose another manifested Operation by its public
  capability identity without loading or flattening the nested Operation's internal stages/Skills;
  resolution MUST reject cycles and a missing explicit enforcing dispatcher, preserve nested
  state/failure/policy boundaries, and make the
  standard-development and reflection-routing graphs reference `concorde-plan` rather than its
  private leaves wherever they invoke planning.

### Non-Functional Requirements

- **NFR-001**: Permission-policy loading, normalization, validation, and native rendering MUST be
  deterministic, offline, and independent of LangGraph import until graph construction.
- **NFR-002**: Equivalent normalized policies MUST produce equivalent effective filesystem boundaries
  for Codex and Claude in contract tests.
- **NFR-003**: Default Operation execution MUST require no network access and expose no ambient secret
  environment variables unless an explicit reviewed policy adds them.

### Assumptions

- Workflow hosts own agent-process creation and can pass Codex or Claude native configuration; the
  injected executor contract is therefore the enforcement handoff, not LangGraph itself.
- Codex and Claude configuration syntax can change independently; Concorde validates a stable
  normalized policy and renders version-appropriate native configuration at the host boundary.
- The selected feature's providing module may expose owned implementation locators needed to change
  that module; every dependency module remains opaque behind its feature specifications.

## Success Criteria

- **SC-001**: All manifested Operations pass exact policy-coverage validation, and deleting or
  widening any single binding makes the focused contract test fail before executor invocation.
- **SC-002**: A two-module planning fixture proves 100% of justified dependency feature files are
  readable and 100% of dependency private architecture/source/test/attempt paths are denied.
- **SC-003**: Codex and Claude renderers produce the same canonical effective path sets for every
  shipped policy, with network disabled and sandbox unavailability tested as a hard failure.
- **SC-004**: `concorde-plan` runs a real two-stage LangGraph in order, passes context output to the
  plan author, prevents the second stage after a first-stage failure, and remains installable for
  both integrations.
- **SC-005**: Full unit, contract, integration, installation/projection, deterministic Profile 7,
  and documentation checks pass with no undeclared durable mutation or compatibility capability.
- **SC-006**: Nested-operation tests prove the outer graph sees only public `concorde-plan`, a trusted
  dispatcher runs inner context/author with independent non-null launches, missing dispatcher/factory
  invokes no executor, and a failure at either level prevents the correct downstream nodes.

Implementation/package evidence additionally distinguishes 17 packaged leaves (15 public, two
internal), three public Operations, and the same 18 projected capabilities in Codex and Claude.
