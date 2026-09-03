# Validation: Create Unified Project Docsite

## Protected baseline (plan start, 2026-09-03)

| Authority | SHA-256 |
|---|---|
| `specs/concorde/features/002-auto-docsite.md` | ceaad0b3e8f8fe01ffc06883ba0070d539a8f3b73acd868b248601d7727808c5 |
| `specs/concorde/architecture.md` | b60261b143ff0a0f2e9e9a02f3dc79bc67eec964f5a8e207958289e03cb75171 |
| Canonical related-feature summaries (Protocol 13 JSON) | a878e03b4436c4f454c4c1bc01e576b966eb26b9b608cd14bf77ba46b0b2e10c |
| Module ancestry | none (root module) |

Planning wrote only this attempt directory and one reflection entry. Durable sources above are
expected to change only through T018 and T022.

## Attempt Evidence

- **T001 · Protected baseline**
  - **Trace**: Plan:Risk Controls
  - **Check**: SHA-256 of the feature file, root architecture, and related-feature summaries recorded above.
  - **Outcome**: passed
  - **Evidence**: this file
  - **Scope**: baseline only
- **T002 · Seed identity and workflow template**
  - **Trace**: FR-008
  - **Check**: `docsite/site.json` and `docsite/scaffold/deploy-docsite.yml` created; `tests/repository/github-pages.test.ts` proves Concorde identity values and workflow byte-equality.
  - **Outcome**: passed
  - **Evidence**: `docsite/tests/repository/github-pages.test.ts`
  - **Scope**: Concorde identity only
- **T003 · Template inventory tests**
  - **Trace**: FR-006, NFR-001
  - **Check**: `.venv/bin/python -m unittest tests.concorde.unit.test_docsite_template` (15 tests, including symlinked excluded directories).
  - **Outcome**: passed
  - **Evidence**: `tests/concorde/unit/test_docsite_template.py`
  - **Scope**: synthetic package plus this checkout
- **T004 · Template inventory module**
  - **Trace**: FR-006
  - **Check**: Same run; installer, release builder, verifier, and scaffold import the one rule.
  - **Outcome**: passed
  - **Evidence**: `src/concorde/docsite_template.py`
  - **Scope**: —
- **T005 · Site identity tests**
  - **Trace**: FR-008
  - **Check**: `npx vitest run tests/unit/site-identity.test.ts` (schema 1 rules and diagnostics).
  - **Outcome**: passed
  - **Evidence**: `docsite/tests/unit/site-identity.test.ts`
  - **Scope**: —
- **T006 · Identity-driven adapter**
  - **Trace**: FR-008, FR-009
  - **Check**: `npm run typecheck`; docsite unit tests; fresh-project test proves optional docs/features collections and repository link handling.
  - **Outcome**: passed
  - **Evidence**: `docsite/docusaurus.config.ts`, `docsite/plugins/concorde-content/site-identity.ts`
  - **Scope**: —
- **T007 · Foundational checks**
  - **Trace**: plan gate
  - **Check**: Focused Python run (7 modules, 72 tests) and docsite unit run (7 files, 35 tests).
  - **Outcome**: passed
  - **Evidence**: this file
  - **Scope**: mixed working tree; superseded by T011/T024 isolated runs
- **T008 · Packaging tests**
  - **Trace**: FR-006
  - **Check**: `test_install_concorde`, `test_release_artifacts`, `test_capability_validation`, `test_installation_lifecycle`, `test_skill_update` pass.
  - **Outcome**: passed
  - **Evidence**: `tests/concorde/unit/test_install_concorde.py`, `tests/concorde/contract/test_release_artifacts.py`
  - **Scope**: —
- **T009 · Package the template**
  - **Trace**: FR-006
  - **Check**: Same tests; `build-release.py` then `verify-release.py` in the isolated detached worktree of this change (no unrelated working-tree edits) (offline isolated install, byte-equivalent rebuild).
  - **Outcome**: passed
  - **Evidence**: `concorde.json`, `scripts/install-concorde.py`, `scripts/release/`
  - **Scope**: —
- **T010 · Repository evidence split**
  - **Trace**: FR-006, FR-009
  - **Check**: Concorde-specific tests live under `docsite/tests/repository/`; `.github/workflows/deploy-docsite.yml` equals the template; `npm run check` in the isolated detached worktree of this change (no unrelated working-tree edits): 22 files / 90 tests.
  - **Outcome**: passed
  - **Evidence**: `docsite/tests/repository/`
  - **Scope**: —
- **T011 · Story 1 evidence**
  - **Trace**: FR-006
  - **Check**: In the isolated detached worktree of this change (no unrelated working-tree edits): `.venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'` → 416 tests OK; `npm run check` → 90 tests, 45 pages validated, verified site promoted.
  - **Outcome**: passed
  - **Evidence**: this file
  - **Scope**: the shared working tree also holds an unrelated in-flight reflections migration, so only the isolated run is authoritative
- **T012 · Scaffold Tool tests**
  - **Trace**: FR-007, FR-010, NFR-001, NFR-002
  - **Check**: `.venv/bin/python -m unittest tests.concorde.integration.test_docsite_scaffold` (19 tests: unconfigured, determinism, identity defaults, GitHub derivation, README-when-absent, workflow, conflicts, exact apply, stale, prerequisites, CLI).
  - **Outcome**: passed
  - **Evidence**: `tests/concorde/integration/test_docsite_scaffold.py`
  - **Scope**: —
