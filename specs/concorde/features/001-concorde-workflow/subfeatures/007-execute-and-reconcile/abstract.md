# Feature Abstract: Execute and Reconcile

`feature.concorde.workflow.execute-and-reconcile` · sub-feature of `feature.concorde.workflow`,
specified at `module.concorde` · about three minutes. This page is enough to understand this
workflow step; the links at the end only redirect you when you want more.

## Purpose

Let a coding agent execute the approved task list, report cross-artifact inconsistencies without
changing analyzed artifacts, record problems only in the project reflection log, and append only
genuine remaining work — all inside the selected root's bounded context, with everything it learns
recorded where acceptance can later find it. The maintainer asks for the ready tasks to be delivered,
verified, analyzed, and honestly reflected in the task list.

## Functionality

The owned command surfaces are `speckit.implement`, `speckit.analyze`, and `speckit.converge`,
each confined to the selected lifecycle root and its attempt.

| Surface | What it does | Writes |
|---|---|---|
| `speckit.implement` | Executes tasks in dependency order against the feature `implementation.md` baseline, runs relevant checks, and marks completion only after proportionate verification | Code, tests, `attempt/` |
| `speckit.analyze` | Reports high-signal inconsistencies and coverage gaps across `abstract.md`, `design.md`, the accepted realization, plan, tasks, and constitution — including any abstract statement the specification does not support, naming the prevailing requirement | `workspace.reflections` only when a problem must be recorded; otherwise nothing |
| `speckit.converge` | Appends only verified remaining work as new dependency-ordered tasks, preserving completed ones and avoiding duplicates | `attempt/` |

Analysis distinguishes absent evidence, disagreement, ambiguity, duplication, and coverage gaps
rather than collapsing them. Implementation context excludes implicit parent and sibling attempts,
unrelated deeper architecture, and any module `design.md` not deliberately opened and cited. Design
decisions, alternatives, and implementation detail discovered along the way are written inside the
attempt. None of the three phases updates `abstract.md`, `design.md`, the feature `implementation.md`, any
`module.md` or module `design.md`, or removes the attempt.

**Not part of this step**: validating maintained architecture (the validate step) and compacting the
attempt into the accepted realization (the accept step).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. Three phase surfaces, resolved through the selected-workspace
adapter, work between the durable trio and the attempt.

```text
Maintainer ──execute · analyze · converge──▶ implement · analyze · converge (Spec Kit phase surfaces)
                                                └─▶ selected-workspace adapter ──▶ .specify/feature.json
                                                      ├─ reads:   abstract.md · design.md · implementation.md (baseline) · attempt/ (plan, tasks, checklists)
                                                      ├─ writes:  code · tests · attempt/ (task state, appended tasks, recorded rationale) · reflections.md (problems only)
                                                      └─ never:   abstract.md · design.md · feature implementation.md · module.md · module implementation.md · attempt removal
```

## Logic

1. Resolve the selected root; every artifact must belong to it.
2. Implement: run ready tasks in dependency order with the feature `implementation.md` as the baseline, run
   relevant checks, and update completion only when evidence supports it.
3. Record any design decision, alternative, or implementation detail discovered during execution
   inside the attempt.
4. Analyze: read the abstract, specification, accepted realization, plan, and tasks, and report
   inconsistencies and gaps — including abstract statements the specification does not support —
   while preserving every file except any required project reflection-log record.
5. Converge: append only verified remaining work as new dependency-ordered tasks; if nothing genuine
   remains, append nothing.

**Rules the implementation must keep**

- All three phases resolve and remain within the selected lifecycle root (FR-001).
- Implementation honors task dependencies, reads the feature `implementation.md` as its baseline, and updates
  completion only after proportionate verification (FR-002).
- Implementation context excludes implicit parent and sibling attempts, unrelated deeper
  architecture, and any module `design.md` not deliberately opened and cited (FR-003).
- Analysis preserves every file except `workspace.reflections`, writes that log only when reflection
  recording requires it, prioritizes specification, accepted realization, plan, task, and
  constitution inconsistencies, and reports any `abstract.md`/`design.md` disagreement naming the
  prevailing requirement (FR-004).
- Analysis distinguishes absent evidence, disagreement, ambiguity, duplication, and coverage gaps
  (FR-005).
- Convergence appends only verified remaining work, preserves completed tasks, and avoids duplicates
  (FR-006).
- No phase updates `abstract.md`, `design.md`, the feature `implementation.md`, any `module.md` or module
  `implementation.md`, or removes the attempt (FR-007).
- Rationale, alternatives, and implementation detail discovered during execution are recorded in the
  attempt so acceptance can carry the durable parts forward (FR-008).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-008 and
  SC-001 to SC-004.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been accepted yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), which state that
  `design.md` prevails over the abstract and that attempts are temporal.
- **Contracts** — `../../contracts/agent-commands.md` for the three surfaces and
  `../../contracts/feature-workspace.schema.json` for the attempt
  paths.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [plan delivery](../006-plan-delivery/design.md) and
  [validate architecture](../008-validate-architecture/design.md).
