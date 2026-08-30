# Feature Abstract: Record and Triage Workflow Reflections

`feature.concorde.record-workflow-reflections` · specified at `module.concorde` · about seven
minutes. This page is enough to understand what the feature does, how it is structured, and how its
improvement loop works; the links at the end only redirect you when you want more.

## Purpose

When a coding agent plans or implements a feature and something does not work as the specification,
accepted realization, existing implementation, installed guidance, architecture, or plan says, it
records the problem in the phase where it happened. The project's one reflection log preserves that
evidence across every feature and attempt.

Recording alone is not self-improvement, so the feature also provides an explicit installed triage
workflow. Specialized investigators establish root cause and a safe route for one entry at a time;
specialized implementers execute only eligible plans in isolated worktrees; and the maintainer
controls merge and every final status or note in the log. Concorde installation projects this shared
workflow into supported agent platforms so a fresh project receives the improvement loop without
copying Concorde's repository-local Claude or Codex setup by hand.

## Functionality

| What | How it shows up |
|---|---|
| Automatic recording | During plan, tasks, implement, analyze, and converge, an agent appends or updates an entry when it meets a problem, then continues if it can. No new phase command or approval. |
| Project log | `reflections.md` directly inside the specification root, beside the root `module.md`; created from the installed template by the first recording phase and never removed. |
| Entry contract | Identifier, phase, date, selected feature, kind, concerned source, expected versus observed, effect, action, improvement, status, note when closed, and occurrence history. |
| Triage entry point | One installed skill with `status`, `investigate`, `implement`, and `merge` actions. `status` is read-only; all other actions preserve normal Concorde phase and maintainer authority. |
| Investigation | One specialized investigator per open entry establishes evidence, owning feature, route (`fast-loop`, `specify`, `dismiss`, or `blocked`), file set, change, validation, and risks in one plan. |
| Implementation | Ready fast-loop plans are grouped by owning feature and executed by specialized implementers in separate Git worktrees and branches, through Speckit Fast Loop, with one commit per successful plan. |
| Merge | A clean maintainer checkout is required; branches merge one at a time, applicable deterministic checks rerun, conflicts stop safely, and only successful worktrees and plan states are cleaned up. |
| Installation | Concorde distributes the shared skill, roles, deterministic queue helper, and default configuration as platform-appropriate Claude and Codex projections with common semantics and state. |
| Maintainer authority | Triage suggests resolution notes and commits but never edits reflection `Status` or `Note`; `specify`, `dismiss`, and `blocked` routes remain human decisions. |
| Acceptance and validation | Acceptance presents the feature's entries and requires every open one to remain cited; deterministic validation checks a present log read-only and reports nothing for an absent log. |

**Not part of this feature**: automatically changing reflection status, auto-implementing
`specify`/`dismiss`/`blocked` routes, per-feature logs, an external service, a dashboard, automatic
archiving, or identical model names and native isolation mechanisms across agent platforms.

## Structure

The core view is <a href="/architecture/workflow-reflection-components.html">workflow reflection
and triage components</a> (maintained source
`diagrams/workflow-reflection-components.json`). In one sketch:

```text
Concorde installation ──▶ installed phase guidance + triage skill + specialized roles
                                  │
Coding agent ── plan · tasks · implement · analyze · converge
                                  │ append/update
                                  ▼
                     <specification root>/reflections.md
                                  │ open entries
Maintainer ──▶ triage orchestrator ─┬─▶ investigator agents ─▶ reflection plans
                                    └─▶ implementer worktrees ─▶ Speckit Fast Loop
                                                                  │ commits + tests
                                                                  ▼
                                                       validation and merge gate
                                                                  │
                                                                  ▼
                                                      accepted implementation.md
```

- **Installed workflow surfaces** carry automatic recording and the explicit triage entry point.
- **The project log and reflection plans** are shared across agent projections; platform-specific
  files do not create separate backlogs.
- **Investigators** are read-heavy and handle exactly one entry; **implementers** receive complete
  plans for one owning feature and write only in assigned worktrees.
- **Speckit Fast Loop** remains the eligibility and bounded-change authority. Feature 003 owns the
  generic installation mechanism; Feature 005 owns what reflection assets mean and how they behave.
- **Validation, merge, and acceptance** keep durable intent and maintainer decisions outside child
  agents' authority.

## Logic

1. A delivery phase meets a problem, records it in the project log, and continues or stops under its
   existing rules.
2. The maintainer invokes triage. `status` reports the ordered queue and plan lifecycle without
   mutation.
3. `investigate` dispatches bounded waves. Each investigator receives one entry, establishes root
   cause, and produces one plan routed to `fast-loop`, `specify`, `dismiss`, or `blocked`.
4. `implement` selects only ready fast-loop plans, rejects overlap with maintainer edits, groups
   plans by owning feature, creates one worktree and branch per group, and has implementers run
   Speckit Fast Loop, exact validation, and one commit per successful plan.
5. `merge` requires a clean checkout, merges branches serially, stops on conflict or validation
   failure, cleans only successful worktrees, and reports suggested reflection notes without
   applying them.
6. At acceptance, every open entry attributed to the feature stays cited in the accepted
   realization and the project log remains intact.

**Rules the implementation must keep**

- Automatic recording remains part of existing delivery phases and introduces no phase command,
  approval, or checkout dependency; triage is an explicit maintainer action (FR-001, FR-002,
  FR-006, FR-018).
- One project-wide maintained log carries the fixed entry vocabulary and survives every attempt;
  repeated problems update occurrences without reversing maintainer decisions (FR-003, FR-004,
  FR-005, FR-008, FR-014, FR-016).
- Recording never edits durable sources or reads another root's attempt, and phase reports,
  analysis, convergence, acceptance, and validation surface the entries within their existing
  authority (FR-007, FR-009, FR-010, FR-011, FR-012, FR-013, FR-015, FR-017).
- Investigation handles one entry per specialized agent and produces the complete plan contract in
  bounded waves with explicit failure reporting (FR-019, FR-020, FR-021).
- Implementation selects only ready fast-loop routes, protects maintainer edits, groups by owning
  feature, isolates each group in a worktree, validates, and commits one successful plan at a time
  (FR-022, FR-023, FR-027).
- Merge is serial, clean-checkout gated, deterministic, conflict-safe, and never changes reflection
  status or notes (FR-024).
- Installation deterministically and idempotently projects one shared queue, plan lifecycle, skill,
  roles, helper, and configuration into every supported subagent platform (FR-025, FR-026).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): six user
  stories, FR-001 to FR-027, and SC-001 to SC-014.
- **The accepted recording realization and the baseline for this new attempt** —
  [implementation.md](implementation.md).
- **The log's grammar** — `contracts/reflection-log.md` and
  `contracts/examples/reflections.md`; the boundary promise is
  [contract.concorde.workflow](../../architecture/contracts/concorde-workflow/contract.md), and the
  host lifecycle is
  [contract.concorde.spec-kit-platform](../../architecture/contracts/spec-kit-platform/contract.md).
- **The project log** — `specs/concorde/reflections.md`.
- **The level this feature belongs to** — [module.md](../../module.md) and its
  [design reference](../../design.md).
- **Related feature authorities** — [Concorde Workflow](../001-concorde-workflow/abstract.md),
  [Install Concorde for Spec Kit](../003-install-concorde-speckit/abstract.md), and
  [Self-Host Concorde](../004-self-host-concorde/abstract.md).
