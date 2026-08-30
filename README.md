# Concorde

Concorde extends [Spec Kit](https://github.com/github/spec-kit) with a hierarchical architecture
workflow for AI-developed software. It keeps feature specifications aligned with the module hierarchy
that realizes them, boundary contracts, bounded architecture views, and accepted implementation
evidence, so that a maintainer can understand any level of the project in minutes.

## Key features

- **Hierarchical zoomable architecture** — start at the project, understand one module at a time, and descend only
  when the question needs more detail.
- **Architecture-aware specifications** — place each feature where all participating modules are
  visible, with stable IDs and explicit refinement relationships.
- **Bounded agent context** — retrieve one architectural level without silently loading child
  internals, unrelated features, or accepted implementation detail.
- **Human-readable contracts** — record boundary direction, exchanged information, obligations, and
  failure behavior alongside the modules and features that rely on them.
- **Durable intent, temporal attempts** — keep specifications and accepted realizations separate from
  disposable plans, tasks, research, validation, and in-progress implementation work.
- **Deterministic validation and review gates** — check hierarchy, references, contracts, diagrams,
  evidence, and generated-output freshness without an LLM; architecture and acceptance changes remain
  explicit human decisions.
- **One generated project read model** — publish the README, architecture, guides, feature abstracts,
  designs, accepted implementations, contracts, and interactive diagrams as a searchable Docusaurus
  site without turning generated pages into sources.

## Concorde commands

The Concorde extension adds five agent-facing commands. Feature delivery still uses Spec Kit command names, and
the `concorde` preset **modifies the installed agent instructions for nine of them** so every
phase resolves the selected hierarchical feature workspace and respects durable versus temporal
file boundaries. `speckit.constitution` keeps its native Spec Kit instructions.
The preset also adds `$speckit-fast-loop`, an alternate direct-edit surface for an established small
change beginning from one selected anchor and spanning a bounded set of related existing features.

| Command | Use it to |
|---|---|
| `$speckit-concorde-init` | Propose a root Concorde architecture and apply it only after explicit approval. |
| `$speckit-concorde-context <module-or-feature-id>` | Retrieve exactly one bounded architectural level. |
| `$speckit-concorde-ask <question>` | Get a cited, read-only answer about Concorde or its use in the current project. |
| `$speckit-concorde-validate` | Deterministically validate the maintained hierarchy, contracts, views, documents, and evidence. |
| `$speckit-concorde-impl-accept <feature-id>` | Propose and, after explicit approval, accept a completed implementation as the durable realization. |

Features are created with the normal `$speckit-specify` phase at their canonical module path and
selected through `.specify/feature.json`; Concorde deliberately adds no separate create or select
command.

### Related Spec Kit commands under Concorde

These are agent skills or slash commands, not shell commands. “Modified by Concorde” means the
Concorde preset supplies the installed instructions while Spec Kit still owns the phase and its
public command name; the commands continue to exist and should still be used.

| Command | Installed behavior with Concorde | Instruction source |
|---|---|---|
| `$speckit-constitution` | Creates or updates only `.specify/memory/constitution.md`, the project policy read by later phases. It does not create Concorde architecture or feature files. | Native Spec Kit |
| `$speckit-specify` | Creates or revises the selected feature's durable `abstract.md` and `design.md`, seeds a new placeholder `implementation.md` while preserving an existing accepted one, persists `.specify/feature.json`, and creates the built-in requirements checklist under `attempt/checklists/`. | Modified by Concorde |
| `$speckit-clarify` | Resolves behavioral ambiguity in the selected feature, updating `design.md` and every affected summary in `abstract.md`; it may re-evaluate the existing requirements checklist but never edits `implementation.md`. | Modified by Concorde |
| `$speckit-checklist` | Reads durable feature intent plus available plan/task context and creates or appends a reviewer-owned requirements-quality checklist under `attempt/checklists/`; generated items remain unchecked until reviewed. | Modified by Concorde |
| `$speckit-plan` | Reads the constitution, feature `design.md`, accepted `implementation.md` baseline, and bounded module architecture; writes `attempt/plan.md`, research/data-model/quickstart artifacts, and durable feature `contracts/**`, and may append problems to project `reflections.md`. | Modified by Concorde |
| `$speckit-tasks` | Converts the selected plan and durable feature intent into dependency-ordered executable work at `attempt/tasks.md`, using accepted `implementation.md` as the prior baseline; it may append problems to project `reflections.md`. | Modified by Concorde |
| `$speckit-analyze` | Checks consistency across `abstract.md`, `design.md`, accepted `implementation.md`, plan, tasks, and constitution. It returns a report without modifying them; its only permitted file write is appending a problem to the project `reflections.md`. | Modified by Concorde |
| `$speckit-implement` | Reads durable intent, accepted realization, `attempt/plan.md`, `attempt/tasks.md`, and checklists; edits product code/tests, marks task state, and may append reflections. It never accepts `implementation.md` or removes `attempt/`. | Modified by Concorde |
| `$speckit-converge` | Compares code with durable intent and the active attempt, then append-only adds remaining work to `attempt/tasks.md` and may append reflections. It does not edit code or durable feature/module files. | Modified by Concorde |
| `$speckit-taskstoissues` | Reads the selected `attempt/tasks.md`, deduplicates task IDs against GitHub, and creates missing external issues. It does not move task authority out of the workspace or modify the task file. | Modified by Concorde |
| `$speckit-fast-loop <small-change description>` | Starts from one selected anchor, discovers every affected existing feature, requires accepted/no-attempt baselines for all, then directly reconciles code, tests, feature specs, and related contract/architecture/user docs. Module responsibility/dependency changes, project-level user compatibility/migration policy changes, ambiguity, and unsafe worktree overlap redirect to the full workflow; architecture edits require exact maintainer review. | Added by Concorde |

A typical combined workflow is:

```text
speckit.specify → speckit.clarify/checklist → speckit.plan → speckit.tasks
                → speckit.analyze → speckit.implement → speckit.converge
                → speckit.concorde.validate → speckit.concorde.impl.accept
```

Clarification, checklists, analysis, and convergence are used when needed; validation can run
repeatedly, and acceptance is always a separate approval-gated Concorde operation. See
[Commands](docs/commands.md) for complete timing, inputs, outputs, and installed execution layers.
For an eligible established small change, select an anchor feature and invoke `speckit.fast-loop`;
it resolves every affected feature explicitly, creates no attempt, and performs no acceptance
operation.

Explore the project through its three generated views:
[Architecture](specs/concorde/module.md), [Documentation](docs/index.md), and
[Features](specs/concorde/features/001-concorde-workflow/abstract.md).

## How Concorde fits Spec Kit

Concorde is designed to be installed as a native Spec Kit bundle containing:

- the `concorde` preset, which appends architecture guidance to Spec Kit's templates, supplies
  the feature abstract, design-reference, and reflection-log templates, modifies nine normal command
  instructions with Concorde-aware workspace routing, and adds one fast-loop command;
- the `concorde` extension, which supplies five Concorde surfaces—four runtime-backed operations plus
  the read-only `ask` procedure—the workspace adapter, and runtime; and
- no second workflow: Spec Kit continues to own specification, planning, tasks, and
  implementation.

The three Spec Kit package concepts have different jobs:

| Concept | Concorde package | Role |
|---|---|---|
| Bundle | `concorde-bundle` | An installation recipe that pins the tested preset and extension versions. |
| Preset | `preset:concorde` | Six templates (three append layers plus the `abstract-template`, `implementation-template`, and `reflections-template` documents), complete instruction modifications for nine normal commands, and one fast-loop command. |
| Extension | `extension:concorde` | Five Concorde-specific surfaces: four deterministic operations and one agent-followed, read-only question procedure. |

Catalogs are trusted discovery metadata for these independently versioned packages; they are not a
fourth installed runtime component. See the maintained
[component model](specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json),
[installation flow](specs/concorde/features/003-install-concorde-speckit/diagrams/bundle-installation-flow.json),
and the full [Feature 003 setup specification](specs/concorde/features/003-install-concorde-speckit/design.md).
The project docsite build turns module-owned and feature-declared diagram sources into interactive
standalone views.


## Quick start: install Concorde as a Spec Kit bundle

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) and its `uvx` command
- a supported coding-agent integration; Codex skills mode is the one exercised by the acceptance
  suite and by development self-hosting

