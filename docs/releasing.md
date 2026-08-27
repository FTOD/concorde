---
title: Releasing Concorde
sidebar_position: 8
---

# Releasing Concorde

A Concorde release is three archives and three Spec Kit catalogs published as immutable assets of
one GitHub release on `FTOD/concorde`, plus a small `release.json` pointer. Publication is automated:
a maintainer marks a version by pushing a tag, and the `Publish Concorde release` workflow builds,
verifies, and publishes it. The normative behavior is the
[publish-release sub-feature](../specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/spec.md)
of Feature 003; the published layout and pointer schema are defined by that sub-feature's
`contracts/release-publication.md` interface profile in the repository.

## Where a release lives

| Location | Content |
|---|---|
| `https://github.com/FTOD/concorde/releases/download/v<version>/<asset>` | Version-specific, immutable: `concorde-core-<v>.zip`, `concorde-<v>.zip`, `concorde-bundle-<v>.zip`, `extensions.json`, `presets.json`, `bundles.json`, `release.json` |
| `https://github.com/FTOD/concorde/releases/latest/download/release.json` | Current-release pointer: the newest published, non-pre-release version and its three catalog URLs |

The catalogs advertise exactly these locations, so `specify … catalog add` works from any project
without a local server.

## 1. Bump the version in one place, then the pins

The release version has a single authority: `bundle.version` in
`bundles/concorde-bundle/bundle.yml`. The bundle's pinned component versions,
`presets/concorde-core/preset.yml`, and `extensions/concorde/extension.yml` must declare the same
version, and every manifest must name the repository `https://github.com/FTOD/concorde`. The
builder refuses to build when they disagree:

```bash
uv run python scripts/release/build-components.py --print-version
```

Bump all four version fields in the same commit. A version with a suffix such as `0.2.0-rc.1` is
published as a pre-release, which the `latest` pointer skips.

## 2. Rehearse without publishing

Locally:

```bash
uv run python scripts/release/build-components.py --output dist
uv run python scripts/release/verify-release.py --dist dist \
  --expect-version "$(uv run python scripts/release/build-components.py --print-version)" \
  --expect-base-url "https://github.com/FTOD/concorde/releases/download/v$(uv run python scripts/release/build-components.py --print-version)"
uv run python scripts/release/publish-release.py --dist dist --tag "v$(uv run python scripts/release/build-components.py --print-version)" --dry-run
```

The dry run prints the Publication Record: the ordered `gh release` operations, the release notes,
and the pointer, and performs no GitHub operation. On GitHub, run the `Publish Concorde release`
workflow manually with `dry_run` checked to rehearse the same steps on a clean runner.

## 3. Tag the merged commit

```bash
git tag v0.1.0
git push origin v0.1.0
```

The tag must equal `v` + the manifest version; anything else stops with `version-mismatch` before
any change. The workflow then:

1. runs the unit tests and the release contract tests;
2. builds the archives and catalogs and verifies digests, locations, and a byte-equivalent rebuild;
3. creates the release as a **draft**, uploads all seven assets, and only then publishes it, so the
   `latest` pointer never observes an incomplete release;
4. writes the Publication Record to the job summary.

## 4. Read the Publication Record

| `outcome` | Meaning | Exit |
|---|---|---|
| `published` | New release published with seven assets. | 0 |
| `already-published` | Same version already published with identical catalogs and digests; nothing changed. | 0 |
| `dry-run` | Plan printed; no GitHub operation. | 0 |
| `divergent` | Same version already published with different content. Refused. Publish a new version. | 2 |
| `version-mismatch` | Tag does not equal the manifest version. | 1 |
| `verification-failed` | Digests, locations, or reproducibility failed. | 1 |
| `publication-failed` | A GitHub operation failed after the draft was created; `residual_state` names the draft. Re-running the workflow repairs the draft and publishes. | 1 |

## Rules

- Never delete, move, or re-point a published tag. A published version is immutable; a change
  needs a new version.
- Never upload assets by hand or with `--clobber`; the publisher only ever adds a complete release.
- The localhost path used by the acceptance suite (`scripts/release/build-components.py
  --base-url http://127.0.0.1:8765` plus `tests/concorde/support/catalog_server.py`) is unchanged and
  remains the development install path described in the [Quick start](quick-start.md).
