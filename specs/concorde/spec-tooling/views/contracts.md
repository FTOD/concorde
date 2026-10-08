# Views contracts

The interfaces of [Views](module.md) are:

- The scaffold proposal exchanged with its caller.
- The site identity file.
- The build commands.
- The site manifest.

## Scaffold proposal

`concorde docsite --propose` returns Spec core's
[command-line envelope](../spec/contracts.md#validation-result) with `tool: "docsite"`.
Its `result.proposal` is the value below.
Its `result.prerequisites` is a separate array of `{name, status, detail}` records for `node` and
`npm`, with status `present`, `missing` or `outdated`.
Prerequisite warnings never change the proposal. `--apply --proposal PATH` reads a safe
project-relative JSON file holding one of these forms:

- The value itself.
- `{"proposal": value}`.
- The whole propose result `{"result": {"proposal": value}}`.

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

**Files.** The entries are sorted by `path`. The entries are unique.
Each has exactly one of `source` and `content`.
`sha256` is `sha256:` followed by the lowercase hex SHA-256 of the file's bytes. The
complete set is fixed:

- Every template file, with `source` equal to `path`.
- `docsite/site.json` is the only entry with inline `content`.
  Its `content` is the proposal's `identity` serialized as JSON with these formatting rules:
  - Sorted keys.
  - Two-space indentation.
  - A final newline.
- `.github/workflows/deploy-docsite.yml` with `source` `docsite/scaffold/deploy-docsite.yml`, only
  when `github_pages` is true.

**Template inventory.** The template files are the regular files below the installed package's
`docsite/` whose suffix is `.css`, `.json`, `.md`, `.svg`, `.ts`, `.tsx` or `.yml`.
The inventory excludes:

- Any path with a directory component named `node_modules`, `build`, `.generated`, `.docusaurus`
  or `coverage`.
- The subtrees `tests/repository/`, `custom-docs/` and `scaffold/`.
- The root `site.json`.

A symbolic link anywhere in the traversed tree is an error.
The installer ships the same set plus `scaffold/` into the project's `.concorde/framework/docsite/`.
This directory is the installed package's `docsite/`.
The installer refuses to install a template this rule rejects.
`template_digest` is `sha256:` over UTF-8 text made of one line per template file, sorted by path.
Each line is the `path`, a tab and the lowercase hex SHA-256 of the file's bytes, in that order.
The lines are joined by newlines with a final newline.

**Identity.** `identity` is a site identity (below)
with `schema_version` 1, `title`, `url`, `baseUrl`, `organizationName` and `projectName`.
When known, it also has `repository`.
The title defaults to the root [Module](../../glossary.json#concept.module)'s title.
A GitHub repository, given by `--repository` or read from the `origin` remote, supplies:

- The repository supplies `https://<owner>.github.io` as `url`.
- For the `<owner>.github.io` repository, it supplies `/` as `baseUrl`.
  Otherwise, it supplies `/<repo>/` as `baseUrl`.
- The repository supplies the owner and repository names.

Otherwise:

- The defaults are `https://localhost` and `/`.
- The remaining default is the lowercased title with every run of other characters replaced by
  one hyphen, trimmed. When this value is empty, the default is `project`.
- An info finding asks the developer to set the final values.

Explicit options override the defaults. The scaffold never adds
user documents or
custom docs.

**Conflicts.** `conflicts` lists every proposed destination that already exists, with reason
`target already exists`. It is information only. It authorizes nothing.

**Apply.** Apply rebuilds the complete inventory from the installed package and the proposal's
`identity` and `github_pages`.
Apply requires the proposal's `template_digest` and `files` to equal it exactly.
Otherwise, Apply returns `invalid` with a `CONCORDE-DOCSITE-004` finding and Spec tooling's
[error record](../spec/errors.md) as the envelope's `error`.
The error record names:

- The proposal file.
- The offending field and value. For differing files, this includes every differing path.
- When the package's template digest moved, `stale_proposal`.

Then:

- When every destination already has the proposed bytes, the result is `unchanged`. Nothing is
  written.
- Otherwise, when any destination exists, whatever its content, the result is `conflict`, naming
  every existing destination. Nothing is written.
- When every destination is absent, the files are created through a
  [file transaction](../../glossary.json#concept.file-transaction).
  The transaction checks each destination is still absent before staging and before each write.
  If one appears, the transaction removes the files it created.
  The result is `success` with the created paths, or `failed` after a rollback.

Apply never replaces or deletes a file. Therefore, Apply cannot update an existing site or touch a
[Spec](../../glossary.json#concept.spec).

<a id="scaffold-proposal-participation"></a>

**Participation.** Views provides this contract, version 2, to external callers: the developer or
[main agent](../../glossary.json#concept.main-agent) calling the command.
Views:

- Keeps the proposal deterministic for unchanged inputs.
- Refuses any proposal that differs from the exact current inventory.
- Never lets an accepted proposal replace, delete or reach outside the files listed above.

## Site identity {#site-identity}

`docsite/site.json` is project-owned JSON, site identity schema 1.
When the site starts or builds, the file is read.
Each of these cases fails with an error naming `docsite/site.json` and the field:

- A missing file.
- Invalid JSON.
- A broken rule.

| Field | Rule |
| --- | --- |
| `schema_version` | Exactly `1`. |
| `title` | Nonempty; site and navigation title. |
| `url` | Absolute `http://` or `https://` URL with a host. |
| `baseUrl` | Starts and ends with `/`. |
| `organizationName`, `projectName` | Nonempty. |
| `repository` | Optional absolute HTTP(S) URL with a host; adds a navigation link, an icon for `github.com`, otherwise a "Source" label. |
| `tagline` | Optional nonempty string. |
| `userDocs` | Optional object, below; without it the root redirects to the root Module's entry. |
| `customDocs` | Optional array of collections, below. |

The field `protocolDocs` is rejected with a message pointing to `customDocs`.
The removed field `homepage` is rejected with a message pointing to `userDocs`.

**User documents.** `userDocs` has a nonempty `path` and an optional nonempty `label`.
The label defaults to "User documents".
`path` names a directory relative to `docsite/` under the same rules
as a collection's `path` below.
The directory must contain a root page, `README.md`, `README.mdx`, `index.md` or `index.mdx`.
The directory must contain no registered Spec document.
None of its top-level documents or folders may be named `specs`, `search` or the first segment of
a collection's `routeBasePath`.
The directory is published as one Docusaurus docs instance at route base `/`.
Its sidebar is generated from its folders.
The instance is the first navigation item. Its root page is the site's home page.

**Custom docs collections.** Each has nonempty `id`, `label`, `path` and `routeBasePath`.
Each has optional `sidebarPath`. `id` is a unique lowercase slug other than `default`.
`routeBasePath` is one or more `/`-separated segments of letters, digits, `_` or `-`.
The route is not `specs` or below it.
The route does not:

- Equal another collection's route.
- Lie inside another collection's route.
- Contain another collection's route.

`path` (a directory) and `sidebarPath` (a file) are relative to `docsite/`.
Both may use `../`. Neither may:

- Be absolute.
- Use a drive prefix.
- Contain a backslash.

A collection must not contain a registered Spec document.
Each collection is published as its own Docusaurus docs instance with:

- A sidebar of its own.
- A search index of its own.
- A navigation entry of its own after the Module documents tab.

Its landing document uses `slug: /`.

A project may also provide `docsite/custom-docs/index.ts`, exporting an object with optional
`plugins` and `navbarItems` arrays.
They are added to the site as they are. Their routes must stay outside `/specs`.
Duplicate routes fail the build.

## Build commands {#build-commands}

Commands run from `docsite/` with the dependencies installed from `package-lock.json`.

| Command | Effect |
| --- | --- |
| `npm run validate` | Loads the project and renders every page in memory, diagrams included; reports the number of Modules and documents or fails. Writes nothing. |
| `npm run start` | Stages the Specs and starts the Docusaurus preview; stages and restarts it whenever a registered input changes, until interrupted. |
| `npm run build` | Stages, builds the candidate, validates it and promotes it to `docsite/build/`. |
| `npm test` | Runs the publisher's tests. |
| `npm run typecheck` | Type-checks the TypeScript sources. |
| `npm run check` | Runs typecheck, tests, validate and build in that order. |

`validate`, `build`, `test`, `typecheck` and `check` exit nonzero with a diagnostic on any failure.
`start` exits nonzero with a diagnostic only when its first staging fails.
A later staging failure or a Docusaurus exit is reported while the command keeps waiting for the
next change, as the [pipeline](pipeline.md#preview) describes.
An interruption stops it.
When the project has no Concorde configuration, `validate`, `start` and `build` fail first.

**One build at a time.** Callers must serialize the production builds of one docsite for the
whole build, from staging through promotion.
A build deletes the previous candidate and backup and owns the candidate, `docsite/build/` and
the backup directory exclusively until it ends.
A second build started meanwhile can delete the first build's candidate or its recovery backup.
A preview may run beside a build, since each mode stages into its own directory.

## Site manifest

A successful build writes `build-manifest.json` at the root of the
published site:

```json
{
  "schema_version": 23,
  "sourceDigest": "sha256:…",
  "pages": [
    {
      "sourcePath": "specs/concorde/spec-tooling/views/module.md",
      "route": "/specs/concorde/spec-tooling/views/module",
      "contentDigest": "sha256:…",
      "metadataPath": "specs/concorde/spec-tooling/views/module.md.json",
      "metadataDigest": "sha256:…",
      "readingCollection": "module",
      "owner": "module.views",
      "includedBy": [
        {"moduleId": "module.concorde", "reasons": [{"relation": "contains", "id": "module.views"}]},
        {"moduleId": "module.views", "reasons": [{"relation": "owns", "id": "module.views"}]}
      ]
    }
  ]
}
```

`schema_version` is 23. `pages` has one entry per registered document in registry order, with
exactly the fields shown, in that order. `contentDigest` and `metadataDigest` hash the exact bytes
of the reading and metadata files.
`includedBy` lists, in registry order, each Module whose
one-level [Spec context](../../glossary.json#concept.spec-context) selects the document.
Each Module's reasons are sorted by `relation`, `kind` and `id`.
`relation` is `owns`, `contains`, `uses` or `includes`.
An `includes` reason also has `kind` `module` or `document`.
`id` is the Module or document that the relation names.
`includedBy` is the document's selecting Modules, which equal Spec core's `selected-by` index.
This is the same reason shape as the Spec core's context records.
`sourceDigest` is defined in the [pipeline](pipeline.md#source-digest).
A manifest of any other version, or with any difference in these fields, is stale and requires a
fresh build.
The manifest records inputs only. It makes no claim that code satisfies the Specs.
