# Implementation Plan: Complete the Concorde Core Workflow

**Working branch**: `main` (logical feature selection: `001-concorde-starter-workflow`)  
**Date**: 2026-08-22  
**Spec**: [../spec.md](../spec.md)

**Lifecycle**: Active temporal implementation plan. It describes one delivery attempt and is not
durable feature or architecture authority.

## Summary

Complete Concorde's post-installation development workflow by building on the implemented
initialization, one-level context, structural validation, append-only guidance, and portable command
foundation. This attempt adds reviewed nested feature creation and selection, defines and implements
the durable-root/temporal-implementation path service consumed by installed commands, makes
architecture readiness verifiable before plan approval, enriches active-feature implementation
context, and completes deterministic contract/evidence/freshness reconciliation.

Feature 001 owns the command semantics and workflow behavior. Feature 003 remains responsible for
the preset's nine normal-command overrides, extension/package manifests, release archives, catalogs,
agent-specific materialization, and clean-project execution evidence. Feature 001 supplies a
versioned workspace/command handoff that Feature 003 must package without redefining. Feature 002
remains responsible for rendering and publishing the site; Feature 001 consumes its deterministic
provenance/freshness evidence without reimplementing Docusaurus or Archify.

## Technical Context

**Language/Version**: Python 3.11+ for the installed deterministic runtime and portable workspace
adapter; Bash for this repository's selected self-hosting Spec Kit script surface; Markdown with
constrained YAML front matter and JSON for maintained sources and normative result contracts
including descriptively named feature-owned Archify JSON for scenario explanation

**Primary Dependencies**: Spec Kit/Specify CLI 0.16.4 `.specify/feature.json` selection and lifecycle
semantics; the Feature 003 installation contract for release-time command materialization; Python
standard library for the deterministic runtime/workspace adapter; existing Archify and Docusaurus
validators as delegated freshness owners

**Storage**: `.concorde/config.json` for source-profile configuration; `.specify/feature.json` for the
single project-scoped selected feature root; recursive maintained intent under `specs/`; one temporal
`implementation/` child per active feature; code/tests as implementation evidence; generated
Archify/Docusaurus outputs and manifests as reproducible projections

**Testing**: Python `unittest`; subprocess tests of the workspace/runtime contracts and normal phase
semantics; deterministic source-hash and byte-equivalence assertions; contract/example parsing and
supported conformance adapters; Feature 003's clean installed skills/slash acceptance as the
distribution handoff gate; existing Archify validation plus Docusaurus `npm run check`; separate
human protocols for SC-001, SC-007, and the approval portion of SC-008

**Target Platform**: Windows, macOS, and Linux supported by the declared Spec Kit range, with Python
3.11+ and a supported active coding-agent integration

**Project Type**: Dependency-light, project-local architecture workflow and runtime integrated with
Spec Kit; Feature 003 separately packages its preset and extension; no server or database

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
- this feature must expose distribution-neutral workspace semantics; Feature 003 must deliver them
  through public Spec Kit preset/extension mechanisms without overwriting managed core infrastructure;
- Feature 003 installation logic and Feature 002 rendering logic remain outside this implementation;
- feature diagrams remain explanatory rather than behavioral authority; a cross-component feature
  has at most one `role: core` architecture view of stable component interaction or a recorded
  sufficiency rationale, while dynamic scenario diagrams remain `role: supplemental`

**Scale/Scope**: One recursively nested specification package per project; one selected feature and
one active attempt; five canonical Concorde command intents; module/feature/contract/scenario/view/evidence
validation; one versioned handoff to Feature 003 for nine normal and five Concorde-specific installed
surfaces; Concorde self-application

## Constitution Check

*GATE: Passed for design before Phase 0 and re-checked after Phase 1. The public composition prototype
below is a blocking implementation checkpoint; failure stops the attempt before product changes.*

