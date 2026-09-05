---
id: feature.concorde.workflow
kind: feature
module: module.concorde
related_features:
  - id: feature.understanding.initialize-architecture
    relation: composes
  - id: feature.understanding.retrieve-bounded-context
    relation: composes
  - id: feature.understanding.answer-workflow-questions
    relation: composes
  - id: feature.understanding.resolve-feature-workspace
    relation: composes
  - id: feature.understanding.validate-architecture
    relation: composes
  - id: feature.lifecycle.specify-behavior
    relation: composes
  - id: feature.lifecycle.plan-attempt
    relation: composes
  - id: feature.lifecycle.execute-and-reconcile
    relation: composes
  - id: feature.lifecycle.deliver-attempt
    relation: composes
  - id: feature.lifecycle.fast-loop
    relation: composes
  - id: feature.lifecycle.standard-development-loop
    relation: composes
  - id: feature.reflections.record-and-triage
    relation: composes
  - id: feature.capabilities.permission-bounded-execution
    relation: depends_on
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.distribution.install-concorde
    relation: depends_on
  - id: feature.concorde.define-project-ontology
    relation: depends_on
  - id: feature.concorde.evolve-protocol
    relation: refined_by
interfaces:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.agent-platform
---

# Feature Design: Concorde Workflow

## Outcome and Scope

A maintainer can direct one normal feature from its complete direct file through permission-bounded
planning, dependency-ordered implementation/evidence, deterministic validation, and cleanup-only
delivery using installed skills as the sole conversational surface. Every mutating agent session
starts in one linked worktree from the primary worktree's exact committed `HEAD`; unrelated primary
dirty state is excluded. Concorde's own normative Protocol evolution is explicitly excluded and
routed to its isolated bootstrap feature.

## Usage

1. Install Concorde with the preview/apply flow in `feature.distribution.install-concorde`, then
   initialize the root module with `concorde-init` when the project has no Profile 7 architecture.
   When the project grows child modules, partition them by capability, use case, or axis of change,
   never by artifact type (constitution A.VI).
2. Before any agent plans, persists selection, creates an attempt/checklist/reflection, or writes,
   resolve the primary worktree's committed `HEAD` and create a unique branch/linked worktree there.
   Continue the complete request in that worktree. Never import staged, unstaged, untracked, or
   ignored primary-worktree bytes; only an explicit instruction to modify the primary worktree
   enables the override.
3. Select one direct `features/<NNN-name>.md` and invoke `concorde-specify`; use
   `concorde-clarify` for material ambiguity and `concorde-checklist` for reviewer-owned quality
   checks. A new file is resolved again after stable-ID front matter exists.
4. For a normal change, invoke `concorde-plan`, `concorde-tasks`, and `concorde-implement`; use
   `concorde-analyze` for a read-only audit and `concorde-converge` only when verified work remains.
   `concorde-standard-dev-loop` composes specify → plan → tasks/implement → validate/deliver when the
   complete loop is desired.
5. Run `concorde-validate`, then invoke `concorde-deliver` only after every task/checklist and its
   canonical evidence block passes. Delivery removes the attempt, not the specification.
6. Use `concorde-fast-loop` instead only when preflight proves the change is already specified,
   bounded, non-structural, and has no active attempt.
7. In the Concorde repository, classify a change to the normative semantics of Concorde Protocol
   before invoking any lifecycle capability. Route it to `feature.concorde.evolve-protocol`, which
   uses no selection, attempt, checklist, fast loop, standard loop, or delivery.

