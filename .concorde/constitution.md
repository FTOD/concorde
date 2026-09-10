<!--
Sync Impact Report
- Version: 14.1.0 -> 15.0.0
- Bump rationale: MAJOR; adopt Protocol 3.0.0 (one Spec kind with four mandatory parts), drop
  Implementation Specs, Feature/Interface registration and external diagram sources.
- Modified principles: P1–P10; entity file listings replace Implementation Spec bindings, pending
  files are confirmed at delivery, planners see file names but never contents.
- Added sections: four-part Module Specs, entity file listings.
- Removed sections: Implementation Spec reuse, external diagram-source declarations, the retained
  pre-Profile-10 compatibility utilities and their fixtures.
- Deferred placeholders: none.
-->

# Concorde Constitution

Version: 15.0.0. Architecture Profile 10; Workspace Protocol 15; Delivery Proposal 10.

## Part A: Protocol and Framework rule sources

The independent specification standard is authored under `protocol/`. Its principles, Module
chapter, Spec management (including Spec and Context), Required format and canonical templates
define the meaning and authored representation of project Specs.

Concorde's operational rules are authored separately in `prompts/protocol/framework-profile.md`.
They define the Framework's configuration compatibility, bounded agent contexts, execution
permissions, review evidence, worktree handoffs and authoring/publication conventions.

`generated/protocol/principles.md` combines the Protocol principles, Spec management, its Spec and
Context chapter, and Required format with those Framework rules, including P10. The generated
Module kind definition supplies the Module chapter with its canonical templates. Read the current
built rule assets; this constitution references those authorities instead of maintaining a
second copy of their text.

## Part B: Concorde project application

The explicit registry is `.concorde/specs.json`; `module.concorde` is the project entry Module.
Concorde adopts Protocol 3.0.0 and registry schema 3. Every Module owns a self-contained English
Spec collection whose `module.md` states its Purpose, Scenarios, Entities and Architecture. Its
entities list the exact files that realize them; the registry mirrors that union as the Module's
`files`, and a file shared by several Modules is listed by each of them. Only code-writing
workers receive file contents; other workers use their own complete Module contracts and see file
names only. Changes to a shared file require fresh evidence for every listing Module. Delivery
confirms declared pending files that now exist. Runtime, distribution, self Specs and human
publication evolve together. Older profiles have no compatibility path: the runtime, the validator
and publication accept Profile 10 only, and an older project requires an explicit migration.

### Independent Protocol standard

The Protocol text lives under `protocol/` and defines the standard independently of the Framework.
It is not a registered Module and is not required to conform to its own format. The Framework's
software Specs under `specs/` remain subject to the adopted Protocol.

### Concorde project architecture diagrams

Every Module in this repository describes its entities and directed relationships in an inline
Mermaid flowchart in its local `module.md` Architecture section, with English accessible title
and description text. Node labels are exactly the declared entity titles and every edge is
labeled with its relationship verb. The whole registered Markdown remains the source of
authority. Publication renders that source in place; generated views do not create additional
context membership. This convention applies to Concorde's software Specs and leaves the
independent Protocol unchanged.
