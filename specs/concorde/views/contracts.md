# Views contracts

The interfaces of [Views](module.md): the scaffold proposal exchanged with its caller, the site
identity file, the build commands and the build manifest.

## Scaffold proposal

`concorde.py docsite --propose` returns a result whose `result.proposal` is the value below and
whose `result.prerequisites` is a separate array of `{name, status, detail}` records for `node` and
`npm`, with status `present`, `missing` or `outdated`. Prerequisite warnings never change the
proposal. `--apply --proposal PATH` reads a safe project-relative JSON file holding the value
itself, `{"proposal": value}` or the whole propose result `{"result": {"proposal": value}}`.

```concorde-contract
{
  "id": "contract.views.scaffold-proposal",
  "version": 2,
  "schema": {
    "type": "object",
    "required": [
      "proposal_version",
      "template_root",
      "template_digest",
      "identity",
      "github_pages",
      "files",
      "conflicts"
    ],
    "properties": {
      "proposal_version": {
        "enum": [
          2
        ]
      },
      "template_root": {
        "enum": [
          "docsite"
        ]
      },
      "template_digest": {
        "type": "string"
      },
      "identity": {
        "type": "object"
      },
      "github_pages": {
        "type": "boolean"
      },
      "files": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "required": [
            "path",
            "sha256"
          ],
          "properties": {
            "path": {
              "type": "string"
            },
            "sha256": {
              "type": "string"
            },
            "source": {
              "type": "string"
            },
            "content": {
              "type": "string"
            }
          },
          "additionalProperties": false
        }
      },
      "conflicts": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "path",
            "reason"
          ],
          "properties": {
            "path": {
              "type": "string"
            },
            "reason": {
              "type": "string"
            }
          },
          "additionalProperties": false
        }
      }
    },
    "additionalProperties": false
  },
  "semantics": "An exact, package-digest-bound scaffold proposal; the local ownership and content rules determine which files may be created. It grants no replacement or deletion authority.",
  "example": {
    "proposal_version": 2,
    "template_root": "docsite",
    "template_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "identity": {
      "schema_version": 1,
      "title": "Example",
      "url": "https://localhost",
      "baseUrl": "/",
      "organizationName": "example",
      "projectName": "example"
    },
    "github_pages": false,
    "files": [
      {
        "path": "docsite/package.json",
        "source": "docsite/package.json",
        "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
      }
    ],
    "conflicts": []
  }
}
```

The example shows the shape, not a real inventory or digest.

**Files.** The entries are sorted by `path`, unique, and each has exactly one of `source` and
`content`. `sha256` is `sha256:` followed by the lowercase hex SHA-256 of the file's bytes. The
complete set is fixed:

- every template file, with `source` equal to `path`;
- `docsite/site.json`, the only entry with inline `content`: the proposal's `identity` serialized
  as JSON with sorted keys, two-space indentation and a final newline;
- only when `github_pages` is true, `.github/workflows/deploy-docsite.yml` with `source`
  `docsite/scaffold/deploy-docsite.yml`.

**Template inventory.** The template files are the regular files below the installed package's
`docsite/` whose suffix is `.css`, `.json`, `.md`, `.svg`, `.ts`, `.tsx` or `.yml`, excluding any
path with a directory component named `node_modules`, `build`, `.generated`, `.docusaurus` or
`coverage`, the subtrees `tests/repository/`, `custom-docs/` and `scaffold/`, and the root
`site.json`. A symbolic link anywhere in the traversed tree is an error. The installer ships the
same set plus `scaffold/`. `template_digest` is `sha256:` over the UTF-8 text made of one line per
template file, sorted by path, each `path`, a tab and the lowercase hex SHA-256 of its bytes,
joined by newlines with a final newline.

**Identity.** `identity` is a site identity (below) with `schema_version` 1, `title`, `url`,
`baseUrl`, `organizationName`, `projectName` and, when known, `repository`. The title defaults to
the root Module's title. A GitHub repository, given by `--repository` or read from the `origin`
remote, supplies `https://<owner>.github.io` as `url`, `/<repo>/` as `baseUrl` (`/` for the
`<owner>.github.io` repository) and the owner and repository names. Otherwise the defaults are
`https://localhost`, `/`, and the lowercased title with every run of other characters replaced by
one hyphen, trimmed, or `project` when empty; an info finding then asks the developer to set the
final values. Explicit options override the defaults. The scaffold never adds a homepage or custom
docs.

**Conflicts.** `conflicts` lists every proposed destination that already exists, with reason
`target already exists`. It is information only and authorizes nothing.

**Apply.** Apply rebuilds the complete inventory from the installed package and the proposal's
`identity` and `github_pages`, and requires the proposal's `template_digest` and `files` to equal it
exactly; otherwise it returns `invalid`. Then:

- every destination already has the proposed bytes: `unchanged`, nothing written;
- any destination exists with other content: `conflict`, nothing written;
- every destination is absent: the files are created through a file transaction that checks each
  destination is still absent before staging and before each write, and removes the files it
  created if one appears; the result is `success` with the created paths, or `failed` after a
  rollback.

