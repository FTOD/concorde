```concorde-document
{
  "id": "document.spec.registry",
  "owner": "module.spec",
  "main_visible": true
}
```
# Registry

This document defines `SpecRepository`'s selection and query behavior: what a caller receives when it selects a Module, reads its documents and structured declarations, or resolves a stable ID to its complete Spec file set. [values](values.md) defines the exact returned records and Framework configuration versions; [structure](structure.md) defines validation; [initialize](initialize.md) defines project initialization.

## Scenarios

### scenario.spec.select-module — Selecting a Module's complete context

- GIVEN a registered Module identity
- WHEN a caller selects it
- THEN the repository returns that Module's complete descriptor including its owned documents and explicit references
- AND resolving its context includes only the full documents selected by those declarations, with original ownership retained

### scenario.spec.select-scenario-focus — Selecting through a scenario focus

- GIVEN a registered scenario identity that belongs to a Module
- WHEN a caller selects the Module with that scenario as focus
- THEN the repository returns the same complete Module descriptor as an unfocused selection
- AND the focus narrows attention only, never the returned file set

### scenario.spec.reject-foreign-focus — Rejecting a focus that is not the target's own

- GIVEN a scenario identity that belongs to a different Module than the one being selected
- WHEN a caller selects the target with that focus
- THEN selection fails with an invalid-focus error
- AND no descriptor is returned

### scenario.spec.query-files — Resolving a stable ID to its complete file set

- GIVEN a registered Module identity or a registered scenario identity
- WHEN a caller queries its Spec file set
- THEN the query returns the owning Module's complete resolved document context, deduplicated and sorted by canonical path
- BUT it neither follows uses, parentage nor entity listing entries, and it never reads the returned files' contents

## Requirements

### req.spec.no-writes — No writes during construction or queries

SpecRepository construction and every query method SHALL NOT write project files.

### req.spec.snapshot-reconstruct — A repository instance is an immutable snapshot

A repository instance SHALL be treated as a snapshot.

### req.spec.reconstruct-for-changes — Reconstruct the repository to see changes

A caller SHALL reconstruct the repository to observe source changes.

### req.spec.deterministic-order — Deterministic order for repeated queries

Repeated queries against the same admitted repository SHALL return results in the same order.

### req.spec.local-contracts-only — Definition ownership stays local

contracts(target) SHALL return only canonical definitions in documents owned by the target.

### req.spec.contracts-defer-agreement-checks — Cross-Module checks stay with the validator

contracts(target) SHALL leave canonical-definition uniqueness and cross-Module binding checks to the
repository validator.

## Interface signatures

```python
SpecRepository(project_root: Path | str, package_root: Path | str | None = None, *,
               registry_bytes: bytes | None = None,
               document_overrides: dict[str, bytes] | None = None)
SpecRepository.select(target_id: str, focus_id: str | None = None) -> SpecTarget
SpecRepository.document(path: str) -> SpecDocument
SpecRepository.documents(target: SpecTarget) -> tuple[SpecDocument, ...]
SpecRepository.contracts(target: SpecTarget) -> tuple[dict, ...]
SpecRepository.dependencies(target: SpecTarget) -> tuple[dict, ...]
SpecRepository.definitions(target: SpecTarget) -> ModuleDefinitions
SpecRepository.entities(target: SpecTarget) -> tuple[SpecEntity, ...]
SpecRepository.scenarios(target: SpecTarget) -> tuple[Scenario, ...]
SpecRepository.entity_files(target: SpecTarget) -> dict[str, SpecEntity]
SpecRepository.entity_for_path(target: SpecTarget, path: str) -> SpecEntity | None
SpecRepository.implementation_entries(target: SpecTarget) -> tuple[str, ...]
SpecRepository.implementation_paths(target: SpecTarget) -> tuple[str, ...]
SpecRepository.implementation_files(target: SpecTarget) -> tuple[str, ...]
SpecRepository.missing_entries(target: SpecTarget) -> tuple[str, ...]
SpecRepository.children(target: SpecTarget) -> tuple[SpecTarget, ...]
SpecRepository.descendants(target: SpecTarget) -> tuple[SpecTarget, ...]
SpecRepository.listing_users(path: str) -> tuple[str, ...]
SpecRepository.affected_modules(paths: tuple[str, ...]) -> tuple[SpecTarget, ...]
SpecRepository.covering_modules(target: SpecTarget) -> tuple[SpecTarget, ...]
digest(value: bytes | Any) -> str
read_file(root: Path, relative: str) -> bytes
strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]
identifier(value: Any) -> str
```

Listing queries separate declarations from current disk state. `implementation_entries` returns the
declared entries unchanged, exact files and directory prefixes alike; `implementation_paths` returns
their base paths without a trailing slash, for permission and history roots; `implementation_files`
expands each directory entry into the existing regular files below it, skipping the Framework's
skipped directories, dot-prefixed names, symlinks and skipped suffixes; `missing_entries` returns the
entries whose file or directory does not exist yet. `entity_files` is keyed by declared entry, and
`entity_for_path` answers which entity owns a concrete file through the most specific covering entry.
`listing_users` and `affected_modules` resolve a path or entry through the reverse index, in which a
directory prefix covers every path below it, and `covering_modules` answers the same question for one
Module's whole listing, so a peer that binds a file inside a listed directory is found as well.

