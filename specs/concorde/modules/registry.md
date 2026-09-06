```concorde-document
{
  "id": "document.module.registry",
  "targets": ["module.registry"],
  "main_visible": false
}
```

# Registry

## api.registry.select

SpecRepository(project_root, package_root=None) admits Profile 8 config, verifies pinned Protocol assets and builds both target-to-document and document-to-target indexes. select(target_id,focus_id=None) returns one immutable Target or raises SpecError for missing/foreign identity. document(path) verifies one concorde-document ID/reference/main-visibility declaration; documents(target) returns the ordered Target Spec plus Shared Specs without following other references. contracts(target) parses local concorde-contract blocks; participants(domain) parses the Domain-local concorde-participants routing view. implementation_files(target) enumerates explicit owned files with symlink rejection. Deterministic validation checks document identity/membership/visibility, parent graphs, participation and disjoint code grants. This Module may inspect global metadata but never supplies a co-referencing entity's remaining bodies as target context.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of repository:

```text
digest(value: bytes | Any) -> str
read_file(root: Path, relative: str) -> bytes
strings(value: Any, label: str, *, nonempty: bool=False) -> tuple[str, ...]
identifier(value: Any) -> str
SpecRepository.document(path: str) -> SpecDocument
SpecRepository.documents(target: SpecTarget) -> tuple[SpecDocument, ...]
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
