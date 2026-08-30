# Feature Abstract: Fast Loop

`feature.concorde.workflow.fast-loop` · specified at `module.concorde` · about three minutes. This
page is enough to understand the fast path; the links at the end only redirect to deeper detail.

## Purpose

Fast Loop lets a maintainer complete a small, well-bounded modification to one existing feature in a
single command. It directly reconciles code, tests, and related maintained documentation without an
implementation attempt, while redirecting larger or riskier work to the normal workflow before any
mutation.

## Functionality

| Part | What it does |
|---|---|
| `speckit.fast-loop` | Accepts a concrete small-change description and resolves one selected feature. |
| Eligibility preflight | Confirms an accepted baseline, no active attempt, one-feature ownership, no architecture or contract impact, and safe worktree ownership. |
| Direct change | Updates code, proportional tests, the selected feature's affected durable documents, and related non-architectural user guidance. |
| Verification | Runs proportional tests and deterministic validation, then reports scope, files, evidence, and preserved unrelated work. |
| Escalation | Rejects ineligible work before mutation and points to the earliest applicable stage of the full workflow. |

The command updates `design.md` and keeps `abstract.md` faithful only when required behavior changes;
it updates `implementation.md` whenever verified realization changes. It never creates or uses an
`attempt/`, plan, task list, or acceptance proposal.

**Not part of this feature**: first-time realization, active attempts, new or restructured features
or modules, architecture or boundary-contract changes, cross-feature behavior, compatibility or
migration work, and hidden execution of the ordinary planning, task, implementation, convergence,
or acceptance phases.

## Structure

The parent <a href="/architecture/concorde-workflow-components.html">workflow components</a> view
(maintained source `../../diagrams/concorde-workflow-components.json`) is sufficient for this child.

```text
Maintainer request
      │
      ▼
selected feature + accepted realization + worktree ──▶ eligibility decision
                                                         ├─ ineligible ──▶ no edits + full-flow guidance
                                                         └─ eligible ───▶ code + tests + related docs
                                                                               │
                                                                               ▼
                                                                     checks + truthful report
```

The selected feature remains the only behavioral authority in scope. Sibling bodies, module design
sources, architecture views, boundary contracts, and unrelated worktree changes stay outside the
direct change set.

## Logic

1. Resolve one canonical selected feature and inspect its accepted realization, attempt state,
   bounded context, relevant implementation evidence, and current worktree changes.
2. Decide eligibility before mutation. Reject and redirect anything outside one already-realized
   feature's existing ownership or anything whose edits cannot be separated safely.
3. Apply the bounded code and test change, reconcile affected feature and user-facing documentation,
   and create no attempt artifacts.
4. Run proportional tests and deterministic validation. Repair within the same loop or report the
   remaining failure without claiming success.
5. Report the selected target, eligibility, files, documentation impact, checks, preserved unrelated
   work, and confirmation that no attempt or acceptance operation ran.

**Rules the implementation must keep**

- Resolve exactly one existing selected feature and require a concrete request before changing
  anything. (FR-001, FR-002)
- Fast-loop requires an accepted baseline, no active attempt, and scope wholly inside the selected
  feature's existing outcome; architecture, contracts, compatibility, and cross-feature behavior
  always escalate before mutation. (FR-003, FR-004, FR-014)
- Direct edits keep code, proportional tests, affected durable feature documents, and related user
  guidance truthful without creating or invoking attempt lifecycle artifacts. (FR-006, FR-007,
  FR-008, FR-009)
- Preserve unrelated worktree changes and stop before writing when overlapping ownership is unsafe.
  (FR-005, FR-010)
- Claim completion only after proportional checks pass, and report target, changes, evidence,
  failures, and the skipped ceremony explicitly. (FR-011, FR-012, FR-013)

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md)
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md)
- **Contracts** — `contracts/fast-loop-command.md`; parent contract sources under `../../contracts/`
- **The level this feature belongs to** — [module.md](../../../../module.md)
- **Parent feature** — [Concorde Workflow](../../design.md)
