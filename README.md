# Concorde

Concorde extends [Spec Kit](https://github.com/github/spec-kit) with a hierarchical architecture
workflow for AI-developed software. It keeps feature specifications aligned with module ownership,
boundary contracts, bounded architecture views, and implementation evidence.

Concorde is designed to be installed as a native Spec Kit bundle containing:

- the `concorde-core` preset, which appends architecture guidance to templates and replaces nine
  normal command instructions with Concorde-aware workspace routing;
- the `concorde` extension, which supplies seven Concorde surfaces—six runtime-backed operations plus
  the read-only `ask` procedure—the workspace adapter, and runtime; and
- no replacement workflow: Spec Kit continues to own specification, planning, tasks, and
  implementation.

The three Spec Kit package concepts have different jobs:

| Concept | Concorde package | Role |
|---|---|---|
| Bundle | `concorde-bundle` | An installation recipe that pins the tested preset and extension versions. |
| Preset | `concorde-core` | Three append template layers plus nine complete normal-command replacements for nested workspace routing. |
| Extension | `concorde` | Seven Concorde-specific surfaces: six deterministic operations and one agent-followed, read-only question procedure. |

Catalogs are trusted discovery metadata for these independently versioned packages; they are not a
fourth installed runtime component. See the maintained
[component model](specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json),
[installation flow](specs/concorde/features/003-install-concorde-speckit/diagrams/bundle-installation-flow.json),
and the full [Feature 003 setup specification](specs/concorde/features/003-install-concorde-speckit/spec.md).
The project docsite build turns declared diagram sources into interactive standalone views.

## Project status

The project docsite and architecture publication pipeline are implemented and tested. Feature 003
owns the native Concorde bundle, preset command composition, seven-surface extension, release/catalog
tooling, and setup lifecycle. Feature 001 defines the Concorde architecture-aware development workflow;
its initialization, nested feature placement/selection, bounded context, architecture readiness, and
deterministic validation behavior are implemented. Timed human pilots and browser-based diagram
review remain pending and are kept separate from automated evidence.

Concorde can also install the current checkout's framework sources into this repository for
development self-application. That review-first path is deliberately separate from the release
bundle used by other projects; see [Developing Concorde with Concorde](docs/self-hosting.md).

## Quick start: install Concorde as a Spec Kit bundle

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) for the repository's Python 3.11 development environment
- Spec Kit/Specify CLI 0.16.4, installed into the development environment by `uv sync`
- Codex for the initial skills-mode integration

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
`https://github.com/FTOD/concorde/releases/latest/download/release.json`. See the
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

The release contains exactly `concorde-core@0.1.0` and `concorde@0.1.0`. It does not install a custom
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

For the published-release installation and release acceptance, follow the
[framework quick start](docs/quick-start.md) and the
[release publication validation guide](specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/quickstart.md).

### 5. Use the Concorde commands

After installation, invoke these agent skills from the target project:

```text
$speckit-concorde-init
$speckit-concorde-feature-create --module-id module.<project-slug> --feature-id feature.<project-slug>.<name> --short-name <name>
$speckit-concorde-feature-select feature.<project-slug>.<name>
$speckit-concorde-feature-harden feature.<project-slug>.<name>
$speckit-concorde-context module.<project-slug>
$speckit-concorde-validate
$speckit-concorde-ask When should I use context instead of feature-select?
```

- `init` proposes a root architecture package and writes it only after explicit approval.
- `feature.create` proposes reviewed module ownership and one canonical nested feature root.
- `feature.select` selects an existing nested feature for all normal Spec Kit phases.
- `feature.harden` proposes a permanent design from a task-complete implementation attempt and,
  only after explicit approval, promotes it and removes that temporal `implementation/` directory.
- `context` returns one bounded architectural level without expanding child internals.
- `validate` deterministically checks identities, hierarchy, references, contracts, views, and
  evidence status.
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

The independent [`docsite/`](docsite/) package builds Concorde's own read-only Docusaurus site from
two canonical source roots, presented through three reader-facing navigation families:

| Source | Published content |
|---|---|
| `specs/**/module.md`, `specs/**/contracts/**/contract.md` | Architecture modules, boundary contracts, and declared Archify views |
| `docs/**/*.md` | Project documentation |
| `specs/**/spec.md`, `specs/**/design.md` | Permanent feature specifications and accepted designs |

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

- [Project constitution](.specify/memory/constitution.md)
- [Root architecture](specs/concorde/module.md)
- [Concorde workflow specification](specs/concorde/features/001-concorde-workflow/spec.md)
- [Project docsite specification](specs/concorde/features/002-create-project-docsite/spec.md)
- [Spec Kit installation specification](specs/concorde/features/003-install-concorde-speckit/spec.md)
- [Releasing Concorde](docs/releasing.md)
- [Development self-hosting specification](specs/concorde/features/004-self-host-concorde/spec.md)