The installer runs inside an ephemeral `specify-cli==0.16.4` environment. You do not need to install
Python, Spec Kit, clone Concorde, create a virtual environment, build archives, or run a catalog
server first.

### Install the current published release

From the empty directory or existing Spec Kit project you want to enable, run one command (replace
`codex` with your integration):

```bash
curl -fsSL https://raw.githubusercontent.com/FTOD/concorde/main/scripts/install-concorde.py \
  | uvx --from specify-cli==0.16.4 python - --integration codex
```

For an existing project, `--integration` may be omitted; if supplied, it must match the project's
recorded default. Add `--target PATH` to act on another directory or `--version 0.1.0` to select an
immutable published release. The command prints Spec Kit's exact expanded bundle plan before it
installs or updates anything, then reports the bundle, preset, extension, versions, reload need, and
next workflow step.

Preview the same plan with zero target writes:

```bash
curl -fsSL https://raw.githubusercontent.com/FTOD/concorde/main/scripts/install-concorde.py \
  | uvx --from specify-cli==0.16.4 python - --integration codex --preview
```

Because piping remote code deserves scrutiny, you can download and inspect the exact plain-text
installer first:

```bash
curl -fsSLo install-concorde.py \
  https://raw.githubusercontent.com/FTOD/concorde/main/scripts/install-concorde.py
less install-concorde.py
uvx --from specify-cli==0.16.4 python install-concorde.py --integration codex
```

