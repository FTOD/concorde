# Concorde

Concorde adds a module-centered architecture and feature workflow to
[Spec Kit](https://github.com/github/spec-kit). It gives maintainers one structural entry point per
module, one complete specification per feature, bounded context for coding agents, deterministic
validation, and cleanup-only delivery.

## The model

```text
specs/<project>/
├── architecture.md
├── diagrams/                     # optional module-owned sources
├── modules/<child>/              # recursive, same shape
└── features/<NNN-name>.md        # complete durable feature specification

.concorde/
├── config.json                   # Profile 7 + root module selection
├── attempts/<stable-feature-id>/ # optional temporal work; removed by delivery
└── reflections/log.md            # tracked project process memory
```

A module is the only recursive specification unit. Its `architecture.md` defines responsibility,
boundary, immediate child modules and level-local features, typed architecture entities, directed
relationships, and representative interactions. Significant entities can be modules, packages,
programs, files, scripts, classes, functions, interfaces, schemas, stores, configuration, tests,
external systems, or a project-defined type with an explicit meaning.

A feature is one usable capability at that module level. Its direct Markdown file contains outcome, scope,
usage, scenarios, requirements, failures, related-feature semantics, embedded provided/required
interfaces, and an Architecture Zoom over entity IDs from the providing module or permitted
ancestry. Existing `contract.*` IDs may remain interface identities, but interfaces are part of the
feature rather than separate specification files.

Source code is the implementation. Tests and deterministic checks are evidence. Plans, research,
tasks, checklists, and validation logs are temporary attempt memory. Generated sites, diagrams,
indexes, packages, and delivery results are reproducible projections, not source authority.

Read more in [Ontology](docs/ontology.md), [Specification model](docs/specification-model.md), and
[Project structure](docs/project-structure.md).

## Workflow

Concorde composes normal Spec Kit commands with five framework commands:

| Command | Outcome |
|---|---|
| `$speckit-concorde-init` | Propose and explicitly apply a Profile 7 root module and reflection log. |
| `$speckit-specify` | Create or revise one direct level-local feature file and its requirements checklist. |
| `$speckit-clarify` | Resolve important ambiguity inside that design and its embedded interfaces. |
| `$speckit-checklist` | Create a reviewer-owned requirements-quality checklist in the corresponding stable-ID attempt. |
| `$speckit-plan` | Plan from feature file + module architecture + current code/tests into `.concorde/attempts/<stable-feature-id>/`. |
| `$speckit-tasks` | Generate dependency-ordered, traceable, test-first tasks. |
| `$speckit-analyze` | Read-only consistency and coverage audit. |
| `$speckit-implement` | Execute tasks across architecture/feature/code/tests/projections with evidence. |
| `$speckit-converge` | Append only remaining executable work to the active task list. |
| `$speckit-taskstoissues` | Convert tasks into dependency-aware external issues when authorized. |
| `$speckit-fast-loop` | Directly complete one eligible small no-attempt change. |
| `$speckit-concorde-context` | Retrieve exactly one bounded module or feature context. |
| `$speckit-concorde-validate` | Deterministically validate the complete source profile. |
| `$speckit-concorde-ask` | Answer from cited installed guidance and bounded project sources. |
| `$speckit-concorde-deliver` | Validate a completed attempt and atomically remove only that attempt. |

Feature Workspace Protocol 12 returns one selected `feature_path`, its providing module
architecture, bounded module ancestry, bounded related-feature summaries, temporal paths, reflection
state, and deterministic code/test discovery context. It never expands unrelated feature bodies or
synthesizes an implementation narrative.

Delivery Proposal 8 binds the stable target, current source/attempt digest, eligibility evidence,
and exact removal path. Apply revalidates everything and removes one real, non-symlinked project-control attempt.
Any stale, incomplete, invalid, or unsafe proposal is non-mutating.

See [Workflow](docs/concorde-workflow.md) and [Command reference](docs/commands.md).

## Install

Use Python 3.11+, `uv`, and Spec Kit 0.16.4. The one-command installer previews by default and uses
Spec Kit's native catalog/bundle lifecycle:

```bash
uv run python scripts/install-concorde.py --target ../my-project --integration codex --preview
uv run python scripts/install-concorde.py --target ../my-project --integration codex
```

Omit `--preview` to apply the reviewed installation plan.

For local development from this checkout:

```bash
uv run python scripts/install-concorde.py \
  --target ../my-project \
  --integration codex \
  --checkout . \
  --preview
```

The release pointer and catalogs declare Architecture Source Profile 7 and Workspace Protocol 12;
the installer rejects a package with a different profile/protocol. Installation owns component and
agent projections only. It preserves project-authored configuration, specifications, code, tests,
docs, and unrelated agent assets.

See [Quick start](docs/quick-start.md).

## Self-host this checkout

Canonical distribution sources live under `presets/concorde/` and `extensions/concorde/`. Installed
`.specify/`, Codex, and Claude surfaces are projections. Review and apply a scoped self-host proposal,
then verify freshness:

```bash
uv run python scripts/development/self-host-concorde.py --project-root . propose --format json
uv run python scripts/development/self-host-concorde.py --project-root . \
  apply --proposal .specify/self-hosting-proposal.json --format json
uv run python scripts/development/self-host-concorde.py --project-root . \
  status --require-current --format json
```

Self-host verification compares canonical component bytes, Spec Kit registries, materialized command
and template surfaces, active-integration assets, Protocol 12 markers, and absence of removed
templates. See [Self-hosting](docs/self-hosting.md).

## Develop and validate

```bash
uv sync --extra dev
.venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'
.venv/bin/python extensions/concorde/scripts/python/concorde.py --project-root . validate

cd docsite
npm ci
npm run check
```

The repository self-applies the model at [specs/concorde/architecture.md](specs/concorde/architecture.md).
Canonical packages, runtime, tests, documentation adapter, and public guides are kept in one coherent
profile; mixed source layouts are invalid.

## Release

```bash
uv run python scripts/release/build-components.py --output dist
uv run python scripts/release/verify-release.py --dist dist
```

The build produces deterministic preset, extension, and bundle archives plus matching catalogs.
Release verification checks identity, Profile 7/Protocol 12 metadata, safe members, digests, URLs,
capability counts, and byte-equivalent rebuilds. See [Releasing](docs/releasing.md).

## Repository map

| Path | Responsibility |
|---|---|
| `presets/concorde/` | Canonical host-phase commands and templates. |
| `extensions/concorde/` | Canonical runtime, schemas, framework commands, and agent assets. |
| `specs/concorde/` | Self-hosted module architectures, direct feature files, and diagrams. |
| `.concorde/` | Project configuration, stable-ID attempts, tracked reflection log, and triage state. |
| `tests/concorde/` | Python unit, contract, integration, and acceptance evidence. |
| `docsite/` | Generated architecture/feature publication adapter. |
| `scripts/` | Installer, self-host, and release programs. |
| `bundles/`, `catalogs/` | Installable package recipe and release catalogs. |
| `docs/` | Public framework and contributor guidance. |

Concorde package manifests declare the MIT license.
