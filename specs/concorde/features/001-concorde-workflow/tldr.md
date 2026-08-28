# TL;DR: Concorde Workflow

`feature.concorde.workflow` · specified at `module.concorde` · about six minutes. This page is
enough to understand what the workflow does, how it is built, and how it works; the links at the
end only redirect you when you want more.

## Purpose

Concorde wraps the normal Spec Kit lifecycle with architectural controls so that a maintainer or a
coding agent can understand any level of a project in minutes and move one change from
architectural placement through specification, planning, implementation, validation, and accepted
realization without losing track of who owns which fact. It exists for the programmer who no
longer writes most of the code but still has to own the project, and for the agent that needs a
bounded, trustworthy context for every task.

The idea underneath everything: at every level there is a document that is **read** (absorbable in
minutes) and a document that is **consulted** (opened for one question), and only an explicit,
approved milestone turns work in progress into accepted realization.

## Functionality

**The document model** — what each file at a level is for:

| Where | File | What it is |
|---|---|---|
| module root | `module.md` | the summary of the level: responsibility, boundary, structure diagram, feature/contract/submodule tables, one scenario, key rationale; under 20 minutes |
| module root | `design.md` | the module design reference: implementation notes, rationale, alternatives, decision log; consulted, never required |
| feature root | `tldr.md` | this kind of page: purpose, functionality, structure, logic; under 15 minutes |
| feature root | `spec.md` | the complete behavioral authority: scenarios, requirements, success criteria |
| feature root | `design.md` | the feature design reference: how the accepted implementation realizes the feature, in full detail; written only by hardening |
| feature root | `implementation/` | the one attempt in progress: plan, tasks, checklists, research, evidence; removed when hardened |

**The command surfaces** — 14 in total, all reached through the active coding-agent integration as
skills or slash commands:

| Surface | What it does |
|---|---|
| `speckit.concorde.init` | Proposes, and on approval creates, the root module package: `module.md`, `design.md`, the level view, initial contracts, `.concorde/config.json`. Idempotent. |
| `speckit.concorde.context` | Returns exactly one level — a module with its immediate children, current-level features, contracts, and scenarios, or a feature with its parent and siblings — with any `design.md` as a link, never as content. |
| `speckit.concorde.ask` | Answers a workflow question read-only from installed guidance, module summaries, and feature TL;DRs, citing anything deeper it opens. Agent-followed; no runtime. |
| `speckit.concorde.validate` | Checks every maintained source deterministically and returns sorted findings with rule, severity, location, and remediation; byte-equivalent on repeat. |
| `speckit.concorde.feature.harden` | Turns a completed attempt into accepted realization: proposal, exact review, explicit approval, atomic apply. |
| `speckit.specify` · `clarify` · `checklist` | Author `tldr.md` and `spec.md` for the selected root, seed a placeholder `design.md` for a new root, and write review checklists under `implementation/checklists/`. |
| `speckit.plan` · `tasks` · `taskstoissues` | Plan one attempt from `spec.md`, the accepted `design.md`, and the level's `module.md`; write only under `implementation/`. |
| `speckit.implement` · `analyze` · `converge` | Execute the task list inside the attempt, report inconsistencies read-only, and append only genuine remaining work. |

**Not part of this feature**: installing or updating Concorde (`feature.concorde.install-with-spec-kit`),
building the docsite (`feature.concorde.publish-project-docsite`), a third containment level, a
second feature registry, a generated TL;DR, a reading budget for `spec.md`, and any migration
command or compatibility alias for earlier document models.

## Structure

The core view is <a href="/architecture/concorde-workflow-components.html">workflow components</a>
(maintained source `diagrams/concorde-workflow-components.json`). In one sketch:

```text
Maintainer ──invoke · review · approve──▶ Coding-agent integration (skills / slash commands)
                                            ├─ 9 Spec Kit phase surfaces ──▶ selected-workspace adapter ──▶ .specify/feature.json
                                            └─ 5 Concorde surfaces ─────────▶ launchers + Python runtime ──▶ architecture sources
                                                 (init · context · validate · feature.harden · ask)        (module.md · design.md · views · contracts)

Selected feature root:   tldr.md   spec.md   design.md      +   implementation/  (one attempt, until hardened)
                         read      authority reference           plan · tasks · checklists · research · evidence
```

- **Spec Kit phase surfaces** are Spec Kit's own nine commands with a Concorde preset override
  that resolves the selected root *before* the phase runs, so no inherited helper can fall back to
  a root-level plan or task path.
- **Concorde surfaces** come from the `concorde` extension: four runtime operations plus the
  agent-only `ask`. The runtime is portable standard-library Python reached through launchers;
  installed projects never depend on the Concorde checkout.
- **The selected-workspace adapter** turns the standard `.specify/feature.json` selection into the
  exact durable and temporal paths of one canonical top-level feature or immediate sub-feature.
