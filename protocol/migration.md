# Migration to Protocol 11, 12 and 13

Version 11 replaces Protocol 10's prose model with a declared one. Version-10 registries, metadata
and reading structures are invalid and MUST be migrated explicitly. No tool may silently
reinterpret them.

## What changed and why

| Protocol 10 | Protocol 11 | Reason |
| --- | --- | --- |
| Model stated across `principles`, `module`, `spec-management`, `spec-and-context` and `format` | One model in [model](model.md), [relations](relations.md), [context](context.md) and [`model.yaml`](model.yaml) | Relations lived in four different carriers and no single place showed them together |
| One `entity` record with a free-text `kind` | `concept` and `realization` | One record did three unrelated jobs, so its rules were conditionals over optional fields |
| Provider entity with `target_id` | removed | Collaborations carry their own `meaning`, and checked diagrams name Modules directly |
| Terminology rows typed by hand, imports as links, optional restatement | Concepts with identity and owner; the definition written once as the owner's table row; imports as link-only rows that declare `imports` | A term had no identity or owner, a link granted no context, and restatements drifted unchecked |
| `references` selected all context; `uses` and `parent` granted none | `uses` and `contains` grant the target's Specs, optionally narrowed by `relies_on` to the promises actually relied upon; `includes` covers the rest with a `reason` | A dependency could be declared without its provider ever being in context |
| External references as a separate kind of reference with no reason | `includes` of kind `external`, pinned by version control | One relation for everything a Module reads but does not own or depend on |
| Context obligations of term imports and contract participation stated as prose | `context_requires` plus `CHK.context.reconciled`, exact to the defining document | Nothing checked that the defining document was in context |
| Free relationships between entities existed only in prose and unchecked diagrams | `relates` with a verb, and checked flowcharts | A diagram could assert a collaboration nothing declared |
| Module relations declared in the registry; `dependencies` and `bindings` metadata arrays | a `module` block in the entry's metadata, mirrored and checked in the registry | A Module's declarations lie in its own write set, and a worker sees its relations without a global file |
| File listings implied what code might change; nothing defined what Specs a task might change | [Boundaries](boundaries.md): read sets, write sets (`SpecScope`, `ImplementationScope`), impact and composition rules | A harness needs exact read and write boundaries per task, derived from declarations |
| Metadata `schema_version` 2 | `schema_version` 3 | Declaration arrays restructured |

## Migration steps

1. **Declare each Module in its entry.** Add a `module` block to the entry's metadata with its
   `title` and `owns`. `parent` becomes the parent's `contains` entry with a `meaning`. `uses`
   gains a `meaning`, taken from the former dependency record, and optionally `relies_on`.
   Specification `references` already covered by a `uses` or `contains` are dropped; the rest
   become `includes` with a `reason`. External references become `includes` of kind `external`.
   Former contract `bindings` become `participates` with a `meaning`. Then regenerate the registry
   as the index and mirror of these blocks.
2. **Upgrade metadata to schema 3.** Split each `entities` array into `concept` and `realization`
   records in `defines`. Drop every provider entity and the `dependencies` and `bindings`
   arrays.
3. **Declare terms.** Each row of a Terminology table becomes a defining row, with a concept record
   in metadata, or a link-only import row. Delete restated definitions from import rows. Move a
   word shared by several Modules to their nearest common ancestor.
4. **Declare structure.** For each edge of an existing relationship diagram, declare the
   corresponding `relates`, `uses` or `contains`, or mark the diagram `illustrative`.
5. **Reconcile context.** Run `CHK.context.reconciled`; for each failure, select the defining
   document through `uses`, `contains` or `includes`, or remove the relation if it was not real.
6. **Resolve collisions.** Run `CHK.contrasts.required` and declare a `contrasts` with a reason for
   each reported pair.
7. **Bind every source file.** Run `CHK.binds.unbound`; a file no Module binds is outside every
   task's write boundary until a realization lists it.

