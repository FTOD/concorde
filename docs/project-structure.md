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
│   ├── module.md                         # root architectural prose
│   ├── architecture.json                 # root plus immediate children
│   ├── contracts/<contract>/
│   │   ├── contract.md
│   │   ├── schema.*
│   │   └── example.*
│   ├── features/<number>-<feature>/
│   │   ├── spec.md
│   │   ├── design.md
│   │   ├── contracts/
│   │   ├── diagrams/
│   │   ├── subfeatures/<number>-<sub-feature>/ # optional; one level only
│   │   │   ├── spec.md
│   │   │   ├── design.md
│   │   │   └── implementation/
│   │   └── implementation/
│   └── modules/<child-module>/           # repeats the module package
├── docs/                                 # explanatory project guides
├── <source directories>/                 # executable implementation
├── <test directories>/                   # executable evidence
├── generated/                            # reproducible diagram deliveries
└── docsite/                              # publication code and disposable output
```

Architecturally meaningful modules do not have to map one-to-one to source directories. The
`specs/` hierarchy expresses ownership and abstraction; the accepted feature design can point from
that model to the concrete code that realizes it.

## Authority classes

| Class | Representative paths | What it can establish |
|---|---|---|
| Workflow control | `.concorde/config.json`, `.specify/feature.json` | Where sources and the active feature are located—not project behavior |
| Installed tooling | `.specify/extensions/concorde/`, agent skill or slash-command directories | How the installed workflow is invoked—not project intent |
| Maintained architecture | `module.md`, module contracts, `architecture.json` | Responsibility, ownership, I/O boundaries, and current-level organization |
| Durable feature intent | `spec.md`, feature contracts, declared diagrams | Required behavior, normative feature representations, and representative explanations |
| Durable accepted realization | `design.md` | How the accepted implementation realizes one feature |
| Temporary attempt | `implementation/**` | Proposed work, task/checklist state, research, and current evidence |
| Executable reality | Source and tests | What code exists and what executable checks demonstrate |
| Generated read model | `generated/`, `docsite/.generated/`, `docsite/build/` | A reproducible presentation of maintained sources |

Location alone does not prove authority. In particular, a file under
`specs/**/implementation/` remains temporary, and a generated page remains non-authoritative even if
it is committed under a project-specific policy.

## Find the correct edit location

| You want to change… | Edit or invoke… |
|---|---|
| Required behavior, scope, failure handling, or success criteria | The owning feature's `spec.md` through specification review |
| Which module owns behavior | The relevant module package and feature placement, with architecture review |
| A module boundary or immediate-child organization | `module.md`, affected contracts, and `architecture.json` together |
| Information crossing a boundary | The owning contract and any normative schema/example |
| How an accepted implementation realizes a feature | Complete the attempt and use approved feature hardening; do not directly promote a plan |
| The current implementation approach or work order | Files under the selected feature's `implementation/` directory |
| Runtime behavior or executable proof | Source code and tests, reconciled against the durable sources |
| Adoption or contributor explanation | Markdown under `docs/` |
| Diagram meaning | Maintained Archify JSON and its textual counterpart—not delivered HTML |
| Site rendering or validation behavior | Code under `docsite/`—not copied canonical content |

When two artifacts disagree, resolve the disagreement in the artifact that owns the fact. For
example, do not edit `design.md` to redefine a module boundary, and do not weaken `spec.md` merely to
match incomplete code. Concorde validation reports disagreement but does not choose a new authority
for you.

## Nested feature selection

Normal Spec Kit originally assumes a relatively flat feature workspace. Concorde allows a selected
feature to live under any providing module in the recursive hierarchy and to be either a top-level
feature or one immediate sub-feature. The project-scoped
`.specify/feature.json` stores that canonical feature root.

Protocol v3 classifies the selected root. For a sub-feature it also returns the parent durable
spec/design as read-only context and concise sibling summaries; no parent/sibling attempt is an
implicit input or output.

The installed workspace adapter derives phase-specific paths from the selection:

| Phase class | Durable inputs and outputs | Temporary inputs and outputs |
|---|---|---|
| Specify and clarify | Root `spec.md`, `design.md` as read-only accepted context, feature contracts | Generated review state under `implementation/checklists/` |
| Checklist | Durable feature context | `implementation/checklists/*.md` |
| Plan | Root `spec.md` and `design.md` | Plan, research, model, and quick start under `implementation/` |
| Tasks, implementation, analysis, convergence, issue conversion | Durable feature context | The same active `implementation/` attempt |
| Hardening | Root `spec.md` and current `design.md` plus the complete attempt | Approved update to `design.md`; exact removal of `implementation/` |

Selecting a feature changes routing state; requesting bounded context does not. The distinction is
explained in [Commands and installed surfaces](commands.md).

## Publication paths

The documentation site reads architecture and feature sources from `specs/` and project guides from
`docs/`. It stages disposable projections beneath `docsite/`, validates a candidate build, and only
then promotes successful output. Plans, tasks, checklists, and other attempt artifacts are excluded
from the public Features collection.

See the [root architecture](../specs/concorde/module.md) for Concorde's own module hierarchy and
[Feature 002](../specs/concorde/features/002-create-project-docsite/spec.md) for the complete
publication contract.
