# Concorde

Concorde extends [Spec Kit](https://github.com/github/spec-kit) with a hierarchical architecture
workflow for AI-developed software. It keeps feature specifications aligned with the module hierarchy
that realizes them, boundary contracts, bounded architecture views, and accepted implementation
evidence, so that a maintainer can understand any level of the project in minutes.

## Key features

- **Zoomable architecture** — start at the project, understand one module at a time, and descend only
  when the question needs more detail.
- **Architecture-aware specifications** — place each feature where all participating modules are
  visible, with stable IDs and explicit refinement relationships.
- **Bounded agent context** — retrieve one architectural level without silently loading child
  internals, unrelated features, or accepted implementation detail.
- **Human-readable contracts** — record boundary direction, exchanged information, obligations, and
  failure behavior alongside the modules and features that rely on them.
- **Durable intent, temporal attempts** — keep specifications and accepted realizations separate from
  disposable plans, tasks, research, validation, and in-progress implementation work.
- **Deterministic validation and review gates** — check hierarchy, references, contracts, diagrams,
  evidence, and generated-output freshness without an LLM; architecture and acceptance changes remain
  explicit human decisions.
- **One generated project read model** — publish the README, architecture, guides, feature abstracts,
  designs, accepted implementations, contracts, and interactive diagrams as a searchable Docusaurus
  site without turning generated pages into sources.

## Concorde commands

Concorde adds five agent-facing commands. Normal feature work still uses Spec Kit's standard
`$speckit-specify`, `$speckit-clarify`, `$speckit-plan`, `$speckit-tasks`,
`$speckit-implement`, `$speckit-analyze`, and `$speckit-converge` phases.

| Command | Use it to |
|---|---|
| `$speckit-concorde-init` | Propose a root Concorde architecture and apply it only after explicit approval. |
| `$speckit-concorde-context <module-or-feature-id>` | Retrieve exactly one bounded architectural level. |
| `$speckit-concorde-ask <question>` | Get a cited, read-only answer about Concorde or its use in the current project. |
| `$speckit-concorde-validate` | Deterministically validate the maintained hierarchy, contracts, views, documents, and evidence. |
| `$speckit-concorde-impl-accept <feature-id>` | Propose and, after explicit approval, accept a completed implementation as the durable realization. |

Features are created with the normal `$speckit-specify` phase at their canonical module path and
selected through `.specify/feature.json`; Concorde deliberately adds no separate create or select
command. See [Commands](docs/commands.md) for timing, inputs, outputs, and the installed execution
layers.

Explore the project through its three generated views:
[Architecture](specs/concorde/module.md), [Documentation](docs/index.md), and
[Features](specs/concorde/features/001-concorde-workflow/abstract.md).

## How Concorde fits Spec Kit

Concorde is designed to be installed as a native Spec Kit bundle containing:

- the `concorde-core` preset, which appends architecture guidance to Spec Kit's templates, supplies
  the feature abstract and design-reference templates, and replaces nine normal command instructions
  with Concorde-aware workspace routing;
- the `concorde` extension, which supplies five Concorde surfaces—four runtime-backed operations plus
  the read-only `ask` procedure—the workspace adapter, and runtime; and
- no replacement workflow: Spec Kit continues to own specification, planning, tasks, and
  implementation.

The three Spec Kit package concepts have different jobs:

| Concept | Concorde package | Role |
|---|---|---|
| Bundle | `concorde-bundle` | An installation recipe that pins the tested preset and extension versions. |
| Preset | `concorde-core` | Five templates (three append layers plus the `abstract-template` and `implementation-template` feature documents) and nine complete normal-command replacements for nested workspace routing. |
| Extension | `concorde` | Five Concorde-specific surfaces: four deterministic operations and one agent-followed, read-only question procedure. |

Catalogs are trusted discovery metadata for these independently versioned packages; they are not a
fourth installed runtime component. See the maintained
[component model](specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json),
[installation flow](specs/concorde/features/003-install-concorde-speckit/diagrams/bundle-installation-flow.json),
and the full [Feature 003 setup specification](specs/concorde/features/003-install-concorde-speckit/design.md).
The project docsite build turns module-owned and feature-declared diagram sources into interactive
standalone views.

## Project status

Feature 001 defines the Concorde architecture-aware development workflow. Its root initialization,
Feature Workspace Protocol v8 resolution of the standard Spec Kit selection, bounded context,
deterministic validation, approval-gated implementation acceptance, and the read-only `ask` procedure are
implemented and covered by the automated suites, and this repository itself lives under the
three-tier feature document model (`abstract.md`, `design.md`, `implementation.md`) and the module summary/design
reference pair that the feature specifies. Feature 002's docsite publication pipeline, Feature 003's
native bundle, preset composition, five-surface extension, and release tooling, and Feature 004's
review-first self-hosting are implemented and tested. Feature 005 adds the project-wide reflection
log (`specs/concorde/reflections.md`): every phase after specification records the difficulties it
meets there, attributed to the feature being worked on and naming the source concerned, and
acceptance cites a feature's open entries; its runtime, guidance, and evidence are in progress in this
checkout. Timed human comprehension pilots and browser-based diagram review remain pending and are
kept separate from automated evidence.

The newest published release is `v0.1.0`, which predates the module design reference, the feature
abstract, and the removal of the `feature.create`/`feature.select` commands. This README and the guides
under `docs/` describe the `0.4.0` sources in this checkout; until `0.4.0` is published, the local
build path below is the way to use them.

Concorde can also install the current checkout's framework sources into this repository for
development self-application. That review-first path is deliberately separate from the release
bundle used by other projects; see [Developing Concorde with Concorde](docs/self-hosting.md).

## Quick start: install Concorde as a Spec Kit bundle

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) for the repository's Python 3.11 development environment
- Spec Kit/Specify CLI 0.16.4, installed into the development environment by `uv sync`
- a supported coding-agent integration; Codex skills mode is the one exercised by the acceptance
  suite and by development self-hosting

