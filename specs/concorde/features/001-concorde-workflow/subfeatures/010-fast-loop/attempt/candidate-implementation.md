# Feature Implementation: Fast Loop

**Feature**: `feature.concorde.workflow.fast-loop`

**Realization status**: Accepted realization of the relaxed direct small-change workflow, revised
2026-08-30 for bounded multi-feature and inter-module contract/format reconciliation.

**Selected level**: Immediate sub-feature of `feature.concorde.workflow`; the parent durable trio
remains aggregate authority and is not restated here.

## Realization Overview

Concorde ships `speckit.fast-loop` as an additive tenth command in the `concorde` preset, beside nine
normal Spec Kit phase modifications and five Concorde extension surfaces. The coding agent follows
the command Markdown directly; no new mutation runtime or launcher verb exists. Its first action
invokes the installed project-relative workspace adapter with `--phase fast-loop`. Protocol v8
resolves the standard selected root, which fast-loop treats as an anchor rather than proof of
single-feature ownership.

The agent discovers the complete affected feature set from bounded module summaries, contracts,
code, tests, accepted implementation references, and maintained/user documentation. It then invokes
the same adapter with `--feature-directory <affected-root> --phase fast-loop` for every affected
existing feature. Each receipt remains single-root path authority, and `.specify/feature.json`
remains the one standard selection pointer.

Eligibility requires a non-placeholder accepted `implementation.md` and absent `attempt/` for every
affected feature, a safely separable worktree, and a materially clear bounded outcome. The loop may
reconcile cross-feature behavior plus related inter-module contract/data-format, maintained-diagram,
module-reference, and user-guide sources. It rejects feature/module creation or restructuring,
changed module responsibility or dependency direction, and changes to project-level compatibility or
migration promises made to users of the whole project. No plan, task list, implementation phase,
convergence pass, or acceptance proposal is hidden inside an actual fast-loop invocation.

## Module and Feature Collaboration

- `module.concorde.skills` owns `presets/concorde/commands/speckit.fast-loop.md`, eligibility and
  direct-authoring guidance, hooks, reflection rules, architecture-review state, and completion
  reporting. Codex, Claude, and slash-command materializations preserve the same intent.
- `module.concorde.scripts` supplies only canonical workspace facts. `feature_workspace.py` keeps
  `fast-loop` root-scoped, and `workspace.py` already accepts one explicit `--feature-directory` per
  call. Repeated calls validate affected roots without a protocol or schema change; semantic impact
  discovery remains with the coding agent.
- `module.concorde.workspace-files` supplies Protocol v8 durable trio paths, providing-module and
  parent/sibling bounds, attempt state, and project reflection path for each resolved root. Normal
  phases remain single-selected-root operations.
- `module.concorde.distribution` packages ten preset commands and materializes the additive surface.
  The nine normal modifications may reveal lower-layer winners on removal; fast-loop has no fictional
  lower winner.
- `module.concorde.auto-docs` publishes child/parent workflow authorities and the project workflow
  contracts/views as generated read models while excluding `attempt/`.

The external procedure is `contracts/fast-loop-command.md` under
`contract.concorde.workflow`. Parent `contracts/architecture-sources.md` and
`contracts/agent-commands.md` define durable-write and distribution obligations; the project
`architecture/contracts/concorde-workflow/contract.md` defines single-root lookup plus the bounded
fast-loop exception. The implementation changes no module responsibility, dependency direction,
Protocol v8 payload, runtime operation, or project compatibility policy.

## Scenario Realization

### Discover and reconcile a bounded affected set

The `direct-authoring` scenario begins with a concrete maintainer request and one selected anchor.
The agent records the pre-existing worktree plus anchor durable-document hashes, discovers affected
roots from directly relevant evidence, resolves each root canonically, and records every affected
durable trio/hash and attempt state. A placeholder realization or active attempt in any affected root
returns that root to the normal lifecycle before mutation.

After all gates pass, proportional tests and implementation change in the same bounded loop. Every
affected `design.md` and `abstract.md` changes only when that feature's required behavior changes;
every affected `implementation.md` records its verified realization delta. Related contract,
diagram, module-reference, and user-guide sources change only when required for truthfulness.
Unrelated feature, architecture, integration, and worktree sources remain untouched.

### Distinguish architecture detail from module boundaries

An inter-module format, schema, example, or maintained view is not independently disqualifying.
Fast-loop may author the complete coordinated change when module responsibilities and dependency
direction remain stable. If an internal contract is also the project's public user interface, its
compatibility/migration promise is project-level and returns to the full workflow.

AI-authored contract, maintained-diagram, or other architecture-authority edits are validated first,
then reported as `review_pending` with exact paths, hashes, and diff. The command cannot claim final
success until the maintainer confirms that unchanged validated diff, at which point it reports
`reviewed`; a run without architecture changes reports `not_required`. This review creates no
attempt or implementation-acceptance artifact.

