---
title: Quick Start
sidebar_position: 2
---

# Quick Start

This guide has four parts: preview Concorde's generated read model, install the published release
into a Spec Kit project, optionally build and install the current local sources instead, and start a
first architecture-aware feature. The installation paths are intentionally isolated so they exercise
the bundle, preset, extension, and agent integration that a user project receives.

The supported setup boundary and current evidence status are authoritative in
[Feature 003](../specs/concorde/features/003-install-concorde-speckit/design.md).

## 1. Preview this project's read model

You need Node.js 20 or newer. Concorde tracks its officially installed Archify 2.16 project-local
skill under `.agents/skills/archify`, so no separate renderer installation or environment variable is
required. Run these commands from the Concorde repository root:

```bash
cd docsite
npm ci
npm run start
```

Open the local address printed by Docusaurus. The site has three views over maintained sources:

- **Architecture** publishes each module summary with its embedded architecture diagrams, its linked
  `design.md` design reference, and boundary contracts.
- **Documentation** publishes the explanatory guides under `docs/`.
- **Features** opens each feature on its `abstract.md`, with `design.md` and `implementation.md`
  as companion pages, while excluding its temporary `attempt/` workspace.

Before submitting a publication change, run the complete gate:

```bash
cd docsite
npm run check
```

The gate checks types, tests, source validity, deterministic Archify delivery, routes, links,
manifest completeness, and a production build. It recreates ignored standalone diagrams from their
maintained JSON; a failed candidate is not promoted over the previous successful output. Publication
behavior is specified by [Feature 002](../specs/concorde/features/002-create-project-docsite/design.md).

## 2. Install the published release

This is the normal path for a project that wants Concorde. It needs only the pinned Spec Kit CLI —
no Concorde checkout, no build, and no local server. Install the CLI once (`uv tool install
specify-cli==0.16.4`, or run it ad hoc with `uvx --from specify-cli==0.16.4 specify …`), then, in
your project directory:

```bash
specify init --here --integration claude
base=https://github.com/FTOD/concorde/releases/download/v0.1.0
specify extension catalog add "$base/extensions.json" --name concorde --install-allowed
specify preset catalog add "$base/presets.json" --name concorde --install-allowed
specify bundle catalog add "$base/bundles.json" --id concorde
specify bundle info concorde-bundle --json
specify bundle install concorde-bundle
```

Use the integration your coding agent needs (`claude`, `codex --integration-options="--skills"`,
`gemini`, …). `bundle info` shows the exact preset and extension versions before `bundle install`
adds them. To find the current version without hard-coding it, read the pointer:

```bash
curl -fsSL https://github.com/FTOD/concorde/releases/latest/download/release.json
```

It names the newest published version and the three catalog URLs to register. Every published
version stays available at its own `releases/download/v<version>/` location; see
[Releasing Concorde](releasing.md) for how releases are produced.

The newest published version is currently `v0.1.0`, which predates the module design reference, the
feature abstract, and the removal of the `feature.create`/`feature.select` commands. These guides
describe the `0.3.0` sources in this checkout; to work under the document model they describe, use
the development path in part 3 until `0.3.0` is published. Otherwise continue with part 4.

## 3. Build the current local release (development path)

Use this path to try unreleased sources or to reproduce the acceptance suite. It requires:

- Python 3.11;
- `uv`;
- Specify CLI 0.16.4, installed into the development environment by `uv sync`; and
- a supported coding-agent integration such as Codex skills mode.

Check the tools in a terminal:

```bash
python3 --version
uv --version
uv sync
source .venv/bin/activate
specify --version
```

From the Concorde checkout, build and verify the independently versioned packages:

```bash
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-bundle --output dist
uv run python scripts/release/verify-release.py --dist dist
```

The base URL is written into catalog metadata as the future location of archives. The release
builder does not contact that address while building.

Start a local catalog server in a second terminal:

```bash
uv run python tests/concorde/support/catalog_server.py --dist dist --port 8765
```

### Install the local build into a disposable project

Create the target outside the Concorde checkout so local self-hosting files are less likely to hide a
packaging problem:

```bash
target_project="$(mktemp -d)"
cd "$target_project"
specify init --here --integration codex --integration-options="--skills"
```

Register the generated local catalogs:

```bash
specify extension catalog add http://127.0.0.1:8765/extensions.json \
  --name concorde-dev --install-allowed
specify preset catalog add http://127.0.0.1:8765/presets.json \
  --name concorde-dev --install-allowed
specify bundle catalog add http://127.0.0.1:8765/bundles.json \
  --id concorde-dev --policy install-allowed
```