Every migrated document changes bytes, so every context identity changes and evidence bound to the
old identities no longer applies.

## Costs

- **Every existing specification is invalid until migrated**, from the moment the Protocol binding
  changes.
- **Writing Specs changes shape.** Import rows lose their restated definitions, and an unmarked
  flowchart must match declared relations.
- **Contexts may grow.** A `uses` or `contains` without `relies_on` selects the whole target.
- **Name collisions must be acknowledged.** `CHK.contrasts.required` reports unrelated same-named
  concepts too; each needs a one-line `contrasts`.

## What did not change

Module ownership exclusivity. The paired document. One-level, non-recursive context selection.
Both members of a document travelling together. Anchors addressable but not selectable. The
separation of context from change authority. Evidence originating from what runs. Honest gaps over
inferred promises.

## Version 11.1

Version 11.1 changes one boundary rule and no document format. Under 11.0, a task writing a file
bound by several Modules received read access to every binding Module's documents in addition to
its own context. Under 11.1 such a task MUST instead be bound to every binding Module, so its reads
stay within the `SpecContext` of the Modules it is bound to. Specifications need no change; a
harness that granted the extra read replaces it with the wider task binding.

## Version 12

Version 12 makes task boundaries normative and changes no document format. Under 11, the
Protocol defined the boundary sets and left the level each task receives to the harness, with an
illustrative table. Under 12, the Protocol defines six task types (`understand`, `specify`,
`implement`, `test`, `review-spec`, `review-code`), each assigning every boundary set one access
level. The rule for tasks bound to several Modules and for paths in several sets is now stated.
Specifications need no change. A harness that used its own task kinds maps each onto a task type,
and MUST NOT grant a level the type does not assign.

## Version 13

Version 13 changes how reading draws diagrams and relaxes two layout rules. Mermaid is no longer
part of reading: a checked diagram is a `d2` block in the semantic subset of D2, in which nesting
asserts composition, ownership and file binding, an unlabelled edge between two Modules asserts a
`uses`, and a labelled edge asserts a `relates`. The look of a diagram is the publisher's. A picture
that is not checked is a `d2 illustrative` block and may use the whole D2 language. Separately, the
five sections of an entry may appear in any order, and an anchor may open a paragraph or a list
item, in which case it explains exactly that block.

To migrate, rewrite every Mermaid block. For a checked flowchart, draw each `contains` edge as
nesting, keep each `uses` edge as an unlabelled `->` between the two Modules, and keep each `relates`
edge as `->` with its verb as label; drop styling, `accTitle` and `accDescr`. Rewrite an illustrative
Mermaid block as `d2 illustrative`. Nothing else in a specification needs to change.

## Version 13.1

Version 13.1 adds a seventh task type and changes no document format. `code-to-spec` reads the bound
Modules' code and writes their own documents, so that a project whose code came before its
specification can describe what exists. It records behaviour as it is and reports every doubtful
intent as an open question instead of writing it as a promise. Specifications need no change; a
harness that does not offer the new task type loses nothing it had.

## Version 13.2

Version 13.2 adds the read set `ProjectImplementation`, every file any Module binds and all external
material any Module includes, and assigns it at `read` to the task types that read code:
`implement`, `test`, `review-code` and `code-to-spec`. A task that changes one Module's code can now
read and run the code it uses and the code that uses it, as running a package needs, while what it
may change stays within its bound Modules' scopes. The impact of writing a file now also concerns
every Module that uses the file's binders, directly or through further `uses`, since their code
runs against it. Specifications need no change.

## Version 13.3

Version 13.3 adds installed files, the files an installer lists as its own in the installation
record `.concorde/install.json`, to what no Module may write. They may still be bound, but only by
their exact paths (`CHK.binds.installed`), and a grant gives them at most read access. A
specification that binds a directory holding installed files, such as `.claude/` or `.pi/`, lists
its own files there exactly instead.
