# Spec Protocol

Concorde Spec Protocol **10.0.0** describes software responsibilities through one Module Spec model.
It defines the complete specification content and **the subset intended for human reading**. It
does not prescribe a docsite's page, navigation or interaction design.

Module Specs start with Purpose, Terminology, Usage, Design and Relationships and continue in explanatory topic
pages. Implementation Specs contain the same Module's precise requirements, scenarios and canonical
interface contracts. Both are explicit document roles within one complete Module specification,
not independent owners or context filters. Formal definitions are forbidden in entries and topic
pages. Internal constraints and infrequent failures remain readable, binding obligations. Identity, ownership and implementation mappings live in associated metadata,
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

## Upgrade from Protocol 9

Version 10 separates shared provider ownership from execution composition: a shared provider
cannot be owned by one of its consumers, but dependencies may cross hierarchy levels. References
still select context independently of either relationship. The Protocol does not require every
executable entity to be a Module, or every Module to provide one executable entity.

Concorde's Framework profile uses Operation as its only executable entity and LangGraph's graph/node
vocabulary. The Framework migration guide (`docs/changes/operations-graphs.md` in the source
checkout) records renamed interfaces, incompatible records and explicit acceptance. These execution rules belong to the
Framework, not to consumer projects implementing only the independent Spec Protocol.

## Earlier upgrade from Protocol 8

Version 9 makes the intended reader explicit: general software knowledge, no project implementation
knowledge. Add early Terminology tables with one canonical definition per concept and direct links
to those tables elsewhere. Retain a normal path, concrete illustrations, causal design and visible
safety limits in explanatory reading. Move remaining technical contracts and exact executable Graph
catalogs out of topics regardless of heading syntax. Reconcile anchors, references and bound evidence.
Metadata schema 2, ownership, complete context and implementation authority remain unchanged.

This is an editorial and structural migration, not a new context filter. Passing a table-shape
check does not prove that an explanation is understandable.

## Earlier upgrade from Protocol 7

Version 8 makes document roles and formal-definition placement mandatory. Migration must:

- upgrade every paired metadata source to schema 2 with explicit `document.role`;
- retain `module.md` and explanatory topics as module-role reading, with coherent explanations;
- move all formal requirements, scenarios and canonical structured contracts to implementation-role
  units owned directly by their existing Module; topic names do not become owners;
- preserve definition IDs and valid obligations, and assign new document IDs to new split units;
- remove the retired publisher-only `concorde.publication` classification extension;
- reconcile links, references, local meaning anchors, paired ownership and all dependent evidence;
- explicitly accept the new Protocol binding; no runtime silently migrates old metadata.

The one-level complete-context model is unchanged: both roles and both source members remain in
scope. Implementation Specs are not implementation code and do not grant code access. Tool registry,
configuration and wire versions need change only when their own representation changes.

Do not treat mechanical conversion as completed semantic editing. Preserve valid guarantees and
name contradictions or unresolved facts. Moving a definition does not by itself change interface
behavior or require a contract-version increment; an actual schema/behavior change does. Old
profiles must receive an explicit migration error, not silent reinterpretation or a permanently
maintained alternate runtime. Reading completeness, structural consistency and implementation
conformance remain distinct claims.