Inspect before installing. Set the checkout path explicitly, validate the passive bundle recipe,
and review its expanded information:

```bash
concorde_checkout=/absolute/path/to/concorde
specify bundle validate --offline \
  --path "$concorde_checkout/bundles/concorde-bundle"
specify bundle info concorde-bundle --json
specify bundle install "$concorde_checkout/bundles/concorde-bundle/bundle.yml"
```

The `concorde-bundle` bundle is an installation recipe. It pins exactly two independently versioned
components:

| Installed component | Responsibility |
|---|---|
| `concorde-core` preset | Adds five architecture-aware templates (including the feature abstract and design-reference templates) and complete selected-workspace routing for nine normal Spec Kit phases |
| `concorde` extension | Adds five Concorde-specific surfaces: four runtime-backed operations, one read-only agent question procedure, portable adapters and launchers, and the deterministic Python runtime |

Spec Kit resolves and installs those components and asks the active coding-agent integration to
materialize skills or slash commands. The bundle itself does not execute the workflow.

## 4. Start the first feature through the agent

The next examples belong in the coding-agent conversation, not in Bash. The `$...` notation invokes
an installed agent skill.

If you are unsure which command or artifact applies, ask before changing the project:

```text
$speckit-concorde-ask Where should planning artifacts for the selected feature live?
```

The answer should cite installed guidance and any bounded project sources it uses. The question
surface does not select a feature, create files, or begin implementation.

First establish and inspect the root architecture:

```text
$speckit-concorde-init
$speckit-concorde-context module.<project>
```

Review the initialization proposal (`.concorde/config.json`, a `module.md` summary, a seeded
`design.md` design reference, and a first level view at `architecture/diagrams/level-view.json`)
before allowing it to write maintained sources. Every module package keeps that shape: `module.md`
and `design.md` beside a `features/` directory for what the level can do and an `architecture/`
directory (`diagrams/`, `contracts/`, and `modules/`) for how it is composed. Context retrieval is
read-only and loads one bounded architecture level for the current agent interaction.

After deciding at which level the feature is specified (the level at which every module it uses is
visible), create it with the normal specify phase.
Concorde has no feature-creation command: export the canonical feature root in the terminal before
invoking the skill, so the Concorde specify addendum authors `abstract.md` and `design.md`, seeds a
placeholder `implementation.md`, and records the root in `.specify/feature.json`:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/<project>/features/001-<name>
```

```text
$speckit-specify Describe the feature's required behavior and why it matters.
```

Add the feature's `id` and `module` to the design front matter, register it in the module's
`features` list, and run `$speckit-concorde-validate` to confirm registration, canonical path, and
identity. To work on an existing feature later, set `SPECIFY_FEATURE_DIRECTORY` to its root (or edit
`.specify/feature.json`); standard Spec Kit selection is all Concorde uses.

When that feature needs a simpler correlated decomposition, create an immediate child rather than a
new unrelated top-level feature by pointing the same variable one level down:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/<project>/features/001-<name>/subfeatures/001-<focused-part>
```

Run `$speckit-specify` again, add `parent_feature` to the child's front matter, and register it in
the parent's `subfeatures` list. Only one child level is valid; the parent keeps aggregate facts and
each child keeps its focused outcome.

Then continue with the normal Spec Kit lifecycle, now routed through the selected feature workspace:

```text
$speckit-clarify
$speckit-checklist
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
$speckit-converge
$speckit-concorde-validate
```

The abstract (`abstract.md`), behavioral design (`design.md`), and accepted implementation
(`implementation.md`) stay at
the feature root; read them in that order. Checklists, plans, tasks, research, and delivery evidence
stay under the single active `attempt/` attempt.

## 5. Finish the milestone deliberately

When all tasks and every existing checklist item are complete, validation has been reviewed, and you
accept the implementation, ask the agent to harden the feature:

```text
$speckit-concorde-feature-harden feature.<project>.<name>
```

The first result is a proposal, not a mutation. Review the full candidate feature `implementation.md`, any
proposed amendment to the `design.md` of the module at which the feature is specified, the exact
`attempt/` removal target, and the source digest. Only explicit approval applies that
unchanged proposal. On success, the durable realization (and the amended design reference, when
proposed) remains and the temporary attempt is removed.

Continue with the [Concorde workflow](concorde-workflow.md) for the review gates and
[Commands and installed surfaces](commands.md) for command-by-command behavior.
