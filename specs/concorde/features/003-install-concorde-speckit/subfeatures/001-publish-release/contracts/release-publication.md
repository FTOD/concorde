# Interface Profile: Published Release Layout and Current-Release Pointer

**Profile ID**: `profile.feature003.publish-release.release-publication`
**Representation**: Spec Kit 0.16.4 catalogs and archives (governed by the parent's
`contracts/bundle-distribution.md`) plus one custom JSON pointer document defined here
**Owner**: `feature.concorde.install-with-spec-kit.publish-release`
**Audience**: maintainers, the sibling one-command installer, documentation, Spec Kit catalog resolution

This feature-local profile specializes the root `contract.concorde.spec-kit-installation`. It adds
no runtime behavior; it fixes where a release lives, what it contains, and how the current version
is discovered.

## Published release layout

For version `<v>` (tag `v<v>`) on repository `R = https://github.com/FTOD/concorde`:

| Location | Content | Mutability |
|---|---|---|
| `R/releases/download/v<v>/concorde-core-<v>.zip` | preset archive | immutable |
| `R/releases/download/v<v>/concorde-<v>.zip` | extension archive | immutable |
| `R/releases/download/v<v>/concorde-bundle-<v>.zip` | bundle archive | immutable |
| `R/releases/download/v<v>/{extensions,presets,bundles}.json` | Spec Kit catalogs whose `catalog_url` and `download_url` values use exactly this base | immutable |
| `R/releases/download/v<v>/release.json` | pointer document (schema below) | immutable |
| `R/releases/latest/download/<asset>` | platform alias for the newest published, non-prerelease version's asset | moves only when a newer version is fully published |

Obligations:

- All seven assets exist before the release is visible as published; the alias never resolves to a
  draft.
- Archives and catalogs are byte-identical to a deterministic rebuild from the tagged sources.
- A published asset is never replaced. An identical re-publication is a no-op; a differing one is
  refused with the differing asset names.
- `catalog_url`/`download_url` in the catalogs equal the version-specific locations above (HTTPS,
  host present) so Spec Kit's remote-URL validation and redirect re-validation pass.

## `release.json` — normative schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/FTOD/concorde/schemas/release-pointer-1.0.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "version", "tag", "repository", "base_url",
               "speckit_version", "bundle_id", "catalogs", "archives"],
  "properties": {
    "schema_version": { "const": "1.0" },
    "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[0-9A-Za-z.]+)?$" },
    "tag": { "type": "string", "pattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+(-[0-9A-Za-z.]+)?$" },
    "repository": { "type": "string", "format": "uri", "pattern": "^https://" },
    "base_url": { "type": "string", "format": "uri", "pattern": "^https://" },
    "speckit_version": { "type": "string", "minLength": 1 },
    "bundle_id": { "type": "string", "minLength": 1 },
    "prerelease": { "type": "boolean" },
    "catalogs": {
      "type": "object", "additionalProperties": false,
      "required": ["extensions", "presets", "bundles"],
      "properties": {
        "extensions": { "type": "string", "format": "uri" },
        "presets": { "type": "string", "format": "uri" },
        "bundles": { "type": "string", "format": "uri" }
      }
    },
    "archives": {
      "type": "object", "minProperties": 3,
      "additionalProperties": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" }
    }
  }
}
```

### Field semantics

| Field | Meaning |
|---|---|
| `schema_version` | Pointer document schema; `1.0` for this profile. Consumers reject unknown major versions. |
| `version` / `tag` | The release identified; `tag` is always `v` + `version`. |
| `repository` | The maintained repository; equals the `repository` field in the catalogs. |
| `base_url` | Version-specific asset base; every URL in `catalogs` starts with it. |
| `speckit_version` | Supported Spec Kit range, copied from the bundle manifest `requires.speckit_version`. |
| `bundle_id` | Catalog bundle id to pass to `specify bundle install`. |
| `prerelease` | Optional; `true` for versions with a pre-release suffix. Absent means `false`. |
| `catalogs` | The three catalog URLs to register, in the order extension → preset → bundle. |
| `archives` | Archive file name → `sha256:` digest, identical to the digests in the catalogs. |

### Compatibility rules

- Adding optional fields is a minor change (`schema_version` stays `1.x`); removing or renaming a
  required field or changing URL layout is a major change and requires a new profile version.
- The document contains no wall-clock or run-specific fields, so it is reproducible from the same
  build.
- Consumers MUST use `catalogs` URLs as given rather than constructing them from `base_url`.

### Example

```json
{
  "schema_version": "1.0",
  "version": "0.1.0",
  "tag": "v0.1.0",
  "repository": "https://github.com/FTOD/concorde",
  "base_url": "https://github.com/FTOD/concorde/releases/download/v0.1.0",
  "speckit_version": ">=0.16.4,<0.16.5",
  "bundle_id": "concorde-bundle",
  "catalogs": {
    "extensions": "https://github.com/FTOD/concorde/releases/download/v0.1.0/extensions.json",
    "presets": "https://github.com/FTOD/concorde/releases/download/v0.1.0/presets.json",
    "bundles": "https://github.com/FTOD/concorde/releases/download/v0.1.0/bundles.json"
  },
  "archives": {
    "concorde-core-0.1.0.zip": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "concorde-0.1.0.zip": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "concorde-bundle-0.1.0.zip": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
  }
}
```

(Digests are placeholders; a real document carries the built archives' digests.)

## Failure semantics

| Condition | Result |
|---|---|
| Tag does not equal manifest version, or manifests disagree | No publication; exit 1 `version-mismatch` naming each value. |
| Verification fails | No publication; exit 1 `verification-failed` with the verifier's message. |
| Release exists, digests/URLs identical | No change; exit 0 `already-published`. |
| Release exists, any difference | No change; exit 2 `divergent` listing differing assets. |
| Run interrupted after draft creation | Draft remains, alias unaffected; next run repairs the draft and publishes. |

## Evidence

- `tests/concorde/contract/test_release_publication.py`: example validates against the schema;
  publisher-generated `release.json` for a local build validates and matches catalog digests; the
  workflow file declares the tag trigger, dry-run input, and `contents: write`.
- `tests/concorde/unit/test_publish_release.py`: decision table above against a fake `gh`.
- Live evidence after the first publication is recorded in `attempt/validation.md`.
