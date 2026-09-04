---
id: feature.concorde.evolve-protocol
kind: feature
module: module.concorde
related_features:
  - id: feature.concorde.workflow
    relation: refines
  - id: feature.concorde.define-project-ontology
    relation: depends_on
  - id: feature.reflections.record-and-triage
    relation: relates_to
interfaces:
  provided:
    - interface.concorde.protocol-evolution
  required:
    - contract.concorde.ontology
---

# Feature Design: Evolve the Concorde Protocol

**Input**: Concorde is the only project that defines, implements, and consumes its own normative
change process. Every semantic change to that Concorde Protocol must therefore bypass the normal
attempt/delivery lifecycle and be completed as one explicitly authorized, isolated-worktree cutover.

## Outcome and Scope

**Outcome**: A Concorde maintainer can evolve any normative Concorde Protocol behavior without asking
the Protocol being changed to host or deliver its own replacement, while the base checkout remains
valid until one complete target-state commit has passed review and deterministic validation.

**In scope**:

- classification of normative Concorde Protocol changes;
- a Git-only, maintainer-authorized, isolated-worktree cutover with no Concorde attempt, checklist,
  fast loop, standard development loop, or delivery;
- direct reconciliation of every affected governance, architecture, feature, source, test, template,
  control-state, and generated-source authority;
- target-state validation, one reviewable cutover commit, merge eligibility, and Git recovery; and
- the self-application boundary unique to the Concorde repository as Protocol owner and consumer.

**Out of scope**:

- ordinary feature work or implementation/test fixes that restore already specified Protocol behavior;
- a general source-profile migrator, compatibility reader, dual-layout mode, or automatic downgrade;
- automatic migration of external projects that consume an upgraded Concorde release; and
- replacing Git with a generic transaction engine or exposing protocol evolution as a Skill or Operation.

## Usage

The maintainer identifies a proposed change as a semantic change to Concorde Protocol, confirms the
tracked checkout is clean and has no active attempts, and explicitly authorizes a cutover from that
exact commit. A dedicated branch and isolated worktree are created without changing selection or
creating temporal Concorde state. Governance, specifications, architecture, code, tests, templates,
fixtures, and projections are reconciled directly in that worktree. The target checkout must pass
the complete applicable validation suite before its single cutover commit may merge. Failure leaves
the base checkout unchanged; the branch/worktree is abandoned before merge or the cutover commit is
reverted before later work proceeds.

### Edge Cases

- A change touches a Protocol implementation file but only restores behavior already required by the
  maintained specification; it remains normal lifecycle work.
- A proposed cutover starts with a dirty tracked checkout, any active attempt, ignored authoritative
  state, a stale base commit, or an already checked-out target branch; preflight rejects it.
- A nominally compatible change alters a normative Protocol output, obligation, failure, phase,
  authority, or permission rule; it still requires this cutover.
- Target validation fails after direct edits; no cutover commit is eligible and the base checkout is
  not changed.
- Main advances after the worktree was created; the cutover must be rebased/recreated and fully
  revalidated rather than merged against a stale base.
- A released Protocol change requires an external project migration; that migration is specified
  separately and is not inferred from this repository-only workflow.

## User Scenarios & Testing

### User Story 1 — Cut over a normative Protocol change (Priority: P1)

A Concorde maintainer can change the rules that govern Concorde's own selected-feature workflow
without creating an attempt whose location, permissions, or delivery semantics the change may
invalidate.

**Why this priority**: It removes the self-reference that otherwise leaves no valid intermediate
combination of old/new Protocol implementation and old/new control state.

**Independent Test**: From a clean commit with no active attempts, create an isolated worktree,
change a maintained Protocol rule and all affected authorities without creating `.concorde/attempts/`,
run complete target validation, and inspect one commit containing the entire cutover.

**Acceptance Scenarios**:

