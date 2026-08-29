---
title: Project Structure and Source Authority
sidebar_position: 5
---

# Project Structure and Source Authority

A Concorde workspace contains several kinds of information side by side: installed workflow
machinery, workflow control state, durable intent, one temporary delivery attempt, executable
evidence, and generated read models. They must not be treated as interchangeable.

## Workspace map

```text
<project>/
├── .concorde/
│   └── config.json                       # Concorde source profile and root module
├── .specify/
│   ├── feature.json                      # selected nested feature
│   └── extensions/concorde/              # installed adapter, launchers, runtime
├── .agents/skills/                       # one possible agent presentation
├── specs/<root-module>/
│   ├── module.md                         # root module summary: read first
│   ├── design.md                         # root module design reference
│   ├── reflections.md                    # the project's one reflection log (maintained; never removed)
│   ├── features/<number>-<feature>/      # what this level can do
│   │   ├── abstract.md                       # feature abstract: read first
│   │   ├── design.md                       # feature behavioral authority
│   │   ├── implementation.md               # feature's accepted implementation
│   │   ├── diagrams/                       # feature-owned Archify JSON, declared in design.md
│   │   ├── contracts/                      # feature-owned contracts
│   │   ├── subfeatures/<number>-<sub-feature>/ # optional; one level only
│   │   │   ├── abstract.md
│   │   │   ├── design.md
│   │   │   ├── implementation.md
│   │   │   ├── diagrams/
│   │   │   ├── contracts/
│   │   │   └── attempt/
│   │   └── attempt/               # at most one temporal attempt
│   └── architecture/                     # how this level is composed
│       ├── diagrams/<name>.json          # level views and explanatory views, linked from the docs
│       ├── contracts/<contract>/         # the module's boundary contracts
│       │   ├── contract.md
│       │   ├── schema.*
│       │   └── example.*
│       └── modules/<child-module>/       # immediate submodules; each repeats the module package
├── docs/                                 # explanatory project guides
├── <source directories>/                 # executable implementation
├── <test directories>/                   # executable evidence
├── generated/                            # ignored, reproducible diagram deliveries
└── docsite/                              # publication code and disposable output
```

Architecturally meaningful modules do not have to map one-to-one to source directories. The
`specs/` hierarchy expresses ownership and abstraction; the feature's accepted implementation in
feature `implementation.md` can point from that model to the concrete code that realizes it.

## Authority classes

| Class | Representative paths | What it can establish |
|---|---|---|
| Workflow control | `.concorde/config.json`, `.specify/feature.json` | Where sources and the active feature are located—not project behavior |
| Installed tooling | `.specify/extensions/concorde/`, agent skill or slash-command directories | How the installed workflow is invoked—not project intent |
| Maintained architecture | `module.md` (module summary), `architecture/contracts/`, the level views under `architecture/diagrams/` | Responsibility, boundaries, the features specified at the level, and current-level organization |
| Module design reference | `design.md` beside each `module.md` | Implementation detail, rationale, alternatives, and decisions for one level; it explains module architecture and never redefines it |
| Feature orientation | `abstract.md` beside each `design.md` | A self-contained quick understanding of one feature; it summarizes `design.md` and never defines beyond it |
| Durable feature intent | `design.md`, feature contracts, declared diagrams | Required behavior, normative feature representations, and representative explanations |
| Feature implementation | `implementation.md` beside each feature `design.md` | How the accepted implementation realizes one feature, in full implementation detail |
| Temporary attempt | `attempt/**` | Proposed work, task/checklist state, research, and current evidence |
| Project reflection log | `reflections.md` beside the root `module.md` | Every difficulty or problem an agent met during any attempt, attributed to a feature and naming the source it concerns, with maintainer-owned statuses; not behavioral authority |
| Executable reality | Source and tests | What code exists and what executable checks demonstrate |
| Generated read model | `generated/`, `docsite/.generated/`, `docsite/build/` | An ignored, reproducible presentation of maintained sources |

Location alone does not prove authority. In particular, a file under
`specs/**/attempt/` remains temporary, and a generated page remains non-authoritative even if
it is committed under a project-specific policy.

## Find the correct edit location

