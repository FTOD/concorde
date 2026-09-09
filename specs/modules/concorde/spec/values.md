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

`Profile 9` is the Framework's project-configuration compatibility version for the
Module/Implementation model. It is distinct from Spec Protocol 2.1.0 and from registry schema 2,
which versions the Framework's JSON encoding. These numbers do not classify project Modules or
add concepts to the specification language.

The Framework reads `.concorde/config.json` with exactly `profile_version: 9`, `registry` (the
registry's project-relative path), `protocol` (the accepted version and manifest digest) and
`capability_configuration` (the typed integration/enforcement configuration). Other profile values
fail with `unsupported_profile`; an incompatible Protocol binding fails with `protocol_mismatch`.

Registry schema 2 stores exactly `schema_version`, `project_id`, `entry_target`, `targets`,
`implementations` and `checks`. `targets` holds Module descriptors and `implementations` holds
Implementation Spec descriptors. The separate check records configure executable verification;
they are Framework execution metadata. Their serialized shape does not replace the Protocol's
meaning of identity, membership, composition, dependency or file ownership.

## Selection and returned values

SpecRepository(project_root, package_root=None, *, registry_bytes=None, document_overrides=None)
admits Profile 9 and registry schema 2. The optional bytes and document overrides form an in-memory
candidate; they never authorize ambient agent reads. Construction rejects malformed identities,
unknown parents/dependencies, cycles, unknown Implementation references and duplicate file owners.

SpecTarget has id, kind="module", title, documents, parent, uses, implementations, features,
interfaces, checks and diagrams. primary_document resolves exactly one local module.md, independently
of document order. ImplementationSpec has id, title, documents and files. The two collections are
separate. implementation_users maps each Implementation ID to all using Module IDs;
file_implementations maps each exact bound file to its unique Implementation Spec ID.

select(target_id, focus_id=None) returns the complete Module descriptor and rejects a foreign focus.
documents(target) returns only its registered Markdown collection. document(path) checks the exact
concorde-document identity and membership. diagram_sources(target) returns only declared sources.
contracts(target) parses locally provided/required contracts and checks schemas/examples offline.
dependencies(target) parses local concorde-dependencies promises without following those edges.
children(target) and descendants(target) return structural metadata, never inherited context.

implementation_specs(target) selects the referenced descriptors. implementation_documents(target)
reads those registered implementation documents only when the caller is an authorized code writer.
implementation_paths(target) returns exact declared files, including planned files not yet created.
implementation_files(target) returns existing bound regular files, with no directory traversal.
affected_modules(paths) resolves changed source or Implementation documents through the reverse
index. These deterministic lookups convey identity and impact, not an execution grant.

SpecDocument carries path, content, digest, document_id, targets, main_visible, metadata and body.
A shared Module document is returned only by explicit membership. An Implementation document is
never Module context. Paths are safe project-relative POSIX file paths; symlinks and aliases fail.
read_file reads a regular file, digest produces canonical sha256 identity, strings checks unique
string arrays and identifier checks stable IDs. Failures raise SpecError with code and field;
typed path/JSON failures retain their TypedDataError contract. No lookup writes files, changes
authority, silently retries a different path or reads source to invent missing Module meaning.

## Inline architecture membership

A Mermaid fence in a registered document belongs to that document’s complete context. Its source
path, kind and title are identified beside the fence. No directory walk or additional document
registration is needed, and `diagram_sources(target)` returns `[]` when there are no external
source declarations. New authoring uses `diagrams: []`; old external JSON diagrams require an
explicit source migration. Reading an inline diagram never adds another Module’s context.
