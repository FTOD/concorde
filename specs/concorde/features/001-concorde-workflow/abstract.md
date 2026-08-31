# Feature Abstract: Concorde Workflow

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
minutes) and a document that is **consulted** (opened for one question). The normal lifecycle turns
work in progress into accepted realization only through an explicitly approved milestone; fast-loop
is a separate, explicitly invoked direct-authoring path limited to an established small change.

## Functionality

**The document model** — what each file at a level is for:

| Where | File | What it is |
|---|---|---|
| module root | `module.md` | the summary of the level: responsibility, boundary, structure diagram, feature/contract/submodule tables, one scenario, key rationale; under 20 minutes |
| module root | `design.md` | the module design reference: implementation notes, rationale, alternatives, decision log; consulted, never required |
| feature root | `abstract.md` | this kind of page: purpose, functionality, structure, logic; under 15 minutes |
| feature root | `design.md` | the complete behavioral authority: scenarios, requirements, success criteria |
| feature root | `implementation.md` | the feature design reference: how the accepted implementation realizes the feature, in full detail; normally written by acceptance and directly reconciled only by an eligible fast-loop |
| feature root | `attempt/` | the one attempt in progress: plan, tasks, checklists, research, evidence; removed when accepted |

**The command surfaces** — 15 in total, all reached through the active coding-agent integration as
skills or slash commands:

| Surface | What it does |
|---|---|
| `speckit.concorde.init` | Proposes, and on approval creates, the root module package: `module.md`, `design.md`, a seed level view under `architecture/diagrams/`, initial contracts, `.concorde/config.json`. Reports an existing configured hierarchy as unchanged. |
| `speckit.concorde.context` | Returns exactly one level — a module with its immediate children, current-level features, contracts, and scenarios, or a feature with its parent and siblings — with any `implementation.md` as a link, never as content. |
| `speckit.concorde.ask` | Answers a workflow question read-only from installed guidance, module summaries, and feature abstracts, citing anything deeper it opens. Agent-followed; no runtime. |
| `speckit.concorde.validate` | Checks every maintained source deterministically and returns sorted findings with rule, severity, location, and remediation; byte-equivalent on repeat. |
| `speckit.concorde.impl.accept` | Turns a completed attempt into accepted realization: proposal, exact review, explicit approval, atomic apply. |
| `speckit.fast-loop` | Directly reconciles an eligible small change across code, tests, every affected existing feature, and related contract/architecture/user documentation; an explicit logic-preserving pure rename may span bounded authorities; no attempt or separate post-edit architecture review is created. |
| `speckit.specify` · `clarify` · `checklist` | Author `abstract.md` and `design.md` for the selected root, seed a placeholder `implementation.md` for a new root, and write review checklists under `attempt/checklists/`. |
| `speckit.plan` · `tasks` · `taskstoissues` | Plan one attempt from `design.md`, the accepted `implementation.md`, and the level's `module.md`; write only under `attempt/`. |
| `speckit.implement` · `analyze` · `converge` | Execute the task list inside the attempt, report inconsistencies read-only, and append only genuine remaining work. |

**Not part of this feature**: installing or updating Concorde (`feature.concorde.install-with-spec-kit`),
building the docsite (`feature.concorde.publish-project-docsite`), a third containment level, a
second feature registry, a generated abstract, a reading budget for `design.md`, and any migration
command or compatibility alias for earlier document models.

## Structure

The core view is <a href="/architecture/concorde-workflow-components.html">workflow components</a>
(maintained source `diagrams/concorde-workflow-components.json`). In one sketch:

```text
Maintainer ──invoke · review · approve──▶ Coding-agent integration (skills / slash commands)
                                            ├─ 9 Spec Kit phase surfaces ──▶ selected-workspace adapter ──▶ .specify/feature.json
                                            ├─ fast-loop direct surface ───▶ code + tests + all affected authorities
                                            └─ 5 Concorde surfaces ────────▶ launchers + Python runtime ──▶ architecture sources
                                                 (init · context · validate · impl.accept · ask)        (module.md · design.md · architecture/: diagrams · contracts · modules)

Selected feature root:   abstract.md   design.md   implementation.md      +   attempt/  (one attempt, until accepted)
                         read      authority reference           plan · tasks · checklists · research · evidence
```

- **Spec Kit phase surfaces** are Spec Kit's own nine commands with a Concorde preset override
  that resolves the selected root *before* the phase runs, so no inherited helper can fall back to
  a root-level plan or task path.
- **Fast-loop** is the explicitly invoked alternate for a bounded small change beginning from one
  selected anchor and affecting one or more related already-realized features with no active
  attempts. It may reconcile contract/architecture detail while module responsibilities,
  dependencies, and project-level user policy stay stable; a pure rename may replace names while
  following that policy, and eligible architecture edits complete after deterministic validation.
- **Concorde surfaces** come from the `concorde` extension: four runtime operations plus the
  agent-only `ask`. The runtime is portable standard-library Python reached through launchers;
  installed projects never depend on the Concorde checkout.
- **The selected-workspace adapter** turns the standard `.specify/feature.json` selection into the
  exact durable and temporal paths of one canonical top-level feature or immediate sub-feature.
- **Architecture sources** are the module hierarchy under `specs/`: at every level a summary, a
  module reference, feature roots (two containment levels: a feature and its immediate
  sub-features), and an `architecture/` directory holding the level's diagrams (its level views),
  boundary contracts, and submodules. Every mutating proposal is bound to a digest of them.

## Logic

