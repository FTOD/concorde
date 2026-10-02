# Spec interface definitions

The exact files, calls and records of the [Spec core](module.md)
[Module](../../glossary.json#concept.module). The Protocol's Required format (`protocol/format.md`)
defines the entry `module` block, document metadata, identities, anchors and reading syntax; this
document does not repeat it and adds only what Concorde fixes on top of it.

## Project configuration {#project-configuration}

`.concorde/config.json` is a control record that Spec core loads. It holds these fields:

```json
{
  "profile_version": 19,
  "protocol": {"version": "13.2.0", "digest": "sha256:<64 hex digits>"},
  "python": ".venv/bin/python"
}
```

- `profile_version` is the Framework's configuration profile; the loader supports exactly `19` and
  refuses others with `unsupported_profile`. It is a compatibility number of this file and of the
  registry, not a Protocol version.
- `protocol` is the [Protocol binding](../../glossary.json#concept.protocol-binding): the `version`
  from the installed copy's manifest and the SHA-256 digest of that manifest's exact bytes.
- `python` is optional. It names the project's own interpreter, which Method reads and passes to
  Check execution to substitute for `{python}` in a check's `argv`; Spec core accepts it without interpreting it, and
  [initialization](#initialization) records it.

No other field is allowed. The settings earlier profiles kept here live elsewhere, and a field
left from them is refused with an error naming where its setting lives now: the registry is
always `.concorde/specs.json` ([registry file](#registry-file)), the
[configured checks](../../glossary.json#concept.configured-check) are Check execution's
[checks files](../../execution/checks/service.md), and the worker limits and runtime paths are part of the
[worker configuration](../../glossary.json#concept.worker-configuration)
`.concorde/workers.json`, which Workers owns. Spec core only verifies the binding; changing it is an explicit step of Distribution, such as
rebinding a Concorde checkout to its freshly built Protocol.

## Registry file {#registry-file}

The registry file is always `.concorde/specs.json`, a place no setting changes. It is JSON with
exactly two fields:

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
`participates`, in this order, followed by `glossary` in the record of the one Module whose block
declares the project glossary. `id` equals the entry metadata's `document.owner`, `entry` is the
entry's reading path, and every other field equals the same field of the entry's `module` block
(`CHK.registry.mirror`). Records are unique by `id`. Decoding rejects duplicate keys and non-JSON
numeric constants.

## Repository interface {#repository-interface}

The repository has one vocabulary: every query that answers a Protocol concept carries the
Protocol's name for it. A query that takes a Module accepts its identity or its `Module` record.

```python
SpecRepository(project_root, package_root=None, *, registry_bytes=None, document_overrides=None)
SpecRepository.modules -> dict[str, Module]
SpecRepository.module(module_id: str, scenario: str | None = None) -> Module
SpecRepository.root_module -> str
SpecRepository.contained(module) -> tuple[Module, ...]
SpecRepository.document(path: str) -> SpecDocument
SpecRepository.documents(module) -> tuple[SpecDocument, ...]
SpecRepository.definitions(module) -> ModuleDefinitions
SpecRepository.definer(identity: str) -> str | None
SpecRepository.selection(relation: dict) -> tuple[str, ...]
SpecRepository.meaning_text(module_id: str, meaning: str) -> str | None
SpecRepository.realization_entries(module) -> dict[str, Realization]
SpecRepository.realization_for_path(module, path: str) -> Realization | None
SpecRepository.fresh() -> SpecRepository
```

Construction reads the configuration, verifies the Protocol binding, reads the registry and loads
every entry and registered document. `package_root` locates the running Concorde package, whose
`protocol/manifest.json` the project copy must equal; it defaults to the package the code is loaded
from. `registry_bytes` and `document_overrides` (a map from member path to bytes) replace the
corresponding files in memory only, so a caller can load a state it has not written; they are never
written.
`fresh()` builds a new repository from the same root and overrides. Construction never consults a
[build manifest](../../glossary.json#concept.build-manifest) or any other output of Distribution.

`modules` maps every registered Module to its `Module` record, in registry order; `module` returns
one: its `id`, `title`, entry path, owned document paths (`documents`), parent, used Module
identities (`uses`), realization entries (`files`) and inclusions (`references`). A `scenario`
must be a scenario the Module owns and never changes the result. An unknown
Module, or a scenario of another Module, fails with a `SpecError`. `root_module` is the first
recorded Module that no other Module contains, and `contained` returns the Modules a Module
`contains`.

`definitions` returns the requirements, scenarios, realizations and contracts the Module's own
documents define, and the concepts whose glossary entries name the Module as owner. `document`
returns one registered reading member with its metadata, owner and digest, and `documents` every
document a Module owns. `definer` returns the reading path of the document defining a node, for a
concept the document its glossary entry names as its explanation, or `None` for an unknown identity.
`selection` returns the documents one `contains`, `uses` or `includes` declaration selects.
`meaning_text` returns the prose a Module relation's `meaning` anchor resolves to.
`realization_entries` maps each declared entry of the Module to its realization, and
`realization_for_path` returns the realization whose most specific entry covers a file; an exact
entry is more specific than any directory entry.

Failures raise Spec tooling's own [error](errors.md): a `SpecError`, or a subclass such as the
[typed values](../../glossary.json#concept.typed-value)' `TypedDataError`, with its code, a concrete
message, its location, the reason it is an error, a remediation and its causes. No call writes a
file.

### Loading failures {#loading-failures}

A repository opened for consumers refuses the project, raising a `SpecError`, on any of these
problems. When the [Spec](../../glossary.json#concept.spec) structure is at fault, the error counts
the fatal problems and carries every one of them as a cause, each with its path and the statement of
the check it fails:

- an unreadable configuration or registry, a configuration without `profile_version` or `protocol`
  or with a field other than those and `python`, a field of an earlier profile (`registry`,
  `checks` or `workers`), or a registry with malformed or duplicate records;
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

```python
SpecRepository.spec_context(query_id: str) -> SpecContext
SpecContext.paths -> tuple[str, ...]
SpecContext.value -> dict
SpecRepository.recheck_context(context: SpecContext) -> None
SpecRepository.context_bytes(context: SpecContext) -> dict[str, bytes]
```

`spec_context` accepts a Module identity or a scenario identity; a scenario resolves to its owner.
Any other identity fails with code `invalid_target`. `paths` is the Protocol's `SpecContext`: the
paths of both members of every selected document, without duplicates and sorted. `value` is the
record of that context, a JSON object with:

| Field | Meaning |
| --- | --- |
| `schema_version` | `4` |
| `query_id`, `query_kind` | the queried identity and whether it is a `module` or a `scenario` |
| `module_id` | the Module whose context was selected |
| `registration` | that Module's descriptor, as `module` returns it |
| `reading_entry` | that Module's entry reading path |
| `documents` | the paths of the documents that Module owns |
| `references` | that Module's inclusions |
| `sources` | one record per selected member, sorted by path |
| `terms` | one record per selected glossary entry, sorted by concept identity |

Each source record has `document_id`, `path`, `owner` (the defining Module, never the selecting
one), `role` (`reading` or `metadata`), `digest` (SHA-256 of the exact bytes, as `sha256:` plus 64
lowercase hexadecimal digits) and `reasons`: every relation that selected the document, each
recorded as the Protocol relation and its target, sorted by relation, kind and identity:

| Reason | Recorded when |
| --- | --- |
| `{"relation": "owns", "id": M}` | the queried Module M owns the document |
| `{"relation": "contains", "id": N}` | a `contains` of child N selected it |
| `{"relation": "uses", "id": N}` | a `uses` of provider N selected it |
| `{"relation": "includes", "kind": "module" or "document", "id": X}` | an `includes` of Module or document X selected it |

Each term record is `{"entry": E, "reasons": R}`: `E` is the concept's whole glossary entry as
written, and `R` every declaration that selected it, sorted by relation and identity:

| Reason | Recorded when |
| --- | --- |
| `{"relation": "owns", "id": M}` | the queried Module M owns the concept |
| `{"relation": "mentions", "id": D}` | a selected document D, or the definition of a selected concept D, links it |
| `{"relation": "relies_on", "id": N}` | a `contains` or `uses` of N lists it in `relies_on` |
| `{"relation": "relates", "id": S}` | a `relates` from S declared in a selected document or in a selected entry targets it |
| `{"relation": "narrows" or "supersedes", "id": C}` | the selected concept C narrows or supersedes it |

Two relations that select the same document are both recorded, so removing a redundant one changes
the record and the [context identity](../../glossary.json#concept.context-identity). No other reason
exists: a file shared with another Module adds no document. No source record carries file content; a
consumer reads the file the record names and can check its digest. A member that is not valid UTF-8
or cannot be read fails the resolution.

`recheck_context(context)` recomputes the record from the current files and fails with
`stale_context` when anything differs; `context_bytes(context)` rechecks and returns the exact bytes
of every source.

### Boundary sets and impact indexes {#boundary-sets}

The repository answers every set and index of the Protocol's Boundaries (`protocol/boundaries.md`)
and [Context](../../glossary.json#concept.context) (`protocol/context.md`) chapters for a Module,
computed from declarations alone:

| Set or index | Returns | Repository query |
| --- | --- | --- |
| [Spec context](../../glossary.json#concept.spec-context) | both members of each owned and selected document, sorted, with the selecting relations | `spec_context(...).paths`, `spec_context` |
| [External context](../../glossary.json#concept.external-context) | per external inclusion: the entry, whether it is a directory, whether it exists, the readable files below it and one digest over their paths and bytes | `external_context`; `external_inclusions` lists the declared entries, `external_files` and `external_digest` expand and digest one entry |
| Implementation context | the names of the files the realizations bind | `implementation_context`; `bound_files` lists the same files |
| Spec scope | both members of each owned document, and the project glossary, of whose entries only those the Module owns or adds are its to change | `spec_scope` |
| Implementation scope | the realization entries; a directory entry covers every present and future file below it | `implementation_scope`; `missing_entries` lists the entries not on disk, which `CHK.binds.exists` reports |
| ProjectImplementation | the names of the files every Module's realizations bind and every Module's external inclusions; the same for every Module | `project_implementation` |
| selected-by | the Modules whose Spec context contains a document | `selected_by` |
| referenced-by | the declarations that name a concept, requirement, scenario or contract, each with its Module | `referenced_by` |
| implemented-by | the Modules whose realizations bind a path or list it as an entry | `implemented_by` |
| binding Modules | per other Module, the files both it and this Module bind | `shared_files` |
| covered-by | the verification declarations that name a scenario; `coverage` answers it for every scenario of a Module | `covered_by`, `coverage` |
| changed definitions | between two repositories: the documents whose members differ, and the nodes whose definitions differ | `changed_documents(old, new, paths=None)`, `changed_nodes(old, new, paths)` |

`boundary_sets(module)` returns all five sets of one Module at once, together with
ProjectImplementation, as a `BoundarySets` record, whose `writable(path)` answers whether a path
lies in the Spec scope or is covered by the implementation scope. `impact(*, documents=(), nodes=(),
paths=())` returns every Module that writing the given documents, nodes or files concerns: the
readers of the documents, the Modules referencing the nodes and the Modules binding the files.
`shared_files` is computed from entries alone: an exact entry both Modules list, an exact entry of
one below a directory entry of the other, or the inner of two nested directory entries.
`scope_roots(entries)` turns entries into permission roots by dropping trailing slashes.

`changed_nodes` compares a node by its definition: a requirement or scenario by its defining
section, a contract by its fence, a concept by its glossary entry, a
realization by its record, and a Module by its entry's `module` block. It takes the member paths to
compare, so a caller can restrict it to the documents a change touched.

A `uses` or `contains` with `relies_on` selects the target's entry and the documents defining the
listed nodes, a concept's being the document its glossary entry names as its explanation; without
it, every document the target owns. An `includes` of kind `document` selects
that document; of kind `module`, every document that Module owns. Selection never follows the
selected Modules' own relations.

### Implementation exclusions {#implementation-exclusions}

A directory entry binds every regular file below it except files inside a directory named
`node_modules`, `__pycache__`, `.venv`, `build` or `dist`, files and directories whose names begin
with a dot, files ending in `.pyc` or `.log`, and symbolic links. External material is expanded by
the same rule and additionally excludes media and archive files by suffix: images (`.gif`, `.png`,
`.jpg`, `.jpeg`, `.webp`, `.svg`, `.ico`), video (`.mp4`, `.webm`), fonts (`.woff`, `.woff2`,
`.ttf`, `.otf`), `.pdf`, archives (`.zip`, `.gz`, `.tar`, `.tgz`, `.bz2`, `.xz`, `.7z`) and
packaged binaries (`.jar`, `.whl`, `.so`, `.dylib`, `.dll`). A path is never bound when it lies
under `.concorde/` or `generated/`.

## Grants {#grants}

```python
grant(repository, modules: Sequence[str], task_type: str) -> Grant
Grant.value -> dict
context_identity(repository, modules: Sequence[str]) -> str
```

`grant` takes a repository loaded from the worktree whose Specs decide, a nonempty list of
registered Module identities and one [task type](../../glossary.json#concept.task-type).
`Grant.value` is:

```json
{
  "task_type": "implement",
  "modules": ["module.a"],
  "context_identity": "sha256:<64 hex digits>",
  "entries": [
    {"path": "specs/a/module.md", "level": "ro"},
    {"path": "specs/a/module.md.json", "level": "ro"},
    {"path": "src/a/", "level": "rw"}
  ],
  "terms": [
    {"id": "concept.hold", "title": "Hold", "owner": "module.a",
     "definition": "Stock withheld until a submission succeeds or expires.",
     "explanation": "specs/a/module.md#concept.hold"}
  ],
  "glossary": "specs/glossary.json"
}
```

`terms` is the union of the glossary entries of the bound Modules' terms, each entry whole and
sorted by identity; it is how a worker learns the definitions its documents link without reading
the glossary file. `glossary` is the project glossary's path, or `null` when no Module declares
one, so that the [write audit](../../glossary.json#concept.write-audit) can hold a change of it to
the bound Modules' entries.

`task_type` is one of `understand`, `specify`, `implement`, `test`, `review-spec`, `review-code`,
`code-to-spec` and `review-architecture`. `modules` is sorted and without duplicates. Each entry's `level` follows the
table below, where a dash means the set contributes nothing:

| Task type | Spec context | Implementation context | Implementation scope | Spec scope | External context | ProjectImplementation | ProjectSpecification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `understand` | `ro` | `names` | — | — | `ro` | — | — |
| `specify` | `ro` | `names` | — | `rw` | `ro` | — | — |
| `implement` | `ro` | `names` | `rw` | — | `ro` | `ro` | — |
| `test` | `ro` | `names` | `ro` | — | `ro` | `ro` | — |
| `review-spec` | `ro` | `names` | — | — | `ro` | — | — |
| `review-code` | `ro` | `names` | `ro` | — | `ro` | `ro` | — |
| `code-to-spec` | `ro` | `names` | `ro` | `rw` | `ro` | `ro` | — |
| `review-architecture` | `ro` | `names` | — | — | `ro` | `names` | `ro` |

The sets contribute these paths:

- Spec context and Spec scope: both members of each document, as exact paths. Spec scope also
  contributes the project glossary, so a task that writes Specs may change the entries its bound
  Modules own; which entries it changed is checked after the task, not by the grant.
- Implementation context: the files the realizations bind, expanded below directory entries by the
  [exclusion rule](#implementation-exclusions).
- Implementation scope: each realization entry as declared; an entry ending with `/` covers every
  present and future file below it under the exclusion rule.
- External context: each external inclusion's declared path; a directory path ends with `/` and
  covers the readable files below it.
- ProjectImplementation: the files every registered Module's realizations bind and their external
  inclusions, so a task that reads code reads the code it uses and the
  code that uses it. Only the bound Modules' own scopes are ever `rw`.
- ProjectSpecification: both members of every document of every registered Module and the project
  glossary, as exact paths, so that a `review-architecture` task reads every Module's Specs and
  every term; the glossary is then listed `ro`.

The computation runs in this order. Over every bound Module and every set, a path receives the
highest level assigned to it, ordered `names`, `ro`, `rw`. If an `rw` entry would then cover a file
a Module outside the grant also binds, the computation fails with `shared_file` (below). An
installed file, one that the installation record `.concorde/install.json` lists under `files`
outside `.concorde/` and not under `amended`, is then lowered from `rw` to `ro`. Finally, an exact
path that a directory entry of equal or higher level covers is dropped. Entries are unique and
sorted by path. A path covered by no entry is denied.

Computing fails, returning no grant and writing nothing, with a `SpecError` whose `code` is the one
below; its message names the offending value, for `unknown_module` also every registered Module:

| Code | When |
| --- | --- |
| `invalid_input` | the Module list is empty or repeats a Module |
| `invalid_task_type` | the task type is none of the eight |
| `unknown_module` | a Module identity is not registered |
| `shared_file` | an `rw` entry covers a file that a Module outside `modules` also binds; the message names each such file and Module |

A shared file is found with the binding-Modules index (`shared_files`), so an exact entry, an exact
entry below a directory entry and nested directory entries are all detected.

`context_identity(repository, modules)` returns `sha256:` and 64 lowercase hexadecimal digits over
the canonical JSON of `{"modules": [...]}`, one item per bound Module in sorted order:
`{"module": M, "sources": S, "terms": T, "external": E}`, where `S` and `T` are the `sources` and
`terms` lists of `spec_context(M).value` ([Spec context records](#spec-context-records)) and `E` lists
`{path, digest}` for each of M's external inclusions, sorted by path. `grant` sets the grant's
`context_identity` to this value for its Modules.

`concorde grant --root <worktree> --modules <id>[,<id>...] --type <task type>` loads the
repository at the given root, computes the grant and prints the common command-line envelope with
`tool: "grant"`, `status` `success` with the grant value as `result`, or `invalid` with the
failure's [error record](errors.md) as `error`. The exit code is 0 for `success`, 1 for `invalid`
and 3 for `failed`, the status of a command line that could not run, as for `spec-validation`.

## Validation result {#validation-result}

```python
validate_repository(root, target_id=None, package_root=None, *, registry_bytes=None,
                    document_overrides=None) -> ToolResult
```

`concorde spec-validation [target]` prints this result as JSON, with one addition of the command's
own: in a project that a `concorde update` marked as not yet validated, the command adds
Distribution's update findings to it and removes the mark once the project validates, as
[Distribution](../../distribution/module.md#updating-an-installed-concorde) says. This function and
every other caller of it return the result without those findings and never touch the mark. The result has
`tool: "spec-validation"`, `target` (the requested Module or `.`), `status` (`success` or
`invalid`, or `failed` when the command could not do its work), `artifacts` (the assessed Spec
member paths and the project glossary), `findings` and `result`. A target must name a registered
Module, otherwise the call fails with `unknown_target`; it does not narrow the run, which checks the
whole project and reports every finding whatever the target.

A finding has `rule_id`, `strictness` (`error` or `warning`), `source` (a project-relative path),
`message` and `remediation`, and optionally `line`, `column` and `subject_id` (the node identity
concerned). For every Protocol check, `rule_id` is the check's identity, such as
`CHK.relies-on.linked`. Findings that Concorde adds beyond the Protocol use `CONCORDE-` rule
identities:

| Rule | Strictness | Meaning |
| --- | --- | --- |
| `CONCORDE-LINK-001` | error | a link fragment shaped like a requirement, scenario, realization or contract identity names no definition in the linked document |
| `CONCORDE-COVERAGE-001` | warning | no test declares a scenario of a Module that binds files |
| `CONCORDE-COVERAGE-003` | error | a bound test cannot be parsed, or a declaration in it is malformed; reported per file |
| `CONCORDE-SOURCE-008` | error | the configuration, registry or Protocol binding cannot be read, so nothing else was checked; the message is the load error's, the remediation carries its remediation and reason, and `result.load_error` holds its [error record](errors.md) |

`result` holds `summary` (the counts of errors and warnings), `source_digest` (a digest over the
paths and digests of the configuration, the registry, every assessed document member, the project
glossary and the Protocol binding), `claims` (the kinds
of structure the run checked) and `semantic_completeness: "not_proven"`. No other Module's records
enter the digest, nor do the files Modules bind, the list of version-controlled files or the tests
scanned for verification declarations, so a finding about bindings, unbound files or scenario
coverage can change while `source_digest` stays the same.

The command-line envelope is canonical JSON with `schema_version: 4`, the fields above and `error`:
`null` when the command did its work, otherwise the [error record](errors.md) of its failure,
including a malformed command line (`invalid_input`) and an unexpected failure
(`unexpected_error`). Findings are sorted by rule, source, line, column and message, and artifacts
are sorted. The exit code follows the status, as for every command that prints this envelope: 0
for `success`, `proposal` and `unchanged`, 1 for `invalid`, 2 for `conflict` and 3 for `failed`.


## Registry command {#registry-command}

`concorde registry --write` loads every recorded Module's entry and rewrites the registry so that
each record's `title`, `owns`, `contains`, `uses`, `includes`, `participates` and, where the block
declares it, `glossary` equal the entry's `module` block. It keeps the records' order and their `id`
and `entry`, and adds or removes no record. It writes through a [file
transaction](../../glossary.json#concept.file-transaction) and reports `unchanged` when nothing
differs. With `--check` it writes nothing and reports one `CHK.registry.mirror` finding per record
that differs. The command fails, with the [error record](errors.md) naming the registry or the entry
and its cause, and writes nothing when the registry or an entry cannot be read.

## Verification declarations {#verification-declarations}

A [verification declaration](../../glossary.json#concept.verification-declaration) is written in the
test's own source. A Python test uses the `verifies` decorator from `concorde.spec.verification` on
a test function or method; a TypeScript test uses an own-line comment directly above its `it`,
`test` or `describe` call, with several identities separated by commas or spaces:

```python
from concorde.spec.verification import verifies

@verifies("scenario.checkout.submit", "scenario.checkout.retry")
def test_submit_once():
    ...
```

```typescript
// verifies: scenario.checkout.render
it("renders the page", () => {});
```

At run time the decorator only attaches the identities to the test function and returns it
unchanged, and it refuses an argument that does not begin with `scenario.`.

The scanner reads bound files ending in `.py`, `.ts`, `.tsx`, `.mts` or `.cts`, never importing,
compiling or running them. It parses a Python file and reads its module-level functions and the
methods of classes at any class nesting; a function nested inside another function is a helper and
is ignored. Every argument must be a string literal beginning with `scenario.`. It reads a
TypeScript file line by line, as UTF-8 with undecodable bytes replaced, so a TypeScript file never
fails to parse: a declaration is an own-line comment whose text after the comment marker begins
with `verifies:`; it applies to the next `it`, `test` or `describe` call, whose title names the
declaring test. A declaration that names no scenario, a declaration comment that no test call
follows, an argument that is not a scenario identity, and a Python file that does not parse are
`CONCORDE-COVERAGE-003` errors for that file; the scanner then continues with the next file. Each
declaration yields `{scenario_id, path, line, name}`.

## Typed values {#typed-values}

Spec core's own copy of the [typed value](../../glossary.json#concept.typed-value) format the
[Kernel's contracts](../../kernel/contracts.md#typed-values) define, kept in Spec core's code so that
the spec part depends on no other part, and raising Spec tooling's own errors. A typed value is a
closed JSON object `{"type_id": ..., "schema_version": ..., "data": ...}`. Types are registered by
their owners within the spec part, Spec core, the Spec MCP server and Views; Spec core registers only
its own.

```python
register(type_id: str, version: int, schema: dict) -> None
typed_schema(type_id: str) -> dict
typed(type_id: str, data: dict) -> dict
validate_typed(value, expected: str | None = None, field: str = "") -> dict
```

`register` adds a type. `type_id` is a nonblank name such as `concorde-project-proposal`, `version`
a positive integer and `schema` a schema admitted by the offline subset below, describing `data`.
Registering an identity already registered with the same version and an equal schema changes
nothing; with another version or schema it fails with `duplicate_type` and leaves the existing
registration in force. Owners call `register` when their own code is loaded. Spec core never imports
an owner, so a caller that checks a value must have loaded the code of the value's owner.

`typed_schema(type_id)` returns a schema fragment that matches a whole typed value of that type:
its `type_id`, its registered `schema_version` and its `data`. The fragment refers to the type by
name and is resolved when a value is checked, so a registered schema may embed another owner's type
without importing it; a reference to a type that is still unregistered at check time fails with
`unknown_type`.

`typed` builds and checks a value at the registered version of its type; `validate_typed` checks
an existing one and, with `expected`, its type. A value with another version fails with
`unsupported_version`, an unregistered type with `unknown_type`, a value of the wrong type where
`expected` is given with `incompatible_handoff`, and any other mismatch with `invalid_field` naming
the JSON pointer of the offending field. A checked value is returned as a deep copy.

The `data` is checked as JSON Schema checks it, for the keywords a registered schema may use. An
object admits keys its `properties` do not name unless its `additionalProperties` is `false`, and
checks them against `additionalProperties` when that is a schema; `obj` therefore spells
`additionalProperties: false` to close its objects. `number` admits integers and finite
non-integral numbers and `integer` only integers, neither a boolean, and `minimum` and `maximum`
bound both. `pattern` matches anywhere in the string unless it is anchored. `const` and `enum`
compare values with their JSON type, so `true` is not `1`. Each keyword applies to the kind of value
it constrains, whether the schema names a `type` or not. Beyond JSON Schema, a string whose schema
sets `minLength` must not consist of whitespace only. A registered schema may use every keyword of
the offline subset below except `$defs`, `oneOf`, `allOf`, a list of types and a `$ref` other than
`typed_schema`'s, which the checker does not evaluate: registering one fails with `invalid_input`,
so that no registered type promises more than its values are checked for.

The shared building blocks are `obj(properties, optional=())` (a closed object whose listed
properties are required unless optional), `array(items, unique=False)`, `STRING` (a nonempty
string), `PATH` (a canonical project-relative path), `DIGEST` (`sha256:` and 64 lowercase
hexadecimal digits) and `ARTIFACT` (`{id, path, digest}`).

```python
decode(text: str) -> Any
canonical(value: Any) -> str
safe_path(value: str, field: str = "") -> str
checked_path(project: Path, relative: str, field: str = "") -> Path
artifact(root: Path, identifier: str, relative: str) -> dict
verify_artifacts(root: Path, value, field: str = "") -> None
```

`decode` parses JSON, rejecting duplicate keys and non-finite numbers. `canonical` writes sorted,
compact JSON. `safe_path` accepts only canonical project-relative POSIX paths: nonempty, no leading
`/`, no backslash, colon or control character, and no empty, `.` or `..` component. `checked_path`
additionally refuses a path any of whose components is a symbolic link. `artifact` returns
`{id, path, digest}` for a file below the given root and fails with `stale_reference` when it does
not exist; `verify_artifacts` walks a value and fails with `stale_reference` when any embedded
artifact's bytes changed. The caller chooses the root: Spec core never decides in which worktree
a record lives. Failures raise `TypedDataError(ValueError)` with `code` and `field`.

### Offline schema subset {#offline-schema-subset}

The schema and example of every `concorde-contract` fence, and every registered schema, are checked
with an offline JSON Schema subset:

```python
admit(schema, root: dict | None = None) -> None
validate(value, schema, field: str = "", *, root: dict | None = None, depth: int = 0) -> None
```

A schema is an object or a boolean. The admitted keywords are `$schema`, `$id`, `$defs`, `$ref`,
`title`, `description`, `examples`, `default`, `type`, `properties`, `required`,
`additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`, `maxLength`,
`pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and `format`. In a
contract fence, `$ref` must be `#/$defs/<name>` into the same root schema; any other reference is
refused, so no schema can load a Spec document or a remote resource. The only `format` is
`project-path`, checked by `safe_path`. Integers satisfy `number`; booleans do not. Unknown
keywords, invalid bounds and unresolved references fail admission, and nesting deeper than 100
levels fails validation, with a `ContractError(ValueError)` carrying the JSON pointer of the
problem.

### Front matter

Instruction files begin with a constrained YAML front matter block, which
`concorde.spec.frontmatter.parse_document` reads: space-indented keys, scalars, lists, nested maps
and JSON-style inline collections. Tags, anchors, aliases, merge keys, block scalars and duplicate
keys are refused with a `FrontMatterError` naming the file and line.

## File transactions {#file-transactions}

Spec core's own copy of the [file transaction](../../glossary.json#concept.file-transaction) the
[Kernel's contracts](../../kernel/contracts.md#file-transactions) define, with Spec tooling's own
errors:

```python
file_change(root: Path, path: str, content: str) -> dict
apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]
```

`file_change` returns `{path, before_digest, content}`, where `before_digest` is the digest of the
file's current bytes or `null` when it does not exist. `apply_files` requires a nonempty list of
such changes with unique paths, every path in `allowed` and every content a string. It fails with
`invalid_proposal` for a malformed change set, `permission_denied` for a path outside `allowed`, and
`stale_proposal` when a file's current bytes do not match its `before_digest`, checked once before
any write and again just before each write. Each file is written to a temporary file in its
directory, flushed and renamed into place. After all writes, the optional `verify` callable runs;
if it or any write raises, every written file is restored to its original bytes, through the same
temporary file and rename, or removed if it did not exist. It returns the written paths in order.

A failure then propagates as follows:

- an operating-system error of a write becomes a `SpecError` with the code `system_error`, the
  file's path and the message that every file written so far was restored, whose one cause is the
  `system_error` record of the operating system's error;
- a `SpecError` of a write, such as `stale_proposal`, and any exception `verify` raises propagate
  unchanged, so a caller's own check error reaches the caller as the caller raised it;
- when the operating system refuses a restore, the other restores are still attempted and the
  transaction fails with a `SpecError` of code `system_error` that names every file not restored
  and says each still holds the new content; its causes are the first failure (unchanged when it
  is a `SpecError`, otherwise its `system_error` or `unexpected_error` record) followed by one
  `system_error` record per refused restore.

These guarantees hold for failures the process observes as an exception. A killed or interrupted
process restores nothing: each file already renamed into place keeps its new content, every other
file keeps its original bytes, and `.concorde-write-` temporary files may remain beside them.

## Initialization {#initialization}

```python
initialize(root: Path, package: Path, data: dict) -> dict
```

Initialization is deterministic; it runs no model and selects no context. `root` is the project
and `package` the running Concorde package. `data` is one of:

- `{"action": "propose", "name": ..., "target_id": ..., "python": ...}`: `name` is required and
  nonblank; `target_id`, the root Module's identity, defaults to `module.project`; `python`, the
  project's interpreter, is optional and nonblank when given. Propose fails with
  `already_initialized` when `.concorde/config.json` exists and with `not_installed` when the
  installer's [Protocol copy](../../glossary.json#concept.protocol-copy) is missing.
- `{"action": "apply", "proposal": ..., "proposal_digest": ...}`: `proposal` is the complete
  `concorde-project-proposal@2` value propose returned, with closed data `{action: "initialize",
  base_digest: null, source_digest, files: [{path, before_digest, content}]}`, and
  `proposal_digest` the digest propose returned for it.

Any other action, a propose without a name and an apply without both fields fail with
`invalid_input`. Spec core registers the proposal type.

`source_digest` is the `sha256:` digest of the canonical JSON of `{protocol, entries}`: the binding
of the installed Protocol copy and the realization entries the proposal binds (below), that is, the
project state the proposal was computed from. `proposal_digest` is the `sha256:` digest of the
canonical JSON of the proposal typed value.

Propose returns `{status: "proposed", proposal, proposal_digest, files}` with the typed proposal,
its digest and its ordered paths. Apply returns `{status: "applied", proposal: null,
proposal_digest: null, files}` with the written paths.

The proposal contains five files, each with `before_digest: null`: `.concorde/config.json` with
profile 19, the binding of the installed Protocol copy and `python`, which is the interpreter named
on propose as given, otherwise the first of `.venv/bin/python` and `venv/bin/python` that exists,
and absent when there is none;
`.concorde/specs.json` with one record for the root Module; `specs/project/module.md` with its
metadata; and the empty project glossary `specs/project/glossary.json`, beside the entry. The entry
follows the reading order the Protocol's writing guidance recommends, in three sections: Purpose;
Not yet specified, which says that the project's core concepts, behaviour and architecture are not
yet specified; and Parts, which says that the root contains, uses and includes nothing yet, explains
its realizations and is where the children are explained once it has some. Its metadata declares the `module` block with the entry as the
only owned document, empty relation arrays and the glossary, and the glossary holds no concept.

When the project already has files, the metadata defines one realization,
`realization.<local>.existing-files` titled Existing project files, where `<local>` is the last
segment of the root Module's identity. Its entries cover every file that version control tracks or
leaves untracked without ignoring, except the proposed document members, files under `.concorde/`,
generated and build outputs, and paths inside submodules. A file directly under the project root is
an exact entry; a top-level directory is one directory entry, unless it holds a document member or a
file of the Concorde installation, in which case its files are exact entries, as are files the
exclusion rule would skip. The entry explains this realization and says it promises nothing about
the files. A project with no files gets no realization.

The files `.concorde/install.json` lists under `files` that lie outside `.concorde/`, exist and are
not listed under `amended` are left out of that realization and bound instead by
`realization.<local>.concorde-installation`, titled Concorde installation, which the entry explains
as the agents' configuration the installer replaces on every update. Without a receipt, or without
such files, there is no such realization.

Initialization binds the installed files of its time; the installer, after every later install or
update, **binds the installation** to keep that realization in step with the receipt
([requirements](requirements.md#req.spec.installation-follows-record)). The function
`bind_installation(root)` adds, as exact entries, the receipt's installed files that exist and
that no realization binds by its exact path, removes the entries whose files are gone, and never
touches another realization. When no realization's identity ends in `.concorde-installation` it
creates `realization.<local>.concorde-installation` in the root Module and appends its explaining
paragraph to the root entry. It returns the realization's identity with the entries it `bound`
and `released`, or nothing for a project that is not initialized or whose registry or metadata it
cannot read, which it leaves unchanged.

Apply checks a proposal's shape, the integrity its digest gives and its freshness, not its
provenance: the proposal digest is one any caller can compute, so apply cannot tell a proposal
propose returned from one built to the same shape. Its guarantee is that an applied proposal had
exactly that shape and digest, was computed from the project's current state, wrote only the
allowed files, replaced none, and left a project that validates. It refuses, writing nothing: a
`proposal_digest` that is not the digest of the given proposal; a proposal whose envelope is not
exactly that shape, that lacks the configuration or the registry, whose configuration names a
Protocol binding other than the installed copy's, or that has a non-null
before-digest (all `invalid_proposal`); and a proposal whose `source_digest` differs from the
project's current one, because the project's files changed so that propose would now return a
different proposal (`stale_proposal`). It writes only the configuration, the registry, the
members of the documents the proposed registry lists and the glossary it declares
(`permission_denied` otherwise), through one
file transaction whose final check validates the project; a destination that appeared since the
proposal fails with `stale_proposal`, and a validation error rolls every file back.

## Protocol manifest and binding {#protocol-manifest}

`protocol/manifest.json` records the distributed Protocol bundle:

```json
{
  "schema_version": 1,
  "version": "13.2.0",
  "source_profile": 15,
  "workspace_protocol": 16,
  "assets": [{"path": "generated/protocol/principles.md", "digest": "sha256:<64 hex digits>"}]
}
```

`version` is the Protocol version. `source_profile` and `workspace_protocol` are compatibility
numbers of the bundle sources and of the configuration profile the bundle was released with; the
loader reads neither. The assets are `generated/protocol/principles.md` (the Protocol chapters,
assembled from `prompts/protocol/principles.md`) and `generated/protocol/kinds/module.md` (Spec
writing guidelines: the overview, Required format, Writing guidance and the templates, assembled
from `prompts/protocol/kinds/module.md`). Required format remains in the principles bundle as well,
so each guide includes the syntax its readers need. The bundle sources include nothing but Protocol
text. The installer copies the manifest and the assets into `.concorde/protocol/`. The project's
binding is the manifest's `version` and the digest of the manifest's bytes. The loader reads the
installed copy, checks each asset against its recorded digest, and requires the copy's manifest to
equal the running package's `protocol/manifest.json`; any mismatch is `protocol_mismatch`.
Distribution's build renders the assets and its `protocol-manifest` command recomputes the recorded
digests.
