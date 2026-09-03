# Concorde

Concorde is a standalone, module-centered architecture and feature workflow for maintainers and
coding agents. It provides one structural entry point per module, one complete specification per
feature, bounded implementation context, deterministic validation, and cleanup-only delivery.

Concorde no longer depends on or composes with Spec Kit. Its public capability namespace is
`concorde-*`: public leaf Skills perform one bounded phase, internal leaves support Operations, and
paired Operation skills invoke acyclic LangGraphs over ordered Skills/Operations with per-leaf
Codex/Claude enforcement. Skill/template Markdown retains useful formatting
ideas from Spec Kit as acknowledged reference lineage; all behavior and ownership are Concorde-native.

## The model

```text
specs/<project>/
├── architecture.md
├── diagrams/                     # required system overview + optional module-owned views
├── modules/<child>/              # recursive, same shape
└── features/<NNN-name>.md        # complete durable feature specification

.concorde/
├── config.json                   # Profile 7 + root module
├── feature.json                  # selected direct feature path
├── constitution.md               # optional project governance
├── attempts/<stable-feature-id>/ # temporal work; removed by delivery
├── reflections/index.json        # tracked allocation high-water only
├── reflections/R-NNN.md          # one detailed problem per tracked file
├── framework/                    # installed Concorde package projection
└── install.json                  # installed-output ownership receipt
```

A module is the only recursive specification unit. Its `architecture.md` owns responsibility,
boundary, immediate children/features, significant typed entities, directed relationships, and
representative interactions. A feature is one direct Markdown file with outcome/scope, usage,
scenarios, requirements, embedded provided/required interfaces, and an Architecture Zoom over
visible entity IDs.

Source code is implementation. Tests and deterministic checks are evidence. Plans, tasks, research,
checklists, and validation logs are temporary attempt memory. Generated sites/diagrams and
installed framework/agent files are reproducible projections, never intent authority.

Read [Ontology](docs/ontology.md), [Specification model](docs/specification-model.md), and
[Project structure](docs/project-structure.md).

## Leaf Skills and Operations

Seventeen canonical leaves (15 public, two internal) live at `skills/<name>/SKILL.md`. Each of three Operations lives at
`operations/<name>/{operation.py,SKILL.md}` and its Markdown is installed into the same agent Skill
namespace while Python remains in the framework.

| Public leaf Skill | Outcome |
|---|---|
| `$concorde-constitution` | Create or amend `.concorde/constitution.md`. |
| `$concorde-init` | Propose and explicitly apply a Profile 7 root module/reflection index. |
| `$concorde-specify` | Create or revise one direct level-local feature and its requirements checklist. |
| `$concorde-clarify` | Resolve important ambiguity in that feature/interfaces. |
| `$concorde-checklist` | Create a reviewer-owned requirements-quality checklist. |
| `$concorde-tasks` | Generate dependency-ordered, traceable, test-first tasks. |
| `$concorde-analyze` | Run a read-only consistency/coverage audit. |
| `$concorde-implement` | Execute tasks across architecture/feature/code/tests/projections with evidence. |
| `$concorde-converge` | Append only remaining verified work to the active task list. |
| `$concorde-taskstoissues` | Convert tasks into dependency-aware external issues when authorized. |
| `$concorde-fast-loop` | Complete one eligible small established change without an attempt. |
| `$concorde-context` | Retrieve exactly one bounded module or feature context. |
| `$concorde-validate` | Deterministically validate the complete source profile. |
| `$concorde-ask` | Answer from cited package guidance and bounded project sources. |
| `$concorde-deliver` | Validate a completed attempt and remove exactly that attempt. |

Feature Workspace Protocol 13 returns one selected `feature_path`, its providing architecture,
bounded ancestry/related summaries, stable-ID attempt/reflection state, and deterministic source/test
discovery hints. Delivery Proposal 9 binds current digests and one exact removal path. Any stale,
incomplete, invalid, or unsafe delivery is non-mutating.

| Public Operation | Outcome |
|---|---|
| `$concorde-plan` | Resolve read-only context, then author one temporal plan behind published feature interfaces. |
| `$concorde-standard-dev-loop` | Run the four-stage lifecycle while nesting public planning. |
| `$concorde-reflections-triage` | Run only the explicitly selected status/investigate/route/validation branch. |

The framework packages internal `concorde-plan-context` and `concorde-plan-author`, but neither is
projected as a user capability. Both agents receive the same 18 public `concorde-*` skills. See
[Workflow](docs/concorde-workflow.md) and [Skill reference](docs/skills.md).

## Compose prompts with LangGraph

Canonical `skills/*/SKILL.md` files are complete leaves with public/internal exposure and
machine-readable effects when composed. Operations resolve whole direct Skills or public Operations
into ordered [LangGraph](https://github.com/langchain-ai/langgraph) stages without copying/flattening
prompts. LangGraph is control plane only: trusted code resolves concrete paths, narrows leaf effects,
renders a Codex permission profile or Claude restricted strict sandbox, and requires a receipt.

The tested standard graph is:

```text
START → specify → plan → tasks → deliver → END
```

Its direct bundles preserve the full lifecycle: `specify`; public nested `plan`; `tasks` + `implement`; then
`validate` + cleanup-only `deliver`. Run the deterministic, credential-free example from a source
checkout:

```bash
uv sync
uv run python operations/concorde-standard-dev-loop/operation.py "Add audit logging" --describe-policy
```

The base Concorde installer remains Python-only and offline; LangGraph is an optional workflow-host
dependency constrained to `langgraph>=1.2,<2`. See
[Workflow](docs/concorde-workflow.md#langgraph-operations) for the injected executor API
and installation boundary.

## Explore architecture and implementation alignment

The native read-only `concorde explore` Tool works without an implementation graph,
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
nor name/path similarity creates a mapping. The Tool emits canonical JSON to stdout and writes no
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
Concorde 2.1.0 installs 17 leaves and three complete Operation pairs in the framework while projecting
only 15 public leaves plus the three Operations.

See [Quick start](docs/quick-start.md).

## Maintain this checkout

Root `skills/`, `operations/`, `templates/`, `src/concorde/`, `scripts/`, `agent-assets/`, and
`docsite/` are canonical.
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

Python 3.11+ is the only hard requirement. Archify visual checks additionally need a Chrome or
Chromium build, which Playwright's bundled Chromium can supply through `ARCHIFY_CHROME`; see
[Recommended software](docs/quick-start.md#recommended-software).

## Repository map

| Path | Responsibility |
|---|---|
| `skills/` | Canonical public/internal leaf capabilities, one `SKILL.md` with exposure/effects per directory. |
| `operations/` | Paired public LangGraph `operation.py`/`SKILL.md` with ordered capabilities/bindings. |
| `templates/` | Complete feature/plan/task/checklist/constitution/reflection format references. |
| `src/concorde/` | Deterministic Tools plus Operations-owned graph, policy, path-context, and process-handoff programs. |
| `agent-assets/` | Canonical reflection-triage roles and integration templates. |
| `scripts/` | Portable runtime adapters, installer, and checkout sync. |
| `concorde.json` | Single package/version/profile/protocol/inventory authority. |
| `specs/concorde/` | Self-applied module architectures and direct features. |
| `.concorde/` | Native project configuration, selection, constitution, attempts, and reflections. |
| `tests/concorde/` | Python unit, contract, integration, and acceptance evidence. |
| `docsite/` | Architecture/feature publication adapter, packaged as every project's docsite template. |
| `docs/` | Public framework and contributor guidance. |

Concorde is distributed under the MIT License in `LICENSE`, declared by its package manifest and
included in every installed framework projection.
