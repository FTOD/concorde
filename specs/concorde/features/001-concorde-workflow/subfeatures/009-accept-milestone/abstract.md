# Feature Abstract: Deliver Milestone

`feature.concorde.workflow.accept-milestone` · sub-feature of `feature.concorde.workflow`, specified at
`module.concorde` · about four minutes. This page is enough to understand this workflow step; the
links at the end only redirect you when you want more.

## Purpose

Let a maintainer invoke one command to deliver a completed implementation attempt as a feature or
sub-feature root's durable `implementation.md`, carry the rationale developed during the attempt
into the level's module `design.md` when the proposal includes it, and atomically remove exactly that
milestone's `attempt/`. The invocation itself authorizes delivery, so the command never pauses for a
second approval. It never touches the abstract or the specification.

## Functionality

The owned command surface is `speckit.concorde.deliver`. Internally, two runtime modes remain bound
together by an exact proposal, but they are one user interaction:

| Mode | Reads | Produces |
|---|---|---|
| Proposal (read-only, internal) | The complete attempt, the durable trio, the level summary and module reference | Eligibility; the runtime-resolved candidate feature `implementation.md`; task and checklist summaries; the selected target; the optional module `design.md` amendment target; the whole-attempt cleanup target; the source digest; the retained authorities |
| Apply (automatic for the current proposal) | The invocation-authorized proposal | The feature `implementation.md` matching the candidate; the module `design.md` matching the amendment when one was proposed; the attempt removed; a result with prior and resulting digests, removed artifacts, selected feature, and retained authorities |

An attempt with incomplete tasks or unresolved checklist items is ineligible and nothing changes.
The candidate captures accepted collaboration, flows, decisions, evidence, limitations, and the
implementation detail a coder needs under the parent's six fixed sections, without copying the task
log. A module amendment carries only detail and rationale developed during the attempt, under the
reference's stable headings, and never alters facts owned by `module.md`, contracts, or the level
view. Reflection entries are presented transiently from the project log for review; neither durable
candidate may persist an `R-NNN` identifier or reflection entry content. A stale or interrupted apply leaves the previous feature `implementation.md`, the previous module
`design.md`, and the complete attempt recoverable.

**Not part of this step**: executing incomplete work (the execute step), changing behavior
requirements or refreshing the abstract (the specify step), and validation (the validate step).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. The delivery invocation authorizes the agent to generate the
digest-bound candidate and immediately ask the runtime to mutate the selected root and, optionally,
the level's module reference.

```text
Maintainer ──invoke once──▶ speckit.concorde.deliver ──▶ agent + launcher + runtime
                                                            ├─ propose: attempt/ + durable sources
                                                            │           → candidate feature implementation.md · optional module design.md amendment · cleanup manifest · digest
                                                            └─ apply immediately: feature implementation.md ⟵ candidate · module design.md ⟵ amendment · attempt/ removed   (atomic)
                                                                                  never: abstract.md · feature design.md · module.md · another level's design.md
```

## Logic

1. Check eligibility: a recognizable task list, all tasks complete, all checklist items complete
   and well formed.
2. Synthesize the candidate feature `implementation.md` and, when warranted, the module `design.md`
   amendment; compute the source digest and the whole-attempt cleanup target.
3. Treat the user's delivery invocation as authorization for the generated proposal; reject
   reflection identifiers copied into either durable candidate and do not ask a second approval
   question.
4. Immediately apply realization replacement, reference amendment, and attempt removal atomically;
   on staleness, an unsafe path, or interruption, restore every prior state.
5. Report prior and resulting digests, removed artifacts, the selected feature, and the retained
   authorities.

**Rules the implementation must keep**

- Eligibility needs at least one recognizable task, every task complete, and every existing checklist
  item complete and well formed (FR-001).
- Proposal mode is read-only and returns the candidate location, task and checklist summaries,
  selected target, optional module-reference amendment target, cleanup target, and source digest
  (FR-002).
- The candidate captures collaboration, flows, decisions, evidence, limitations, and coder-level
  detail under the six fixed sections, without copying the task log or reflection identity/content
  from the centralized project log (FR-003).
- Invoking delivery is the sole authorization; after candidate generation the command applies
  without displaying another approval question or waiting for another response (FR-004).
- Mutation targets are only the selected root's `implementation.md`, its complete `attempt/`, and —
  when proposed — the module `design.md` of the level where the feature is specified; any
  `module.md`, `abstract.md`, feature `design.md`, other-level `implementation.md`, or legacy name is rejected
  (FR-005).
- Replacement, amendment, and removal complete atomically or every prior state is restored (FR-006).
- Child milestone delivery preserves the parent and siblings; parent milestone delivery preserves every child root
  (FR-007).
- A success result reports prior and resulting feature `implementation.md` and module `design.md` digests, removed
  artifacts, the selected feature, and retained authorities (FR-008).
- A module amendment holds only attempt-developed detail and rationale under stable headings and
  never restates or alters facts owned by `module.md`, contracts, or the level view (FR-009).
- The first delivered milestone writes the feature `implementation.md` in full; later ones complete or update
  it, never leaving the placeholder beside accepted content (FR-010).
- Every current command, runtime operation, status, diagnostic, contract, schema, example, test,
  guide, and specification uses Deliver Milestone consistently; the superseded interface is rejected
  without an alias or transition period (FR-011).
- Removing the second interaction does not weaken digest binding, path constraints, candidate
  validation, atomic staging, rollback, or result reporting (FR-012).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-012 and
  SC-001 to SC-005.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been accepted yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), which define the
  six fixed sections of a feature `implementation.md`.
- **Contracts** — `../../contracts/feature-workspace.schema.json`
  (the delivery proposal), `../../contracts/agent-commands.md`, and
  `../../contracts/architecture-sources.md`.
- **The level** — [module.md](../../../../module.md).
- **Previous step** — [validate architecture](../008-validate-architecture/design.md); a later attempt
  begins again with [plan delivery](../006-plan-delivery/design.md).
