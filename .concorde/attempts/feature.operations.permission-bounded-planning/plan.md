# Implementation Plan: Permission-Bounded Planning Operations

**Branch**: `main (implementation in isolated worktree)` | **Date**: 2026-09-02 | **Feature**:
`specs/concorde/modules/operations/features/002-permission-bounded-planning.md`

**Input**: Selected feature, Operations architecture, current runtime/capability/workspace code and
tests, Constitution, bounded related-feature summaries, official Codex/Claude permission documents,
and the project reflection queue.

## Summary

Replace the stage-opaque Operation executor with a capability-aware, per-leaf launch contract;
compile exact workspace roles into Codex permission profiles or Claude rules plus strict sandboxing;
add an injectable real CLI executor and enforcement receipts; promote the public `concorde-plan`
name to a nested Operation over two internal leaves; preserve provider-module opacity by admitting
only required-interface owner feature specs; and migrate the standard-development/reflection graphs,
installer, projections, documentation, architecture, and tests together.

## Technical Context

**Language/Version**: Python 3.11+; Markdown/YAML front matter; JSON/TOML render targets

**Primary Dependencies**: standard library, LangGraph `>=1.2,<2` (lazy), Codex CLI permission
profiles (supported client), Claude Code permission rules/Bash sandbox, Archify 2.16

**Storage/State**: Package Manifest 2; canonical Skill/Operation pairs; Protocol 13 selection/attempt;
ephemeral launch specifications and subprocess output; no persistent credential/config copy

**Testing**: `unittest`, deterministic Concorde validation, installer/release/projection acceptance,
Archify showcase/delivery/freshness, docsite checks

**Target Platform**: macOS/Linux/WSL/native Windows where Codex profiles are supported; Claude native
sandbox on macOS/Linux/WSL with outer sandbox required elsewhere

**Project Type**: standalone Python package/CLI and generated Codex/Claude agent integrations

**Performance Goals**: policy/context compilation deterministic and sub-second on repository fixtures;
no live model/network dependency in tests

**Constraints**: deny by default; no ambient credential/network authority; no `$CODEX_HOME` mutation;
no nested Operation cycles; internal leaves not user-projected; dependency modules visible only through
required-interface owner feature specs; existing user work preserved

**Scale/Scope**: 17 packaged leaves (15 public, 2 internal), three Operations, 18 projected public
skills, shared runtime/workspace/validation, both integrations, package/install/release/docs/specs

## Constitution Check

| Principle | Plan evidence | Status |
|---|---|---|
| A.I module stopping points | Required-interface feature bodies cross module boundaries; provider architecture/source remain denied. | Pass |
| A.II implementation authority | Selected module owned locators and tests remain implementation evidence; dependency code is not copied into context. | Pass |
| A.III typed hierarchy | Operation nesting is typed, directional, acyclic, and opaque; module/entity diagrams change with text. | Pass |
| A.IV feature promises | Required interface ownership deterministically selects dependency feature specs. | Pass |
| A.V deterministic/risk-proportional gates | Policy/path/topology/render validation is offline and fails before agent launch. | Pass |
| B.I usable workflow | The public plan capability becomes an executable permission-bounded Operation. | Pass |
| B.II self-application | This attempt uses Protocol 13, isolated implementation, evidence, and cleanup-only delivery. | Pass |

The Constitution currently says Operations compose only leaf Skills and every leaf is projected. The
implementation must amend it to 7.1.0 before code relies on nested Operations/internal leaves; the
user's explicit request is the maintainer direction for that reviewed change.

## Concorde Architecture Gate

### Selected module and interfaces

- `module.concorde.operations` owns the graph runtime, Operation pairs, policy compiler/launcher, and
  new planning Operation.
- `contract.operations.permission-bounded-execution` adds normalized policy/native configuration/
  receipt semantics.
- `contract.operations.plan` owns the public nested context→author graph.
- `contract.skills.workflow-guidance` changes leaf metadata/exposure/effect semantics.
- `contract.skills.agent-surface` changes projection counts and internal-leaf filtering.
- `contract.workspace.feature-workspace` gains required-interface provider and owned-locator context.

### Affected architecture entities and relationships

- Add policy/context/launcher entities to Operations architecture; add planner graph/pair entities.
- Change Operation definition/stage/executor entities from leaf bundles to ordered capability
  occurrences and per-leaf launch specifications.
- Extend `composes` to Operation→Skill or Operation→Operation and add acyclic dependency validation.
- Update standard loop and reflection triage relationships to the public nested planner.
- Update Skills, Runtime, Workspace, Distribution, and root architecture boundaries/entities only
  where their public contracts change; do not copy Operations internals into parent/peer modules.

### Durable feature reconciliation

- Update the selected feature after implementation decisions are concrete, including internal-leaf
  exposure and exact native enforcement behavior.
- Reconcile standard loop, Skills workflow, root workflow/plan/reflections, project ontology,
  Workspace/Runtime Tools, package/install, agent surfaces, and release features named by tasks.
- Preserve stable public interface/capability name `concorde-plan`; remove the leaf source without an alias.

