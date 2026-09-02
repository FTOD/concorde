# Concorde

Concorde is a standalone, module-centered architecture and feature workflow for maintainers and
coding agents. It provides one structural entry point per module, one complete specification per
feature, bounded implementation context, deterministic validation, and cleanup-only delivery.

Concorde no longer depends on or composes with Spec Kit. The familiar `speckit-*` command IDs remain
temporarily for workflow compatibility, and the Markdown formatting of commands/templates retains
useful ideas from Spec Kit as acknowledged reference lineage. All current instructions, templates,
runtime behavior, installation, and ownership are Concorde-native.

## The model

```text
specs/<project>/
├── architecture.md
├── diagrams/                     # optional module-owned sources
├── modules/<child>/              # recursive, same shape
└── features/<NNN-name>.md        # complete durable feature specification

.concorde/
├── config.json                   # Profile 7 + root module
├── feature.json                  # selected direct feature path
├── constitution.md               # optional project governance
├── attempts/<stable-feature-id>/ # temporal work; removed by delivery
├── reflections/log.md            # tracked process memory
├── framework/                    # installed Concorde package projection
└── install.json                  # installed-output ownership receipt
```

A module is the only recursive specification unit. Its `architecture.md` owns responsibility,
boundary, immediate children/features, significant typed entities, directed relationships, and
representative interactions. A feature is one direct Markdown file with outcome/scope, usage,
scenarios, requirements, embedded provided/required interfaces, and an Architecture Zoom over
visible entity IDs.

Source code is implementation. Tests and deterministic checks are evidence. Plans, tasks, research,
checklists, and validation logs are temporary attempt memory. Generated sites/diagrams/releases and
installed framework/agent files are reproducible projections, never intent authority.

Read [Ontology](docs/ontology.md), [Specification model](docs/specification-model.md), and
[Project structure](docs/project-structure.md).

## Workflow commands

Canonical command sources live together in root `commands/` (for example,
`commands/speckit.specify.md`). Install/rendering turns
them into agent-native skills while retaining these public IDs:

| Command | Outcome |
|---|---|
| `$speckit-constitution` | Create or amend `.concorde/constitution.md`. |
| `$speckit-concorde-init` | Propose and explicitly apply a Profile 7 root module/reflection log. |
| `$speckit-specify` | Create or revise one direct level-local feature and its requirements checklist. |
| `$speckit-clarify` | Resolve important ambiguity in that feature/interfaces. |
| `$speckit-checklist` | Create a reviewer-owned requirements-quality checklist. |
| `$speckit-plan` | Plan from feature + module architecture + current code/tests into one attempt. |
| `$speckit-tasks` | Generate dependency-ordered, traceable, test-first tasks. |
| `$speckit-analyze` | Run a read-only consistency/coverage audit. |
| `$speckit-implement` | Execute tasks across architecture/feature/code/tests/projections with evidence. |
| `$speckit-converge` | Append only remaining verified work to the active task list. |
| `$speckit-taskstoissues` | Convert tasks into dependency-aware external issues when authorized. |
| `$speckit-fast-loop` | Complete one eligible small established change without an attempt. |
| `$speckit-concorde-context` | Retrieve exactly one bounded module or feature context. |
| `$speckit-concorde-validate` | Deterministically validate the complete source profile. |
| `$speckit-concorde-ask` | Answer from cited package guidance and bounded project sources. |
| `$speckit-concorde-deliver` | Validate a completed attempt and remove exactly that attempt. |

Feature Workspace Protocol 12 returns one selected `feature_path`, its providing architecture,
bounded ancestry/related summaries, stable-ID attempt/reflection state, and deterministic source/test
discovery hints. Delivery Proposal 8 binds current digests and one exact removal path. Any stale,
incomplete, invalid, or unsafe delivery is non-mutating.

See [Workflow](docs/concorde-workflow.md) and [Command reference](docs/commands.md).

## Explore architecture and implementation alignment

