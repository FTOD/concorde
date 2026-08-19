# Implementation Plan: Install Concorde Starter Bundle

**Branch**: `001-concorde-starter-workflow` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-concorde-starter-workflow/spec.md`

## Summary

Deliver Concorde's first usable vertical slice as three independently valid Spec Kit ecosystem
artifacts: the `concorde-core` append-only preset, the `concorde` command extension, and the
`concorde-starter` bundle that pins exactly those two components. The extension registers
`speckit.concorde.init`, `speckit.concorde.context`, and `speckit.concorde.validate` for the active
agent integration. Those skills coordinate a dependency-free Python 3.11 runtime that proposes or
creates a root architecture package, emits a one-level context projection, and deterministically
validates Concorde sources. Component and bundle catalogs remain the standard release/discovery
mechanism; acceptance fixtures serve the same artifacts from a local HTTP catalog so development and
release exercise the native Spec Kit lifecycle without a Concorde-specific installer.

## Technical Context

**Language/Version**: Python 3.11+ for deterministic runtime and acceptance tooling; Markdown with
YAML front matter and JSON for maintained architecture sources; YAML/JSON manifests defined by Spec
Kit 0.16.4

**Primary Dependencies**: Spec Kit/Specify CLI 0.16.4 public bundle, preset, extension, catalog, and
agent-registration contracts; `uv` for the repository development environment; Python standard
library only in the installed Concorde runtime

**Storage**: Project-scoped files: Spec Kit registries and provenance under `.specify/`, Concorde
configuration under `.concorde/`, maintained architecture under `architecture/`, canonical feature
specifications under `specs/`, and disposable release artifacts under `dist/`

**Testing**: Python `unittest` for unit and contract tests; Spec Kit's pytest/Typer harness where
native lifecycle behavior must be exercised; subprocess-driven clean-project acceptance fixtures for
Codex skills mode and one slash-command integration

**Target Platform**: Windows, macOS, and Linux environments supported by Spec Kit 0.16.4, with an
active supported coding-agent integration and Python 3.11+

**Project Type**: Ecosystem bundle containing one preset, one command extension, and a project-local
deterministic CLI runtime

**Performance Goals**: Complete the documented clean install-to-first-validation journey in under 10
minutes; produce byte-equivalent structured findings across three unchanged validation runs; return
only the requested one-level bounded context

**Constraints**: Exactly one preset and one extension; no workflow or reusable step component; no
parallel Concorde feature specification; no LLM in validation or context projection; no overwrite of
maintained intent without explicit approval; Spec Kit 0.16.4 is the only advertised platform version
for this release; release installation uses approved catalogs and HTTPS artifacts

**Scale/Scope**: One project architecture hierarchy per target project; starter validation covers
modules, features, contracts, scenarios, references, refinement, evidence status, and one-level views;
three agent commands; clean-project lifecycle fixtures for install, repeat install, update, and remove

## Constitution Check

*GATE: Passed before Phase 0 research; re-checked after Phase 1 design.*

| Principle or gate | Design response | Status |
|---|---|---|
| I. Workflow product and proving ground | Acceptance installs the same bundle into clean fixtures and uses its own commands against Concorde-style sources. Bootstrap-only manual architecture review is recorded until the validator exists. | PASS |
| II. Spec Kit-native and composable | Uses public bundle, preset, extension, catalog, and integration contracts. The preset appends to core artifacts; it does not fork the lifecycle or create another spec. | PASS |
| III. Recursive, bounded architecture | `context` and validation enforce exactly the current module plus immediate children, contracts, permitted externals, scenarios, and refinement links. | PASS |
| IV. Explicit ownership and feature alignment | The root feature remains owned by `module.concorde`; implementation adds adjacent-level refining features to Distribution, Spec Kit Integration, and Architecture Core. | PASS |
| V. Contracts govern every boundary | Phase 1 defines the bundle, command, architecture-source, and runtime request/result contracts. Implementation updates child-module contract documents and examples with evidence. | PASS |
| VI. One authority per fact | Spec Kit `spec.md` stays canonical for feature behavior; Markdown owns prose and IDs, JSON owns view structure, code owns behavior, and generated reports remain disposable evidence. | PASS |
| VII. Deterministic validation and reviewed evidence | Runtime operations are standard-library Python with sorted traversal and stable JSON. `init` separates proposal from apply, and maintained-source writes require explicit approval. | PASS |
| Ecosystem compatibility | Version range is pinned to the tested 0.16.4 line. Components are independently packaged and resolved through install-allowed catalogs before the bundle is installed. | PASS |
| Pre-implementation architecture gate | Root ownership, participating immediate submodules, contracts, source locations, and expected architecture updates are explicit in this plan. | PASS |

### Post-Design Re-check

Phase 1 preserves every pre-design gate. The contracts assign authority without duplication, the data
model separates intended architecture from installation and validation evidence, and the quickstart
tests the native lifecycle rather than a private launcher. No constitutional exception is required.
Before implementation is accepted, the root and three participating child-module sources must be
updated, Concorde validation must pass on them, and generated architecture outputs must be refreshed.

## Architecture and Ownership

The root feature spans three immediate submodules and is therefore correctly owned by
`module.concorde`. Implementation introduces these adjacent-level refinements:

| Providing module | Planned child feature | Responsibility in this slice |
|---|---|---|
| `module.concorde.distribution` | `feature.distribution.package-starter-bundle` | Package, publish, preview, install, update, and remove the pinned component set. |
| `module.concorde.spec-kit-integration` | `feature.integration.compose-starter-workflow` | Append Concorde guidance to core phases and register the three portable agent commands. |
| `module.concorde.architecture-core` | `feature.architecture-core.manage-bounded-sources` | Initialize, retrieve, and validate the maintained architecture package deterministically. |

The root `install-starter-workflow` scenario remains the cross-module orchestration scenario. Child
feature specifications refine it and may describe their internal behavior without expanding child
details in `architecture/concorde/architecture.json`.

## Project Structure

### Documentation (this feature)

```text
specs/001-concorde-starter-workflow/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent-commands.md
│   ├── architecture-service.schema.json
│   ├── architecture-sources.md
│   ├── bundle-distribution.md
│   └── examples/
│       ├── context-response.json
│       └── validation-response.json
└── tasks.md                         # Created later by $speckit-tasks
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
    │   ├── test_slash_commands.py
    │   └── test_starter_journey.py
    ├── contract/
    │   ├── test_agent_commands.py
    │   ├── test_manifests.py
    │   └── test_structured_results.py
    ├── integration/
    │   ├── test_bundle_lifecycle.py
    │   ├── test_context.py
    │   ├── test_initialize.py
    │   └── test_validation.py
    ├── unit/
    │   ├── test_frontmatter.py
    │   ├── test_repository.py
    │   └── test_rules.py
    ├── fixtures/
    │   ├── valid-project/
    │   ├── invalid-projects/
    │   └── context-project/
    └── support/
        └── catalog_server.py

architecture/concorde/
├── module.md
├── architecture.json
└── modules/
    ├── distribution/
    ├── spec-kit-integration/
    └── architecture-core/
```

**Structure Decision**: Keep each distributable Spec Kit primitive at the repository root in the
same shape as the upstream examples. The extension directory is the canonical runtime package so the
installed copy contains everything its agent commands need. Catalogs describe released archives but
do not duplicate component behavior. Tests are grouped outside release assets and exercise source
packages, built archives, and installed copies. Architecture sources stay under their existing
self-similar hierarchy and are updated as maintained intent, not generated from implementation.

## Implementation Strategy

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
6. Update the root and child architecture sources, run the new Concorde validator against this
   repository, and refresh Archify outputs only after maintained intent passes review.

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
- Self-application evidence validates Concorde's own architecture package and records unknown
  implementation evidence honestly until tests exist.

## Complexity Tracking

No constitution violations or exceptional complexity are required.
