# Migration to Protocol 11, 12, 13, 14, 15 and 16

Version 11 replaces Protocol 10's prose model with a declared one. The following Version-10 items
are invalid and MUST be migrated explicitly:

- Registries.
- Metadata.
- Reading structures.

No tool may silently reinterpret them.

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
   Specification `references` already covered by a `uses` or `contains` are dropped. The rest
   become `includes` with a `reason`. External references become `includes` of kind `external`.
   Former contract `bindings` become `participates` with a `meaning`. Then regenerate the registry
   as the index and mirror of these blocks.
2. **Upgrade metadata to schema 3.** Split each `entities` array into `concept` and `realization`
   records in `defines`. Drop every provider entity. Drop the `dependencies` and `bindings`
   arrays.
3. **Declare terms.** Each row of a Terminology table becomes a defining row, with a concept record
   in metadata, or a link-only import row. Delete restated definitions from import rows. Move a
   word shared by several Modules to their nearest common ancestor.
4. **Declare structure.** For each edge of an existing relationship diagram, declare the
   corresponding `relates`, `uses` or `contains`, or mark the diagram `illustrative`.
5. **Reconcile context.** Run `CHK.context.reconciled`. For each failure, select the defining
   document through `uses`, `contains` or `includes`, or, if the relation was not real, remove it.
6. **Resolve collisions.** Run `CHK.contrasts.required`. For each reported pair, declare a
   `contrasts` with a reason.
7. **Bind every source file.** Run `CHK.binds.unbound`. Until a realization lists it, a file no
   Module binds is outside every task's write boundary.

Every migrated document changes bytes. Therefore, every context identity changes. Evidence bound
to the old identities no longer applies.

## Costs

- From the moment the Protocol binding changes, **every existing specification is invalid until
  migrated**.
- **Writing Specs changes shape.** Import rows lose their restated definitions. An unmarked
  flowchart must match declared relations.
- **Contexts may grow.** A `uses` or `contains` without `relies_on` selects the whole target.
- **Name collisions must be acknowledged.** `CHK.contrasts.required` reports unrelated same-named
  concepts too. Each needs a one-line `contrasts`.

## What did not change

The following did not change:

- Module ownership exclusivity.
- The paired document.
- One-level, non-recursive context selection.
- Both members of a document travelling together.
- Anchors addressable but not selectable.
- The separation of context from change authority.
- Evidence originating from what runs.
- Honest gaps over inferred promises.

## Version 11.1

Version 11.1 changes one boundary rule. It changes no document format. Under 11.0, a task writing a
file bound by several Modules received read access to every binding Module's documents in addition
to its own context. Under 11.1, such a task MUST instead be bound to every binding Module.
Its reads therefore stay within the `SpecContext` of the Modules it is bound to. Specifications
need no change. A harness that granted the extra read replaces it with the wider task binding.

## Version 12

Version 12 makes task boundaries normative. It changes no document format. Under 11, the Protocol
defined the boundary sets. It left the level each task receives to the harness, with an
illustrative table.

Under 12, the Protocol defines six task types (`understand`, `specify`,
`implement`, `test`, `review-spec`, `review-code`). Each assigns every boundary set one access
level. The rule for tasks bound to several Modules and for paths in several sets is now stated.
Specifications need no change. A harness that used its own task kinds maps each onto a task type.
Such a harness MUST NOT grant a level the type does not assign.

## Version 13

Version 13 changes how reading draws diagrams. It relaxes two layout rules. Mermaid is no longer
part of reading. A checked diagram is a `d2` block in the semantic subset of D2. In that subset:

- Nesting asserts composition.
- Nesting asserts ownership.
- Nesting asserts file binding.
- An unlabelled edge between two Modules asserts a `uses`.
- A labelled edge asserts a `relates`.

The look of a diagram is the publisher's. A picture that is not checked is a `d2 illustrative`
block. Such a picture may use the whole D2 language. Separately, the five sections of an entry may
appear in any order. An anchor may open a paragraph or a list item. In that case, the anchor
explains exactly that block.

To migrate, rewrite every Mermaid block. For a checked flowchart:

- Draw each `contains` edge as nesting.
- Keep each `uses` edge as an unlabelled `->` between the two Modules.
- Keep each `relates` edge as `->` with its verb as label.
- Drop styling, `accTitle` and `accDescr`.

Rewrite an illustrative Mermaid block as `d2 illustrative`. Nothing else in a specification
needs to change.

## Version 13.1

