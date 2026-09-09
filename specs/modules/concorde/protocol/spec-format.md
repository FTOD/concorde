```concorde-document
{
  "id": "document.specs.modules.concorde.protocol.spec-format",
  "targets": [
    "module.protocol"
  ],
  "main_visible": true
}
```

# Spec format

Profile 9 configuration declares profile_version, registry, protocol and capability_configuration.
The accepted Protocol is bound by version and digest. Registry schema 2 has schema_version,
project_id, entry_target, targets, implementations and checks. Targets are Modules; each descriptor
has id, kind (module), title, documents, parent, uses, implementations, features, interfaces,
checks and diagrams. Parent is one Module ID or null. Uses and implementations contain stable IDs.
Features and interfaces declare id, title and one local document. Each Module registers exactly
one module.md; its complete collection supplies the features, interfaces and Architecture.

An Implementation descriptor has id, title, documents and files. Documents are explicitly
registered Markdown; files are an explicit nonempty set of project-relative implementation files.
Two Implementation Specs cannot bind the same file. A Module may reuse an Implementation Spec
already referenced by other Modules. Directories and generated/control files are not file bindings.

Every physical Markdown document has exactly one concorde-document block with a stable document
id, its exact targets array and main_visible boolean. IDs are globally unique across documents,
Modules, Implementation Specs and feature/interface focuses. An Implementation document cannot be
part of a Module collection. Shared Module documents, when explicitly registered, are part of each
referring Module's own collection and never cause recursive inclusion of another collection.

A concorde-dependencies block contains target_id, responsibility, selection_condition and nonempty
relied_upon_promises for each direct uses edge or submodule. It supplies local meaning; registry
edges alone do not. A concorde-contract block defines id, version, role, peer, schema, semantics and
example for exact provided/required interface agreement. Schema admission and examples are checked
offline. Diagram declarations name exact source, kind and title and may name the system-overview
recipe. Diagram output is derived under generated/diagrams, never an additional Spec authority.
