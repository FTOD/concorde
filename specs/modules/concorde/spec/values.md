```concorde-document
{
  "id": "document.spec.values",
  "targets": [
    "module.spec"
  ],
  "main_visible": true
}
```
# Registry values and selection

## Framework configuration and storage versions

`Profile 10` is the Framework's project-configuration compatibility version for the four-part Module model (Purpose, Scenarios, Entities, Architecture). It is distinct from Spec Protocol 3.0.0 and from registry schema 3, which versions the Framework's JSON encoding. These numbers do not classify project Modules or add concepts to the specification language.

The Framework reads `.concorde/config.json` with exactly `profile_version: 10`, `registry` (the registry's project-relative path), `protocol` (the accepted version and manifest digest) and `capability_configuration` (the typed integration/enforcement configuration). Other profile values fail with `unsupported_profile`; an incompatible Protocol binding fails with `protocol_mismatch`.

Registry schema 3 stores exactly `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. `targets` holds Module descriptors; there is no separate Implementation Spec collection, because every entity file binding is declared inside its owning Module's own documents. The separate check records configure executable verification; they are Framework execution metadata. Their serialized shape does not replace the Protocol's meaning of identity, membership, composition, dependency, entity or file binding.

## Scenarios

### scenario.spec.reject-unsupported-profile — Rejecting an unsupported configuration profile

- GIVEN a project configuration whose profile_version is not 10, or whose Protocol binding does not match the installed Protocol assets
- WHEN the repository is constructed
- THEN construction fails with unsupported_profile or protocol_mismatch
- BUT a matching Profile 10 configuration with a current Protocol binding admits normally

## Selection and returned values

SpecRepository(project_root, package_root=None, *, registry_bytes=None, document_overrides=None)
admits Profile 10 and registry schema 3. The optional bytes and document overrides form an in-memory
candidate; they never authorize ambient agent reads. Construction rejects malformed identities,
unknown parents/uses, cycles, duplicate file owners within one Module and non-sibling shared
providers.

SpecTarget has id, kind="module", title, documents, parent, uses, files and checks. primary_document
resolves exactly one local module.md, independently of document order. select(target_id,
focus_id=None) returns the complete Module descriptor and rejects a focus that does not belong to
the target. documents(target) returns only its registered Markdown collection. document(path) checks
the exact concorde-document identity and membership. contracts(target) parses locally
provided/required contracts and checks schemas/examples offline. dependencies(target) parses local
concorde-dependencies promises without following those edges. definitions(target) parses the
Module's own scenarios, requirements and entities from its registered documents; entities(target) and
scenarios(target) project that same result. entity_files(target) maps each declared file to its
owning entity. children(target) and descendants(target) return structural metadata, never inherited
context. affected_modules(paths) resolves changed files through the reverse index, which maps each
file to every Module whose entity lists it; a shared file therefore names several Modules, never one
exclusive owner.

SpecDocument carries path, content, digest, document_id, targets, main_visible, metadata and body.
A shared Module document is returned only by explicit membership. Paths are safe project-relative
POSIX file paths; symlinks and aliases fail. read_file reads a regular file, digest produces
canonical sha256 identity, strings checks unique string arrays and identifier checks stable IDs.
Failures raise SpecError with code and field; typed path/JSON failures retain their TypedDataError
contract. No lookup writes files, changes authority, silently retries a different path or reads
source to invent missing Module meaning.
