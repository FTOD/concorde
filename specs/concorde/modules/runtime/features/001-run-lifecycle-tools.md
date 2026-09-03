---
id: feature.runtime.run-lifecycle-tools
kind: feature
module: module.concorde.runtime
related_features:
  - feature.concorde.workflow
  - feature.concorde.explore-alignment
  - feature.concorde.maintain-agent-surfaces
  - feature.concorde.record-workflow-reflections
  - feature.operations.standard-development-loop
  - feature.operations.permission-bounded-planning
interfaces:
  provided:
    - contract.runtime.tools
  required:
    - contract.workspace.feature-workspace
    - contract.workspace.records
evidence_status: verified
---

# Feature Design: Run Lifecycle Tools

## Outcome and Scope

Skills, Operations, scripts, CI, and maintainers can invoke portable deterministic Tools that resolve
Profile 7 sources and native control state, validate typed architecture/interfaces/capabilities,
initialize safely, scaffold the packaged project docsite, return bounded context, explore
evidence-qualified alignment, maintain reflection queue state, and close attempts atomically.

These are bounded runtime actions, not LangGraph Operations. CLI subcommand spelling remains stable,
while public results use Tool terminology and versioned contracts.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.runtime.cli` | Dispatches Tools into one envelope contract. |
| `entity.runtime.tool-result` | Carries the structured result of one bounded action. |
| `entity.runtime.tool-envelope` | Serializes the public `tool` discriminator. |
| `entity.runtime.repository-loader` | Loads normalized Profile 7 modules/entities/features/interfaces and control authorities. |
| `entity.runtime.alignment-explorer` | Projects bounded Profile subjects beside optional pinned UA graph/evidence with conservative status. |
| `entity.runtime.workspace-resolver` | Emits Protocol 13 stable-ID paths and bounded relations. |
| `entity.runtime.validator` | Produces exhaustive deterministic findings, including package capability structure. |
| `entity.runtime.delivery` | Applies digest-bound cleanup-only Delivery Proposal 9. |

## Interfaces

### `contract.runtime.tools` — Deterministic Runtime Tools

- **Consumer**: Source-checkout or installed Concorde Skills and Operations, scripts, CI, and supported
  automation.
- **Direction**: Safe Tool arguments to one structured result envelope.
- **Entry points**: Colocated POSIX/PowerShell launchers and Python `scripts/concorde.py` in source or
  `.concorde/framework`; Tools include `init`, `docsite`, `context`, `explore`, `validate`, `deliver`,
  and `agent-assets`.
- **Inputs**: Project root, Tool name, stable target, format, and Tool-specific proposal/options;
  exploration additionally accepts safe graph/sidecar paths, expected revision, text query, and
  effective-status filters.
- **Outputs**: `tool`, target, status, artifacts, findings, and versioned result payload; exploration
  returns Alignment Schema 1 specification/implementation/provenance/alignment projections.
- **Obligations**: Deterministic behavior, safe paths, non-mutating reads, atomic reviewed mutations,
  actionable diagnostics, and no import of optional LangGraph during base Tool use.
- **Failures**: Invalid config/source/target/path/proposal, unavailable input, or filesystem failure
  returns failure and preserves unrelated/current authority.
- **Compatibility**: Architecture-service envelope 2 exposes Profile 7, Protocol 13, Initialization
  Proposal 3, Docsite Scaffold Proposal 1, Delivery Proposal 9, and Alignment Schema 1 terminology. Concorde 2.1.0 reserves
  Operation for paired LangGraphs.
- **Implementing entities**: `entity.runtime.cli`, `entity.runtime.tool-result`,
  `entity.runtime.tool-envelope`, `entity.runtime.repository-loader`,
  `entity.runtime.alignment-explorer`, `entity.runtime.validator`, `entity.runtime.docsite-scaffold`,
  and `entity.runtime.delivery`.
- **Example**: `python3 scripts/concorde.py --project-root . validate --format json` emits a Tool
  envelope whose findings carry stable rule IDs and remediations.

## Usage Scenarios

A launcher locates the installed Runtime, the CLI loads the same repository model used by validation,
and the Tool returns exactly one machine-readable result without becoming a conversational UI. For
exploration, optional implementation evidence is validated and bounded after Profile validation; no
Tool writes an explorer index or repairs input.

## Requirements

- **FR-001**: All platform launchers MUST preserve the same Python Runtime Tool semantics.
- **FR-002**: Every Tool MUST validate safe project-relative targets before reading or writing.
- **FR-003**: Read-only failures and rejected mutation proposals MUST be byte-preserving.
- **FR-004**: Exploration MUST preserve Profile identity separately from adapter metadata and reduce
  absent, stale, candidate-only, or invalid evidence to unknown.
- **FR-005**: Every public envelope MUST use `tool`; no lower-level action may claim Operation identity.
- **FR-006**: Package capability validation MUST inspect exposure/effects, mixed
  Skill/Operation literals, exact occurrence bindings, and cycles from source/metadata/AST without
  importing or executing arbitrary Operation Python.

## Edge Cases

- A target or attempt path is a symlink.
- PowerShell and POSIX quoting produce equivalent arguments.
- A valid implementation graph has no explicit alignment sidecar or current expected revision.
- LangGraph is unavailable while a base Tool is imported or invoked; Tool behavior remains available.
- Operation permission/native process modules share the physical package but remain owned by
  Operations and are not reclassified as deterministic Runtime Tools.
