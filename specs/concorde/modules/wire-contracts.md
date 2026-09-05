# Wire contracts

## api.wire.validate

typed(type_id,data,schema_version=1) produces a validated TypedValue; validate_typed(value,expected_type=None,field="") rejects unknown type/version, unknown properties, malformed values and unsafe paths. decode(text) rejects duplicate JSON keys and non-finite numbers. json_schema(type_id) exports self-contained schemas with local definitions. Contract IDs are stable independent of paths. Local required/provided schemas admit only the supported offline subset: remote references and unknown keywords fail. Structural validation is not a claim of semantic completeness.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of operation_data:

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

Public functions of protocol_contracts:

```text
dependencies(operation: str) -> tuple[str, ...]
contracts() -> dict[str, tuple[str, str]]
schemas() -> dict
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
