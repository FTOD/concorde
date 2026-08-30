# Feature Abstract: Fast Loop

`feature.concorde.workflow.fast-loop` · specified at `module.concorde` · about three minutes. This
page is enough to understand the fast path; the links at the end only redirect to deeper detail.

## Purpose

Fast Loop lets a maintainer complete a small, well-bounded modification that begins from one existing
anchor feature and may affect other related existing features. It directly reconciles code, tests,
and all related maintained documentation without an implementation attempt, while redirecting
module-boundary, project-policy, larger, or riskier work to the normal workflow before mutation.

## Functionality

| Part | What it does |
|---|---|
| `speckit.fast-loop` | Accepts a concrete small-change description and resolves a selected anchor feature. |
| Eligibility preflight | Discovers every affected existing feature; confirms accepted baselines, no active attempts, stable module responsibilities and dependencies, stable project-level user compatibility/migration policy, and safe worktree ownership. |
| Direct change | Updates code, proportional tests, every affected feature's durable documents, and related contract, architecture-detail, and user guidance sources. |
| Verification | Runs proportional tests and deterministic validation, presents any architecture-source diff for required maintainer review, then reports the anchor, affected set, files, evidence, and preserved unrelated work. |
| Escalation | Rejects ineligible work before mutation and points to the earliest applicable stage of the full workflow. |

The command updates `design.md` and keeps `abstract.md` faithful only when required behavior changes;
it updates `implementation.md` whenever verified realization changes. It never creates or uses an
`attempt/`, plan, task list, or acceptance proposal.

**Not part of this feature**: first-time realization, active attempts in any affected feature, new or
restructured features or modules, changed module responsibilities or dependencies, changes to the
project's compatibility or migration policy for users of the whole project, unrelated source edits,
and hidden execution of the ordinary planning, task, implementation, convergence, or acceptance
phases.

## Structure

The parent <a href="/architecture/concorde-workflow-components.html">workflow components</a> view
(maintained source `../../diagrams/concorde-workflow-components.json`) is sufficient for this child.

```text
Maintainer request
      │
      ▼
anchor feature + bounded impact discovery + worktree ──▶ eligibility decision
                                                            ├─ ineligible ──▶ no edits + full-flow guidance
                                                            └─ eligible ───▶ code + tests + all related docs
                                                                                  │
                                                                                  ▼
                                                                        checks + truthful report
```

The selected feature is an anchor, not the only behavioral authority in scope. The command opens an
additional feature body only when bounded evidence makes it part of the affected set, never reads an
affected feature's attempt, and keeps unrelated feature, architecture, and worktree sources outside
the direct change set.

## Logic

1. Resolve a canonical selected anchor, use bounded module, contract, implementation, test, and
   documentation evidence to discover every affected feature, and inspect each affected feature's
   durable trio and attempt state deliberately.
2. Decide eligibility before mutation. Reject new feature/module structure, changed module
   responsibility or dependency direction, changed whole-project user compatibility/migration
   policy, unaccepted or active affected roots, material ambiguity, and edits that cannot be
   separated safely.
3. Apply the bounded code and test change, reconcile every affected feature plus related contract,
   architecture-detail, and user-facing documentation, and create no attempt artifacts.
4. Run proportional tests and deterministic validation. Repair within the same loop or report the
   remaining failure without claiming success. When architecture sources changed, present their
   exact diff and keep the result review-pending until the maintainer confirms it.
5. Report the anchor, affected feature set, eligibility, files, documentation impact, checks,
   architecture-review state, preserved unrelated work, and confirmation that no attempt or
   acceptance operation ran.

**Rules the implementation must keep**

- Resolve an existing anchor and identify every affected existing feature before changing anything;
  each affected root requires an accepted baseline and no active attempt. (FR-001, FR-002, FR-003)
- Cross-feature and contract-format changes remain eligible when bounded, but module responsibility,
  dependency direction, and project-level user compatibility/migration policy changes always
  escalate before mutation. (FR-004, FR-014, FR-015)
- Direct edits keep code, proportional tests, every affected durable feature document, related
  contract and architecture detail, and user guidance truthful without creating or invoking attempt
  lifecycle artifacts. (FR-006, FR-007, FR-008, FR-009)
- Preserve unrelated worktree changes and stop before writing when overlapping ownership is unsafe.
  (FR-005, FR-010)
- Claim completion only after proportional checks pass, and report the anchor, affected set, changes,
  evidence, failures, and skipped ceremony explicitly. (FR-011, FR-012, FR-013)
- Treat validated contract or maintained-diagram edits as review-pending until the maintainer reviews
  their exact diff; this review creates no attempt or acceptance proposal. (FR-016)

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md)
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md)
- **Contracts** — `contracts/fast-loop-command.md`; parent contract sources under `../../contracts/`
- **The level this feature belongs to** — [module.md](../../../../module.md)
- **Parent feature** — [Concorde Workflow](../../design.md)
