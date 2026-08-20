# Docsite Build Interface v1

**Contract ID**: `contract.documentation.build-interface`

**Owner**: `module.concorde.documentation`

**Role / flow**: provided, bidirectional

**Consumers**: maintainers, contributors, and continuous-integration runners

## Purpose

Provide deterministic commands for installing, validating, previewing, testing, inspecting, and
building the project site from `docsite/`.

## Representation

The interface uses npm package scripts and process exit status. Standard output carries summaries;
standard error carries actionable diagnostics. All displayed repository paths are project-relative.

## Commands

| Command | Inputs | Successful output | Failure behavior |
|---|---|---|---|
| `npm ci` | `package.json`, `package-lock.json` | Exact locked dependencies installed | Non-zero; no source change |
| `npm run inspect` | Canonical sources and site config | Sorted counts, mappings, exclusions, findings | Non-zero on any validation error |
| `npm run validate` | Canonical sources, schemas, config | Zero validation errors | Non-zero with rule/source/remediation |
| `npm run start` | Valid sources; optional Docusaurus host/port args | Local preview using production inclusion rules | Non-zero before serving invalid content |
| `npm test` | Unit, contract, and integration fixtures | All selected tests pass | Non-zero with failed assertion/fixture |
| `npm run build` | Valid sources and locked dependencies | Verified site at `docsite/build/` and manifest | Non-zero; last successful build preserved |
| `npm run check` | All maintained inputs | Type, test, validation, and production-build gates pass | Non-zero at first failed gate |

## Guarantees

- Preview and production build use the same source registry and route rules.
- `build` is promoted only after validation, rendering, route verification, and manifest-schema checks.
- Existing successful output remains available when candidate validation or rendering fails.
- Repeating `build` with identical inputs yields an equivalent schema-valid manifest.
- No command writes beneath root `docs/` or root `specs/`.
- Commands do not require a hosted service, credentials, or LLM.

## Failure Semantics

Diagnostics use this textual shape:

```text
<rule-id> <project-relative-source[:line:column]>: <reason>
Remediation: <concrete correction>
```

Process exit code `0` means the named operation completed. Any non-zero status means its promised
output MUST NOT be treated as current or complete.

## Compatibility

Command names, exit-status meaning, output location, manifest location, and source-immutability
guarantee are stable for interface version 1. Additional commands and optional flags are compatible;
renaming or weakening an existing guarantee requires a new major interface version.

## Evidence

Contract tests invoke every command against valid and invalid fixtures. The production integration
test additionally invokes `build` against Concorde's real root `docs/` and `specs/`.
