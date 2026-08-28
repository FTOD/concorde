# TL;DR: Harden Design

`feature.concorde.workflow.harden-design` · sub-feature of `feature.concorde.workflow`, specified at
`module.concorde` · about four minutes. This page is enough to understand this workflow step; the
links at the end only redirect you when you want more.

## Purpose

Let a maintainer explicitly accept the durable realization of one completed feature or sub-feature
milestone into that root's feature `design.md`, carry the rationale developed during the attempt
into the level's module `design.md` when the proposal includes it, and atomically remove exactly that
milestone's `implementation/` attempt. It never touches the TL;DR or the specification.

## Functionality

The owned command surface is `speckit.concorde.feature.harden`, in two modes bound together by an
exact proposal:

| Mode | Reads | Produces |
|---|---|---|
| Proposal (read-only) | The complete attempt, the durable trio, the level summary and module reference | Eligibility; the runtime-resolved candidate feature `design.md`; task and checklist summaries; the selected target; the optional module `design.md` amendment target; the whole-attempt cleanup target; the source digest; the retained authorities |
| Apply (explicit approval of that exact, unchanged proposal) | The reviewed proposal | The feature `design.md` matching the candidate; the module `design.md` matching the reviewed amendment when one was proposed; the attempt removed; a result with prior and resulting digests, removed artifacts, selected feature, and retained authorities |

An attempt with incomplete tasks or unresolved checklist items is ineligible and nothing changes.
The candidate captures accepted collaboration, flows, decisions, evidence, limitations, and the
implementation detail a coder needs under the parent's six fixed sections, without copying the task
log. A module amendment carries only detail and rationale developed during the attempt, under the
reference's stable headings, and never alters facts owned by `module.md`, contracts, or the level
view. A stale or interrupted apply leaves the previous feature `design.md`, the previous module
`design.md`, and the complete attempt recoverable.

**Not part of this step**: executing incomplete work (the execute step), changing behavior
requirements or refreshing the TL;DR (the specify step), and validation (the validate step).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. The runtime resolves the candidate; the maintainer reviews the
exact proposal; only their approval lets the runtime mutate the selected root and, optionally, the
level's module reference.

```text
Maintainer ──review · explicit approval──▶ speckit.concorde.feature.harden ──▶ launcher + runtime
                                                                                 ├─ proposal: implementation/ (tasks · checklists · research · evidence) + trio + module.md + module design.md
                                                                                 │            → candidate feature design.md · optional module design.md amendment · cleanup manifest · digest
                                                                                 └─ apply:    feature design.md ⟵ candidate · module design.md ⟵ amendment · implementation/ removed   (atomic)
                                                                                              never: tldr.md · spec.md · module.md · another level's design.md · implementation.md
```

## Logic

1. Check eligibility: a recognizable task list, all tasks complete, all checklist items complete
   and well formed.
2. Synthesize the candidate feature `design.md` and, when warranted, the module `design.md`
   amendment; compute the source digest and the whole-attempt cleanup target.
3. Present the exact proposal — candidate, amendment, cleanup manifest, digest, retained
   authorities — and change nothing.
4. On explicit approval of that unchanged proposal, apply realization replacement, reference
   amendment, and attempt removal atomically; on staleness, an unsafe path, or interruption, restore
   every prior state.
5. Report prior and resulting digests, removed artifacts, the selected feature, and the retained
   authorities.

**Rules the implementation must keep**

- Eligibility needs at least one recognizable task, every task complete, and every existing checklist
  item complete and well formed (FR-001).
- Proposal mode is read-only and returns the candidate location, task and checklist summaries,
  selected target, optional module-reference amendment target, cleanup target, and source digest
  (FR-002).
- The candidate captures collaboration, flows, decisions, evidence, limitations, and coder-level
  detail under the six fixed sections, without copying the task log (FR-003).
- Apply requires explicit approval of the exact unchanged proposal (FR-004).
- Mutation targets are only the selected root's `design.md`, its complete `implementation/`, and —
  when proposed — the module `design.md` of the level where the feature is specified; any
  `module.md`, `tldr.md`, `spec.md`, other-level `design.md`, or `implementation.md` is rejected
  (FR-005).
- Replacement, amendment, and removal complete atomically or every prior state is restored (FR-006).
- Child hardening preserves the parent and siblings; parent hardening preserves every child root
  (FR-007).
- A success result reports prior and resulting feature and module `design.md` digests, removed
  artifacts, the selected feature, and retained authorities (FR-008).
- A module amendment holds only attempt-developed detail and rationale under stable headings and
  never restates or alters facts owned by `module.md`, contracts, or the level view (FR-009).
- The first accepted milestone writes the feature `design.md` in full; later ones complete or update
  it, never leaving the placeholder beside accepted content (FR-010).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [spec.md](spec.md): FR-001 to FR-010 and
  SC-001 to SC-004.
- **How the accepted implementation realizes this step** — [design.md](design.md) (states that no
  realization has been hardened yet).
- **The parent feature** — its [TL;DR](../../tldr.md) and [spec.md](../../spec.md), which define the
  six fixed sections of a feature `design.md`.
- **Contracts** — `../../contracts/feature-workspace.schema.json`
  (the hardening proposal), `../../contracts/agent-commands.md`, and
  `../../contracts/architecture-sources.md`.
- **The level** — [module.md](../../../../module.md).
- **Previous step** — [validate architecture](../008-validate-architecture/spec.md); a later attempt
  begins again with [plan delivery](../006-plan-delivery/spec.md).
