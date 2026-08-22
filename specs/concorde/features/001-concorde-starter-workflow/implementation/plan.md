# Implementation Plan: Complete the Concorde Core Workflow

**Working branch**: `main` (logical feature selection: `001-concorde-starter-workflow`)  
**Date**: 2026-08-22  
**Spec**: [../spec.md](../spec.md)

**Lifecycle**: Active temporal implementation plan. It describes one delivery attempt and is not
durable feature or architecture authority.

## Summary

Complete Concorde's post-installation development workflow by building on the implemented
initialization, one-level context, structural validation, append-only guidance, and portable command
foundation. This attempt adds reviewed nested feature creation and selection, installs the
durable-root/temporal-implementation path model through supported Spec Kit composition, makes
architecture readiness verifiable before plan approval, enriches active-feature implementation
context, and completes deterministic contract/evidence/freshness reconciliation.

Feature 001 owns the command semantics and workflow behavior. Feature 003 remains responsible for
packaging and installation lifecycle; it receives only the metadata/version updates required when
the public command set or packaged adapter changes. Feature 002 remains responsible for rendering and
publishing the site; Feature 001 consumes its deterministic provenance/freshness evidence without
reimplementing Docusaurus or Archify.

## Technical Context

**Language/Version**: Python 3.11+ for the installed deterministic runtime and portable workspace
adapter; Bash for this repository's selected self-hosting Spec Kit script surface; Markdown with
constrained YAML front matter and JSON for maintained sources and normative result contracts

**Primary Dependencies**: Spec Kit/Specify CLI 0.16.4 public preset command composition, extension
command registration, active integration, and `.specify/feature.json` selection behavior; Python
standard library for the installed runtime; existing Archify and Docusaurus validators as delegated
freshness owners

**Storage**: `.concorde/config.json` for source-profile configuration; `.specify/feature.json` for the
single project-scoped selected feature root; recursive maintained intent under `specs/`; one temporal
`implementation/` child per active feature; code/tests as implementation evidence; generated
Archify/Docusaurus outputs and manifests as reproducible projections

**Testing**: Python `unittest`; subprocess calls to the real Spec Kit 0.16.4 CLI; clean temporary
projects in Codex skills mode and a slash-command integration; deterministic source-hash and
byte-equivalence assertions; contract/example parsing and supported conformance adapters; existing
Archify validation plus Docusaurus `npm run check`; separate human protocols for SC-001, SC-007, and
the approval portion of SC-008

**Target Platform**: Windows, macOS, and Linux supported by the declared Spec Kit range, with Python
3.11+ and a supported active coding-agent integration

**Project Type**: Spec Kit preset plus extension around a dependency-light, project-local architecture
workflow runtime; no server or database

**Performance Goals**:

- first-time maintainers place and select a feature within 10 minutes in at least 90% of pilot runs;
- root and child context over a three-level fixture always obey one-level visibility;
- unchanged validation produces byte-equivalent ordered output in all repeated supported-environment
  runs;
- path routing creates one canonical root spec and zero root plan/task aliases;
- first-time maintainers preserve all four artifact-authority distinctions after at most five minutes
  of review in at least 90% of pilot runs

**Constraints**:

- no parallel Concorde feature lifecycle or second active-feature registry;
- durable feature intent at the feature root, all delivery details under `implementation/`;
- at most one active implementation attempt and no silent resume/replacement;
- no LLM in path resolution, context projection, validation, conformance, or freshness decisions;
- all paths project-relative and confined; no symlink escape, traversal, compatibility copy, or alias;
- one-level module visibility and explicit contract on every boundary crossing;
- AI-authored durable architecture requires exact human approval and deterministic checks;
- installed path routing must use public Spec Kit preset/extension mechanisms, not overwrite managed
  core infrastructure;
- Feature 003 installation logic and Feature 002 rendering logic remain outside this implementation

**Scale/Scope**: One recursively nested specification package per project; one selected feature and
one active attempt; five canonical Concorde commands; module/feature/contract/scenario/view/evidence
validation; clean-project acceptance across two agent presentation families; Concorde self-application

## Constitution Check

*GATE: Passed for design before Phase 0 and re-checked after Phase 1. The public composition prototype
below is a blocking implementation checkpoint; failure stops the attempt before product changes.*