Version 13.1 adds a seventh task type. It changes no document format. `code-to-spec` reads the bound
Modules' code. It writes their own documents. This lets a project whose code came before its
specification describe what exists. `code-to-spec` records behaviour as it is. It reports every
doubtful intent as an open question instead of writing it as a promise. Specifications need no
change. A harness that does not offer the new task type loses nothing it had.

## Version 13.2

Version 13.2 adds the read set `ProjectImplementation`. It holds every file any Module binds and
all external material any Module includes. Version 13.2 assigns it at `read` to the task types
that read code: `implement`, `test`, `review-code` and `code-to-spec`.

A task that changes one Module's code can now read and run the code it uses and the code that uses
it. Running a package needs this access.

What the task may change stays within its bound Modules' scopes. Since their code runs against
it, the impact of writing a file now also concerns every Module that uses the file's binders.
This includes use directly or through further `uses`. Specifications need no change.

## Version 13.3

Version 13.3 adds installed files to what no Module may write. Installed files are the files an
installer lists as its own in the installation record `.concorde/install.json`. They may still be
bound, but only by their exact paths (`CHK.binds.installed`). A grant gives them at most read
access. A specification that binds a directory holding installed files, such as `.claude/` or
`.pi/`, lists its own files there exactly instead.

## Version 14

Version 14 folds an entry's Relationships section into its Design. An entry has four sections:

- Purpose.
- Terminology.
- Usage.
- Design.

It has no level-2 section titled `Relationships` (`CHK.document.sections`). A separate
Relationships section repeated the design. Its one required picture was often drawn for its own
sake. Design now holds the whole architecture. The inside is how the Module is built from its
children and realizations. The outside is how it works with the Modules it uses and those that
use it.

Design may draw several diagrams, each answering one question. When there is nothing structural
to show, it draws none.

To migrate, move the Relationships section's prose and diagrams into Design, next to the design
reasons they belong to. Delete the heading. The `meaning` anchors of `contains` and `uses` keep
their identities. They move with their explanations. Replace a diagram that only lists children
without edges by one that shows the edges that matter, or by prose. The following do not change:

- Metadata.
- Relations.
- Checked diagram syntax.

## Version 15

Version 15 moves every term of a project into one glossary. Per-Module Terminology tables made each
reader list the shared words it used as link-only import rows. They also made each reader select
those words' defining documents with further inclusions. The rows carried no meaning of their
own. A word could be defined twice in two Modules without either noticing. Now:

- Every concept is an entry of the glossary the root Module declares (`glossary` in its `module`
  block). Each entry contains:
  - An identity.
  - A title.
  - An owner.
  - A one-sentence definition.
  - A reference to its explanation in a document of the owner.

  Titles are unique in the project.
- A document links a term where it uses it. The link is the `mentions` relation, replacing
  `imports`. It grants the definition rather than requiring the defining document.
- A reader's context holds the definitions of the terms its documents link and of the concepts
  its Module owns in the `term` channel. These definitions are closed over the terms they link.
- An entry has the following sections:
  - Purpose.
  - Usage.
  - Design.

  No document has a Terminology table.
- `narrows`, `supersedes`, `contrasts` and a concept's `relates` are declared in its glossary entry.
  Document metadata declares only realizations and their, or the Module's, `relates`.
- A task whose type writes `SpecScope` may change the glossary entries its bound Modules own.
  The harness compares the file before and after to hold the task to those entries.

To migrate:

1. Create the glossary. Declare it in the root Module's `module` block. Regenerate the registry.
2. Give every concept a project-wide identity `concept.<name>` and a title unique in the project.
   Rename a title defined by two Modules into two distinct terms.
3. Move each concept record into the glossary with:
   - Its owner.
   - Its Terminology row's sentence as `definition`.
   - Its `meaning` anchor, qualified by its document's path, as `explanation`.

   Move its `narrows`, `supersedes`, `contrasts` and `relates` from the document's `relations` into
   the entry.
4. Delete every Terminology section and every `includes` that existed only to satisfy an import.
5. Perform these steps:
   - Point every link to a concept's anchor at the glossary (`<path to glossary>#concept.<name>`).
   - Rename identities in `relies_on` and `relates`.
   - Link each term where a document first uses it.

   `CHK.term.unlinked` lists the rest.

## Version 15.1

