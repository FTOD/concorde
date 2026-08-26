---
title: Quick Start
sidebar_position: 2
---

# Quick Start

This guide has three parts: preview Concorde's generated read model, install the current local
release into a disposable Spec Kit project, and start a first architecture-aware feature. The
installation path is intentionally isolated so it exercises the bundle, preset, extension, and
agent integration that a user project receives.

The supported setup boundary and current evidence status are authoritative in
[Feature 003](../specs/concorde/features/003-install-concorde-speckit/spec.md).

## 1. Preview this project's read model

You need Node.js 20 or newer. From the Concorde repository root, run these commands in a terminal:

```bash
cd docsite
npm ci
npm run start
```

Open the local address printed by Docusaurus. The site has three views over maintained sources:

- **Architecture** publishes module and boundary-contract sources plus declared Archify views.
- **Documentation** publishes the explanatory guides under `docs/`.
- **Features** publishes each durable feature `spec.md` and `design.md` while excluding its temporary
  `implementation/` workspace.

Before submitting a publication change, run the complete gate:

```bash
cd docsite
npm run check
```

The gate checks types, tests, source validity, routes, links, manifest completeness, and a production
build. A failed candidate is not promoted over the previous successful output. Publication behavior
is specified by [Feature 002](../specs/concorde/features/002-create-project-docsite/spec.md).

## 2. Build the current local release

This is a development installation path, not a public catalog shortcut. It currently requires:

- Python 3.11;
- `uv`;
- Specify CLI 0.16.4, available as `specify`; and
- a supported coding-agent integration such as Codex skills mode.

Check the tools in a terminal:

```bash
python3 --version
uv --version
specify --version
```

From the Concorde checkout, build and verify the independently versioned packages:

```bash
uv sync
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-starter --output dist
uv run python scripts/release/verify-release.py --dist dist
```

The base URL is written into catalog metadata as the future location of archives. The release
builder does not contact that address while building.

Start a local catalog server in a second terminal:

```bash
uv run python tests/concorde/support/catalog_server.py --dist dist --port 8765
```

## 3. Install into a disposable project

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
  --path "$concorde_checkout/bundles/concorde-starter"
specify bundle info concorde-starter --json
specify bundle install "$concorde_checkout/bundles/concorde-starter/bundle.yml"
```

The `concorde-starter` bundle is an installation recipe. It pins exactly two independently versioned
components:

| Installed component | Responsibility |
|---|---|
| `concorde-core` preset | Adds architecture-aware templates and complete selected-workspace routing for nine normal Spec Kit phases |
| `concorde` extension | Adds seven Concorde-specific surfaces: six runtime-backed operations, one read-only agent question procedure, portable adapters and launchers, and the deterministic Python runtime |

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

Review the initialization proposal before allowing it to write maintained sources. Context retrieval
is read-only and loads one bounded architecture level for the current agent interaction.

After deciding which module provides the behavior, create and select the nested feature:

```text
$speckit-concorde-feature-create \
  --module-id module.<project> \
  --feature-id feature.<project>.<name> \
  --short-name <name>

$speckit-concorde-feature-select feature.<project>.<name>
```

Then use the normal Spec Kit lifecycle, now routed through the selected feature workspace:

When that feature needs a simpler correlated decomposition, create an immediate child rather than a
new unrelated top-level feature:

```text
speckit.concorde.feature.create --parent-feature feature.example.outcome \
  --feature-id feature.example.outcome.focused-part --short-name focused-part
```

Review the exact proposal before apply. Only one child level is valid; the parent keeps aggregate
facts and each child keeps its focused outcome.

```text
$speckit-specify Describe the feature's required behavior and why it matters.
$speckit-clarify
$speckit-checklist
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
$speckit-converge
$speckit-concorde-validate
```

Specification and accepted design stay at the feature root. Checklists, plans, tasks, research, and
delivery evidence stay under the single active `implementation/` attempt.

## 5. Finish the milestone deliberately

When all tasks and every existing checklist item are complete, validation has been reviewed, and you
accept the implementation, ask the agent to harden the feature:

```text
$speckit-concorde-feature-harden feature.<project>.<name>
```

The first result is a proposal, not a mutation. Review the full candidate `design.md`, the exact
`implementation/` removal target, and the source digest. Only explicit approval applies that
unchanged proposal. On success, the durable design remains and the temporary attempt is removed.

Continue with the [Concorde workflow](concorde-workflow.md) for the review gates and
[Commands and installed surfaces](commands.md) for command-by-command behavior.
