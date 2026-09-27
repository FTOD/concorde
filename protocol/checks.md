# Checks

Every check has a stable identity, a decidable statement and a severity. The identities listed
here are exactly those referenced by [`model.yaml`](model.yaml) and the other chapters.

Checks serve boundaries directly: a harness can only compute a trustworthy boundary from a
specification whose ownership, declaration sites and selections are structurally sound. They serve
understanding only indirectly, by keeping explanations attached to what they explain; no check
proves that an explanation is understandable.

Severities: **error** blocks structural conformance. **warning** is reported and does not block.

## Nodes

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.node.id` | Every node identity matches the grammar, is project-wide unique and, for requirements and scenarios, carries its prefix. | error |
| `CHK.node.type` | Every `defines` record has type `realization`. | error |
| `CHK.node.owner` | Every node resolves to exactly one owning Module. | error |
| `CHK.node.title` | Titles are nonempty. Module titles are unique in the project; concept titles are unique in the project under name normalization; realization titles are unique among the concepts and realizations of their owner. | error |
| `CHK.node.meaning` | A realization's `meaning` is a local `#anchor` resolving to nonempty prose in the same document; a concept's `explanation` names a `module` document its owner owns and an anchor there resolving to nonempty prose. | error |
| `CHK.node.explained` | An anchor group's prose is not empty and not only links, headings or fences. | warning |
| `CHK.concept.definition` | Each concept's `definition` is one nonempty sentence. | error |
| `CHK.concept.retired` | `retired`, when present, has a nonempty `reason`; only a retired concept is the source of `supersedes`. | error |
| `CHK.requirement.statement` | The first paragraph is one sentence containing `SHALL` or `SHALL NOT` exactly once; the section has no nested heading. | error |
| `CHK.scenario.steps` | Every list item is a step; the grammar of [Format](format.md) holds. | error |
| `CHK.glossary.declared` | At most one Module declares a `glossary`, it has no parent, and the declared file exists; a project whose documents or declarations name a concept declares one. | error |
| `CHK.glossary.schema` | The glossary is `schema_version` 1 with a `concepts` array sorted by `id`, and every entry has the fields of [Format](format.md#glossary) and no others; its `owner` is a registered Module. | error |
| `CHK.contract.fence` | The fence has exactly the five fields, a positive version, nonempty semantics, an offline schema using only the keywords [Format](format.md#canonical-contracts) lists and an example that satisfies it. | error |

## Documents

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.document.pair` | Both members exist and agree with the owner's `owns` on identity and owner; `role` is declared. | error |
| `CHK.document.path` | Paths are canonical project-relative POSIX, with no alias, traversal or symlink. | error |
| `CHK.document.role` | `role` is exactly `module` or `implementation`, explicitly declared. | error |
| `CHK.document.schema` | Metadata is `schema_version` 3 with the required fields and no unknown keys outside `extensions`. | error |
| `CHK.document.entry` | Each Module owns exactly one `module`-role document whose reading path ends in `module.md`; its metadata, and no other, has the `module` block, whose `owns` includes the entry. | error |
| `CHK.document.sections` | An entry has the level-2 sections Purpose, Usage and Design, each exactly once, in any order, and no level-2 section `Relationships`. | error |
| `CHK.document.prose` | Purpose is plain prose; Usage and Design are not only links, headings or diagrams. | error |
| `CHK.term.link` | Every term link, in reading or in a definition, addresses the glossary and names a declared concept. | error |
| `CHK.term.unlinked` | A document whose reading uses a concept's title outside code, headings, links and anchors links that concept somewhere. A one-word title counts only as written, a longer title in any letter case, each also with a plural `s`. | warning |

## Relations

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.relation.type` | Every relation has a registered type. | error |
| `CHK.relation.endpoints` | Source and target resolve and have permitted types. | error |
| `CHK.relation.site` | Every relation is declared at its site: a metadata relation is a `relates` whose source is a realization that document defines or its owning Module; a concept's relations are in its glossary entry. | error |
| `CHK.relation.meaning` | A Module relation's `meaning` is a local anchor into the entry, or a qualified anchor into another document the source Module owns, resolving to nonempty prose. | error |
| `CHK.registry.mirror` | The registry has exactly one record per Module, with the entry's path and every field of its `module` block, equal to that block. | error |
| `CHK.owns.unique` | Each document is owned exactly once. | error |
| `CHK.defines.once` | Each node has exactly one defining document. | error |
| `CHK.defines.role` | Requirements, scenarios and contracts are defined only in `implementation` documents. | error |
| `CHK.contains.acyclic` | Composition is acyclic. | error |
| `CHK.contains.single-parent` | A Module has at most one parent. | error |
| `CHK.contains.root` | Exactly one Module has no parent. | warning |
| `CHK.uses.no-self` | A Module does not use itself. | error |
| `CHK.uses.unique` | A Module uses each provider at most once. | error |
| `CHK.relies-on.owned` | Every identity in `relies_on` names a requirement, scenario, contract or concept owned by the relation's target. | error |
| `CHK.relies-on.linked` | When `relies_on` is present, every stable-identity link from the relation's `meaning` section to a node of the target names a listed node. | error |
| `CHK.includes.no-self` | A Module does not include itself or a document it owns. | error |
| `CHK.includes.unique` | No duplicate `(kind, target)` pairs. | error |
| `CHK.includes.reason` | Each `includes` has a nonempty `reason`. | error |
| `CHK.includes.redundant` | A spec inclusion whose documents are all already selected by `owns`, `contains`, `uses` or another inclusion is reported. | warning |
| `CHK.external.exists` | External material exists at the declared path and is tracked by the project's version control. | error |
| `CHK.external.no-overlap` | External paths overlap no document member and no realization entry. | error |
| `CHK.binds.exists` | Non-pending entries exist; exact entries are files and `/` entries are directories. | error |
| `CHK.binds.disjoint` | No two realizations in one Module list the same entry. | error |
| `CHK.binds.no-spec` | No document member, generated output or control record is bound; a bound directory contains no document member. | error |
| `CHK.binds.installed` | No directory entry covers an installed file, which is bound only by its exact path. | error |
| `CHK.binds.pending-subset` | `pending` is a subset of `entries`, and pending entries do not exist. | error |
| `CHK.binds.unbound` | Every version-controlled file is bound by some Module, unless it is a document member, generated output, external material or a control record such as the project registry and configuration. | error |
| `CHK.narrows.acyclic` | `narrows` never relates a concept to itself, directly or through other `narrows`. | error |
| `CHK.contrasts.required` | A concept and a Module other than its owner whose titles normalize equal have a `contrasts` between them. | error |
| `CHK.contrasts.once` | At most one `contrasts` is declared per unordered pair, and it has a nonempty `reason`. | error |
| `CHK.relates.source` | A `relates` source is the concept whose entry declares it, a realization the declaring document defines, or the declaring document's owning Module. | error |
| `CHK.relates.verb` | `verb` is nonempty; `(source, verb, target)` is unique. | error |
| `CHK.participates.version` | The contract exists and the declared version is its current version. | error |
| `CHK.participates.complementary` | Internal peers declare complementary roles for the same contract and version and name each other. | error |
| `CHK.participates.unique` | `(contract, peer, role)` is unique per Module. | error |
| `CHK.verifies.resolves` | Every verified scenario identity exists. | error |
| `CHK.evidence.no-spec-coverage` | Reading content contains no test-declaration syntax outside fences. | error |

**Name normalization** for `CHK.node.title` and `CHK.contrasts.required`: Unicode NFKC, case
folding, and every run of whitespace, hyphens and underscores treated as one space, trimmed.
`CHK.node.title` compares concepts with each other; `CHK.contrasts.required` compares concepts with
Modules, never a concept with its own Module.

## Views

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.view.marked` | Every diagram in reading is a `d2` block; a checked one lies in `module` reading, and every other is marked `illustrative`. A Mermaid block is an error. | error |
| `CHK.view.subset` | A checked diagram uses only the semantic subset of D2. | error |
| `CHK.view.nodes` | Every shape of a checked diagram resolves to exactly one node, Module or, inside a realization, bound file. | error |
| `CHK.view.nesting` | Every nesting of a checked diagram matches a declared `contains`, the ownership of a node or the binding of a file. | error |
| `CHK.view.edges` | Every edge of a checked diagram matches a declared relation in its direction: an unlabelled edge between two Modules a `uses`, and a labelled edge a `relates`; an edge touching a node is labelled and no edge touches a file. | error |

## Reconciliation

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.context.reconciled` | For every Module M and every `q ∈ Requires(M)`, `satisfied(q, Spec(M))` holds. | error |

## Limits of the checks

These checks are weaker than the obligations they serve:

| Check | What it does not establish |
| --- | --- |
| `CHK.relies-on.linked` | That `relies_on` lists a relied-upon promise the explanation never links to. |
| `CHK.term.unlinked` | That a term is linked where it is first used, or that a word matching a title is used in the term's sense; an ordinary word spelled like a one-word title in the same letter case is reported too, and linking or rephrasing it is the answer. |
| `CHK.relation.meaning` | That a parent's or consumer's explanation of a collaboration is adequate. |
| `CHK.node.explained` | That prose explains its node; it detects empty regions only. |
| `CHK.contrasts.required` | Collisions that normalization misses. Unrelated same-named nodes also trigger it; declaring the `contrasts` with its reason is then the correct answer, not an escape. |
| `CHK.view.edges` | That a drawn label describes the declared relation accurately. |
| `CHK.participates.version` | That the participant behaves as the contract says; that is implementation conformance. |

Not checked at all: whether a requirement is true of the implementation, whether reading is
sufficient for its reader, whether a scenario is worth having, and whether an illustrative block is
accurate.

## Tool obligations

These are requirements on tools rather than checks of declarations:

- Context selection is one level and never follows a selected Module's own relations; term
  selection closes over the glossary only.
- Documents are registered, never discovered from the filesystem or links.
- Coverage is read from test declarations without executing tests.
- Derived views are never written into reading files.
- A harness keeps every task boundary within the composition rules of [Boundaries](boundaries.md):
  writes only within write sets of bound Modules, write implies read, reads only within their read
  sets, and task material adds no source.
