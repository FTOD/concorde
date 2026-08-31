# Feature Implementation: Record and Triage Workflow Reflections

**Realization status**: Accepted realization, revised 2026-08-31 so reflection entries are maintained
docs/specs with controlled rewrite support and stable valid identities.

**Selected level**: Top-level feature of `module.concorde`; it has no parent feature.

## Realization Overview

The accepted project-wide reflection log remains the durable source for problems encountered during
planning, task generation, implementation, analysis, convergence, and fast-loop work. This milestone
closes the improvement loop by adding an explicit `reflections-triage` skill, specialized
investigator and implementer roles, a deterministic queue/plan helper, shared project state, and
Claude/Codex-native projections installed from the Concorde extension.

Ordinary phase recording remains append/update-only. Separately, an explicitly requested rename or
documentation correction may rewrite existing reflection text and references like other maintained
docs/specs while preserving every exact unique `R-NNN` identifier, required structure, maintainer
decision, occurrence identity, and problem meaning. Deterministic validation checks the complete
result read-only.

Canonical behavior lives once under `extensions/concorde/agent-assets/reflections/`. Thin wrappers
render one triage skill and two roles for each supported platform. Investigators are read-only and
return a complete plan to the parent; implementers receive complete plans and an assigned Git
worktree. The parent alone persists plan state, authorizes merge, and suggests—but never applies—
reflection status or note changes.

Feature 003 packages these assets in `extension:concorde@0.5.0`. The one-command installer previews
the component and agent plan, installs or updates the Spec Kit bundle, invokes only the projector
from the installed extension, verifies path/digest ownership, and reports success afterwards.
Self-hosting uses the same projector and preserves inactive integrations and maintainer state.

## Module and Feature Collaboration

| Part | Contribution |
|---|---|
| Skills | Existing phase instructions record problems automatically. The canonical triage orchestrator defines `status`, `investigate`, `implement`, and `merge`; Claude and Codex wrappers expose it natively. |
| Scripts | `concorde.reflections` remains the log parser. `scripts/python/reflections_queue.py` deterministically orders entries, resolves ownership, validates plan metadata, and performs bounded plan-state updates. `concorde.agent_assets` renders/reconciles projections and receipts. |
| Workspace Files | `reflections.md` remains project-wide durable memory. `.concorde/reflections/config.json` is shared maintainer configuration; nested `.gitignore` keeps plans/worktrees temporal; `.specify/concorde-agent-assets.json` owns generated path digests only. |
| Distribution | Feature 003 releases the canonical assets and helper, installs native Claude/Codex projections after the bundle lifecycle, verifies them, and preserves modified, unrelated, inactive, and shared state. |

`contract.concorde.workflow` governs phase and triage writes; `contract.concorde.spec-kit-platform`
governs host phases and command materialization; `contracts/reflection-log.md` remains Reflection Log
v1; `contracts/reflection-triage.md` governs actions, roles, plans, concurrency, worktrees, merge, and
projection ownership. Speckit Fast Loop remains the eligibility and bounded-change authority.

No module responsibility, boundary, dependency direction, level view, or module contract changed.

## Scenario Realization

### Record during delivery (US1 and US2)

The accepted shared Reflection Recording block remains byte-identical across plan, tasks,
implement, analyze, and converge guidance. Workspace Protocol v8 returns the project log path and
open count. The parser, validator, context operation, and acceptance citation gate continue to use
one grammar and one project-level file. Existing parser, workspace, context, validation, composition,
and implementation-acceptance tests all remain green.

### Reconcile maintained reflection documentation (US4)

An explicit rename or documentation correction may include `workspace.reflections` in its bounded
maintained-source set. The agent applies only the requested mapping, keeps every `R-NNN` identifier
unchanged and unique, preserves required fields, maintainer-owned decisions, occurrence identity, and
problem meaning, updates renamed `Feature`/`Concerns` references so they resolve, and requires the
complete log to pass deterministic validation. Explicit maintainer cleanup may remove closed entries;
surviving IDs remain unchanged and removed IDs are never reused.

