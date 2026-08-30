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

This is the normal path for a project that wants Concorde. It needs `uvx`, a shell, and network
access—no preinstalled Python or Spec Kit CLI, Concorde checkout, release build, or local server.
From an empty directory or existing Spec Kit project, run one command:

```bash
curl -fsSL https://raw.githubusercontent.com/FTOD/concorde/main/scripts/install-concorde.py \
  | uvx --from specify-cli==0.16.4 python - --integration codex
```

Use the integration your coding agent needs (`claude`, `codex`, `gemini`, …). Codex defaults to
skills mode; other initialization options can be passed with `--integration-options`. On an existing
project, omit `--integration` to preserve its recorded default. Use `--target PATH` for another
directory or `--version 0.1.0` for an immutable release.

The installer obtains the pinned Spec Kit CLI in an ephemeral uv tool environment, validates the
release pointer, initializes only a fresh empty target, reconciles three installer-owned catalogs,
prints native `bundle info`, and chooses native install, update, or a byte-identical current no-op.
It ends with exact component versions, reload status, and the next Concorde command.

Preview performs the same native bundle resolution in a disposable project and changes zero target
bytes:

```bash
curl -fsSL https://raw.githubusercontent.com/FTOD/concorde/main/scripts/install-concorde.py \
  | uvx --from specify-cli==0.16.4 python - --integration codex --preview
```

Review the plain-text installer before execution when desired:

```bash
curl -fsSLo install-concorde.py \
  https://raw.githubusercontent.com/FTOD/concorde/main/scripts/install-concorde.py
less install-concorde.py
uvx --from specify-cli==0.16.4 python install-concorde.py --integration codex
```

The [one-command installation design](../specs/concorde/features/003-install-concorde-speckit/subfeatures/002-one-command-install/design.md)
defines the required behavior, inputs, reports, and failure handling; its repository-owned
`contracts/installer-cli.md` supplies the exact interface profile. The command is only an accelerator:
it invokes the public Spec Kit operations in the manual path below and never copies component files
itself.

The newest published version is currently `v0.1.0`, which predates the module design reference, the
feature abstract, and the removal of the `feature.create`/`feature.select` commands. These guides
describe the `0.4.0` sources in this checkout; to work under the document model they describe, use
the development path in part 3 until `0.4.0` is published. Otherwise continue with part 4.

## 3. Build the current local release (development path)

Use this one-command path to try unreleased checkout sources or reproduce the installer's acceptance
journey:

```bash
target_project="$(mktemp -d)"
uvx --from specify-cli==0.16.4 python scripts/install-concorde.py \
  --target "$target_project" --integration codex --checkout "$PWD"
```

The command binds an ephemeral loopback port, builds and reproducibly verifies the checkout before
target mutation, serves its catalogs for this run, follows the same catalog and bundle lifecycle,
removes its transient `concorde-dev` registrations, and always stops the server. Run it again to
verify the `already-current` byte-level no-op.

### Manual native fallback

Use the explicit sequence when auditing or debugging the lifecycle. First build and verify the
release and keep the server running in a second terminal:

```bash
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
uv run python scripts/release/verify-release.py --dist dist
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
specify bundle install concorde-bundle
```

The `concorde-bundle` bundle is an installation recipe. It pins exactly two independently versioned
components:

| Installed component | Responsibility |
|---|---|
| `preset:concorde` | Adds six architecture-aware templates (including feature abstract, design-reference, and reflection-log templates), modifies the installed instructions for nine normal Spec Kit phases with complete selected-workspace routing, and adds one fast-loop command |
| `extension:concorde` | Adds five Concorde-specific surfaces: four runtime-backed operations, one read-only agent question procedure, portable adapters and launchers, and the deterministic Python runtime |

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

For a bounded small change, select one existing accepted feature as the anchor and use the alternate
direct path. Every related affected feature must also have an accepted implementation and no active
`attempt/`:

```text
$speckit-fast-loop <small-change description>
```

Fast-loop discovers and explicitly resolves every affected feature before mutation, then directly
reconciles code, proportional tests, each affected durable trio, and related contract/architecture/
user documentation. Cross-feature and internal contract/data-format changes can remain on the fast
path when module responsibilities and dependencies stay stable. Changes to those module boundaries,
to project-level compatibility/migration promises for users of the whole project, ambiguous work, or
unsafe worktree overlap return to the normal lifecycle. Architecture-source edits require exact
maintainer review. Fast-loop creates no attempt or acceptance proposal.

The abstract (`abstract.md`), behavioral design (`design.md`), and accepted implementation
(`implementation.md`) stay at
the feature root; read them in that order. Checklists, plans, tasks, research, and delivery evidence
stay under the single active `attempt/` attempt.

## 5. Finish the milestone deliberately

When all tasks and every existing checklist item are complete, validation has been reviewed, and you
accept the implementation, ask the agent to accept that implementation:

```text
$speckit-concorde-impl-accept feature.<project>.<name>
```

The first result is a proposal, not a mutation. Review the full candidate feature `implementation.md`, any
proposed amendment to the `design.md` of the module at which the feature is specified, the exact
`attempt/` removal target, and the source digest. Only explicit approval applies that
unchanged proposal. On success, the durable realization (and the amended design reference, when
proposed) remains and the temporary attempt is removed.

Continue with the [Concorde workflow](concorde-workflow.md) for the review gates and
[Commands and installed surfaces](commands.md) for command-by-command behavior.
