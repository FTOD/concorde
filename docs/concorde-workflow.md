---
title: Concorde Workflow
sidebar_position: 6
---

# Concorde Workflow

Concorde surrounds the normal Spec Kit lifecycle with architectural ownership, bounded context,
deterministic validation, and approval-gated hardening. It does not replace specification, planning,
tasks, or implementation.

Contributors changing the Concorde framework itself must also use the explicit local synchronization
described in [Developing Concorde with Concorde](self-hosting.md). Updating checked-in preset or
extension sources does not hot-reload their installed copies or the current agent session.

The authoritative workflow, including requirements and edge cases, is
[Feature 001](../specs/concorde/features/001-concorde-workflow/spec.md). The stages below
explain how to apply it in a project.

At any stage, invoke `speckit.concorde.ask <question>` when the uncertainty is about the workflow
itself rather than the product being implemented. The agent grounds its read-only answer in the
installed extension/preset guidance and, for project-specific questions, module summaries and
feature TL;DRs first; it opens a `spec.md` for a requirement's exact wording and a `design.md` only
deliberately. It cites those paths, distinguishes framework rules from project observations and
inference, and asks for focused clarification when it cannot safely resolve the target. It does not
run another stage on your behalf.

## Before feature work: establish the root

Run `speckit.concorde.init` after Concorde has been installed in a Spec Kit project. Initialization
does not attempt to decompose the whole future system. It proposes the minimum root package needed
to reason safely: `.concorde/config.json`, a `module.md` summary in the required shape (stable
module ID, responsibility and boundary, explicit provided and required contract sets, current-level
features, immediate children, and a link to the one-level view), a seeded `design.md` design
reference, and the `architecture.json` view.

The proposal is reviewable and no maintained architecture is written until it is explicitly
approved. Re-running the accepted initialization is idempotent; conflicting existing content is not
silently overwritten.

## 1. Find the level at which to specify it

Request context for the root module. A feature is specified at the level at which every module it
uses is visible, so ask whether the new behavior is realized by that module or by its visible
children:

- If one child realizes the whole behavior on its own, zoom into that child and repeat the question.
- If several immediate children collaborate, specify the feature at this level; those children are
  its realizing modules, and their own features may refine it.
- If no existing module has a coherent responsibility for it, review the architecture instead of
  letting the agent invent placement while planning code.

`speckit.concorde.context` returns exactly one bounded level. It gives the agent the current module,
its features and I/O, immediate children and their I/O, externals, current-level scenarios,
refinement links, and navigation references: the module's `module.md`, `design.md`, and view paths,
and each feature's TL;DR path. It never expands a module or feature `design.md`, and it does not
select a feature or permanently load the entire hierarchy.

## 2. Create or select the feature workspace

Concorde has no feature-creation command. For a new feature, set `SPECIFY_FEATURE_DIRECTORY` to the
canonical feature root inside the hierarchy—`<module directory>/features/NNN-<short-name>`, for
example `specs/example/modules/api/features/002-observe-health`—and run the normal
`speckit.specify` phase. The Concorde specify addendum authors root `tldr.md` and `spec.md`, seeds a
placeholder `design.md` that explicitly states no realization has yet been hardened, and persists
the root to `.specify/feature.json`. Record the feature's identity and placement in the spec front matter (`id`
and `module`), register it in the module's `features` list, and run `speckit.concorde.validate`,
which deterministically checks registration, canonical path, two-level containment, and identity.

For an existing feature, selection is plain Spec Kit selection: `.specify/feature.json`
`feature_directory`, written by specify or set explicitly with
`export SPECIFY_FEATURE_DIRECTORY=<feature root>`. Concorde adds no selection command and no second
selection store. Before every normal phase the workspace adapter resolves and validates the selected
root: safe path, canonical `tldr.md`/`spec.md`/`design.md` trio with no legacy `implementation.md`,
workspace kind, parent context and sibling summaries for a sub-feature, durable and temporal paths,
the module's `module.md` and `design.md` as navigation references, and `implementation_state`. A
non-empty `implementation/` attempt appears as `implementation_state: active`; there is no separate
resume step—decide whether to continue that attempt or harden or archive it.

Selection is what routes later Spec Kit phases. Context retrieval is only a read operation.

If the behavior is too broad for one clear specification, keep one aggregate parent and create one
level of immediate sub-features beneath it. Point `SPECIFY_FEATURE_DIRECTORY` at
`<parent feature root>/subfeatures/NNN-<short-name>`, for example
`specs/example/features/001-checkout/subfeatures/003-capture-payment`, run `speckit.specify`, add
`parent_feature` to the child's front matter, and register it in the parent's `subfeatures` list.
The child inherits the parent's placement and cannot have children. Select either level for normal
phases; selecting a child keeps parent durable context read-only and never opens sibling bodies or
attempts implicitly.

