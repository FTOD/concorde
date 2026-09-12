```concorde-document
{
  "id": "document.spec.values",
  "owner": "module.spec",
  "main_visible": true
}
```
# Registry values and selection

## Framework configuration and storage versions

`Profile 12` is the Framework's project-configuration compatibility version for the four-part Module model (Purpose, Requirements, Scenarios, Ontology). It is distinct from Spec Protocol 5.0.0 and from registry schema 4, which versions the Framework's JSON encoding. These numbers do not classify project Modules or add concepts to the specification language.

The Framework reads `.concorde/config.json` with exactly `profile_version: 12`, `registry` (the registry's project-relative path), `protocol` (the accepted version and manifest digest) and `capability_configuration` (the typed integration/enforcement configuration). Other profile values fail with `unsupported_profile`; an incompatible Protocol binding fails with `protocol_mismatch`.

Registry schema 4 stores exactly `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. `targets` holds Module descriptors; there is no separate Implementation Spec collection, because every entity file binding is declared inside its owning Module's own documents. The separate check records configure executable verification; they are Framework execution metadata. Their serialized shape does not replace the Protocol's meaning of identity, membership, composition, dependency, entity or file binding.

## Scenarios

### scenario.spec.reject-unsupported-profile — Rejecting an unsupported configuration profile

- GIVEN a project configuration whose profile_version is not 12, or whose Protocol binding does not match the installed Protocol assets
- WHEN the repository is constructed
- THEN construction fails with unsupported_profile or protocol_mismatch
- BUT a matching Profile 12 configuration with a current Protocol binding admits normally

## Selection and returned values

SpecRepository(project_root, package_root=None, *, registry_bytes=None, document_overrides=None)
admits Profile 12 and registry schema 4. The optional bytes and document overrides form an in-memory
candidate; they never authorize ambient agent reads. Construction rejects malformed identities,
unknown parents/uses/references, composition cycles, duplicate file owners within one Module and non-sibling shared
providers.

SpecTarget has id, kind="module", title, documents, references, parent, uses, files and checks. primary_document
resolves exactly one local module.md, independently of document order. select(target_id,
focus_id=None) returns the complete Module descriptor and rejects a focus that does not belong to
the target. documents(target) returns only its owned Markdown collection; spec_context(target.id) returns
the owned-plus-referenced full sources with provenance. document(path) checks
the exact concorde-document identity and sole owner. contracts(target) parses owned canonical contract definitions and checks schemas/examples offline;
contract_bindings(target) returns local participant bindings without copying provider definitions.
context_contracts(target) resolves canonical definitions from the full context, retaining their owners. dependencies(target) parses local
concorde-dependencies promises without following those edges. definitions(target) parses the
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

SpecDocument carries path, content, digest, document_id, owner, main_visible, metadata and body.
A referenced document is included only by explicit Module references and retains its sole owner. Paths are safe project-relative
POSIX file paths; symlinks and aliases fail. read_file reads a regular file, digest produces
canonical sha256 identity, strings checks unique string arrays and identifier checks stable IDs.
Failures raise SpecError with code and field; typed path/JSON failures retain their TypedDataError
contract. No lookup writes files, changes authority, silently retries a different path or reads
source to invent missing Module meaning.

## Task authoring transport values

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

### scenario.spec.task-control-values — Admit bounded task metadata without granting authority

- GIVEN a task-scope-feedback or task-identity-constraints value using the shapes above
- WHEN the Typed values interface validates it
- THEN a valid version-1 value is returned without rewriting its data
- AND unknown fields, malformed digests, other reason values, blank or duplicate reserved IDs, wrong types and unsupported versions raise TypedDataError with a code and field
- AND repeated validation of unchanged input returns the same data without project reads, writes or lifecycle effects
- BUT structural admission does not establish current task identity, complete history or phase authorization
