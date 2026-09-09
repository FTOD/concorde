```concorde-document
{
  "id": "document.module.registry",
  "targets": [
    "module.registry"
  ],
  "main_visible": true
}
```

# Registry

## api.registry.select

`SpecRepository` admits the explicitly configured Profile 9 topology and pinned Protocol, selects
one complete target with an optional local API/Feature focus, and returns registered documents,
local contracts, Module participant promises and existing implementation locators. The registered
Shared Spec **Registry selection and value contracts** in this same collection defines constructor
inputs, configuration/registry shapes, exact returned records, indexes, effects, errors and examples.
It does not admit any collaborator's remaining Spec or infer target meaning from implementation.

## Interface signatures

```python
SpecRepository(project_root: Path | str, package_root: Path | str | None = None, *,
               registry_bytes: bytes | None = None,
               document_overrides: dict[str, bytes] | None = None)
SpecRepository.select(target_id: str, focus_id: str | None = None) -> SpecTarget
SpecRepository.document(path: str) -> SpecDocument
SpecRepository.documents(target: SpecTarget) -> tuple[SpecDocument, ...]
SpecRepository.diagram_sources(target: SpecTarget) -> list[dict]
SpecRepository.contracts(target: SpecTarget) -> tuple[dict, ...]
SpecRepository.dependencies(target: SpecTarget) -> tuple[dict, ...]
SpecRepository.implementation_files(target: SpecTarget) -> tuple[str, ...]
digest(value: bytes | Any) -> str
read_file(root: Path, relative: str) -> bytes
strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]
identifier(value: Any) -> str
```

No call above writes project files. Host candidate overlays stay in memory. A repository is a
snapshot-oriented reader with document caching; reconstruct it after source changes. Selection
returns the full target descriptor even with a focus. Target and Shared Spec membership is exactly
registered and one-hop; paths, links and dependencies never add another target's remaining body.

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
access. Local `contracts` includes every block from Target Spec plus Shared Specs, returns an empty
tuple when no blocks exist, and leaves duplicate-provider/global consumer agreement checks to the
separate repository validator. These are complete required promises for selection and local parsing;
no agent needs to read the collaborators' implementation or other Spec files to use this API.