1. **Given** an explicitly authorized normative Protocol change and a clean attempt-free base,
   **When** the maintainer completes the isolated-worktree procedure, **Then** the target state is
   fully reconciled and validated before one cutover commit becomes mergeable.
2. **Given** dirty state, an active attempt, a stale base, ambiguous Protocol scope, or failed target
   validation, **When** cutover preflight or validation runs, **Then** merge eligibility is denied and
   the base checkout remains unchanged.

### User Story 2 — Keep ordinary work on the normal lifecycle (Priority: P2)

A maintainer can distinguish Protocol semantics from their implementation so that the bootstrap
exception does not become a general way to bypass Concorde review.

**Why this priority**: The exception is safe only while normal product changes continue to use the
workflow Concorde provides to every project.

**Independent Test**: Classify representative semantic changes and conformance-restoring fixes and
verify that only the former route to protocol evolution.

**Acceptance Scenario**:

1. **Given** a code refactor, test addition, or defect fix that preserves the maintained Protocol
   contract, **When** its route is selected, **Then** the normal attempt workflow or eligible fast
   loop remains required.

## Interfaces

### `interface.concorde.protocol-evolution` — Isolated Protocol cutover

- **Consumer**: Concorde repository maintainer.
- **Direction**: Explicitly classified and authorized normative Protocol intent plus one clean Git
  base to either one validated target-state cutover commit or a non-mutating rejection/failure.
- **Entry points**: Maintainer invocation of `interaction.concorde.evolve-protocol` in a dedicated Git
  branch/worktree; no Concorde Skill, Operation, attempt, checklist, selection update, or delivery.
- **Inputs**: Exact base commit; explicit maintainer authorization; the complete affected Protocol
  semantics and compatibility decision; current constitution, ontology, architecture, feature,
  source, test, template, fixture, projection, and tracked control-state authorities.
- **Outputs**: One reviewable commit containing the complete reconciled target state and named
  deterministic validation evidence, or diagnostics that leave the base checkout unchanged.
- **Obligations**: Classify every normative semantic change into this route regardless of apparent
  compatibility; require clean tracked state and no active attempt; author only in the isolated
  worktree; preserve unrelated/user state; reconcile every affected authority; validate the full
  target; and merge no partial, stale, or failed cutover.
- **Failures**: Non-Git checkout, dirty or ambiguous state, active attempt, unsafe path/symlink,
  incomplete authority inventory, stale base, merge conflict, validation failure, or a multi-commit
  partial transition makes the cutover ineligible.
- **Compatibility**: Constitution 8.0.0 makes this route mandatory for normative Concorde Protocol
  changes. External projects consume the Protocol but neither define it nor invoke this self-evolution
  interface; no compatibility reader or automatic project migration is implied.
- **Example**: A change to attempt path authority updates Constitution, ontology, workspace/lifecycle
  specifications, resolver code, tests, fixtures, and projections in one isolated worktree, passes
  complete validation, and merges as one commit without ever creating a migration attempt.
