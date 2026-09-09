```concorde-document
{
  "id": "document.shared.registry-contracts",
  "targets": [
    "module.registry"
  ],
  "main_visible": true
}
```

# Registry values and selection

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
