# Implementation Plan: Deliver Concorde through Spec Kit

**Working branch**: `main` (logical feature selection: `003-install-concorde-speckit`)  
**Date**: 2026-08-22  
**Spec**: [../spec.md](../spec.md)

**Lifecycle**: Active temporal implementation plan. Package manifests and durable contracts remain
authoritative; this file records one attempt to make the distributed workflow match them.

## Summary

Refactor the already working bundle lifecycle so a release-installed project receives the complete
Concorde workflow, not merely package files and late command addenda. Keep the three preset template
layers composable, replace all nine affected normal Spec Kit command surfaces with authoritative
Concorde-aware forms, package the five Concorde-specific commands plus Feature 001's workspace
adapter/runtime in the extension, materialize both contribution types through the active integration,
and prove the result from built archives in checkout-isolated skills and slash-command projects.

Feature 003 owns composition strategy, package manifests, release archives, catalogs, registration,
update/removal, and clean-install evidence. Feature 001 remains authoritative for workspace paths,
command intent, architecture behavior, and result/failure semantics. Feature 003 must identify the
exact Feature 001 handoff digest it packages and cannot repair a semantic mismatch by changing an
agent-specific prompt.

## Technical Context

**Language/Version**: Python 3.11+ for release tooling, installed workspace/runtime entry points, and
acceptance harnesses; Spec Kit command Markdown rendered to agent-specific Markdown/TOML forms; YAML
manifests; JSON catalogs, plans, receipts, and Archify sources

**Primary Dependencies**: Specify CLI/Spec Kit 0.16.4 public bundle, preset, catalog, provenance,
command-composition, and `CommandRegistrar` contracts; Feature 001 Feature Workspace Protocol v1 and
installed adapter; Python standard library; `uv`; Archify 2.14; the existing Docusaurus publication
pipeline

**Storage**: Maintained bundle/preset/extension sources; generated `dist/` archives and catalogs;
project-scoped Spec Kit component registries and registered agent command files in isolated targets;
project-authored `.concorde/` and `specs/` sources; generated Archify/Docusaurus projections

**Testing**: Python `unittest` with subprocess calls to the real Specify CLI; reproducible ZIP/catalog
hashes; clean temporary targets outside the repository; installed command-surface inventory and
bootstrap execution; full path matrix in Codex skills and one slash-command integration; update,
disable, priority, removal, rollback, and source-hash assertions; Archify showcase validation;
Docusaurus `npm run check`; human SC-001/SC-007 protocols

**Target Platform**: Spec Kit 0.16.4 projects on Windows, macOS, and Linux with Python 3.11+ and a
supported active coding-agent integration

**Project Type**: Versioned Spec Kit ecosystem distribution: one bundle recipe, one preset, one
extension, three catalogs, deterministic release tooling, and acceptance fixtures; no server in the
product

**Performance Goals**:

- at least 90% of first-time maintainers inspect and install the starter within 15 minutes;
- preview and installation agree on component IDs/versions for every supported source form;
- three repeat installs produce one unchanged component set and zero user-source mutations;
- all supported presentations materialize nine normal and five Concorde-specific command surfaces;
- every phase-path matrix run produces zero root plan/task copies or symlinks;
- missing release inputs and every seeded failure stop without a false success record;
- disable and reprioritize preserve all nine registered winners while changing future resolution;
  update/removal materialize the accepted or next surviving layer with no stale Concorde instructions

**Constraints**:

- use only public Spec Kit 0.16.4 bundle, preset, extension, and command-registration mechanisms;
- preset command replacement is supported; preset delivery of replacement core scripts is not assumed;
- no direct mutation of managed `.specify/scripts/` or locally installed core skills;
- no dependence on the Concorde checkout's `.agents/`, `.specify/`, source tree, or Python import path;
- normal Spec Kit phase names and meanings remain authoritative;
- Feature 001 owns workspace/command semantics; Feature 003 owns their distribution and presentation;
- command winner, source package, handoff digest, and execution receipt must remain traceable;
- release building writes `--base-url` metadata and never contacts it;
- project-authored `.concorde/`, `specs/`, and `docs/` content is never component-owned;
- diagrams are supplemental maintained sources, and generated HTML remains a projection

**Scale/Scope**: Three release units at one pinned version, three catalogs, three template layers,
nine existing command replacements, five extension commands, two agent presentation families, four
bundle source forms, and the complete install/update/remove lifecycle

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1. The former late append-only command state
has been replaced by the public nine-command `replace` composition described below.*

