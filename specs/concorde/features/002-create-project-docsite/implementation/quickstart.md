# Quickstart Validation: Unified Project Docsite

This guide is executable after feature implementation. It validates the external contracts and user
journeys; it is not an implementation tutorial.

## Prerequisites

- Node.js 20 or newer
- npm with lockfile support
- A clean Concorde checkout containing the unified root `specs/` hierarchy,
  `generated/architecture/`, `docs/`, and `docsite/`

## 1. Install Locked Dependencies

```bash
cd docsite
npm ci
```

Expected: installation completes from `docsite/package-lock.json`. It does not create or change files
under `../docs` or `../specs`.

## 2. Inspect and Validate Canonical Inputs

```bash
npm run inspect
npm run validate
```

Expected:

- The summary identifies `architecture`, `docs`, `features`, and `feature-designs` as four source
  collections presented through Architecture, Documentation, and Features navigation.
- The Documentation collection contains exactly the maintained eight-page baseline: the landing
  page, six framework learning guides, and the nested docsite contributor guide.
- Architecture Markdown sources, bounded module views, and feature-declared Archify views are discoverable.
- Root features 001 and 002 plus the nested Documentation refinement are discovered from their
  canonical `spec.md` files.
- Every root `spec.md` and paired `design.md` is included, while all Markdown below
  `implementation/`—including checklists, plans, tasks, and validation—is reported as excluded.
- All paths are project-relative and all checks pass with exit status 0.

The required source semantics are defined by
[`../contracts/content-sources.md`](../contracts/content-sources.md).

## 3. Run Deterministic Evidence

```bash
npm test
```

Expected: unit, contract, and fixture integration tests pass, including:

- four-source-collection discovery through three navigation families with stable ordering;
- framework-guide baseline inventory, landing-page links, routes, and canonical authority links;
- architecture identity and declared-view publication;
- feature identity/status extraction;
- feature specification/design pairing and permanent design provenance;
- documentation-to-feature and feature-to-document link mapping;
- missing source, duplicate ID, duplicate route, and escaping-path failures;
- manifest example and generated-manifest schema validation;
- failure-safe candidate promotion and source immutability.

## 4. Build the Production Site

```bash
npm run build
```

Expected:

- `docsite/build/` contains the landing page, `/architecture`, `/docs`, `/features`, delivered
  Archify HTML, local search index, and
  `build-manifest.json`.
- `docsite/.generated/content/architecture/` and `docsite/.generated/content/features/` are recreated
  as ignored renderer inputs, while every page and manifest record retains the canonical `specs/`
  source path.
- The landing page links to Architecture, Documentation, and Features.
- The Documentation landing page links directly to the quick start, framework overview,
  specification model, project structure, core workflow, and command reference.
- Every included page displays its project-relative source provenance.
- Feature specification pages display stable ID, owning module, and recorded status; paired design
  pages display durable source provenance and are grouped with their specification.
- Feature pages automatically embed every fresh diagram declared by `spec.md`, including source
  provenance and an open-standalone-view link.
- Architecture pages show stable identity and embed declared Archify views in a sandbox.
- No generated or copied content appears under `../docs` or `../specs`.

Validate the generated manifest explicitly:

```bash
npx ajv-cli@5 validate \
  --spec=draft2020 \
  -s ../specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json \
  -d build/build-manifest.json
```

Expected: the manifest is valid. Its normative field meanings are documented in
[`../contracts/build-manifest-contract.md`](../contracts/build-manifest-contract.md).

## 5. Verify Repeatability

```bash
tmp_dir="$(mktemp -d)"
cp build/build-manifest.json "$tmp_dir/first-build.json"
npm run build
cmp "$tmp_dir/first-build.json" build/build-manifest.json
```

Expected: `cmp` exits 0. This compares the required page inventory, navigation, source mapping,
versions, hashes, and passed checks without depending on wall-clock metadata.

## 6. Preview the User Experience

```bash
npm run start
```

Open the URL printed by Docusaurus and validate:

1. The landing page reaches Architecture, Documentation, and Features.
2. A known phrase returns results across all three route spaces in local search.
3. The root module page shows its stable ID and embeds the delivered root view.
4. Root feature 001 shows its current status, while root feature 002 and its Documentation refinement
   are visibly Implemented; each permanent design is reachable beside its specification.
5. A cross-collection link reaches its target and preserves its heading fragment.
6. Narrow and wide browser layouts keep content, navigation, provenance, and embedded views readable.

Then perform the two reader exercises without using repository search:

7. Classify representative paths as durable intent, temporary implementation state, installed
   workflow machinery, executable evidence, or generated projection. Record the participant count
   and percentage correct for SC-011.
8. For five representative architecture, feature, implementation, documentation, and diagram
   changes, identify the canonical edit path and next workflow operation. Record the participant
   count and percentage correct for SC-012.

Do not mark either participant criterion complete from automated route or content checks alone.

## 7. Verify the Framework Guide Contract

```bash
npm test -- --run tests/integration/framework-guides.test.ts
npm run validate
```

Expected: every baseline guide is present exactly once, the Documentation landing page reaches all
six learning guides, canonical authority links resolve to published Architecture or Features pages,
and no temporal implementation artifact is presented as permanent authority.

## 8. Run Failure Contracts

```bash
npm test -- --run tests/integration/atomic-promotion.test.ts
npm test -- --run tests/contract/content-sources.test.ts
```

Expected:

- Invalid fixtures fail with rule ID, source path, reason, and remediation.
- A failed candidate leaves the previously successful `docsite/build/` unchanged.
- No failed run emits a manifest with `validation.status: "passed"`.

The command and promotion guarantees are defined by
[`../contracts/build-interface.md`](../contracts/build-interface.md) and
[`../contracts/published-site.md`](../contracts/published-site.md).

## 9. Run the Complete Gate

```bash
npm run check
```

Expected: type checks, unit and contract tests, source validation, production rendering, route
verification, schema validation, source-immutability checks, and architecture publication all pass.
Archify showcase validation and delivery remain repository-level gates and must also pass before merge.