| You want to change… | Edit or invoke… |
|---|---|
| Required behavior, scope, failure handling, or success criteria | The owning feature's `design.md` through specification review, with its `abstract.md` updated wherever it summarized the change |
| The level at which a feature is specified, or the modules that realize it | The feature's placement (its `module` and canonical root) and the affected module packages, with architecture review |
| A module boundary or immediate-child organization | `module.md`, the affected contracts under `architecture/contracts/`, and the level views under `architecture/diagrams/` together |
| Why a level is built the way it is, or implementation detail beneath its summary | The module's `design.md`, edited directly or amended by an approved acceptance proposal; keep `module.md` a summary |
| Information crossing a boundary | The owning contract and any normative schema/example |
| How an accepted implementation realizes a feature | Complete the attempt and use approved implementation acceptance to write feature `implementation.md`; do not directly promote a plan |
| The current implementation approach or work order | Files under the selected feature's `attempt/` directory |
| Runtime behavior or executable proof | Source code and tests, reconciled against the durable sources |
| Adoption or contributor explanation | Markdown under `docs/` |
| Diagram meaning | Maintained Archify JSON (a module's `architecture/diagrams/` or a feature's `diagrams/`) and its textual counterpart—not delivered HTML |
| Site rendering or validation behavior | Code under `docsite/`—not copied canonical content |

When two artifacts disagree, resolve the disagreement in the artifact that owns the fact. For
example, do not edit a module or feature `design.md` to redefine a module boundary, do not let
`abstract.md` state what `design.md` does not, and do not weaken `design.md` merely to match incomplete
code. Concorde validation reports disagreement but does not choose a new authority for you.

## Nested feature selection

Normal Spec Kit originally assumes a relatively flat feature workspace. Concorde allows the selected
feature to live at any module level in the recursive hierarchy and to be either a top-level feature
or one immediate sub-feature. Selection itself is standard Spec Kit: the project-scoped
`.specify/feature.json` stores the canonical feature root, written by the specify phase or set
explicitly through `SPECIFY_FEATURE_DIRECTORY`. Concorde adds no selection command and no second
selection store.

Feature Workspace Protocol v8 classifies the selected root before every normal phase: safe path,
canonical `abstract.md`/`design.md`/`implementation.md` trio with no legacy names or attempt directory, workspace kind,
`attempt_state`, and the `module.md` and `design.md` of the module at which the feature is
specified (the result's `providing_module`) as navigation references. The result names the trio as
`feature_abstract`, `feature_design`, and `feature_implementation` and the module pair as
`module_summary` and `module_design`. For a sub-feature it also returns the parent's durable trio as read-only context
and concise sibling summaries; no parent/sibling attempt is an implicit input or output.

The installed workspace adapter derives phase-specific paths from the selection:

| Phase class | Durable inputs and outputs | Temporary inputs and outputs |
|---|---|---|
| Specify and clarify | Root `abstract.md` and `design.md` (a new root also receives placeholder `implementation.md`), existing feature `implementation.md` as read-only accepted context, feature contracts | Generated review state under `attempt/checklists/` |
| Checklist | Durable feature context, the abstract included | `attempt/checklists/*.md` |
| Plan | Root `design.md` and feature `implementation.md`, module `module.md` as bounded context; the abstract for orientation only; module `design.md` only deliberately, with citation; appends problems to the project reflection log | Plan, research, model, and quick start under `attempt/` |
| Tasks, implementation, analysis, convergence, issue conversion | Durable feature context; analysis also reads `abstract.md` to report disagreement with `design.md`; every phase appends problems to the project reflection log (`workspace.reflections`) and reports the feature's open count | The same active `attempt/` attempt |
| Acceptance | Root `abstract.md`, `design.md`, and current `implementation.md`, module `module.md` and `design.md`, the project reflection log, plus the complete attempt | Approved update to feature `implementation.md` (citing open reflection entries) and optional amendment of module `design.md`, applied atomically; exact removal of `attempt/`; the log is left byte-identical |

Selecting a feature changes routing state; requesting bounded context does not. The distinction is
explained in [Commands and installed surfaces](commands.md).

## Publication paths

The documentation site reads architecture and feature sources from `specs/` and project guides from
`docs/`. It stages disposable projections beneath `docsite/`, validates a candidate build, and only
then promotes successful output. Each module page embeds every diagram beneath its
`architecture/diagrams/` and links its `design.md` as a separate design-reference page; published
routes drop the `architecture/` grouping segment (`/architecture/<root>/modules/<child>/…`,
`/architecture/<root>/contracts/<id>/…`). Features are a separate semantic projection: a top-level
feature opens at `/features/<feature-id>`, and an immediate sub-feature opens beneath its explicit
parent feature route. Module placement and adjacent-level refinement remain metadata and links, so
architecture/module storage directories never become Features hierarchy nodes. The design
(`…/design`) and implementation (`…/implementation`) remain companion pages. Plans,
tasks, checklists, and other attempt artifacts are excluded from the public Features collection.

See the [root architecture](../specs/concorde/module.md) for Concorde's own module hierarchy and
[Feature 002](../specs/concorde/features/002-create-project-docsite/design.md) for the complete
publication contract.