### Code/test baseline

- `src/concorde/operation_runtime.py` currently invokes one executor per stage and rejects non-leaves.
- `src/concorde/skill_assets.py` and `src/concorde/validation/capabilities.py` require at least two
  leaf Skill names and project every manifested capability.
- `src/concorde/feature_workspace.py` exposes repository-wide executable roots and summary-only
  relations; interface ownership exists in the loaded repository model.
- Existing Operation CLIs record topology only; no process launcher or enforcement receipt exists.
- Reflection triage is linear and bundles mutually exclusive routes.
- Installer/tests hard-code 16 leaves, two Operations, and 18 projections.

### Architecture diagrams

The Operations system overview is mandatory and currently passes showcase 9/9. Its entity graph must
change. Update `specs/concorde/modules/operations/diagrams/system-overview.json`, retain normalized
unique output `generated/architecture/concorde-operations-system-overview.html`, `showcase`, and hidden
legend, then validate/deliver/freshness/visual-check. Update peer/root diagrams only if their own
principal entity/relationship graph changes; every diagram update includes its textual counterpart.

## Source Structure

```text
operations/
├── concorde-plan/{operation.py,SKILL.md}
├── concorde-standard-dev-loop/{operation.py,SKILL.md}
└── concorde-reflections-triage/{operation.py,SKILL.md}
skills/
├── concorde-plan-context/SKILL.md
└── concorde-plan-author/SKILL.md
src/concorde/
├── operation_runtime.py
├── operation_permissions.py          # new normalized policy/native render/receipt
├── operation_executor.py             # new injectable Codex/Claude process boundary
├── planning_context.py               # new trusted bounded context resolver
├── feature_workspace.py
├── skill_assets.py
└── validation/capabilities.py
tests/concorde/
├── unit/test_operation_permissions.py
├── unit/test_operation_executor.py
├── unit/test_planning_context.py
├── integration/test_plan_operation.py
└── existing capability/workspace/install/release/Operation suites
```

**Structure Decision**: Policy compilation and process launching are separate Operations-owned
programs; planning context is a trusted deterministic resolver; paired graphs remain exact canonical
directories; internal leaves remain ordinary package Skills with explicit non-projected exposure.

## Attempt Artifacts

All plan/research/data-model/quickstart/tasks/checklist/validation files stay under
`.concorde/attempts/feature.operations.permission-bounded-planning/`. No interface or implementation
narrative is created elsewhere.

## Research Decisions

See `research.md` for eleven decisions. The critical choices are nested public Operation identity,
leaf-owned machine effects, interface-owner-only dependency specs, exact pre-launch path resolution,
Codex profile/Claude strict sandbox parity, injectable real process execution, conditional reflection
routing, internal leaf exposure, and Concorde 2.1.0/Constitution 7.1.0 migration.

## Implementation Phases

1. Add failing tests for leaf effects/exposure, normalized policies, native rendering, nested/cycle
   validation, per-leaf executor calls, bounded planning context, and public projection counts.
2. Implement capability metadata, workspace/path context, policy compiler, executor/receipt, and nested
   runtime foundations.
3. Add internal planning leaves and public plan Operation; migrate standard loop and conditional
   reflection triage without exposing private identities.
4. Reconcile manifest/version, installer/release/sync, generated Codex/Claude surfaces, authorities,
   diagrams, templates, README/docs, and deterministic counts/provenance.
5. Run focused/full/package/docsite/Archify/freshness checks, record every task evidence item, and
   prove protected changes are task-authorized before cleanup-only delivery.

## Risk Controls

| Risk | Control | Verification |
|---|---|---|
| Policy exists only on paper | Real injectable subprocess executor plus matching enforcement receipt | exact argv/settings/receipt tests; no live model |
| Multi-leaf permission union | one binding and executor handoff per occurrence | tasks/implement distinct-policy test |
| Nested abstraction leak/cycle | public capability identity and graph-cycle preflight | direct/indirect cycle and outer-visibility tests |
| Provider internals leak | required-interface owner-only resolver and deny policy | sentinel two-module fixture |
| Native config widening/fallback | ignore/narrow ambient config, strict parsing, fail-if-unavailable/no retry | Codex/Claude config parity and negative tests |
| Credential/network exposure | false/deny defaults and scrubbed environment | normalized policy/native config assertions |
| Same target changes kind | digest-owned installer role transition | update/conflict/rollback integration tests |
| Reflection routes execute together | explicit action/route conditional graph | status/investigate/implement branch tests |
| Diagram/source drift | text+JSON, showcase nine checks, delivery/freshness, truthful visual check | Archify receipts and docsite checks |
| Broad migration misses stale counts | repository-wide `rg` plus manifest/install/release acceptance | zero stale 16/2/old-kind assertions |

## Post-Design Constitution Re-check

The design preserves module/feature authority, adds an explicit acyclic capability hierarchy, and
makes agent effects deterministically enforceable. The planned 7.1.0 amendment is required because
the current wording forbids the chosen nested/internal-leaf model; after that same-milestone
reconciliation there is no intended exception.
