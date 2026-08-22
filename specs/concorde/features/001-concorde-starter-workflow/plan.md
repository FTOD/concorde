# Implementation Plan: Install Concorde Starter Bundle

**Working branch**: `main` (existing-feature update; no feature branch was created) | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/concorde/features/001-concorde-starter-workflow/spec.md`

## Summary

Deliver Concorde's first usable vertical slice as three independently valid Spec Kit ecosystem
artifacts: the `concorde-core` append-only preset, the `concorde` command extension, and the
`concorde-starter` bundle that pins exactly those two components. The extension registers
`speckit.concorde.init`, `speckit.concorde.context`, and `speckit.concorde.validate` for the active
agent integration. Those installed command surfaces coordinate a dependency-free Python 3.11
runtime that proposes or creates a root specification hierarchy under `specs/<root-slug>/`, emits a
one-level context projection, and deterministically validates Concorde sources. Module specifications, boundary
contracts, Archify JSON, and module-owned feature workspaces share that hierarchy without sharing
canonical responsibilities. Component and bundle catalogs remain the standard release/discovery
mechanism; acceptance fixtures serve the same artifacts from a local HTTP catalog so development and
release exercise the native Spec Kit lifecycle without a Concorde-specific installer. Plain-language
documentation and two supplemental Archify views distinguish that install-time composition from the
two use-time paths: preset guidance through normal Spec Kit phases and extension commands through the
active coding-agent integration. Those explanations add no workflow component, runtime capability,
or second source of feature authority.

## Technical Context

**Language/Version**: Python 3.11+ for deterministic runtime and acceptance tooling; Markdown with
YAML front matter and JSON for maintained architecture sources; YAML/JSON manifests defined by Spec
Kit 0.16.4

**Primary Dependencies**: Spec Kit/Specify CLI 0.16.4 public bundle, preset, extension, catalog, and
agent-registration contracts; `uv` for the repository development environment; Python standard
library only in the installed Concorde runtime; the existing Archify renderer and Docusaurus
publication pipeline for non-runtime explanatory views

**Storage**: Project-scoped files: Spec Kit registries and provenance under `.specify/`, Concorde
configuration under `.concorde/`, maintained architecture and canonical feature specifications under
the unified `specs/` hierarchy, supplemental explanatory Archify JSON beside Feature 001,
reproducible HTML and visual-review evidence under `generated/architecture/`, and disposable release
artifacts under `dist/`

**Testing**: Python `unittest` for unit, contract, integration, and acceptance tests;
subprocess-driven calls to the real Spec Kit/Specify CLI for native lifecycle behavior and
clean-project fixtures in Codex skills mode and one slash-command integration; Archify showcase validation and desktop visual
review; Docusaurus source, route, freshness, test, and production-build gates; a timed human
comprehension pilot for outcomes automation cannot establish

**Target Platform**: Windows, macOS, and Linux environments supported by Spec Kit 0.16.4, with an
active supported coding-agent integration and Python 3.11+

**Project Type**: Spec Kit ecosystem integration comprising an independently packaged preset and
extension plus a bundle recipe that pins them; the extension carries a project-local deterministic
CLI runtime

**Performance Goals**: Complete the documented clean install-to-first-validation journey in under 10
minutes; produce byte-equivalent structured findings across three unchanged validation runs; return
only the requested one-level bounded context; enable at least 90% of first-time pilot maintainers to
identify the bundle, preset, extension, and catalog roles after no more than five minutes of review

**Constraints**: Exactly one preset and one extension; no workflow or reusable step component; no
parallel Concorde feature specification; no LLM in validation or context projection; no overwrite of
maintained intent without explicit approval; Spec Kit 0.16.4 is the only advertised platform version
for this release; release installation uses approved catalogs and HTTPS artifacts; explanatory text
must remain complete without diagrams; supplemental views must not become normative package
manifests or canonical module-level views

**Scale/Scope**: One project architecture hierarchy per target project; starter validation covers
modules, features, contracts, scenarios, references, refinement, evidence status, and one-level views;
three agent commands; clean-project lifecycle fixtures for install, repeat install, update, and remove;
two supplemental diagrams covering ecosystem composition and release-to-use flow

## Constitution Check

*GATE: Passed before Phase 0 research; re-checked after Phase 1 design.*

| Principle or gate | Design response | Status |
|---|---|---|
| I. Workflow product and proving ground | Acceptance installs the same bundle into clean fixtures, uses its commands, and validates Concorde's own hierarchy. The implemented validator removes the earlier bootstrap-only manual exception. | PASS |
| II. Spec Kit-native and composable | Uses public bundle, preset, extension, catalog, and integration contracts. The preset appends to core artifacts; each feature keeps one canonical Spec Kit `spec.md` inside the module-owned hierarchy. | PASS |
| III. Recursive, bounded architecture | `context` and validation enforce exactly the current module's I/O and features plus immediate children and their I/O, permitted externals, current-level scenarios, and navigation references. | PASS |
| IV. Explicit ownership and feature alignment | The root feature remains owned by `module.concorde`; adjacent-level refinements in Distribution, Spec Kit Integration, and Architecture Core own their narrower outcomes. Documentation consumes supplemental views without claiming feature ownership. | PASS |
| V. Contracts govern every boundary | Phase 1 defines the bundle, command, architecture-source, runtime request/result, and ecosystem-explanation interfaces. Child-module contracts and representative examples carry implementation evidence. | PASS |
| VI. One authority per fact | Spec Kit `spec.md` stays canonical for feature behavior; component manifests own package identity and contents; Markdown owns explanatory semantics; Archify JSON owns visual composition; code owns behavior; generated HTML and reports remain reproducible projections. | PASS |
| VII. Deterministic validation and reviewed evidence | Runtime operations are standard-library Python with sorted traversal and stable JSON. `init` separates proposal from apply, and maintained-source writes require explicit approval. | PASS |
| Ecosystem compatibility | Version range is pinned to the tested 0.16.4 line. Components are independently packaged and resolved through install-allowed catalogs before the bundle is installed. | PASS |
| Pre-implementation architecture gate | Root ownership, participating immediate submodules, contracts, source locations, and expected architecture updates are explicit in this plan. | PASS |
| Architecture documentation standards | Standalone prose carries the complete explanation; the two supplemental view sources are validated, published with provenance, and kept separate from the canonical root module view. | PASS |

### Post-Design Re-check

Phase 1 preserves every pre-design gate. The contracts assign authority by artifact meaning rather
than by a separate top-level directory, the data model separates intended architecture from
installation and validation evidence, and the quickstart tests the native lifecycle rather than a
private launcher. The explanation profile keeps package facts authoritative in manifests/contracts,
textual meaning in Markdown, visual composition in Archify JSON, and HTML as generated output. The
three child feature specifications and affected module contracts now exist, self-validation passes,
the supplemental views pass showcase and desktop review, and the generated site publishes them. No
constitutional exception is required. Only the timed participant evidence for SC-001, SC-009, and
SC-011 remains non-automatable.

## Architecture and Ownership

The root feature spans three immediate submodules and is therefore correctly owned by
`module.concorde`. The implemented design uses these adjacent-level refinements:

| Providing module | Child feature | Canonical feature workspace | Responsibility in this slice |
|---|---|---|---|
| `module.concorde.distribution` | `feature.distribution.package-starter-bundle` | `specs/concorde/modules/distribution/features/001-package-starter-bundle/` | Package, publish, preview, install, update, and remove the pinned component set. |
| `module.concorde.spec-kit-integration` | `feature.integration.compose-starter-workflow` | `specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/` | Append Concorde guidance to core phases and register the three portable agent commands. |
| `module.concorde.architecture-core` | `feature.architecture-core.manage-bounded-sources` | `specs/concorde/modules/architecture-core/features/001-manage-bounded-sources/` | Initialize, retrieve, and validate the maintained specification hierarchy deterministically. |

The root `install-starter-workflow` scenario remains the cross-module orchestration scenario. Child
feature specifications refine it and may describe their internal behavior without expanding child
details in `specs/concorde/architecture.json`.

At the root level, the visible model is limited to Concorde's own features and boundary contracts,
all immediate submodules (including non-participating siblings), each submodule's I/O contracts,
permitted external actors, and their organization. Child feature bodies are navigation targets, not
root-view content. Selecting one of the three participating child modules repeats the same rule at
that module; because all three are leaves in this slice, each child view consists of its own contracts
and features without inventing deeper structure. Scenarios illustrate representative behavior across
those visible participants; they do not replace the feature's textual definition.

### Spec Kit Ecosystem Roles

| Role | Ownership in this feature |
|---|---|
| Spec Kit | Owns component resolution, template composition, lifecycle operations, registries, provenance, and active-integration selection. |
| Catalog | Supplies discovery and trust metadata for independently versioned bundle, preset, and extension archives. |
| Bundle | Is a passive recipe that pins one preset and one extension; it contains no executable workflow or runtime. |
| Preset | Adds passive, append-only guidance when Spec Kit resolves the normal `specify`, `plan`, and `tasks` templates. |
| Extension | Owns the three active command definitions and their deterministic project-local runtime. |
| Active coding-agent integration | Renders and registers the commands using that agent's native presentation and invocation syntax; it does not own Concorde behavior. |
| Architecture Core | Owns the deterministic `init`, `context`, and `validate` behavior invoked by extension commands. |

### Supplemental Explanation Views

The maintained `spec-kit-component-model.json` answers the structural question “what are the
ecosystem parts and who owns what?” The maintained `starter-installation-flow.json` answers the
temporal question “what happens from release through install, and which of the two paths runs during
use?” Both are Feature-001-owned Archify sources with complete textual counterparts in `spec.md`,
`quickstart.md`, this plan, and the relevant platform/workflow contracts. They are supplemental views,
not module-owned `architecture.json` files, and therefore do not weaken the hierarchical one-level
visibility rule or add participants to the canonical root view.

## Project Structure

### Documentation (this feature)

```text
specs/concorde/features/001-concorde-starter-workflow/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── validation.md
├── spec-kit-component-model.json
├── starter-installation-flow.json
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── agent-commands.md
│   ├── architecture-service.schema.json
│   ├── architecture-sources.md
│   ├── bundle-distribution.md
│   ├── ecosystem-explanation.md
│   └── examples/
│       ├── context-response.json
│       └── validation-response.json
└── tasks.md
```

### Source Code (repository root)

```text
bundles/
└── concorde-starter/
    ├── bundle.yml
    └── README.md