| Principle or gate | Design response | Status |
|---|---|---|
| I. Workflow product and proving ground | Acceptance installs built archives into checkout-isolated targets and executes the same handoff used by Concorde itself. Local skills are explicitly insufficient. | PASS |
| II. Spec Kit-native and composable | Templates remain append layers; nine path-sensitive commands use the documented preset `replace` strategy; extension commands/runtime use the extension manager; bundle lifecycle remains native. Core-script replacement is prohibited. | PASS — CLEAN-INSTALL PROOF RECORDED |
| III. Recursive, bounded architecture | Distribution does not change hierarchy semantics; installed commands delegate to Feature 001's bounded workspace and context contracts. | PASS |
| IV. Explicit ownership and feature alignment | Distribution packages the bundle; Spec Kit Integration owns preset/extension composition; both child features refine Feature 003. Feature 001 owns workspace semantics through a separate child refinement. | PASS |
| V. Contracts govern every boundary | Bundle lifecycle, ecosystem explanation, installed command surfaces, Feature Workspace handoff, agent skills, and Spec Kit platform contracts identify roles, failures, compatibility, and evidence. | PASS |
| VI. One authority per fact | Manifests own package content; Feature 001 owns command/path meaning; preset sources own installed override instructions; generated catalogs and registered files are projections with provenance. | PASS |
| VII. Deterministic validation and reviewed evidence | Release hashes, winner resolution, bootstrap execution, phase paths, source isolation, lifecycle restoration, diagrams, and docs are deterministic. Human comprehension remains separate evidence. | PASS |
| Architecture documentation standards | Both Feature 003 diagrams remain text-backed supplemental views under `diagrams/`; root architecture remains one-level and bounded. | PASS |

No constitutional exception is planned. If public command replacement cannot establish routing before
the lower core workflow would select legacy paths, implementation stops and records the required
upstream Spec Kit capability/version; it must not fall back to installer patching.

## Architecture and Ownership

### Participating refinements

| Module | Child feature | Responsibility in this attempt |
|---|---|---|
| `module.concorde.distribution` | `feature.distribution.package-starter-bundle` | Reproducible archives/catalogs, exact pins, preview/install parity, provenance, update/removal, rollback, and clean-target isolation. |
| `module.concorde.spec-kit-integration` | `feature.integration.compose-starter-workflow` | Three template layers, nine authoritative normal-command replacements, five extension command registrations, active-integration rendering, and lower-layer restoration. |

`feature.integration.manage-feature-workspace` refines Feature 001 and supplies the protocol/runtime
handoff consumed here. Architecture Core behavior is packaged but not redefined. Documentation only
publishes the already declared Feature 003 diagrams through Feature 002.

### Boundary contracts

| Contract | Authority and use |
|---|---|
| `contract.concorde.spec-kit-installation` | Root user-facing installation, verification, update, and removal obligation. |
| `contract.distribution.bundle-lifecycle` | Exact native bundle operations, ownership, rollback, and source preservation. |
| `contract.integration.workflow-composition` | Template/command composition without changing normal phase meaning. |
| `contract.integration.agent-skills` | Presentation-neutral command intent and registered agent forms. |
| `contract.integration.spec-kit-platform` | Required public Spec Kit 0.16.4 behavior. |
| `contract.integration.feature-workspace` | Feature 001-owned workspace and phase-path semantics consumed by installed surfaces. |
| `contracts/installed-command-surfaces.md` | Feature-local inventory, winner, bootstrap-order, isolation, and restoration profile. |

## Project Structure

### Documentation and design artifacts

```text
specs/concorde/features/003-install-concorde-speckit/
├── spec.md
├── diagrams/
│   ├── spec-kit-component-model.json
│   └── starter-installation-flow.json
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── bundle-distribution.md
│   ├── ecosystem-explanation.md
│   └── installed-command-surfaces.md
└── implementation/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md              # regenerate after this plan
    └── validation.md         # reset mappings for FR-001..029 and SC-001..011
```

### Distribution sources and tests

