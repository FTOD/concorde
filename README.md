# Concorde

Concorde extends [Spec Kit](https://github.com/github/spec-kit) with a hierarchical architecture
workflow for AI-developed software. It keeps feature specifications aligned with module ownership,
boundary contracts, bounded architecture views, and implementation evidence.

Concorde is designed to be installed as a native Spec Kit bundle containing:

- the `concorde-core` preset, which adds architecture-aware guidance to normal Spec Kit artifacts;
- the `concorde` extension, which supplies Concorde agent commands; and
- no replacement workflow: Spec Kit continues to own specification, planning, tasks, and
  implementation.

## Project status

The project docsite and its architecture publication pipeline are implemented and tested. The starter
bundle is fully specified and planned in
[`specs/001-concorde-starter-workflow/`](specs/001-concorde-starter-workflow/), but its distributable
bundle, preset, extension, and release scripts have not been implemented yet. The bundle commands
below describe the intended Feature 001 quick start and will become runnable when that feature is
implemented.

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
uv run python scripts/release/build-components.py --output dist
specify bundle validate --path bundles/concorde-starter
specify bundle build --path bundles/concorde-starter --output dist
uv run python scripts/release/verify-release.py --dist dist
```

The release contains exactly `concorde-core@0.1.0` and `concorde@0.1.0`. It does not install a custom
workflow or reusable Spec Kit steps.

### 2. Initialize a target Spec Kit project

Use a new project directory, or run the equivalent command in an existing supported Spec Kit project:

```bash
project_root="$(mktemp -d)"
cd "$project_root"
specify init --here --integration codex --integration-options="--skills"
```

### 3. Install the local bundle

Set `concorde_checkout` to the absolute path of this repository:

```bash
concorde_checkout=/absolute/path/to/concorde
specify bundle info "$concorde_checkout/bundles/concorde-starter/bundle.yml" --json
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
[Feature 001 quick start](specs/001-concorde-starter-workflow/quickstart.md).

### 4. Use the Concorde commands

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

Project-authored `.concorde/` and `architecture/` sources are retained when the bundle is updated or
removed.

## Run this project's documentation site

The independent [`docsite/`](docsite/) package builds Concorde's own read-only Docusaurus site from
three canonical collections:

| Source | Published content |
|---|---|
| `architecture/**/*.md` | Modules, architectural features, contracts, and declared Archify views |
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
- [Root architecture](architecture/concorde/module.md)
- [Starter bundle specification](specs/001-concorde-starter-workflow/spec.md)
- [Project docsite specification](specs/002-create-project-docsite/spec.md)
