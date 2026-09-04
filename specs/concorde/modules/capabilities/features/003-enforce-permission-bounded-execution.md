---
id: feature.capabilities.permission-bounded-execution
kind: feature
module: module.concorde.capabilities
related_features:
  - id: feature.lifecycle.plan-attempt
    relation: depended_on_by
  - id: feature.lifecycle.standard-development-loop
    relation: depended_on_by
  - id: feature.reflections.record-and-triage
    relation: depended_on_by
  - id: feature.understanding.bound-planning-context
    relation: depends_on
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
interfaces:
  provided:
    - contract.capabilities.permission-bounded-execution
  required:
    - contract.capabilities.skill-contract
    - contract.understanding.feature-workspace
---

# Feature Design: Enforce Permission-Bounded Execution

## Outcome and Scope

**Outcome**: A workflow host can launch every Codex or Claude agent selected by a Concorde Operation
with a committed-base isolated-worktree preflight and a validated least-privilege filesystem policy.

**In scope**:

- One integration-neutral, fail-closed permission policy on every Operation and every composed leaf
  Skill invocation.
- Deterministic compilation of that policy into Codex permission-profile configuration and Claude
  permission rules plus sandbox settings.
- Concrete read/write/deny paths resolved from Workspace Protocol 13 and stable feature/interface
  relationships before an agent starts.
- Migration of existing standard-development and reflection-triage Operations to the same policy
  contract, including their installed Codex and Claude projections.
- Optional outer OS/container isolation when the selected integration cannot enforce the declared
  boundary itself.
- A fail-closed Git preflight for actual mutating Operation/workspace/Tool entry points, with one
  explicit maintainer-authorized primary-worktree override and no dirty-state materialization.

## Usage

The same host can invoke the standard development or reflection-triage Operation. Before actual
mutation, it requires a linked worktree created from the primary worktree's exact committed `HEAD`;
staged, unstaged, untracked, and ignored primary state is neither read nor copied. Before each direct
leaf Skill invocation, the runtime supplies one immutable launch specification containing the
chosen integration, prompt/prior results, normalized policy, native configuration, and digests. The
injectable process executor version-checks `codex exec` or restricted `claude -p`, scrubs ambient
secret variables, and returns a matching enforcement receipt; tests inject the runner and never call
a live model.

## Interfaces

### `contract.capabilities.permission-bounded-execution` — Compile and enforce an Operation launch

- **Consumer**: Paired Concorde Operations, workflow hosts, Codex/Claude executors, capability
  validators, installers, and Operation integration tests.
- **Direction**: Operation definition plus resolved workspace authority to one immutable normalized
  policy and integration-native launch configuration per composed leaf Skill.
- **Entry points**: Shared Operation runtime, each `operations/<name>/operation.py` policy
  declaration, and the injected executor contract.
- **Inputs**: Operation/stage/Skill identity; selected integration; project root; isolated-worktree
  Git identity and committed `HEAD` (or explicit primary override); Protocol 13 feature,
  architecture, ancestry-summary, related-feature-summary, attempt, reflection, and executable
  context; declared path roles; network posture; and optional outer-sandbox requirement.
- **Outputs**: Validated worktree boundary; canonical read/write/deny path sets; Codex named permission-profile/config selection;
  Claude `permissions` rules and strict sandbox settings; enforcement status; and an immutable launch
  specification attached to the Skill invocation.
- **Obligations**: Resolve real project-relative non-symlink paths; apply deny-before-allow semantics;
  keep writes a subset of the Skill's declared mutation authority; disable network unless explicitly
  required; scrub ambient credential access; reject primary mutation without the explicit override,
  never infer authority from primary dirty state, reject profile widening; and prevent launch unless one
  supported enforcement layer covers every declared path rule.
- **Failures**: Primary or non-Git mutation without explicit authorization, missing committed input,
  missing policy coverage, duplicate or mismatched Skill bindings, path escape,
  symlink/unsafe root, unavailable native sandbox without an approved outer equivalent, unsupported
  integration, configuration widening, or executor refusal stops the invocation and all downstream
  nodes.
- **Compatibility**: Codex uses a selected named permission profile when supported and otherwise an
  equivalently restrictive sandbox/outer boundary. Claude uses permission rules together with an
  enabled sandbox, `failIfUnavailable`, and no unsandboxed retry. Native syntax may evolve while the
  normalized policy and fail-closed semantics remain stable.
- **Example**: A `concorde-standard-dev-loop` leaf stage receives read access to its selected feature
  and owned module locators; it receives write access only to
  `.concorde/attempts/<stable-feature-id>/**` and `.concorde/reflections/**`. A reflection-triage
  implementer stage instead receives write access scoped to the same isolated worktree established
  before investigation and planning.
