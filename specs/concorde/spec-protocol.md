```concorde-document
{
  "id": "document.concorde.spec-protocol",
  "targets": [
    "domain.concorde"
  ],
  "main_visible": true
}
```

# Concorde Spec Protocol

The Concorde Spec Protocol is the specification standard within Concorde Framework. It defines the
organization, meaning and file format of conforming Specs. The Framework also contains Skills,
validation, Agent orchestration and developer tools that apply the Protocol. This project's own Spec
collection follows the same Protocol as consumer projects. The Protocol governs each project's
Spec organization throughout authoring, validation and evolution: Domain/Service/Module meanings,
registered document collections, Domain main Specs, shared documents and declared diagrams.
Installation distributes the rules; it is one application of the Protocol.

The canonical authoring source for Concorde Spec Protocol 1.2.0 is `prompts/protocol/principles.md`, with
Domain/Service/Module definitions under `prompts/protocol/kinds/`. The Framework bundles these rules
with its separately authored execution profile. That distribution mechanism does not define what
a Domain or a Spec document means.

## Specification model

An **Ontology** defines a Domain's entities, their types and meanings, and their named, directed
relationships. The term does not require OWL, RDF or another formal ontology language.

| Category | Meaning | Required view |
| --- | --- | --- |
| Domain | A business or problem-space scope | Entity types, relationships, responsibilities, rules, interactions and outcomes |
| Service | A component kind offering a consumer capability | Features, usage and complete interaction contracts |
| Module | A component kind exposing an API | Provided and required interfaces, preconditions, results, effects and errors |

A **Spec target** is a registered Domain, Service or Module described by a complete collection of
Spec documents. Its identity is independent of document paths. A Feature or API can focus work
within that target without replacing its complete context.

Domain narrowing, component composition and component participation in Domains are independent
relationships. For example, a Transfer Service may participate in both Banking and Audit without
becoming two components. Account and Transfer can be entities in a Domain's Ontology without each
becoming a new Spec target or file.

## Document organization and file format

| File or declaration | Purpose and rules |
| --- | --- |
| `ontology.md` | Exactly one per Domain's registered collection; the local main Spec, visible to Main and referenced only by that Domain |
| Topic Spec document | A registered Markdown document explaining a workflow, routing view, Feature, API or other part of the target's behavior; filenames remain flexible |
| Shared Spec document | One physical Markdown truth explicitly referenced by several targets; each receives the same source bytes as part of its context |
| `concorde-document` block | Declares a stable physical document ID, exact referencing targets and main visibility |
| `concorde-participants` block | Describes each directly participating component's Domain-local role, selection condition and relied-upon promises |
| `concorde-contract` block | Declares a versioned provided or required interface, its schema, semantics and example |
| Registered diagram JSON | Supplies a named view; a Domain has exactly one architecture declaration with `recipe: system-overview` |

A Domain main Spec defines its scope and contains an **Ontology** section. It groups relevant entity
types and explains relationships within and across the boundary. Its System overview is rendered
with Archify and embedded on the main page; missing business information is declared honestly,
including in an initialized project stub. Additional workflow and contract documents carry detail.

The main page is chosen from registered members by the exact filename `ontology.md`, independently
of member order. Main-document identity does not grant authority to adjacent files. Each target
still receives its entire registered collection: local Target Spec plus explicitly referenced Shared
Specs. One shared file contributes only that file, not every other document of its referencing targets.

`SKILL.md` is a Framework instruction format, not an additional Domain/Service/Module kind or a
Concorde Spec Protocol document role. Likewise registry storage, version binding, digests, Python Capability
modules and model-process policies are explained in the Framework's implementation contracts.

## Guidance for organizing explanations

The Protocol recommends a main page that establishes overall understanding of the Domain, with
more detailed explanations in the relevant child Domain, Service, Module or topic Spec. A main
page can still explain internal structure and cross-domain collaborations when that helps the
reader. There is no required abstraction hierarchy or black-box presentation.

Prefer a clear source for detailed definitions and explain their local use where they are referenced.
Brief introductions and navigation links can help readers without repeating all definitions on the
main page. An implementing system's overview need not restate the complete model or file format of
the protocol it uses. Completeness is assessed across the registered context rather than each page
in isolation; a link does not itself add a document to an agent's context.

These are writing recommendations. Page organization and amount of detail alone do not fail
validation or block review. Missing or contradictory promises needed by an actual task remain
substantive Spec issues under the existing rules.

## Protocol design principles

P1 distinguishes scope from component structure and requires a meaningful Ontology. P2 defines the
consumer view appropriate to each target kind. P3 makes a complete, explicit document collection the
unit of Spec context, with `ontology.md` as the Domain reading entry. P4 requires conformance to the
accepted Concorde Spec Protocol while distinguishing project-specific application from universal modeling rules.
The Framework execution profile (P5–P10) explains how this software uses those Specs in agent work.
A routing view may be a separate document in the same collection; a hyperlink never substitutes for
explicit context membership. Structural checks prove format and contract consistency, not that every
future business task is answerable.

## feature.concorde.evolve-protocol


A Concorde Spec Protocol change affects all consumers, not just Concorde's self-description. A developer authors
principles and corresponding schemas, runtime admission, context grants, templates, installation
and publication behavior together. The distributable Protocol is versioned and hashed. Existing
projects do not silently acquire a new meaning: they must explicitly accept compatible bindings.
Source Profile 8 rejects Profile 7 for agent work, and there is no migration capability; Profile 7
projects are rejected outright. Legacy deterministic readers remain diagnostic utilities only.

Changing the Concorde Spec Protocol is an explicitly authorized version cutover, not ordinary work performed
under the version being replaced. The previous Protocol remains authoritative for its published
version and for unrelated work, but it does not validate the incomplete intermediate state of its
own replacement. The developer first reconciles every normative asset, runtime boundary, self Spec,
consumer-facing migration and executable check. Only the completed candidate is validated under its
own proposed rules. Until that validation succeeds, the candidate is unpublished, cannot be bound by
consumer projects and cannot be described as the active Protocol. This bootstrap exception is limited
to the coordinated Protocol cutover and does not authorize ordinary changes to bypass the active
workflow.

Concorde's own code is changed under the user's authorized refactor task. Product Agent Graphs
must continue to obey these same rules. Structural checks cannot establish semantic completeness
for every future task; a successful task-specific assessment is bounded by its recorded context.

The `ontology.md` and System overview requirements enter Concorde Spec Protocol 1.2.0. Existing collections
must designate their own local main Specs and register their overview sources before accepting this
revision. Service/Module filenames stay unrestricted. Installed project bindings are never silently
rewritten; Framework admission rejects a mismatched rule revision until the developer accepts it.
