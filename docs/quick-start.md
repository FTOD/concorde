---
title: Quick Start
sidebar_position: 2
---

# Quick Start

There are two useful ways to start: browse Concorde itself, or install the current local release in
a disposable Spec Kit project. The first path takes only a few commands. The second demonstrates the
same bundle, preset, extension, skills, and runtime surfaces that a user project receives.

## Preview the Concorde project site

You need Node.js 20 or newer. From the repository root:

```bash
cd docsite
npm ci
npm run start
```

The preview validates the canonical sources, prepares disposable renderer projections, and starts
Docusaurus. Open the URL printed in the terminal and use the Architecture, Documentation, and
Features navigation families.

Before submitting docsite changes, run the complete gate:

```bash
cd docsite
npm run check
```

This checks types, tests, content validity, manifest completeness, links, and a production build. A
failed candidate does not replace the last successful `docsite/build/` output.

## Install a local Concorde release

The current self-hosted release path requires Python 3.11, `uv`, and Specify CLI 0.16.4. First build
the independently versioned Concorde components and starter bundle:

```bash
uv sync
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-starter --output dist
uv run python scripts/release/verify-release.py --dist dist
```

The base URL is catalog metadata for the next step; the build command does not contact it. In a
second terminal, serve the generated local catalogs:

```bash
uv run python tests/concorde/support/catalog_server.py --dist dist --port 8765
```

Create a disposable Spec Kit project and register the local catalogs:

```bash
project_root="$(mktemp -d)"
cd "$project_root"
specify init --here --integration codex --integration-options="--skills"

specify extension catalog add http://127.0.0.1:8765/extensions.json \
  --name concorde-dev --install-allowed
specify preset catalog add http://127.0.0.1:8765/presets.json \
  --name concorde-dev --install-allowed
specify bundle catalog add http://127.0.0.1:8765/bundles.json \
  --id concorde-dev --policy install-allowed
```

Set `concorde_checkout` to this repository's absolute path, inspect the recipe, and install it:

```bash
concorde_checkout=/absolute/path/to/concorde
specify bundle validate --offline \
  --path "$concorde_checkout/bundles/concorde-starter"
specify bundle info concorde-starter --json
specify bundle install "$concorde_checkout/bundles/concorde-starter/bundle.yml"
```

The bundle installs two components: the `concorde-core` preset changes how normal Spec Kit phases
resolve a nested feature workspace, and the `concorde` extension adds Concorde-specific commands and
their deterministic runtime. Spec Kit remains the lifecycle host.

## Start the first architecture-aware feature

In the target project, invoke the installed command skills through the coding-agent integration:

```text
$speckit-concorde-init
$speckit-concorde-context module.<project>
$speckit-concorde-feature-create --module-id module.<project> --feature-id feature.<project>.<name> --short-name <name>
$speckit-concorde-feature-select feature.<project>.<name>
```

Review every proposed write before approval. Then use the normal Spec Kit phases—specify, clarify,
checklist, plan, tasks, implement, analyze, and converge. Concorde routes them to the selected nested
feature and separates durable `spec.md` and `design.md` from the current `implementation/` attempt.

Validate the bounded architecture throughout the work:

```text
$speckit-concorde-validate
```

After every task and checklist item is complete and the implementation is accepted, you may run
`$speckit-concorde-feature-harden`. It presents the exact durable-design update and temporal files to
remove; nothing is promoted until you explicitly approve the digest-bound proposal.

Continue with [What Concorde is](framework-overview.md), or consult the canonical
[installation specification](../specs/concorde/features/003-install-concorde-speckit/spec.md) and
[core workflow specification](../specs/concorde/features/001-concorde-starter-workflow/spec.md).