- **Architecture sources** are the module hierarchy under `specs/`: summaries, module references,
  level views, contracts, and feature roots (two containment levels: a feature and its immediate
  sub-features). Every mutating proposal is bound to a digest of them.

## Logic

**How one change moves through the workflow**

1. **Initialize** the root once: proposal, approval, then the root package appears together and
   validates.
2. **Find the level** with context: one level, nothing deeper; design references as links.
3. **Create or select the root**: `speckit.specify` with `SPECIFY_FEATURE_DIRECTORY` at the
   canonical path writes `tldr.md`, `spec.md`, and a placeholder `design.md` and records the
   selection in `.specify/feature.json`; selecting an existing root is the same pointer.
4. **Specify**: the TL;DR and the specification are written together; clarification updates both;
   checklists gate the next phases without granting approval.
5. **Plan**: one attempt under `implementation/`, derived from the specification and the accepted
   design reference; the TL;DR only orients.
6. **Execute and reconcile**: tasks run inside the attempt; analysis reports disagreement — including
   a TL;DR that says something the specification does not — without editing anything; convergence
   appends only real remaining work.
7. **Validate** whenever maintained structure changed; budget overruns are warnings, everything
   else in the document model is an error.
8. **Harden**: the agent drafts the candidate feature `design.md` (optionally with a module
   `design.md` amendment), the maintainer reviews the exact proposal, and only an explicit yes
   applies it atomically and removes `implementation/`. The next attempt starts again from the
   trio.

`speckit.concorde.ask` fits anywhere in that sequence and never mutates anything.

**Rules the implementation must keep**

- Every feature root owns `tldr.md`, `spec.md`, and `design.md` as real files; `implementation.md`
  at a feature root is a legacy name to rename, and no alias or symlink stands in for any of the
  three (FR-005, FR-009).
- Read-first documents are budgeted — a module summary under 20 minutes, a TL;DR under 15 — and an
  overrun is a validation warning, not an error (FR-002, FR-006, FR-018).
- The TL;DR is self-contained but never the authority: it states nothing `spec.md` lacks, and
  `spec.md` prevails when they disagree (FR-006, FR-007).
- A `design.md` — module or feature — is never an implicit input; context, questions, and planning
  reach it only by deliberate navigation and cite it when used (FR-004, FR-011, FR-012, FR-015).
- The feature `design.md` is written only by hardening: a placeholder until the first accepted
  milestone, written in full then, completed later (FR-008, FR-017).
- Hardening never edits `tldr.md`, `spec.md`, or any `module.md`; a module `design.md` amendment
  rides only on the same reviewed, digest-bound proposal and applies atomically with the
  compaction (FR-017, FR-028).
- Every phase operates on the one selected canonical root through the Feature Workspace Protocol
  paths and never derives competing root-level plan, task, or checklist paths (FR-013, FR-023,
  FR-024).
- Exactly two containment levels exist; a sub-feature reads its parent's trio as read-only context
  and never loads sibling bodies or attempts (FR-025, FR-026).
- Proposal, question, context, analysis, and validation are read-only; mutations of maintained
  intent require explicit approval of the presented proposal and fail safely when reviewed inputs
  go stale (FR-027, FR-028).
- Generated diagrams, pages, manifests, and reports are reproducible projections that exclude
  temporal attempts; missing evidence is reported as unknown, never inferred (FR-029, FR-031).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [spec.md](spec.md): the Document Model
  and "Where a fact lives" table, the Decomposition table, the End-to-End Workflow table, FR-001 to
  FR-034, and SC-001 to SC-013.
- **How the accepted implementation realizes this feature** — [design.md](design.md) (accepted realization and
  implementation detail, written by hardening).
- **The contracts this feature crosses** — `contracts/agent-commands.md`
  (command surfaces), `contracts/architecture-sources.md` (the source
  profile), and `contracts/feature-workspace.schema.json` (the
  workspace protocol and hardening proposal); the boundary promise is
  [contract.concorde.workflow](../../contracts/concorde-workflow/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary, with the
  level view) and its [design reference](../../design.md).
- **The nine workflow steps** — one sub-feature each:
  [initialize](subfeatures/001-initialize-architecture/spec.md),
  [context](subfeatures/002-retrieve-bounded-context/spec.md),
  [ask](subfeatures/003-answer-workflow-questions/spec.md),
  [workspaces](subfeatures/004-manage-feature-workspaces/spec.md),
  [specify](subfeatures/005-specify-behavior/spec.md),
  [plan](subfeatures/006-plan-delivery/spec.md),
  [execute](subfeatures/007-execute-and-reconcile/spec.md),
  [validate](subfeatures/008-validate-architecture/spec.md),
  [harden](subfeatures/009-harden-design/spec.md).
- **Framework-level explanation** — [docs/concorde-workflow.md](../../../../docs/concorde-workflow.md)
  and [docs/specification-model.md](../../../../docs/specification-model.md).