| Principle or gate | Design response | Status |
|---|---|---|
| I. Workflow product and proving ground | This plan completes the user workflow and applies the durable/temporal model to Feature 001 itself. Self-application and real clean-project acceptance are final gates. | PASS |
| II. Spec Kit-native and composable | Research selects public preset command composition plus an extension-local workspace adapter. Current `.specify`/skill edits are explicitly self-hosting prototypes, not delivery evidence. Phase 1 must prove installed Codex and slash-command routing; if it fails, stop and pursue an upstream Spec Kit capability/version rather than patch core files. | PASS WITH BLOCKING PROTOTYPE |
| III. Recursive, bounded architecture | Placement resolves one providing module; context and views expose only the current module and immediate children. Three-level root→child acceptance is required. | PASS |
| IV. Explicit ownership and feature alignment | A new Integration refinement, `feature.integration.manage-feature-workspace`, owns create/select/routing. Distribution now refines only installation; Architecture Core retains bounded source semantics. | PASS |
| V. Contracts govern every boundary | Phase 1 adds the Feature Workspace Protocol and extends agent/source contracts. Scenario crossings, custom conformance, failures, and evidence remain explicit implementation gates. | PASS |
| VI. One authority per fact | Root spec/contracts/checklists are durable; implementation artifacts are temporal; `.specify/feature.json` is the only selection pointer; generated outputs remain projections. Existing feature workspaces must be migrated or recorded as finite bootstrap debt before completion. | PASS |
| VII. Deterministic validation and reviewed evidence | Proposal/apply or atomic selection protects mutations; validators remain sorted/read-only; approval, evidence disagreement, and freshness receipts are separately tested. | PASS |
| Architecture documentation standards | Root view stays one-level. Scenario IDs/interactions and governing contracts must be made stable and complete before architecture readiness can pass. | PASS WITH REQUIRED SOURCE UPDATE |
| Pre-implementation ownership gate | Feature 001 is correctly root-owned because it coordinates Spec Kit Integration and Architecture Core; Documentation is a downstream publication handoff, not an unmodeled owned implementation. | PASS |

No constitutional exception is accepted. The public composition prototype and architecture source
updates are stop conditions, not deferred waivers.

## Architecture and Ownership

### Participating module refinements

| Module | Child feature | Responsibility in this implementation |
|---|---|---|
| `module.concorde.spec-kit-integration` | `feature.integration.manage-feature-workspace` | Reviewed placement, nested feature selection, public preset command adapters, phase-specific path routing, and portable create/select commands. |
| `module.concorde.architecture-core` | `feature.architecture-core.manage-bounded-sources` | Root proposal/apply, source semantics, placement-supporting bounded context, enriched active-feature context, deterministic validation, evidence/freshness normalization. |

`feature.integration.compose-starter-workflow` now refines Feature 003 only. Distribution therefore
does not participate in Feature 001 implementation except that Feature 003 must refresh package
metadata after the command/adapter payload changes. Documentation consumes a validated handoff under
Feature 002 and does not become a hidden Feature 001 implementation owner.

### Boundary contracts

| Contract | Owner | Role here |
|---|---|---|
| `contract.concorde.core-workflow` | root Concorde | User-facing composition of the post-installation workflow. |
| `contract.integration.feature-workspace` | Spec Kit Integration | Normative create/select paths, proposal, selection, collision, and active-attempt semantics. |
| `contract.integration.workflow-composition` | Spec Kit Integration | Public composition and phase routing without changing Spec Kit phase meaning. |
| `contract.integration.agent-skills` | Spec Kit Integration | Five portable command surfaces and presentation-neutral intent. |
| `contract.core.architecture-services` | Architecture Core | Existing custom v1 init/context/validate JSON boundary. |
| `contract.integration.spec-kit-platform` | external Spec Kit | Supported preset, command, selection, and lifecycle behavior required by Concorde. |

The new Feature Workspace Protocol remains separate from Architecture Service Protocol v1. Selection
is owned by Integration; adding create/select enum values to Architecture Core would blur module
responsibility and risk strict v1 consumers.

### Current-level scenario design

The root Archify view remains the canonical one-level view and must carry stable scenario IDs for:

- establishing the hierarchy and reviewing feature placement;
- creating/selecting the nested feature and running the normal lifecycle;
- reviewing architecture readiness before plan approval; and
- implementing with bounded context, reconciling evidence, and handing validated sources to
  Documentation.

Each ordered cross-boundary interaction must name its root or child contract. Child feature bodies
remain navigation targets and are never embedded in the root view.

## Project Structure

### Documentation and design artifacts

```text
specs/concorde/features/001-concorde-starter-workflow/
├── spec.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── agent-commands.md
│   ├── architecture-service.schema.json
│   ├── architecture-sources.md
│   ├── feature-workspace.schema.json
│   └── examples/
│       ├── context-response.json
│       ├── validation-response.json
│       ├── feature-create-proposal.json
│       └── feature-select-response.json
└── implementation/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md                 # regenerated after this plan
    └── validation.md            # reset for this attempt; no Feature 003 evidence

specs/concorde/modules/spec-kit-integration/
├── module.md
├── contracts/feature-workspace/contract.md
└── features/002-manage-feature-workspace/spec.md
```

