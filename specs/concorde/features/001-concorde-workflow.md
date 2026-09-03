---
id: feature.concorde.workflow
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow.initialize-architecture
  - feature.concorde.workflow.retrieve-bounded-context
  - feature.concorde.workflow.answer-workflow-questions
  - feature.concorde.workflow.manage-feature-workspaces
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.workflow.execute-and-reconcile
  - feature.concorde.workflow.validate-architecture
  - feature.concorde.workflow.accept-milestone
  - feature.concorde.workflow.fast-loop
  - feature.operations.standard-development-loop
  - feature.operations.permission-bounded-planning
  - feature.skills.project-workflow
interfaces:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.agent-platform
evidence_status: partial
---

# Feature Design: Concorde Workflow

## Outcome and Scope

A maintainer can direct one feature from its complete direct file through permission-bounded planning, dependency-
ordered implementation/evidence, deterministic validation, and cleanup-only delivery using installed
skills as the sole conversational surface.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.skills` | Presents public leaves and package-only internal effect-declared leaves. |
| `module.concorde.operations` | Composes acyclic Skill/Operation graphs and enforces one native/outer policy per leaf. |
| `module.concorde.runtime` | Resolves workspaces and performs deterministic init/context/validate/deliver Tools. |
| `module.concorde.workspace` | Defines durable specification paths plus stable-ID attempts and reflections in project control state. |
| `entity.concorde.coding-agent` | Authors design/plan/tasks/code/tests and follows evidence/authority rules. |

## Interfaces

### `contract.concorde.workflow` — Skill-guided feature lifecycle

- **Consumer**: Maintainer and supported coding-agent integration.
- **Direction**: Maintainer intent to leaf or multi-Skill result, with structured deterministic Tool crossings.
- **Entry points**: Installed public lifecycle leaves plus paired `concorde-plan`, standard-loop, and
  reflection-triage Operations; internal planner leaves are not entry points.
- **Inputs**: Selected `feature_path`, providing module architecture, related feature paths, code/tests, constitution, `.concorde/reflections/`, and optional corresponding stable-ID control attempt.
- **Outputs**: Revised durable intent/architecture when authorized, temporal planning/evidence, reconciled code/tests/projections, findings, and delivery cleanup result.
- **Obligations**: Keep each fact in one authority, resolve Protocol 13/concrete paths first, trace
  every task, validate deterministically, disclose evidence limits, keep nested Operations opaque,
  and never launch a leaf without an exact narrowing enforced policy/receipt.
- **Failures**: Invalid placement/authority, incomplete checklist/task, failed check, stale/unsafe delivery, or ambiguous impact stops the affected phase without implied authorization.
- **Compatibility**: Profile 7 features are direct Markdown files; Protocol 13 rejects specification-local control state/redundant feature fields, while Delivery 9 retains cleanup-only semantics.
- **Implementing entities**: `module.concorde.skills`, `module.concorde.operations`,
  `module.concorde.runtime`, `module.concorde.workspace`, and `entity.concorde.coding-agent`.
- **Example**: A maintainer specifies `features/001-change.md` with ID `feature.example.change`, runs plan/tasks/implement in `.concorde/attempts/feature.example.change/`, verifies all evidence, then invokes delivery once to remove that attempt.

### `contract.concorde.agent-platform` — Supported coding-agent execution surface

- **Provider**: `external:coding-agent-platform` (supported Codex or Claude integration).
- **Consumer**: Maintainers and Concorde-rendered leaf and Operation skills.
- **Direction**: Installed Skill files and user invocation to an agent turn that follows the declared
  leaf phase or paired LangGraph workflow.
- **Entry points**: `.agents/skills/**` and `.codex/agents/**`, or `.claude/skills/**` and `.claude/agents/**`.
- **Inputs**: Regular rendered Markdown/TOML, project root, user arguments, concrete normalized path
  policy, integration-native Codex/Claude or approved outer configuration, and prior results.
- **Outputs**: Conversational phase/Operation result plus only authorized file/Tool effects and, for
  Operation leaves, a digest-bound enforcement receipt.
- **Obligations**: Load project-local metadata/body, invoke paired Python when declared, enforce
  default-deny paths/network/credentials outside LangGraph, prohibit unsandboxed retry, surface
  Tool/graph/policy failures, and keep `concorde-*` identity consistent.
- **Failures**: Missing/unsupported integration assets, invalid capability metadata or pairing,
  unavailable Tools/dependencies, or denied permissions stop execution without hidden fallback behavior.
- **Compatibility**: Concorde 2.1.0 Package Manifest 2 packages 17 leaves/three pairs and exposes the
  same 15 public leaves plus three Operations in Codex and Claude.
- **Implementing entities**: `entity.concorde.coding-agent`, `entity.concorde.skills`,
  `entity.concorde.operations`, and `entity.concorde.agent-assets`.
- **Example**: Codex loads `.agents/skills/concorde-plan/SKILL.md`, whose Operation runs bounded
  context → author with two distinct permission profiles.

## Usage Scenarios

1. Establish or revise one direct module feature file and its interface/architecture references.
2. Create its corresponding stable-ID control attempt whose plan/tasks trace every affected architecture, feature, code, test, and projection.
3. Execute with evidence, validate the reconciled project, then deliver by removing only the attempt.
4. Use the fast loop only when deterministic preflight proves the change is already specified, bounded, and non-structural.

## Requirements

- **FR-001**: Every path-sensitive direct leaf occurrence MUST resolve one Protocol 13 feature
  workspace into concrete safe roles and receive one enforceable narrowing policy; prompts and graph
  topology alone MUST NOT claim filesystem enforcement.
- **FR-002**: Specification/architecture/code/test/projection facts MUST remain in their single authority and be reconciled together when affected.
- **FR-003**: Every executable task MUST have a requirement trace, exact path, dependency state, passed check, artifact, and stated evidence limitation before completion.
- **FR-004**: Validation/read-only failures MUST be non-mutating; reviewed initialization, eligible fast loop, and cleanup delivery MUST be atomic within their explicit authority.
- **FR-005**: Delivery MUST remove one complete current `.concorde/attempts/<stable-feature-id>/`, retain the direct feature and per-file reflection collection byte-identically, and MUST NOT author durable implementation prose or architectural intent.

## Edge Cases

- Related features span several immediate modules but the feature remains specified at the level where those modules are visible.
- A passing structural check has no behavioral evidence and therefore cannot authorize a completion claim.
- A stale proposal or unexpected protected-source change stops mutation while preserving the attempt.
