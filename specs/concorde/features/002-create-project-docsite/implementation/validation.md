# Validation Record: Unified Project Docsite

**Validated**: 2026-08-20  
**Environment**: Node.js 22.22.3, npm lockfile, Linux  
**Result**: Automated implementation gates and both architecture visual reviews pass; the timed
SC-006 participant exercise remains a release-level manual check because no participant pool was
available.

## Command Evidence

| Gate | Result | Evidence |
|---|---|---|
| Locked install | PASS | `npm ci` installed the lockfile successfully without maintained-source writes. |
| Inspect | PASS | 19 architecture sources, 2 project documents, and 6 canonical feature specs discovered; 22 supporting Markdown files are reported as excluded. |
| Validate | PASS | 27 included real-repository pages and all declared architecture views validated with zero findings. |
| Type check | PASS | Strict `tsc --noEmit`. |
| Test suite | PASS | 14 files and 29 tests: architecture publication, unit, contracts, fixtures, immutability, atomicity, accessibility, scale, and two production renders. |
| Scale | PASS | 1,000 documents plus 250 specs discovered and validated in 0.613 seconds in the final measured gate. |
| Production build | PASS | Three-collection Docusaurus render, sandboxed view embedding, strict route verification, local-search generation, manifest v2 validation, and atomic promotion. |
| Repeatability | PASS | Two unchanged production renders emitted byte-identical manifests. |
| Complete gate | PASS | Final `npm run check` completed successfully: typecheck, 14 files/29 tests, validation, and production build. |
| Preview | PASS | Validation ran before the server; landing, Architecture index, root/Documentation modules, both delivered views, Documentation index, and Feature 002 returned HTTP 200 on `127.0.0.1:3010`. |
| Architecture | PASS | Reconciled root and Documentation views each passed 9/9 Archify showcase checks with 0 errors and 0 warnings and were freshly delivered. |
| Architecture visual review | PASS | Chromium containment and light/dark captures pass at 1440×900, 1600×1000, 1920×1080, and 2048×1320 for both views. Perceptual inspection found no clipping, crossings, unreadable labels, or unbalanced large-screen composition. The root view required two focused card-copy corrections; Documentation required none. |

The final generated manifest is `docsite/build/build-manifest.json`. Build output is ignored and
disposable. Its recorded SHA-256 is
`95db6396814acdff23326ac146898769e366407a942075922a0ff8f27aca581f` and can be reproduced with
`sha256sum`.

The reviewed Archify artifacts are `generated/architecture/concorde-root.html` at SHA-256
`04649fed737b3b891f26f34f50190593afc3cbcd64efab201262d91fc30fd134` and
`generated/architecture/documentation.html` at SHA-256
`a4e88271bc7c566bc420551ded3836d926c4bc8901c7ae64ae5ec34c40a9655c`. Their adjacent visual-check
receipts and light/dark screenshots bind the inspection to those exact delivered bytes.

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

Feature tests recursively discover only `**/spec.md`, extract feature ID, module, status, and feature
directory, and reject duplicate IDs. The real site renders all six current specifications with their
recorded lifecycle status and never labels plans, tasks, checklists, or contracts as feature pages.

### User Story 4

Command contract tests cover stable npm entry points, exit status, and actionable errors. Atomic
promotion tests cover success, stale backup cleanup, and rollback after a missing candidate. The real
production test performs two builds and compares the complete manifest bytes.

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

## Success-Criteria Matrix

| Criterion | Status | Evidence |
|---|---|---|
| SC-001 | PASS | Locked install plus complete build finished well under five minutes. |
| SC-002 | PASS | Registry/manifest cardinality covers 19 architecture, 2 documentation, and 6 feature pages; actual-route assertions pass. |
| SC-003 | PASS | Add/rename/remove authoring integration test. |
| SC-004 | PASS | Byte-identical unchanged-build manifest comparison. |
| SC-005 | PASS | Invalid fixture matrix and command diagnostic contract tests. |
| SC-006 | MANUAL | Landing, three-section navigation, route reachability, and search index are automated acceptance proxies; the specified 90%-of-participants exercise was not run. |
| SC-007 | PASS | Production HTML checks every feature source plus ID/module/status provenance; Feature 001 displays `Implemented; timed first-use pilot pending`, and Feature 002 plus its Documentation refinement display `Implemented`. |
| SC-008 | PASS | Before/after source hashing and ignored-output repository audit show zero generated copies or mutations under `docs/` or `specs/`. |

## Security and Output Audit

The compatible Vitest update from 4.0.8 to 4.1.11 removed the lockfile's critical development-tool
advisory. `npm audit` still reports 26 transitive advisories (7 moderate, 19 high, 0 critical) in the
pinned Docusaurus/search dependency graph. They are not silently force-upgraded because that could
cross the planned Docusaurus 3.10.2 compatibility boundary; dependency remediation remains follow-up
maintenance.

`git status --ignored` confirms `docsite/node_modules/`, `.docusaurus/`, `.generated/`, and `build/`
are ignored. No generated site, cache, or staged canonical copy is a maintained project source.
