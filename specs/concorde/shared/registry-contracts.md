```concorde-document
{
  "id": "document.shared.registry-contracts",
  "targets": ["service.spec-context", "service.workflow-host", "module.registry"],
  "main_visible": false
}
```

# Registry selection and value contracts

This registered Shared Spec defines the in-process registry interface required by the context and
Operation hosts. It is part of each listed target's admitted collection; callers need no provider,
parent or co-referencing entity's other documents. Python paths below are relative to the supplied
project root unless explicitly typed as project/package roots. No method grants an agent authority.

## Public call shapes

```python
SpecRepository(project_root: Path | str, package_root: Path | str | None = None, *,
               registry_bytes: bytes | None = None,
               document_overrides: dict[str, bytes] | None = None)
SpecRepository.select(target_id: str, focus_id: str | None = None) -> SpecTarget
SpecRepository.document(path: str) -> SpecDocument
SpecRepository.documents(target: SpecTarget) -> tuple[SpecDocument, ...]
SpecRepository.contracts(target: SpecTarget) -> tuple[dict, ...]
SpecRepository.participants(target: SpecTarget) -> tuple[dict, ...]
SpecRepository.implementation_files(target: SpecTarget) -> tuple[str, ...]
digest(value: bytes | Any) -> str
read_file(root: Path, relative: str) -> bytes
identifier(value: Any) -> str
strings(value: Any, label: str, *, nonempty: bool = False) -> tuple[str, ...]
SpecError(message: str, code: str = "invalid_spec", field: str = "")
```

Construction reads Profile 8 configuration, its explicitly pinned Protocol/package assets and the
registered topology. `package_root=None` selects the runtime's owning package. `registry_bytes` and
`document_overrides` are host-only candidate overlays for validation; they do not write files or
supplement an agent context. Construct a fresh repository after source, registry or Protocol changes:
an instance caches documents already read and is not a live filesystem view. The constructor rejects
unsafe roots, unsupported profiles/Protocol bindings, malformed registry/identity/relationship/check
metadata and overlapping implementation grants. The root must contain `.concorde/config.json` with exactly
`{profile_version: 8, registry: relative_path, protocol: {version: "1.0.0", digest: sha256},
operation_configuration: {type_id: "concorde-operation-configuration", schema_version: 1,
data: {integration: "codex"|"claude", enforcement: "native"|"outer"}}}`. The referenced registry is
`{schema_version: 1, project_id: stable_id, entry_target: target_id, targets: [SpecTarget records],
checks: [Check records]}`; tuple fields below are JSON arrays in that file. Entry target is a registered
Domain or Service. Every descriptor has exactly the listed fields; IDs are unique across targets and
focuses, each focus document belongs to its target, parent kinds match their independent axis, and
parents are acyclic. Domains have no code grants or component parent; components have no scope parent.
Component participation names existing Domains. Registered implementation path prefixes are disjoint
and cannot contain control/configuration files or Spec documents. Check IDs belong to their target.

The supplied package contains `protocol/manifest.json` with version `1.0.0` and an `assets` list of
`{path, digest}`. The project pins the manifest's exact byte digest, and each asset must match its own
listed byte digest. Principles and all three kind definitions are mandatory assets. Missing or changed
bindings/assets fail with `protocol_mismatch`; this repository never silently upgrades a binding.
Full document and shared-contract validation is a
separate deterministic host responsibility; successful construction is not semantic completeness.

`select` accepts a stable **target ID** and optional Feature/API focus owned by that target. It returns
the complete target descriptor without narrowing documents. Unknown targets raise
`SpecError(code="unknown_target")`; missing/foreign focus IDs raise `SpecError(code="invalid_focus")`.
For example, `feature.concorde.evolve-protocol` is a focus of `domain.concorde`, not another target.

`document` accepts only a registered document path, reads UTF-8 Markdown (or its explicit overlay),
and verifies exactly one document declaration with valid ID, exact reference set and boolean
`main_visible`. `documents` returns that operation for every registered path in target order, once
each. It does not follow links or include another referencing target's remaining documents.
Read/parse/declaration failures raise `SpecError`, Unicode/JSON parsing errors, or the declared safe-path
error; callers abort context construction rather than use an incomplete collection.

