# Spec and Context

A Module is the unit of complete Spec context selection. A scenario query first resolves its sole
owner and selects that Module. Reading is the Protocol-defined human-readable subset of content,
not an additional query kind, a summary substitute or an execution grant.

## Exact source selection

Let `D(M)` be the document units owned by M, `R(M)` its explicit references, and `members(U)` the
reading and metadata files of unit U. A Module reference includes its owned units; a document
reference includes exactly the identified unit. External material is selected separately.

```text
Units(M) = D(M) union (union of include(r) for r in R(M) when r is a context reference)
Context(M) = union of members(U) for U in Units(M)
ReadingContext(M) = the reading member of each U in Units(M)
Context(scenario S) = Context(owner(defining_unit(S)))
```

Only `R(M)` expands. Never recursively resolve a provider's context. Neither links, parentage,
uses, directory neighbors, entity target IDs nor implementation bindings add sources. Each selected
unit contributes both exact members, even when a publisher puts its reading on an auxiliary page.
No excerpt, summary, diagram export or reading-only projection replaces a complete unit.
`D(M)` includes both module-role explanations and implementation-role precise specifications.
A document's role never filters this union, including during discovery, planning or Spec review.
Implementation Specs are Spec context, not the separately authorized implementation source context.

```text
resolve(registry, query):
    find the unique selected Module or scenario owner
    validate registration, ownership, paths, kinds and source availability
    include each owned unit, reason = owned(Module ID)
    include each directly referenced unit, retaining its typed reference reason
    expand each included unit to its exact reading and metadata source members
    deduplicate sources and retain all sorted inclusion reasons
    return source records sorted by canonical project-relative path
```

Every record contains document ID, sole owner, path, source role (`reading` or `metadata`), exact-byte
SHA-256 digest and inclusion reasons. The selecting registration, including owned collection and
explicit references, is bound to context identity. Both members have the same owner, document ID
and inclusion provenance. Changing only whitespace, metadata, reference declarations or provenance
invalidates dependent byte-bound evidence even if the set of paths is unchanged.

Unknown IDs, wrong kinds, duplicate identities, unsafe or aliased paths, ambiguous ownership and
missing members fail without partial successful resolution. Identity lookup may inspect registered
metadata without reading unselected human bodies. Requirement, entity, contract, document and
heading anchors are addressable artifacts, not separate task-context query kinds.

## Visibility and delivery

The resolved context is the exact Spec visibility scope of a bounded reader. The tool must make
every selected source available whole and no unselected source visible. It may grant paths in place,
copy byte-identical members into a capsule, provide their bodies, or combine these mechanisms.
Delivery mechanism does not change membership, ownership, source identity or authority.

A tool may also provide task material derived from in-scope files, such as their changes since a
baseline. Such material adds no file and cannot replace complete sources. An agent that reads only
some granted files still received the complete context; missing meaning is judged against the full
scope, not against what that reader happened to open.

## Example: overlapping references

Checkout owns its entry and scenario units. It references Inventory's entire collection and also
Inventory's interface unit. Inventory owns its entry and interface and references Tax. Checkout
therefore receives four units, eight source members, with two reference reasons on both interface
members. Tax is absent. Querying an Inventory scenario selects Inventory's own context, including
Tax. Removing Checkout's redundant interface reference changes provenance and invalidates its
context identity even though its source paths are unchanged.

## Implementation context

Implementation context is derived only from local entity file bindings. Exact entries and files
below directory prefixes are resolved under an explicit deterministic exclusion rule. Metadata
records pending intent without pretending missing file contents exist.

```text
ImplementationContext(M) = union of bound files of locally owned entities
ImplementationContext(scenario S) = ImplementationContext(owner(S))
```

Neither reading nor metadata members belong to implementation context. A file shared with another
Module adds that Module to reverse-use metadata, not its Spec or implementation to the selected
reader's context. A Module with no bindings has an empty implementation context; this does not
prove it has no realization.

Implementation names and pending status are visible through admitted metadata. Contents are a
separate phase-specific grant. A tool may grant names for planning, read-only contents for review,
or writable contents for implementation, but never add unlisted files implicitly. Context inclusion
alone grants no write, command, credential or network authority. Test-to-scenario coverage is derived
from tests in implementation context, not from a second Spec-authored test list.

## External reference material

External references declare existing project-relative vendored library, service or tool material,
pinned at a known revision. They are neither specification promises nor implementation files and
cannot overlap a document unit or the selecting Module's implementation listing. They are never
pending. Only the selected Module's external references are considered.

```text
References(M) = union of readable files selected by M's external entries
References(scenario S) = References(owner(S))
```

A tool may exclude media and archives by a documented deterministic rule and record one tree digest
per external entry. The entries are metadata; their contents are separately authorized read-only.
An undeclared network fetch or installed dependency's sources must not substitute for declared
material. Missing necessary external knowledge is a gap, not permission to widen the grant.

## Changes and gaps

Source members stay paired for ownership, context and review. An owner-only authoring proposal may
change either or both members, but must be checked as one complete overlay before application.
Referenced units remain read-only. A metadata-only ownership or binding edit cannot evade affected
context review, stale-input checks or the prohibition on code writers changing Specs.

A missing definition is a semantic gap, even after successful structural resolution. Record the
needed promise, its owner when known, selected Module, context identity and blocked step. Do not
follow an included Module's references or a prose link to repair it. An additional explicit Module
selection is a new bounded context, not a retrospective claim that the old one was complete.