Concorde's earlier dedicated creation and selection commands encoded the old rule of one providing
module per feature. The constitution (v2.0.0, principle A.III) no longer requires it, and standard
Spec Kit creation and selection plus deterministic validation are sufficient, so those commands were
removed.

## 3. Specify observable behavior

Use the normal `specify` and `clarify` phases to describe:

- actors and value;
- observable behavior and constraints;
- expected failures and degraded behavior;
- measurable outcomes;
- boundary contracts; and
- representative user or system scenarios.

`specify` writes two documents: `spec.md`, the complete authority, and `tldr.md`, a self-contained
quick understanding of the feature in five fixed sections (`Purpose`, `Functionality`, `Structure`,
`Logic`, `Read Next`) that summarizes the specification and never defines beyond it. `clarify`
encodes accepted answers into `spec.md` and updates the TL;DR wherever it summarized the changed
behavior. Keep the TL;DR within its budget and faithful: `spec.md` prevails when they disagree.

Keep the distinction clear: the prose defines the feature; scenarios illustrate it. When multiple
components collaborate, add one core Archify architecture diagram showing stable participants,
responsibilities, interactions, and contracts, or state why the bounded module view plus prose is
sufficient. Add sequence, workflow, data-flow, or lifecycle diagrams only as supplemental answers to
narrower dynamic questions.

Requirements-quality checklists belong under `implementation/checklists/`. A checklist records the
current review cycle; accepted behavioral conclusions must be incorporated into `spec.md`.

## 4. Approve architecture before planning implementation

Before accepting a plan, review the structure that the agent will be allowed to realize:

- Is the placement level correct and are the realizing modules right?
- Does a parent feature need child-level refinements?
- Which immediate submodules participate?
- Does every boundary crossing name a provided or required contract?
- Are contract direction, obligations, failures, representation, and compatibility explicit?
- Does the current-level view show only permitted participants?
- Does `module.md` still read as a summary, with new implementation detail and rationale bound for
  `design.md`?
- Does `tldr.md` still read in minutes and state nothing that `spec.md` does not?
- What implementation and test evidence will demonstrate agreement?

For a custom serialized contract, require a readable schema or grammar, field meanings, examples,
compatibility rules, and conformance evidence. For an adopted standard, identify the standard and
version and briefly explain the information passed.

Architecture review happens before code planning because a structurally valid implementation can
still embody the wrong ownership or dependency direction.

## 5. Plan one implementation attempt

The normal `plan` phase reads two durable inputs, with the owning level's `module.md` as bounded
context:

- `spec.md`, which defines required behavior; and
- the feature `design.md`, which records the accepted realization baseline (the seeded placeholder
  counts as no baseline).

The TL;DR is orientation only, never a planning input. The plan consults the module's `design.md`
only deliberately and cites it when used.

It writes the proposed delta beneath `implementation/`: research, plan, technical model, quick start,
and related artifacts. `tasks` then creates dependency-ordered executable work in the same attempt.
Every specification, architecture, cross-feature, or guidance problem planning cannot resolve is
recorded as an entry in the project reflection log (`reflections.md` at the specification root, the
path returned as `workspace.reflections`) and listed in the plan's architecture gate; nothing is
"fixed" by editing a durable document or another feature's sources.
If architecture, contracts, diagrams, traceability, validation, or generated freshness are affected,
the plan and tasks must include that work explicitly.

Run `analyze` after task generation to check consistency among the durable behavior, accepted
realization, plan, and tasks before code changes begin; it also reports any statement in the TL;DR
that `spec.md` does not make, naming the prevailing requirement.

## 6. Implement with bounded context

`implement` executes the selected task set. Give the coding agent the selected feature, its owning
module level, relevant contracts and diagrams, and the evidence expected for the current tasks. Only
descend into a child module when the work actually requires that child's internal level.

This keeps an agent from treating the whole repository as undifferentiated context. It also makes
structural deviations visible: the agent can choose low-level code details, but it should not invent
new cross-module dependencies or silently change contracts.

Whenever a phase cannot follow the specification, the design baseline, an existing implementation,
the guidance, or the plan — a tool fails, another feature's code disagrees with its design
reference, an instruction cannot be followed, a dependency is missing, a workaround is taken — the
agent records the problem in the project reflection log in that same phase, attributed to the
selected feature and naming the source it concerns, and continues when it can; a halt is recorded
with `Effect: blocked` first. Re-encountering a recorded problem, from any feature, adds an
occurrence rather than a new entry. Every recording phase ends its report with the entries it added
and the feature's open count, and `analyze` lists the feature's open entries and flags those whose
referenced source has since changed.

