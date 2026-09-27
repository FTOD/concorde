# Context

Context is the information explicitly made available to a reader of one Module. Knowing that a
document exists does not make it available; neither does linking to it or naming a word it
explains. Only declared relations grant context, and a term link grants only the term's definition.

This chapter defines the read side of the Protocol's boundary purpose: the four context
channels, how a Module's context is selected, term selection, the reconciliation of what relations
grant against
what they require, and context identity. The write side is in [Boundaries](boundaries.md). Because
the reconciliation guarantees that a Module's context holds every definition its own Spec relies
on, the same selection is also what a human reader of the Module needs open beside it.

## Four channels

| Channel | Granted by | Contains | Authority conveyed |
| --- | --- | --- | --- |
| `spec` | `owns`, `contains`, `uses`, `includes` of kind `module` or `document` | both members of each selected document | read only |
| `term` | the concepts a Module owns, `mentions`, `narrows`, `supersedes`, concept-targeted `relates` and `relies_on` | the glossary entries of the selected concepts | read only |
| `implementation` | `binds` | the **names** of bound paths | none |
| `external` | `includes` of kind `external` | pinned third-party material | read only |

The channels stay separate so that "may read this Module's promises" never implies "may read or
change its code", and knowing what a word means never implies reading how its owner works. Whether a
task receives implementation contents, read-only or writable, is part of its task boundary; see
[Boundaries](boundaries.md).

## Expressions

`context_grants` and `context_requires` in [`model.yaml`](model.yaml) use this expression language:

```text
spec(target)             the target document
spec(selection)          for a contains or uses with relies_on: the target's entry and the
                         documents defining the listed nodes; otherwise every document the
                         target Module owns
spec(definer(target))    the document that defines the target node; for a Module target,
                         that Module
term(target)             the glossary entry of the target concept
external(target)         the pinned material at the target path
implementation(target)   the name of the target path
none                     nothing
```

A requirement `spec(D)` naming a document D is satisfied when D is in the Module's spec channel. A
requirement `spec(N)` naming a Module N is satisfied when at least one document N owns is in it.

## Spec context selection

Let `D(M)` be the documents Module M owns, and `members(U)` the reading and metadata members of a
document U.

```text
Spec(M)        = D(M)
               ∪ ⋃ { selection(r) : r a contains, uses or spec includes declared by M }
SpecContext(M) = ⋃ { members(U) : U ∈ Spec(M) }

selection(r to Module N) = { entry(N) } ∪ { definer(x) : x ∈ r.relies_on }  if relies_on present
                         = D(N)                                               otherwise
definer(concept c)       = the document c's entry names as its explanation
selection(includes document U) = { U }
```

Selection is one level. A selected Module contributes its owned documents, never the documents its
own relations select. Parentage, dependency and inclusion of the target, term links,
participation, other Markdown links, directory neighbourhood and implementation bindings add no
document. Because
expansion is not recursive, cycles among Modules are harmless, and every member of a read set is
explained by the one declaration that selected it.

A scenario query resolves the scenario's owner and selects that owner's whole context. It never
trims to the scenario, and never selects the consumer that happened to read it.

Every selected document contributes **both** members whole. No excerpt, summary, rendered view or
diagram export substitutes for a complete document.

## Term selection

A reader needs the meaning of every term the documents it reads use, and nothing more. Term
selection gives it exactly those definitions:

```text
Seeds(M) = { c : owner(c) = M }
         ∪ { c : a document in Spec(M) mentions c }
         ∪ { c : c ∈ r.relies_on, r a contains or uses of M }
         ∪ { c : a relates declared in a document in Spec(M) targets c }
Terms(M) = the least set containing Seeds(M) and closed under
           c ∈ Terms(M) mentions, narrows, supersedes or relates to concept d  ⇒  d ∈ Terms(M)
TermContext(M) = { entry(c) : c ∈ Terms(M) }
```