- **T013 · Scaffold Tool and CLI**
  - **Trace**: FR-007, FR-010
  - **Check**: Same run, including `concorde.py docsite --propose/--apply` round trips.
  - **Outcome**: passed
  - **Evidence**: `src/concorde/docsite_scaffold.py`, `src/concorde/cli.py`
  - **Scope**: —
- **T014 · Story 2 evidence**
  - **Trace**: FR-007
  - **Check**: Focused run above; full suite in T011.
  - **Outcome**: passed
  - **Evidence**: this file
  - **Scope**: —
- **T015 · concorde-init offers the step**
  - **Trace**: interface.concorde.scaffold-docsite
  - **Check**: Docsite section added; `sync-agent-surfaces.py apply` refreshed both projections; `status` → current in the isolated detached worktree of this change (no unrelated working-tree edits).
  - **Outcome**: passed
  - **Evidence**: `skills/concorde-init/SKILL.md`, `.claude/skills/concorde-init/SKILL.md`, `.agents/skills/concorde-init/SKILL.md`
  - **Scope**: —
- **T016 · Fresh-project test**
  - **Trace**: FR-009
  - **Check**: `docsite/tests/repository/fresh-project-scaffold.test.ts` runs init → docsite propose/apply → validate → build in a temp project holding only Initialization Proposal 3 outputs.
  - **Outcome**: passed
  - **Evidence**: `docsite/tests/repository/fresh-project-scaffold.test.ts`
  - **Scope**: reuses this checkout's `node_modules` and pinned Archify
- **T017 · Story 3 evidence**
  - **Trace**: FR-009
  - **Check**: `npx vitest run tests/repository/fresh-project-scaffold.test.ts` → 3 tests passed (21.6 s); also passed inside the isolated `npm run check`.
  - **Outcome**: passed
  - **Evidence**: this file
  - **Scope**: —
- **T018 · Root architecture and overview**
  - **Trace**: Architecture Zoom
  - **Check**: `archify validate architecture specs/concorde/diagrams/system-overview.json --quality showcase` → ok, composition pass, 9 checks; `npm run render-diagrams` delivered 7 views.
  - **Outcome**: passed
  - **Evidence**: `generated/architecture/concorde-system-overview.html`
  - **Scope**: visual inspection not performed (no browser)
- **T019 · Runtime reconciliation**
  - **Trace**: contract.runtime.tools
  - **Check**: `concorde.py validate` → success, 0 errors in the isolated detached worktree of this change (no unrelated working-tree edits); runtime overview unchanged (no principal collaborator added).
  - **Outcome**: passed
  - **Evidence**: `specs/concorde/modules/runtime/`
  - **Scope**: —
- **T020 · Distribution reconciliation**
  - **Trace**: contract.distribution.standalone-package
  - **Check**: Same validation; release verify proves the packaged `concorde/docsite/` inventory.
  - **Outcome**: passed
  - **Evidence**: `specs/concorde/modules/distribution/`
  - **Scope**: —
- **T021 · Auto-docs reconciliation**
  - **Trace**: contract.auto-docs.build-interface
  - **Check**: Same validation; docsite check publishes both module pages.
  - **Outcome**: passed
  - **Evidence**: `specs/concorde/modules/auto-docs/`
  - **Scope**: —
- **T022 · Feature reconciliation**
  - **Trace**: FR-006, FR-007, FR-008, FR-009, FR-010
  - **Check**: Outputs, compatibility, edge cases, and `evidence_status: verified` reconciled; validation success.
  - **Outcome**: passed
  - **Evidence**: `specs/concorde/features/002-auto-docsite.md`
  - **Scope**: —
- **T023 · Public docs**
  - **Trace**: interface.concorde.scaffold-docsite
  - **Check**: Quick start, skills, workflow, project structure, framework overview, contributing docsite, both READMEs updated; published as part of the 45 validated pages.
  - **Outcome**: passed
  - **Evidence**: `docs/`, `README.md`, `docsite/README.md`
  - **Scope**: —
- **T024 · Cross-cutting validation**
  - **Trace**: SC
  - **Check**: In the isolated detached worktree of this change (no unrelated working-tree edits): `concorde.py validate` success; full Python suite 416 OK; `npm run check` 90/90; `sync-agent-surfaces.py status` current; release build + verify OK; final protected digests recorded below.
  - **Outcome**: passed
  - **Evidence**: this file
  - **Scope**: diagram visual inspection not performed

## Final protected digests (implementation complete)

| Authority | SHA-256 | Change authorized by |
|---|---|---|
| `specs/concorde/features/002-auto-docsite.md` | 347b405dabe189c4ee7649f7500e70ef9b07cfcfe72cda640ddd3797da5f078e | T022 |
| `specs/concorde/architecture.md` | 4b695e4f954f379da64a013e30313a589d69e3640a430875d39364167861bfcd | T018 |
| Canonical related-feature summaries | unchanged (a878e03b…e10c) | — |

Delivery remove path: `.concorde/attempts/feature.concorde.publish-project-docsite` (exactly this attempt).
Limitations: the root system overview passed Archify showcase validation but was not visually inspected;
the reflection entry recorded during planning lives in the project reflection log outside this attempt.