After implementation, use `converge` to compare code with intended behavior and append genuinely
unbuilt work. Convergence must not rewrite the specification to make incomplete code appear correct;
it treats an open, deferred reflection entry of the feature as candidate work only when it is
genuine feature work.

### Reviewing reflections

The reflection log is one file for the whole project, so a maintainer reviews it in one place:
filter by `Feature` for what one attempt met, or by `Concerns` for everything recorded against one
module, contract, instruction, or tool. Bounded context (`speckit.concorde.context`) names the log
and the open count per feature. Resolve or dismiss an entry by editing its `Status` and `Note`
directly; the actual improvement goes through the path that owns the concerned source — `specify`
or `clarify` for a requirement, an architecture change for a placement or contract, a guidance or
runtime change for an instruction or tool. Agents never delete entries or reverse a maintainer's
decision. In the Concorde project itself, an accepted `guidance` or `tooling` entry is planned
framework work or a framework change, and that change counts as used only after the self-hosted
installation is refreshed.

## 7. Validate and reconcile disagreement

Run `speckit.concorde.validate` after maintained structural changes, during implementation, and
before hardening. It deterministically checks source parsing, unique identities, containment and
refinement, feature ownership, contract completeness, scenario scope, view depth, references,
evidence status, module summary and feature TL;DR shape and reading budgets (the budgets as warnings
only), the presence of a `design.md` beside every `module.md`, the feature-root trio and the legacy
`implementation.md` name, the shape of the project reflection log when present
(`CONCORDE-REFLECT-001` to `-004`), and generated freshness.

Validation is read-only. It reports rule, severity, location, and remediation in stable order. Valid
architecture does not prove that code conforms; missing evidence remains `unknown`, and conflicting
specification, accepted realization, code, tests, or projections are reported as disagreement.

Review behavioral, architectural, implementation, and evidence changes together. Do not resolve a
finding by weakening the wrong authority.

## 8. Harden an accepted milestone

Hardening is appropriate only when:

- the active attempt has a real `implementation/tasks.md` with at least one task;
- every recognizable task is complete;
- every existing checklist item is satisfied;
- validation and evidence have been reviewed; and
- the maintainer accepts the implementation as the new durable baseline.

The agent first asks the runtime for eligibility (which also summarizes the feature's reflection
entries by status), then synthesizes a proposed feature `design.md` from the complete attempt, the
current feature `design.md`, the TL;DR and specification, the module summary and module
`design.md`, relevant architecture, contracts, code, tests, and the project reflection log: every
open entry attributed to the feature is cited among the known limitations, and resolved entries that
shaped the realization among the decisions. When the attempt
produced implementation detail or rationale worth keeping, the same proposal carries a full
replacement `design.md` for the module at which the feature is specified, adding that material
under the reference's stable headings without restating what the summary owns. The proposal names
the exact feature `design.md` target, the optional module `design.md` target, the complete
`implementation/` removal target, and a digest of the source bytes reviewed, which includes the
current module `design.md`.

Checked boxes do not grant approval. Only explicit acceptance of that exact proposal authorizes the
runtime to write the feature `design.md`, amend the module `design.md` when proposed, and remove
`implementation/` as one atomic operation; the result reports digests for both documents. A stale
digest, changed path, symlink, incomplete task, unresolved checklist, amendment aimed at `tldr.md`,
`spec.md`, `module.md`, or another level, an uncited open reflection entry (`CONCORDE-HARDEN-012`),
or failed apply leaves the previous state recoverable. Hardening never edits `tldr.md`, `spec.md`,
`module.md`, the reflection log, contracts, or views.

## 9. Publish the read model

The docsite publishes module summaries with their embedded level views and linked design references,
boundary contracts, every feature opening on its TL;DR with the specification and the design
reference as companion pages, and explanatory project guides. It excludes the active implementation
attempt from the Features view. Preview and production publication validate and deliver every
declared Archify source before Docusaurus consumes it. Publication is deterministic and read-only;
ignored generated pages and diagram deliveries never become a second source of project intent.

The publication behavior is specified separately by
[Feature 002](../specs/concorde/features/002-create-project-docsite/spec.md).

## Starting the next change

A hardened feature has no active `implementation/` directory. Select it again by pointing
`SPECIFY_FEATURE_DIRECTORY` (and therefore `.specify/feature.json`) at its root, revise `spec.md`
and its TL;DR if the required behavior changes, review any affected architecture, and start a fresh
plan. The current feature `design.md` remains the accepted realization until another complete
attempt is explicitly hardened.

Use [Commands and installed surfaces](commands.md) for exact command timing, side effects, and the
difference between agent skills and terminal commands.
