# Validation Record: Unified Project Docsite

**Validated**: 2026-08-24
**Environment**: Node.js 22.22.3, npm lockfile, Linux  
**Accepted design SHA-256**: `4997088cdfaa455393de68707fbbe6ea851ffcc5b7a1c5351e1669fc7dde31ee`
**Result**: Automated implementation and showcase-delivery gates pass. Current browser perceptual
review and the SC-006, SC-011, and SC-012 participant exercises remain manual checks because
Chromium and a participant pool were unavailable.

## Command Evidence

| Gate | Result | Evidence |
|---|---|---|
| Locked install | PASS | `npm ci` installed the lockfile successfully without maintained-source writes. |
| Inspect | PASS | 21 architecture sources, 8 project documents, and 8 permanent feature specification/design pairs discovered; 31 supporting Markdown files are reported as excluded. |
| Validate | PASS | 45 included real-repository pages and all declared architecture views validated with zero findings. |
| Type check | PASS | Strict `tsc --noEmit`. |
| Test suite | PASS | 15 files and 32 tests: architecture publication, framework-guide baseline, unit, contracts, fixtures, immutability, atomicity, accessibility, scale, and two production renders. |
| Framework guide contract | PASS | Three focused integration tests cover all eight maintained project documents, six landing-page journey links, stable Documentation routes, canonical Architecture/Features authority links, and temporal-artifact exclusion. |
| Concorde validation | PASS | Targeted validation of `feature.concorde.publish-project-docsite` completed with 0 errors, 0 warnings, and source digest `sha256:bdf25d4c318fdc77f2c6a60486ca7ab464d6e180bef08d8a0d2b710e09d7c936`. |
| Scale | PASS | 1,000 documents plus 250 specs discovered and validated in 0.613 seconds in the final measured gate. |
| Production build | PASS | Four-source-collection Docusaurus render through three navigation families, sandboxed view embedding, strict route verification, local-search generation, manifest v3 validation, and atomic promotion. |
| Repeatability | PASS | Two unchanged production renders emitted byte-identical manifests. |
| Complete gate | PASS | Final `npm run check` completed successfully: typecheck, 15 files/32 tests, validation, and production build. |
| Preview | PASS | Validation ran before the server; landing, Architecture index, root/Documentation modules, both delivered views, Documentation index, and Feature 002 returned HTTP 200 on `127.0.0.1:3010`. |
| Checklist confinement | PASS | `requirements.md` was moved to `implementation/checklists/`; no root copy or symlink remains. |
| Architecture | PASS | Reconciled root and Documentation views each passed 9/9 Archify showcase checks with 0 errors and 0 warnings and were freshly delivered. |
| Architecture visual review | PENDING | The current delivered bytes do not reuse older perceptual receipts. Chromium was unavailable in this execution environment, so containment, light/dark, and perceptual outcomes for the current artifacts are not claimed. |
| Feature publication sequence | PASS / visual pending | `diagrams/project-docsite-publication-flow.json` passed 9/9 showcase checks with zero errors or warnings and was freshly delivered and embedded on the canonical feature page. Chrome/Chromium was unavailable for its new visual-check receipt, so no perceptual claim is made. |

The final generated manifest is `docsite/build/build-manifest.json`. Build output is ignored and
disposable. Its recorded SHA-256 is
`df9b69190f302c2e4a31954e5ff4f7655d868a4b4a25580ff4a4f922417231ef` and can be reproduced with
`sha256sum`.

The current Archify artifacts are `generated/architecture/concorde-root.html` at SHA-256
`73e6f842d642eb8cc8703764f3be2788df558e8586d21983cb95c21c60e491d5` and
`generated/architecture/documentation.html` at SHA-256
`8d2231b853f3b88b1f87e35a9fca33a511e1b4a78e750cc469de9864bb3fddad`.
Older visual receipts do not bind these bytes, so a fresh browser review remains pending.

The supplemental publication sequence is `generated/architecture/project-docsite-publication-flow.html`.
Its maintained-source SHA-256 is
`d483e6d7592dd378ba227bc7bf760cd88fb3e2c9e0f44d746827025806568116`, and its delivered artifact
SHA-256 is `c85d98ffce678d41c4dc3a7f75ba7102aa6c1e7b0753616c3dd7a9afa5d002a6`.

## Story Checkpoints

### User Story 1

The valid fixture and real production site expose Architecture, Documentation, and Features from one landing page.
Every included page appears once in the manifest and rendered route inventory, has source provenance,
and is included in the self-hosted search index. Registry, production-build, and accessibility tests
provide the executable evidence.

