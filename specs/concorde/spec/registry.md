# Registry

The registry makes a project's Module boundaries explicit. It lets developers and tools select the
contract for a responsibility without inferring ownership from directories, packages or links.
This is a topic of the [Spec Module](module.md), not another Module or a separate owner of rules.

## Independent relationships

Ownership answers which Module authors a document. Composition answers which responsibility
contains another. A use identifies a separately owned provider, while a reference selects knowledge
needed to understand the current Module. None of those relations substitutes for the others: using
a provider does not make it a child, and reading its contract does not grant its implementation.

A Module registers both its explanatory documents and its precise implementation specifications in
one owned collection. Each reading path has one metadata companion; the two members share document
identity and Module ownership. The explicit role organizes the reader's path through the collection,
not which obligations apply. A topic called Registry does not own the requirements that describe it.

Implementation bindings answer a different question: where the responsibility is realized. An entity
can name exact files or directory prefixes, and several Modules can list shared code without merging
their contracts. Pending entries record intent, not existing implementation or proof of completion.
The [value model](values.md) explains how these identities differ from snapshot and evidence records.

## Selecting context

Construct a repository from the initialized project's explicit configuration and accepted Protocol.
Select a Module to obtain its descriptor and use its Spec context query to obtain complete sources.
Selecting a scenario chooses the same owner's complete context; the focus narrows the question, not
the available specification. The source index retains each unit's owner and inclusion provenance.

References expand only once from the selected Module. A Module reference includes that provider's
owned collection; a document reference includes one whole paired unit. Provider references, ordinary
Markdown links and neighboring files do not expand the result. This makes missing necessary meaning
an explicit contract gap rather than an invitation to read more code or documentation implicitly.

The distinction matters after a document split: a consumer referencing only the old topic needs an
explicit reference to any new unit containing a relied-upon definition. A consumer referencing the
whole owner already includes its new owned units. A link is navigation, not that inclusion decision.

## Changes and affected consumers

Treat a repository instance as a snapshot. Reconstruct it after authored sources or registrations
change rather than mixing old declarations with new content. Metadata edits matter as much as prose
edits because roles, ownership, references and exact source bytes participate in context identity.

The context-user index identifies consumers of a changed Spec unit; the implementation reverse index
identifies Modules whose contracts concern a changed code file. Those indexes serve different review
questions and neither grants a writer permission to edit another owner's sources. Invalid or
ambiguous declarations stop admission instead of yielding a partially trustworthy repository.

## Precise specifications

The Spec Module owns the [requirements](requirements.md#registry),
[scenarios](scenarios.md#registry) and [query interfaces](contracts.md#registry-interface-signatures).
The [context record](contracts.md#registry-stable-id-spec-context-queries) defines exact fields,
ordering and failures; [structural validation](structure.md) explains what deterministic evidence
can and cannot establish. These are parts of the same complete Module specification.