The installer is an optional accelerator over public Spec Kit operations; it never copies component
files or bypasses bundle ownership. Its full inputs, outputs, and failure behavior are in the
[one-command installation design](specs/concorde/features/003-install-concorde-speckit/subfeatures/002-one-command-install/design.md).
The manual native path remains in the [framework quick start](docs/quick-start.md).

### Install current checkout sources (development)

From a Concorde checkout, install the current unreleased sources into a disposable or existing
target with the same command:

```bash
target_project="$(mktemp -d)"
uvx --from specify-cli==0.16.4 python scripts/install-concorde.py \
  --target "$target_project" --integration codex --checkout "$PWD"
```

Development mode builds and verifies the checkout before touching the target, serves its catalogs on
an ephemeral loopback port for this run only, installs through the same bundle lifecycle, removes the
transient `concorde-dev` catalog registrations, and stops the server. Repeating it at the same version
changes no target bytes.

### Use the Concorde commands

After installation, invoke these agent skills from the target project:

```text
$speckit-concorde-init
$speckit-concorde-impl-accept feature.<project-slug>.<name>
$speckit-concorde-context module.<project-slug>
$speckit-concorde-validate
$speckit-concorde-ask When should I use context instead of changing the selected feature?
```

- `init` proposes a root architecture package—`.concorde/config.json`, a `module.md` summary, a
  seeded `design.md` design reference, and a first level view at
  `architecture/diagrams/level-view.json`—and writes it only after explicit approval.
- Features are created with the normal `$speckit-specify` phase after exporting
  `SPECIFY_FEATURE_DIRECTORY` at their canonical path—`<module directory>/features/NNN-<short-name>`,
  or `<parent feature root>/subfeatures/NNN-<short-name>` for a sub-feature—and are selected
  through the standard `.specify/feature.json`; Concorde adds no creation or selection command.
  Every feature root owns `abstract.md` (read first), `design.md` (the authority), and
  `implementation.md` (the accepted implementation, written by acceptance).
- `impl.accept` proposes the feature `implementation.md`—and, when the attempt produced detail or
  rationale worth keeping, an amendment to the `design.md` of the module at which the feature is
  specified—from a task-complete implementation attempt and, only after explicit approval, applies
  both atomically and removes that temporal `attempt/` directory.
- `context` returns one bounded architectural level without expanding child internals or the body
  of any module `design.md` or feature `implementation.md`.
- `validate` deterministically checks identities, hierarchy, module layout, references, contracts,
  views, evidence status, module summary and feature abstract shape and reading budgets, and the feature-root document
  trio.
