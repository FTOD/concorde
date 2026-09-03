# Implementation Plan: Create Unified Project Docsite

**Branch**: `docsite/navigation-cleanup` | **Date**: 2026-09-03 | **Feature**: [specs/concorde/features/002-auto-docsite.md](../../../specs/concorde/features/002-auto-docsite.md)

**Input**: The selected direct feature file, `specs/concorde/architecture.md`, current source code,
executable tests/checks, Constitution, bounded related-feature summaries, the admitted
`feature.auto-docs.publish-project-docsite` and `feature.distribution.package-concorde` bodies
(owners of the required `contract.auto-docs.architecture-site` and
`contract.distribution.native-installation`), and the reflection log.

## Summary

Ship the `docsite/` adapter as a packaged template, add a `docsite` propose/apply Tool that
scaffolds it into any initialized project with a project-owned `docsite/site.json`, make the adapter
read its identity from that file, offer the step from `concorde-init`, and reconcile package,
architecture, feature, docs, and projection authorities. Today no template exists, the package roots
exclude `docsite/`, and `docusaurus.config.ts` hardcodes Concorde's identity.

## Technical Context

**Language/Version**: Python 3.11+ (runtime Tools, packaging); TypeScript on Node.js 20 (adapter).

**Primary Dependencies**: standard library only for Tools; Docusaurus 3.10.2, vitest 4, pinned Archify skill for the adapter.

**Storage/State**: `concorde.json` package inventory; `docsite/site.json` per project; `.concorde/docsite-proposal.json` saved by the maintainer.

**Testing**: `.venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'`; `npm run check` in `docsite/`; `python3 scripts/concorde.py --project-root . validate`.

**Target Platform**: Source checkout, extracted release archive, and `.concorde/framework/` installation on POSIX/Windows.

**Project Type**: CLI Tool plus static-site adapter.

**Performance Goals**: Scaffold proposal under one second offline; package copy adds about 1 MB (dominated by `package-lock.json`).

**Constraints**: Preview by default; digest-bound apply; never overwrite; no network; adapter bytes identical across projects; repository-specific evidence outside the template.

**Scale/Scope**: Modules concorde, runtime, distribution, auto-docs; features 002 (selected), runtime 001, distribution 001, auto-docs 001; about 12 source/script files, 6 test files, 8 docs.

## Constitution Check

| Principle | Plan evidence | Status |
|---|---|---|
| A.I Fast comprehension at every module | New entities land in their owning modules (runtime Tool, auto-docs identity/template, distribution inventory) with one-line definitions; feature 002 stays the single entry point for the capability. | Pass |
| A.II Complete architecture, real implementation | Specs inventory the new Tool, identity file, template root, and relationships; algorithms stay in code; tests are the evidence. | Pass |
| B.I Concorde ships a usable workflow | The template travels in the same package, installer, and archive as every other asset. | Pass |
| B.II Concorde develops itself with Concorde | Concorde's own `docsite/` is the template instance; its identity moves to `docsite/site.json`; its workflow equals the template. | Pass |

## Concorde Architecture Gate

1. Interfaces and zoom entities resolve: `interface.concorde.scaffold-docsite`, `interface.concorde.publish-docsite`, `module.concorde.auto-docs`, `module.concorde.distribution`, `entity.concorde.package-manifest`, `entity.concorde.cli`, `entity.concorde.runtime`, `entity.concorde.specification`, `entity.concorde.archify`.
2. Affected authorities:
   - `specs/concorde/architecture.md`: `entity.concorde.cli` and `entity.concorde.package-manifest` definitions; new relationship `entity.concorde.package-manifest declares module.concorde.auto-docs`; new `interaction.concorde.scaffold-docsite`. System overview gains connection `distribution -> autodocs` ("packages template"); re-validated through Archify showcase (`npm run render-diagrams`).
   - `specs/concorde/modules/runtime/architecture.md`: entities `entity.runtime.docsite-scaffold` and `entity.runtime.docsite-template`; relationships from `entity.runtime.cli`. Runtime overview unchanged: the CLI node already depicts Tool dispatch and no principal collaborator is added.
   - `specs/concorde/modules/runtime/features/001-run-lifecycle-tools.md`: Tools list and proposal terminology.
   - `specs/concorde/modules/distribution/architecture.md`: `entity.distribution.framework-projection`, `entity.distribution.archive` definitions and installer relationship text. Distribution overview unchanged: no new entity.
   - `specs/concorde/modules/distribution/features/001-package-concorde.md`: entry points, obligations, example.
   - `specs/concorde/modules/auto-docs/architecture.md`: entities `entity.auto-docs.site-identity` and `entity.auto-docs.pages-workflow-template`; relationship `entity.auto-docs.publisher reads_from entity.auto-docs.site-identity`; decisions. Auto-docs overview unchanged: identity is configuration input, not a principal collaborator.
   - `specs/concorde/modules/auto-docs/features/001-publish-project-docsite.md`: build-interface inputs/compatibility.
   - `specs/concorde/features/002-auto-docsite.md`: outputs (README when absent), example, `evidence_status`.
   - Code: `src/concorde/docsite_template.py`, `src/concorde/docsite_scaffold.py`, `src/concorde/cli.py`, `scripts/install-concorde.py`, `scripts/release/build-release.py`, `scripts/release/verify-release.py`, `concorde.json`, `docsite/docusaurus.config.ts`, `docsite/plugins/concorde-content/site-identity.ts`, `docsite/site.json`, `docsite/scaffold/deploy-docsite.yml`, `.github/workflows/deploy-docsite.yml`.
   - Tests: `tests/concorde/unit/test_docsite_template.py`, `tests/concorde/integration/test_docsite_scaffold.py`, existing installer/release/capability tests, `docsite/tests/unit/site-identity.test.ts`, `docsite/tests/repository/*`.
   - Projections and docs: `skills/concorde-init/SKILL.md` plus `.claude`/`.agents` projections; `docs/quick-start.md`, `docs/skills.md`, `docs/concorde-workflow.md`, `docs/project-structure.md`, `docs/framework-overview.md`, `docs/contributing/docsite.md`, `README.md`, `docsite/README.md`.
