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
with a committed-base isolated-worktree preflight, a validated least-privilege task policy, an
attested client-runtime bootstrap, and typed semantic completion that admits only successful
capabilities to downstream state.

**In scope**:

- One integration-neutral, fail-closed permission policy on every Operation and every composed leaf
  Skill invocation.
- Deterministic compilation of that policy into Codex permission-profile configuration and Claude
  permission rules plus sandbox settings.
- Concrete read/write/deny paths resolved from Workspace Protocol 13 and stable feature/interface
  relationships before an agent starts.
- A separately attested, read-only integration runtime bootstrap that lets the selected native
  client execute itself without making host paths part of task authority.
- One canonical host workspace receipt per leaf and Capability Completion Envelope 2 across Codex
  JSONL/output-schema and Claude JSON-schema output.
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
leaf Skill invocation, the runtime supplies one immutable launch request containing the chosen
integration, canonical prompt, typed task/configuration, invocation identity, normalized task policy,
native configuration, canonical Protocol
13 receipt, and digests. The process executor resolves and attests the exact selected Codex native
binary when native enforcement needs it, finalizes a new immutable launch, version-checks
`codex exec` or restricted `claude -p`, scrubs ambient secrets, and requires Capability Completion
Envelope 2. A zero process exit is transport evidence only. Tests inject client processes and
runtime attestations; live model calls remain optional acceptance evidence.

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
  context; canonical workspace receipt; declared path roles; selected client executable; network
  posture; and optional outer-sandbox requirement.
- **Outputs**: Validated worktree boundary; canonical task read/write/deny sets; attested read-only
  runtime-bootstrap files separate from those sets; Codex named profile or Claude strict sandbox;
  finalized launch/config/bootstrap digests; Capability Completion Envelope 2; enforcement receipt;
  and only validated successful capability state.
- **Obligations**: Resolve real project-relative non-symlink paths; apply deny-before-allow semantics;
  keep writes a subset of the Skill's declared mutation authority; disable network unless explicitly
  required; scrub ambient credential access; reject primary mutation without the explicit override,
  never infer authority from primary dirty state; attest only the selected real executable outside
  project authority, reject unsafe owner/mode/path substitution and stale bootstrap identity; keep
  runtime bootstrap out of task-policy parity; bind workspace/bootstrap/completion identity into the
  finalized launch and receipt; require schema-constrained semantic completion; and prevent launch
  unless one supported enforcement layer covers every declared path rule.
- **Failures**: Primary or non-Git mutation without explicit authorization, missing committed input,
  missing policy coverage, duplicate or mismatched Skill bindings, path escape,
  symlink/unsafe root, unresolved or mutable runtime bootstrap, unavailable native sandbox without an
  approved outer equivalent, unsupported integration, configuration widening, client lifecycle
  failure, nonzero transport exit, malformed/stale/failed completion, missing gate evidence, or
  executor refusal stops the invocation and all downstream nodes.
- **Compatibility**: Codex uses a selected named permission profile when supported and otherwise an
  equivalently restrictive sandbox/outer boundary. A native Codex launch may add only its attested
  real executable as runtime-bootstrap read authority; this is digest-bound integration runtime, not
  project/task context. Claude uses permission rules with `failIfUnavailable` and no unsandboxed
  retry. Codex JSONL/output-schema and Claude JSON-schema output both realize Capability Completion
  Envelope 2. Native syntax may evolve while normalized task authority and fail-closed semantics stay
  stable.
- **Example**: A `concorde-standard-dev-loop` leaf stage receives read access to its selected feature
  and owned module locators; it receives write access only to
  `.concorde/attempts/<stable-feature-id>/**` and `.concorde/reflections/**`. A reflection-triage
  implementer stage instead receives write access scoped to the same isolated worktree. The host adds
  one SHA-256-attested Codex binary read to bootstrap the sandbox, then accepts the leaf only after a
  success envelope reports passed gates and no limitations.