Planning, task, checklist, research, quickstart, and validation files live only under
`.concorde/attempts/<stable-feature-id>/`; they are workflow memory, not another documentation set.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.understanding` | Resolves Protocol 13 workspaces, bounded context, planning context, and deterministic validation for every phase. |
| `module.concorde.lifecycle` | Owns the specify, plan, tasks, implement, deliver, and fast-loop Skills and the paired plan and standard-loop Operations. |
| `module.concorde.reflections` | Receives one problem document per phase-level problem and triages it back through lifecycle capabilities. |
| `module.concorde.capabilities` | Declares, permission-bounds, launches, and projects every Skill and Operation the workflow invokes. |
| `entity.concorde.coding-agent` | Authors design/plan/tasks/code/tests and follows evidence/authority rules. |
| `entity.concorde.control-state` | Holds the selected feature, its stable-ID attempt, and the reflection collection during the workflow. |
| `entity.concorde.protocol` | Governs this normal selected-feature lifecycle; Feature Workspace Protocol 13 is one component. |
| `entity.concorde.protocol-cutover` | Receives every normative Protocol semantic change before lifecycle selection and evolves it outside this workflow. |
| `entity.concorde.git` | Supplies the exact committed base, unique linked worktree, reviewable branch, and later integration boundary for every mutating agent session. |

## Interfaces

### `contract.concorde.workflow` — Skill-guided feature lifecycle

- **Consumer**: Maintainer and supported coding-agent integration.
- **Direction**: Maintainer intent to leaf or multi-Skill result, with structured deterministic Tool crossings.
- **Entry points**: Installed public lifecycle leaves plus paired `concorde-plan`, standard-loop, and
  reflection-triage Operations; internal planner leaves are not entry points.
- **Inputs**: Exact committed primary `HEAD`, isolated-worktree identity (or an explicit
  primary-mutation override), selected `feature_path`, providing module architecture, related
  feature paths, code/tests, constitution, `.concorde/reflections/`, and optional corresponding
  stable-ID control attempt. Primary staged/unstaged/untracked/ignored bytes are not inputs.
- **Outputs**: Revised durable intent/architecture when authorized, temporal planning/evidence, reconciled code/tests/projections, findings, and delivery cleanup result.
- **Obligations**: Keep each fact in one authority, resolve Protocol 13/concrete paths first, trace
  every task, validate deterministically, disclose evidence limits, keep nested Operations opaque,
  never launch a mutating phase before the committed-base worktree gate, and never launch a leaf
  without an exact narrowing enforced policy/receipt.
- **Failures**: Primary-worktree mutation without explicit authorization, missing committed input,
  non-Git mutation without an explicit current-directory override, invalid placement/authority,
  incomplete checklist/task, failed check, stale/unsafe
  delivery, ambiguous impact, or a normative Concorde Protocol change stops the affected phase
  without implied authorization; the latter routes to `interface.concorde.protocol-evolution` before
  any workspace mutation.
- **Compatibility**: Profile 7 features are direct Markdown files; Feature Workspace Protocol 13
  rejects specification-local control state/redundant feature fields, while Delivery 9 retains
  cleanup-only semantics. Constitution 8.1.0 makes committed-base worktree isolation the mutation
  default and retains normative Concorde Protocol evolution outside this normal lifecycle.
- **Implementing entities**: `module.concorde.understanding`, `module.concorde.lifecycle`,
  `module.concorde.reflections`, `module.concorde.capabilities`, and `entity.concorde.coding-agent`.
- **Example**: A maintainer specifies `features/001-change.md` with ID `feature.example.change`, runs plan/tasks/implement in `.concorde/attempts/feature.example.change/`, verifies all evidence, then invokes delivery once to remove that attempt.

### `contract.concorde.agent-platform` — Supported coding-agent execution surface

- **Provider**: `external:coding-agent-platform` (supported Codex or Claude integration).
- **Consumer**: Maintainers and Concorde-rendered leaf and Operation skills.
- **Direction**: Installed Skill files and user invocation to an agent turn that follows the declared
  leaf phase or paired LangGraph workflow.
- **Entry points**: `.agents/skills/**` and `.codex/agents/**`, or `.claude/skills/**` and `.claude/agents/**`.
- **Inputs**: Regular rendered Markdown/TOML, project root, user arguments, concrete normalized path
  policy, committed-base linked-worktree identity for mutation (or explicit primary override),
  integration-native Codex/Claude or approved outer configuration, and prior results.
- **Outputs**: Conversational phase/Operation result plus only authorized file/Tool effects and, for
  Operation leaves, a digest-bound enforcement receipt.
- **Obligations**: Load project-local metadata/body, invoke paired Python when declared, enforce
  default-deny paths/network/credentials outside LangGraph, prohibit unsandboxed retry, surface
  Tool/graph/policy failures, reject implicit primary-worktree mutation, and keep `concorde-*`
  identity consistent.
- **Failures**: Missing/unsupported worktree authorization or integration assets, invalid capability
  metadata or pairing,
  unavailable Tools/dependencies, or denied permissions stop execution without hidden fallback behavior.
- **Compatibility**: Concorde 3.0.0 Package Manifest 2 packages 17 leaves/three pairs and exposes the
  same 15 public leaves plus three Operations in Codex and Claude.
- **Implementing entities**: `entity.concorde.coding-agent`, `module.concorde.capabilities`, and
  `module.concorde.reflections`.
- **Example**: Codex loads `.agents/skills/concorde-plan/SKILL.md`, whose Operation runs bounded
  context → author with two distinct permission profiles.

## Related Features

- `feature.understanding.initialize-architecture`, `feature.understanding.retrieve-bounded-context`,
  `feature.understanding.answer-workflow-questions`, `feature.understanding.resolve-feature-workspace`,
  and `feature.understanding.validate-architecture` are composed as the orientation and gate phases
  of this workflow.
- `feature.lifecycle.specify-behavior`, `feature.lifecycle.plan-attempt`,
  `feature.lifecycle.execute-and-reconcile`, `feature.lifecycle.deliver-attempt`, and
  `feature.lifecycle.fast-loop` are the change phases this workflow sequences;
  `feature.lifecycle.standard-development-loop` composes them as one Operation.
- `feature.reflections.record-and-triage` is depended on for recording every phase-level problem.
- `feature.capabilities.permission-bounded-execution` and
  `feature.capabilities.provide-capability-surfaces` are depended on so that every invoked Skill or
  Operation runs under one enforced policy with identical Codex and Claude semantics.
- `feature.distribution.install-concorde` precedes the workflow in a fresh project.
- `feature.concorde.evolve-protocol` refines this workflow with the Concorde-repository-only,
  attempt-free cutover required for every normative Concorde Protocol semantic change.

## Usage Scenarios

1. Before the first mutation, create or enter one unique linked worktree at the primary worktree's
   committed `HEAD`; ignore and preserve all primary dirty state.
2. Establish or revise one direct module feature file and its interface/architecture references.
3. Create its corresponding stable-ID control attempt whose plan/tasks trace every affected architecture, feature, code, test, and projection.
4. Execute with evidence, validate the reconciled project, then deliver by removing only the attempt.
5. Use the fast loop only when deterministic preflight proves the change is already specified, bounded, and non-structural.
6. Reject normative Concorde Protocol evolution before selection and route it to one isolated
   worktree cutover without lifecycle state.

## Requirements

- **FR-001**: Every path-sensitive direct leaf occurrence MUST resolve one Protocol 13 feature
  workspace into concrete safe roles and receive one enforceable narrowing policy; prompts and graph
  topology alone MUST NOT claim filesystem enforcement.
- **FR-002**: Specification/architecture/code/test/projection facts MUST remain in their single authority and be reconciled together when affected.
- **FR-003**: Every executable task MUST have a requirement trace, exact path, dependency state, passed check, artifact, and stated evidence limitation before completion.
- **FR-004**: Validation/read-only failures MUST be non-mutating; reviewed initialization, eligible fast loop, and cleanup delivery MUST be atomic within their explicit authority.
- **FR-005**: Delivery MUST remove one complete current `.concorde/attempts/<stable-feature-id>/`, retain the direct feature and per-file reflection collection byte-identically, and MUST NOT author durable implementation prose or architectural intent.
- **FR-006**: Module architecture and direct feature files MUST also serve as the maintained project
  documentation; lifecycle guidance MUST update those owners rather than create a parallel `docs/`
  authority.
- **FR-007**: Every canonical and projected lifecycle entry point MUST reject a normative Concorde
  Protocol semantic change before workspace mutation and direct the Concorde maintainer to
  `feature.concorde.evolve-protocol`; implementation fixes that restore already specified semantics
  remain eligible for this workflow.
- **FR-008**: Every agent-authored mutation MUST begin in a unique linked worktree created from the
  primary worktree's exact committed `HEAD`, before planning, selection persistence, or attempt/
  checklist/reflection creation, unless the maintainer explicitly authorizes primary-worktree
  mutation. Primary staged, unstaged, untracked, and ignored bytes MUST remain excluded and
  untouched; missing committed input MUST stop rather than trigger stash/copy recovery.

## Edge Cases

- Related features span several immediate modules but the feature remains specified at the level where those modules are visible.
- A passing structural check has no behavioral evidence and therefore cannot authorize a completion claim.
- A stale proposal or unexpected protected-source change stops mutation while preserving the attempt.
- A Concorde maintainer asks a normal lifecycle leaf or Operation to change Protocol semantics; it
  stops before selection/attempt mutation and names the isolated protocol-evolution route.
- The primary worktree is dirty because another programmer is active; the agent branches from its
  committed `HEAD`, leaves every dirty byte untouched, and performs the complete workflow in the
  linked worktree.
- A required feature or attempt exists only as an untracked primary-worktree path; the agent reports
  it missing and does not import it without an explicit primary-state handoff.
