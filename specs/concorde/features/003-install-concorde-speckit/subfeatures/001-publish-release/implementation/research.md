# Research: Publish a Concorde Release

All items below resolve the Technical Context and the spec's edge cases. Format: decision,
rationale, alternatives considered.

## R1 — Public location and stable current-release pointer

- **Decision**: Publish each version as a GitHub Release on the maintained repository
  `FTOD/concorde`, tag `v<version>`, with seven assets: `concorde-core-<v>.zip`,
  `concorde-<v>.zip`, `concorde-bundle-<v>.zip`, `extensions.json`, `presets.json`,
  `bundles.json`, `release.json`. Version-specific location:
  `https://github.com/FTOD/concorde/releases/download/v<version>/<asset>`. Current-release
  location: `https://github.com/FTOD/concorde/releases/latest/download/<asset>`, which the platform
  resolves to the newest published, non-draft, non-prerelease release.
- **Rationale**: The catalogs already advertise `releases/download/<tag>/…` URLs, so this is the
  location the parent design intended; the `latest/download` alias is a platform feature that gives
  FR-007's pointer without maintaining a second publication channel. Spec Kit accepts these URLs:
  scheme HTTPS with a host, and its fetcher re-validates each redirect hop to the asset CDN as HTTPS
  (`bundler/services/adapters.py::_http_get_json`).
- **Alternatives**: (a) publish `latest.json` on the GitHub Pages docsite — rejected because Pages
  deploys on pushes to `main`, not tags, so the pointer would lag or require cross-workflow
  triggering; (b) a mutable `latest` git tag/release — rejected because it mutates a published
  location, violating FR-006's spirit and confusing `latest/download` semantics.

## R2 — Single version authority and tag equality (FR-005, Principle VI)

- **Decision**: `build-components.py` reads the release version from
  `bundles/concorde-bundle/bundle.yml` (`bundle.version`) and asserts that the pinned
  `provides.presets[0].version`, `provides.extensions[0].version`,
  `presets/concorde-core/preset.yml` and `extensions/concorde/extension.yml` all equal it. The
  `--version` flag is removed (it could only produce archives that disagree with their manifests).
  `verify-release.py --expect-version <v>` and the publisher require the tag `v<v>` to equal that
  version. The default base URL is derived: `<repository>/releases/download/v<version>`.
- **Rationale**: Today the version is duplicated in the builder constant and three manifests; a tag
  is a fourth copy. Making the manifest the authority and checking the rest is the cheapest way to
  keep one authority per fact.
- **Alternatives**: keep `VERSION` constant and add a test — rejected; still two authorities.

## R3 — Repository URL correction (FR-003)

- **Decision**: Replace `https://github.com/concorde-workflow/concorde` with
  `https://github.com/FTOD/concorde` in `build-components.py` (`repository`, base URL) and in
  `preset.yml` / `extension.yml` `repository` fields; the verifier asserts every catalog
  `download_url` and `catalog_url` start with the expected base URL and that the manifests'
  repository equals the builder's.
- **Rationale**: The current metadata advertises a repository that does not exist; publishing it
  would violate FR-003 on the first release.

## R4 — Atomic publication and immutability (FR-004, FR-006, FR-007)

- **Decision**: `publish-release.py` performs: (1) `gh release view v<v>`; (2) if absent → create as
  **draft** with `--verify-tag`, upload all seven assets, then edit `--draft=false` (and
  `--prerelease` when the version has a pre-release suffix); (3) if present and published →
  download its `bundles.json`/`presets.json`/`extensions.json` and compare every `sha256` and URL
  with the local build; identical → exit 0 "already published, no-op"; any difference → exit 2
  "divergent release, refusing to overwrite" with the differing fields; (4) if present as a
  leftover draft (previous partial run) → delete the draft's assets and re-upload, then publish.
  Never `--clobber` a published asset.
- **Rationale**: Draft-then-publish makes the `latest` pointer flip only after all assets exist
  (FR-007) and makes an interrupted run recoverable (edge case "partial publication"). Comparing
  digests rather than "exists" gives FR-006 idempotence and a named conflict.
- **Alternatives**: `gh release create` in one step — rejected (assets upload after creation, so
  `latest` could briefly point at an incomplete release); overwrite with `--clobber` — rejected
  (mutates a published location).

## R5 — Verification before publication (FR-004)

- **Decision**: The workflow runs, in order: `uv sync`; `uv run python -m unittest discover -s
  tests/concorde/contract -p 'test_release*.py'` plus `tests/concorde/unit`; build to `dist/`;
  `specify bundle build`; `verify-release.py --dist dist --expect-version <v> --expect-base-url
  <url>`; only then the publisher. Any failure stops before any `gh` mutation. The full acceptance
  suite is not part of the release job (it is the parent's evidence and runs separately).
- **Rationale**: Matches the existing quick-start build order; the verifier's byte-equivalent rebuild
  is the reproducibility proof SC-002 asks for.

## R6 — Trigger and rehearsal (FR-001)

- **Decision**: `on: push: tags: ['v*']` for real publication; `on: workflow_dispatch` with a
  `dry_run` boolean input that runs everything and prints the publisher's plan without touching
  `gh`. Job permissions: `contents: write`. Concurrency group per tag.
- **Rationale**: Tag push is the "mark a release version" action the spec names and needs no manual
  upload; the dry-run satisfies the maintainer's need to see the plan before the first real tag.

## R7 — Release notes (FR-009)

- **Decision**: The publisher generates notes from a fixed template: version, component ids and
  versions, supported Spec Kit range, digests table, the three catalog registration commands, and a
  link to the quick start. Passed with `--notes-file`.
- **Rationale**: Deterministic, contains what FR-009 requires, and avoids relying on commit history.

## R8 — `release.json` pointer content

- **Decision**: A small JSON asset (schema in `contracts/release-publication.md`) naming
  `schema_version`, `version`, `tag`, `speckit_version` range, `base_url`, the three catalog URLs,
  the bundle id, and archive digests. Generated by the publisher from `dist/` (no wall-clock
  fields, so it is reproducible from the same build).
- **Rationale**: The sibling installer and documentation need one document that says "current
  version is X and its catalogs are here"; catalogs alone require knowing which file to read first.

## R9 — Existing test coupling to ignored `catalogs/`

- **Decision**: `test_default_catalog_urls_are_https` currently compares a default build with
  `catalogs/*.json`, which are git-ignored and therefore absent in a fresh clone or CI. Replace that
  comparison with assertions on URL shape (HTTPS, expected base URL, expected repository). Keep the
  `--publish-catalogs` builder flag as a local convenience.
- **Rationale**: The release job must run from a clean checkout.

## R10 — Development path preserved (FR-010)

- **Decision**: No change to `tests/concorde/support/catalog_server.py`, the localhost base-URL
  path, or the acceptance fixtures. The verifier keeps accepting `http://127.0.0.1:` base URLs.

## R11 — Pre-release versions and tag hygiene

- **Decision**: A version with a pre-release suffix (e.g. `0.2.0-rc.1`) is published with
  `--prerelease`, so `latest/download` skips it. `docs/releasing.md` instructs maintainers never to
  delete or move a published tag and to bump `bundle.yml` before tagging.
