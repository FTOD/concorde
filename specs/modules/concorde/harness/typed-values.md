```concorde-document
{
  "id": "document.harness.typed-values",
  "targets": [
    "module.harness"
  ],
  "main_visible": true
}
```
# Typed values

## interface.harness.validate

`typed(type_id, data)` produces a validated TypedValue; `validate_typed(value, expected=None,
field="")` rejects unknown type/version, unknown properties, malformed values and unsafe paths.
There is no caller-supplied `schema_version` argument to `typed`. `decode(text)` rejects duplicate
JSON keys and non-finite numeric constants. `json_schema(type_id)` exports self-contained schemas
with local definitions. Contract IDs are stable independent of paths. Local required/provided
schemas admit only the supported offline subset: remote references and unknown keywords fail.
Structural validation is not a claim of semantic completeness.

## Canonical serialization

`canonical(value)` returns a JSON string using Python's standard JSON encoder with sorted
object keys, compact separators (`,` and `:`), ASCII escaping and `allow_nan=False`, with no
trailing newline. It accepts `None`, booleans, strings, integers, finite floats, lists, tuples
(encoded as arrays), and dictionaries containing recursively supported values. String-keyed
objects are the transport contract: keys sort lexicographically, array order is preserved, and
non-ASCII characters are escaped. It does not validate TypedValue schemas, normalize Unicode or
numeric representations, or implement a separate cross-language canonicalization standard.

The underlying encoder also accepts dictionary keys of type integer, finite float, boolean or
`None` when key sorting is possible, converting them to JSON property strings. Such coercion can
produce duplicate property strings; callers requiring round trips through `decode` must use
unique string keys. Mixed keys that cannot be compared raise `TypeError`. Unsupported objects
(including bytes, sets and arbitrary class instances) and unsupported key types raise `TypeError`.
Non-finite floats anywhere in values or keys, and circular containers, raise `ValueError`;
excessive nesting can raise `RecursionError`. These encoder exceptions propagate directly and
are not wrapped as `TypedDataError`. Successful serialization has no filesystem effects and
normalizes only the encoding choices stated above.

## Typed values and recursive dispatch

A TypedValue is exactly `{type_id: str, schema_version: int, data: object}`. This API constructs
and accepts version 1 only (an integer, never a boolean). The separate outer native/capability
completion envelopes may have other versions; they are not constructed by this helper.
`validate_typed` returns a deep copy after validating the registered payload schema and applicable
type-specific rules. `expected` requires an exact type ID match. Errors are
`TypedDataError(ValueError)` with `code`, JSON-pointer `field` and message; `to_dict()` returns
those three fields. Codes include `unknown_type`, `unsupported_version`, `incompatible_handoff`,
`invalid_field`, `invalid_json`, `stale_reference` and `workspace_mismatch`.

`contracts()` returns the installed capability-name mapping to `(request_type_id, response_type_id)`;
names use `concorde-` and their types use `-request` and `-response`. `schemas()` returns the installed
Profile 9 type-ID-to-payload-schema mapping. `exported_types()` enumerates its public capability
request/response types followed by internal stage types; callers can use each ID with `json_schema`
to obtain its exact envelope and recursively referenced payload schemas. These returned schemas
are the supported machine-readable discovery interface, not a grant to inspect implementation.
`dependencies(capability)` returns its declared host role/capability dependencies, including a main
coordinator for main-routed capabilities, or an empty tuple when none are declared. It does not
return Agent delegation edges, select context or grant invocation authority. Retained legacy
low-level data types cannot reactivate retired public workflows.

The recursive Agent adapter adds these version-1 payload contracts. All listed fields are required,
unknown properties are rejected, `S` means a nonblank string and `N` means `S | null`:

| Type ID | Payload |
| --- | --- |
| `concorde-agent-task` | `task: S`, `target_id: S` |
| `concorde-agent-answer` | `answer: S` |
| `concorde-agent-interruption` | `gaps: Gap[]`, `decision: N` |
| `concorde-agent-loop-context` | `invocation_id: S`, `parent_id: N`, `agent_id: S`, `input_json: S`, `context_json: S`, `feedback: Feedback[]`, `children: Child[]`, `result_schema_json: S` |
| `concorde-agent-loop-step` | `source: "code-driven" | "model-driven"`, `action: "delegate" | "complete"`, `agent_id: N`, `value_json: N`, `outcome: Outcome`, `details: TypedValue<concorde-agent-interruption> | null` |

`Gap` has `question`, `blocked_step`, `needed_contract`, `target_id` and `context_id`, all `S`;
`context_id` additionally must be `sha256:` followed by exactly 64 lowercase hexadecimal digits.
`Feedback` has `invocation_id: S`, `parent_id: N`, `agent_id: S`, `outcome: Outcome`,
`value_json: N`, `error: N` and nullable typed interruption `details`. `Child` has `agent_id`,
`input_type`, `result_type`, `input_schema_json` and `result_schema_json`, all `S`. These nested
records also reject unknown properties. `Outcome` is `completed`, `spec_incomplete`, `waiting`,
`cancelled`, `failed`, `limit_exhausted` or `rejected`. Arrays may be empty unless the runtime's
outcome rules require otherwise. The `_json` fields are serialized transport values; this Module
checks their string shape. The execution host separately parses them, validates them against the
admitted type/schema, checks grant and invocation bindings, and enforces the relationships between
action, outcome, result and interruption. Structural acceptance alone does not authorize a child.