- `ask` answers questions about Concorde concepts, command timing, artifact authority, or this
  project's use of the workflow from cited installed guidance and bounded maintained sources. It is
  agent-followed and read-only: it has no Python runtime verb and does not execute recommended work.

Use `ask` whenever the uncertainty is about how Concorde itself works or applies to the current
project. Use `context` when you need the deterministic one-level architecture projection, and use
the normal Spec Kit phases when you intend to change specifications or implementation.

Project-authored `.concorde/` configuration and the unified `specs/` hierarchy are retained when the
bundle is updated or removed.

## Run this project's documentation site

The published site is available at [ftod.github.io/concorde](https://ftod.github.io/concorde/).
Every push to `main` rebuilds the canonical sources and deploys the verified output through the
repository's GitHub Pages workflow; generated site files are not committed.

The independent `docsite/` package, documented in the
[docsite contributor guide](docs/contributing/docsite.md), builds Concorde's own read-only Docusaurus
site from the root README and two canonical source trees, presented through a shared homepage and
three reader-facing navigation families:

| Source | Published content |
|---|---|
| `README.md` | The project homepage at `/`, including this same introduction, feature summary, and command overview |
| `specs/**/module.md`, its adjacent `design.md`, `specs/**/architecture/contracts/**/contract.md`, `specs/**/architecture/diagrams/*.json` | Architecture module summaries (each embedding its module-owned Archify diagrams), module design references, and boundary contracts |
| `docs/**/*.md` | Project documentation |
| Feature-root `abstract.md`, `design.md`, and `implementation.md` | Feature abstracts (the landing pages), behavioral designs, and accepted implementations |

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
production Docusaurus build. Start with the maintained [documentation overview](docs/index.md) and
[framework quick start](docs/quick-start.md); see the
[docsite contributor guide](docs/contributing/docsite.md) for authoring rules and troubleshooting.

## Project orientation

- [Project constitution](https://github.com/FTOD/concorde/blob/main/.specify/memory/constitution.md)
- [Root architecture](specs/concorde/module.md) (module summary; its design reference is the adjacent `design.md`)
- [Concorde workflow abstract](specs/concorde/features/001-concorde-workflow/abstract.md) and [specification](specs/concorde/features/001-concorde-workflow/design.md)
- [Project docsite specification](specs/concorde/features/002-create-project-docsite/design.md)
- [Spec Kit installation specification](specs/concorde/features/003-install-concorde-speckit/design.md)
- [Releasing Concorde](docs/releasing.md)
- [Development self-hosting specification](specs/concorde/features/004-self-host-concorde/design.md)
- [Workflow reflections specification](specs/concorde/features/005-record-workflow-reflections/design.md); the maintained log is `specs/concorde/reflections.md`


## Project status

Feature 001 defines the Concorde architecture-aware development workflow. Its root initialization,
Feature Workspace Protocol v8 resolution of the standard Spec Kit selection, bounded context,
deterministic validation, approval-gated implementation acceptance, and the read-only `ask` procedure are
implemented and covered by the automated suites, and this repository itself lives under the
three-tier feature document model (`abstract.md`, `design.md`, `implementation.md`) and the module summary/design
reference pair that the feature specifies. Feature 002's docsite publication pipeline, Feature 003's
native bundle, preset composition, five-surface extension, and release tooling, and Feature 004's
review-first self-hosting are implemented and tested. Feature 005 adds the project-wide reflection
log (`specs/concorde/reflections.md`): every phase after specification records the difficulties it
meets there, attributed to the feature being worked on and naming the source concerned, and
acceptance cites a feature's open entries; its runtime, guidance, and evidence are in progress in this
checkout. Timed human comprehension pilots and browser-based diagram review remain pending and are
kept separate from automated evidence.

The newest published release is `v0.1.0`, which predates the module design reference, the feature
abstract, and the removal of the `feature.create`/`feature.select` commands. This README and the guides
under `docs/` describe the `0.4.0` sources in this checkout; until `0.4.0` is published, the local
development path above is the way to use them.

Concorde can also install the current checkout's framework sources into this repository for
development self-application. That review-first path is deliberately separate from the release
bundle used by other projects; see [Developing Concorde with Concorde](docs/self-hosting.md).