## Returned records and indexes

`SpecTarget` is a frozen dataclass (the tuple-contained dictionaries are data, not immutable grants):

```python
id: str
kind: Literal["domain", "service", "module"]
title: str
documents: tuple[str, ...]
scope_parent: str | None
component_parent: str | None
participates_in: tuple[str, ...]
implementation: tuple[str, ...]
features: tuple[dict, ...]   # each {id: str, title: str, document: str}
apis: tuple[dict, ...]       # same shape, independently owned focus IDs
checks: tuple[str, ...]
diagrams: tuple[dict, ...]   # each {source: str, kind: str, title: str}
```

`SpecDocument` is a frozen record with `path/content/digest/document_id: str`, `targets: tuple[str,...]`,
`main_visible: bool`, `metadata: dict` (parsed front matter, or empty) and `body: str` (Markdown after
front matter). `content` preserves the complete text. `digest` hashes its exact source bytes.
A document referenced by multiple targets belongs under Shared Specs; otherwise it is Target Spec.

Hosts may read these admitted repository indexes: `root/package_root: Path`, `config: dict`,
`project_id/entry_target/registry_path: str`, `registry_bytes: bytes`, `registry: dict`,
`protocol_manifest: dict`, `targets: dict[str, SpecTarget]`,
`focus: dict[str, tuple[str, str, dict]]` (owning target ID, `features|apis`, focus record),
`document_targets: dict[str, list[str]]`, `checks: dict[str, dict]`, and
`protocol_assets: dict[str, bytes]`. Index metadata locates authority; it does not supply business
promises or authorize directory traversal. Check records have `id`, `target_id`, nonempty `argv`,
positive `timeout_seconds`, and optional relative `inputs` paths.

`contracts` returns parsed local contract dictionaries in document/block order, with exactly the
registered contract fields `id: str`, `version: int > 0`, `role: provided|required`, `peer: str`,
`schema: dict`, `semantics: str`, `example: Any`, plus host-added `source: str` (document path) and
`owner: str` (target ID). Peer is a target identity or `external:name`. It validates schema admission
and the local example, but does not open a peer Spec. Global provider/consumer agreement is checked
separately. `participants` returns an empty tuple for non-Domains; for Domains it parses the local
routing entries, each with `target_id`, `kind`, `responsibility`, `selection_condition`,
`relied_upon_promises: list[str]`, and host-added `source`/`owner`. Context workers receive these
promises only through their admitted documents, never an implicit registry lookup.

`implementation_files` returns sorted, unique, existing regular files under the target's explicit
file/directory grants. It rejects symlinks; `.git`, `.venv`, `node_modules` and `__pycache__` members
are excluded. A missing future implementation path yields no existing file. The method returns
locators only, without reading file contents or granting writes. A code reviewer gets these exact
current file paths read-only; a Spec-only worker gets none.

## Effects, errors and representative use

All functions in this collection are read-only. `read_file` rejects unsafe relative paths, symlink
components and missing/nonregular files, returning exact bytes. `digest` hashes bytes directly or
canonical JSON serialization of another value and returns a `sha256:` identity. `identifier`
validates `[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*` and returns the string. `strings` accepts a list of unique
nonblank strings and returns a tuple, requiring at least one only when `nonempty=True`.
`SpecError` is a `ValueError` exposing stable `code` and `field`; messages explain diagnostics and
are not a compatibility key. Safe-path admission may raise `OperationDataError(ValueError)` with
its own code/field. OS read failures propagate without fallback to broader sources.

```python
repository = SpecRepository(project_root, package_root)
selected = repository.select("module.registry", "api.registry.select")
collection = repository.documents(selected)       # complete ordered collection
contracts = repository.contracts(selected)        # local contract views only
files = repository.implementation_files(selected) # host locators, not an agent grant
```

Unchanged inputs yield the same descriptors, order and byte digests. A changed document membership,
classification or byte sequence requires a new repository and context, and invalidates dependent
plans/reviews according to the host's version checks. Unknown selection and failed reading stop
that request; they never justify substituting another target or implementation facts for a Spec.
