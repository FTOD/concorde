---
title: Concorde Workflow
sidebar_position: 6
---

# Concorde Workflow

Concorde surrounds the normal Spec Kit lifecycle with architectural ownership, bounded context,
deterministic validation, and durable-design review. It does not replace specification, planning,
tasks, or implementation.

The authoritative workflow, including requirements and edge cases, is
[Feature 001](../specs/concorde/features/001-concorde-workflow/spec.md). The stages below
explain how to apply it in a project.

At any stage, invoke `speckit.concorde.ask <question>` when the uncertainty is about the workflow
itself rather than the product being implemented. The agent grounds its read-only answer in the
installed extension/preset guidance and, for project-specific questions, only the smallest relevant
maintained project sources. It cites those paths, distinguishes framework rules from project
observations and inference, and asks for focused clarification when it cannot safely resolve the
target. It does not run another stage on your behalf.

## Before feature work: establish the root

Run `speckit.concorde.init` after Concorde has been installed in a Spec Kit project. Initialization
does not attempt to decompose the whole future system. It proposes the minimum root package needed
to reason safely: a stable module ID, responsibility and boundary, explicit provided and required
contract sets, current-level features, immediate children, and a one-level view.

The proposal is reviewable and no maintained architecture is written until it is explicitly
approved. Re-running the accepted initialization is idempotent; conflicting existing content is not
silently overwritten.

## 1. Find the owning level

Request context for the root module. Ask whether the new behavior is provided by that module or by
one visible child:

- If one child owns the whole behavior, zoom into that child and repeat the question.
- If multiple immediate children collaborate, place the feature on their nearest common parent.
- If no existing module has a coherent responsibility for it, review the architecture instead of
  letting the agent invent ownership while planning code.

`speckit.concorde.context` returns exactly one bounded level. It gives the agent the current module,
its features and I/O, immediate children and their I/O, externals, current-level scenarios,
refinement links, and deeper navigation references. It does not select a feature or permanently load
the entire hierarchy.

## 2. Create or select the feature workspace

For a new feature, `speckit.concorde.feature.create` first proposes the providing module, canonical
feature path, module registration, affected contracts/view, and source digest. After approval it
uses the normal specification phase to establish root `spec.md` and a `design.md` that explicitly
states no realization has yet been hardened.

For an existing feature, `speckit.concorde.feature.select` verifies its identity, providing module,
durable files, path confinement, and attempt state before updating `.specify/feature.json`. If a
non-empty implementation attempt already exists, resuming it must be explicit.

Selection is what routes later Spec Kit phases. Context retrieval is only a read operation.

## 3. Specify observable behavior

Use the normal `specify` and `clarify` phases to describe:

- actors and value;
- observable behavior and constraints;
- expected failures and degraded behavior;
- measurable outcomes;
- boundary contracts; and
- representative user or system scenarios.

Keep the distinction clear: the prose defines the feature; scenarios illustrate it. When multiple
components collaborate, add one core Archify architecture diagram showing stable participants,
responsibilities, interactions, and contracts, or state why the bounded module view plus prose is
sufficient. Add sequence, workflow, data-flow, or lifecycle diagrams only as supplemental answers to
narrower dynamic questions.

Requirements-quality checklists belong under `implementation/checklists/`. A checklist records the
current review cycle; accepted behavioral conclusions must be incorporated into `spec.md`.

## 4. Approve architecture before planning implementation

Before accepting a plan, review the structure that the agent will be allowed to realize:

- Is the providing module and abstraction level correct?
- Does a parent feature need child-level refinements?
- Which immediate submodules participate?
- Does every boundary crossing name a provided or required contract?
- Are contract direction, obligations, failures, representation, and compatibility explicit?
- Does the current-level view show only permitted participants?
- What implementation and test evidence will demonstrate agreement?

For a custom serialized contract, require a readable schema or grammar, field meanings, examples,
compatibility rules, and conformance evidence. For an adopted standard, identify the standard and
version and briefly explain the information passed.

Architecture review happens before code planning because a structurally valid implementation can
still embody the wrong ownership or dependency direction.

## 5. Plan one implementation attempt

The normal `plan` phase reads two durable inputs:

- `spec.md`, which defines required behavior; and
- `design.md`, which records the accepted realization baseline.

It writes the proposed delta beneath `implementation/`: research, plan, technical model, quick start,
and related artifacts. `tasks` then creates dependency-ordered executable work in the same attempt.
If architecture, contracts, diagrams, traceability, validation, or generated freshness are affected,
the plan and tasks must include that work explicitly.

Run `analyze` after task generation to check consistency among the durable behavior, accepted design,
plan, and tasks before code changes begin.

## 6. Implement with bounded context

`implement` executes the selected task set. Give the coding agent the selected feature, its owning
module level, relevant contracts and diagrams, and the evidence expected for the current tasks. Only
descend into a child module when the work actually requires that child's internal level.

This keeps an agent from treating the whole repository as undifferentiated context. It also makes
structural deviations visible: the agent can choose low-level code details, but it should not invent
new cross-module dependencies or silently change contracts.

After implementation, use `converge` to compare code with intended behavior and append genuinely
unbuilt work. Convergence must not rewrite the specification to make incomplete code appear correct.

## 7. Validate and reconcile disagreement

Run `speckit.concorde.validate` after maintained structural changes, during implementation, and
before hardening. It deterministically checks source parsing, unique identities, containment and
refinement, feature ownership, contract completeness, scenario scope, view depth, references,
evidence status, and generated freshness.

Validation is read-only. It reports rule, severity, location, and remediation in stable order. Valid
architecture does not prove that code conforms; missing evidence remains `unknown`, and conflicting
specification, design, code, tests, or projections are reported as disagreement.

Review behavioral, architectural, implementation, and evidence changes together. Do not resolve a
finding by weakening the wrong authority.

## 8. Harden an accepted milestone

Hardening is appropriate only when:

- the active attempt has a real `implementation/tasks.md` with at least one task;
- every recognizable task is complete;
- every existing checklist item is satisfied;
- validation and evidence have been reviewed; and
- the maintainer accepts the implementation as the new durable baseline.

The agent first synthesizes a proposed `design.md` from the complete attempt, relevant architecture,
contracts, code, and tests. The proposal names the exact design target, the complete
`implementation/` removal target, and a digest of the source bytes reviewed.

Checked boxes do not grant approval. Only explicit acceptance of that exact proposal authorizes the
runtime to update `design.md` and remove `implementation/` atomically. A stale digest, changed path,
symlink, incomplete task, unresolved checklist, or failed apply leaves the previous state
recoverable.

## 9. Publish the read model

The docsite publishes module and contract architecture, durable feature specifications and designs,
and explanatory project guides. It excludes the active implementation attempt from the Features
view. Publication is deterministic and read-only; generated pages and diagram deliveries never
become a second source of project intent.

The publication behavior is specified separately by
[Feature 002](../specs/concorde/features/002-create-project-docsite/spec.md).

## Starting the next change

A hardened feature has no active `implementation/` directory. Select it again, revise `spec.md` if
the required behavior changes, review any affected architecture, and start a fresh plan. The current
`design.md` remains the accepted realization until another complete attempt is explicitly hardened.

Use [Commands and installed surfaces](commands.md) for exact command timing, side effects, and the
difference between agent skills and terminal commands.