**How one change moves through the workflow**

1. **Initialize** the root once: proposal, approval, then the root package appears together and
   validates.
2. **Find the level** with context: one level, nothing deeper; design references as links.
3. **Create or select the root**: `speckit.specify` with `SPECIFY_FEATURE_DIRECTORY` at the
   canonical path writes `abstract.md`, `design.md`, and a placeholder `implementation.md` and records the
   selection in `.specify/feature.json`; selecting an existing root is the same pointer.
4. **Specify**: the abstract and the specification are written together; clarification updates both;
   checklists gate the next phases without granting approval.
   For an already-realized bounded small change, the maintainer may instead invoke **fast-loop**:
   the selected root anchors affected-feature discovery, every affected baseline is checked before
   mutation, then code, tests, and all related authorities are reconciled directly with no attempt or
   acceptance operation; explicit pure renames are referential-only and maintained architecture
   edits finish after validation.
5. **Plan**: one attempt under `attempt/`, derived from the specification and the accepted
   design reference; the abstract only orients.
6. **Execute and reconcile**: tasks run inside the attempt; analysis reports disagreement — including
   a abstract that says something the specification does not — while writing only required problem
   records to the project reflection log; convergence appends only real remaining work.
7. **Validate** whenever maintained structure changed; budget overruns are warnings, everything
   else in the document model is an error.
8. **Accept**: the agent drafts the candidate feature `implementation.md` (optionally with a module
   `implementation.md` amendment), the maintainer reviews the exact proposal, and only an explicit yes
   applies it atomically and removes `attempt/`. The next attempt starts again from the
   trio.

`speckit.concorde.ask` fits anywhere in that sequence and never mutates anything.

**Rules the implementation must keep**

- Every feature root owns real `abstract.md`, `design.md`, and `implementation.md`; former names and
  aliases are invalid (FR-005, FR-009).
- Read-first documents are budgeted — a module summary under 20 minutes, a abstract under 15 — and an
  overrun is a validation warning, not an error (FR-002, FR-006, FR-018).
- The abstract is self-contained but never the authority: it states nothing `design.md` lacks, and
  `design.md` prevails when they disagree (FR-006, FR-007).
- Module `design.md` and feature `implementation.md` are never implicit inputs; context, questions,
  and planning reach them deliberately and cite them (FR-004, FR-011, FR-012, FR-015).
- The feature `implementation.md` gets its first accepted realization only through acceptance;
  an eligible fast-loop may directly reconcile an established realization with a verified small
  change and never creates the first one (FR-008, FR-017, FR-035).
- Acceptance never edits `abstract.md`, `design.md`, or any `module.md`; a module `design.md` amendment
  rides only on the same reviewed, digest-bound proposal and applies atomically with the
  compaction (FR-017, FR-028).
- Every normal phase operates on the one selected canonical root through Feature Workspace Protocol
  paths and never derives competing root-level plan, task, or checklist paths; fast-loop may repeat
  explicit resolution for its bounded affected roots without creating another selection registry
  (FR-013, FR-023, FR-024, FR-035).
- Exactly two containment levels exist; a sub-feature reads its parent's trio as read-only context
  and never loads sibling bodies or attempts (FR-025, FR-026).
- Proposal, question, context, analysis, and validation are read-only; mutations of maintained
  intent require explicit approval of the presented proposal and fail safely when reviewed inputs
  go stale (FR-027, FR-028).
- Generated diagrams, pages, manifests, and reports are reproducible projections that exclude
  temporal attempts; missing evidence is reported as unknown, never inferred (FR-029, FR-031).
- Fast-loop starts from one selected anchor, requires every affected feature to be already realized
  with no active attempt, preserves unrelated work, rejects module-boundary and project-level user
  compatibility/migration policy changes except a pure rename that follows existing policy, creates
  no attempt artifacts, and succeeds only with aligned authorities, passing checks, and validated
  architecture evidence (FR-028, FR-035).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): the Document Model
  and "Where a fact lives" table, the Decomposition table, the End-to-End Workflow table, FR-001 to
  FR-035, and SC-001 to SC-014.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (accepted realization and
  implementation detail, written by acceptance).
- **The contracts this feature crosses** — `contracts/agent-commands.md`
  (command surfaces), `contracts/architecture-sources.md` (the source
  profile), and `contracts/feature-workspace.schema.json` (the
  workspace protocol and acceptance proposal); the boundary promise is
  [contract.concorde.workflow](../../architecture/contracts/concorde-workflow/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary, linking the root
  level view under `../../architecture/diagrams/`) and its [design reference](../../design.md).
- **The ten workflow steps and alternate** — one sub-feature each:
  [initialize](subfeatures/001-initialize-architecture/design.md),
  [context](subfeatures/002-retrieve-bounded-context/design.md),
  [ask](subfeatures/003-answer-workflow-questions/design.md),
  [workspaces](subfeatures/004-manage-feature-workspaces/design.md),
  [specify](subfeatures/005-specify-behavior/design.md),
  [plan](subfeatures/006-plan-delivery/design.md),
  [execute](subfeatures/007-execute-and-reconcile/design.md),
  [validate](subfeatures/008-validate-architecture/design.md),
  [accept](subfeatures/009-accept-milestone/design.md),
  [fast-loop](subfeatures/010-fast-loop/design.md).
- **Framework-level explanation** — [docs/concorde-workflow.md](../../../../docs/concorde-workflow.md)
  and [docs/specification-model.md](../../../../docs/specification-model.md).