`obj` makes a closed object schema whose declared properties are required except those named in
`optional`; `array` supplies an item schema and optional uniqueness assertion. `typed_schema`
describes the exact version-1 envelope using a bare type-ID reference into the installed internal
schema map. `check_schema` consumes these internal schemas, not arbitrary external schema documents.
`json_schema` requires a known type ID and returns Draft 2020-12 syntax with all transitive
definitions under `$defs` and local references. An unknown ID raises `KeyError`; public value
admission instead reports `TypedDataError/unknown_type`. Export strips internal format annotations,
so callers must still use typed validation for project-path and contextual admission rules.

## Offline schema and artifact contracts

`schema.admit` accepts boolean schemas or objects containing only `$schema`, `$id`, `$defs`, `$ref`,
`title`, `description`, `examples`, `default`, `type`, `properties`, `required`,
`additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`, `maxLength`,
`pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and `format`.
Types are object, array, string, integer, number, boolean and null; nonempty type unions are allowed.
Only the `project-path` format is supported. Assertions follow their ordinary JSON Schema meaning;
numbers and numeric bounds must be finite, booleans are not integers, and integer values satisfy
number schemas. Annotation fields do not fetch remote resources. References must be direct
`#/$defs/<name>` references resolved against `root`, which defaults to the enclosing schema;
remote, nested and unresolved references fail admission. Required names must be unique strings,
length bounds nonnegative integers, numeric bounds finite, regex patterns valid, and lower bounds
must not exceed upper bounds. Schema combinators require nonempty schema arrays.
Successful `schema.admit` returns `None`. Its declared rejection cases (unsupported keywords,
malformed assertions, and unsupported or unresolved references) raise `ContractError(ValueError)`;
the exception carries `field` (empty for admission's schema-level diagnostic), and its string
message is prefixed by that pointer or `/` when empty. Admission returns no findings list.

`schema.validate` requires an already admitted schema and the same root, returns `None` on success
and rejects mismatches or nesting beyond 100 with `ContractError(ValueError)`, whose `field` is a
JSON pointer. `pointer(base, key)` appends an escaped segment (`~` becomes `~0`, `/` becomes `~1`).
Project-path format failures may propagate `TypedDataError`. Neither admission nor validation
mutates files, resolves network references or proves business semantics.

`safe_path` returns its input only when it is a canonical, nonempty project-relative POSIX path.
It rejects absolute paths, backslashes, colons, control characters, empty components, `.` and `..`
with `TypedDataError/invalid_field`. `checked_path` joins that path beneath a caller-owned trusted
project root and rejects symlinks in every relative path component; it need not already exist.
`artifact` requires a regular file there and returns `{id, path, digest}`, where `digest` is
`sha256:` followed by the 64 lowercase hexadecimal digits of the exact file bytes. A missing file
raises `stale_reference`; filesystem I/O errors may propagate. It does not create the file.
`verify_artifacts` recursively visits dictionaries and lists, recognizes references by the exact
key set `{id, path, digest}`, validates their shape and recomputes each artifact. Missing or changed
bytes fail with `stale_reference`; unsafe paths fail with `invalid_field`. It returns `None` on
success, ignores scalar leaves, and creates no read authority beyond the caller's trusted root.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of typed_data:

```text
canonical(value: Any) -> str
decode(text: str) -> Any
obj(properties: dict, optional: tuple[str, ...]=()) -> dict
array(items: dict, *, unique: bool=False) -> dict
typed_schema(type_id: str) -> dict
check_schema(value: Any, schema: dict, field: str='') -> None
safe_path(value: str, field: str='') -> str
checked_path(project: Path, relative: str, field: str='') -> Path
typed(type_id: str, data: dict) -> dict
validate_typed(value: Any, expected: str | None=None, field: str='') -> dict
artifact(project: Path, identifier: str, relative: str) -> dict
verify_artifacts(project: Path, value: Any, field: str='') -> None
json_schema(type_id: str) -> dict
```

Public functions of contracts:

```text
dependencies(capability: str) -> tuple[str, ...]
contracts() -> dict[str, tuple[str, str]]
schemas() -> dict
exported_types() -> tuple[str, ...]
```

Public functions of wire_shapes:

```text
obj(properties: dict, optional: tuple[str, ...]=()) -> dict
array(items: dict, *, unique: bool=False) -> dict
typed_schema(type_id: str) -> dict
```

Public functions of schema:

```text
pointer(base: str, key: Any) -> str
admit(schema: Any, root: dict | None=None) -> None
validate(value: Any, schema: Any, field: str='', *, root: dict | None=None, depth: int=0) -> None
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