| Principle or gate | Design response | Status |
|---|---|---|
| I. Workflow product and proving ground | This plan completes the user workflow and applies the durable/temporal model to Feature 001 itself. Self-application and real clean-project acceptance are final gates. | PASS |
| II. Spec Kit-native and composable | Feature 001 owns the extension-local workspace service and command semantics; Feature 003 owns public preset command replacement/materialization. Current `.specify`/skill edits are explicitly self-hosting prototypes, not delivery evidence. The combined milestone cannot pass until Feature 003 proves clean installed Codex and slash-command routing. | PASS WITH CROSS-FEATURE GATE |
| III. Recursive, bounded architecture | Placement resolves one providing module; context and views expose only the current module and immediate children. Three-level root→child acceptance is required. | PASS |
| IV. Explicit ownership and feature alignment | A new Integration refinement, `feature.integration.manage-feature-workspace`, owns create/select/routing. Distribution now refines only installation; Architecture Core retains bounded source semantics. | PASS |
| V. Contracts govern every boundary | Phase 1 adds the Feature Workspace Protocol and extends agent/source contracts. Scenario crossings, custom conformance, failures, and evidence remain explicit implementation gates. | PASS |
| VI. One authority per fact | Root spec/contracts/checklists are durable; implementation artifacts are temporal; `.specify/feature.json` is the only selection pointer; generated outputs remain projections. Existing feature workspaces must be migrated or recorded as finite bootstrap debt before completion. | PASS |
| VII. Deterministic validation and reviewed evidence | Proposal/apply or atomic selection protects mutations; validators remain sorted/read-only; approval, evidence disagreement, and freshness receipts are separately tested. | PASS |
| Architecture documentation standards | Root view stays one-level. Scenario IDs/interactions and governing contracts stay stable; the feature has a separate text-backed core architecture view for stable component interaction, while dynamic views remain supplemental. | PASS |
| Pre-implementation ownership gate | Feature 001 is correctly root-owned because it coordinates Spec Kit Integration and Architecture Core; Documentation is a downstream publication handoff, not an unmodeled owned implementation. | PASS |

No constitutional exception is accepted. The public composition prototype and architecture source
updates are stop conditions, not deferred waivers.

## Architecture and Ownership

### Participating module refinements

| Module | Child feature | Responsibility in this implementation |
|---|---|---|
| `module.concorde.spec-kit-integration` | `feature.integration.manage-feature-workspace` | Reviewed placement, nested feature selection, phase-specific path semantics, workspace adapter, and portable create/select commands. |
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
| `contract.integration.workflow-composition` | Spec Kit Integration | Feature 001 supplies phase-path semantics; Feature 003 owns their public preset composition and materialization. |
| `contract.integration.agent-skills` | Spec Kit Integration | Five portable command intents from Feature 001; Feature 003 owns installed presentations. |
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
├── diagrams/
│   └── core-workflow-components.json
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
extensions/concorde/
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

### Feature 003 distribution handoff

Feature 001 changes to command/workspace semantics produce a versioned handoff consumed by Feature
003. The following sources are Feature 003 implementation scope and MUST NOT be treated as Feature
001 delivery evidence:

```text
presets/concorde-core/{preset.yml,commands/,templates/}
extensions/concorde/extension.yml
scripts/release/build-components.py
catalogs/{extensions,presets,bundles}.json
specs/concorde/features/003-install-concorde-speckit/
tests/concorde/{contract,integration,acceptance}/  # release/install/materialization checks
```

Feature 003 may package Feature 001's extension runtime and commands, but it may not redefine their
canonical intent, result contracts, path semantics, or failure behavior.

## Implementation Strategy

### Phase 1: Freeze the workflow-to-distribution handoff

1. Finalize the Feature Workspace Protocol and the distribution-neutral adapter result containing the
   feature root, `implementation/` root, and every phase path.
2. Define the nine normal-command routing obligations and five Concorde-specific command intents in
   durable contracts without embedding agent-specific filenames or preset composition strategy.
3. Prove the adapter and command semantics in self-hosting/source fixtures, including explicit
   selection, read-only resolution, conflict handling, and no root aliases.
4. Hand the versioned contract, examples, runtime sources, and expected acceptance matrix to Feature
   003. Release-installed parity is a Feature 003 gate and cannot be claimed by Feature 001 tests.

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
2. Load declared feature-diagram JSON as durable feature sources, include it in the canonical source
   digest, and project its scenario, kind, output, and title into active-feature context without
   treating it as a module-level architecture view.
3. Preserve one-level module visibility and return only paths/content necessary for the selected
   feature.
