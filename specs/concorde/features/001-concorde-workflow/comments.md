# Feature 001 Decomposition Review Comments

**Reviewed**: 2026-08-26

**Status**: Non-normative review notes. These comments do not amend `spec.md`, `design.md`, module
architecture, contracts, or implementation behavior.

## Review Summary

The existing implementation substantially supports the nine workflow-step sub-features introduced
under Feature 001. Runtime discovery, two-level containment validation, selected-root routing,
bounded parent/sibling context, documentation relationships, and child hardening are already present
and exercised by the existing test suite. The new real-project hierarchy validates with zero
findings, every child can be selected, and the documentation build emits parent/child routes for all
nine children.

The review found one concrete command-contract inconsistency and two important follow-up needs. They
are intentionally not fixed here because each requires a product-level decision or an approved
hardening migration rather than an obvious local correction.

## Significant Findings

### C-001 — Feature creation documents an apply flag that the runtime does not provide

**Severity**: High

`contracts/agent-commands.md` declares a `feature create --approve` input and says registration plus
selection are applied atomically. The actual CLI parser exposes only placement, identity, numbering,
participant, and format arguments for `feature create`; dispatch always returns
`propose_feature(...)`. The installed feature-create instruction instead tells the coding agent to
run the normal specification phase after approval, register the maintained metadata, validate, and
then select the feature.

Evidence:

- `contracts/agent-commands.md`, feature-create inputs and behavior around lines 78–105;
- `extensions/concorde/runtime/concorde/cli.py`, create parser and dispatch;
- `extensions/concorde/commands/speckit.concorde.feature.create.md`, workflow steps 1–5; and
- integration tests, which test proposal and selection but do not exercise a runtime creation apply.

This is more than a spelling error: there are two plausible intended contracts.

1. Keep creation agent-mediated. Remove `--approve` and the atomic-runtime wording from the contract,
   explicitly define the normal specify/registration/select sequence, and specify recovery behavior
   if a later step fails.
2. Add a source-bound creation proposal artifact and runtime apply mode comparable to initialization
   and hardening, including transactional registration/selection and safe coordination with the
   normal specification phase.

The second option gives stronger failure semantics; the first matches the current implementation and
is smaller. The choice should be specified before code or contract changes are made.

**Resolution note (2026-08-27)**: Resolved as moot. `speckit.concorde.feature.create` and
`speckit.concorde.feature.select` were removed together with the `propose_feature`/`select_feature`
runtime functions and Protocol v3's `feature.create`/`feature.select` operations. Creation is now the
standard `speckit.specify` phase with `SPECIFY_FEATURE_DIRECTORY` at the canonical root, selection is
the standard `.specify/feature.json` pointer, and `speckit.concorde.validate` enforces registration,
canonical path, two-level containment, and identity rules deterministically. Neither option above is
pursued; the constitution (v2.0.0, principle A.III) no longer requires one providing module per
feature, which the removed commands assumed.

### C-002 — Accepted parent design and evidence have not yet migrated to child ownership

**Severity**: High

The hardened parent `design.md` correctly describes the implemented workflow, but it still owns
detailed realization and evidence for initialization, context, workspace routing, normal phases,
validation, Q&A, and hardening. After decomposition, those focused realization facts belong in the
corresponding child designs, while the parent design should retain only aggregate collaboration,
cross-step flow, and shared decisions.

The new child designs intentionally state that no implementation realization has been hardened. That
is the only safe initial state: existing code and tests cannot become accepted child design merely
because the specification was reorganized. Consequently, the current parent evidence counts,
digests, generated-page totals, and release hashes also describe the pre-decomposition source state
and should not be treated as fresh evidence for the new hierarchy.

Recommended migration:

1. For each child, create a bounded reconciliation attempt that maps its requirements to the existing
   command/runtime/test evidence and records any genuine gaps.
2. Harden each completed child attempt after explicit review.
3. Create and harden a final parent reconciliation attempt that removes child-owned implementation
   detail from the parent design, retains aggregate flow and cross-child decisions, and refreshes
   project-wide evidence references.

