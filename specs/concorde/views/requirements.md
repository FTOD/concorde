# Views requirements

These are the precise Module-wide obligations of [Views](module.md). They constrain implementations,
including externally observable behavior; they are not a description of current code or a separate
Spec owner. Read the Module entry first for purpose, correct use and design. Concrete situations and
interface definitions live in the Module-owned [scenarios](scenarios.md) and [contracts](contracts.md),
with explanatory topics linked from the Module entry.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../module.md#terminology) | Defined in Concorde Framework. |
| [Implementation Specs](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |
| [Publication candidate](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Promotion](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Entity](../module.md#terminology) | Defined in Concorde Framework. |
| [Scenario](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |

### req.views.registry-derived-pages — Pages and navigation derive from the registry

Publication SHALL derive Module Spec pages and their navigation only from the explicit registry.

Every published Module Spec is traceable to a registered entry. The optional project introduction
and project-owned custom docs are presentation surfaces outside that membership.
Both Spec sidebars follow registry parentage alone; a document's explicit publication collection
selects its reading tab without changing ownership or context. See
[req.views.no-directory-scanning](#req.views.no-directory-scanning).

### req.views.custom-docs — Separate project documentation

Publication SHALL support project-owned custom docs through independent tabs outside Module Spec registration and agent Spec context.

The generic template defaults to Module Specs alone until a registered companion explicitly selects
Implementation Specs, and publishes no unregistered Projections section. See
[custom docs](scenarios.md#scenario.views.custom-docs) for configuration and migration.

### req.views.reading-collections — Reading tabs preserve one complete Module specification

Publication SHALL preserve the same document ownership, canonical definitions and complete Spec context when a registered companion is assigned to Implementation Specs.

Module Specs is the explanation-first reading path; Implementation Specs contains precise normative
obligations, scenarios and interface details. Both remain human-readable specification content.
Publication classification never makes a document optional for context resolution or review.
The [collection scenarios](scenarios.md#scenario.views.reading-collections) define admission,
navigation and rejection of missing or invalid document roles.

### req.views.no-directory-scanning — No directory scanning or link-based discovery

Publication SHALL NOT discover Spec documents by scanning directories or following links.

### req.views.one-page-per-document — One canonical page per registered document

A physical Spec document SHALL publish at exactly one canonical page regardless of how many Modules reference it.

### req.views.current-internal-links — Published internal links resolve

Publication SHALL promote only a candidate in which every internal navigation link retained in its published documents resolves to an available destination and, when specified, an existing anchor.

The guarantee covers the site's own published pages, including enabled reading collections.
Cross-Module references are valid navigation and do not establish document ownership and references or expand
Spec context. External destinations retain their existing handling; publication does not promise
the continued availability of another website. Current-owner legacy aliases and failure
behavior are defined in [publication](scenarios.md#scenario.views.publish-legacy-redirect)
and [pipeline](scenarios.md#scenario.views.validate-candidate-mismatch).

### req.views.no-agent-context-grant — No extra agent context from a rendered view

A rendered page or generated view SHALL NOT itself grant an agent invocation additional Spec context beyond its own host-bound target snapshot.

### req.views.diagram-source-identity — Mermaid fence is the sole diagram source

An inline Mermaid fence in a Module's Relationships subsection SHALL be its sole authored diagram source.

### req.views.no-external-diagram-record — No external diagram record or output

Publication SHALL create no external diagram record or `generated/diagrams` output.

The authored fence is the sole source; publication produces no external record derived from it.

### req.views.no-docsite-graph-view — No docsite graph view

Publication SHALL NOT expose the former Module, Scenario or entity-relationship graph view.

This removes the docsite graph page and route, Graph navigation entry, graph-specific UI,
architecture-graph projection and artifact, and resources or dependencies used exclusively for that
feature. It also applies to the publishing template supplied to consumer projects. Dependencies
and resources still needed for ordinary reading, navigation or inline Mermaid rendering remain.

Concorde's own source-checkout site has an independent Agent Graphs page describing actual runtime
execution. It is excluded from the consumer template and does not derive a graph from the Spec
registry. See [Agent execution publication](scenarios.md#scenario.views.agent-graphs).

### req.views.agent-graphs — Concorde-only execution diagrams

Concorde's own docsite SHALL publish an Agent Graphs tab whose LangGraph nodes and edges come from
the current executable factories and whose explanations distinguish execution, wrappers and
unimplemented design.

### req.views.production-preview-isolation — Production builds preserve preview output

A production build SHALL NOT clear or overwrite the development preview's generated directory.

### req.views.hash-format — Digests use the sha256 hex format

Every content or source digest SHALL be `sha256:` followed by 64 lowercase hexadecimal digits.

### req.views.safe-relative-paths — Member paths are safe relative POSIX paths

Every member path SHALL use POSIX separators without absolute paths, backslashes, empty, dot or traversal components, or symlinks.

### req.views.promote-atomic — Promotion restores the prior destination on failure

`promoteCandidate` SHALL attempt to restore the prior destination on a failed move or removal.

### req.views.promote-requires-checked-candidate — Promotion runs only on checked candidates

`promoteCandidate` SHALL NOT be called on unchecked or stale output.

### req.views.no-contract-context-expansion — Contract edges do not expand loaded context

The registry loader SHALL NOT follow a `concorde-contract` edge to import additional Module context.