Version 15.1 frees an entry from a fixed section structure. The Protocol requires no level-2
section of an entry. `CHK.document.sections` and `CHK.document.prose` are removed. The ban on a
`Relationships` section is removed too. A required Purpose, Usage and Design made writers put an
entry-point walk-through first. They also made writers split what a Module is from why it is built
that way. This buried the ideas a reader needs first. Writing guidance now recommends a reading
order instead:

- Purpose.
- Core concepts.
- Overview diagrams of the main structure.
- Functions and flows.
- The details.

Writing guidance treats the whole entry as the Module's design. The Module's design still never
moves to a topic. A Module's own concepts are explained in its entry rather than in a separate
topic collecting them. When that helps, a process, including an interaction among several Modules
or agents, is drawn as a workflow diagram with a lane per participant. A sequence diagram is kept
for when the interleaving of messages is itself the point.

Every specification valid under 15.0 stays valid. Nothing needs to change. To follow the new
guidance:

- Reorder an entry so that its purpose and core concepts come first and its overview diagrams
  follow them.
- Move command-level walk-throughs to the Module that owns the commands.
- Fold a topic that only explains the Module's concepts into its entry.
- Redraw a sequence diagram whose point is the steps rather than the interleaving as a workflow.

## Version 16

Version 16 removes pending realization entries. Under 15:

- A realization could list in `pending` entries whose files did not exist yet.
- A Spec change could thus declare where code would go before any code was written.
- The file was created later.
- Once the file existed, the marker was cleared.

The marker was intent stored beside evidence. A grant had to tell its pending paths from the
bound ones. Only when some later task wrote it did the file appear. Now:

- A realization has no `pending` field. Every entry MUST exist. `CHK.binds.pending-subset` is
  removed. `CHK.binds.exists` applies to every entry.
- For a new file outside every bound directory, the following apply:
  - The file is created and bound together by the work that prepares the task that fills it.
  - The file is created with the least content its format needs to be valid.
  - The file is never created or bound by a Module-scoped task.

  A new file below a bound directory still needs no new entry.
- `ImplementationScope` and implementation context hold only bound paths. All of those paths
  exist.

To migrate, for every realization with a `pending` field, either create each listed file and keep
its entry, or delete the entry. Then delete the field.

Metadata that still carries `pending` is invalid.

## Version 16.1

Version 16.1 states how a Spec is evaluated. It adds a task type that judges the architecture
between Modules. The criteria a Spec was judged by lived only in the instructions of one tool's
reviewers. Two tools could thus judge the same Spec by different standards. Nothing judged the
division into Modules as a whole. Every reviewer saw one Module and the Specs its declarations
select. Now:

- [Evaluating a Spec](evaluation.md) is the third part of the Spec writing guidelines. It states:
  - The criteria of Module quality.
  - The criteria of architecture quality between Modules.
  - The criteria that determine when a problem is blocking or advisory.

  Evaluation is a judgment and not deterministic. It adds no check.
- The read set `ProjectSpecification` holds both members of every document any Module owns and the
  whole glossary. This read set is the same for every Module.
- The task type `review-architecture` reads:
  - `ProjectSpecification`.
  - The bound Modules' `SpecContext` and external context.
  - The names of `ProjectImplementation`.

  This task type writes nothing. Only this task type reads other Modules' Specs beyond what its
  bound Modules' declarations select. This task type never reads code contents.

Every specification valid under 16.0 stays valid. Nothing needs to change. A harness that does not
offer the new task type loses nothing it had.

## Version 16.2

Version 16.2 adds a sentence style to the Spec writing guidelines. Specs grew long sentences that
joined several facts with commas and semicolons. A reader had to hold many clauses at once. A
requirement could hide who acts. Now:

- [Sentence style](style.md) is the fourth part of the Spec writing guidelines. Its rules are
  inspired by the structural rules of ASD-STE100 Simplified Technical English. The requirement
  keywords keep their Protocol meanings.
- Three new checks with strictness warning measure the decidable rules:
  `CHK.style.sentence-length`, `CHK.style.semicolon` and `CHK.style.one-obligation`.
- [Evaluating a Spec](evaluation.md#readability) judges the other rules as part of readability.

Every specification valid under 16.1 stays valid. The new checks are warnings and block nothing.
To follow the style, rewrite each sentence that a style check reports. Then read the text again
for the rules that no check measures.

## Version 16.2.1

Version 16.2.1 rewrites the Protocol's own chapters and templates in [Sentence style](style.md).
The wording changes. No rule, check, field or task type changes.

Every specification valid under 16.2 stays valid. Nothing needs to change.