```text
bundles/concorde-starter/
├── bundle.yml
└── README.md

presets/concorde-core/
├── preset.yml
├── templates/               # three append-composed lifecycle templates
└── commands/                # nine complete existing-command replacements

extensions/concorde/
├── extension.yml
├── commands/                # five Concorde-specific command sources
├── scripts/                 # installed launchers + workspace adapter
└── runtime/concorde/        # Feature 001 deterministic behavior

scripts/release/
├── build-components.py
└── verify-release.py

catalogs/
├── bundles.json
├── presets.json
└── extensions.json

tests/concorde/
├── support/
│   ├── catalog_server.py
│   ├── installed_command_surface.py
│   └── specify_project.py
├── contract/
│   ├── test_manifests.py
│   ├── test_release_artifacts.py
│   └── test_installed_command_surfaces.py
├── integration/
│   ├── test_bundle_lifecycle.py
│   ├── test_command_recomposition.py
│   └── test_clean_phase_matrix.py
└── acceptance/
    ├── test_installed_codex_workflow.py
    └── test_installed_slash_workflow.py
```

`.agents/skills/` and project-root `.specify/` remain self-hosting inputs for this repository and are
deliberately absent from release archive construction.

## Implementation Strategy

### Phase 1: Freeze the Feature 001 handoff and baseline the failure

1. Record the Feature Workspace Protocol version, source digest, nine normal phase obligations, five
   Concorde command intents, and installed-relative adapter/runtime paths.
2. Add a regression fixture demonstrating the current defect: an appended routing addendum appears
   after a lower command step has already selected a root-level plan/task path.
3. Make the failure explicit in validation evidence; do not mark Feature 003 implemented because the
   preset and extension happen to register.

### Phase 2: Replace the nine normal command surfaces authoritatively

1. Keep template entries append-composed; change each of the nine command entries to the public
   `replace` strategy.
2. Author a complete command for each normal phase that preserves its Spec Kit responsibility but
   invokes the installed workspace adapter before any path-sensitive setup or prerequisite check.
3. Route specify/clarify/checklist to durable root artifacts and plan/tasks/implement/analyze/
   converge/taskstoissues to the single `implementation/` workspace.
4. Reject an invalid, missing, ambiguous, or incompatible handoff before producing an artifact.
5. Maintain a compatibility map to the Spec Kit 0.16.4 core command semantics; version expansion
   requires reviewing every replacement against the new upstream command.

### Phase 3: Package the five Concorde-specific intents and runtime

1. Ensure the extension manifest declares init, feature create/select, context, and validate plus all
   launchers, workspace adapter, and deterministic runtime files they reference.
2. Resolve every runtime path relative to the installed extension root; prohibit checkout-relative
   imports and undeclared source dependencies.
3. Keep platform-safe registered spellings presentation details only; canonical IDs and result
   contracts remain Feature 001 authority.

### Phase 4: Rebuild reproducible release units and catalogs

1. Build separate preset, extension, and bundle archives from explicit source allowlists.
2. Verify manifests, catalogs, ZIP member lists, semantic versions, compatibility ranges, download
   URLs, and SHA-256 digests agree.
3. Prove `--base-url` is serialized metadata and is not contacted during build.
4. Ensure none of `.agents/`, root `.specify/`, tests, temporal feature implementation files, or
   generated site outputs enter a release archive.

### Phase 5: Execute installed command surfaces in isolated targets

1. Build and serve the release, then initialize clean targets outside the checkout for Codex skills
   and one slash-command integration.
2. Install only through catalogs/built archives and inventory the materialized winning artifacts:
   nine normal plus five Concorde-specific surfaces.
3. For each surface, bind the registered artifact to its package source and handoff digest, execute
   its installed workspace bootstrap, then exercise the phase outcome against a nested feature.
4. Assert the complete durable/temporal matrix, zero root aliases/symlinks, equivalent result/failure
   behavior across presentations, and zero reads from the checkout.
5. Remove one required archive member at a time and prove acceptance fails rather than falling back to
   local state.

### Phase 6: Prove recomposition and lifecycle safety

1. Stack a lower-priority core command layer and verify Concorde wins while enabled.
2. Disable and reprioritize `concorde-core`; assert all nine registered surfaces remain active while
   future resolution changes, matching Spec Kit 0.16.4.
3. Update and remove `concorde-core`; assert all nine surfaces materialize the accepted update or
   restore the correct surviving lower layer with no stale Concorde text.
4. Repeat install three times; verify one bundle/preset/extension record and unchanged user sources.
5. Exercise shared-component retention, local source forms, compatible update, digest failure,
   command collision, partial rollback, and unsupported-version refusal.