presets/
└── concorde-core/
    ├── preset.yml
    ├── README.md
    └── templates/
        ├── spec-template.md
        ├── plan-template.md
        └── tasks-template.md

extensions/
└── concorde/
    ├── extension.yml
    ├── README.md
    ├── commands/
    │   ├── speckit.concorde.init.md
    │   ├── speckit.concorde.context.md
    │   └── speckit.concorde.validate.md
    ├── scripts/
    │   ├── bash/concorde.sh
    │   ├── powershell/concorde.ps1
    │   └── python/concorde.py
    └── runtime/
        └── concorde/
            ├── __init__.py
            ├── __main__.py
            ├── cli.py
            ├── context.py
            ├── diagnostics.py
            ├── frontmatter.py
            ├── initialize.py
            ├── model.py
            ├── repository.py
            └── validate.py

catalogs/
├── bundles.json
├── extensions.json
└── presets.json

scripts/
└── release/
    ├── build-components.py
    └── verify-release.py

tests/
└── concorde/
    ├── acceptance/
    │   ├── test_codex_skills.py
    │   ├── test_preset_workflow.py
    │   ├── test_slash_commands.py
    │   └── test_starter_journey.py
    ├── contract/
    │   ├── test_agent_commands.py
    │   ├── test_manifests.py
    │   ├── test_release_artifacts.py
    │   └── test_structured_results.py
    ├── integration/
    │   ├── test_bundle_lifecycle.py
    │   ├── test_context.py
    │   ├── test_initialize.py
    │   ├── test_preset_composition.py
    │   ├── test_self_architecture.py
    │   └── test_validation.py
    ├── unit/
    │   ├── test_frontmatter.py
    │   ├── test_repository.py
    │   └── test_rules.py
    ├── fixtures/
    │   ├── valid-project/
    │   ├── invalid-projects/
    │   ├── context-project/
    │   └── releases/
    └── support/
        ├── catalog_server.py
        ├── paths.py
        └── specify_project.py

