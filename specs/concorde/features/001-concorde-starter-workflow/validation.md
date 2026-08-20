# Validation Evidence: Concorde Starter Workflow

**Recorded**: 2026-08-20  
**Automated implementation status**: Passed  
**Overall feature evidence**: Partial — the timed human first-use pilot for SC-001 and SC-009 is
still pending and is not inferred from automation.

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

Result: **49 tests passed** in unit, contract, integration, and acceptance suites.

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

## Self-Application Evidence

The installed-compatible launcher validated Concorde's own hierarchy three times:

```bash
extensions/concorde/scripts/bash/concorde.sh --project-root . validate --format json
```

All three outputs were byte-equivalent with status `success`, **27 inspected maintained artifacts**,
zero errors/warnings/infos, and source digest
`sha256:e75f6b0b39f67e6a82a4781d74eb5173f3d4ac417befce45bf5dd1f8b5974ee1`.
No bootstrap exception remains for source validation.

The root bounded-context projection contained two root features, four immediate children, three
permitted externals, five current-level scenario views, four adjacent refinement links, and four
deeper child references. Child feature bodies and grandchildren were absent; each child exposed only
its organization at this level and concise contract ID/role/flow/counterparty information.

## Archify and Documentation Freshness

The root architecture specification passed all nine Archify showcase checks with zero composition
errors and warnings. Delivery receipts:

- specification SHA-256: `feb429fdbc0a5eb4f964351b44af72a1c6a1dbb1eace6486aeb8a1cf0f61b6f8`
- generated HTML SHA-256: `0dbce3452b3c8befc43e5ea6ce8f273f998f18f0c6b4adaf158e36415b949b1c`

Archify visual-check was truthfully `skipped` and visual review remains `pending` because Chrome or
Chromium was unavailable.

```bash
cd docsite
npm run check
```

Result: TypeScript passed; **14 Vitest files / 29 tests passed**; 27 pages and 21 explicit exclusions
validated with zero errors; the optimized Docusaurus site built and promoted successfully.

## Requirement and Outcome Summary

- FR-001–FR-010 and FR-025–FR-028: verified by manifests, release/catalog tests, preset composition,
  exact cardinality, and cross-integration registration.
- FR-011–FR-015 and FR-024: verified by initialization, bounded context, deterministic validation,
  explicit evidence, conflict, and source-immutability tests.
- FR-016–FR-023: verified by compatibility refusal, repeat install, update/failure/removal,
  provenance, quickstart, and retained-source tests.
- SC-002–SC-008 and SC-010: satisfied by automated acceptance evidence above.
- SC-001 and SC-009: **pending human evidence**. No participant count, timing, or assistance rate has
  been fabricated.

## Pending Timed Pilot

Conduct the quickstart with first-time maintainers and record participant count, environment,
completion times, assistance required, and outcome. Acceptance requires the primary journey to finish
within ten minutes and at least 90% of participants to complete without assistance beyond the bundled
quickstart.
