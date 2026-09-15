# Spec Protocol

Concorde Spec Protocol **7.0.0** describes software responsibilities through one Module Spec model.
It defines the complete specification content and **the subset intended for human reading**. It
does not prescribe a docsite's page, navigation or interaction design.

Reading starts with Purpose, Usage, Design and Relationships, followed by precise requirements,
scenarios and other necessary detail. Internal constraints and infrequent failures remain readable,
binding obligations. Identity, ownership and implementation mappings live in associated metadata,
not giant inventories mixed into the main explanation. Schemas and examples can remain reading
when they express an interface developers need to understand.

A registered Markdown file and its `.md.json` companion form one document unit with one identity
and owner. Explicit Module references select complete units once. Both source members enter the
complete context; a readable projection never replaces it. Metadata points to canonical local
reading meaning instead of copying responsibilities and obligations into a second authority.

## Read the standard

1. [Principles](principles.md): complete content, the readable subset, completeness and conformance.
2. [Module specifications](module.md): purpose, usage, design, relationships and precise obligations.
3. [Spec management](spec-management.md): identity, ownership, collaboration and interface agreements.
4. [Spec and Context](spec-management/spec-and-context.md): deterministic complete source selection.
5. [Required format](format.md): reading structure, metadata, anchors, declarations and diagrams.
6. Templates: [Module](templates/module.md) and [Scenario fragment](templates/scenario.md).

These are chapters of one standard, not project Module Specs themselves. A project does not need
Concorde Framework, a particular publisher or a particular agent runtime to understand the language.
Configuration, registry serialization, worker wire versions and execution permissions are separate
implementation agreements, not additional Protocol versions.

## Upgrade from Protocol 6

Version 7 is intentionally incompatible with the enclosing two-part format. Migration must:

- separate reading from mechanical declarations while preserving readable duties and stable IDs;
- register and validate paired source members with one owner and one-level reference semantics;
- reorganize entry reading as Purpose, Usage, Design, Relationships, then detailed obligations;
- replace the entity-inventory chapter with coherent design/collaboration explanations;
- permit scoped diagrams without inventing entities or weakening relationship meaning;
- reconcile anchors, references, file exclusions, metadata edits and all dependent evidence;
- explicitly update the accepted Protocol binding and the tool's corresponding format versions.

Do not treat mechanical conversion as completed semantic editing. Preserve valid guarantees and
name contradictions or unresolved facts. Moving a definition does not by itself change interface
behavior or require a contract-version increment; an actual schema/behavior change does. Old
profiles must receive an explicit migration error, not silent reinterpretation or a permanently
maintained alternate runtime. Reading completeness, structural consistency and implementation
conformance remain distinct claims.
