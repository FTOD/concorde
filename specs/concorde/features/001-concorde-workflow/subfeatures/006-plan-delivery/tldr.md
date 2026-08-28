# TL;DR: Plan Delivery

`feature.concorde.workflow.plan-delivery` · sub-feature of `feature.concorde.workflow`, specified at
`module.concorde` · about three minutes. This page is enough to understand this workflow step; the
links at the end only redirect you when you want more.

## Purpose

Turn the selected root's durable behavior and its accepted realization baseline into one bounded,
dependency-ordered delivery attempt — and, when the maintainer asks, a faithful projection of that
attempt's tasks into issues. The maintainer reviews architecture and contracts, chooses an approach,
and gets a task list confined to the root's active `implementation/`.

## Functionality

The owned command surfaces are `speckit.plan`, `speckit.tasks`, and `speckit.taskstoissues`, all
routed through the selected root's temporal attempt.

| Input | Role in planning |
|---|---|
| `spec.md` | Required behavior |
| Feature `design.md` | The accepted realization baseline; the not-yet-hardened placeholder means there is no baseline, not an invented one |
| `tldr.md` | Orientation only; never a substitute for `spec.md` |
| The level's `module.md` and bounded view | Architecture context |
| The level's `design.md` | Consulted only for a specific recorded detail, and cited in the plan |
| Parent durable context (sub-feature) | Readable aggregate context; parent and sibling attempts are never implicit inputs |

Outputs land only beneath `implementation/`: a plan, a dependency-ordered task list that is
independently actionable and traceable to requirements or acceptance outcomes, and, on explicit
request, an issue set that preserves task identity, order, dependencies, and scope. Required
architecture, contract, validation, diagram, documentation, and evidence work appears explicitly.
Nothing durable changes — not `tldr.md`, `spec.md`, the feature `design.md`, any `module.md` or
module `design.md` — and no root-level compatibility copy is created. External issue writes need
separate authority.

**Not part of this step**: executing tasks (the execute step), hardening the result (the harden
step), and changing required behavior (the specify step).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. Three phase surfaces, resolved through the selected-workspace
adapter, read the root's durable trio and the level summary and write only the attempt.

```text
Maintainer ──approach · approve plan · request issues──▶ plan · tasks · taskstoissues (Spec Kit phase surfaces)
                                                            └─▶ selected-workspace adapter ──▶ .specify/feature.json
                                                                  ├─ reads:  spec.md (behavior) · design.md (baseline) · module.md + view
                                                                  ├─ orient: tldr.md          on demand, cited: level design.md
                                                                  └─ writes: implementation/ (plan · tasks · issue projection)
```

## Logic

1. Resolve the selected root and create or continue its one temporal attempt.
2. Read `spec.md` as required behavior and the feature `design.md` as the baseline; if the reference
   holds only the placeholder, plan as if no realization has been accepted.
3. Use the level's `module.md` and bounded view for architecture context; consult the level's
   `design.md` only for a specific recorded detail and cite it rather than copying it.
4. Write the plan, then generate dependency-ordered tasks that cover behavior, architecture,
   contracts, validation, documentation freshness, and acceptance evidence where applicable.
5. On explicit request, convert tasks to issues preserving order and dependencies; external writes
   require separately granted authority.

**Rules the implementation must keep**

- Planning resolves the selected root and creates or continues only its temporal attempt (FR-001).
- `spec.md` is required behavior, the feature `design.md` is the accepted baseline, the placeholder
  is the absence of a baseline, and the TL;DR only orients (FR-002).
- Child planning may read parent durable context but never sibling or parent attempts implicitly
  (FR-003).
- Tasks are dependency ordered, independently actionable, and traceable to requirements or
  acceptance outcomes (FR-004).
- Required architecture, contract, validation, diagram, documentation, and evidence work is explicit
  in the plan and tasks (FR-005).
- Issue conversion preserves task identity, order, dependencies, and scope and requires separate
  authority for external writes (FR-006).
- These phases never update `tldr.md`, `spec.md`, the feature `design.md`, any `module.md` or module
  `design.md`, and never create root-level compatibility copies (FR-007).
- The level's `module.md` is the bounded context; its `design.md` is consulted only for a specific
  recorded detail and cited (FR-008).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [spec.md](spec.md): FR-001 to FR-008 and
  SC-001 to SC-005.
- **How the accepted implementation realizes this step** — [design.md](design.md) (states that no
  realization has been hardened yet).
- **The parent feature** — its [TL;DR](../../tldr.md) and [spec.md](../../spec.md), which define the
  durable/temporal split this step relies on.
- **Contracts** — `../../contracts/agent-commands.md` for the three surfaces and
  `../../contracts/feature-workspace.schema.json` for the attempt
  paths.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [specify behavior](../005-specify-behavior/spec.md) and
  [execute and reconcile](../007-execute-and-reconcile/spec.md).
