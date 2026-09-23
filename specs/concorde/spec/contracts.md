# Spec interface definitions

The exact files, calls and records of the [Spec tooling](module.md) Module. The Protocol's
Required format (`protocol/format.md`) defines the entry `module` block, document metadata,
identities, anchors and reading syntax; this document does not repeat it and adds only what
Concorde fixes on top of it.

## Project configuration {#project-configuration}

`.concorde/config.json` is a control record. It holds exactly these fields:

```json
{
  "profile_version": 16,
  "registry": ".concorde/specs.json",
  "protocol": {"version": "11.0.0", "digest": "sha256:<64 hex digits>"},
  "operation_configuration": {
    "type_id": "concorde-operation-configuration",
    "schema_version": 2,
    "data": {"model": "provider/model-id", "thinking": "medium"}
  },
  "checks": [
    {"id": "check.spec.model", "module": "module.spec",
     "argv": ["{python}", "-m", "pytest", "tests/concorde/spec"],
     "timeout_seconds": 120, "inputs": ["src", "tests/concorde/spec"]}
  ]
}
```

- `profile_version` is the Framework's configuration profile; the loader supports exactly `16` and
  refuses others with `unsupported_profile`. It is a Framework compatibility number, not a Protocol
  version.
- `registry` is the project-relative path of the registry.
- `protocol` is the Protocol binding: the `version` from the installed copy's manifest and the
  SHA-256 digest of that manifest's exact bytes.
