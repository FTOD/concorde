<!--
Sync Impact Report
- Version: 14.0.0 -> 14.1.0
- Bump rationale: MINOR; adopt Protocol 2.1.0 (implementation context) and the six capability-oriented Modules.
- Modified principles: P1–P10; complete Module contexts, explicit file ownership and per-consumer evidence.
- Added sections: Module architecture, implementation reuse and direct authorized maintenance.
- Removed sections: separate Domain/Service taxonomy and visibility-trimmed cognitive contexts.
- Deferred placeholders: none.
-->

# Concorde Constitution

Version: 14.1.0. Architecture Profile 9; Workspace Protocol 14; Delivery Proposal 10.

## Part A: Protocol and Framework rule sources

The independent specification standard is authored under `protocol/`. Its principles, Module and
Implementation chapters, Spec management (including Spec and Context), Required format and
canonical templates define the meaning and authored representation of project Specs.

Concorde's operational rules are authored separately in `prompts/protocol/framework-profile.md`.
They define the Framework's configuration compatibility, bounded agent contexts, execution
permissions, review evidence, worktree handoffs and authoring/publication conventions.

`generated/protocol/principles.md` combines the Protocol principles, Spec management, its Spec and
Context chapter, and Required format with those Framework rules, including P10. The two generated
kind definitions supply the Module and Implementation chapters with their canonical templates.
Read the current built rule assets; this constitution references those authorities instead of
maintaining a second copy of their text.

## Part B: Concorde project application

The explicit registry is `.concorde/specs.json`; `module.concorde` is the project entry Module.
Concorde adopts Protocol 2.1.0 and registry schema 2. Every Module owns a self-contained English
Spec collection describing its features, interfaces and internal architecture. Implementation
Specs bind explicit files with one owner per file and may be reused by multiple Modules. Only
code-writing workers receive these Implementation Specs; other workers use their own complete
Module contracts. Shared implementation changes require fresh evidence for every using Module.
Runtime, distribution, self Specs and human publication evolve together. Legacy Profile 7 utilities
may inspect old fixtures deterministically but never supply cognitive inputs to a Profile 9 agent.

### Independent Protocol standard

The Protocol text lives under `protocol/` and defines the standard independently of the Framework.
It is not a registered Module or Implementation Spec and is not required to conform to its own
format. The Framework's software Specs under `specs/` remain subject to the adopted Protocol.

### Concorde project architecture diagrams

Every Module in this repository describes its principal entities and directed relationships in
an inline Mermaid fence in its local `module.md` Architecture section. Each source declares its
project-relative Markdown path, `mermaid` kind and title, and includes English accessible title
and description text. The whole registered Markdown remains the source of authority. Publication
renders that source in place; generated views do not create additional context membership.
This convention applies to Concorde’s software Specs and leaves the independent Protocol unchanged.