### Implementation source

```text
presets/concorde-core/
├── preset.yml
├── commands/                    # supported wrappers/overrides for affected core phases
└── templates/                   # existing append-only architecture guidance

extensions/concorde/
├── extension.yml               # five canonical commands
├── commands/
│   ├── speckit.concorde.init.md
│   ├── speckit.concorde.feature.create.md
│   ├── speckit.concorde.feature.select.md
│   ├── speckit.concorde.context.md
│   └── speckit.concorde.validate.md
├── scripts/
│   ├── bash/concorde.sh
│   ├── powershell/concorde.ps1
│   └── python/
│       ├── concorde.py
│       └── workspace.py         # portable selection/path adapter
└── runtime/concorde/
    ├── cli.py
    ├── context.py
    ├── feature_workspace.py
    ├── repository.py
    ├── validate.py
    ├── validation/
    │   ├── contracts.py
    │   ├── evidence.py
    │   ├── layout.py
    │   ├── scenarios.py
    │   └── freshness.py
    └── ...                      # existing init/model/diagnostics modules

.specify/scripts/bash/           # self-hosting prototype; not packaged authority
.agents/skills/speckit-*/        # self-hosting rendered command surfaces

tests/concorde/
├── unit/
│   ├── test_feature_workspace.py
│   └── test_*_validation.py
├── contract/
│   ├── test_agent_commands.py
│   ├── test_feature_workspace_contract.py
│   └── test_structured_results.py
├── integration/
│   ├── test_feature_workspace.py
│   ├── test_implementation_workspace.py
│   ├── test_context.py
│   ├── test_validation.py
│   └── test_self_architecture.py
└── acceptance/
    └── test_core_workflow.py
```

### Cross-feature compatibility updates

Public command-count/package changes require narrow synchronization in:

```text
scripts/release/build-components.py
catalogs/extensions.json
specs/concorde/features/003-install-concorde-speckit/
tests/concorde/contract/test_manifests.py
tests/concorde/acceptance/test_{codex_skills,slash_commands}.py
```

These updates keep Feature 003 metadata truthful; they do not move installation lifecycle into this
plan.

## Implementation Strategy

### Phase 1: Prove supported installed routing

1. Prototype `concorde-core` command composition against unmodified Spec Kit 0.16.4 core
   infrastructure.
2. Have composed commands call an extension-local workspace adapter that returns the feature root,
   `implementation/` root, and all phase paths.
3. Install the real preset and extension into clean Codex and slash-command projects; prove plan,
   tasks, implement, analyze, converge, checklist, and task-to-issue paths plus no root aliases.
4. If public APIs cannot provide the behavior, stop. Record the failed prototype and pursue an
   upstream Spec Kit change; do not continue with installer patches.

### Phase 2: Finish workspace routing and lifecycle state

1. Consolidate path derivation and safe persistence in the portable workspace adapter.
2. Preserve `SPECIFY_FEATURE_DIRECTORY` as explicit override and `.specify/feature.json` as the only
   persisted selection.
3. Add active/resume/accepted conflict semantics so a non-empty attempt is never silently replaced.
4. Migrate current Concorde feature workspaces to the durable/temporal layout or record a finite,
   named bootstrap migration before claiming self-application.

### Phase 3: Deliver reviewed feature create/select

1. Implement deterministic safe module/feature lookup, number allocation, path derivation, collision
   reporting, and source-digest binding.
2. Add the two portable commands using the Feature Workspace Protocol.
3. Creation presents bounded context and an exact placement proposal, invokes the normal specify
   phase only after approval, registers accepted architecture intent, validates it, and selects the
   resulting root atomically.
4. Selection validates an existing canonical spec and ownership before changing only the standard
   selection pointer.

### Phase 4: Strengthen hierarchy and architecture readiness

1. Require non-empty Module Responsibility/Boundary and stable ID grammar.
2. Validate canonical spec paths, one provider, nearest-common-parent placement, and adjacent
   refinement.
3. Replace heuristic view matching with explicit stable module/feature references; verify current
   module, immediate child I/O, permitted externals, and contract-governed ordered interactions.
4. Turn preset architecture guidance into a reviewable readiness result covering owner, abstraction,
   participating children, dependency direction, refinements, crossings, affected view, and expected
   evidence. Missing durable information blocks architecture-ready status without replacing Spec
   Kit's plan phase.

