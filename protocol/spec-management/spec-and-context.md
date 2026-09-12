# Spec and Context

Module is the core unit of Spec context resolution. Ownership determines definitions; registered
Module references determine additional reading. Implementation context is resolved separately.
Neither context inclusion nor inventory metadata grants write, command or network authority.

## Queryable entities

| Entity kind | Resolution |
| --- | --- |
| Module | Its own complete context. |
| Scenario | Find the sole owner of its defining document, then resolve that Module's context. |

The requested scenario remains the focus, but never trims files. Ownership comes from registration
and document metadata, not prefixes, paths or the Module in whose context a definition was seen.
Requirements, entities, documents and headings are addressable artifacts, not additional Spec query
kinds. A document reference is an inclusion instruction, not a document-scoped task.

## Deterministic single-level resolution

Let `D(M)` be the documents owned by M and `R(M)` its registered references. Let `include(r)` be
`D(r.id)` for a Module reference, or the singleton registered document for a document reference.

```text
Context(M) = D(M) union (union of include(r) for r in R(M))
Context(scenario S) = Context(owner(defining_document(S)))
```

Only `R(M)` is consulted. Never resolve `Context(r.id)` during expansion. Links, directory
neighbors, parentage, uses, file bindings and included document metadata do not expand context. All
included files are complete, even with `main_visible: false`; no excerpt or summary replaces them.
Cycles in references terminate immediately because the algorithm is not recursive.

```text
resolve(inventory, query_id):
    M = registered Module or unique owner of registered scenario(query_id)
    validate ownership, paths, reference kinds and availability
    include every document in D(M), reason = owned(M.id)
    for r in R(M):
        include every document in include(r), reason = reference(r.kind, r.id)
    deduplicate by canonical physical document identity and path
    return complete records sorted by canonical project-relative POSIX path
```

Aliases, symlinks, duplicate paths/IDs, missing files, ambiguous owners, wrong kinds and unknown
identities fail resolution without a partial successful context. Distinct routes to the same file
retain every reason, sorted by kind and ID, but supply its bytes once. A reading entry and authored
document order aid navigation and do not change this reproducible file order.

Every resolution MUST record query ID/kind, selected Module ID, scenario owner when applicable, the
selecting Module's ownership and reference declarations, and for each included file its stable
document ID, canonical path, sole owner, byte digest and inclusion reasons. A byte digest is SHA-256
of the exact source bytes, before decoding or rendering. The resolver MUST bind these declarations
and source identities to the snapshot so unchanged file sets with changed references also invalidate
reuse. Inventory metadata can resolve identities without admitting unrelated source bodies.

## Example: overlapping references without recursion

Checkout owns `checkout/module.md` and `checkout/scenarios.md`. It references Module Inventory and
document `document.inventory.interface`, which Inventory owns alongside `inventory/module.md`.
Inventory references Tax. Checkout's context has four full files: its two own files and Inventory's
two files. The interface has two reference reasons and one body. No Tax file is included. Querying a
scenario defined in the Inventory interface selects Inventory, whose own context includes Tax; it
does not select Checkout. Removing Checkout's redundant document reference preserves the file set
but changes provenance and the context identity.

## Implementation context


**Implementation context** is the Protocol term for the implementation knowledge that belongs to a
Module: the files its entities bind, each identified as existing or pending. Let `F(E)` be the
files bound by entity `E`, that is its exact entries together with every regular file below its
directory prefixes that the tool's explicit exclusion rule does not remove, and `entities(M)` the
entities defined in documents owned by Module `M`, excluding referenced definitions. Then:

```text
ImplementationContext(M) = union over E in entities(M) of F(E)
ImplementationContext(scenario S) = ImplementationContext(owner(S))
```

Implementation context is determined from the entity declarations alone, without model judgment or
interpretation of prose links; expanding a directory prefix is a deterministic listing of the files
below it, not a judgment about them. The scenario verification index is likewise derived from the
tests in that context and adds no file to it. It is disjoint from `Context(M)`: neither owned nor
referenced Spec documents are part of it, and a file shared with another Module never adds that
Module's contract. Those other users remain metadata identified by the reverse index. Declared files
pending creation are identified as pending rather than represented as available contents. A Module
whose entities bind no files has an empty implementation context; that is a statement about the
declarations, not evidence that no realization exists.

The file names in a Module's implementation context are visible wherever the Module's entity
declarations are visible, because those declarations are part of the Spec context. File contents are
a separate grant. A tool MAY authorize a phase-specific subset of the implementation context, such
as file names without contents for planning or read-only contents for review, but MUST NOT add files
outside it. The union of `Context(M)` and `ImplementationContext(M)` is the maximal file set a
Module-bound task may receive without a new explicit selection. The development environment defines
which phases receive which subset and the applicable permissions; a Spec query never includes file
contents implicitly.

## Completeness and gaps

A missing necessary definition is a semantic gap even when the declared file set resolved fully.
Name the required definition, its owner when known, selected Module, snapshot and blocked step. Do
not silently follow an included link or a referenced Module's references to repair the gap. An
explicit additional Module selection is a new bounded context, never a retrospective claim that the
old one was complete. Included definitions retain their owner; they confer no authority to edit
provider Specs or read provider implementation. A consumer's main diagram covers only its own
entities, including its local collaborator entities, not every included provider entity.
