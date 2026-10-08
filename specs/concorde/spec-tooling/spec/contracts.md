# Spec interface definitions

This document defines the exact files, calls and records of the [Spec core](module.md)
[Module](../../glossary.json#concept.module).

The Protocol's Required format (`protocol/format.md`) defines the entry `module` block, document
metadata, identities, anchors and reading syntax.

This document does not repeat it. It adds only what Concorde fixes on top of it.

## Project configuration {#project-configuration}

`.concorde/config.json` is a control record that Spec core loads. It holds these fields:

```json
{
  "profile_version": 19,
  "protocol": {"version": "13.2.0", "digest": "sha256:<64 hex digits>"},
  "python": ".venv/bin/python"
}
```

- `profile_version` is the Framework's configuration profile. The loader supports exactly `19`.
  For other values, the loader refuses the configuration with `unsupported_profile`.
  `profile_version` is a compatibility number of this file and of the registry, not a Protocol
  version.
- `protocol` is the [Protocol binding](../../glossary.json#concept.protocol-binding): the `version`
  from the installed copy's manifest and the SHA-256 digest of that manifest's exact bytes.
- `python` is optional. It names the project's own interpreter. Method reads it.
  Method passes it to Check execution to substitute for `{python}` in a check's `argv`.
  Spec core accepts it without interpreting it. [initialization](#initialization) records it.

No other field is allowed. The settings earlier profiles kept here live elsewhere.
A field left from them is refused with an error naming where its setting lives now:

- The registry is always `.concorde/specs.json` ([registry file](#registry-file)).
- The [configured checks](../../glossary.json#concept.configured-check) are Check execution's
  [checks files](../../execution/checks/service.md).
- The worker limits and runtime paths are part of the
  [worker configuration](../../glossary.json#concept.worker-configuration) `.concorde/workers.json`.
  Workers owns it.

Spec core only verifies the binding. Changing it is an explicit step of Distribution, such as
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
`participates`, in this order. In the record of the one Module whose block declares the project
glossary, `glossary` follows them. `id` equals the entry metadata's `document.owner`.
`entry` is the entry's reading path. Every other field equals the same field of the entry's
`module` block (`CHK.registry.mirror`). Records are unique by `id`. Decoding rejects duplicate
keys and non-JSON numeric constants.

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

Construction performs these steps:

- Reads the configuration.
- Verifies the Protocol binding.
- Reads the registry.
- Loads every entry and registered document.

`package_root` locates the running Concorde package. The project copy must equal its
`protocol/manifest.json`. `package_root` defaults to the package the code is loaded from.
`registry_bytes` and `document_overrides` replace the corresponding files in memory only.
`document_overrides` is a map from member path to bytes. A caller can therefore load a state it
has not written. The overrides are never written.
`fresh()` builds a new repository from the same root and overrides. Construction never consults a
[build manifest](../../glossary.json#concept.build-manifest) or any other output of Distribution.

`modules` maps every registered Module to its `Module` record, in registry order.
`module` returns one record with:

- Its `id`.
- Its `title`.
- Its entry path.
- Its owned document paths (`documents`).
- Its parent.
- Its used Module identities (`uses`).
- Its realization entries (`files`).
- Its inclusions (`references`).

A `scenario` must be a scenario the Module owns. A `scenario` never changes the result.
An unknown Module, or a scenario of another Module, fails with a `SpecError`.
`root_module` is the first recorded Module that no other Module contains.
`contained` returns the Modules a Module `contains`.

`definitions` returns the requirements, scenarios, realizations and contracts the Module's own
documents define.

`definitions` also returns the concepts whose glossary entries name the Module as owner.
`document` returns one registered reading member with its metadata, owner and digest.
`documents` returns every document a Module owns.
`definer` returns:

- For a node, the reading path of the document defining it.
- For a concept, the document its glossary entry names as its explanation.
- For an unknown identity, `None`.

`selection` returns the documents one `contains`, `uses` or `includes` declaration selects.
`meaning_text` returns the prose a Module relation's `meaning` anchor resolves to.
`realization_entries` maps each declared entry of the Module to its realization.
`realization_for_path` returns the realization whose most specific entry covers a file.
An exact entry is more specific than any directory entry.

Failures raise Spec tooling's own [error](errors.md): a `SpecError`, or a subclass such as the
[typed values](../../glossary.json#concept.typed-value)' `TypedDataError`.
The error carries:

- Its code.
- A concrete message.
- Its location.
- The reason it is an error.
- A remediation.
- Its causes.

No call writes a file.

### Loading failures {#loading-failures}

On any of these problems, a repository opened for consumers refuses the project, raising a
`SpecError`:

- An unreadable configuration or registry.
- A configuration without `profile_version`.
- A configuration without `protocol`.
- A configuration with a field other than `profile_version`, `protocol` and `python`.
- A field of an earlier profile (`registry`, `checks` or `workers`).
- A registry with malformed or duplicate records.
- A Protocol binding that does not match the installed copy (`protocol_mismatch`) or an
  unsupported profile (`unsupported_profile`).
- An entry whose metadata owner differs from its registry record.
- A failure of `CHK.document.entry`, `CHK.document.pair` or `CHK.document.path`.
- A metadata envelope with the wrong schema version.
- A metadata envelope with missing fields.
- A metadata envelope with an invalid role.
- Two documents with one identity.
- A failure of `CHK.node.owner` or of `CHK.owns.unique`.
- A `contains`, `uses` or `includes` whose target is unknown.
- A failure of `CHK.contains.single-parent` or `CHK.contains.acyclic`.

When the [Spec](../../glossary.json#concept.spec) structure is at fault, the error:

- Counts the fatal problems.
- Carries every one as a cause.
- Gives each cause its path and the statement of the check it fails.

Every other problem leaves the repository usable. Validation alone reports it.
The validator opens the repository in a collecting mode.
In that mode, these problems become findings as well.

### Spec context records {#spec-context-records}

```python
SpecRepository.spec_context(query_id: str) -> SpecContext
SpecContext.paths -> tuple[str, ...]
SpecContext.value -> dict
SpecRepository.recheck_context(context: SpecContext) -> None
SpecRepository.context_bytes(context: SpecContext) -> dict[str, bytes]
```

`spec_context` accepts a Module identity or a scenario identity. A scenario resolves to its owner.
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

Each source record has `document_id`, `path`, `owner`, `role`, `digest` and `reasons`.
Their details are:

- `owner` is the defining Module, never the selecting one.
- `role` is `reading` or `metadata`.
- `digest` is SHA-256 of the exact bytes, as `sha256:` plus 64 lowercase hexadecimal digits.
- `reasons` records every relation that selected the document as the Protocol relation and its
  target. The records are sorted by relation, kind and identity.

The reasons are:

| Reason | Recorded when |
| --- | --- |
| `{"relation": "owns", "id": M}` | the queried Module M owns the document |
| `{"relation": "contains", "id": N}` | a `contains` of child N selected it |
| `{"relation": "uses", "id": N}` | a `uses` of provider N selected it |
| `{"relation": "includes", "kind": "module" or "document", "id": X}` | an `includes` of Module or document X selected it |

Each term record is `{"entry": E, "reasons": R}`.
`E` is the concept's whole glossary entry as written.
`R` is every declaration that selected it, sorted by relation and identity:

| Reason | Recorded when |
| --- | --- |
| `{"relation": "owns", "id": M}` | the queried Module M owns the concept |
| `{"relation": "mentions", "id": D}` | a selected document D, or the definition of a selected concept D, links it |
| `{"relation": "relies_on", "id": N}` | a `contains` or `uses` of N lists it in `relies_on` |
| `{"relation": "relates", "id": S}` | a `relates` from S declared in a selected document or in a selected entry targets it |
| `{"relation": "narrows" or "supersedes", "id": C}` | the selected concept C narrows or supersedes it |

Two relations that select the same document are both recorded.
Removing a redundant one therefore changes the record and the
[context identity](../../glossary.json#concept.context-identity).
No other reason exists. A file shared with another Module adds no document.
No source record carries file content. A consumer reads the file the record names.
The consumer can check its digest.
When a member is not valid UTF-8 or cannot be read, resolution fails.

`recheck_context(context)` recomputes the record from the current files.
When anything differs, `recheck_context(context)` fails with `stale_context`.
`context_bytes(context)` rechecks the context.
`context_bytes(context)` returns the exact bytes of every source.

### Boundary sets and impact indexes {#boundary-sets}

For a Module, the repository computes every set and index of the Protocol's Boundaries
(`protocol/boundaries.md`) and [Context](../../glossary.json#concept.context) (`protocol/context.md`)
chapters from declarations alone:

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
ProjectImplementation, as a `BoundarySets` record. Its `writable(path)` answers whether a path lies
in the Spec scope or is covered by the implementation scope.
`impact(*, documents=(), nodes=(),
paths=())` returns every Module that writing the given documents, nodes or files concerns:

- The readers of the documents.
- The Modules referencing the nodes.
- The Modules binding the files.

`shared_files` is computed from entries alone. It finds each of these entries:

- An exact entry both Modules list.
- An exact entry of one below a directory entry of the other.
- The inner of two nested directory entries.

`scope_roots(entries)` turns entries into permission roots by dropping trailing slashes.

`changed_nodes` compares a node by its definition:

- A requirement or scenario by its defining section.
- A contract by its fence.
- A concept by its glossary entry.
- A realization by its record.
- A Module by its entry's `module` block.

`changed_nodes` takes the member paths to compare.
A caller can therefore restrict it to the documents a change touched.

With `relies_on`, a `uses` or `contains` selects the target's entry and the documents defining the
listed nodes.
For a concept, this is the document its glossary entry names as its explanation.
Without `relies_on`, a `uses` or `contains` selects every document the target owns.

For kind `document`, an `includes` selects that document.
For kind `module`, an `includes` selects every document that Module owns.
Selection never follows the selected Modules' own relations.

### Implementation exclusions {#implementation-exclusions}

A directory entry binds every regular file below it except:

- Files inside a directory named `node_modules`, `__pycache__`, `.venv`, `build` or `dist`.
- Files and directories whose names begin with a dot.
- Files ending in `.pyc` or `.log`.
- Symbolic links.

External material is expanded by the same rule. It additionally excludes media and archive files
by suffix:

- Images (`.gif`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.ico`).
- Video (`.mp4`, `.webm`).
- Fonts (`.woff`, `.woff2`, `.ttf`, `.otf`).
- Files ending in `.pdf`.
- Archives (`.zip`, `.gz`, `.tar`, `.tgz`, `.bz2`, `.xz`, `.7z`).
- Packaged binaries (`.jar`, `.whl`, `.so`, `.dylib`, `.dll`).

When a path lies under `.concorde/` or `generated/`, it is never bound.

## Grants {#grants}

```python
grant(repository, modules: Sequence[str], task_type: str) -> Grant
Grant.value -> dict
context_identity(repository, modules: Sequence[str], project_specification: bool = False) -> str
```

`grant` takes:

- A repository loaded from the worktree whose Specs decide.
- A nonempty list of registered Module identities.
- One [task type](../../glossary.json#concept.task-type).

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

`terms` is the union of the glossary entries of the bound Modules' terms.
Each entry is whole. The entries are sorted by identity.
Through `terms`, a worker learns the definitions its documents link without reading the glossary
file. When no Module declares a project glossary, `glossary` is `null`.
Otherwise, `glossary` is the project glossary's path.
This lets the [write audit](../../glossary.json#concept.write-audit) hold a change of it to the
bound Modules' entries.

`task_type` is one of `understand`, `specify`, `implement`, `test`, `review-spec`, `review-code`,
`code-to-spec` and `review-architecture`. `modules` is sorted and without duplicates.
Each entry's `level` follows the table below, where a dash means the set contributes nothing:

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
  contributes the project glossary. A task that writes Specs may therefore change the entries its
  bound Modules own. Which entries it changed is checked after the task, not by the grant.
- Implementation context: the files the realizations bind, expanded below directory entries by the
  [exclusion rule](#implementation-exclusions).
- Implementation scope: each realization entry as declared.
  When an entry ends with `/`, it covers every present and future file below it under the exclusion
  rule.
- External context: each external inclusion's declared path. A directory path ends with `/` and
  covers the readable files below it.
- ProjectImplementation: the files every registered Module's realizations bind and their external
  inclusions. A task that reads code therefore reads the code it uses and the code that uses it.
  Only the bound Modules' own scopes are ever `rw`.
- ProjectSpecification: both members of every document of every registered Module and the project
  glossary, as exact paths. A `review-architecture` task therefore reads every Module's Specs and
  every term. The glossary is then listed `ro`.

The computation runs in this order:

- Over every bound Module and every set, a path receives the highest level assigned to it, ordered
  `names`, `ro`, `rw`.
- If an `rw` entry would then cover a file a Module outside the grant also binds, the computation
  fails with `shared_file` (below).
- An installed file is then lowered from `rw` to `ro`.
- Finally, an exact path that a directory entry of equal or higher level covers is dropped.

An installed file meets all these conditions:

- The installation record `.concorde/install.json` lists it under `files`.
- It lies outside `.concorde/`.
- It is not under `amended`.

Entries are unique and sorted by path. A path covered by no entry is denied.

Computing fails with a `SpecError` whose `code` is the one below. It then returns no grant and
writes nothing. The error's message names the offending value. For `unknown_module`, the message
also names every registered Module:

| Code | When |
| --- | --- |
| `invalid_input` | the Module list is empty or repeats a Module |
| `invalid_task_type` | the task type is none of the eight |
| `unknown_module` | a Module identity is not registered |
| `shared_file` | an `rw` entry covers a file that a Module outside `modules` also binds; the message names each such file and Module |

A shared file is found with the binding-Modules index (`shared_files`). This detects all these
cases:

- An exact entry.
- An exact entry below a directory entry.
- Nested directory entries.

`context_identity(repository, modules, project_specification)` returns `sha256:` and 64 lowercase
hexadecimal digits over the canonical JSON of one object.
Its `modules` member has one item per bound Module in sorted order:
`{"module": M, "sources": S, "terms": T, "external": E}`.
The fields are:

- `S`: the `sources` list of `spec_context(M).value`
  ([Spec context records](#spec-context-records)).
- `T`: the `terms` list of `spec_context(M).value`.
- `E`: `{path, digest}` for each of M's external inclusions, sorted by path.

When `project_specification` is false, the object is `{"modules": [...]}`. This ordinary identity
covers the bound Modules' selected sources alone. A document or glossary entry that no bound Module
selects is outside it.

When `project_specification` is true, the object also has the member `project_specification`.
This member lists `{path, digest}` for each path of ProjectSpecification, sorted by path. Each digest
is over the bytes of that path. The list holds both members of every document of every registered
Module. It also holds the project glossary file whole, so every glossary entry is covered.

`grant` sets the grant's `context_identity` to this value for its Modules.
It gives `project_specification` as true exactly when the task type's ProjectSpecification column in
the table above is not a dash. Of the eight task types, only `review-architecture` has that column.

For example, take Module A that uses Module B, and Module D that nothing A declares selects:

- A byte of a document of D changes. The `review-architecture` grant for A then has another context
  identity. The `understand` grant for A and `context_identity(repository, ["module.a"])` keep theirs.
- The definition of a glossary entry that only D's documents link changes. The same three identities
  behave the same way.
- A byte of a document of B that A's Spec context selects changes. All three identities change.

`concorde grant --root <worktree> --modules <id>[,<id>...] --type <task type>` performs these steps:

- Loads the repository at the given root.
- Computes the grant.
- Prints the common command-line envelope with `tool: "grant"`.

For `success`, the envelope has the grant value as `result`.
For `invalid`, it has the failure's [error record](errors.md) as `error`.

The exit codes are:

- 0 for `success`.
- 1 for `invalid`.
- 3 for `failed`.

As for `spec-validation`, `failed` is the status of a command line that could not run.

## Validation result {#validation-result}

```python
validate_repository(root, target_id=None, package_root=None, *, registry_bytes=None,
                    document_overrides=None) -> ToolResult
```

`concorde spec-validation [target]` prints this result as JSON, with one addition of the command's
own. In a project that a `concorde update` marked as not yet validated, the command adds Distribution's
update findings to the result.
Once that project validates, the command removes the mark.
[Distribution](../../distribution/module.md#updating-an-installed-concorde) describes this behaviour.

This function and every other caller of it return the result without those findings.
They never touch the mark. The result has:

- `tool: "spec-validation"`.
- `target` (the requested Module or `.`).
- `status` (`success` or `invalid`, or `failed` when the command could not do its work).
- `artifacts` (the assessed Spec member paths and the project glossary).
- The `findings` field.
- The `result` field.

If a target does not name a registered Module, the call fails with `unknown_target`.
A target does not narrow the run. The run checks the whole project and reports every finding
whatever the target.

A finding has `rule_id`, `strictness`, `source`, `message` and `remediation`.
Its fields have these details:

- `strictness` is `error` or `warning`.
- `source` is a project-relative path.
- `line`, `column` and `subject_id` are optional.
- `subject_id` is the node identity concerned.

For every Protocol check, `rule_id` is the check's identity, such as
`CHK.relies-on.linked`. Findings that Concorde adds beyond the Protocol use `CONCORDE-` rule
identities:

| Rule | Strictness | Meaning |
| --- | --- | --- |
| `CONCORDE-LINK-001` | error | a link fragment shaped like a requirement, scenario, realization or contract identity names no definition in the linked document |
| `CONCORDE-COVERAGE-001` | warning | no test declares a scenario of a Module that binds files |
| `CONCORDE-COVERAGE-003` | error | a bound test cannot be parsed, or a declaration in it is malformed; reported per file |
| `CONCORDE-SOURCE-008` | error | the configuration, registry or Protocol binding cannot be read, so nothing else was checked; the message is the load error's, the remediation carries its remediation and reason, and `result.load_error` holds its [error record](errors.md) |

`result` holds `summary` (the counts of errors and warnings), `source_digest`, `claims` (the kinds
of structure the run checked) and `semantic_completeness: "not_proven"`.

`source_digest` is a digest over the paths and digests of:

- The configuration.
- The registry.
- Every registered document member as read, whether or not it was admitted.
- The project glossary.
- The Protocol binding.

None of these enter the digest:

- Any other Module's records.
- The files Modules bind.
- The list of version-controlled files.
- The tests scanned for verification declarations.

While `source_digest` stays the same:

- A finding about bindings can change.
- A finding about unbound files can change.
- A finding about scenario coverage can change.

The command-line envelope is canonical JSON with `schema_version: 4`, the fields above and `error`.
When the command did its work, `error` is `null`.
Otherwise, `error` is the [error record](errors.md) of its failure, including a malformed command
line (`invalid_input`) and an unexpected failure (`unexpected_error`).
Findings are sorted by rule, source, line, column and message. Artifacts are sorted.
As for every command that prints this envelope, the exit code follows the status:

- 0 for `success`, `proposal` and `unchanged`.
- 1 for `invalid`.
- 2 for `conflict`.
- 3 for `failed`.


## Registry command {#registry-command}

`concorde registry --write` loads every recorded Module's entry.
The command rewrites each record to equal the entry's `module` block in `title`, `owns`, `contains`,
`uses`, `includes` and `participates`.
Where the block declares `glossary`, the command also rewrites the record's `glossary` to equal it.

It keeps the records' order and their `id` and `entry`. It adds or removes no record.
It writes through a [file
transaction](../../glossary.json#concept.file-transaction).
When nothing differs, it reports `unchanged`.
With `--check`, the command writes nothing and reports one `CHK.registry.mirror` finding per record
that differs.

When the registry or an entry cannot be read, the command fails and writes nothing.
The failure has the [error record](errors.md) naming the registry or the entry and its cause.

## Verification declarations {#verification-declarations}

A [verification declaration](../../glossary.json#concept.verification-declaration) is written in the
test's own source. A Python test uses the `verifies` decorator from `concorde.spec.verification` on
a test function or method. A TypeScript test uses an own-line comment directly above its `it`,
`test` or `describe` call.
The comment separates several identities by commas or spaces:

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

At run time, the decorator only attaches the identities to the test function.
The decorator returns the test function unchanged.

When an argument does not begin with `scenario.`, the decorator refuses it.

The scanner reads bound files ending in `.py`, `.ts`, `.tsx`, `.mts` or `.cts`.
The scanner never imports, compiles or runs them.

The scanner parses a Python file.
The scanner reads its module-level functions and the methods of classes at any class nesting.
A function nested inside another function is a helper.
The scanner ignores such a function.
Every argument must be a string literal beginning with `scenario.`.
The scanner reads a TypeScript file line by line, as UTF-8 with undecodable bytes replaced.
A TypeScript file therefore never fails to parse.
In a TypeScript file, a declaration is an own-line comment whose text after the comment marker
begins with `verifies:`. The declaration applies to the next `it`, `test` or `describe` call.
The call's title names the declaring test.
These cases are `CONCORDE-COVERAGE-003` errors for that file:

- A declaration that names no scenario.
- A declaration comment that no test call follows.
- An argument that is not a scenario identity.
- A Python file that does not parse.

The scanner then continues with the next file.
Each declaration yields `{scenario_id, path, line, name}`.

## Typed values {#typed-values}

Spec core keeps its own copy of the [typed value](../../glossary.json#concept.typed-value) format
that the [Kernel's contracts](../../kernel/contracts.md#typed-values) define.
The copy stays in Spec core's code so that the spec part depends on no other part.
It raises Spec tooling's own errors.
A typed value is a closed JSON object `{"type_id": ..., "schema_version": ..., "data": ...}`.
Within the spec part, the owners that register types are Spec core, the Spec MCP server and Views.

Spec core registers only its own.

The Kernel's [registered schemas](../../kernel/contracts.md#registered-schemas) define the schema
dialect a registered type may use.
They also define the `typed_schema` reference by which one type embeds another.

Spec core's copy admits exactly that dialect.
The wider dialect of `concorde-contract` fences below is Spec tooling's own.

```python
register(type_id: str, version: int, schema: dict) -> None
typed_schema(type_id: str) -> dict
typed(type_id: str, data: dict) -> dict
validate_typed(value, expected: str | None = None, field: str = "") -> dict
```

`register` adds a type. Its arguments are:

- `type_id`: a nonblank name such as `concorde-project-proposal`.
- `version`: a positive integer.
- `schema`: a schema admitted by the offline subset below, describing `data`.

With the same version and an equal schema, registering an identity already registered changes
nothing. With another version or schema, registering that identity fails with `duplicate_type`
and leaves the existing registration in force.

When their own code is loaded, owners call `register`. Spec core never imports an owner.
A caller that checks a value must therefore have loaded the code of the value's owner.

`typed_schema(type_id)` returns a schema fragment that matches a whole typed value of that type:
its `type_id`, its registered `schema_version` and its `data`.

The fragment refers to the type by name. When a value is checked, the fragment is resolved.
A registered schema may therefore embed another owner's type without importing it.
At check time, a reference to a still unregistered type fails with `unknown_type`.

`typed` builds and checks a value at the registered version of its type.

`validate_typed` checks an existing one. With `expected`, it also checks the value's type.
The failures are:

- A value with another version fails with `unsupported_version`.
- An unregistered type fails with `unknown_type`.
- Where `expected` is given, a value of the wrong type fails with `incompatible_handoff`.
- Any other mismatch fails with `invalid_field` naming the JSON pointer of the offending field.

A checked value is returned as a deep copy.

The `data` is checked as JSON Schema checks it, for the keywords a registered schema may use.
Unless its `additionalProperties` is `false`, an object admits keys its `properties` do not name.
When `additionalProperties` is a schema, the object checks those keys against it.
`obj` therefore spells `additionalProperties: false` to close its objects.
`number` admits integers and finite non-integral numbers. `integer` admits only integers.
Neither admits a boolean. `minimum` and `maximum` bound both.
Unless it is anchored, `pattern` matches anywhere in the string.
`const` and `enum` compare values with their JSON type.
Therefore, `true` is not `1`.
Each keyword applies to the kind of value it constrains, whether the schema names a `type` or not.
Beyond JSON Schema, when a string's schema sets `minLength`, the string must not consist of
whitespace only.
A registered schema may use only the Kernel's
[registered dialect](../../kernel/contracts.md#registered-schemas).
The checker evaluates every keyword of that dialect.
When registered, a schema with any of these fails with `invalid_input`:

- Any other keyword of the offline subset below, including `$schema`, `$id`, `$defs`, `oneOf`
  and `allOf`.
- A list of types.
- A `$ref` other than `typed_schema`'s.

No registered type therefore promises more than its values are checked for.

The shared building blocks are:

- `obj(properties, optional=())`: a closed object.
  Unless optional, its listed properties are required.
- `array(items, unique=False)`.
- `STRING`: a nonempty string.
- `PATH`: a canonical project-relative path.
- `DIGEST`: `sha256:` and 64 lowercase hexadecimal digits.
- `ARTIFACT`: `{id, path, digest}`.

```python
decode(text: str) -> Any
canonical(value: Any) -> str
safe_path(value: str, field: str = "") -> str
checked_path(project: Path, relative: str, field: str = "") -> Path
artifact(root: Path, identifier: str, relative: str) -> dict
verify_artifacts(root: Path, value, field: str = "") -> None
```

`decode` parses JSON, rejecting duplicate keys and non-finite numbers. `canonical` writes sorted,
compact JSON. `safe_path` accepts only canonical project-relative POSIX paths, which meet
all of these constraints:

- The path is nonempty.
- It has no leading `/`.
- It contains no backslash, colon or control character.
- It has no empty, `.` or `..` component.

`checked_path` additionally refuses a path any of whose components is a symbolic link.
`artifact` returns `{id, path, digest}` for a file below the given root.
When the file does not exist, `artifact` fails with `stale_reference`.
`verify_artifacts` walks a value.
When any embedded artifact's bytes changed, `verify_artifacts` fails with `stale_reference`.
The caller chooses the root. Spec core never decides in which worktree a record lives.
Failures raise `TypedDataError(ValueError)` with `code` and `field`.

### Offline schema subset {#offline-schema-subset}

The schema and example of every `concorde-contract` fence, and every registered schema, are checked
with an offline JSON Schema subset:

```python
admit(schema, root: dict | None = None) -> None
validate(value, schema, field: str = "", *, root: dict | None = None, depth: int = 0) -> None
```

A schema is an object or a boolean.
The admitted keywords are `$schema`, `$id`, `$defs`, `$ref`, `title`, `description`, `examples`,
`default`, `type`, `properties`, `required`, `additionalProperties`, `items` and `minItems`.
The subset also admits `maxItems`, `uniqueItems`, `minLength`, `maxLength`, `pattern`, `minimum`,
`maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and `format`.

In a contract fence, `$ref` must be `#/$defs/<name>` into the same root schema.
Any other reference is refused, so no schema can load a Spec document or a remote resource.
The only `format` is `project-path`, checked by `safe_path`.
Integers satisfy `number`. Booleans do not.
These problems fail admission with a `ContractError(ValueError)` carrying the JSON pointer of the
problem:

- Unknown keywords.
- Invalid bounds.
- Unresolved references.

When nesting is deeper than 100 levels, validation fails with a `ContractError(ValueError)`.
The error carries the JSON pointer of the problem.

### Front matter

Instruction files begin with a constrained YAML front matter block.
`concorde.spec.frontmatter.parse_document` reads the block.
The block supports space-indented keys, scalars, lists, nested maps and JSON-style inline collections.
Tags, anchors, aliases, merge keys, block scalars and duplicate keys are refused with a
`FrontMatterError` naming the file and line.

## File transactions {#file-transactions}

Spec core keeps its own copy of the [file transaction](../../glossary.json#concept.file-transaction)
that the [Kernel's contracts](../../kernel/contracts.md#file-transactions) define.
The copy raises Spec tooling's own errors:

```python
file_change(root: Path, path: str, content: str) -> dict
apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]
```

`file_change` returns `{path, before_digest, content}`.
When the file does not exist, `before_digest` is `null`.
Otherwise, `before_digest` is the digest of the file's current bytes.
`apply_files` requires:

- A nonempty list of such changes with unique paths.
- Every path is in `allowed`.
- Every content is a string.

Its failures are:

- For a malformed change set, it fails with `invalid_proposal`.
- For a path outside `allowed`, it fails with `permission_denied`.
- When a file's current bytes do not match its `before_digest`, it fails with `stale_proposal`.

The before-digest is checked once before any write and again just before each write.
Each file goes through these steps:

- It is written to a temporary file in its directory.
- It is flushed.
- It is renamed into place.

After all writes, the optional `verify` callable runs.
If it or any write raises, every written file is restored to its original bytes through the same
temporary file and rename, or removed if it did not exist.

`apply_files` returns the written paths in order.

A failure then propagates as follows:

- An operating-system error of a write becomes a `SpecError` with the code `system_error`.
  The error carries the file's path and the message that every file written so far was restored.
  Its one cause is the `system_error` record of the operating system's error.
- A `SpecError` of a write, such as `stale_proposal`, and any exception `verify` raises propagate
  unchanged. A caller's own check error therefore reaches the caller as the caller raised it.
- When the operating system refuses a restore, the other restores are still attempted.
  The transaction fails with a `SpecError` of code `system_error` that names every file not restored.
  The error says each still holds the new content.
  Its causes are the first failure followed by one `system_error` record per refused restore.
  When the first failure is a `SpecError`, it stays unchanged.
  Otherwise, the first cause is its `system_error` or `unexpected_error` record.

These guarantees hold for failures the process observes as an exception.
A killed or interrupted process restores nothing:

- Each file already renamed into place keeps its new content.
- Every other file keeps its original bytes.
- `.concorde-write-` temporary files may remain beside them.

## Initialization {#initialization}

```python
initialize(root: Path, package: Path, data: dict) -> dict
```

Initialization is deterministic. It runs no model. It selects no context.

`root` is the project. `package` is the running Concorde package. `data` is one of:

- `{"action": "propose", "name": ..., "target_id": ..., "python": ...}`.
  `name` is required and nonblank.
  `target_id`, the root Module's identity, defaults to `module.project`.
  When given, `python`, the project's interpreter, is nonblank. `python` is optional.
  When `.concorde/config.json` exists, propose fails with `already_initialized`.
  When the installer's [Protocol copy](../../glossary.json#concept.protocol-copy) is missing,
  propose fails with `not_installed`.
- `{"action": "apply", "proposal": ..., "proposal_digest": ...}`.
  `proposal` is the complete `concorde-project-proposal@2` value propose returned.
  It has closed data `{action: "initialize",
  base_digest: null, source_digest, files: [{path, before_digest, content}]}`.
  `proposal_digest` is the digest propose returned for it.

These cases fail with `invalid_input`:

- Any other action.
- A propose without a name.
- An apply without both fields.

Spec core registers the proposal type.

`source_digest` is the `sha256:` digest of the canonical JSON of `{protocol, entries, installed}`.
The object contains:

- The binding of the installed Protocol copy.
- The realization entries of the existing project files (below).
- The installed files the Concorde installation realization binds (below).

This is the project state the proposal was computed from.
`proposal_digest` is the `sha256:` digest of the canonical JSON of the proposal typed value.

Propose returns `{status: "proposed", proposal, proposal_digest, files}` with the typed proposal,
its digest and its ordered paths.

Apply returns `{status: "applied", proposal: null,
proposal_digest: null, files}` with the written paths.

The proposal contains five files, each with `before_digest: null`:

- `.concorde/config.json` with:
  - Profile 19.
  - The binding of the installed Protocol copy.
  - The `python` field.
- `.concorde/specs.json` with one record for the root Module.
- `specs/project/module.md` with its metadata.
- The empty project glossary `specs/project/glossary.json`, beside the entry.

When propose names an interpreter, `python` is that interpreter as given.
Otherwise, `python` is the first of `.venv/bin/python` and `venv/bin/python` that exists.
When propose names no interpreter and neither exists, `python` is absent.

The entry follows the reading order the Protocol's writing guidance recommends, in three sections:

- The `Purpose` section.
- `Not yet specified`, which says that these aspects of the project are not yet specified:
  - Its core concepts.
  - Its behaviour.
  - Its architecture.
- `Parts`, which says that the root:
  - Contains nothing yet.
  - Uses nothing yet.
  - Includes nothing yet.

  This section explains the root's realizations.
  Once the root has children, this section is where they are explained.

Its metadata declares the `module` block with:

- The entry as the only owned document.
- Empty relation arrays.
- The glossary.

The glossary holds no concept.

When the project already has files, the metadata defines one realization with these properties:

- Its identity is `realization.<local>.existing-files`.
- Its title is Existing project files.
- `<local>` is the last segment of the root Module's identity.

Its entries cover every file that version control tracks or leaves untracked without ignoring,
except:

- The proposed document members.
- Files under `.concorde/`.
- Generated and build outputs.
- Paths inside submodules.

A file directly under the project root is an exact entry.
If a top-level directory holds a document member or a file of the Concorde installation, its files
are exact entries.
Otherwise, the directory is one directory entry.
Files the exclusion rule would skip are also exact entries.
The entry explains this realization.
The entry says the realization promises nothing about the files.
A project with no files gets no realization.

When all these conditions hold, files are left out of that realization:

- `.concorde/install.json` lists them under `files`.
- They lie outside `.concorde/`.
- They exist.
- They are not listed under `amended`.

These files are bound instead by `realization.<local>.concorde-installation`, titled Concorde
installation. The entry explains this realization as the agents' configuration the installer
replaces on every update.
Without a receipt, or without such files, there is no such realization.

Initialization binds the installed files of its time.
After every later install or update, the installer **binds the installation** to keep that
realization in step with the receipt
([requirements](requirements.md#req.spec.installation-follows-record)).
The function `bind_installation(root)`:

- Adds, as exact entries, the receipt's installed files that exist and that no realization binds
  by its exact path.
- Removes the entries whose files are gone.
- Never touches another realization.

When no realization's identity ends in `.concorde-installation`, the function creates
`realization.<local>.concorde-installation` in the root Module and appends its explaining paragraph
to the root entry.

For a project that is not initialized or whose registry or metadata it cannot read, the function
returns nothing and leaves the project unchanged.

Otherwise, it returns the realization's identity with the entries it `bound` and `released`.

Apply checks these properties of a proposal, not its provenance:

- Its shape.
- The integrity its digest gives.
- Its freshness.

Any caller can compute the proposal digest.
Apply therefore cannot tell a proposal propose returned from one built to the same shape.
Its guarantee is that an applied proposal:

- Had exactly that shape and digest.
- Was computed from the project's current state.
- Wrote only the allowed files.
- Replaced none.
- Left a project that validates.

Apply refuses these cases, writing nothing:

- A `proposal_digest` that is not the digest of the given proposal (`invalid_proposal`).
- A proposal whose envelope is not exactly that shape (`invalid_proposal`).
- A proposal that lacks the configuration or the registry (`invalid_proposal`).
- A proposal whose configuration names a Protocol binding other than the installed copy's
  (`invalid_proposal`).
- A proposal that has a non-null before-digest (`invalid_proposal`).
- A proposal whose `source_digest` differs from the project's current one (`stale_proposal`).
  The project's files changed so that propose would now return a different proposal.

Apply writes only these files, with `permission_denied` otherwise:

- The configuration.
- The registry.
- The members of the documents the proposed registry lists.
- The glossary it declares.

It writes through one file transaction whose final check validates the project.
When a proposal destination appeared since the proposal, apply fails with `stale_proposal`.
A validation error rolls every file back.

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

`version` is the Protocol version.
`source_profile` and `workspace_protocol` are compatibility numbers of the bundle sources and of
the configuration profile the bundle was released with. The loader reads neither.
The assets are `generated/protocol/principles.md` and `generated/protocol/kinds/module.md`.
`generated/protocol/principles.md` contains the Protocol chapters, assembled from
`prompts/protocol/principles.md`.
`generated/protocol/kinds/module.md` contains Spec writing guidelines, assembled from
`prompts/protocol/kinds/module.md`.

The Spec writing guidelines contain the overview, Required format, Writing guidance and the
templates.

Required format remains in the principles bundle as well.
Each guide therefore includes the syntax its readers need.
The bundle sources include nothing but Protocol text.
The installer copies the manifest and the assets into `.concorde/protocol/`.
The project's binding is the manifest's `version` and the digest of the manifest's bytes.
The loader performs these steps:

- Reads the installed copy.
- Checks each asset against its recorded digest.
- Requires the copy's manifest to equal the running package's `protocol/manifest.json`.

Any mismatch is `protocol_mismatch`.
Distribution's build renders the assets. Its `protocol-manifest` command recomputes the recorded
digests.