- **Implementing entities**: `entity.concorde.protocol-cutover`, `entity.concorde.protocol`,
  `entity.concorde.git`, `entity.concorde.specification`, `entity.concorde.control-state`,
  `entity.concorde.source-code`, and `entity.concorde.tests`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.protocol` | Supplies the normative process boundary whose semantics classify the change. | The maintainer identifies a semantic change before invoking any normal lifecycle capability. |
| `entity.concorde.protocol-cutover` | Owns the direct, attempt-free self-evolution procedure. | It binds one base commit to one isolated target worktree and admits only a completely validated cutover commit. |
| `entity.concorde.git` | Supplies immutable base/target history, branch/worktree isolation, diff review, merge, abandonment, and revert. | It keeps the base checkout valid while the complete target is built separately. |
| `entity.concorde.specification` | Owns the Constitution-aligned architecture and feature semantics affected by the cutover. | Protocol definitions and every affected interface are reconciled directly. |
| `entity.concorde.control-state` | Must contain no active attempt and must remain free of provisional bootstrap state. | Tracked control authorities change only when the target Protocol requires them. |
| `entity.concorde.source-code` | Realizes the target Protocol. | Implementation changes together with its maintained semantics rather than before or after them. |
| `entity.concorde.tests` | Supplies executable target evidence. | Complete deterministic checks run before merge eligibility. |

## Related Features

- This feature `refines` `feature.concorde.workflow` by defining the Concorde-repository-only boundary
  outside the normal workflow for normative Protocol evolution.
- This feature `depends_on` `feature.concorde.define-project-ontology` for the definition of Concorde
  Protocol, its component concepts, project/control roles, and self-application relationship.
- This feature `relates_to` `feature.reflections.record-and-triage` because read-only investigation
  may establish a Protocol problem, while implementation/merge/close delegates to this root cutover
  and the cutover commit preserves the maintainer disposition in Git history.

## Requirements

### Functional Requirements

- **FR-001**: Concorde Protocol MUST mean the complete normative process by which a selected feature
  is resolved, permission-bounded, specified, planned, executed, validated, reflected on, and
  delivered, together with its Source Profile and control-state authority rules; Feature Workspace
  Protocol MUST remain one serialized component rather than a synonym.
- **FR-002**: Every change to normative Concorde Protocol semantics MUST use this feature regardless
  of backward compatibility; a change that only restores already specified semantics MUST use the
  normal lifecycle.
- **FR-003**: Protocol evolution MUST create no attempt, checklist, selection mutation, plan/tasks,
  fast-loop execution, standard-loop execution, or delivery action.
- **FR-004**: Cutover preflight MUST require an explicit maintainer decision, an exact clean tracked
  base commit, a Git repository, no active attempts, and no unresolved authoritative state outside
  that commit.
- **FR-005**: The complete change MUST be authored in one isolated worktree/branch while the base
  checkout remains unchanged and usable.
- **FR-006**: The cutover MUST reconcile every affected constitution, architecture, feature,
  interface, source, test, template, fixture, tracked control-state, canonical guidance, and generated
  projection source before it is eligible to merge.
- **FR-007**: The complete target checkout MUST pass deterministic workspace, architecture, capability,
  reflection, package, documentation, projection-freshness, and executable behavioral validation as
  applicable to the changed Protocol semantics.
- **FR-008**: One reviewable commit MUST contain the complete transition; stale bases, partial commits,
  merge conflicts, or failed checks MUST prevent merge, while pre-merge failure is abandoned and an
  immediate post-merge failure is recovered by reverting that commit before later work proceeds.
- **FR-009**: The feature MUST NOT introduce a dual reader, generic migrator, automatic downgrade,
  normal-command auto-migration, or external-project source-profile conversion.

### Non-Functional Requirements

- **NFR-001**: Git diff/commit identity plus named deterministic checks MUST make every cutover path,
  semantic rewrite, deletion, and evidence boundary reviewable without temporal Concorde artifacts.

### Assumptions

- The Concorde repository requires Git and treats an exact commit as the bootstrap transaction base.
- Maintainer classification is semantic: touching a Protocol implementation file is not sufficient
  when the change merely restores already specified behavior.
- External projects need a separately specified upgrade mechanism only when a released Protocol
  change makes their maintained state incompatible.

## Success Criteria

- **SC-001**: Every maintained description of Concorde self-development names the isolated-worktree
  Protocol-evolution route and excludes attempts, fast loop, standard loop, and delivery for normative
  semantic changes.
- **SC-002**: A representative Protocol cutover produces no attempt/checklist/selection diff and yields
  one commit whose target checkout passes every applicable deterministic and executable check.
- **SC-003**: Dirty, active-attempt, stale-base, incomplete, or failed examples are rejected before
  merge while the base commit remains recoverable without a custom migrator.
- **SC-004**: Normal conformance-restoring implementation fixes remain eligible for the standard
  lifecycle and the bootstrap exception cannot be selected merely from file location.