The real build publishes 19 architecture Markdown pages. The root and Documentation pages expose
stable identity and source provenance and embed their declared Archify outputs from
`/architecture/concorde-root.html` and `/architecture/documentation.html` in sandboxed iframes.

### User Story 2

The authoring test adds, renames, and removes a nested root document without changing `docsite/`
registration. Link tests cover same-collection, cross-collection, fragments, missing targets,
excluded targets, and escaping targets. Before/after SHA-256 inventories prove validation does not
write canonical fixture sources.

### User Story 3

Feature tests recursively discover permanent `**/spec.md` and paired `**/design.md`, extract feature
ID, module, status, and feature directory, and reject duplicate IDs or invalid pairings. The real
site renders all eight current specification/design pairs with provenance and never labels temporal
plans, tasks, checklists, validation, or feature-local contracts as permanent feature pages.

### User Story 4

Command contract tests cover stable npm entry points, exit status, and actionable errors. Atomic
promotion tests cover success, stale backup cleanup, and rollback after a missing candidate. The real
production test performs two builds and compares the complete manifest bytes.

### User Story 5

The Documentation landing page now provides direct, ordered links to the quick start, framework
overview, specification model, project structure guide, core workflow, and command reference. The
eight-page collection distinguishes explanatory guidance from normative architecture and feature
authority and uses validated cross-collection links back to the relevant canonical sources. The
specified reader-classification and first-use exercises remain manual checks.

The focused framework-guide contract passes 3/3 tests. The final registry and production build
include all eight project documents exactly once, expose stable routes for all six learning guides,
retain every landing-page journey link, and resolve each normative summary to an included canonical
Architecture or Features source. Automated publication is complete; SC-006, SC-011, and SC-012 are
not inferred from these structural results.

## Functional Requirement Matrix

| Requirement | Status | Evidence |
|---|---|---|
| FR-001 | PASS | Independent `docsite/` package owns configuration, presentation, plugin, scripts, and tests. |
| FR-002 | PASS | Root `docs/` owns maintained project documentation. |
| FR-003 | PASS | Feature prose remains in root `specs/**/spec.md`. |
| FR-004 | PASS | No canonical source copies exist in `docsite/`; test fixtures are explicitly test-only synthetic inputs. |
| FR-005 | PASS | Recursive docs glob and registry/authoring tests. |
| FR-006 | PASS | Recursive canonical-spec glob and feature-publication tests. |
| FR-007 | PASS | Exclusion records and canonical-only assertions. |
| FR-008 | PASS | SHA-256 source-immutability test and final repository audit. |
| FR-009 | PASS | Landing page and three-section navigation production smoke test. |
| FR-010 | PASS | Autogenerated path hierarchy plus navigation metadata. |
| FR-011 | PASS | Feature titles in navigation; ID and status in accessible provenance. |
| FR-012 | PASS | Add/rename/remove fixture test with no page registration. |
| FR-013 | PASS | Shared provenance banner records kind and project-relative source across all collections. |
| FR-014 | PASS | One Docusaurus theme and DocItem wrapper serve all three collections. |
| FR-015 | PASS | Self-hosted search indexes architecture, docs, and feature specifications. |
| FR-016 | PASS | Registry-backed pre-default Markdown transformer and link unit tests. |
| FR-017 | PASS | Missing title/link, duplicate identity/route, containment, read-failure handling, and stable diagnostics. |
| FR-018 | PASS | Draft specs remain published with literal status; presentation makes no approval claim. |
| FR-019 | PASS | Preview validates first; preview and build share the registry and Docusaurus config. |
| FR-020 | PASS | Byte-identical manifest test over two independent renders. |
| FR-021 | PASS | `.gitignore` covers all generated/cache/output directories. |
| FR-022 | PASS | Manifest and page banner record collection kind, source, route, and source SHA-256. |
| FR-023 | PASS | `docsite/README.md` and `docs/contributing/docsite.md`. |
| FR-024 | PASS | Empty/missing inputs cannot fabricate pages; absent roots or metadata result in validation/render diagnostics while the landing summary remains data-driven. |
| FR-025 | PASS | Candidate verification precedes atomic promotion; rollback tests preserve prior output. |
| FR-026 | PASS | Site has no editing path and directs contributors to canonical Markdown. |
| FR-027 | PASS | Recursive architecture-pattern discovery under `specs/` publishes all module and boundary-contract sources without additional maintained copies. |
| FR-028 | PASS | Architecture sidebar hierarchy plus provenance exposes stable ID, kind, module/parent, and source path. |
| FR-029 | PASS | Declared views are mapped from JSON `meta.output`, sandbox-embedded, directly linked, and covered by production tests. |
| FR-030 | PASS | `architecture.view.unpublishable` blocks unresolved JSON/output mappings with remediation. |
| FR-031 | PASS | Registry reads architecture Markdown/JSON and delivered HTML without mutation; generated site remains disposable. |
| FR-032 | PASS | Architecture and feature specifications share the hierarchical `specs/` source root and are projected into separate site views. |
| FR-033 | PASS | The text-backed publication sequence names the build, registry, Archify, materialization, Docusaurus, candidate, and publisher calls; the manifest records its declaration/provenance and the canonical feature page embeds it with a standalone link. |
| FR-034 | PASS | `docs/framework-overview.md` explains the problem, combined influences, recursive abstraction, and adjacent-tool boundaries. |
| FR-035 | PASS | `docs/quick-start.md` covers project-site preview, verified local bundle installation, first feature setup, validation, and approval gates. |
| FR-036 | PASS | The specification model and project structure guides distinguish durable intent, temporary work, installed machinery, evidence, and generated projections. |
| FR-037 | PASS | `docs/project-structure.md` maps major workspace locations to role, maintenance status, and correct edit path. |
| FR-038 | PASS | `docs/core-workflow.md` explains the path from root architecture through feature work, validation, hardening, and publication. |
| FR-039 | PASS | `docs/commands.md` separates normal Spec Kit phases, six Concorde operations, integration presentation, adapters/launchers, and runtime. |
| FR-040 | PASS | `docs/index.md` supplies the progressive reading path; source validation confirms every maintained canonical-authority link. |

