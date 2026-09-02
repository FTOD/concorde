# Releasing Concorde

Concorde releases one standalone package. `concorde.json` is the sole version, repository,
Architecture Profile, Workspace Protocol, command/template inventory, and integration authority.

## Build

```bash
python3 scripts/release/build-release.py --output dist
```

The builder creates exactly:

- `concorde-<version>.zip`
- `release.json`

The archive has one `concorde/` root and an allowlisted set of root README/manifest, commands,
templates, runtime, portable scripts/native installer, and agent assets. Member order, timestamp,
mode, and compression settings are normalized. The pointer binds name/version/tag/repository,
Profile 7, Protocol 12, archive URL, and SHA-256.

## Verify

```bash
python3 scripts/release/verify-release.py \
  --dist dist \
  --expect-version 1.0.0 \
  --expect-base-url https://github.com/FTOD/concorde/releases/download/v1.0.0
```

Verification checks:

- package/pointer/tag/profile/protocol identity;
- pointer URL and archive digest;
- unique safe archive members beneath `concorde/`;
- required manifest, installer, runtime, command, and template members;
- absence of removed host-package layouts;
- isolated extraction and native Codex installation; and
- a byte-equivalent rebuild from the same source and base URL.

## Publish

```bash
python3 scripts/release/publish-release.py --dist dist --tag v1.0.0 --dry-run
python3 scripts/release/publish-release.py --dist dist --tag v1.0.0
```

Publication verifies first. An absent release becomes a draft, receives the archive/pointer, then is
published. A leftover draft is repaired by replacing draft assets. An already-published identical
release is a no-op. Divergent published bytes are never overwritten; bump the package version.

## Release checklist

- Python unit, contract, integration, and acceptance suites pass.
- `python3 scripts/concorde.py --project-root . validate` succeeds.
- `python3 scripts/development/sync-agent-surfaces.py status` is current.
- Docsite `npm run check` succeeds.
- The release archive/pointer verify and rebuild byte-identically.
- Tag is exactly `v<concorde.json version>`.
