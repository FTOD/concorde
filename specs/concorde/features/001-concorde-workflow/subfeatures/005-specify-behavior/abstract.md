# Feature Abstract: Specify Behavior

`feature.concorde.workflow.specify-behavior` · sub-feature of `feature.concorde.workflow`, specified
at `module.concorde` · about four minutes. This page is enough to understand this workflow step;
the links at the end only redirect you when you want more.

## Purpose

Let a maintainer define focused, testable behavior for the selected root with a faithful abstract,
resolve only the uncertainty that matters, and record requirements-quality review — while keeping
durable intent (`abstract.md`, `design.md`), accepted realization (`implementation.md`), and temporal review
state (`attempt/checklists/`) in their own places. This step is the only writer of a
feature's abstract.

## Functionality

The owned command surfaces are the three Spec Kit phases that shape intent, each routed through the
selected workspace before touching any artifact:

| Surface | Reads | Writes |
|---|---|---|
| `speckit.specify` | The level's `module.md` and bounded view; the existing `abstract.md` and `design.md` | `abstract.md` and `design.md` together; for a new root also a `implementation.md` holding only the not-yet-accepted state |
| `speckit.clarify` | `abstract.md`, `design.md` | Accepted answers encoded into the same `design.md`; `abstract.md` wherever it summarized the changed behavior |
| `speckit.checklist` | `abstract.md`, `design.md` | A checklist under the selected root's `attempt/checklists/` covering, among other items, the abstract's shape, budget, and faithfulness |

An existing feature `implementation.md` stays byte-identical; specify seeds it only when missing.
The level's module `design.md` is neither read implicitly nor written; it is
opened only when the maintainer asks for a recorded detail. For a sub-feature, the parent's durable
sources are read-only aggregate context and sibling bodies are excluded. A child specification owns
one focused outcome and does not repeat parent-owned facts; a cross-component specification declares
one text-backed core diagram or records why prose and the bounded view suffice.

**Not part of this step**: resolving the selection itself (the workspaces step), planning an attempt
(the plan step), and writing substantive content into any `implementation.md` (the accept step).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. Three phase surfaces, resolved through the selected-workspace
adapter, write the two read-and-authority documents of one root and one temporal checklist
directory.

```text
Maintainer ──describe · answer · review──▶ specify · clarify · checklist (Spec Kit phase surfaces)
                                              └─▶ selected-workspace adapter ──▶ .specify/feature.json
                                                    ├─ context (read):  level module.md + bounded view · parent trio (sub-feature)
                                                    ├─ writes:          abstract.md · design.md · [new root: placeholder implementation.md]
                                                    ├─ writes:          attempt/checklists/
                                                    └─ untouched:       existing feature implementation.md · module design.md · siblings
```

## Logic

1. Resolve the selected workspace; every artifact path comes from the Feature Workspace Protocol.
2. Specify: author `abstract.md` and `design.md` together, reading the level's `module.md` and bounded
   view for architecture context; for a new root, seed the placeholder `implementation.md`.
3. Clarify: put consequential scope, security, and user-outcome questions first; encode accepted
   answers into `design.md` and update the abstract wherever it summarized the changed behavior.
4. Checklist: write the requirements-quality checklist beneath `attempt/checklists/`,
   including the abstract's shape, budget, and faithfulness; a abstract that states something `design.md`
   does not, whose rules cite no requirement, or that cannot stand alone is named as a failing item.
5. Leave every `implementation.md` byte-identical and the parent and siblings untouched.

**Rules the implementation must keep**

- All three phases resolve the selected workspace before any artifact access (FR-001).
- Specification and clarification write only the selected canonical `abstract.md` and `design.md`
  (FR-002).
- Existing durable `implementation.md` content stays byte-identical through these phases (FR-003).
- Requirements-quality checklists live only in the selected temporal checklist directory (FR-004).
- A child specification owns one focused outcome and does not duplicate parent-owned aggregate facts
  (FR-005).
- A cross-component specification declares one text-backed core diagram or records why prose and the
  bounded view suffice (FR-006).
- Clarification prioritizes consequential choices, encodes answers in `design.md`, and updates the
  abstract where it summarized the changed behavior (FR-007).
- A new root gets `abstract.md`, `design.md`, and placeholder `implementation.md`, never a legacy filename;
  substantive implementation is written by delivery (FR-008).
- The level's `module.md` is bounded architecture context; module `design.md` is never an
  implicit input and is never written here (FR-009).
- The authored abstract is self-contained, has exactly the five sections in order, links a structure
  view from its structure section, cites a requirement ID for every `Logic` rule, stays within
  budget, and states nothing absent from `design.md` (FR-010).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-010 and
  SC-001 to SC-006.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been accepted yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), which define the
  abstract shape, the reading budget, and how the tiers stay honest.
- **Contracts** — `../../contracts/agent-commands.md` for the three surfaces and
  `../../contracts/feature-workspace.schema.json` for the paths they
  write.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [manage feature workspaces](../004-manage-feature-workspaces/design.md)
  and [plan delivery](../006-plan-delivery/design.md).
