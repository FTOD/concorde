# Context

Context is the information explicitly made available to a reader of one Module. Knowing that a
document exists does not make it available; neither does linking to it or naming a word it defines.
Only declared relations grant context.

This chapter defines the read side of the Protocol's boundary purpose: the three context
channels, how a Module's context is selected, the reconciliation of what relations grant against
what they require, and context identity. The write side is in [Boundaries](boundaries.md). Because
the reconciliation guarantees that a Module's context holds every definition its own Spec relies
on, the same selection is also what a human reader of the Module needs open beside it.

## Three channels

| Channel | Granted by | Contains | Authority conveyed |
| --- | --- | --- | --- |
| `spec` | `owns`, `contains`, `uses`, `includes` of kind `module` or `document` | both members of each selected document | read only |
| `implementation` | `binds` | the **names** of bound paths | none |
| `external` | `includes` of kind `external` | pinned third-party material | read only |

The channels stay separate so that "may read this Module's promises" never implies "may read or
change its code". Whether a task receives implementation contents, read-only or writable, is part
of its task boundary; see [Boundaries](boundaries.md).

## Expressions

`context_grants` and `context_requires` in [`model.yaml`](model.yaml) use this expression language:

```text
spec(target)             the target document
spec(selection)          for a contains or uses with relies_on: the target's entry and the
                         documents defining the listed nodes; otherwise every document the
                         target Module owns
spec(definer(target))    the document that defines the target node; for a Module target,
                         that Module
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
selection(includes document U) = { U }
```

Selection is one level. A selected Module contributes its owned documents, never the documents its
own relations select. Parentage, dependency and inclusion of the target, term usage, participation,
Markdown links, directory neighbourhood and implementation bindings add nothing further. Because
expansion is not recursive, cycles among Modules are harmless, and every member of a read set is
explained by the one declaration that selected it.

A scenario query resolves the scenario's owner and selects that owner's whole context. It never
trims to the scenario, and never selects the consumer that happened to read it.

Every selected document contributes **both** members whole. No excerpt, summary, rendered view or
diagram export substitutes for a complete document.

## Reconciliation

```text
Requires(M) = ⋃ { r.context_requires : r declared in the metadata or reading
                                        of a document M owns, including its entry }

CONFORMANCE:  ∀ q ∈ Requires(M) :  satisfied(q, Spec(M))
```

`imports`, `narrows`, `supersedes`, `relates` and `participates` each require the document that
defines their target. A Module that declares one without having that document in its context fails
`CHK.context.reconciled`. The repair is an explicit grant: a `uses` or `contains` that selects the
document, or an `includes` that states a reason.

The check is exact, because a node has exactly one defining document. A `uses` or `contains` that
narrows its grant with `relies_on` selects the documents defining the listed promises, so the
narrowing is exact as well. What no check establishes is that the list names every promise the
Module actually relies on; `CHK.relies-on.linked` catches every one the explanation links to.

## Implementation context

```text
ImplementationContext(M) = ⋃ { entries of M's realizations }
ImplementationContext(scenario S) = ImplementationContext(owner(S))
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

A resolved context is identified by its selected sources and the declarations that selected them,
so a harness can tell whether anything inside a boundary changed since a check.
Every source record carries document identity, owner, path, member role (`reading` or `metadata`),
an exact-byte SHA-256 digest, and every relation that selected it. External entries carry one tree
digest each.

The identity changes, even when the set of paths is unchanged, on:

- any byte change in either member of a selected document, including whitespace;
- a change to the declarations that selected the context, including removing a redundant inclusion;
- an ownership transfer;
- a change to pinned external material.

What a tool does with evidence bound to a previous identity is the tool's policy.

## Visibility

The resolved context is the exact visibility scope of a bounded reader: every selected source is
available whole and no unselected source is visible. How a tool makes it available is not part of
the Protocol. A tool MAY also supply task material such as changes since a baseline; such material
adds no source and replaces none. A reader that opened only some granted files still received the
complete context: missing meaning is judged against the full granted scope.

## Gaps

A missing definition is a semantic gap even after structural resolution succeeds. Record the needed
promise, its owner when known, the selected Module, the context identity and the blocked step. Do
not follow a selected Module's own relations or a prose link to repair it. An additional explicit
selection is a new context, not a retrospective claim that the previous one was complete.
