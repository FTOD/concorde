# Validation Evidence: Concorde Starter Workflow

**Recorded**: 2026-08-20  
**Automated implementation status**: Passed  
**Overall feature evidence**: Partial — the timed human first-use and comprehension pilot for SC-001,
SC-009, and SC-011 is still pending and is not inferred from automation.

## Environment

| Dependency | Observed version |
|---|---|
| `uv` | 0.11.19 |
| Python | 3.11.15 |
| Specify CLI / Spec Kit | 0.16.4 |
| Primary integration | Codex skills mode |
| Portability integration | Gemini slash-command mode |

## Release Evidence

The documented build sequence completed successfully:

```bash
uv sync
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-starter --output dist
uv run python scripts/release/verify-release.py --dist dist
specify bundle validate --offline --path bundles/concorde-starter
```

Native bundle build reported two files and structural validity. Offline validation reported the
expected unverified external-reference warnings; the catalog-backed preview/install tests then
resolved and installed both exact pins.

| Artifact | SHA-256 |
|---|---|
| `concorde-0.1.0.zip` | `71e89c6769c95975039d61d3422ba38c256ce9d4d59922f562557cdb886e158c` |
| `concorde-core-0.1.0.zip` | `4f166f1fb614081f7775609e45a164e7136dad19bd1e79a929c4303e40bde28d` |
| `concorde-starter-0.1.0.zip` | `af0581a97fb28c898876d6ce9c5ef672a40f6b80efe4ee8be9fd0ad3be1afd3a` |

Two independent builds were byte-equivalent. The checked-in HTTPS catalog entries, generated
localhost acceptance catalogs, component manifests, versions, URLs, and archive digests agreed.

## Automated Test Evidence

```bash
uv run python -m unittest discover -s tests/concorde -p 'test_*.py'
```

Result: **53 tests passed** in unit, contract, integration, and acceptance suites.

Observed coverage includes:

- constrained Profile 1 front matter, deterministic recursive discovery, project-root confinement,
  unsafe paths, symlink escapes, unsupported profiles, canonical JSON, finding order, and exits;
- append-only spec/plan/tasks composition in a module-owned nested workspace with one `spec.md` and no
  top-level `architecture/` source tree;
- source directory, `bundle.yml`, built archive, catalog ID, and isolated uninitialized-project install
  forms, all yielding the same two pinned components;
- preview/install parity, one bundle/one preset/one extension after three repeat installs, Codex
  command discovery, active/disabled component state, and project-relative launchers;
- accepted compatible update to fixture version 0.1.1, injected archive-integrity failure with the
  prior 0.1.0 record retained, shared-preset retention for another bundle, locally modified
  bundle-owned component removal, and byte-identical `.concorde/` plus `specs/` sources;
- proposal-only initialization with zero writes, exact accepted apply, staged promotion, partial and
  changed-target conflicts, malformed proposal refusal, and idempotent `unchanged` results;
- module- and feature-ID context resolution, immediate-child contract summaries, deeper navigation,
  no child feature/grandchild expansion, invalid targets, and source immutability;
- complete deterministic rule groups for identity, references, containment, refinement, contracts,
  scenario participants, one-level views, evidence status, stable digest, and all-findings behavior;
- installed proposal/apply/context/validation journeys, seeded validation failure, three-run byte
  equivalence, Codex skills registration, and Gemini slash-command registration.
- consistent Spec Kit, catalog, bundle, preset, extension, coding-agent integration, and Architecture
  Core explanations; both supplemental diagram models and use-time paths; separation from the bounded
  root view; generated artifact presence; and publication of both interactive routes.

## Self-Application Evidence

The installed-compatible launcher validated Concorde's own hierarchy three times:

```bash
extensions/concorde/scripts/bash/concorde.sh --project-root . validate --format json
```

All three outputs were byte-equivalent with status `success`, **27 inspected maintained artifacts**,
zero errors/warnings/infos. The latest post-planning validation produced source digest
`sha256:14408d3f3029e1d027c664e0ae87591bedd97f48700afd58306afa7e1f5dd6f5`.
No bootstrap exception remains for source validation.

The root bounded-context projection contained two root features, four immediate children, three
permitted externals, five current-level scenario views, four adjacent refinement links, and four
deeper child references. Child feature bodies and grandchildren were absent; each child exposed only
its organization at this level and concise contract ID/role/flow/counterparty information.

## Archify and Documentation Freshness

The root architecture specification and both supplemental Feature 001 diagrams passed all nine
Archify showcase checks with zero composition errors and warnings. Delivery receipts:

- root specification / HTML:
  `f81f718b9f3c8e4eb279cb0377ba5f45d1f9e30d9552ea737d3a1e38a02bf76f` /
  `ff42d428bbebd5863561f612db0644b9954aab43c0eda94c53c8a0c98839a3c0`
- Spec Kit component model specification / HTML:
  `dfacd3c2fa6d190dd0b737582782fbf894a0317ded6438623cd8c06c1c9b4f24` /
  `bec4fe89ab0fe5fcf66887f2efe30bcabfd259dca84a38f454b83ff37c82850c`
- starter installation flow specification / HTML:
  `1f1dd03335f4fc395ef567ef59833e1b25de9944cbf8a847b86a6ccabfc526d2` /
  `ac808d28ec9bfe2e8a5369be0a27acd67eff9095aee56e64d77f92cd574fd202`

Automated containment passed for the root and both new diagrams at 1440×900, 1600×1000, 1920×1080, and
2048×1320. Light/dark screenshots at the smallest and largest viewports received perceptual review;
labels, routes, hierarchy, theme contrast, and vertical balance passed without unresolved findings.

```bash
cd docsite
npm run check
```

Result: TypeScript passed; **14 Vitest files / 29 tests passed**; 27 pages and 23 explicit exclusions
validated with zero errors; the optimized Docusaurus site built and promoted successfully.

## Requirement and Outcome Summary

- FR-001–FR-010 and FR-025–FR-028: verified by manifests, release/catalog tests, preset composition,
  exact cardinality, and cross-integration registration.
- FR-011–FR-015 and FR-024: verified by initialization, bounded context, deterministic validation,
  explicit evidence, conflict, and source-immutability tests.
- FR-016–FR-023: verified by compatibility refusal, repeat install, update/failure/removal,
  provenance, quickstart, and retained-source tests.
- FR-029–FR-030: verified by the aligned feature, module, refinement, and contract explanations; two
  validated supplemental diagrams; desktop visual evidence; and a successful production docsite build.
- SC-002–SC-008 and SC-010: satisfied by automated acceptance evidence above.
- SC-001, SC-009, and SC-011: **pending human evidence**. No participant count, timing, assistance
  rate, or comprehension result has been fabricated.

## Pending Timed Pilot

Conduct the quickstart with first-time maintainers and record participant count, environment,
completion times, assistance required, outcome, and answers to the four role questions plus the
unchanged-lifecycle prompt.
Acceptance requires the primary journey to finish within ten minutes, at least 90% of participants to
complete without assistance beyond the bundled quickstart, and at least 90% to distinguish bundle,
preset, extension, and catalog roles and explain the unchanged Spec Kit lifecycle after reviewing the
explanation for no more than five minutes.