Every selected document counts, including the provider documents a `uses` selects, because the
reader reads them too. A Module always receives the definitions of its own concepts, since it is
entitled to change them.

The closure is the Protocol's only recursive selection. It runs inside the glossary, adds one
sentence per concept and never adds a document, so a reader whose definitions use further terms
understands them without widening what it reads. `contrasts` adds nothing: the warning is in the
entry that declares it.

Each selected entry is available whole: identity, title, owner, definition and explanation
reference. The explanation it references stays a document of the owner, readable only when
`Spec(M)` selects it.

## Reconciliation

```text
Requires(M) = ⋃ { r.context_requires : r declared in the metadata or reading
                                        of a document M owns, including its entry }

CONFORMANCE:  ∀ q ∈ Requires(M) :  satisfied(q, Spec(M))
```

A `relates` to a realization or a Module, and a `participates`, require the document that defines
their target. A Module that declares one without having that document in its context fails
`CHK.context.reconciled`. The repair is an explicit grant: a `uses` or `contains` that selects the
document, or an `includes` that states a reason. Relations that target a concept require nothing,
because they grant its definition themselves.

The check is exact, because a node has exactly one defining document. A `uses` or `contains` that
narrows its grant with `relies_on` selects the documents defining the listed promises, so the
narrowing is exact as well. What no check establishes is that the list names every promise the
Module actually relies on; `CHK.relies-on.linked` catches every one the explanation links to.

## Implementation context

```text
ImplementationContext(M) = ⋃ { entries of M's realizations }
ImplementationContext(scenario S) = ImplementationContext(owner(S))
ProjectImplementation = ⋃ { ImplementationContext(M) ∪ ExternalContext(M) : every Module M }
```

Exact entries and files below directory prefixes resolve under an explicit deterministic exclusion
rule. Pending entries record intent without pretending that missing content exists.

Document members never belong to implementation context. When another Module binds the same file,
a change to it concerns that Module too; this adds neither that Module's Specs nor its code to this
reader's context. A Module with no bindings has an empty implementation context, which does not
prove it has no realization.

## External context

```text
ExternalContext(M) = ⋃ { readable files below M's external inclusions }
```

Only the selecting Module's own external inclusions count; a selected Module does not bring its
own. External material MUST be pinned by the project's version control, for example as a
submodule at a fixed commit, so that its content is identified by the checkout rather than by a
second declared revision. A tool MAY exclude media and archives by a documented deterministic rule.
An undeclared network fetch or an installed dependency's sources MUST NOT substitute for declared
material. External material supplies no promise absent from the Spec.

## Context identity

A resolved context is identified by its selected sources, its selected terms and the declarations
that selected them, so a harness can tell whether anything inside a boundary changed since a check.
Every source record carries document identity, owner, path, member role (`reading` or `metadata`),
an exact-byte SHA-256 digest, and every relation that selected it. Every term record carries the
concept's whole entry and every declaration that selected it. External entries carry one tree
digest each.

The identity changes, even when the set of paths is unchanged, on:

- any byte change in either member of a selected document, including whitespace;
- any change to a selected glossary entry, or a change of which entries are selected;
- a change to the declarations that selected the context, including removing a redundant inclusion;
- an ownership transfer;
- a change to pinned external material.

What a tool does with evidence bound to a previous identity is the tool's policy.

## Visibility

The resolved context is the exact visibility scope of a bounded reader: every selected source and
every selected glossary entry is available whole, and no unselected source or entry is visible. The
glossary file as a whole is not a source of any context. How a tool makes it available is not part
of the Protocol. A tool MAY also supply task material such as changes since a baseline; such
material adds no source and replaces none. A reader that opened only some granted files still
received the complete context: missing meaning is judged against the full granted scope.

## Gaps

A missing definition is a semantic gap even after structural resolution succeeds. Record the needed
promise, its owner when known, the selected Module, the context identity and the blocked step. Do
not follow a selected Module's own relations or a prose link to repair it. An additional explicit
selection is a new context, not a retrospective claim that the previous one was complete.
