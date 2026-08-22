# Concorde

Concorde extends [Spec Kit](https://github.com/github/spec-kit) with a hierarchical architecture
workflow for AI-developed software. It keeps feature specifications aligned with module ownership,
boundary contracts, bounded architecture views, and implementation evidence.

Concorde is designed to be installed as a native Spec Kit bundle containing:

- the `concorde-core` preset, which adds architecture-aware guidance to normal Spec Kit artifacts;
- the `concorde` extension, which supplies Concorde agent commands; and
- no replacement workflow: Spec Kit continues to own specification, planning, tasks, and
  implementation.

The three Spec Kit package concepts have different jobs:

| Concept | Concorde package | Role |
|---|---|---|
| Bundle | `concorde-starter` | An installation recipe that pins the tested preset and extension versions. |
| Preset | `concorde-core` | Append-only guidance added to the existing spec, plan, and task templates. |
| Extension | `concorde` | Agent commands and deterministic runtime behavior for architecture operations. |

Catalogs are trusted discovery metadata for these independently versioned packages; they are not a
fourth installed runtime component. See the interactive
[component model](generated/architecture/concorde-spec-kit-component-model.html),
[installation flow](generated/architecture/concorde-starter-installation-flow.html), and the full
[Feature 003 setup specification](specs/concorde/features/003-install-concorde-speckit/spec.md).

## Project status

The project docsite and architecture publication pipeline are implemented and tested. Feature 003
owns the native starter bundle, append-only preset, three-command extension, release/catalog tooling,
and setup lifecycle. Feature 001 now defines the core architecture-aware development workflow; its
initialization, bounded-context, and validation slice is implemented, while dedicated nested feature
creation and selection remain planned.

## Quick start: install Concorde as a Spec Kit bundle

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) for the repository's Python 3.11 development environment
- Spec Kit/Specify CLI 0.16.4 available as `specify`
- Codex for the initial skills-mode integration

Check the required versions:

```bash
uv --version
uv sync
uv run python --version
specify --version
```

`uv sync` creates the repository-local `.venv/` from `pyproject.toml` and `uv.lock`. Concorde's
installed bundle runtime remains Python 3.11 standard-library-only and does not require target
projects to install `uv`.

### 1. Build the local release

From a Concorde checkout:

```bash
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-starter --output dist
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
  --path "$concorde_checkout/bundles/concorde-starter"
specify bundle info concorde-starter --json
specify bundle install "$concorde_checkout/bundles/concorde-starter/bundle.yml"
```

The information command previews the exact preset, extension, versions, compatibility range, and
project changes before installation. Verify the installed state:

```bash
specify bundle list --json
specify extension list
specify preset list
find .agents/skills -maxdepth 2 -name SKILL.md -print | sort
```

For catalog-based installation and release acceptance, follow the complete
[Feature 003 setup quick start](specs/concorde/features/003-install-concorde-speckit/implementation/quickstart.md).

### 5. Use the Concorde commands

After installation, invoke these agent skills from the target project:

```text
$speckit-concorde-init
$speckit-concorde-context module.<project-slug>
$speckit-concorde-validate
```

- `init` proposes a root architecture package and writes it only after explicit approval.
- `context` returns one bounded architectural level without expanding child internals.
- `validate` deterministically checks identities, hierarchy, references, contracts, views, and
  evidence status.

Project-authored `.concorde/` configuration and the unified `specs/` hierarchy are retained when the
bundle is updated or removed.

## Run this project's documentation site

The independent [`docsite/`](docsite/) package builds Concorde's own read-only Docusaurus site from
two canonical source roots, presented as three reader-facing collections:

| Source | Published content |
|---|---|
| `specs/**/module.md`, `specs/**/contracts/**/contract.md` | Architecture modules, boundary contracts, and declared Archify views |
| `docs/**/*.md` | Project documentation |
| `specs/**/spec.md` | Canonical Spec Kit feature specifications |

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
production Docusaurus build. See the [docsite contributor guide](docs/contributing/docsite.md) for
authoring rules and troubleshooting.

## Project orientation

- [Concorde prototype reference](concorde-prototype-reference.md)
- [Project constitution](.specify/memory/constitution.md)
- [Root architecture](specs/concorde/module.md)
- [Core workflow specification](specs/concorde/features/001-concorde-starter-workflow/spec.md)
- [Project docsite specification](specs/concorde/features/002-create-project-docsite/spec.md)
- [Spec Kit installation specification](specs/concorde/features/003-install-concorde-speckit/spec.md)