No call above writes project files. Host candidate overlays stay in memory. A repository is a snapshot-oriented reader with document caching; reconstruct it after source changes. Selection returns the full target descriptor even with a scenario focus. Ownership and references are explicit; context expands references once. Paths, links and entity file listings do not add files.

## Required collaborator promises

The wire boundary's `decode(text: str) -> Any` rejects duplicate JSON keys and non-finite numbers;
`canonical(value: Any) -> str` produces stable sorted-key compact JSON. Its
`safe_path(value: str, field: str = "") -> str` and
`checked_path(project: Path, relative: str, field: str = "") -> Path` reject absolute paths, traversal,
backslashes and symlink components. Failures raise `TypedDataError(ValueError)` carrying `code`
and `field`; they never retry through a different path. The offline schema boundary provides
`admit(schema: Any, root: dict | None = None) -> None` and
`validate(value: Any, schema: Any, field: str = "", *, root: dict | None = None, depth: int = 0) -> None`.
This is a bounded offline subset, not a full JSON Schema dialect. Schemas are objects or booleans.
The admitted keywords are `$schema`, `$id`, `$defs`, `$ref`, `title`, `description`, `examples`,
`default`, `type`, `properties`, `required`, `additionalProperties`, `items`, `minItems`, `maxItems`,
`uniqueItems`, `minLength`, `maxLength`, `pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`,
`oneOf`, `allOf` and `format`. The metadata keywords do not select a dialect or fetch resources.
Types are object, array, string, integer, number, boolean and null, individually or in a nonempty
array; integers satisfy number, while booleans do not satisfy numeric types. References must be
direct `#/$defs/<name>` references to the supplied root's definitions; nested pointers and remote
references are rejected. Object properties, required fields and additional-properties rules,
homogeneous array items and uniqueness, inclusive size/numeric bounds, Python-regex string patterns,
exact typed enum/const values and the three schema combinators are enforced. Only `project-path`
format is supported and delegates to the safe-path boundary. Bounds must be valid finite numbers
or nonnegative integer lengths with minimum no greater than maximum. Unknown keywords, invalid
types, unresolved references and malformed rule values fail admission; schema/value recursion beyond
100 validation levels fails validation. `validate` expects an admitted schema.

Schema admission or example-validation failures raise `ContractError(ValueError)` with a `field`
JSON pointer (empty for an admission/root error). Invalid `project-path` values instead propagate
`TypedDataError` from the path boundary. `contracts()` propagates both without wrapping, returns
no partial tuple on any error, and separately raises `SpecError` for malformed contract metadata.
It rejects unknown keywords, remote references, invalid schemas and invalid examples without network
access. Local `contracts` includes every block from the target's own registered documents, returns an
empty tuple when no blocks exist, and leaves canonical-definition uniqueness and global binding checks to the
separate repository validator. This is the canonical offline schema and path boundary used by interface definitions; consumers
include this document explicitly and link to it without copying its vocabulary.

## Stable-ID Spec context queries

`spec_files(entity_id: str) -> tuple[str, ...]` is the metadata-only locator query. Module and
scenario identities resolve to the selected owner's full context, sorted by canonical path:
owned documents plus one-level Module/document references. It does not read those files' bodies.
A scenario's defining document never trims the result or transfers the scenario to a consumer.
Document IDs, requirements, entities and paths are unsupported query kinds (`SpecError/invalid_target`).
Unknown references, wrong kinds, ambiguous ownership and unsafe aliases reject the selection.

`spec_context(entity_id: str) -> SpecResolution` reads the resolved files and supplies exact byte
digests, original owner and every inclusion reason. It rejects unavailable required bytes rather
than returning a partial success. Reconstruct the repository after source changes. Both APIs are
read-only, offline and deterministic. Neither follows links, parentage, uses, referenced Modules'
references or implementation listings.

`SpecResolution` is a closed record with `query_id`, `query_kind` (`module` or `scenario`),
`module_id`, `documents` (the selected owner's ordered registered paths), `references` (its typed
reference pairs) and `sources` (sorted complete records). Each source has `document_id`, `path`,
`owner`, `digest`, `main_visible`, `content` and `reasons`. A reason is `{kind, id}`: kind `owned`
names the selected Module, kind `module` names a direct referenced Module, and kind `document`
names a direct referenced document. Reasons are unique and sorted by kind then ID. Digests hash
exact bytes before UTF-8 decoding; invalid UTF-8 rejects resolution. The record is bound into
the Harness snapshot, not independently authored as another context inventory.

`context_contracts(target)` returns canonical contracts in this resolution with owner/document
provenance; `contract_bindings(target)` returns only owned bindings. `definitions`, `entities`,
`scenarios`, dependency and implementation queries remain ownership-only. Reference inclusion
never affects their entity union, diagram requirements or code permissions.

`context_users(document_id)` returns the owner plus every Module whose one-level context includes
the document, sorted by Module ID. It drives review/invalidation, separately from the implementation
reverse index. Ownership or reference edits compare both old and candidate users, even when the
resulting file set is unchanged. A Module reference tracks additions/removals to the provider's
owned documents; changes only to the provider's references do not expand the consumer.

These resolution and binding interfaces are specified migration work. The current runtime still
admits Protocol 4.0.0/Profile 11/schema 3 and has no conforming `spec_files`/`spec_context` or
Module-reference resolver. The authored Profile 12 registry must fail closed in that runtime;
new documentation and successful build generation do not establish implementation support.
