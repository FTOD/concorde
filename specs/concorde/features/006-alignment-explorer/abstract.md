# Feature Abstract: Alignment Explorer

`feature.concorde.explore-alignment` · specified at `module.concorde` · about 6 minutes. This feature
adds an interactive second viewing channel for developers while preserving Concorde's source
authority and evidence semantics.

## Purpose

Alignment Explorer lets a developer invoke the canonical `speckit.concorde.explore` intent through
`/concorde-explore` or `$speckit-concorde-explore`, browse from Concorde's architecture hierarchy into
implementation and tests, and see whether required intent, accepted realization, executable reality,
and evidence agree. It uses Understand Anything as the graph adapter and interactive presentation
without letting its node names redefine Concorde terminology.

The key trust rule is simple: maintained Concorde sources own intent, code and tests own executable
reality and evidence, and the explorer is a disposable read model. Missing or ambiguous evidence stays
visible as uncertainty.

## Functionality

| Surface or part | What it provides |
|---|---|
| `speckit.concorde.explore` command | Searchable, filterable navigation across modules, features, sub-features, contracts, scenarios, source artifacts, code, and tests; presented as `/concorde-explore` or `$speckit-concorde-explore` |
| Alignment view | Per-entity coverage and the evidence states `unknown`, `partial`, `verified`, and `disagrees` |
| Shared project ontology | Separate, complete-enough definitions of Concorde and pinned UA terminology plus their identity, representation, correlation, realization, evidence, disagreement, provenance, and rendering relationships |
| Adapter representation profile | Rendering-only choices for representing Concorde subjects with UA node/edge types without treating the ontologies as equivalent |
| Provenance and freshness | Source digest, implementation revision, upstream/schema pin, graph version, ontology version, and analysis time |
| Diagnostics | Missing inputs, stale projections, ambiguous matches, validation findings, and upstream ontology drift |

Every entity and alignment state links back to its basis. Name-only correlations may be presented as
candidates but cannot become verified. If the implementation graph is unavailable, the Concorde
hierarchy can still be browsed and alignment remains explicitly unknown.

**Not part of this feature**: replacing canonical Markdown, contracts, code, or tests; accepting an
implementation attempt; making model-generated summaries proof of correctness; or treating upstream
knowledge/design graphs as Concorde alignment without a later ontology revision.

## Structure

The core view is
<a href="/architecture/alignment-explorer-components.html">Concorde Alignment Explorer Components</a>
(maintained source:
[`diagrams/alignment-explorer-components.json`](diagrams/alignment-explorer-components.json)).

Concorde sources and code/tests enter through separate authority paths. The validator contributes
deterministic findings, Understand Anything contributes the implementation knowledge graph, and the
shared [project ontology](../../../../docs/ontology.md) defines both vocabularies and their
relationship. The alignment projection applies its subordinate adapter representation profile,
combines the inputs with provenance, and feeds the explore command; the projection never writes back
to its inputs.

## Logic

1. Read the maintained hierarchy and its stable IDs, authority classes, and source digest.
2. Read the implementation graph together with its upstream revision, graph version, analyzed commit,
   and normalization findings.
3. Apply the shared ontology's cross-ontology relationship rules, then its rendering-specific adapter
   representation profile, while retaining each Concorde kind and canonical relation separately.
4. Correlate specification, accepted realization, implementation, tests, and findings by explicit
   identity and provenance; keep ambiguous candidates unresolved.
5. Assign `unknown`, `partial`, `verified`, or `disagrees` using deterministic evidence, record
   coverage and freshness, and publish the disposable projection through the explore command.
6. Let the developer browse, filter, inspect the reason for each state, and return to canonical
   sources.

**Rules the implementation must keep**

- `speckit.concorde.explore` is a read-only second channel, is presented as `/concorde-explore` or
  `$speckit-concorde-explore` rather than bare `/explore`, and generated graph state never becomes
  authoritative. (FR-001, FR-017)
- Concorde stable identity, kind, authority, lifecycle, context, and provenance survive every
  adapter representation mapping and remain the user-facing semantic labels. (FR-002, FR-004,
  FR-008, FR-009)
- Alignment exposes every contributing or missing source, and only positive deterministic evidence
  can establish `verified` or `disagrees`. (FR-005, FR-006, FR-010, FR-011, FR-015)
- `docs/ontology.md` separately defines Concorde, pinned UA, and their relationship; vocabulary or
  relationship drift is explicit, and Concorde must discover, validate, digest, link-check, and
  publish the shared ontology. (FR-007, FR-008, FR-016, FR-018, FR-019)
- Freshness inputs are recorded and stale, absent, invalid, or incompatible inputs remain visible;
  architecture browsing degrades to specification-only rather than inventing alignment. (FR-012,
  FR-013, FR-014)
- Developers can search and filter the combined view by semantic identity, source, level, adapter
  representation, and evidence state. (FR-003)

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md)
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md)
- **Shared project ontology and terminology** — [docs/ontology.md](../../../../docs/ontology.md)
- **Provided explorer bundle contract** — [Alignment Explorer contract](../../architecture/contracts/alignment-explorer/contract.md)
- **Required upstream graph contract** — [Understand Anything graph contract](../../architecture/contracts/understand-anything-graph/contract.md)
- **The level this feature belongs to** — [module.md](../../module.md)
- **Parent or sub-features** — none; this is an atomic project-level feature
