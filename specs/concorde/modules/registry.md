# Registry

## api.registry.select

SpecRepository(project_root, package_root=None) admits Profile 8 config, verifies pinned Protocol assets and parses the registry. select(target_id,focus_id=None) returns one immutable Target or raises SpecError for missing/foreign identity. documents(target) reads exactly ordered Markdown members; contracts(target) parses only local concorde-contract blocks. implementation_files(target) enumerates explicit owned files with symlink rejection. IDs, both parent graphs, participation and disjoint code grants are validated using metadata. This Module may inspect global metadata but never supplies peer bodies as target context.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of repository:

```text
digest(value: bytes | Any) -> str
read_file(root: Path, relative: str) -> bytes
strings(value: Any, label: str, *, nonempty: bool=False) -> tuple[str, ...]
identifier(value: Any) -> str
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