### Escalation, hooks, and failure reporting

New or restructured features/modules, changed module responsibilities/dependencies, project-level
user compatibility/migration policy changes, ambiguous scope, unsafe overlapping ownership,
unavailable required evidence, failing mandatory hooks, and unrepaired test/validation failures
prevent success. Expected ineligibility makes zero fast-loop edits and is not itself a reflection.
The report identifies the failed gate and earliest normal stage. Genuine workflow/tooling problems
are recorded in the project reflection log.

## Durable Implementation Decisions

- Fast-loop remains an additive preset command, not a normal Spec Kit phase and not a deterministic
  runtime operation.
- `.specify/feature.json` remains a single canonical pointer. Fast-loop treats it as an anchor and
  independently resolves each affected existing root through unchanged Protocol v8.
- Semantic impact discovery belongs to the coding agent; a deterministic path-only impact engine and
  an all-project feature payload were rejected as unreliable or unbounded.
- Every affected feature requires a non-placeholder accepted implementation and no active attempt.
  Fast-loop cannot create a first accepted milestone.
- Smallness is determined by bounded affected-authority completeness and architectural risk, not by
  changed-line count or number of feature roots.
- Significant architecture means changed module responsibility or dependency direction. Related
  contract/format, maintained-view, and module-reference detail may be reconciled directly but
  requires exact maintainer review under constitution A.V (R-041).
- Compatibility and migration gating applies only to durable project-level promises made to users of
  the whole project; feature/module sources do not invent separate policy.
- Behavioral documents remain byte-identical for unaffected or realization-only features; every
  changed authority is validated in proportion to its role.
- Completion reports the anchor, complete affected set, per-feature document impact, changed files,
  checks, architecture review state, preserved unrelated work, and explicit no-attempt/no-acceptance
  confirmation.
- Installed-surface generation continues through self-hosting. A dual active-integration refresh
  currently needs a generated Codex backup/restore to survive the second Claude apply (R-042); this
  does not change the canonical command or either final projection.

## Traceability and Evidence

Required behavior and acceptance scenarios are in `design.md`; the external procedure is
`contracts/fast-loop-command.md`; aggregate behavior is in the parent `design.md`; project/module
authority is in `specs/concorde/design.md`, the workflow contracts, and the two maintained workflow
views.

The maintained realization centers on `presets/concorde/commands/speckit.fast-loop.md`, installed
`.agents`/`.claude` and `.specify/presets` projections, existing
`extensions/concorde/scripts/python/workspace.py` and `feature_workspace.py`, plus command/workspace/
installed/self-host tests. Public guidance is reconciled in `README.md`, `docs/commands.md`,
`docs/concorde-workflow.md`, and `docs/quick-start.md`.

Executable evidence on 2026-08-30:

- 21 focused command, workspace, installed Codex/Gemini, and self-hosted Codex/Claude tests passed;
- the full Concorde Python suite passed 281 tests in 162.472 seconds;
- repeated explicit-root resolution leaves standard selection unchanged;
- release build and verification produced matching bundle, extension, and preset digests;
- deterministic Concorde validation returned `success` with zero findings/errors/warnings/infos;
- both workflow views passed 9/9 Archify showcase validation/delivery with zero composition errors or
  warnings; the parent verified 16 repository references;
- the docsite passed TypeScript, 19 files / 81 tests, 108-page validation with zero errors, and
  optimized production build; and
- active Claude self-host status is `current` with source/installed/registry/surfaces matching, while
  both Codex and Claude projections contain the relaxed policy.

## Known Limitations

- Browser containment and light/dark perceptual review remains pending because Chrome/Chromium is
  unavailable; deterministic delivery is not visual inspection (R-026).
- The tasks template's literal selected-child path wording still conflicts with realizing source,
  test, and coordinated authority paths outside the child root (R-027).
- Generated task paths are not checked automatically against repository files (R-028).
- Installed receipt parsing still derives accepted phase-token shape from a regex rather than the
  runtime vocabulary (R-029).
- Additive fast-loop recomposition remains a special ownership case without a lower winner (R-030).
- Ad hoc full-suite discovery can shadow the runtime package unless the discovery root is chosen
  correctly (R-031).
- Release capability counts remain duplicated literals instead of manifest-derived values (R-032).
- Specification validation does not yet catch invented level-view scenario identifiers early
  (R-033).
- Architecture-source fast loops now require a two-turn exact review; future guidance should keep
  that timing explicit whenever direct architecture authoring is widened (R-041).
- Switching active integration twice during self-host refresh can delete inactive generated
  Concorde surfaces; the final dual projection currently requires backup/restore (R-042).
- The generic skill-creator validator rejects Spec Kit/Claude-owned front-matter keys, so Concorde's
  repository-native manifest/surface/release gates remain authoritative (R-043).