- **Implementing entities**: `entity.capabilities.worktree-gate`, `entity.capabilities.operation-runtime`,
  `entity.capabilities.operation-binding`, `entity.capabilities.operation-state`,
  `entity.capabilities.policy-compiler`, `entity.capabilities.runtime-bootstrap`,
  `entity.capabilities.completion-envelope`, `entity.capabilities.process-launcher`,
  `entity.concorde.coding-agent`, and `module.concorde.understanding`.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.capabilities.operation-runtime` | Validates direct capability/binding coverage, supplies the canonical workspace receipt, and admits only successfully completed leaves to state. |
| `entity.capabilities.worktree-gate` | Reads only Git identity and exact `HEAD`, accepts linked worktrees, and rejects primary-worktree mutation unless the explicit override is present. |
| `entity.capabilities.operation-binding` | Carries exact stage, occurrence, capability, agent, and narrowing bindings; prevents undeclared, duplicated, widened, or order-mismatched execution. |
| `entity.capabilities.operation-state` | Carries request plus validated successful capability/completion/receipt triples so later stages never consume a semantic failure. |
| `entity.capabilities.policy-compiler` | Freezes normalized task policy and Codex/Claude/outer configurations, keeping integration runtime bootstrap out of task parity. |
| `entity.capabilities.runtime-bootstrap` | Canonicalizes and attests the selected Codex executable, rejects project-local/mutable/substituted paths, and binds its exact read grant to the finalized launch. |
| `entity.capabilities.completion-envelope` | Versioned semantic success/failure, output, limitations, gates, and launch/workspace/bootstrap identity shared by Codex and Claude. |
| `entity.capabilities.process-launcher` | Finalizes runtime bootstrap, invokes native structured output, validates completion, and returns a matching receipt or raises before state admission. |
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

### User Story 3 — Distinguish transport from phase completion (Priority: P1)

A workflow host receives a zero-exit client process only as transport evidence and advances the
Operation after a separately validated semantic completion proves every reported mandatory gate.

**Why this priority**: A client can exit zero after truthfully reporting that no workspace gate or
source inspection ran; treating that prose as success violates every downstream safety guarantee.

**Independent Test**: Inject Codex and Claude results for valid success, explicit failure at exit
zero, malformed/stale completion, lifecycle error, and a recovered command failure; require only the
first and recovered cases to enter Operation state.

**Acceptance Scenario**:

1. **Given** a client exits zero but returns `status: failed` with a failed workspace gate, **When**
   the host validates Capability Completion Envelope 2, **Then** it emits a failed receipt, raises,
   and invokes no downstream capability.

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
- **FR-012**: Before native Codex execution, the host MUST resolve the selected command to one real
  executable outside project authority, require a trusted owner plus no group/world write, hash its
  bytes and metadata, add only that exact path as read-only runtime bootstrap, and bind the
  attestation to finalized configuration, launch, and receipt digests. A stale, substituted, unsafe,
  unresolved, or project-local executable MUST fail before model launch.
- **FR-013**: Runtime-bootstrap paths MUST remain a separately reported integration dependency and
  MUST NOT enter normalized task read/write sets or Codex/Claude task-authority parity. Outer
  enforcement and integrations that bootstrap themselves MUST add no Codex runtime grant.
- **FR-014**: The host MUST give every Operation-composed leaf a canonical, digest-bound Protocol 13
  workspace receipt. That receipt satisfies the leaf's workspace gate; the leaf MUST NOT rerun the
  broader resolver from its narrower policy. The exact script declared by that leaf MUST remain
  readable as framework authority for any later phase Tool invocation.
- **FR-015**: Every real agent process MUST return Capability Completion Envelope 2 with exact
  operation/stage/occurrence/capability, finalized launch, workspace, and runtime-bootstrap identity;
  semantic `success | failed`; audit output; limitations; non-empty unique gate evidence; and
  `domain_output` (the contracted investigation TypedValue on triage-analysis success, otherwise
  null). The low-level injected unstructured host API retains Envelope 1; JSON Operations never
  downgrade. A domain value does not replace native completion or enforcement evidence.
- **FR-016**: Process exit zero MUST be necessary but insufficient for success. Nonzero exit, native
  lifecycle error, malformed/missing/stale/contradictory envelope, explicit failure, failed gate, or
  success with limitations MUST create a failed receipt and raise before `CapabilityResult` state.
  A recovered command failure MAY complete successfully when the final envelope is valid.
- **FR-017**: Codex MUST use JSONL lifecycle evidence plus schema-constrained final output; Claude
  MUST use equivalent JSON-schema output. Free-form phrase matching and blanket command-exit
  heuristics MUST NOT determine semantic completion.

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
- The selected client binary is already trusted to host the agent process; attesting and admitting
  that exact immutable executable to bootstrap its own native sandbox does not authorize its package
  directory, siblings, project data, or task writes.
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
- **SC-006**: A real standalone Codex 0.153.2 launch under the generated read-only profile executes an
  authorized tool without a runtime `execvp` failure; its receipt carries distinct requested/final
  launch and runtime-bootstrap digests.
- **SC-007**: Injected tests cover valid success, explicit zero-exit failure, nonzero transport
  failure, malformed/stale completion, missing/failed gates, native lifecycle error, and recovered
  command failure for both result parsing and downstream stopping.

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
- A PATH entry is a wrapper, symlink, project file, untrusted-owner file, or group/world-writable
  executable; bootstrap attestation rejects it or resolves only its safe real external target.
- A direct Skill invocation has no host receipt and runs Protocol 13 itself; an Operation leaf uses
  the supplied receipt and does not reopen global resolver inputs.
- A command fails during diagnosis and the Skill safely recovers; its final success envelope may be
  admitted. A mandatory gate fails even though the client exits zero; its failed envelope stops.
