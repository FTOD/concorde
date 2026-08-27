# Data Model: Publish a Concorde Release

## Entities

### Version Identity

| Field | Source | Rule |
|---|---|---|
| `version` | `bundles/concorde-bundle/bundle.yml` → `bundle.version` | Single authority. Semantic version; optional pre-release suffix. |
| pinned preset/extension versions | `bundle.yml` → `provides.*[].version` | MUST equal `version`. |
| manifest versions | `preset.yml`, `extension.yml` → `*.version` | MUST equal `version`. |
| `tag` | git tag that triggered publication | MUST equal `v<version>`; otherwise publication stops (FR-005). |
| `repository` | builder constant `https://github.com/FTOD/concorde` | Manifests' `repository` MUST equal it (FR-003). |
| `base_url` | derived `<repository>/releases/download/<tag>` | Every catalog `catalog_url`/`download_url` MUST start with it. |

### Published Release

One immutable version at the public location.

| Field | Description |
|---|---|
| `tag`, `version` | From Version Identity. |
| `assets` | Exactly seven Release Assets (see below). |
| `state` | `absent` → `draft` → `published`; `published` is terminal. |
| `prerelease` | `true` when `version` has a pre-release suffix; excluded from the current-release pointer. |
| `notes` | Human-readable text naming component versions, Spec Kit range, digests, registration commands. |

### Release Asset

| Name | Kind | Produced by | Integrity |
|---|---|---|---|
| `concorde-core-<v>.zip` | preset archive | `build-components.py` | sha256 in `presets.json` |
| `concorde-<v>.zip` | extension archive | `build-components.py` | sha256 in `extensions.json` |
| `concorde-bundle-<v>.zip` | bundle archive | `specify bundle build` / builder | sha256 in `bundles.json` |
| `extensions.json`, `presets.json`, `bundles.json` | Spec Kit catalogs | `build-components.py` | verified by `verify-release.py` |
| `release.json` | Current-Release Pointer document | `publish-release.py` | schema-validated; digests copied from catalogs |

Rules: names are fixed per version; archives and catalogs MUST be byte-identical to a rebuild from
the tagged sources (SC-002); an asset of a `published` release is never replaced.

### Current-Release Pointer

The document at `<repository>/releases/latest/download/release.json`. Its schema and semantics are
normative in [`contracts/release-publication.md`](../contracts/release-publication.md). Identifies
exactly one `version` and the three catalog URLs for it (FR-007). Resolves only to `published`,
non-prerelease releases; a `draft` never affects it.

### Publication Record

The evidence of one publisher run.

| Field | Values |
|---|---|
| `outcome` | `published` · `already-published` (identical, no-op) · `divergent` (refused) · `version-mismatch` · `verification-failed` · `dry-run` |
| `compared` | For `already-published`/`divergent`: per-asset digest/URL equality. |
| `plan` | Ordered `gh` operations that were (or, in dry-run, would be) performed. |
| `residual_state` | For failures after a draft was created: the draft tag and which assets exist. |

Emitted as JSON on stdout and as the workflow job summary.

## State transitions

```text
absent ──(create draft, verify-tag)──▶ draft ──(all 7 assets uploaded)──▶ published
draft  ──(re-run: delete draft assets, re-upload)──▶ draft ──▶ published
published ──(re-run, identical digests)──▶ published            [no-op]
published ──(re-run, any difference)──▶ published + error 2     [refused, unchanged]
any    ──(tag ≠ version | verification fails)──▶ unchanged + error 1
```

## Validation rules mapped to requirements

| Rule | Requirement |
|---|---|
| Tag equals manifest version; all manifests agree | FR-005 |
| Catalog URLs start with the published base URL; repository matches | FR-003 |
| Verifier passes (digests, HTTPS, safe entries, byte-equivalent rebuild) before any `gh` call | FR-004, SC-002 |
| Draft-then-publish; pointer only sees published releases | FR-007 |
| Identical re-run → no-op; different → refused | FR-006, SC-004 |
| Notes present with versions and Spec Kit range | FR-009 |
| Localhost base URL still accepted by builder/verifier | FR-010 |
