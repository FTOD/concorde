# TL;DR: Specify Behavior

`feature.concorde.workflow.specify-behavior` · sub-feature of `feature.concorde.workflow`, specified
at `module.concorde` · about four minutes. This page is enough to understand this workflow step;
the links at the end only redirect you when you want more.

## Purpose

Let a maintainer define focused, testable behavior for the selected root with a faithful TL;DR,
resolve only the uncertainty that matters, and record requirements-quality review — while keeping
durable intent (`tldr.md`, `spec.md`), accepted realization (`design.md`), and temporal review
state (`implementation/checklists/`) in their own places. This step is the only writer of a
feature's TL;DR.

## Functionality

The owned command surfaces are the three Spec Kit phases that shape intent, each routed through the
selected workspace before touching any artifact:

| Surface | Reads | Writes |
|---|---|---|
| `speckit.specify` | The level's `module.md` and bounded view; the existing `tldr.md` and `spec.md` | `tldr.md` and `spec.md` together; for a new root also a `design.md` holding only the not-yet-hardened state |
| `speckit.clarify` | `tldr.md`, `spec.md` | Accepted answers encoded into the same `spec.md`; `tldr.md` wherever it summarized the changed behavior |
| `speckit.checklist` | `tldr.md`, `spec.md` | A checklist under the selected root's `implementation/checklists/` covering, among other items, the TL;DR's shape, budget, and faithfulness |

An existing feature `design.md` stays byte-identical through all three phases, and none of them
creates an `implementation.md`. The level's `design.md` is neither read implicitly nor written; it is
opened only when the maintainer asks for a recorded detail. For a sub-feature, the parent's durable
sources are read-only aggregate context and sibling bodies are excluded. A child specification owns
one focused outcome and does not repeat parent-owned facts; a cross-component specification declares
one text-backed core diagram or records why prose and the bounded view suffice.

**Not part of this step**: resolving the selection itself (the workspaces step), planning an attempt
(the plan step), and writing substantive content into any `design.md` (the harden step).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. Three phase surfaces, resolved through the selected-workspace
adapter, write the two read-and-authority documents of one root and one temporal checklist
directory.

```text
Maintainer ──describe · answer · review──▶ specify · clarify · checklist (Spec Kit phase surfaces)
                                              └─▶ selected-workspace adapter ──▶ .specify/feature.json
                                                    ├─ context (read):  level module.md + bounded view · parent trio (sub-feature)
                                                    ├─ writes:          tldr.md · spec.md · [new root: placeholder design.md]
                                                    ├─ writes:          implementation/checklists/
                                                    └─ untouched:       feature design.md · module design.md · siblings
```

## Logic

1. Resolve the selected workspace; every artifact path comes from the Feature Workspace Protocol.
2. Specify: author `tldr.md` and `spec.md` together, reading the level's `module.md` and bounded
   view for architecture context; for a new root, seed the placeholder `design.md`.
3. Clarify: put consequential scope, security, and user-outcome questions first; encode accepted
   answers into `spec.md` and update the TL;DR wherever it summarized the changed behavior.
4. Checklist: write the requirements-quality checklist beneath `implementation/checklists/`,
   including the TL;DR's shape, budget, and faithfulness; a TL;DR that states something `spec.md`
   does not, whose rules cite no requirement, or that cannot stand alone is named as a failing item.
5. Leave every `design.md` byte-identical and the parent and siblings untouched.

**Rules the implementation must keep**

- All three phases resolve the selected workspace before any artifact access (FR-001).
- Specification and clarification write only the selected canonical `tldr.md` and `spec.md`
  (FR-002).
- Existing durable `design.md` content stays byte-identical through these phases (FR-003).
- Requirements-quality checklists live only in the selected temporal checklist directory (FR-004).
- A child specification owns one focused outcome and does not duplicate parent-owned aggregate facts
  (FR-005).
- A cross-component specification declares one text-backed core diagram or records why prose and the
  bounded view suffice (FR-006).
- Clarification prioritizes consequential choices, encodes answers in `spec.md`, and updates the
  TL;DR where it summarized the changed behavior (FR-007).
- A new root gets `tldr.md`, `spec.md`, and a placeholder `design.md`, never an `implementation.md`;
  the reference's substance is written by hardening (FR-008).
- The level's `module.md` is the bounded architecture context; the level's `design.md` is never an
  implicit input and is never written here (FR-009).
- The authored TL;DR is self-contained, has exactly the five sections in order, links a structure
  view from its structure section, cites a requirement ID for every `Logic` rule, stays within
  budget, and states nothing absent from `spec.md` (FR-010).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [spec.md](spec.md): FR-001 to FR-010 and
  SC-001 to SC-006.
- **How the accepted implementation realizes this step** — [design.md](design.md) (states that no
  realization has been hardened yet).
- **The parent feature** — its [TL;DR](../../tldr.md) and [spec.md](../../spec.md), which define the
  TL;DR shape, the reading budget, and how the tiers stay honest.
- **Contracts** — `../../contracts/agent-commands.md` for the three surfaces and
  `../../contracts/feature-workspace.schema.json` for the paths they
  write.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [manage feature workspaces](../004-manage-feature-workspaces/spec.md)
  and [plan delivery](../006-plan-delivery/spec.md).