- `operation_configuration` is the typed worker model selection described in
  [Typed values](#typed-values).
- `checks` lists the configured checks. Each has a unique `id`, the `module` whose promises it
  checks, a nonempty `argv`, a `timeout_seconds` from 1 to 3600 and optional unique project-relative
  `inputs`. Spec tooling only reads and preserves these records, and validation checks that their inputs exist; the Check execution Module runs
  them.

`concorde-configure` rewrites `operation_configuration`, and `protocol` when the developer accepts
the installed Protocol, and keeps every other field, including `checks`, unchanged.

## Registry file {#registry-file}

The registry file is JSON with exactly two fields:

```json
{
  "schema_version": 3,
  "modules": [
    {"id": "module.example", "title": "Example", "entry": "specs/example/module.md",
     "owns": ["specs/example/module.md"], "contains": [], "uses": [], "includes": [],
     "participates": []}
  ]
}
```

Each record has exactly `id`, `title`, `entry`, `owns`, `contains`, `uses`, `includes` and
`participates`. `id` equals the entry metadata's `document.owner`, `entry` is the entry's reading
path, and every field from `title` on, except `entry`, equals the entry's `module` block
(`CHK.registry.mirror`). Records are unique by `id`. Decoding rejects duplicate keys and non-JSON
numeric constants.

## Repository interface {#repository-interface}

```python
SpecRepository(project_root, package_root=None, *, registry_bytes=None, document_overrides=None)
SpecRepository.select(target_id: str, focus_id: str | None = None) -> SpecTarget
SpecRepository.spec_files(query_id: str) -> tuple[str, ...]
SpecRepository.spec_context(query_id: str) -> SpecResolution
SpecRepository.document(path: str) -> SpecDocument
SpecRepository.definitions(target: SpecTarget) -> ModuleDefinitions
SpecRepository.definer(identity: str) -> str | None
SpecRepository.selection(relation: dict) -> tuple[str, ...]
SpecRepository.meaning_text(module_id: str, meaning: str) -> str | None
SpecRepository.realization_entries(target: SpecTarget) -> dict[str, Realization]
SpecRepository.realization_for_path(target: SpecTarget, path: str) -> Realization | None
SpecRepository.entry_target -> str
SpecRepository.fresh() -> SpecRepository
```

Construction reads the configuration, verifies the Protocol binding, reads the registry and loads
every entry and registered document. `package_root` locates the installed Concorde package whose
Protocol the project copy must equal; it defaults to the running package. `registry_bytes` and
`document_overrides` (a map from member path to bytes) replace the corresponding files in memory
only, so a caller can load a candidate state; they are never written. `fresh()` builds a new
repository from the same root and overrides.

`select` returns the Module's descriptor: its `id`, `title`, entry path, owned document paths
(`documents`), parent, used Module identities (`uses`), realization entries (`files`), inclusions
(`references`) and the identities of the configured checks whose `module` is this Module
(`checks`). A `focus_id` must be a scenario the Module owns and never changes the result. An
unknown Module, or a focus of another Module, fails with a `SpecError`.

`definitions` returns the requirements, scenarios, concepts, realizations and contracts the
Module's own documents define. `document` returns one registered reading member with its metadata,
owner and digest. `definer` returns the reading path of the document defining a node, or `None`
for an unknown identity. `selection` returns the documents one `contains`, `uses` or `includes`
declaration selects. `meaning_text` returns the prose a Module relation's `meaning` anchor
resolves to. `realization_entries` maps each declared entry of the Module to its realization, and
`realization_for_path` returns the realization whose most specific entry covers a file; an exact
entry is more specific than any directory entry. `entry_target` is the root Module: the first
recorded Module that no other Module contains.

Failures raise `SpecError(ValueError)` with a `code` and a `field`; path and JSON failures raised by
the typed values keep their own `TypedDataError`. No call writes a file.

### Loading failures {#loading-failures}

A repository opened for consumers refuses the project, raising `SpecError`, on any of these
problems:

- an unreadable configuration or registry, or a registry with malformed or duplicate records;
- a Protocol binding that does not match the installed copy (`protocol_mismatch`) or an
  unsupported profile (`unsupported_profile`);
- an entry whose metadata owner differs from its registry record;
- a failure of `CHK.document.entry`, `CHK.document.pair` or `CHK.document.path`;
- a metadata envelope with the wrong schema version, missing fields or an invalid role;
- two documents with one identity, a failure of `CHK.node.owner` or of `CHK.owns.unique`;
- a `contains`, `uses` or `includes` whose target is unknown;
- a failure of `CHK.contains.single-parent` or `CHK.contains.acyclic`.

Every other problem leaves the repository usable and is reported only by validation. The
validator opens the repository in a collecting mode, in which these problems become findings as
well.

### Spec context records {#spec-context-records}

`spec_files` and `spec_context` accept a Module identity or a scenario identity; a scenario
resolves to its owner. Any other identity fails with code `invalid_target`. `spec_files` returns
the paths of both members of every selected document, without duplicates and sorted, and reads no
document content. `spec_context` returns a `SpecResolution`, whose value is a JSON object with:

| Field | Meaning |
| --- | --- |
| `schema_version` | the record's version |
| `query_id`, `query_kind` | the queried identity and whether it is a `module` or a `scenario` |
| `module_id` | the Module whose context was selected |
| `registration` | that Module's descriptor, as `select` returns it |
| `reading_entry` | that Module's entry reading path |
| `documents` | the paths of the documents that Module owns |
| `sources` | one record per selected member, sorted by path |

Each source record has `document_id`, `path`, `owner` (the defining Module, never the selecting
one), `role` (`reading` or `metadata`), `digest` (SHA-256 of the exact bytes, as `sha256:` plus 64
lowercase hexadecimal digits) and `reasons`, the declarations that selected the document: its own
ownership, or the `contains`, `uses` or `includes` of the selecting Module that selected it. No
source record carries file content; a consumer reads the file the record names and can check its
digest. A member that is not valid UTF-8 or cannot be read fails the resolution.

### Boundary sets and impact indexes {#boundary-sets}

The repository answers every set and index of the Protocol's Boundaries (`protocol/boundaries.md`)
and Context (`protocol/context.md`) chapters for a Module, computed from declarations alone:

| Set or index | Returns | Repository query |
| --- | --- | --- |
| Spec context | both members of each owned and selected document, sorted; `spec_context` adds the selecting declarations | `spec_files`, `spec_context` |
| External context | per external inclusion: the entry, whether it is a directory, the readable files below it and one digest over their paths and bytes | `boundary_sets(...).external_context`, `external_reference_records` |
| Implementation context | the names of the existing files the realizations bind, and of pending exact entries | `boundary_sets(...).implementation_context`, `implementation_files` |
| Spec scope | both members of each owned document | `spec_scope` |
| Implementation scope | the realization entries, pending entries included; a directory entry covers every present and future file below it | `implementation_scope` |
| selected-by | the Modules whose Spec context contains a document | `selected_by` |
| referenced-by | the declarations that name a concept, requirement, scenario or contract, each with its Module | `referenced_by` |
| implemented-by | the Modules whose realizations cover a path | `implemented_by` |
| covered-by | the verification declarations that name a scenario | `covered_by` |

`boundary_sets(module_id)` returns all five sets of one Module at once; its `writable(path)`
answers whether a path lies in the Spec scope or is covered by the implementation scope. The same
functions are available in `concorde.spec.boundaries`, where `impact(repository, *, documents=(),
nodes=(), paths=())` returns every Module that writing the given documents, nodes or files concerns:
the readers of the documents, the Modules referencing the nodes and the Modules binding the files.
Older implementation queries remain for existing consumers: `implementation_entries`,
`implementation_paths`, `missing_entries`, `context_users`, `listing_users`, `affected_modules` and
`covering_modules`.

A `uses` or `contains` with `relies_on` selects the target's entry and the documents defining the
listed nodes; without it, every document the target owns. An `includes` of kind `document` selects
that document; of kind `module`, every document that Module owns. Selection never follows the
selected Modules' own relations.

### Implementation exclusions {#implementation-exclusions}

A directory entry binds every regular file below it except files inside a directory named
`node_modules`, `__pycache__`, `.venv`, `build` or `dist`, files and directories whose names begin
with a dot, files ending in `.pyc` or `.log`, and symbolic links. External material is expanded by
the same rule and additionally excludes media and archive files by suffix: images (`.gif`, `.png`,
`.jpg`, `.jpeg`, `.webp`, `.svg`, `.ico`), video (`.mp4`, `.webm`), fonts (`.woff`, `.woff2`,
`.ttf`, `.otf`), `.pdf`, archives (`.zip`, `.gz`, `.tar`, `.tgz`, `.bz2`, `.xz`, `.7z`) and
packaged binaries (`.jar`, `.whl`, `.so`, `.dylib`, `.dll`). A path is
never bound when it lies under `.concorde/` or `generated/`.

## Validation result {#validation-result}

```python
validate_repository(root, target_id=None, package_root=None, *, registry_bytes=None,
                    document_overrides=None) -> ToolResult
```

`python3 scripts/concorde.py validate [target]` prints the same result as JSON. The result has
`tool: "validate"`, `target` (the requested Module or `.`), `status` (`success` or `invalid`),
`artifacts` (the assessed Spec member paths), `findings` and `result`.

A finding has `rule_id`, `severity` (`error` or `warning`), `source` (a project-relative path),
`message` and `remediation`, and optionally `line`, `column` and `subject_id` (the node identity
concerned). For every Protocol check, `rule_id` is the check's identity, such as
`CHK.relies-on.linked`. Findings that Concorde adds beyond the Protocol use `CONCORDE-` rule
identities:

| Rule | Severity | Meaning |
| --- | --- | --- |
| `CONCORDE-LINK-001` | error | a link fragment shaped like a node identity names no definition in the linked document |
| `CONCORDE-COVERAGE-001` | warning | no test declares a scenario of a Module that binds files |
| `CONCORDE-COVERAGE-002` | warning | a test declares a scenario whose owner does not bind the test |
| `CONCORDE-COVERAGE-003` | error | a bound test cannot be parsed, or a declaration is malformed |
| `CONCORDE-CHECK-001` | error | a configured check's declared input is missing or unsafe |
| `CONCORDE-ISSUE-001` | error | an Issue record cannot be read |
| `CONCORDE-SOURCE-008` | error | the configuration, registry or Protocol binding cannot be read, so nothing else was checked |

Distribution's package validation adds its own findings in Concorde's source checkout.

`result` holds `summary` (the counts of errors and warnings), `source_digest` (a digest over the
paths and digests of the configuration, registry, every assessed document member, the Protocol
binding and the Issue records), `claims` (the kinds of structure the run checked) and
`semantic_completeness: "not_proven"`.

The command-line envelope is canonical JSON with `schema_version: 2` and the fields above;
findings are sorted by rule, source, line, column and message, and artifacts are sorted. The exit
code is 0 for `success` and 1 for `invalid`.

## Registry command {#registry-command}

`python3 scripts/concorde.py registry --write` loads every recorded Module's entry and rewrites the
registry so that each record's `owns`, `contains`, `uses`, `includes` and `participates` equal the
entry's `module` block. It keeps the records' order and their `id`, `title` and `entry`, and adds or
removes no record. With `--check` it writes nothing and reports one finding per record that
differs. The command fails without writing when an entry cannot be read.

## Verification declarations {#verification-declarations}

A Python test declares the scenarios it verifies with the decorator from
`concorde.spec.verification`, on a test function or method:

```python
from concorde.spec.verification import verifies

@verifies("scenario.example.submit", "scenario.example.retry")
def test_submit_once():
    ...
```

A TypeScript test declares them with an own-line comment directly above the test call; several
identities are separated by commas or spaces, and the title of the following `it`, `test` or
`describe` call names the declaring test:

```typescript
// verifies: scenario.example.render
it("renders the page", () => {});
```

The scanner reads bound files ending in `.py`, `.ts`, `.tsx`, `.mts` or `.cts` by parsing them,
never by importing, compiling or running them. In Python it reads module-level functions and the
methods of classes at any class nesting; a function nested inside another function is a helper and
is ignored. Every argument must be a string literal beginning with `scenario.`. A declaration
comment that no test call follows, an argument that is not a scenario identity, and a Python file
that does not parse are errors.

## Typed values {#typed-values}

A typed value is a closed JSON object `{"type_id": ..., "schema_version": ..., "data": ...}`:

```python
typed(type_id: str, data: dict) -> dict
validate_typed(value, expected: str | None = None, field: str = "") -> dict
json_schema(type_id: str) -> dict
decode(text: str) -> Any
canonical(value: Any) -> str
safe_path(value: str, field: str = "") -> str
checked_path(project: Path, relative: str, field: str = "") -> Path
```

`typed` builds and checks a value at the registered version of its type; `validate_typed` checks
an existing one and, with `expected`, its type. Every type's version is fixed; a value with another
version fails with `unsupported_version`, an unregistered type with `unknown_type`, a value of the
wrong type where `expected` is given with `incompatible_handoff`, and any other mismatch with
`invalid_field` naming the JSON pointer of the offending field. Objects are closed unless their
schema gives one schema for all additional keys. A checked value is returned as a deep copy.

The registered types are the host-owned values (the worker model selection, context snapshots,
stage contexts and results, review records, Issue records, plans and tasks) together with the
`<capability>-request` and `<capability>-response` types each capability adapter and each
request-taking Agent declares. `json_schema` exports one type as a self-contained JSON Schema
Draft 2020-12 document; the build writes all exported types into the distributed
`schemas.json` asset.

`decode` parses JSON, rejecting duplicate keys and non-finite numbers. `canonical` writes sorted,
compact JSON. `safe_path` accepts only canonical project-relative POSIX paths: nonempty, no leading
`/`, no backslash, colon or control character, and no empty, `.` or `..` component. `checked_path`
additionally refuses a path any of whose components is a symbolic link. Failures raise
`TypedDataError(ValueError)` with `code` and `field`.

### Worker model selection {#operation-configuration}

`concorde-operation-configuration` version 2 has optional `model` (a Pi `provider/id`), `thinking`
(`off`, `minimal`, `low`, `medium`, `high`, `xhigh` or `max`), `timeout_seconds` (an integer) and
`workers`, a map from a worker name to an object with the same three optional fields. The most
specific setting wins. An absent value keeps Pi's default model and thinking level and the worker
profile's timeout.

### Task metadata values {#task-metadata-values}

These two version-1 values carry task metadata, not implementation content or authority. Their
data objects are closed and every field is required.

| Type | Data | Meaning |
| --- | --- | --- |
| `concorde-task-scope-feedback` | `{tasks_digest, reason: "implementation_boundary"}` | Host feedback naming the exact task list, by the `sha256:` digest of its canonical JSON, whose implementation acceptance must be separated from later Host responsibilities. |
| `concorde-task-identity-constraints` | `{reserved_task_ids: string[]}` | Task identities a fresh task list must not reuse; strings are nonblank and unique, and an empty list is valid. |

Checking them proves only their shape. It does not prove that a digest names the current task
list, that the reservations are complete, or that a phase may accept the value; the calling Host
decides those.

### Offline schema subset {#offline-schema-subset}

The schema and example of every `concorde-contract` fence are checked with an offline JSON Schema
subset:

```python
admit(schema, root: dict | None = None) -> None
validate(value, schema, field: str = "", *, root: dict | None = None, depth: int = 0) -> None
```

A schema is an object or a boolean. The admitted keywords are `$schema`, `$id`, `$defs`, `$ref`,
`title`, `description`, `examples`, `default`, `type`, `properties`, `required`,
`additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`, `maxLength`,
`pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and `format`. `$ref`
must be `#/$defs/<name>` into the same root schema; any other reference is refused, so no schema
can load a Spec document or a remote resource. The only `format` is `project-path`, checked by
`safe_path`. Integers satisfy `number`; booleans do not. Unknown keywords, invalid bounds and
unresolved references fail admission, and nesting deeper than 100 levels fails validation, with a
`ContractError(ValueError)` carrying the JSON pointer of the problem.

### Front matter

Prompt and agent instruction files begin with a constrained YAML front matter block, which
`concorde.spec.frontmatter.parse_document` reads: space-indented keys, scalars, lists, nested maps and
JSON-style inline collections. Tags, anchors, aliases, merge keys, block scalars and duplicate keys
are refused with a `FrontMatterError` naming the file and line.

## File transactions {#file-transactions}

```python
file_change(root: Path, path: str, content: str) -> dict
apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]
confirm_pending_files(root: Path, package_root: Path | None = None) -> tuple[list[dict], list[str]]
```

`file_change` returns `{path, before_digest, content}`, where `before_digest` is the digest of the
file's current bytes or `null` when it does not exist. `apply_files` requires a nonempty list of
such changes with unique paths, every path in `allowed` and every content a string. It fails with
`invalid_proposal` for a malformed change set, `permission_denied` for a path outside `allowed`, and
`stale_proposal` when a file's current bytes do not match its `before_digest`, checked once before
any write and again just before each write. Each file is written to a temporary file in its
directory, flushed and renamed into place. After all writes, the optional `verify` callable runs;
if it or any write raises, every written file is restored to its original bytes or removed if it
did not exist, and the exception propagates. It returns the written paths in order.

`confirm_pending_files` removes from every realization's `pending` the entries that now exist. It
rewrites only the affected metadata members, in one file transaction whose final check requires the
project to load and no other Spec source to have changed meanwhile. It returns the confirmed entries, each with its
Module, realization and path, and the entries that are still missing. The Validation Module calls it in a
candidate before validating, and delivery calls it again for entries created since.

## Initialization {#initialization}

`concorde-init` takes `concorde-init-request` version 3, whose closed data has `action`
(`"propose"` or `"apply"`) and optional `name`, `target_id`, `configuration`, `proposal` and
`run_in_primary` (Request admission's opt-in to apply in the primary worktree):

- `propose` requires `name` (nonblank) and `configuration` (a worker model selection) and accepts
  `target_id`, default `module.project`. It fails with `already_initialized` when
  `.concorde/config.json` exists and with `not_installed` when the installer's Protocol copy is
  missing.
- `apply` requires `proposal`, the complete `concorde-project-proposal` version-1 value that propose
  returned, with closed data `{action: "initialize", base_digest: null, files: [{path,
  before_digest, content}]}`.

It returns `concorde-init-response` version 1 with closed data `{status, proposal, files}`:
`proposed` with the typed proposal and its ordered paths, or `applied` with `proposal: null` and the
written paths. A request with the Host's describe-policy mode is refused with `use_proposal`,
because the proposal is already the preview.

The proposal contains four files, each with `before_digest: null`: `.concorde/config.json` with
profile 16, the registry path, the binding of the installed Protocol copy, the given worker
configuration and an empty `checks` list; `.concorde/specs.json` with one record for the root Module; and
`specs/project/module.md` with its metadata. The entry has the five required sections and says
that the project's responsibility, behaviour and architecture are not yet specified. Its metadata
declares the `module` block with the entry as the only owned document and empty relation arrays,
and no concepts.

When the project already has files, the metadata defines one realization,
`realization.<local>.existing-files` titled Existing project files, where `<local>` is the last
segment of the root Module's identity. Its entries cover every file that version control tracks or
leaves untracked without ignoring, except the proposed document members, files under `.concorde/`,
generated and build outputs, and paths inside symbolic links. A file directly under the project
root is an exact entry; a top-level directory is one directory entry, unless it holds a document
member, in which case its files are exact entries, as are files the exclusion rule would skip. The
entry explains this realization and says it promises nothing about the files. A project with no
files gets no realization.

Apply refuses a proposal whose envelope is not exactly that shape, that lacks the configuration or
the registry, whose configuration names another registry path or a Protocol binding other than the
installed copy's, or that has a non-null digest (`invalid_proposal`). It writes only the
configuration, the registry and the members of the documents the proposed registry lists, through
one file transaction whose final check validates the project; a validation error rolls every file
back.

At the capability boundary the request travels in a `concorde-operation-invocation` version 3 with
`operation_id: "concorde-init"`, and the result is a `concorde-operation-result` version 3. A
refused request has status `blocked` and a failed application has status `failed`, each with
`errors` of `{code, field, message}` and no output.

## Protocol manifest and binding {#protocol-manifest}

`protocol/manifest.json` records the distributed Protocol:

```json
{
  "schema_version": 1,
  "version": "11.0.0",
  "source_profile": 15,
  "workspace_protocol": 16,
  "assets": [{"path": "generated/protocol/principles.md", "digest": "sha256:<64 hex digits>"}]
}
```

The assets are `generated/protocol/principles.md` (the Protocol chapters and the Framework
execution profile, assembled from `prompts/protocol/principles.md`), `generated/protocol/kinds/module.md`
(the Module chapter and the templates, from `prompts/protocol/kinds/module.md`) and
`generated/protocol/schemas.json` (the exported typed-value schemas). The installer copies the
manifest and the assets into `.concorde/protocol/`. The project's binding is the manifest's
`version` and the digest of the manifest's bytes. The loader reads the installed copy, checks each
asset against its recorded digest, and requires the copy's manifest to equal the package's
`protocol/manifest.json`; any mismatch is `protocol_mismatch`. The Distribution Module's
`protocol-manifest` command recomputes the recorded digests from a fresh build.