## Success-Criteria Matrix

| Criterion | Status | Evidence |
|---|---|---|
| SC-001 | PASS | Locked install plus complete build finished well under five minutes. |
| SC-002 | PASS | Registry/manifest cardinality covers 21 architecture sources, 8 documentation pages, and 8 feature specification/design pairs; actual-route assertions pass. |
| SC-003 | PASS | Add/rename/remove authoring integration test. |
| SC-004 | PASS | Byte-identical unchanged-build manifest comparison. |
| SC-005 | PASS | Invalid fixture matrix and command diagnostic contract tests. |
| SC-006 | MANUAL | Landing, three-section navigation, route reachability, and search index are automated acceptance proxies; the specified 90%-of-participants exercise was not run because no participant pool was available. |
| SC-007 | PASS | Production HTML checks every feature source plus ID/module/status provenance; Feature 002 visibly reports implemented automated publication while retaining pending browser and participant evidence. |
| SC-008 | PASS | Before/after source hashing and ignored-output repository audit show zero generated copies or mutations under `docs/` or `specs/`. |
| SC-009 | PARTIAL | The publication sequence passes all 9 Archify showcase checks with zero errors or warnings, has a fresh provenance-bound delivery, and is embedded on its canonical feature page; browser perceptual review remains pending. |
| SC-010 | PASS | Each required destination is directly linked from the Documentation landing page and all routes pass production validation. |
| SC-011 | MANUAL | The artifact-classification exercise requires a participant pool; the guide coverage and terminology are present and validated as automated prerequisites. |
| SC-012 | MANUAL | The five-change first-use exercise requires participants; the project-structure edit map and workflow operations are present and validated as automated prerequisites. |
| SC-013 | PASS | All framework guides link to canonical architecture or feature sources where they summarize normative behavior; validation reports zero broken or excluded-source links. |

## Security and Output Audit

The compatible Vitest update from 4.0.8 to 4.1.11 removed the lockfile's critical development-tool
advisory. `npm audit` still reports 26 transitive advisories (7 moderate, 19 high, 0 critical) in the
pinned Docusaurus/search dependency graph. They are not silently force-upgraded because that could
cross the planned Docusaurus 3.10.2 compatibility boundary; dependency remediation remains follow-up
maintenance.

`git status --ignored` confirms `docsite/node_modules/`, `.docusaurus/`, `.generated/`, and `build/`
are ignored. No generated site, cache, or staged canonical copy is a maintained project source.
The accepted Feature 002 design remains at SHA-256
`4997088cdfaa455393de68707fbbe6ea851ffcc5b7a1c5351e1669fc7dde31ee`, and `git diff --check`
reports no whitespace errors. The final status audit contains only intended maintained source,
temporal planning/evidence, contract, documentation, and test changes.
