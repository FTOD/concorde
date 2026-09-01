# Releasing Concorde

Concorde releases one pinned preset + extension + bundle component set. The bundle manifest's version
is the single release-version authority; preset/extension manifests and bundle pins must agree.

## Build

```bash
uv run python scripts/release/build-components.py --output dist
```

The builder creates deterministic archives and matching catalogs:

- `concorde-preset-<version>.zip`
- `concorde-extension-<version>.zip`
- `concorde-bundle-<version>.zip`
- `presets.json`, `extensions.json`, and `bundles.json`

Archives use a strict member allowlist, normalized permissions/timestamps, and sorted paths. Catalog
entries include repository/version/Spec Kit range, Architecture Source Profile 7, Feature Workspace
Protocol 12, capability counts derived from manifests, HTTPS release locations, and SHA-256 digests.

## Verify

```bash
uv run python scripts/release/verify-release.py --dist dist
```

Verification checks manifest identity, catalog metadata and URLs, profile/protocol values, archive
digests, safe member paths, and a byte-equivalent rebuild. For CI release tags, also pin expected
version/base URL.

## Release pointer

`release.json` is the installer's current/version-specific entry point. It declares schema/version/
tag/repository/base URL, supported Spec Kit range, bundle ID, Profile 7, Protocol 12, catalog URLs,
and archive digests. The installer rejects a missing or mismatched profile/protocol before catalog
registration.

## Publish

The publisher verifies local artifacts first. An absent release becomes a draft, receives all
immutable assets, then is published. A leftover draft is repaired by replacing draft assets. An
identical published release is a no-op; a divergent published release is refused. Published assets
are never clobbered.

```bash
uv run python scripts/release/publish-release.py --dist dist --tag v<version> --dry-run
uv run python scripts/release/publish-release.py --dist dist --tag v<version>
```

## Pre-release checklist

- canonical package sources and manifests agree;
- self-host status is current for the active integration;
- obsolete template projections are absent;
- Protocol 12/Proposal 8 markers are fresh across installed surfaces;
- full Python tests and docsite `npm run check` pass;
- Concorde validation passes on the self-hosted specifications;
- catalogs rebuild deterministically; and
- release notes explain any breaking interface/profile change.