Check the required versions:

```bash
uv --version
uv sync
source .venv/bin/activate
python --version
specify --version
```

`uv sync` creates the repository-local `.venv/` from `pyproject.toml` and `uv.lock`, including the
exact Spec Kit CLI version exercised by the acceptance suite. Activate that environment before using
the bare `specify` commands below. Concorde's installed bundle runtime remains Python 3.11
standard-library-only and does not require target projects to install `uv`.

The upstream Spec Kit repository is not vendored or included as a submodule. Maintained contracts
link to the supported `v0.16.4` documentation and source when implementation evidence is required.

### Install the published release

Projects that only want to use Concorde do not need this checkout. With the pinned Spec Kit CLI
installed (`uv tool install specify-cli==0.16.4`), register the published catalogs and install the
bundle from inside your project:

```bash
specify init --here --integration claude
base=https://github.com/FTOD/concorde/releases/download/v0.1.0
specify extension catalog add "$base/extensions.json" --name concorde --install-allowed
specify preset catalog add "$base/presets.json" --name concorde --install-allowed
specify bundle catalog add "$base/bundles.json" --id concorde
specify bundle install concorde-bundle
```

The current version and its catalog URLs are published at
`https://github.com/FTOD/concorde/releases/latest/download/release.json`; note the version caveat
under [Project status](#project-status). See the
[framework quick start](docs/quick-start.md) for the full walkthrough and
[Releasing Concorde](docs/releasing.md) for how releases are produced. The steps below build and
install the current local sources instead.

### 1. Build the local release

From a Concorde checkout:

```bash
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-bundle --output dist
uv run python scripts/release/verify-release.py --dist dist
```

The release contains exactly `concorde-core@0.4.0` and `concorde@0.4.0`. It does not install a custom
workflow or reusable Spec Kit steps. `--base-url` is written into the generated catalog metadata; the
builder does not contact it. The value must match the address that serves `dist/` in the next step.

### 2. Serve the local catalogs

In a second terminal:

```bash
uv run python tests/concorde/support/catalog_server.py --dist dist --port 8765
```

### 3. Initialize a target Spec Kit project

Use a new project directory, or run the equivalent command in an existing supported Spec Kit project:

```bash
project_root="$(mktemp -d)"
cd "$project_root"
specify init --here --integration codex --integration-options="--skills"
```

### 4. Install the local bundle

Set `concorde_checkout` to the absolute path of this repository:

```bash
concorde_checkout=/absolute/path/to/concorde
specify extension catalog add http://127.0.0.1:8765/extensions.json \
  --name concorde-dev --install-allowed
specify preset catalog add http://127.0.0.1:8765/presets.json \
  --name concorde-dev --install-allowed
specify bundle catalog add http://127.0.0.1:8765/bundles.json \
  --id concorde-dev --policy install-allowed
specify bundle validate --offline \
  --path "$concorde_checkout/bundles/concorde-bundle"
specify bundle info concorde-bundle --json
specify bundle install "$concorde_checkout/bundles/concorde-bundle/bundle.yml"
```

The information command previews the exact preset, extension, versions, compatibility range, and
project changes before installation. Verify the installed state:

```bash
specify bundle list --json
specify extension list
specify preset list
find .agents/skills -maxdepth 2 -name SKILL.md -print | sort
```

For the published-release installation, follow the [framework quick start](docs/quick-start.md);
release production and its acceptance evidence are described in [Releasing Concorde](docs/releasing.md)
and the [publish-release sub-feature](specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/design.md).

### 5. Use the Concorde commands

After installation, invoke these agent skills from the target project:

```text
$speckit-concorde-init
$speckit-concorde-impl-accept feature.<project-slug>.<name>
$speckit-concorde-context module.<project-slug>
$speckit-concorde-validate
$speckit-concorde-ask When should I use context instead of changing the selected feature?
```

- `init` proposes a root architecture package—`.concorde/config.json`, a `module.md` summary, a
  seeded `design.md` design reference, and a first level view at
  `architecture/diagrams/level-view.json`—and writes it only after explicit approval.
- Features are created with the normal `$speckit-specify` phase after exporting
  `SPECIFY_FEATURE_DIRECTORY` at their canonical path—`<module directory>/features/NNN-<short-name>`,
  or `<parent feature root>/subfeatures/NNN-<short-name>` for a sub-feature—and are selected
  through the standard `.specify/feature.json`; Concorde adds no creation or selection command.
  Every feature root owns `abstract.md` (read first), `design.md` (the authority), and
  `implementation.md` (the accepted implementation, written by acceptance).
- `impl.accept` proposes the feature `implementation.md`—and, when the attempt produced detail or
  rationale worth keeping, an amendment to the `design.md` of the module at which the feature is
  specified—from a task-complete implementation attempt and, only after explicit approval, applies
  both atomically and removes that temporal `attempt/` directory.
- `context` returns one bounded architectural level without expanding child internals or the body
  of any module `design.md` or feature `implementation.md`.
- `validate` deterministically checks identities, hierarchy, module layout, references, contracts,
  views, evidence status, module summary and feature abstract shape and reading budgets, and the feature-root document
  trio.
- `ask` answers questions about Concorde concepts, command timing, artifact authority, or this
  project's use of the workflow from cited installed guidance and bounded maintained sources. It is
  agent-followed and read-only: it has no Python runtime verb and does not execute recommended work.

Use `ask` whenever the uncertainty is about how Concorde itself works or applies to the current
project. Use `context` when you need the deterministic one-level architecture projection, and use
the normal Spec Kit phases when you intend to change specifications or implementation.

Project-authored `.concorde/` configuration and the unified `specs/` hierarchy are retained when the
bundle is updated or removed.

## Run this project's documentation site

The published site is available at [ftod.github.io/concorde](https://ftod.github.io/concorde/).
Every push to `main` rebuilds the canonical sources and deploys the verified output through the
repository's GitHub Pages workflow; generated site files are not committed.

The independent `docsite/` package, documented in the
[docsite contributor guide](docs/contributing/docsite.md), builds Concorde's own read-only Docusaurus
site from the root README and two canonical source trees, presented through a shared homepage and
three reader-facing navigation families:

| Source | Published content |
|---|---|
| `README.md` | The project homepage at `/`, including this same introduction, feature summary, and command overview |
| `specs/**/module.md`, its adjacent `design.md`, `specs/**/architecture/contracts/**/contract.md`, `specs/**/architecture/diagrams/*.json` | Architecture module summaries (each embedding its module-owned Archify diagrams), module design references, and boundary contracts |
| `docs/**/*.md` | Project documentation |
| Feature-root `abstract.md`, `design.md`, and `implementation.md` | Feature abstracts (the landing pages), behavioral designs, and accepted implementations |

Generated pages never become maintained source documents.

### Local preview

```bash
cd docsite
npm ci
npm run start
```

The preview validates all sources before starting. Open the local URL printed by Docusaurus, then use
the Architecture, Documentation, and Features sections in the navigation bar.

### Validate and build

```bash
cd docsite
npm run inspect
npm run validate
npm run build
```

The verified static site is promoted to `docsite/build/`. A failed build preserves the previous
successful output.

Run the complete project-docsite gate with:

```bash
cd docsite
npm run check
```

This runs TypeScript checking, the full test suite, source validation, manifest validation, and a
production Docusaurus build. Start with the maintained [documentation overview](docs/index.md) and
[framework quick start](docs/quick-start.md); see the
[docsite contributor guide](docs/contributing/docsite.md) for authoring rules and troubleshooting.

## Project orientation

- [Project constitution](https://github.com/FTOD/concorde/blob/main/.specify/memory/constitution.md)
- [Root architecture](specs/concorde/module.md) (module summary; its design reference is the adjacent `design.md`)
- [Concorde workflow abstract](specs/concorde/features/001-concorde-workflow/abstract.md) and [specification](specs/concorde/features/001-concorde-workflow/design.md)
- [Project docsite specification](specs/concorde/features/002-create-project-docsite/design.md)
- [Spec Kit installation specification](specs/concorde/features/003-install-concorde-speckit/design.md)
- [Releasing Concorde](docs/releasing.md)
- [Development self-hosting specification](specs/concorde/features/004-self-host-concorde/design.md)
- [Workflow reflections specification](specs/concorde/features/005-record-workflow-reflections/design.md); the maintained log is `specs/concorde/reflections.md`