generated/architecture/
├── concorde-root.html
├── concorde-spec-kit-component-model.html
├── concorde-starter-installation-flow.html
└── *.visual-check.*                 # reproducible containment and review receipts

specs/concorde/
├── module.md
├── architecture.json
├── contracts/
├── features/
│   └── 001-concorde-starter-workflow/
│       └── ...                      # this feature workspace
└── modules/
    ├── distribution/
    │   ├── module.md
    │   └── features/001-package-starter-bundle/spec.md
    ├── spec-kit-integration/
    │   ├── module.md
    │   └── features/001-compose-starter-workflow/spec.md
    ├── architecture-core/
    │   ├── module.md
    │   └── features/001-manage-bounded-sources/spec.md
    └── documentation/               # implementation is out of scope; its existing site publishes the views
```

**Structure Decision**: Keep each distributable Spec Kit primitive at the repository root in the
same shape as the upstream examples. The extension directory is the canonical runtime package so the
installed copy contains everything its agent commands need. Catalogs describe released archives but
do not duplicate component behavior. Tests are grouped outside release assets and exercise source
packages, built archives, and installed copies. Architecture and feature sources stay under one
self-similar `specs/` hierarchy and are updated as maintained intent, not generated from
implementation. Path patterns identify artifact kinds; directory separation does not create a
second authority for feature behavior. The two supplemental JSON sources author visual composition
for their specific explanatory questions; their generated HTML, screenshots, and receipts are
reproducible projections/evidence and are never edited as maintained intent.

## Realized Implementation Strategy

1. Author and validate the `concorde-core` preset as three append-only template fragments. Each
   fragment adds Concorde metadata or gates while retaining the complete lower-priority Spec Kit
   template.
2. Implement the dependency-free runtime with a strict project-root boundary, deterministic path and
   ID indexes, stable diagnostics, and explicit proposal/apply separation for initialization.
3. Author the three extension command prompts as thin orchestration layers over the runtime. Use
   integration-neutral command references and Spec Kit script-path substitution; never encode one
   agent's invocation syntax as canonical behavior.
4. Package preset and extension archives, publish matching install-allowed catalog entries, then pin
   those versions in `concorde-starter/bundle.yml`. The bundle contains no workflow or step.
5. Exercise validation, build, info, install, list, update, and remove through the Specify CLI against
   clean temporary projects and a local HTTP catalog. Verify ownership/refcount behavior and rollback
   diagnostics using the real primitive managers.
6. Create the three adjacent child feature specifications before implementing their narrower
   outcomes; update the affected root and child module, contract, and view sources; run the Concorde
   validator against this repository; and refresh Archify outputs only after maintained intent passes
   review.
7. Align the plain-language role model across the feature, quickstart, root module, Distribution, and
   Spec Kit Integration documents; author and render the separate component and workflow views;
   validate and visually review them; and publish the generated HTML through the existing docsite.
   Do not add rendering or publication commands to the starter bundle.

## Test and Evidence Strategy

- Unit tests cover constrained front-matter parsing, stable sorting, ID/path lookup, containment,
  refinement cycles, and rule diagnostics.
- Contract tests validate all three Spec Kit manifests, command names, structured result schema,
  source profile, and exact bundle component cardinality.
- Integration tests call runtime operations against valid and seeded-invalid hierarchies and assert
  no maintained-source writes from context or validation.
- Lifecycle tests use the real Spec Kit 0.16.4 CLI and local install-allowed catalogs to compare
  `bundle info --json` with installed records, repeat install three times, update, inject failure, and
  remove while preserving user-authored architecture sources and shared components.
- Agent acceptance installs into Codex skills mode and one slash-command integration, asserts native
  command artifacts and invocation syntax, and completes the primary scenario for every command.
- Self-application evidence validates Concorde's own unified specification hierarchy and records the
  implemented automated evidence while retaining `partial` status for the pending human outcomes.
- Explanation review traces every FR-029 role and boundary to the feature prose, manifests, module
  contracts, and both supplemental views; Archify sources must pass all showcase checks, remain
  contained at four desktop viewport sizes, pass light/dark perceptual review, and generate fresh
  outputs with provenance. The Docusaurus `npm run check` gate verifies source discovery, routes,
  links, freshness, automated tests, and a production build.
- SC-011 remains human evidence: after at most five minutes with the explanation, first-time
  maintainers answer four role questions (bundle, preset, extension, catalog) and explain that normal
  Spec Kit phases remain unchanged. At least 90% must answer all five prompts correctly; automated
  diagram or documentation checks cannot substitute for this pilot.

## Complexity Tracking

No constitution violations or exceptional complexity are required.
