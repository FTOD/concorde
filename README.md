# Concorde

Concorde is a standalone, module-centered architecture and feature workflow for maintainers and
coding agents. It provides one structural entry point per module, one complete specification per
feature, committed-base isolated worktrees for agent mutations, bounded implementation context,
deterministic validation, and cleanup-only delivery.

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
├── reflections/pending/R-NNN.md  # recorded problems awaiting triage
├── reflections/planned/R-NNN.md  # triaged; plan proceeds without a maintainer
├── reflections/needs-comments/   # triaged; waiting for maintainer User Comments
├── framework/                    # installed Concorde package projection
└── install.json                  # installed-output ownership receipt
```

A module is the only recursive specification unit. Its `architecture.md` owns responsibility,
boundary, immediate children/features, significant typed entities, directed relationships, and
representative interactions. A feature is one direct Markdown file with outcome/scope, usage,
scenarios, requirements, embedded provided/required interfaces, and an Architecture Zoom over
visible entity IDs. Modules are partitioned by business capability, use case, or axis of change,
never by artifact type: a module owns every Skill, Tool, Operation, template, and rule its
capability needs, and its features are use cases of that capability.

Source code is implementation. Tests and deterministic checks are evidence. Plans, tasks, research,
checklists, and validation logs are temporary attempt memory. Generated sites/diagrams and
installed framework/agent files are reproducible projections, never intent authority.

Module architectures and direct feature files are also the maintained project documentation; there
is no parallel custom-document tree. Read the [project ontology and specification model](specs/concorde/features/002-project-ontology.md)
and the [understanding module architecture](specs/concorde/modules/understanding/architecture.md),
which owns the file-role ontology and Feature Workspace Protocol 13.

Concorde applies the partition to itself. Its six capability modules are:

| Module | Capability |
|---|---|
| [`understanding`](specs/concorde/modules/understanding/architecture.md) | Know what a project is: model, load, validate, bound context, explore alignment, answer questions. |
| [`lifecycle`](specs/concorde/modules/lifecycle/architecture.md) | Change one feature safely from specify through plan, tasks, implement, validate, and deliver. |
| [`reflections`](specs/concorde/modules/reflections/architecture.md) | Record one problem per file and triage it to maintainer disposition. |
| [`capabilities`](specs/concorde/modules/capabilities/architecture.md) | Run any Tool, Skill, or Operation on a coding agent under an enforced policy and project it to Codex and Claude. |
| [`distribution`](specs/concorde/modules/distribution/architecture.md) | Package, install, and update Concorde with an isolated Operation runtime. |
| [`auto-docs`](specs/concorde/modules/auto-docs/architecture.md) | Scaffold and publish the validated documentation site. |

### Concorde Protocol and self-evolution

**Concorde Protocol** is the complete normative process by which a selected feature is resolved,
permission-bounded, specified, planned, executed, validated, reflected on, and delivered, together
with its Source Profile and control-state authority rules. Feature Workspace Protocol 13 is one
serialized component of that process, not a synonym for the whole Protocol.

Every Concorde project consumes Concorde Protocol. This repository alone also defines and implements
it, so a normative Protocol change cannot safely ask an attempt governed by the old Protocol to host
and deliver its replacement. Constitution 8.1.0 therefore requires every such change—even an
apparently compatible one—to use the root
[Protocol-evolution feature](specs/concorde/features/003-evolve-concorde-protocol.md): start from one
exact committed base with no active attempt in that commit, build the complete target directly in an
isolated Git worktree, run full target validation, and merge one reviewable cutover commit. Staged,
unstaged, untracked, and ignored primary-worktree content is excluded and left untouched. It uses no selection,
attempt, checklist, fast loop, standard loop, or delivery. A code/test fix that restores already
specified Protocol behavior remains normal lifecycle work.

The same committed-base rule is the default for normal agent changes. Read-only work may remain in
the primary worktree, but before planning, persisting selection, creating an attempt/checklist/
reflection, changing project files, or writing external state, the agent creates or enters a unique
linked worktree at the primary worktree's exact committed `HEAD`. A generic change request never
authorizes primary-worktree mutation. If required input exists only in dirty primary state, the agent
reports it missing instead of stashing or copying it.

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
[Workflow](specs/concorde/features/001-concorde-workflow.md) and
[Capability surfaces](specs/concorde/modules/capabilities/features/002-provide-capability-surfaces.md).

## Compose prompts with LangGraph

Canonical `skills/*/SKILL.md` files are complete leaves with public/internal exposure and
machine-readable effects when composed. Operations resolve whole direct Skills or public Operations
into ordered [LangGraph](https://github.com/langchain-ai/langgraph) stages without copying/flattening
prompts. LangGraph is control plane only: trusted code resolves concrete paths, narrows leaf effects,
renders a Codex permission profile or Claude restricted strict sandbox, and requires a receipt.

The four stages are specify, plan, tasks, and deliver. Their direct bundles preserve the full
lifecycle: specify; public nested plan; tasks then implement; validate then cleanup-only deliver.
Run this deterministic, credential-free policy inspection from Concorde's source checkout:

```bash
uv sync
python3 - <<'PY' | python3 scripts/run-operation.py operations/concorde-standard-dev-loop/operation.py
import json
from pathlib import Path
configuration = json.loads(Path(".concorde/config.json").read_text())["operation_configuration"]
print(json.dumps({
    "type_id": "concorde-operation-invocation", "schema_version": 1,
    "operation_id": "concorde-standard-dev-loop", "mode": "describe-policy",
    "configuration": configuration,
    "input": {"type_id": "concorde-standard-dev-loop-context", "schema_version": 1,
              "data": {"feature_path": "specs/concorde/modules/lifecycle/features/006-standard-development-loop.md",
                       "request": "Inspect the configured development policies", "constraints": []}}
}))
PY
```

For actual work, set `mode` to `execute` and provide the selected feature/task in an authorized
isolated worktree with the configured Codex or Claude CLI available. The Python process reads one
JSON invocation on stdin and emits one typed result on stdout; policy descriptions use stderr.
Old positional task requests and domain flags are rejected. The agent CLI's public Operation Skill
constructs this same JSON boundary and the Python graph owns all subsequent dispatch.

The standard loop requires an existing direct feature with a resolved stable ID. Create a new feature
with `$concorde-specify` first, complete its post-front-matter workspace resolution, and then pass the
resulting `feature_path` to `$concorde-standard-dev-loop`.

The checkout launcher selects its root `.venv`. Native installation instead creates and verifies a
private `.concorde/.venv`, never touches the target project's `.venv`, and may contact the configured
package index while applying. After installation, all paired Operations start from the private
environment without dependency downloads or package-index access.

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

Concorde requires Python 3.11+, Node.js 18+, npm, and no host framework. Preview is the default and
does not contact either the Python package index or the official Viewer release:

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
Concorde 3.0.0 installs 17 leaves and three complete Operation pairs in the framework while projecting
only 15 public leaves plus the three Operations. During explicit apply it also runs
`npm ci --ignore-scripts` from the shipped lock to install the official Understand Anything Viewer
v2.9.0 beneath `.concorde/.venv/share/concorde/understand-anything-viewer`. The target project's
`package.json`, lock files, `node_modules`, and root `.venv` are never used or modified. Once apply
succeeds, both Operations and the Viewer start without dependency downloads.

### Open the official Understand Anything Viewer

First generate the raw graph with Understand Anything so the installed project contains
`.ua/knowledge-graph.json` (or the official legacy `.understand-anything/knowledge-graph.json`). Then,
from that project, run:

```bash
python3 .concorde/framework/scripts/run-viewer.py --project-root .
```

The official Viewer binds to `127.0.0.1`, prints its tokenized dashboard URL, and opens the browser.
Use `--no-open` on a headless host and `--port 0` to select any free port:

```bash
python3 .concorde/framework/scripts/run-viewer.py \
  --project-root . \
  --port 0 \
  --no-open
```

This launcher accepts only the original UA graph in its conventional project directory. The JSON
printed by `concorde explore` is a bounded specification-to-code evidence envelope for agents and CI;
it is deliberately rejected as Viewer input. If launch reports that the Viewer is missing or
unhealthy, rerun `scripts/install-concorde.py ... --apply` from the matching Concorde checkout. If it
reports a Node/npm prerequisite failure, install Node.js 18+ with its npm command and apply again.

See the complete [installation feature](specs/concorde/modules/distribution/features/002-install-concorde.md) and
[workflow usage](specs/concorde/features/001-concorde-workflow.md#usage).

## Maintain this checkout

Root `skills/`, `operations/`, `templates/`, `src/concorde/`, `scripts/`, `agent-assets/`, `viewer/`,
and `docsite/` are canonical.
Tracked `.agents/**` and `.claude/**` files are generated source-checkout projections; Concorde does
not install a duplicate `.concorde/framework` into its own repository.

```bash
python3 scripts/development/sync-agent-surfaces.py status --format json
python3 scripts/development/sync-agent-surfaces.py apply --format json
```

See [Agent-surface maintenance](specs/concorde/modules/capabilities/features/004-maintain-agent-surfaces.md).

Normative Concorde Protocol evolution is the one checkout-maintenance exception. Do not invoke any
`concorde-*` mutation Skill or Operation for it. After explicit maintainer authorization, require a
committed checkpoint with no active attempt in that commit; create a dedicated branch/worktree
without importing primary dirty state, reconcile every
affected authority directly, run the complete validation commands below, and merge one cutover
commit. Abandon a failed pre-merge worktree or immediately revert a failed merged cutover before
later work. See [Evolve the Concorde Protocol](specs/concorde/features/003-evolve-concorde-protocol.md).

## Operation Concept and Data Contracts

Start with the [project concept model](specs/concorde/architecture.md#project-concept-model): an
Operation definition, its agent Skill and executable Python, a particular invocation, project
configuration, typed runtime input/result, and artifact handoffs are distinct entities.
The architecture includes a [concrete Operation registry](specs/concorde/architecture.md#operation-registry),
cardinalities, ownership/lifetimes, producer-to-consumer field mappings, and a runtime realization
review. Its entity view and Archify dataflow complement the module map.

The [JSON boundary](specs/concorde/modules/capabilities/features/002-provide-capability-surfaces.md#operation-data-contract)
separates project configuration from per-call input such as `concorde-plan-context@1`. The host
validates type/version/fields, copies the configuration snapshot into nested calls, and checks
feature identity, artifact digests, and native completion evidence before handing data on.
Triage investigation returns typed findings; its parent preserves maintainer fields and saves and
relocates validated records. Standard-loop success requires real validation and delivery cleanup.

### Initialize or migrate project configuration

Concorde 3.0.0 changes the Operation ABI; existing source-profile settings remain version 7.
Create `operation-settings.json` with explicit settings (choose the integration actually in use):

```json
{"type_id":"concorde-operation-configuration","schema_version":1,"data":{"integration":"codex","enforcement":"native"}}
```

For a new project, `python3 scripts/concorde.py init --propose --configuration operation-settings.json`
produces Initialization Proposal 4 with five files: project config, root architecture, system
overview, reflection allocation index, and reflection defaults. Review and apply the accepted
proposal with `init --apply --proposal <path>`.

For an existing initialized project, preserve the authored hierarchy and other config fields:

```bash
python3 scripts/concorde.py configure --propose --configuration operation-settings.json > configuration-proposal.json
# Review the exact proposal before applying it.
python3 scripts/concorde.py configure --apply --proposal configuration-proposal.json
```

In installed projects use `.concorde/framework/scripts/concorde.py`. Missing configuration blocks
Operations; stale proposals require a fresh proposal. Later runs load the new settings, while an
active run and its nested Operations keep their original snapshot. `outer` enforcement additionally
requires a verified embedding host. Source/installed managed runtime checks include all three
registered JSON contracts. Integration tests run real graphs, artifact IO, queue, and delivery tools
with an explicit model-process double; they do not claim live model work.

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
[`specs/concorde/architecture.md`](specs/concorde/architecture.md). Normal changes use Concorde's
standard lifecycle from a committed-base linked worktree; normative Concorde Protocol changes use
the isolated bootstrap cutover above.

Python 3.11+ is required for Concorde itself. Native installation additionally requires Node.js 18+
and npm so the pinned official Viewer can be provisioned. Archify visual checks need a Chrome or
Chromium build, which Playwright's bundled Chromium can supply through `ARCHIFY_CHROME`; see
the [Auto-Docs renderer contract](specs/concorde/modules/auto-docs/features/001-publish-project-docsite.md).

## Repository map

| Path | Responsibility |
|---|---|
| `skills/` | Canonical public/internal leaf capabilities, one `SKILL.md` with exposure/effects per directory. |
| `operations/` | Paired public LangGraph `operation.py`/`SKILL.md` with ordered capabilities/bindings. |
| `templates/` | Complete feature/plan/task/checklist/constitution/reflection format references. |
| `src/concorde/` | The Python package realizing every capability module: understanding, lifecycle, reflections, capabilities, distribution, and the docsite scaffold. |
| `agent-assets/` | Canonical reflection-triage roles and integration templates. |
| `scripts/` | Portable runtime adapters, installer, and checkout sync. |
| `viewer/` | Pinned npm package and lock that install the official Understand Anything Viewer into Concorde's managed runtime. |
| `concorde.json` | Single package/version/profile/protocol/inventory authority. |
| `specs/concorde/` | Self-applied capability-partitioned module architectures and direct features; the maintained project documentation. |
| `.concorde/` | Native project configuration, selection, constitution, attempts, and reflections. |
| `tests/concorde/` | Python unit, contract, integration, and acceptance evidence. |
| `docsite/` | Architecture/feature publication adapter, packaged as every project's docsite template. |

Concorde is distributed under the MIT License in `LICENSE`, declared by its package manifest and
included in every installed framework projection.