### Phase 7: Reconcile architecture, diagrams, documentation, and human evidence

1. Update module/refinement status and evidence only after clean installed receipts exist.
2. Validate and deliver both Feature 003 diagrams; verify declaration-driven feature-page embedding,
   source provenance, and freshness. Browser visual review remains pending when Chrome is unavailable.
3. Run the full Python, release, self-validation, Archify, and docsite gates.
4. Conduct SC-001 installation and SC-007 ecosystem-role pilots with real first-time maintainers;
   never infer them from automated checks.

## Feature Diagram Strategy

| View | Question and participants | Contracts/text | Delivery and evidence |
|---|---|---|---|
| `diagrams/spec-kit-component-model.json` | How catalogs, Spec Kit, bundle, preset, extension, resolved core commands, active integration, Architecture Core, clean specs tree, and excluded self-hosting files relate. | `spec.md` role table, ecosystem explanation, bundle lifecycle, workflow composition, agent skills, and Feature Workspace handoff. | Deliver `generated/architecture/concorde-spec-kit-component-model.html`; require 9/9 showcase checks, source digest/provenance, automatic feature-page embedding, and truthful visual receipt. |
| `diagrams/starter-installation-flow.json` | How maintained package sources become archives/catalogs, an accepted plan, installed components, 14 materialized surfaces, and clean-target execution. | User Stories 1–4 plus bundle distribution and installed command surface contracts. | Deliver `generated/architecture/concorde-starter-installation-flow.html` with the same validation, publication, freshness, and visual-evidence rules. |

The diagrams remain supplemental Feature 003 sources. They may explain package/runtime detail but
cannot add module ownership or behavior absent from textual contracts, and they never replace root
`architecture.json`.

## Test and Evidence Strategy

| Requirement area | Evidence |
|---|---|
| Package identity and preview parity | Native validation/info/install across catalog, directory, manifest, and archive forms; exact ID/version comparison. |
| Nine normal overrides | Registered winner/source inventory, pre-path bootstrap ordering, complete phase execution, and durable/temporal path assertions. |
| Five Concorde commands | Installed-relative launcher/runtime execution and Feature 001 contract conformance in both presentations. |
| Checkout isolation | Temporary target outside repository, sanitized environment/import path, filesystem access audit, and missing-member negative fixtures. |
| Host lifecycle | Enable/disable/priority preserve registered winners; update/remove verify accepted or lower-layer hashes for all nine commands. |
| Release reproducibility | Two-build byte equality, ZIP allowlists, manifest/catalog parity, and digests. |
| Safety and rollback | Unsupported host, trust refusal, missing/digest/collision/materialization failures, previous-record retention, and residual-state diagnostics. |
| User-source preservation | Before/after hashes for `.concorde/`, `specs/`, `docs/`, and configuration across install/update/remove/failure. |
| Diagrams/docs | Both declared sources pass Archify showcase/delivery/freshness; docsite validates and embeds both canonical outputs. |
| Human outcomes | Timed SC-001 setup pilot and five-minute SC-007 role/lifecycle comprehension protocol. |

## Post-Design Constitution Re-check

Phase 1 separates workflow meaning from delivery mechanics, chooses only supported Spec Kit package
and command contracts, prohibits core-script mutation, and makes checkout isolation an acceptance
property. The design adds a durable installed-command-surface profile, explicit Feature 001 handoff
digest, reproducible release boundaries, and separate automated/human evidence. The two maintained
diagrams align with the same package/use-time model and remain supplemental.

The current append-only preset and string-presence tests do not satisfy the plan; their `partial`
status is intentional. No compatibility expansion or evidence upgrade occurs until clean archive
installation and the complete command/lifecycle matrix pass.

## Complexity Tracking

| Added complexity | Why needed | Containment |
|---|---|---|
| Nine complete command replacements | A late append cannot prevent lower core instructions from choosing legacy root paths. | Locked to Spec Kit 0.16.4, one compatibility map, one shared workspace bootstrap contract. |
| Installed command-surface harness | Agent command files are presentation artifacts; package presence or matching snippets cannot prove path behavior. | Executes only the declared bootstrap and bounded phase outcomes from installed artifacts. |
| Two presentation families | Integration rendering may alter file format or invocation syntax. | One skills and one slash fixture share the same canonical inventory and result assertions. |

These are contained implementation costs, not constitutional exceptions.
