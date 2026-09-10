<!--
Sync Impact Report
- Version: 15.1.0 -> 16.0.0
- Bump rationale: MAJOR; adopt Protocol 4.0.0 and Architecture Profile 11. The reading entry's
  four parts are now Purpose, Requirements, Scenarios and Ontology (Entities and Relationships);
  requirements are Module-level heading sections with one SHALL statement each and no longer
  attach to scenarios; scenario, requirement and entity IDs are link anchors; tests declare the
  scenarios they verify and Specs never list tests.
- Modified principles: P6 gains the scenario verification index as deterministic evidence; the
  authoring conventions describe the new layout, the `verifies` decorator and ID anchors.
- Added sections: none.
- Removed sections: scenario-attached requirement items; the Architecture section name.
- Deferred placeholders: none.
-->

# Concorde Constitution

Version: 16.0.0. Architecture Profile 11; Workspace Protocol 15; Delivery Proposal 10.

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
Concorde adopts Protocol 4.0.0 and registry schema 3. Every Module owns a self-contained English
Spec collection whose `module.md` states its Purpose, Requirements, Scenarios and Ontology, the
Ontology holding its Entities and Relationships. A requirement is a Module-level heading section
with one SHALL statement; a scenario holds steps only and is the unit that tests verify, each test
declaring the scenario ID it exercises. Its entities list the files that realize them, as exact files or as directory prefixes ending in `/`
that bind every regular file below them; the registry mirrors that union as the Module's `files`,
entry for entry, and a file bound by several Modules is listed by each of them. Within one Module
the most specific entry owns a file. Only code-writing workers receive file contents; other workers
use their own complete Module contracts and see declared entries and bound file names only. Changes
to a shared file require fresh evidence for every listing Module. Delivery confirms declared pending
entries that now exist. Runtime, distribution, self Specs and human publication evolve together.
Older profiles have no compatibility path: the runtime, the validator and publication accept
Profile 11 only, and an older project requires an explicit migration.

### Independent Protocol standard

The Protocol text lives under `protocol/` and defines the standard independently of the Framework.
It is not a registered Module and is not required to conform to its own format. The Framework's
software Specs under `specs/` remain subject to the adopted Protocol.

### Concorde project architecture diagrams

Every Module in this repository describes its entities and directed relationships in an inline
Mermaid flowchart in the Relationships subsection of its local `module.md` Ontology, with English
accessible title and description text. Node labels are exactly the declared entity titles and every edge is
labeled with its relationship verb. The whole registered Markdown remains the source of
authority. Publication renders that source in place; generated views do not create additional
context membership. This convention applies to Concorde's software Specs and leaves the
independent Protocol unchanged.