This work should not be performed as a direct edit to accepted designs.

### C-003 — Tests prove the mechanics, but not the new command-to-sub-feature ownership map

**Severity**: Medium

Existing tests cover the individual runtime operations, all nine normal workspace phases, installed
Codex/slash parity, generic two-level containment, child selection, bounded context, documentation
relationships, and child hardening. The real Feature 001 hierarchy is also discovered by project
validation and publication.

No focused gate currently proves that:

- the seven Concorde command definitions and nine normal Spec Kit phase definitions are each owned by
  exactly one of these nine child specifications;
- the parent command table contains all 16 surfaces exactly once; or
- a command addition, removal, or rename forces an explicit decomposition update.

Add a lightweight contract test or maintained traceability manifest that inventories installed
command definitions, maps them to child feature IDs, rejects duplicate/unmapped surfaces, and verifies
the parent authored order. This would protect the abstraction rather than only the underlying
workspace mechanics.

### C-004 — Large decompositions require repeated single-child approval cycles

**Severity**: Medium suggestion

The feature-create workflow intentionally creates one root per invocation. That is clear and safe for
ordinary work, but decomposing one large feature into many correlated children requires repeated
proposal, approval, specification, registration, validation, and selection cycles. A maintainer can
review the overall decomposition only informally; there is no canonical batch proposal binding the
ordered set as one reviewed change.

Consider an optional decomposition proposal that contains an ordered list of ordinary child-create
proposals, one parent source digest, and an all-or-nothing registration manifest. It should reuse the
same two-level rules and normal child lifecycle rather than introduce another feature kind or nesting
level. This is an ergonomics improvement, not required for the current hierarchy.

**Resolution note (2026-08-27)**: Moot. The feature-create workflow was removed. Decomposition now
proceeds by running `speckit.specify` once per child with `SPECIFY_FEATURE_DIRECTORY` at its canonical
`subfeatures/` root and registering each child in the parent's feature list, with
`speckit.concorde.validate` checking the whole hierarchy; any future batch proposal would build on the
standard specify phase rather than on a Concorde creation command.

## Implementation Alignment by Sub-feature

| Sub-feature | Existing primary evidence | Review result |
|---|---|---|
| Initialize Architecture | `initialize.py`, CLI init dispatch, initialization tests | Behavior aligns with proposal/apply, idempotence, and conflict safety. |
| Retrieve Bounded Context | `context.py`, repository model, bounded-context tests | Behavior aligns with one-level module and feature relationship projections. |
| Answer Workflow Questions | installed `ask` command/skill definitions and parity tests | Instruction surface aligns; evidence remains agent-behavior evidence rather than deterministic runtime proof. |
| Manage Feature Workspaces | `feature_workspace.py`, `workspace.py`, selection and containment tests | Routing and two-level resolution of the standard Spec Kit selection align; finding C-001 became moot when `feature.create`/`feature.select` were removed (2026-08-27). |
| Specify Behavior | `specify`, `clarify`, and `checklist` command replacements plus routing tests | Selected-root and durable/temporal authority align. |
| Plan Delivery | `plan`, `tasks`, and `taskstoissues` replacements plus routing tests | Selected attempt and root confinement align. External issue publication still depends on separate authorization. |
| Execute and Reconcile | `implement`, `analyze`, and `converge` replacements plus routing tests | Phase boundaries align; analysis correctly requires a real active plan/task attempt. |
| Validate Architecture | validation runtime, containment/layout rules, deterministic fixtures | Behavior aligns and the new nine-child hierarchy validates with zero findings. |
| Harden Design | `feature_hardening.py` and parent/child atomicity tests | Eligibility, approval binding, target confinement, recovery, and related-root preservation align. |

## Small Corrections and Verification Notes

- Child metadata was normalized to the source profile's supported block-list syntax after validation
  rejected non-JSON-compatible inline collections.
- The documentation publication step reproduced two previously absent supplemental generated HTML
  views required by the Python contract suite.
- No existing implementation source was changed during this review: every other discrepancy found
  was either intentional authority separation or significant enough to require an explicit decision.