### Investigate and route (US3)

The installed triage skill calls `.specify/extensions/concorde/scripts/python/reflections_queue.py`.
`status` is byte-preserving. `investigate` assigns one entry per read-only child in bounded waves.
The child returns a plan with exactly one route—`fast-loop`, `specify`, `dismiss`, or `blocked`—and
complete problem, change, validation, ownership, file, effort, and risk sections. The parent validates
and serializes plans under `.concorde/reflections/plans/`, preventing concurrent identifier races.

### Implement and merge (US3)

Ready fast-loop plans are grouped by `implement_in`. The parent checks maintainer changes, creates
one Git worktree and branch per group, and supplies full plan text because plans are intentionally
ignored and absent from worktree checkouts. Implementers verify the assigned Git root, invoke
Speckit Fast Loop, run plan and repository validation, revert only a failed plan, and commit each
success separately. Merge requires a clean checkout, proceeds branch-by-branch, aborts on conflict,
reruns applicable validation, and cleans only merged worktrees. Reflection status and note remain
maintainer-owned.

### Install supported projections (US3)

`agent_assets.py` renders three outputs per integration from canonical bodies:

- Claude: `.claude/skills/reflections-triage/SKILL.md` and two `.claude/agents/*.md` roles.
- Codex: `.agents/skills/reflections-triage/SKILL.md` and two `.codex/agents/*.toml` roles.

The Codex TOML uses the official project custom-agent schema (`name`, `description`, and
`developer_instructions`) with read-only/workspace-write sandbox defaults and no mandatory model.
Claude retains native background/worktree metadata where available. The portable contract is an
explicit Git worktree; live parent permissions continue to bound children.

Projection preview classifies every path without mutation. Sync creates, adopts byte-identical,
updates matching-owned, or removes matching-superseded outputs; modified/unowned files are preserved
as conflicts. Verify compares desired, materialized, and receipt digests. Config, plans, worktrees,
logs, unrelated skills, permission settings, and inactive integration receipts are never projection-owned.

### Review, acceptance, and validation (US4–US6)

Maintainers may still edit log status/note directly. Acceptance continues to present attributed
entries and refuse an uncited open entry. Deterministic validation still checks Reflection Log v1
without rewriting it. The updated core diagram shows automatic recording, explicit triage, isolated
implementation, validation/merge, and installed projections while leaving behavior authoritative in
the feature prose and contracts.

## Durable Implementation Decisions

- **One canonical protocol, generated platform wrappers**: full duplicate Claude/Codex workflows
  were rejected because their route, path, and permission semantics would drift.
- **Parent-only plan persistence**: this makes the investigator truly read-only on Codex and removes
  concurrent plan-write races on every platform.
- **Explicit Git worktrees as the portable isolation contract**: Claude may add native isolation;
  Codex project agents receive an exact worktree and verify their Git root.
- **Shared state under `.concorde/reflections/`**: agent platforms consume one queue and plan
  lifecycle instead of maintaining platform-specific backlogs.
- **Digest receipt owns only generated files**: update/removal cannot overwrite customized roles or
  delete maintainer state merely because a filename matches.
- **Installed extension is the projection source**: the installer and self-host flow cannot fall
  back to checkout-local agent files.
- **Deterministic structural evidence rather than live models**: Markdown frontmatter, TOML, shared
  semantics, paths, state transitions, ownership, and installation are release gates; live agent
  execution remains experiential evidence.
- **Specification and storage corrections retained**: the project-wide log and end-state alignment
  decisions from R-003 and R-004 remain the basis of this realization.
- **Maintained-document reconciliation**: reflection history is project documentation rather than an
  immutable event store. Ordinary recording stays append/update-only, while explicit rewrite scope
  permits rename/documentation reconciliation with stable IDs and deterministic structural/reference
  validation.

## Traceability and Evidence

Primary implementation sources:

- `extensions/concorde/agent-assets/reflections/**`
- `extensions/concorde/runtime/concorde/agent_assets.py`
- `extensions/concorde/scripts/python/reflections_queue.py`
- `scripts/install-concorde.py`
- `scripts/development/self-host-concorde.py`
- `scripts/release/build-components.py`