Apply never replaces or deletes a file, so it cannot update an existing site or touch a Spec.

<a id="scaffold-proposal-participation"></a>

**Participation.** Views provides this contract, version 2, to external callers: the developer or
user session calling the command. Views keeps the proposal deterministic for unchanged inputs,
refuses any proposal that differs from the exact current inventory, and never lets an accepted
proposal replace, delete or reach outside the files listed above.

## Site identity {#site-identity}

`docsite/site.json` is project-owned JSON, site identity schema 1. It is read when the site starts
or builds; a missing file, invalid JSON or a broken rule fails with an error naming
`docsite/site.json` and the field.

| Field | Rule |
| --- | --- |
| `schema_version` | Exactly `1`. |
| `title` | Nonempty; site and navigation title. |
| `url` | Absolute `http://` or `https://` URL. |
| `baseUrl` | Starts and ends with `/`. |
| `organizationName`, `projectName` | Nonempty. |
| `repository` | Optional absolute HTTP(S) URL; adds a navigation link, an icon for `github.com`, otherwise a "Source" label. |
| `tagline` | Optional nonempty string. |
| `customDocs` | Optional array of collections, below. |
| `homepage` | Optional object, below; without it the root redirects to the root Module's entry. |

The field `protocolDocs` is rejected with a message pointing to `customDocs`.

**Custom docs collections.** Each has nonempty `id`, `label`, `path` and `routeBasePath`, and
optional `sidebarPath`. `id` is a unique lowercase slug other than `default`. `routeBasePath` is
one or more `/`-separated segments of letters, digits, `_` or `-`, not `specs` or below it, and
neither equal to, inside nor containing another collection's route. `path` (a directory) and
`sidebarPath` (a file) are relative to `docsite/`, may use `../`, and may not be absolute, use a
drive prefix or contain a backslash. A collection must not contain a registered Spec document. Each
collection is published as its own Docusaurus docs instance with its own sidebar, search index and
navigation entry; its landing document uses `slug: /`.

A project may also provide `docsite/custom-docs/index.ts`, exporting an object with optional
`plugins` and `navbarItems` arrays. They are added to the site as they are; their routes must stay
outside `/specs`, and duplicate routes fail the build.

**Homepage.** `homepage` has nonempty strings `eyebrow`, `title` and `description`; `features`
with a nonempty `title` and a nonempty `items` array; `workflow` with nonempty `title`,
`description` and a nonempty `steps` array; and `quickstart` with nonempty `title`, `description`
and `code`. Each item and step has nonempty `title` and `description`. Optional `links` is an array
of `{label, to}` with a nonempty label and a local `/route` or an HTTP(S) URL. Optional `reference`
has nonempty `title` and `description` and a nonempty `tables` array; each table has nonempty
`title` and `description`, a nonempty `columns` array of nonempty strings and a nonempty `rows`
array whose rows have one nonempty string per column. All homepage text renders as plain text.

## Build commands

Commands run from `docsite/` with the dependencies installed from `package-lock.json`.

| Command | Effect |
| --- | --- |
| `npm run validate` | Loads the project and renders every page in memory; reports the number of Modules and documents or fails. Writes nothing. |
| `npm run start` | Stages the Specs and starts the Docusaurus preview. |
| `npm run build` | Stages, builds the candidate, validates it and promotes it to `docsite/build/`. |
| `npm test` | Runs the publisher's tests. |
| `npm run typecheck` | Type-checks the TypeScript sources. |
| `npm run check` | Runs typecheck, tests, validate and build in that order. |

A command exits nonzero with a diagnostic on any failure; `validate`, `start` and `build` fail
first when the project has no Concorde configuration.

## Build manifest

A successful build writes `build-manifest.json` at the root of the published site:

```json
{
  "schema_version": 22,
  "sourceDigest": "sha256:…",
  "pages": [
    {
      "sourcePath": "specs/concorde/views/module.md",
      "route": "/specs/concorde/views/module",
      "contentDigest": "sha256:…",
      "metadataPath": "specs/concorde/views/module.md.json",
      "metadataDigest": "sha256:…",
      "readingCollection": "module",
      "owner": "module.views",
      "includedBy": [
        {"moduleId": "module.concorde", "reasons": [{"kind": "contains", "id": "module.views"}]},
        {"moduleId": "module.views", "reasons": [{"kind": "owns", "id": "module.views"}]}
      ]
    }
  ]
}
```

`schema_version` is 22. `pages` has one entry per registered document in registry order, with
exactly the fields shown, in that order. `contentDigest` and `metadataDigest` hash the exact bytes
of the reading and metadata files. `includedBy` lists, in registry order, each Module whose
one-level Spec context selects the document, with its reasons sorted by `kind` and then `id`;
`kind` is `owns`, `contains`, `uses` or `includes`, and `id` is the Module or document that the
relation names. `sourceDigest` is defined in the [pipeline](pipeline.md#source-digest). A manifest
of any other version, or with any difference in these fields, is stale and requires a fresh build.
The manifest records inputs only and makes no claim that code satisfies the Specs.