4. Add stable navigation IDs rather than expanding unrelated/deeper artifacts.

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
2. Publish the runtime/command handoff expected by Feature 003 and verify that its plan references the
   same contract version and command inventory; do not edit release manifests or catalogs here.
3. Run unit, contract, integration, self-validation, Archify, and docsite gates; consume Feature 003's
   matching installed-agent receipt; verify unchanged-source hashes and byte repeatability.
4. Reset Feature 001 validation evidence for this attempt and never reuse Feature 003 installation
   outcomes.
5. Conduct SC-001 and SC-007 pilots and record SC-008 human approvals. Keep evidence `partial` until
   real results meet thresholds.
6. Maintain the core component-interaction architecture view under `diagrams/`, declare it as `role: core` in `spec.md`, align it with scenario/contract prose,
   deliver it through Archify, publish it through the existing docsite artifact route, and preserve
   truthful pending visual status when no browser is available.

## Test and Evidence Strategy

| Requirement area | Evidence |
|---|---|
| Distribution handoff | Validate the Feature Workspace Protocol, adapter examples, nine phase obligations, and five command intents; consume Feature 003's clean-install acceptance receipt rather than reproducing package tests here. |
| Durable/temporal routing | Exhaustive phase-path matrix, explicit override/persisted selection, read-only no-persist, no root files/symlinks, resume/conflict tests. |
| Initialization/hierarchy | Existing proposal/apply/rollback tests plus three-level root→child bounded-context assertions. |
| Feature placement/selection | Proposal digest, nearest-common-parent fixture, collision/unsafe/stale/duplicate failures, atomic state, idempotent reselection, one complete normal lifecycle. |
| Architecture readiness | Failing cross-boundary fixture missing contracts/scenario/evidence, then passing after durable sources are supplied. |
| Context | Exact feature artifact set, declared feature diagrams, current-level module/children, relevant contracts/refinements/evidence, exclusion of grandchildren/unrelated attempts. |
| Contract conformance | Supported JSON/TOML/constrained-YAML examples, valid and invalid schema/grammar fixtures, unsupported adapter finding. |
| Evidence/freshness | Missing, stale, verified, and disagrees references; Archify/docsite provenance receipts; architecture success never upgrades code evidence. |
| Determinism/safety | Three byte-equivalent runs, stable exit codes/order, before/after source hashes, staged write rollback. |
| Self-application | Zero unexplained findings over Concorde sources plus complete Python, Archify, and Docusaurus gates. |
| Feature diagram | `diagrams/core-workflow-components.json` distinguishes agent-facing skills/commands, phase adapters, portable launchers, Python runtime, workspace authority categories, and their stable interactions; 9/9 Archify showcase validation, fresh HTML delivery, automatic feature-page embedding, and truthful visual-check receipt. |
| Human outcomes | Timed SC-001 placement pilot, five-minute SC-007 authority pilot, explicit SC-008 review records, and five-minute SC-011 installed-layer/workspace-classification pilot; never inferred from tests. |

## Post-Design Constitution Re-check

Phase 1 design artifacts remove installation entities from Feature 001, define durable versus
temporal workspace semantics, introduce a separately owned Feature Workspace contract and child
feature, retain Architecture Service Protocol v1, and supply a versioned handoff to Feature 003. The
clean-install public-composition risk is now planned and evidenced only by Feature 003. No hidden fork,
duplicate authority, or unexplained exception is permitted.

Implementation and human evidence remain incomplete by design. Contract evidence for feature
workspace selection and five-command portability is `unknown`/`partial` until the tasks execute; this
is honest evidence status, not a constitution gate failure.

## Complexity Tracking

| Added complexity | Why needed | Containment |
|---|---|---|
| Separate Feature Workspace Protocol | Selection belongs to Spec Kit Integration and must not expand Architecture Core's v1 enum casually. | One small schema, two examples, one child contract. |
| Cross-feature distribution handoff | Feature 001 owns semantics while Feature 003 owns installed surfaces and package lifecycle. | One versioned workspace/command contract and one acceptance receipt; no duplicated command meaning. |
| Focused validation adapters | FR-020 spans layout, contracts, scenarios, evidence, and freshness. | Stable registry; explicit supported formats; renderer/publisher logic remains delegated. |

No constitution violation or indefinite bootstrap exception is accepted.
