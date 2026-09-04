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
  only the maintained/temporal/executable sources that prompt authorizes.
- **Outputs**: Conversational result, explicit Tool results, evidence, and only phase-authorized file
  changes.
- **Obligations**: Preserve complete prompt/phase boundaries; keep public leaves independently
  invocable and internal leaves Operation-only; declare exact effects when composed; invoke Tools
  explicitly; surface failures/evidence limits; contain no multi-Skill graph.
- **Failures**: Workspace/tool failure, missing authority, invalid project state, denied permission,
  or unmet phase gate stops that Skill without fallback to another source.
- **Compatibility**: Protocol 13 and Delivery Proposal 9 use Tool terminology. Stable public names are
  `concorde-*`; retired dotted prompt identities are not aliases.
- **Implementing entities**: `entity.capabilities.skill-prompt`, `entity.concorde.coding-agent`,
  `module.concorde.understanding`, `module.concorde.lifecycle`, and `module.concorde.reflections`.
- **Example**: The plan Operation launches internal read-only context then temporal author leaves
  with distinct effect-derived policies.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.capabilities.skill-sources` | Owns one canonical directory per leaf Skill. |
| `entity.capabilities.operation-sources` | Owns one canonical Python/Markdown pair per Operation. |
| `entity.capabilities.skill-prompt` | Supplies a complete public/internal leaf contract with exposure/effects. |
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

## Success Criteria

- **SC-001**: Both integrations expose exactly 15 public leaves plus three Operation skills, package
  two internal planner leaves, and have no cross-kind/role collision.
- **SC-002**: Source/projection parity and installed workflow tests prove that leaf Skill semantics and
  Tool entry points are equivalent across supported integrations and that Operation prompts select
  the intended managed venv without activation.

## Edge Cases

- A Skill directory name and declared `name` differ.
- A leaf Skill declares an Operation token or contains multi-Skill graph topology.
- A paired Operation uses the same public name as a leaf Skill.
- A Skill declares a Tool script that does not resolve inside the installed framework.
- An Operation projection resolves its pair but bypasses or cannot resolve the colocated bootstrap.