Feature 005 evidence includes `test_reflections_queue.py`, `test_agent_assets.py`,
`test_reflection_triage_distribution.py`, the retained reflection parser/rules/context/acceptance
suites, and installed-workspace composition. Feature 003 evidence covers manifests, deterministic
archives, one-command fresh/preview/update/conflict/remove behavior, installed command surfaces,
Codex skills, and Claude/Codex self-hosting.

Final evidence on 2026-08-30:

- 294 Concorde Python tests passed; the final focused post-adjustment regression passed 16 tests.
- Concorde validation returned zero findings with source digest
  `sha256:8c0842bd38da77720f3e6cb2b0ce130e984f170010f404a6b79260ec2a06ae4f`.
- The 0.5.0 release rebuilt and verified byte-equivalently: bundle
  `sha256:9a81094801d52fd1c2511400b4ec3b2854a9fde69b6a724583476641c5d243c9`,
  extension `sha256:900044f0d275caa38c8a4bae18a1a85666e0e4aee6356b774004f80c8ea4c307`,
  preset `sha256:997050c07587028f0e5e45fd7eb3fb249bda58f96cb81c5a9f0de54fe5c04fe4`.
- Docsite gates passed: 19 test files, 81 tests, 108 validated pages, zero errors, and successful
  production promotion.
- The Feature 005 core diagram passed 9/9 showcase checks with no errors or warnings; delivered
  source digest `6170494d039be8f8633c124506beb0af17e7adf4b18602d70c0480055dc0abc4`.

The 2026-08-31 maintained-rewrite reconciliation passed 32 focused reflection parser/validation,
installed phase-composition, command-contract, triage-projection, and manifest tests. The full
Concorde suite passed 308 tests; deterministic validation returned zero findings. The full docsite
gate passed TypeScript, 19 test files / 83 tests, 108-page validation, and production promotion.

## Known Limitations

- **R-001**: the historical Claude self-host refresh limitation remains open in the maintainer log;
  the new projector is implemented and tested, but the entry's final disposition is maintainer-owned.
- **R-002**: plan/tasks guidance still contains the recorded module-edit authority disagreement.
- **R-005**: the root level view intentionally remains module-oriented and does not draw every
  Feature 005-specific crossing; the feature core view carries the explanatory detail.
- **R-007**: the docsite still rejects canonical links to non-published reflection artifacts; the
  abstract uses code spans for those paths.
- **R-044**: native Spec Kit 0.16.4 lacks arbitrary custom-agent projection. Feature 003's installed
  bounded projector is implemented, but the reflection remains open until maintainer disposition.
- **R-045**: the sandboxed docsite runner could not bind its local IPC socket; the exact approved
  rerun passed and no test was weakened.
- Browser-based containment and light/dark perceptual review remains pending because Chrome/Chromium
  was unavailable; deterministic showcase checks are not claimed as visual review.

## Implementation Detail

### Queue and plan validation

The queue helper imports the canonical Reflection Log v1 parser, derives the specification root from
`.concorde/config.json`, maps stable feature/contract IDs, validates shared config and safe relative
paths, excludes closed/skipped/planned entries correctly, and permits only named plan fields and
legal status transitions. Read actions are byte-preserving and repeatable.

### Projection and ownership

The canonical projection manifest maps one body and wrapper to each native target. Rendering rejects
unsafe paths, symlinks, missing sources, duplicate targets, unresolved body tokens, and TOML triple
quote conflicts. Receipts keep independent integration records so refreshing one platform preserves
the other. A nested `.concorde/reflections/.gitignore` keeps `plans/` and `worktrees/` temporal without
editing a project's root ignore policy.

### Installer transaction

Preview installs the candidate bundle only in a disposable project and invokes that copy's projector
against the real target. Apply installs/updates components first, then runs projector preview, sync,
and verify. Projection conflict or failure returns exit class 4 with residual component/projection
state and no terminal success. Development cleanup still completes before success output.
