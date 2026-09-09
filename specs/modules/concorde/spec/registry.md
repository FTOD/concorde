```concorde-document
{
  "id": "document.spec.registry",
  "targets": [
    "module.spec"
  ],
  "main_visible": true
}
```
# Registry

This document defines `SpecRepository`'s selection and query behavior: what a caller receives when it selects a Module, reads its documents and structured declarations, or resolves a stable ID to its complete Spec file set. [values](values.md) defines the exact returned records and Framework configuration versions; [structure](structure.md) defines validation; [initialize](initialize.md) defines project initialization.

## Scenarios

### scenario.spec.select-module — Selecting a Module's complete context

- GIVEN a registered Module identity
- WHEN a caller selects it
- THEN the repository returns that Module's complete descriptor: its documents, dependencies, contracts and entity file listings
- AND no other Module's Spec body is read to produce that result

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
- THEN the query returns the owning Module's complete registered document collection, deduplicated and in a reproducible order
- BUT it neither follows uses, parentage nor entity file bindings, and it never reads the returned files' contents

## Requirements

- req.spec.no-writes: SpecRepository construction and every query method SHALL NOT write project files.
- req.spec.snapshot-reconstruct: A repository instance SHALL be treated as a snapshot; a caller SHALL reconstruct it to observe source changes.
- req.spec.deterministic-order: Repeated queries against the same admitted repository SHALL return results in the same order.
- req.spec.local-contracts-only: contracts(target) SHALL include only the blocks declared in the target's own registered documents, and SHALL leave duplicate-provider and cross-Module agreement checks to the repository validator.

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
SpecRepository.children(target: SpecTarget) -> tuple[SpecTarget, ...]
SpecRepository.descendants(target: SpecTarget) -> tuple[SpecTarget, ...]
SpecRepository.affected_modules(paths: tuple[str, ...]) -> tuple[SpecTarget, ...]
digest(value: bytes | Any) -> str
read_file(root: Path, relative: str) -> bytes
strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]
identifier(value: Any) -> str
```

No call above writes project files. Host candidate overlays stay in memory. A repository is a snapshot-oriented reader with document caching; reconstruct it after source changes. Selection returns the full target descriptor even with a scenario focus. Module document membership is exactly registered and one-hop; paths, links and entity file listings never add another Module's remaining body.

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
empty tuple when no blocks exist, and leaves duplicate-provider/global consumer agreement checks to the
separate repository validator. These are complete required promises for selection and local parsing;
no agent needs to read the collaborators' implementation or other Spec files to use this API.

## Stable-ID Spec context queries

`spec_files(entity_id: str) -> tuple[str, ...]` is a specified read-only metadata query, not yet
implemented by code. It admits exactly the Protocol's supported query domain by explicit registered
identity:

| Selected identity | Returned complete file set |
| --- | --- |
| Module | Its registered Markdown documents, in registration order. |
| Scenario | Its providing Module's complete collection, independent of its defining document. |

The returned paths are unique exact project-relative paths. A document identity, heading, directory
or unknown ID raises `SpecError/invalid_target`; identity prefixes and file locations never supply
missing ownership. A query does not follow uses, parentage or entity file bindings. It neither reads
implementation source files nor grants a worker access to the returned paths.

The retired `spec_pair` query, which paired a Module with one of its Implementation Specs, has no
replacement now that Implementation Specs no longer exist: a Module's entity file bindings are
visible directly inside its own Spec context, as file names, and in its separately defined
implementation context, as file contents for code-writing and code-review phases. A normal
`select(target_id, focus_id)` call remains Module-oriented and unchanged.

This query returns locators only, preserves explicit membership and performs no writes or network
I/O. Repeat queries against the same admitted repository yield the same order. Reconstruct the
repository after source changes. This query interface is a specified addition; its implementation
must be supplied before claiming complete Framework query support for Spec Protocol 3.0.0.
