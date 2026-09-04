---
id: feature.capabilities.run-deterministic-tools
kind: feature
module: module.concorde.capabilities
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.understanding.explore-alignment
    relation: depended_on_by
  - id: feature.capabilities.maintain-agent-surfaces
    relation: depended_on_by
  - id: feature.reflections.record-and-triage
    relation: depended_on_by
  - id: feature.lifecycle.standard-development-loop
    relation: depended_on_by
  - id: feature.capabilities.permission-bounded-execution
    relation: depended_on_by
interfaces:
  provided:
    - contract.capabilities.tools
  required:
    - contract.understanding.feature-workspace
    - contract.understanding.records
---

# Feature Design: Run Deterministic Tools

## Outcome and Scope

Skills, Operations, scripts, CI, and maintainers can invoke portable deterministic Tools that resolve
Profile 7 sources and native control state, validate typed architecture/interfaces/capabilities,
initialize safely, scaffold the packaged project docsite, return bounded context, explore
evidence-qualified alignment, maintain reflection agent assets, and close attempts atomically.

These are bounded deterministic actions, not LangGraph Operations. CLI subcommand spelling remains
stable, while public results use Tool terminology and versioned contracts.

## Usage

A launcher locates the installed capability framework, the CLI dispatches the named Tool through one
canonical envelope, and the result returns exactly one machine-readable payload without becoming a
conversational UI. For exploration, optional implementation evidence is validated and bounded after
Profile validation; no Tool writes an explorer index or repairs input.

## Interfaces

### `contract.capabilities.tools` — Deterministic Concorde Tools

- **Consumer**: Source-checkout or installed Concorde Skills and Operations, scripts, CI, and
  supported automation.
- **Direction**: Safe Tool arguments to one structured result envelope.
- **Entry points**: Colocated POSIX/PowerShell launchers and Python `scripts/concorde.py` in source or
  `.concorde/framework`; Tools include `init`, `docsite`, `context`, `explore`, `validate`, `deliver`,
  and `agent-assets`.
- **Inputs**: Project root, Tool name, stable target, format, and Tool-specific proposal/options;
  exploration additionally accepts safe graph/sidecar paths, expected revision, text query, and
  effective-status filters. Mutating actions additionally require linked-worktree Git identity or
  the explicit maintainer-authorized primary/current-directory override.
- **Outputs**: `tool`, target, status, artifacts, findings, and versioned result payload; exploration
  returns Alignment Schema 1 specification/implementation/provenance/alignment projections.
- **Obligations**: Deterministic behavior, safe paths, non-mutating reads, atomic reviewed mutations,
  committed-base isolation before agent-driven writes, actionable diagnostics, and no import of
  optional LangGraph during base Tool use.
- **Failures**: Primary/non-Git mutation without explicit override, invalid config/source/target/path/proposal, unavailable input, or filesystem failure
  returns failure and preserves unrelated/current authority.
- **Compatibility**: Architecture-service envelope 2 exposes Profile 7, Protocol 13, Initialization
  Proposal 3, Docsite Scaffold Proposal 1, Delivery Proposal 9, and Alignment Schema 1 terminology.
  Concorde 2.1.0 reserves Operation for paired LangGraphs.
- **Implementing entities**: `entity.capabilities.cli`, `entity.capabilities.tool-result`,
  `entity.capabilities.tool-envelope`, `entity.capabilities.python-adapter`, `entity.capabilities.worktree-gate`,
  `module.concorde.understanding`, `module.concorde.lifecycle`, and `module.concorde.auto-docs`.
- **Example**: `python3 scripts/concorde.py --project-root . validate --format json` emits a Tool
  envelope whose findings carry stable rule IDs and remediations.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.capabilities.cli` | Dispatches Tools into one envelope contract. |
| `entity.capabilities.worktree-gate` | Rejects agent-driven mutating Tool actions in a primary/non-Git checkout unless the explicit override is present. |
| `entity.capabilities.tool-result` | Carries the structured result of one bounded action. |
| `entity.capabilities.tool-envelope` | Serializes the public `tool` discriminator. |
| `entity.capabilities.python-adapter` | Enters the CLI dispatcher from a portable launcher in source or installed layout. |
| `module.concorde.understanding` | Supplies the validated project package plus the `init`, `context`, `explore`, and `validate` Tools. |
| `module.concorde.lifecycle` | Supplies the cleanup-only `deliver` Tool. |
| `module.concorde.auto-docs` | Supplies the reviewed `docsite` scaffold Tool. |

## Related Features

- `feature.concorde.workflow` composes this Tool-dispatch capability as one stage of the end-to-end
  lifecycle.
- `feature.understanding.explore-alignment` depends on this feature's `explore` Tool entry point to
  project bounded evidence-qualified alignment.
- `feature.capabilities.maintain-agent-surfaces` reuses the same launcher and CLI entry points when a
  maintainer checks or refreshes this repository's own agent surfaces.
- `feature.reflections.record-and-triage` depends on the `agent-assets` Tool dispatched through the
  same CLI envelope.
- `feature.lifecycle.standard-development-loop` invokes the cleanup-only delivery Tool through this
  dispatcher at its final stage.
- `feature.capabilities.permission-bounded-execution` resolves workspace paths through the same Tool
  contract before compiling per-leaf policy.

## Usage Scenarios

1. A maintainer runs `concorde validate` from a checkout; the CLI loads the same repository model used
   by every other Tool and returns one machine-readable envelope with sorted findings.
2. An installed Skill invokes `concorde context` for its selected feature and receives exactly one
   bounded module or feature altitude, never a conversational summary.
3. `concorde explore` validates an optional pinned implementation graph and sidecar, then returns
   bounded alignment projections without writing an index or repairing the input.
4. An agent invokes delivery from the primary worktree without an explicit override; the Tool fails
   before proposal materialization and directs the agent to a linked worktree at committed `HEAD`.

## Requirements

- **FR-001**: All platform launchers MUST preserve identical Tool dispatch semantics regardless of
  entry point.
- **FR-002**: Every Tool MUST validate safe project-relative targets before reading or writing.
- **FR-003**: Read-only failures and rejected mutation proposals MUST be byte-preserving.
- **FR-004**: Exploration MUST preserve Profile identity separately from adapter metadata and reduce
  absent, stale, candidate-only, or invalid evidence to unknown.
- **FR-005**: Every public envelope MUST use `tool`; no lower-level action may claim Operation
  identity.
- **FR-006**: Package capability validation MUST inspect exposure/effects, mixed Skill/Operation
  literals, exact occurrence bindings, and cycles from source/metadata/AST without importing or
  executing arbitrary Operation Python.
- **FR-007**: Agent-driven mutating Tool actions MUST fail closed outside a linked Git worktree unless
  `--allow-primary-worktree` explicitly represents maintainer authorization; the preflight MUST NOT
  read or transfer primary dirty file contents.

## Edge Cases

- A target or attempt path is a symlink.
- PowerShell and POSIX quoting produce equivalent arguments.
- A valid implementation graph has no explicit alignment sidecar or current expected revision.
- LangGraph is unavailable while a base Tool is imported or invoked; Tool behavior remains available.
- Tool dispatch and the Operation runtime/policy/process modules share the physical `src/concorde`
  package but remain distinct kinds: bounded deterministic actions stay Tools and paired LangGraph
  execution stays Operation even under one owning module.
