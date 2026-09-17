# Views interface contracts

These precise specifications belong directly to the [Views Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Implementation Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Document unit](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Publication candidate](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Promotion](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Composition](../spec/registry.md#terminology) | Defined in Registry. |
| [Implementation binding](../spec/registry.md#terminology) | Defined in Registry. |
| [Entity](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Installation](../distribution/installation.md#terminology) | Defined in Installing and updating Concorde. |

## Publication service

### Scaffold proposal exchange and ownership {#publication-scaffold-proposal-exchange-and-ownership}

The Docsite scaffold command exchanges the following JSON value with its caller. The schema uses
JSON Schema's `type`, `properties`, `required`, `items`, `enum`, `minItems` and
`additionalProperties` vocabulary; the path, digest and content rules below further constrain it.
`--apply --proposal PATH` accepts this value directly, as `{"proposal": value}`, or as
`{"result": {"proposal": value}}` in the propose command's Tool result. PATH is a safe
project-relative JSON file. Proposal generation returns `result.proposal` and a separate
`result.prerequisites` array of `{name, status, detail}` strings for Node and npm; prerequisite
warnings do not install dependencies or change proposal bytes.

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

<a id="participation.document.views.publication.1"></a>

**Interface participation.** This Module has the provided role for `contract.views.scaffold-proposal` version 2 with `external:docsite-caller`.

**When this applies.** When a caller proposes or applies a docsite scaffold.

**Relied-upon guarantee.** [Canonical agreement](#contract.views.scaffold-proposal) defines the exchanged value for this operation.

**Local obligation.** Preserve unrelated files and enforce exact proposal digests before applying any scaffold change.

Version 2 excludes project-owned custom docs and the retired projection publisher from the template.
Version-1 proposals are rejected with instructions to regenerate using `docsite --propose`;
acceptance of old template bytes does not authorize this changed inventory.

The example illustrates the schema, not an applicable package inventory or real digest. Each file
entry has exactly one of `source` and `content`, and paths are unique and sorted. `sha256` hashes
the resolved UTF-8 content bytes. The complete file set is the installed adapter inventory plus
`docsite/site.json`, and, only when `github_pages` is true,
`.github/workflows/deploy-docsite.yml`. An adapter entry's source and destination are its identical
package-relative path; the workflow source is `docsite/scaffold/deploy-docsite.yml` and its only
destination is the workflow path above. Only site identity uses inline `content`, containing the
proposal's `identity` serialized as sorted-key, two-space-indented JSON with a final newline.
No remapping, additional destination, partial inventory, replacement or deletion operation is
owned. In particular, the scaffold does not upgrade an existing consumer site by deleting its old
graph source files; graph removal from this repository's publishing template is a source change,
and successful site builds replace obsolete published output as specified below.

The adapter inventory consists of regular files below the installed package's `docsite/` with
suffix `.css`, `.json`, `.md`, `.svg`, `.ts`, `.tsx` or `.yml`, excluding any directory component
named `node_modules`, `build`, `.generated`, `.docusaurus` or `coverage`, the root-relative
`tests/repository/`, `concorde-only/` and `custom-docs/` subtrees, `scaffold/`, and the root `site.json`. Non-excluded symlinks are
invalid. These template files contain no removed graph feature. Inventory discovery reads the
installed template, never consumer Spec directories. `template_digest` hashes UTF-8 lines sorted
by path, each `path`, a tab and the lowercase SHA-256 hex of its bytes, joined by newlines with a
final newline. The workflow's own file digest also binds its bytes. A changed package digest or
file digest invalidates acceptance.

Identity has `schema_version: 1`, nonempty `title`, absolute HTTP(S) `url`, slash-prefixed and
slash-suffixed `baseUrl`, `organizationName`, `projectName`, and optional absolute HTTP(S)
`repository`. Title defaults to the registered entry Module's title. A GitHub repository supplies
owner/repository names, `https://<owner>.github.io`, and `/<repo>/` (or `/` for the owner's Pages
repository); otherwise defaults are `https://localhost`, `/` and the lowercase title with
non-alphanumeric runs replaced by hyphens, stripped at the ends, falling back to `project`.
Explicit options override their corresponding defaults. Scaffolding omits optional homepage and
Protocol content. `conflicts` lists proposed paths already present, with reason `target already
exists`; it is informational and authorizes no overwrite.

Apply first validates the proposal and its owned inventory. If every destination already equals
the accepted bytes it returns `unchanged` without writing. Otherwise every destination must be
absent: any existing destination, including a mix of exact and absent files, returns `conflict`
without writing. Existing symlinks or unsafe paths reject. The creation transaction checks a null
before-digest (absence) for every destination before staging and again before each write; these
before-digests are transaction state, not fields in the exchanged proposal. A concurrent change
rejects with original-byte recovery for writes already performed. Invalid proposals return
`invalid`; staging failures return `failed`; successful creation returns `success` with the
created paths. Repeating an unchanged proposal is idempotent. No accepted proposal can replace or
delete existing files, including project Specs.

For a Module, its unique local `module.md` is the source entry, independent of collection order.

## Publication pipeline

### Interface signatures {#pipeline-interface-signatures}

```typescript
// plugins/scoped-content/model.ts
requireScoped(root: string): void;
loadScopedRegistry(root: string): ScopedRegistry;
safeRead(root: string, path: string): string;
rewriteLinks(registry: ScopedRegistry, page: Page): string;
hash(value: string | Buffer): string;
legacyAliasRoute(targetId: string, sourcePath: string): string;
primaryDocument(target: Target): string;
// plugins/scoped-content/materialize.ts
scopedSidebar(registry: ScopedRegistry, collection?: ReadingCollection): object[];
materializeScoped(registry: ScopedRegistry): Promise<void>;
// plugins/scoped-content/index.ts
validateScopedBuild(root: string, directory: string): Promise<void>;
scopedContent(context: LoadContext, options: unknown): Plugin<ScopedRegistry>; // default export
// scripts/prepare-publication.ts and scripts/build.ts
preparePublication(projectRoot: string, options?: {mode?: 'preview' | 'build'}): Promise<{registry: ScopedRegistry}>;
buildSite(): Promise<void>;
promoteCandidate(candidate: string, destination: string, backup: string): Promise<void>;
```

`root` is a project-root filesystem path. `safeRead` requires a regular file and returns UTF-8
text; invalid paths throw `Error`, and OS read errors retain their Node error code. `hash` returns
`sha256:` followed by 64 lowercase hexadecimal digits. `requireScoped` returns normally only for
`profile_version === 14`; a missing configuration, a different profile, and a malformed JSON,
unsafe path or read error each throw an `Error` naming the reason. Every entry point of this public
build contract calls it first: publication accepts Profile 14 projects only, and no other profile
has a compatibility rendering path.

`loadScopedRegistry` reads `.concorde/config.json`, which must contain `profile_version: 14` and a
safe relative `registry` path. The registry is
`{schema_version: 5, project_id: string, entry_target: string, targets: Module[], checks: unknown[]}`
with project metadata retained in its source bytes. Each Target has all the fields below. Its IDs
are unique, Module parents are acyclic, the entry target exists and is a Module, and `uses` names
Modules. Each Module has explicit `references` with typed Module/document identities. Every
document unit has one schema-2 `.md.json` companion with document identity/owner/role, entity declarations,
dependency references and participant bindings. Its local meaning anchors resolve into the reading
member, and both sources retain sole ownership in `documents`. Malformed identities, ownership, references, diagrams or contract bindings throw
`Error` before writes. Canonical contracts contain id/version/schema/semantics/example; separate
bindings select them with id/version/role/peer and a local readable explanation of conditions, guarantees and obligations. Included definitions
retain their owner and only the explicit one-level resolution supplies validation context.
The loader never follows links or interface bindings as context edges. Removing graph presentation
does not remove ownership, reference or agreement validation responsibilities.

### Public model types {#pipeline-public-model-types}

```typescript
type Kind = 'module';
type ReadingCollection = 'module' | 'implementation';
interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  references: {kind: "module" | "document"; id: string}[];
  parent: string | null; uses: string[]; files: string[]; checks: string[];
}
interface Page {
  sourcePath: string; route: string; stagedPath: string; title: string; content: string;
  contentDigest: string; documentId: string; owner: string; metadataPath: string; metadataDigest: string;
  includedBy: {targetId: string; reasons: {kind: 'owned' | 'module' | 'document'; id: string}[]}[];
  aliases: string[]; kind: Kind; primaryOf: string | null; readingCollection: ReadingCollection;
}
interface ScopedRegistry {
  schema_version: 21; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[];
}
```

Publication model schema 21 adds the explicitly classified `readingCollection` to each page and
build-manifest entry. It binds both reading and metadata source identities and retains explicit
ownership/inclusion provenance. The Protocol's explicit document role selects the reading collection,
never complete Spec context membership or execution authority. The former graph `edges` projection and `Edge` type
remain absent.
`Target.parent` and `Target.uses` remain registry metadata for navigation, provenance and validation.
This change does not change registry schema 5, Profile 14 or any UA graph format.

A file may be listed by several Modules, unlike a document: schema 5 has no single implementation
owner, so a shared file's reverse lookup is a plain list of listing Modules rather than one
authoritative binding. Target/document order follows the registry. There is exactly one Page per
distinct registered physical document, in the order its sourcePath was first registered. Its
canonical route is `/specs/` followed by its sourcePath with a leading `specs/` segment removed —
only when every registered document's path starts with `specs/` — and its `.md` extension dropped;
a project whose documents are not all under `specs/` keeps full paths. Its staged path is that same
(possibly unstripped) relative path, `.md` extension kept. `loadScopedRegistry` throws when two
documents would map to the same canonical route, when a canonical route equals a legacy alias
route. The former `projections/` source prefix is no longer reserved.

A referenced physical document retains one Page and one sole `owner`. `includedBy` records every
Module whose one-level context includes it, in registry order, with all sorted inclusion reasons.
`kind` is `module`; `primaryOf` is the owner only when this page is its unique module.md, otherwise
null. `readingCollection` comes from required schema-2 `document.role`, with no default, under the
[collection agreement](scenarios.md#scenario.views.reading-collections).
`aliases` lists the legacy-format route for the current owner only:
`/specs/<owner-id>/<key>`, where `key` is the first 16 hex digits of `hash(sourcePath)` after
`sha256:`. References contribute no ownership alias. Removed owners contribute no alias and no
historical aliases are inferred. Retained links to a removed alias must be corrected or fail the
candidate, as specified in [current document references](scenarios.md#scenario.views.publish-legacy-redirect).
The Markdown H1 supplies the title, falling back to the owner's title. `content` excludes front
matter; `contentDigest` hashes complete source bytes. Body Markdown links remain links and never
transclude another file. Ownership and inclusion provenance may be displayed beside the page.

`sourceDigest` hashes JSON serialization of ordered `[path, contentDigest]` pairs: configuration,
registry and both source members of each distinct registered document in first-reference order. A shared physical document
contributes its bytes once; ownership and reference changes are represented by the registry input. The reading digest includes every Mermaid fence; a separate metadata digest covers all machine declarations. Inline diagrams create no
additional source or route record. This is a byte/version identity, not a semantic-completeness
claim.

### Build artifacts, validation and promotion {#pipeline-build-artifacts-validation-and-promotion}

Successful plugin post-build writes this JSON verification artifact in `outDir`:

```typescript
// build-manifest.json
{ schema_version: 21, sourceDigest: string,
  pages: {sourcePath: string; route: string; contentDigest: string; metadataPath: string; metadataDigest: string; readingCollection: ReadingCollection; owner: string; includedBy: Page["includedBy"]; aliases: string[]}[] }
```

Build-manifest schema 21 identifies paired-source publication and explicit reading collections
without an architecture-graph artifact. Older manifests require a fresh build. Publication neither produces nor requires
`architecture-graph.json`; it has no replacement graph artifact. UA export remains independent.

`validateScopedBuild(root, directory)` reloads the current model and reads the manifest from the
candidate directory. It resolves with no value only when its schema version, source digest and
ordered page path/route/digest/readingCollection/owner/includedBy/aliases entries match exactly, and every alias has a redirect
stub in the candidate directory whose content contains that page's canonical route. A stale or
incomplete manifest, missing manifest, missing or non-matching redirect stub, or malformed JSON
rejects. It also validates internal navigation links in the completed candidate after redirect
stubs exist. Every link emitted by the site's published documents must resolve to a candidate page
or other existing site-owned destination; a nonempty fragment targeting a page must identify an
anchor present on the resolved page. Current aliases resolve to their canonical pages for this
check, including fragment validation. This covers same-page fragments, root-relative links and
links produced by Markdown forms that `rewriteLinks` leaves unchanged, as well as rewritten
source-path links. It includes enabled reading collections without adding them to Spec membership
or the registered-page manifest.

Resolve navigation URLs against the referring page and the configured site URL/base URL. A
destination is internal when it has the configured site's origin and its path is within the
configured base URL; same-site absolute URLs within that base URL are internal too. Query strings
do not change the destination page or anchor lookup; preserve them in navigation. Other origins,
same-origin destinations outside the base URL and non-navigation schemes retain their existing
external handling without network availability checks. A missing destination, missing
requested anchor or unresolved redirect rejects with the referring page and destination identified.
Validation never silently removes a reference, infers document ownership and references, repairs source text or
retains historical output to make the check pass.

This function does not repair artifacts or promote output. Route coverage is measured by the
plugin's post-build hook; callers must not manufacture a manifest to bypass that hook.

`buildSite` owns `docsite/.generated/candidate`, `docsite/build` and
`docsite/.generated/previous-build`. It clears the candidate, prepares sources, runs Docusaurus,
validates the built artifacts and only then calls `promoteCandidate`. Validation failure removes
the candidate and preserves the previous build. Successful promotion replaces the previous build
as a directory, so a previously published graph page or dedicated graph artifact cannot survive
by being copied forward. Observed source changes during post-build or fresh validation reject;
the identity describes the inputs actually checked and must be checked again if sources change
before a later independent use of the candidate. Preparation/build callers must exclusively own
these derived output directories through promotion; concurrent materialization or manual edits to
staged/candidate artifacts are unsupported. The identity is a host build record, not a signature
authenticating arbitrary externally supplied HTML.

`promoteCandidate` is a filesystem transaction helper, with caller-supplied distinct candidate,
destination and backup paths on a rename-compatible filesystem. Its caller must have successfully
validated the exact candidate. It clears the disposable backup, moves an existing destination to
backup, moves the candidate to destination, and removes the backup on success. A failed
move/removal attempts to restore the prior destination and rejects; filesystem failure during
rollback can still require operator recovery. The helper itself does not validate Spec contents and
must not be called on unchecked or stale output.

```typescript
requireScoped(projectRoot);       // throws unless the project declares profile_version 14
const registry = loadScopedRegistry(projectRoot);
await materializeScoped(registry); // stage derived assets; not yet a published build
await buildSite();                // integrated prepare/build/validate/promotion path
```

Repeated loading of unchanged inputs preserves identities. Repeated successful builds replace
derived output. No returned model, manifest or successful deterministic check proves that the Spec
supports every possible future task; independent Spec review and actual task gaps remain separate.

## Understand Anything viewer service

### Required installed-runtime contract {#viewer-required-installed-runtime-contract}

The project contains `.concorde/framework/concorde.json`. Its `runtime.venv` is `.concorde/.venv`,
and its viewer declaration supplies package, version, install_relative, entrypoint and graph_paths.
Relative runtime paths cannot be absolute, contain `..`, or contain backslashes. Relevant installed
paths must not be symlinks, and the viewer entrypoint must exist as a file.

The runtime marker `.concorde/.venv/.concorde-runtime.json` has schema_version 2, owner concorde,
viewer_version matching the manifest and viewer_entrypoint matching the declared entrypoint. The
viewer package.json must match the declared package name and version. These startup checks verify
recorded identity; installation is responsible for verifying the downloaded artifact.

The current package pins the official Egonex-AI/Understand-Anything viewer at 2.9.0 and installs it
under `share/concorde/understand-anything-viewer` inside the managed runtime. Its entrypoint is
`node_modules/understand-anything-viewer/bin/viewer.mjs`. The Installation service and Managed
runtime entity supply this state through the reviewed install path. Missing or stale state
requires that installation path to repair it; launch does not provision a replacement runtime
itself.

## UA graph exporter

### Local serialized graph contract {#ua-graph-local-serialized-graph-contract}

The UA graph export command admits the JSON schema below. It uses JSON Schema `type`,
`properties`, `required`, `items` and `minLength`; unspecified properties are admitted and
preserved outside exporter ownership. This is the exporter's local admission contract, not a
claim that the independent viewer validates every field. Node and layer IDs are unique within
their respective arrays. Edge duplicates and unresolved endpoints are not rejected by admission.
Optional node `tags` is an array of strings. Other extension fields, including `filePath`, are
not shape-checked; only a nonempty string `filePath` participates in reuse. Missing `layers` and
`tour` normalize to empty arrays; tour entries are unrestricted JSON values.

```concorde-contract
{
  "id": "contract.views.ua-overlay-input",
  "version": 1,
  "schema": {
    "type": "object",
    "required": [
      "version",
      "project",
      "nodes",
      "edges"
    ],
    "properties": {
      "version": {
        "type": "string"
      },
      "project": {
        "type": "object"
      },
      "nodes": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "id",
            "type"
          ],
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            },
            "type": {
              "type": "string",
              "minLength": 1
            },
            "tags": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        }
      },
      "edges": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "source",
            "target",
            "type"
          ],
          "properties": {
            "source": {
              "type": "string",
              "minLength": 1
            },
            "target": {
              "type": "string",
              "minLength": 1
            },
            "type": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "layers": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "id"
          ],
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "tour": {
        "type": "array"
      }
    }
  },
  "semantics": "Existing graph input for skeleton overlay, subject to local unique-ID, path safety, reserved ownership and generated-ID collision rules. Extension fields outside ownership preserve their JSON values.",
  "example": {
    "version": "1.0.0",
    "project": {
      "name": "Example"
    },
    "nodes": [
      {
        "id": "scan:readme",
        "type": "document",
        "filePath": "README.md"
      }
    ],
    "edges": [],
    "layers": [],
    "tour": []
  }
}
```

<a id="participation.document.views.ua-graph.1"></a>

**Interface participation.** This Module has the required role for `contract.views.ua-overlay-input` version 1 with `external:ua-graph-producer`.

**When this applies.** When overlaying an existing graph produced outside Concorde.

**Relied-upon guarantee.** [Canonical agreement](#contract.views.ua-overlay-input) defines the exchanged value for this operation.

**Local obligation.** Validate the input and preserve fields outside exporter ownership; reject invalid graphs without writes.

New skeletons have `version: "1.0.0"`, `tour: []`, and a `project` object with `name` equal to
the registry project ID, `languages: []`, `frameworks: []`, `description` equal to
`Skeleton graph deterministically exported by Concorde from the project's explicit Spec registry.`,
`analyzedAt` equal to creation time in UTC `YYYY-MM-DDTHH:MM:SSZ`, and `gitCommitHash` equal to
the current Git HEAD or an empty string if unavailable. Creation time and Git HEAD initialize
metadata once; overlays preserve them, so determinism means fixed derivation inputs and metadata,
not identical metadata from independent first exports at different times.

Generated record fields and values are as follows. IDs concatenate literal prefixes and exact
registry IDs or project-relative POSIX paths without hashing or escaping.

| Record | Generated fields |
| --- | --- |
| Module node | `id: "module:<target-id>"`, `type: "module"`, `name`: Module title, `summary`: first prose paragraph of its local module.md Purpose with trimmed lines joined by spaces (empty if absent), `tags: ["concorde-ua-graph", "module"]`, `complexity: "moderate"` |
| Document node | `id: "document:<path>"`, `type: "document"`, `name`: path basename, `filePath`: path, `summary`: registered document ID, `tags: ["concorde-ua-graph", "document"]` |
| Bound-file node | ID prefix `document:` for `.md`, `config:` for `.json`, `.yml`, `.yaml` or `.toml`, otherwise `file:`, followed by path; `type`: prefix without colon, `name`: basename, `filePath`: path, `summary`: path, `tags`: `concorde-ua-graph`, type, and `pending` when its selected entity declares that exact entry pending |
| Module layer | `id: "layer:<target-id>"`, `name`: Module title, `description`: Purpose summary through its first `.` sentence boundary, or all of it if none, `nodeIds`: sorted distinct member node IDs |
| Unlisted layer | `id: "layer:unlisted"`, `name: "Not listed by any Module"`, `description: "File-level nodes from the Understand Anything graph that no Module lists as an implementation file."`, `nodeIds`: sorted distinct selected unclaimed file-like node IDs |

Documents are resolved before implementation files, with one generated record per ID. Thus a
bound Markdown file already generated as a registered document retains that document's summary.
Shared implementation paths use the first registered listing Module's node selection and pending state.
Spec documents always use their sole owner; references never alter their layer or implementation status. Each generated
edge has `source`, `target`, `type`, `direction: "forward"` and numeric `weight`; only the rows
with descriptions below include `description`. There is no generated edge ID.

| Relationship | Source → target | Type, weight, description |
| --- | --- | --- |
| Composition | parent Module → child Module | `contains`, `1.0`, `composes` |
| Dependency | consuming Module → used Module | `depends_on`, `0.8`, local dependency responsibility (fallback `uses`) |
| Document ownership | document → sole owner Module | `documents`, `0.7`, `owned by <target-id>` |
| Explicit context reference | selecting Module → referenced Module or document | `references`, `0.6`, `module` or `document` |
| Implementation listing | listing Module → bound file | `contains`, `0.9`, `<entity-id>: <entity-title>` for that Module's most-specific owning entity |
| Additional file lister | file → each lister after the first | `related`, `0.5`, `also listed by <target-id>` |

Overlay reuse considers surviving foreign nodes after the ownership removal below, matches the
exact `filePath` string, and selects the lexicographically smallest node ID among matching types.
Document-like means type exactly `document`; file-like means type in `file`, `config`, `document`,
`pipeline`, `resource`, `schema`. Reuse retains the entire foreign node unchanged. If no eligible
node exists, generation uses the rules above. A surviving foreign node or layer whose ID collides
with a newly generated node or layer causes rejection, even if its other fields resemble the
generated record. During overlay only, the exporter creates `layer:unlisted` when at least one
surviving file-like path is neither a registered document nor a bound implementation path; it
selects one node per such path using the same reuse order. Existing foreign layers remain under
the declared preservation rules even if they also refer to those nodes.

Serialization orders nodes and layers by ID and edges by `(source, target, type)` using a stable
sort, preserving equal-key edge order. Generated fields use the order shown above; top-level
generated order is `version`, `project`, `nodes`, `edges`, `layers`, `tour`. JSON uses two-space
indentation, literal Unicode and a final newline. Existing object-field order and extension values
are retained; normalization of absent layers/tour occurs once. Check compares these serialized
UTF-8 bytes, including formatting, against the existing file; a missing file is drift and is not
created by `--check`.
