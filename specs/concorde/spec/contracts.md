# Spec interface contracts

These precise specifications belong directly to the [Spec Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Snapshot](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Registry

### Interface signatures {#registry-interface-signatures}

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
SpecRepository.external_references(target: SpecTarget) -> tuple[str, ...]
SpecRepository.external_reference_paths(target: SpecTarget) -> tuple[str, ...]
SpecRepository.external_reference_files(entry: str) -> tuple[str, ...]
SpecRepository.external_reference_digest(entry: str) -> str
SpecRepository.external_reference_records(target: SpecTarget) -> list[dict]
SpecRepository.missing_external_references(target: SpecTarget) -> tuple[str, ...]
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
The external-reference queries serve a Module's `references` of kind `external`, the Protocol's
external references: `external_references` and `external_reference_paths` return the declared
entries and their base paths, `external_reference_files` expands one entry with the ordinary
exclusions plus media and archive suffixes, `external_reference_digest` is one digest over those
files' paths and bytes (cached per repository), `external_reference_records` is the snapshot form
(entry, directory flag, digest), and `missing_external_references` names entries that do not
exist. Admission rejects an external reference that is or contains a Spec document, that overlaps
the Module's own files, or that is declared twice; context resolution skips external references
entirely.

No call above writes project files. Host candidate overlays stay in memory. A repository is a snapshot-oriented reader with document caching; reconstruct it after source changes. Selection returns the full target descriptor even with a scenario focus. Ownership and references are explicit; context expands references once. Paths, links and entity file listings do not add files.

### Required collaborator promises {#registry-required-collaborator-promises}

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

### Stable-ID Spec context queries {#registry-stable-id-spec-context-queries}

`spec_files(entity_id: str) -> tuple[str, ...]` is the metadata-only locator query. Module and
scenario identities resolve to the selected owner's full context, sorted by canonical path:
owned document units plus one-level Module/document references, each expanded to its reading and metadata member. Identity resolution reads declared metadata, not unselected reading bodies.
A scenario's defining document never trims the result or transfers the scenario to a consumer.
Document IDs, requirements, entities and paths are unsupported query kinds (`SpecError/invalid_target`).
Unknown references, wrong kinds, ambiguous ownership and unsafe aliases reject the selection.

`spec_context(entity_id: str) -> SpecResolution` reads the resolved files and supplies exact byte
digests, original owner and every inclusion reason. It rejects unavailable required bytes rather
than returning a partial success. Reconstruct the repository after source changes. Both APIs are
read-only, offline and deterministic. Neither follows links, parentage, uses, referenced Modules'
references or implementation listings.

`SpecResolution` is a closed version-1 record with `schema_version`, `registration` (the selecting Module descriptor), `query_id`, `query_kind` (`module` or `scenario`),
`module_id`, `reading_entry` (the selected owner's `module.md` path), `documents` (the selected
owner's ordered registered paths), `references` (its typed reference pairs) and `sources` (sorted
index records). Each source has `document_id`, `path`, `owner`, `digest`, `role` (`reading` or `metadata`) and
`reasons`; no source carries its body, which a consumer reads from the file the record identifies. A reason is `{kind, id}`: kind `owned`
names the selected Module, kind `module` names a direct referenced Module, and kind `document`
names a direct referenced document unit. Both members have identical ownership and provenance. Reasons are unique and sorted by kind then ID. Digests hash
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

The runtime implements these resolution and binding interfaces under Protocol 9.0.0/Profile 14/
schema 5. Older profiles and membership-based declarations fail admission. Owned-definition and
implementation queries remain separate from the explicit context resolver.

## Registry values and selection

### Selection and returned values {#values-selection-and-returned-values}

SpecRepository(project_root, package_root=None, *, registry_bytes=None, document_overrides=None)
admits Profile 14 and registry schema 5. The optional bytes and document overrides form an in-memory
candidate; they never authorize ambient agent reads. Construction rejects malformed identities,
unknown parents/uses/references, composition cycles, duplicate file owners within one Module and non-sibling shared
providers.

SpecTarget has id, kind="module", title, documents, references, parent, uses, files and checks. primary_document
resolves exactly one local module.md, independently of document order. select(target_id,
focus_id=None) returns the complete Module descriptor and rejects a focus that does not belong to
the target. documents(target) returns only its owned Markdown collection; spec_context(target.id) returns
the owned-plus-referenced full sources with provenance. document(path) checks
the paired metadata identity and sole owner. contracts(target) parses owned canonical contract definitions and checks schemas/examples offline;
contract_bindings(target) returns local participant bindings without copying provider definitions.
context_contracts(target) resolves canonical definitions from the full context, retaining their owners. dependencies(target) parses local
dependency metadata and its local readable explanation without following those edges. definitions(target) parses the
Module's own scenarios, requirements and entities from its registered documents; entities(target) and
scenarios(target) project that same result. entity_files(target) maps each declared listing entry, an exact
file or a directory prefix, to its owning entity, and entity_for_path(target, path) resolves a
concrete file through the most specific covering entry. implementation_entries(target),
implementation_paths(target), implementation_files(target) and missing_entries(target) return the
declared entries, their base paths, the existing files those entries bind and the entries whose file
or directory is still missing. children(target) and descendants(target) return structural metadata, never inherited
context. listing_users(path) and affected_modules(paths) resolve changed files or entries through the reverse
index, in which a directory prefix covers every path below it, and covering_modules(target) applies it
to one Module's complete listing; a shared file therefore names several
Modules, never one exclusive owner.

SpecDocument is the reading view carrying path, content, digest, document_id, owner, metadata and body.
DocumentUnit carries the reading and metadata SourceMembers plus local readable meanings. Each source
has path, role, exact bytes and its own digest. SpecTarget.sources expands its registered document
paths to reading/metadata pairs in document order. The metadata document role organizes reading but never filters context; source-member role still distinguishes reading from metadata.
source_records returns both indexed members; source_bytes verifies registration and reads current
bytes for digest checking; source_is_overridden selects the complete candidate unit even when only
metadata changes. validate_source_records rejects incomplete pairs or inconsistent role/provenance.
A referenced document is included only by explicit Module references and retains its sole owner. Paths are safe project-relative
POSIX file paths; symlinks and aliases fail. read_file reads a regular file, digest produces
canonical sha256 identity, strings checks unique string arrays and identifier checks stable IDs.
Failures raise SpecError with code and field; typed path/JSON failures retain their TypedDataError
contract. No lookup writes files, changes authority, silently retries a different path or reads
source to invent missing Module meaning.

### Task authoring transport values {#values-task-authoring-transport-values}

The Typed values interface admits the following existing version-1 records in the closed envelope
`{type_id, schema_version: 1, data}`. Their data objects are closed as well; all fields below are
required. They carry task metadata, not implementation contents or execution authority.

| Type ID | Data shape | Meaning |
| --- | --- | --- |
| `concorde-task-scope-feedback` | `{tasks_digest: sha256, reason: "implementation_boundary"}` | Host feedback identifying the exact task list whose implementation acceptance must be separated from later Host responsibilities. `tasks_digest` is `sha256:` plus 64 lowercase hexadecimal digits, computed over the canonical JSON task list. The fixed reason requests preservation of software acceptance while correcting that phase boundary. |
| `concorde-task-identity-constraints` | `{reserved_task_ids: string[]}` | The IDs a fresh task author must not reuse: retained history and, during replacement, the current task list. Strings are nonblank and unique; an empty array is valid. These are identity reservations only, not additional work obligations or permission to replay prior work. |

`typed(type_id, data)` constructs and validates the envelope; `validate_typed(value, expected=None,
field="")` validates an existing envelope and optionally its expected type. The validator checks
the exact type, version, fields, digest syntax, fixed reason and ID-list shape without reading a
change record. It does not prove that a digest names the current list, that reservations are
complete, or that a caller may admit the value to a phase. Those contextual checks remain with the
calling Host and the receiving Agent's mode. Neither value can complete tasks, waive validation or
review, modify lifecycle state or widen file, network or credential authority by itself.

## Spec structure and validation

### Validator interface {#structure-validator-interface}

`validate_repository(root, target_id=None, package_root=None) -> ToolResult` returns
`status=success|invalid`, findings with `rule_id`, `message` and `remediation`, and a result
containing `source_digest` for the assessed Spec state. It checks identities, document
declarations, unique ownership, one-level references, canonical contract definitions, participant bindings, dependency metadata and readable meaning, scenario/requirement/entity syntax, entity listing
entries against the registry, architecture diagrams, structured contracts and Issue
attribution; a declared entry whose file or directory is missing is an error unless its entity marks
it pending, a still-pending entry that now exists is a warning, and a regular file that no Module's
entries cover is a warning; it explicitly does not prove semantics. Configured implementation checks
execute separately on the host using the registered `argv` and `timeout_seconds`, returning `check_id`,
`target_id`, `status`, `exit_code`, `source_digest` and `log_digest` with raw output retained
privately. No check result is a source-read proxy for an agent. Validation reads project files and
writes nothing.

## Project initialization

### Request and proposal shapes {#initialize-request-and-proposal-shapes}

The public input is `concorde-init-request@1`, an ordinary
`{type_id, schema_version: 1, data}` envelope. `data` is a closed object with required
`action: "propose"|"apply"` and optional `name`, `target_id`, `configuration` and `proposal`.
`name` and `target_id`, when supplied, are nonblank strings. `configuration` is
`concorde-capability-configuration@1`, whose data is the Pi worker model selection: an optional
default `model` (Pi's `provider/id`), `thinking` level and `timeout_seconds`, and optional `workers`
overrides keyed by a worker or a worker child. A key naming no worker or child, a child timeout, a
nonpositive timeout or a model that is not a Pi `provider/id` is rejected here instead of failing at
the first worker launch.
`proposal` is `concorde-project-proposal@1` with exactly `{action: "initialize", base_digest: sha256|null,
files: list[{path, before_digest: sha256|null, content: str}]}` in its data. File paths must be
canonical project-relative paths and distinct; content may be empty. These nested records reject
unknown properties.

Initialization produces only what the user's project generates through Concorde: its
configuration, its registry and its first Module Spec. Everything that exists only because Concorde
is installed, the Protocol copy under `.concorde/protocol/`, the Issue directory defaults and the
topology-artifact ignore file, is the installer's output and is never created here.

`action: "propose"` additionally requires `name` and `configuration` and optionally a `target_id`
(default `module.project`); `action: "apply"` requires the returned typed project proposal. A
proposal records `action: "initialize"`, a nullable `base_digest` and `files: {path, before_digest,
content}`. It creates `specs/project/module.md` with Purpose, Terminology, Usage, Design and Relationships,
paired schema-2 metadata with role module, and
an inline Mermaid diagram in Relationships with accessible title and description text; no external
diagram file is created. The stub models only known participants, the project Spec and the external
Framework; unknown business requirements, scenarios and architecture are explicit gaps recorded in
the stub's own Unresolved information. The illustration does not turn a draft into a complete
business contract.

Success returns `concorde-init-response@1` with closed data
`{status: "proposed"|"applied", proposal: TypedValue<concorde-project-proposal>|null,
files: list[path]}`. Propose returns the exact typed proposal and its ordered paths, without
changing project files; apply returns `status: "applied"`, `proposal: null` and the applied paths.

### Executable boundary {#initialize-executable-boundary}

At the executable boundary these typed values travel inside a
`concorde-capability-invocation@3` with `capability_id: "concorde-init"`, `mode: "execute"`,
nullable typed outer `configuration`, and `input` containing the request. The returned
`concorde-capability-result@3` has the same capability ID, fresh `invocation_id`, mode, nullable
workspace/output, status and `errors: list[{code, field, message}]`. Successful initialization has
`status: "succeeded"` and the typed output above; admission failures are blocked and execution
failures are failed, with no successful output.

## Framework configuration and storage versions {#values-framework-configuration-and-storage-versions}

`Profile 14` is the Framework's project-configuration compatibility version for the complete content model and its human-readable subset. It is distinct from Spec Protocol 9.0.0 and from registry schema 5, which versions the Framework's JSON encoding. These numbers do not classify project Modules or add concepts to the specification language.

The Framework reads `.concorde/config.json` with exactly `profile_version: 14`, `registry` (the registry's project-relative path), `protocol` (the accepted version and manifest digest, whose bundle the project carries under `.concorde/protocol/`) and `capability_configuration` (the typed Pi worker model selection: an optional default `model`, `thinking` level and `timeout_seconds`, and optional `workers` overrides per worker or per worker child). Other profile values fail with `unsupported_profile`; an incompatible Protocol binding fails with `protocol_mismatch`.

Registry schema 5 stores exactly `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. `targets` holds Module descriptors; both Module Specs and Implementation Specs are owned units in the same documents collection, distinguished by the explicit schema-2 document.role. Implementation Specs are normative documents, not entity file bindings or implementation source. The separate check records configure executable verification; they are Framework execution metadata. Their serialized shape does not replace the Protocol's meaning of identity, membership, composition, dependency, entity or file binding.

## Registry admission details {#structure-registry-admission-details}

Registry schema 5 contains `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. A Module descriptor has `id`, `kind="module"`, `title`, `documents`, `references`, `parent`, `uses`, `files` and `checks`. Every array is explicit. `files` holds listing entries: an exact project file, or a directory prefix written with a trailing `/` that binds every regular file below it. It MUST equal the sorted union of the Module's own entity listing declarations, entry for entry, so a directory prefix appears as that prefix and never as its expanded file names; membership, composition and dependency are checked independently of that entry set. The entry names one Module, and its complete collection starts routing.

Each registered reading document has a `.md.json` companion with `schema_version: 2`, `document`
identity/owner/role and explicit `entities`, `dependencies` and `bindings` arrays. Entity records contain
id/title/kind and a local readable meaning anchor, with optional files/pending/target_id. Dependency
records contain target_id and a local meaning anchor. Participant bindings contain id/version/role/
peer and a local meaning anchor. Responsibilities, conditions, guarantees and obligations remain
readable prose, never copied semantic strings in metadata. File/directory binding specificity and
pending rules still apply, and neither source member may be bound as implementation or external
material. Every child and used Module has exactly one local entity and one dependency explanation.

The principal Relationships diagram uses a nonempty subset of local entity titles and labels each
edge. Scoped omission of an inventory node is permitted; inventing a node is not. Check records
retain id/target_id/argv/timeout_seconds and optional inputs. Shared implementation changes concern
every listing Module, whose contract is evaluated separately.

Topology preparation stores the exact validated registry/document replacements below the ignored `.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every file before-digest before one atomic transaction.

### Reference and interface validation

Schema 5 requires a references array on every Module. Each `{kind, id}` must resolve to the
declared Module/document kind; duplicates, self references, document aliases and multiple owners
are errors. Overlap is deduplicated with all provenance, and cycles do not recurse. Each binding's
canonical definition/version must occur in its participant's resolved context; internal peers
require complementary bindings. Definitions have one owner and cannot be duplicated in consumers.
Required links to excluded definitions identify gaps rather than authorizing another read.
Structural checks report missing references/definitions separately from semantic incompleteness.