- **Implementing entities**: `entity.capabilities.worktree-gate`, `entity.capabilities.operation-runtime`,
  `entity.capabilities.operation-binding`, `entity.capabilities.operation-state`,
  `entity.capabilities.policy-compiler`, `entity.capabilities.process-launcher`,
  `entity.concorde.coding-agent`, and `module.concorde.understanding`.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.capabilities.operation-runtime` | Validates direct capability/binding coverage and supplies immutable leaf launch specifications. |
| `entity.capabilities.worktree-gate` | Reads only Git identity and exact `HEAD`, accepts linked worktrees, and rejects primary-worktree mutation unless the explicit override is present. |
| `entity.capabilities.operation-binding` | Carries exact stage, occurrence, capability, agent, and narrowing bindings; prevents undeclared, duplicated, widened, or order-mismatched execution. |
| `entity.capabilities.operation-state` | Carries request plus prior bounded capability results/receipts so a later stage can consume them without reopening unrelated sources. |
| `entity.capabilities.policy-compiler` | Freezes normalized policy and Codex/Claude/outer configurations, proving native effective-set parity and narrowing-only composition. |
| `entity.capabilities.process-launcher` | Performs injectable real CLI preflight/execution; starts only after digest/enforcement/version checks and returns a structured receipt. |
| `entity.concorde.coding-agent` | Enforces the selected Codex, Claude, or outer sandbox configuration while model transport stays outside project network authority. |
| `module.concorde.lifecycle` | Adopts the same per-leaf launch policy across the standard development loop's six-capability graph. |
| `module.concorde.reflections` | Adopts the same per-leaf launch policy, keeping investigators read-only and implementers scoped to isolated worktrees. |

## Related Features

- `feature.lifecycle.plan-attempt` runs `concorde-plan` as the first capability this contract launches
  under a per-leaf policy.
- `feature.lifecycle.standard-development-loop` adopts the same per-leaf policy contract across its
  six-capability graph.
- `feature.reflections.record-and-triage` adopts the same per-leaf policy contract, keeping
  investigators read-only and implementers scoped to isolated worktrees.
- `feature.understanding.bound-planning-context` supplies the concrete Protocol 13 and
  required-interface paths this contract compiles into policy.
- `feature.capabilities.provide-capability-surfaces` supplies the leaf effects and Operation topology
  this contract narrows into per-leaf policy.

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

### User Story 2 — Preserve Codex and Claude parity (Priority: P2)

A maintainer receives equivalent effective file boundaries whether an Operation launches Codex or
Claude Code.

**Why this priority**: Integration-specific syntax must not change Concorde's authority model.

**Independent Test**: Compile one normalized policy to both integrations and compare canonical
effective read/write/deny sets before validating their native configuration shapes.

**Acceptance Scenario**:

1. **Given** the same normalized policy, **When** Codex and Claude configurations are rendered,
   **Then** both deny undeclared paths, allow the same declared paths, disable ambient network by
   default, and fail rather than falling back to an unconfined process.

## Requirements

### Functional Requirements

- **FR-001**: Every manifested Operation MUST declare one permission binding for every composed leaf
  Skill occurrence, and deterministic validation MUST reject missing, duplicate, unknown, or
  stage/order-mismatched bindings.
- **FR-002**: The shared Operation runtime MUST reject graph construction without a leaf launch
  factory and MUST give the executor a non-null immutable launch specification containing the
  selected integration, normalized read/write/deny paths, network posture, native configuration,
  Skill body, and prior stage results before that Skill executes.
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
- **FR-008**: Standard-development and reflection-triage Operations MUST adopt the same per-Skill
  policy contract without weakening their current order, state, worktree isolation, or downstream
  failure behavior.
- **FR-009**: Installation and checkout synchronization MUST project the Operation/leaf inventory and
  its Codex/Claude configuration semantics with no cross-kind name collision or legacy alias.
- **FR-010**: An Operation MUST be able to compose another manifested Operation by its public
  capability identity without loading or flattening the nested Operation's internal stages/Skills;
  resolution MUST reject cycles and a missing explicit enforcing dispatcher, preserve nested
  state/failure/policy boundaries, and make the standard-development and reflection-routing graphs
  reference `concorde-plan` rather than its private leaves wherever they invoke planning.
- **FR-011**: Every actual mutating Operation and workspace/Tool adapter MUST reject the primary Git
  worktree by default, accept a linked worktree at an exact commit, and expose
  `--allow-primary-worktree` only as the machine assertion of explicit maintainer authorization.
  The gate MUST inspect only Git identity/commit metadata and MUST NOT read, stash, copy, reset,
  clean, or otherwise import or alter primary dirty contents.

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
- **SC-002**: Codex and Claude renderers produce the same canonical effective path sets for every
  shipped policy, with network disabled and sandbox unavailability tested as a hard failure.
- **SC-003**: Full unit, contract, integration, installation/projection, deterministic Profile 7, and
  documentation checks pass with no undeclared durable mutation or compatibility capability.
- **SC-004**: Nested-operation tests prove the outer graph sees only public `concorde-plan`, a trusted
  dispatcher runs inner context/author with independent non-null launches, missing dispatcher/factory
  invokes no executor, and a failure at either level prevents the correct downstream nodes.
- **SC-005**: Executable tests reject the primary worktree, accept a linked worktree created at the
  same committed `HEAD`, and prove tracked/untracked primary changes are absent from that target.

## Edge Cases

- An Operation with no permission policy, a missing stage/Skill binding, an unsafe or unresolved
  path, or a write path outside the leaf Skill's authority is invalid and does not launch an agent.
- If Codex permission profiles are unavailable or rejected, the host may use an equivalently narrow
  Codex sandbox or outer OS/container boundary; otherwise execution stops.
- Claude execution stops when its sandbox cannot initialize, and it may not retry a denied command
  outside the sandbox.
- User, project, or managed configuration may narrow an Operation policy, but a less restrictive
  layer may not widen it. A conflict stops the affected invocation.
- A source locator crosses into another module or points through a symlink; policy resolution rejects
  it instead of treating the broad executable root as authority.
- A user-level Codex or Claude setting is stricter than the Operation policy; the stricter effective
  boundary wins and a required denied action fails explicitly.
- A host supports LangGraph but neither a compatible native agent sandbox nor an approved outer
  isolation layer; graph construction may succeed, but agent launch fails before the first Skill.
- Two Skills share one LangGraph stage but require different write sets; each receives its own agent
  launch policy and neither receives the other Skill's rights.
- A primary worktree is dirty because another programmer is active; the gate accepts a linked
  worktree at committed `HEAD` and leaves every primary byte untouched. If the required input exists
  only in dirty state, the agent reports it missing.