3. Code comparison: no scaffold Tool, no template inventory, `PACKAGE_ROOTS` fixed to six roots in `concorde.json`/installer, allowlist prefixes in the release builder exclude `docsite/`, `docusaurus.config.ts` hardcodes title/url/baseUrl/org/project and the repository link, docs plugin registered unconditionally, `docsite/tests` mixes portable and Concorde-specific evidence.
4. Each authority above has an explicit task in `tasks.md`.
5. Executable identity/proposal examples live in tests (`tests/concorde/...`, `docsite/tests/...`), not in feature prose.
6. Diagrams: only the root overview changes (one connection); it keeps `meta.legend.mode: hidden`, `quality_profile: showcase`, and its unique normalized output; delivery via `npm run render-diagrams`; visual inspection is not available in this environment and is recorded truthfully.
7. The project reflection log records the minimal-project assumption.
8. No Operation changes.

## Source Structure

```text
src/concorde/docsite_template.py      # template inventory rule and digest
src/concorde/docsite_scaffold.py      # propose/apply Tool
src/concorde/cli.py                   # docsite subcommand
scripts/install-concorde.py           # docsite package root in framework copy
scripts/release/build-release.py      # docsite in archive
scripts/release/verify-release.py     # docsite members required
docsite/site.json                     # Concorde's own identity (project-owned pattern)
docsite/scaffold/deploy-docsite.yml   # GitHub Pages workflow template
docsite/plugins/concorde-content/site-identity.ts
docsite/tests/repository/             # Concorde-repository evidence, outside the template

tests/
├── concorde/unit/test_docsite_template.py
├── concorde/integration/test_docsite_scaffold.py
└── docsite/tests/unit/site-identity.test.ts, docsite/tests/repository/*.test.ts
```

**Structure Decision**: The inventory rule sits in the runtime package so the installer, release
scripts, and Tool share one definition; identity loading sits beside the content plugin because it
is adapter configuration, not content.

## Attempt Artifacts

```text
.concorde/attempts/feature.concorde.publish-project-docsite/
├── checklists/requirements.md
├── plan.md · research.md · data-model.md · quickstart.md · tasks.md · validation.md
```

## Research Decisions

See `research.md` (template location, inventory rule, identity file, minimal project, proposal
shape, prerequisites, deployment workflow).

## Implementation Phases

1. Seed identity/workflow template files; protected digests.
2. Template inventory module and site identity loader (test-first).
3. US1 package ships the template (manifest, installer, release, repository-test split).
4. US2 scaffold Tool and CLI (test-first).
5. US3 `concorde-init` offers the step; fresh-project end-to-end evidence.
6. Architecture/feature/docs/projection reconciliation; full validation; delivery readiness.

## Risk Controls

| Risk | Control | Verification |
|---|---|---|
| Installed framework or archive bloats with disposable docsite output | Inventory rule excludes disposable directories; verifier rejects `node_modules/`, `build/`, `site.json`, `tests/repository/` members | `test_release_artifacts`, `test_install_concorde` |
| Scaffolded adapter fails in a project with only init outputs | README added when absent; docs collection optional; end-to-end repository test builds a temp project | `docsite/tests/repository/fresh-project-scaffold.test.ts` |
| Stale package bytes after a proposal is saved | Apply recomputes template digests and rejects disagreement | `test_docsite_scaffold` stale case |
| Concorde's own site regresses | `docsite/site.json` reproduces current identity; `npm run check` and the repository tests | `npm run check` |
| Ambient or unioned agent authority | No Operation change; leaf prose only | `sync-agent-surfaces.py status` |

## Post-Design Constitution Re-check

Gates hold after design: one owning module per new fact, code as implementation authority, tests
as evidence, package parity across checkout/archive/install, and Concorde's own docsite as the
template instance.