Concorde 1.1 adds the native read-only `concorde explore` operation. It works without an implementation graph,
returning bounded Profile 7 modules/entities/features/interfaces with truthful `unknown` alignment:

```bash
python3 scripts/concorde.py --project-root . explore feature.example.checkout
```

To overlay Understand Anything output, pass the graph explicitly with a schema-1 alignment sidecar
and the implementation revision you expect:

```bash
python3 scripts/concorde.py --project-root . explore feature.example.checkout \
  --graph .ua/knowledge-graph.json \
  --alignment evidence/alignment.json \
  --revision "$(git rev-parse HEAD)" \
  --query checkout \
  --status verified
```

The sidecar names each Concorde subject, requested status, evidence basis, implementation/evidence UA
node IDs, finding IDs, and rationale. Only explicit revision-current executable evidence can become
verified; deterministic findings can establish disagreement. Missing, stale, candidate-only, or
invalid evidence becomes unknown. UA node/edge types remain adapter metadata, and neither text search
nor name/path similarity creates a mapping. The command emits canonical JSON to stdout and writes no
index or source file. Installed projects use
`.concorde/framework/scripts/concorde.py` with the same arguments.

## Install

Concorde requires Python 3.11+ and no host framework. Preview is the default:

```bash
python3 scripts/install-concorde.py \
  --target ../my-project \
  --integration codex
```

Review the exact create/adopt/update/remove/conflict actions, then explicitly apply:

```bash
python3 scripts/install-concorde.py \
  --target ../my-project \
  --integration codex \
  --apply
```

Use `--integration claude` for Claude. The installer validates [`concorde.json`](concorde.json),
copies one package beneath `.concorde/framework/`, renders the selected integration, seeds only
missing reflection defaults, and writes `.concorde/install.json` last. It updates/removes only files
whose observed bytes still match the prior receipt; unowned or user-modified collisions fail closed.

See [Quick start](docs/quick-start.md).

## Maintain this checkout

Root `commands/`, `templates/`, `src/concorde/`, `scripts/`, and `agent-assets/` are canonical.
Tracked `.agents/**` and `.claude/**` files are generated source-checkout projections; Concorde does
not install a duplicate `.concorde/framework` into its own repository.

```bash
python3 scripts/development/sync-agent-surfaces.py status --format json
python3 scripts/development/sync-agent-surfaces.py apply --format json
```

See [Agent-surface maintenance](docs/agent-surfaces.md).

## Develop and validate

```bash
uv sync
.venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'
python3 scripts/concorde.py --project-root . validate

cd docsite
npm ci
npm run check
```

The repository self-applies the model at
[`specs/concorde/architecture.md`](specs/concorde/architecture.md).

## Release

```bash
python3 scripts/release/build-release.py --output dist
python3 scripts/release/verify-release.py --dist dist
```

The build produces exactly `concorde-<version>.zip` and `release.json`. Verification checks identity,
safe members, SHA-256, an isolated native installation, and byte-equivalent rebuilds. See
[Releasing](docs/releasing.md).

## Repository map

| Path | Responsibility |
|---|---|
| `commands/` | Canonical complete lifecycle command Markdown. |
| `templates/` | Complete feature/plan/task/checklist/constitution/reflection format references. |
| `src/concorde/` | Deterministic runtime, alignment explorer, and command/agent projectors. |
| `agent-assets/` | Canonical reflection-triage roles and integration templates. |
| `scripts/` | Portable runtime adapters, installer, checkout sync, and release programs. |
| `concorde.json` | Single package/version/profile/protocol/inventory authority. |
| `specs/concorde/` | Self-applied module architectures and direct features. |
| `.concorde/` | Native project configuration, selection, constitution, attempts, and reflections. |
| `tests/concorde/` | Python unit, contract, integration, and acceptance evidence. |
| `docsite/` | Architecture/feature publication adapter. |
| `docs/` | Public framework and contributor guidance. |

Concorde is distributed under the MIT License in `LICENSE`, declared by its package manifest and
included in every release/installed framework projection.
