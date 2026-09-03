# Data Model: Create Unified Project Docsite

## Site identity schema 1 — `docsite/site.json`

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | Exactly `1`. |
| `title` | string | Non-empty; site and navbar title. |
| `url` | string | Absolute `http(s)://` URL without path. |
| `baseUrl` | string | Starts and ends with `/`. |
| `organizationName` | string | Non-empty. |
| `projectName` | string | Non-empty. |
| `repository` | string or absent | Absolute URL; enables the navbar repository link. |
| `tagline` | string or absent | Optional site tagline. |

Serialized with sorted keys, two-space indent, trailing newline.

## Docsite Scaffold Proposal 1 — `result.proposal`

| Field | Type | Meaning |
|---|---|---|
| `proposal_version` | integer | Exactly `1`. |
| `template_root` | string | `docsite`. |
| `template_digest` | string | `sha256:` over sorted `path\tsha256` lines of copied template files. |
| `identity` | object | Site identity schema 1 written to `docsite/site.json`. |
| `github_pages` | boolean | Whether `.github/workflows/deploy-docsite.yml` is included. |
| `files[]` | list | `{path, sha256, source}` for template copies (package-relative `source`), `{path, sha256, content}` for generated files. |
| `conflicts[]` | list | `{path, reason}` for targets that already exist. |

Proposal content never includes timestamps or prerequisite state.

## Tool result — `docsite`

| Status | Meaning |
|---|---|
| `proposal` | Preview produced; nothing written. |
| `unchanged` | Every target already holds exact proposed bytes. |
| `invalid` | Unconfigured project, invalid identity input, template inventory disagreement, or invalid/stale proposal. |
| `conflict` | Apply found an existing or changed target; nothing written. |
| `failed` | Staged promotion failed; nothing promoted. |
| `success` | Apply promoted exactly the proposal files. |

`result.prerequisites[]`: `{name: node|npm|archify, status: present|missing|outdated, detail}`.

## Finding IDs

| ID | Severity | Condition |
|---|---|---|
| `CONCORDE-DOCSITE-001` | error | Project has no valid Profile 7 configuration/root architecture. |
| `CONCORDE-DOCSITE-002` | error | Package template inventory missing or disagrees with `concorde.json`. |
| `CONCORDE-DOCSITE-003` | error | Invalid `--title`, `--repository`, `--url`, or `--base-url`. |
| `CONCORDE-DOCSITE-004` | error | Accepted proposal invalid, unsafe, or stale against package bytes. |
| `CONCORDE-DOCSITE-005` | error | Target exists or changed at apply time. |
| `CONCORDE-DOCSITE-006` | error | Staged promotion failed. |
| `CONCORDE-DOCSITE-007` | warning | Prerequisite missing or outdated (node, npm, archify). |
| `CONCORDE-DOCSITE-008` | error | `--apply` without `--proposal`. |
| `CONCORDE-DOCSITE-009` | info | Identity defaults could not be derived from a GitHub `origin`; edit `docsite/site.json`. |

## Package inventory delta

`concorde.json.package_roots`: `agent-assets, docsite, operations, scripts, skills, src, templates`.
Template files: `docsite/**` regular files with suffix `.css .json .md .svg .ts .tsx .yml`, excluding
`node_modules/`, `build/`, `.generated/`, `.docusaurus/`, `coverage/`, `tests/repository/`, and
`site.json`. `docsite/scaffold/` is packaged but never copied into a target `docsite/`.