### Phase 5: Enrich bounded implementation context

1. Add active feature root paths, durable contracts/checklists, current implementation artifacts,
   adjacent refinements, relevant contract bodies, and evidence references.
2. Preserve one-level module visibility and return only paths/content necessary for the selected
   feature.
3. Add stable navigation IDs rather than expanding unrelated/deeper artifacts.

### Phase 6: Complete deterministic reconciliation

1. Split validation into focused, stably ordered rule modules.
2. Add workspace layout/selection, scenario boundary, canonical path, and evidence-reference rules.
3. Support an explicit Profile 1 conformance adapter set: JSON/TOML and constrained YAML parsing;
   a documented deterministic subset for checked-in JSON Schemas/grammars; unsupported formats yield
   a finding rather than false conformance.
4. Consume source-digest/provenance receipts from Archify and Documentation to detect stale
   projections. Do not execute arbitrary configured commands or reimplement their renderers.
5. Preserve `unknown` and `disagrees` independently of architecture validity.

### Phase 7: Self-application, compatibility, and evidence

1. Update root/child module specs, contracts, stable scenario traces, and the root view.
2. Refresh the extension manifest, release command count, catalog digests, and Feature 003
   verification references.
3. Run unit, contract, integration, installed-agent acceptance, self-validation, Archify, and docsite
   gates; verify unchanged-source hashes and byte repeatability.
4. Reset Feature 001 validation evidence for this attempt and never reuse Feature 003 installation
   outcomes.
5. Conduct SC-001 and SC-007 pilots and record SC-008 human approvals. Keep evidence `partial` until
   real results meet thresholds.

## Test and Evidence Strategy

| Requirement area | Evidence |
|---|---|
| Public Spec Kit composition | Install actual preset/extension into unmodified 0.16.4 fixtures; inspect registered core and Concorde commands in Codex and slash-command modes. |
| Durable/temporal routing | Exhaustive phase-path matrix, explicit override/persisted selection, read-only no-persist, no root files/symlinks, resume/conflict tests. |
| Initialization/hierarchy | Existing proposal/apply/rollback tests plus three-level root→child bounded-context assertions. |
| Feature placement/selection | Proposal digest, nearest-common-parent fixture, collision/unsafe/stale/duplicate failures, atomic state, idempotent reselection, one complete normal lifecycle. |
| Architecture readiness | Failing cross-boundary fixture missing contracts/scenario/evidence, then passing after durable sources are supplied. |
| Context | Exact feature artifact set, current-level module/children, relevant contracts/refinements/evidence, exclusion of grandchildren/unrelated attempts. |
| Contract conformance | Supported JSON/TOML/constrained-YAML examples, valid and invalid schema/grammar fixtures, unsupported adapter finding. |
| Evidence/freshness | Missing, stale, verified, and disagrees references; Archify/docsite provenance receipts; architecture success never upgrades code evidence. |
| Determinism/safety | Three byte-equivalent runs, stable exit codes/order, before/after source hashes, staged write rollback. |
| Self-application | Zero unexplained findings over Concorde sources plus complete Python, Archify, and Docusaurus gates. |
| Human outcomes | Timed SC-001 placement pilot, five-minute SC-007 authority pilot, and explicit SC-008 review records; never inferred from tests. |

## Post-Design Constitution Re-check

Phase 1 design artifacts now remove installation entities from Feature 001, define durable versus
temporal workspace semantics, introduce a separately owned Feature Workspace contract and child
feature, retain Architecture Service Protocol v1, and supply target-state acceptance scenarios. The
design identifies the only compatibility risk and makes its clean-install public-composition
prototype a blocking first phase with an upstream-only fallback. No hidden fork, duplicate authority,
or unexplained exception is permitted.

Implementation and human evidence remain incomplete by design. Contract evidence for feature
workspace selection and five-command portability is `unknown`/`partial` until the tasks execute; this
is honest evidence status, not a constitution gate failure.

## Complexity Tracking

| Added complexity | Why needed | Containment |
|---|---|---|
| Separate Feature Workspace Protocol | Selection belongs to Spec Kit Integration and must not expand Architecture Core's v1 enum casually. | One small schema, two examples, one child contract. |
| Preset core-command composition | Installed projects must receive temporal routing without managed core-script overwrites. | Only affected commands; stop-and-upstream fallback if public composition fails. |
| Focused validation adapters | FR-020 spans layout, contracts, scenarios, evidence, and freshness. | Stable registry; explicit supported formats; renderer/publisher logic remains delegated. |

No constitution violation or indefinite bootstrap exception is accepted.
