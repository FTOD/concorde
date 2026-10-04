# Writing guidance

<a id="module-specifications"></a>

This is the content part of [Spec writing guidelines](writing.md). Its companion,
[Required format](format.md), defines the machine-checkable structure and syntax. This chapter
explains what the **reading content** must communicate. Applying it requires reader and editor
judgment. Its semantic requirements remain in force even when structural checks pass.

[Node types](model.md) and [Relations](relations.md) define what a specification declares.
No declaration alone establishes understanding.

This chapter serves understanding above all: it is what makes a structurally valid specification
worth reading.

A Module specifies one responsibility for consumers and implementers. It need not correspond to any
of these:

- A package.
- A directory.
- A service.
- A process.

These establish its boundary:

- Its purpose.
- Its behaviour.
- Its concepts.
- Its collaborations.

Realization bindings locate its code. They establish nothing about scope.

## Choosing Module boundaries

Draw Modules around responsibilities and axes of change:

- A capability.
- A use case.
- A boundary with one collaborator.

Things that change together SHOULD belong to one Module. A Module SHOULD NOT collect things only
because they are the same kind of artifact, such as:

- All scripts.
- All prompts.
- All configuration.

This choice serves both purposes at once. A reader understands a responsibility, not a file type.
A task's boundary is built from Modules. Therefore, a Module that matches how the project actually
changes yields boundaries that fit real tasks. A typical change needs one Module's write sets, not
slices of five.

A Module MAY be purely compositional, explaining how its children together fulfil a responsibility.
A Module MAY bind files of its own.

## The intended reader

Assume a reader with general software knowledge who does **not** know any of these:

- This project's implementation.
- This project's internal type names.
- This project's execution library.
- This project's history.

From the reading content alone, that reader must be able to explain:

- The problem the Module solves.
- When to use it.
- A normal interaction and its result.
- The important stopping conditions.
- Why the design supports the guarantees.

If reaching that state requires any of the following, the specification is incomplete regardless
of how many checks pass:

- Reading source code.
- Reading an unselected document.
- Reading a maintainer.

This reader is the measure of the Protocol's first purpose: a human understands the project from
its specification without reading its code.

## Document roles

One Module specification has two roles of document. Both are reading content. Both are owned
directly by the Module.

- **Module documents** (`role: module`) — the `module.md` entry and explanatory topics. They explain:
  - The responsibility.
  - Correct use.
  - Design.
  - Collaborations.

  Module documents MUST NOT become link indexes or independently maintained summaries with weaker
  promises.
- **Implementation documents** (`role: implementation`) specify:
  - The precise requirements.
  - The scenarios.
  - The canonical contracts.

  They are specifications, not any of these:
  - Source code.
  - Plans.
  - Descriptions of incidental implementation.

Role separation is about meaning, not heading syntax. Even when written as ordinary prose, the
following belong to `implementation` reading:

- Exact private APIs.
- Wire fields.
- Byte algorithms.
- Persistence layouts.
- Internal limits.
- Executable topology.

The following belong to `module` reading:

- Architecture.
- Design reasons.
- Actual public entry points.
- Any limit or hazard a consumer needs for correct use.

A topic is an explanation, never a second owner or a nested requirements container.

A Module's design is its entry. No part of it moves to a topic. Thus, a reader never has to leave
the entry to learn what the Module is and why it is built the way it is.
The concepts a Module owns SHOULD be explained in its entry too, at the anchors their glossary
entries name, not in a separate topic collecting them.

A topic explains something else, such as what a result means for its reader or how to proceed in
one situation. When a topic needs a design reason, it links to the entry.

## The entry

The entry is where a reader meets the Module. The whole entry is its design:

- What the Module is for.
- The ideas it rests on.
- How its parts and the Modules around it work together.
- Why it is built that way.

The Protocol imposes no section structure on it. No section is required. These are chosen for its
reader:

- Its headings.
- Their titles.
- Their order.

This reading order serves a developer who wants to understand the Module quickly.
A writer SHOULD follow this reading order: the picture first, and the details once the picture is
clear.

1. **Purpose.** What the Module is for, who relies on it and where its promises stop, including
   relevant non-goals, in short plain prose. A directory or package name establishes no responsibility.
2. **Core concepts.** The ideas a reader needs before the rest makes sense. These are the Module's
   own terms, each explained at the anchor its glossary entry names, and the terms of other Modules
   it builds on, linked.
3. **Overview.** Diagrams of the Module's main structure, functions and flows.

   Each diagram has short prose saying what it shows:
   - How the parts are arranged.
   - What the Module does with its input.
   - How a typical piece of work progresses.

   See [Diagrams](#diagrams).
4. **Details.** Everything else the reader needs, in the order that suits the Module:
   - Its parts and how each carries the function.
   - Its collaborations with its children and providers.
   - Its actual entry points.
   - Its errors and limits.
   - The reasons for its significant choices.

Keep operational detail with the Module that owns it. A parent or the root shows a process its
children carry out at the level of its own concepts. The parent or root links to the child whose
Spec walks through the commands. The parent or root does not repeat that walk-through. How a Module
fits with the rest is part of its explanation. Thus, a separate list of relationships that only
repeats it adds nothing.

Whatever its structure, the entry satisfies [the intended reader](#the-intended-reader). The
following explains what its content must communicate.

### How the Module is used

Explain these:

- The audience.
- The use conditions and prerequisites.
- The actual entry points.

Where the Module has entry points, follow a representative input through its result and effects on
a coherent normal path before turning to:

- Errors.
- Repeat invocation.
- Cancellation.
- Compatibility.

A reader MUST NOT have to assemble instructions from formal statements. Wherever abstraction would
otherwise hide a decision the user has to make, include a concrete illustration.
An unsupported behaviour is identified as unsupported, never invented to fill a template.
A logical responsibility may participate in a collaboration without having any callable entry point.
A logical responsibility MUST NOT invent one.

The entry's prose is canonical explanation, not a second summary with weaker promises. Link to
precise definitions rather than restating them.

### Why it is built this way

The design has an inside and an outside. Inside, the entry explains how the Module is built:

- Its children.
- The realizations that carry its function and the files they bind.
- How these work together.

Outside, the entry explains how the Module works with the Modules around it:

- The providers it relies on, including which of its parts meets which of theirs.
- Where a reader needs them, the Modules that rely on it, including which of its parts meets which
  of theirs.

Explain why these fulfil the guarantees:

- The decomposition.
- The state.
- The control and data flow.
- The collaboration.
- The failure containment.

Connect each significant choice to a problem it prevents. A list of class or function names in call
order is not an explanation. Intended design is not evidence that code conforms.

For every child and every provider, state:

- Its responsibility.
- When the collaboration applies.
- The canonical promises relied upon.
- This Module's own duties and failure reactions.

These explanations are what the `contains` and `uses` `meaning` anchors point to. A declared
relation with a link and no explanation does not satisfy this.

Record significant choices and required internal constraints. Distinguish them from incidental
current implementation and unresolved questions. Prefer linking to a guarantee over restating it as
a new obligation.

Identity and bindings stay in metadata. Provided the prose explains all of them, several nodes may
share one coherent explanation with distinct anchors.

### Diagrams

Use diagrams wherever they make any of these clearer:

- Relationships.
- Order.
- Branching.
- State.
- Data.

Choose the view by the reader's question, not by a quota or a fixed set of pictures. Each diagram
answers one clear question. Each diagram stands next to the prose that explains it.
Overview diagrams stand near the top of the entry. The others stand beside the details they clarify.

| Reader's question | Useful view |
| --- | --- |
| How does a process progress, including branches, joins, retries, stopping points and hand-offs between participants? | Workflow diagram: steps and directed edges, with a lane per participant or stage groups when helpful |
| Does the exact interleaving of messages between participants matter, as in a request and reply protocol? | Sequence diagram, only then |
| What states can a record or task occupy, and what causes each transition? | State diagram |
| How do the children and realizations carry the Module's function together? | Component view of the inside, with the bindings and edges that explain it |
| How does the Module interact with its users, providers and consumers? | Context view of the outside, or of the parts that meet across Modules |
| Where do processes or services run, and which boundaries do they cross? | Deployment view |
| How do records relate, or how is data transformed and passed between parts? | Data-model or data-flow view |

A process is a workflow diagram by default, including an interaction among several Modules or
agents. Follow these steps:

- Start with step nodes and directed edges.
- Make the main path easy to follow.
- Where these matter, separate branches, recovery and evidence.

When who does a step matters, give each participant a lane so that an edge between lanes shows a
hand-off. A sequence diagram is heavier to read. The reader must follow lifelines and messages to
find the steps. Use one only when the interleaving of messages is itself the point.

All these views use D2. A checked `d2` diagram uses only the semantic subset. It asserts only
declared static relations:

- Nesting for containment, ownership and bindings.
- Unlabelled edges between Modules for `uses`.
- Labelled edges for `relates` with their declared verbs.

Mark every other view `d2 illustrative`. This includes the following views that show behaviour or
runtime facts beyond those relations:

- Workflow views.
- Sequence views.
- State views.
- Deployment views.

Only when a component, context or data-model view fits those same rules is it checked.
See [Views](views.md).

Keep names and meanings consistent with the surrounding Spec. A diagram complements explanatory
prose. Where a diagram cannot carry them, explain the following:

- The conditions.
- The invariants.
- The effects.
- The failure reactions.

Do not invent a promise or a relation to fill a picture. An illustrative view grants no authority.
It never replaces the declaration and prose of a load-bearing collaboration.

Draw the relationships that matter to the question. An inventory of disconnected boxes or files
usually adds nothing to a list. Leave realizations that only keep the repository running to prose.
Examples include:

- Project configuration.
- Development tooling.
- Test suites.

A small Module may need no diagram. A Module with little static structure may still benefit from a
workflow or state view. Use as many diagrams as help understanding, with none drawn only to have one.

## Terms

The words of the whole project live in one glossary. Thus, a word means one thing everywhere.
A reader looks it up in one place. Where a document first uses a term, link it with a
[term link](format.md#term-links) to its glossary entry. Wherever a reader arriving mid-document
would need it, link it again. A reader receives the definition of every term its documents link,
and only those. Thus, an unlinked term is a word the reader may not know.

Deciding which concepts exist is substantive. Declare a concept for a domain word, a record, a
boundary actor or an external standard a reader must understand.

Do not declare a concept for any of these:

- A file.
- An identity.
- An internal class.

Before adding one, look for an existing term with that meaning and link it instead.
Decide who owns each word by who is entitled to change its meaning. See
[Node types](model.md#concept). Write the definition as one sentence a newcomer understands without
the owner's documents. Write the extended explanation in the owner's document at the anchor the
entry names. When a word could be confused with another term or with a Module's name, declare
`contrasts`. When a word conflicts with common usage outside the project, state `external_conflict`.

Titles are unique in the project. Two meanings of one word are two terms with distinct titles, such
as `Session round` and `Headless round`, not one title defined twice.

## Precise obligations

Define these only in `implementation` documents owned by the Module. Group headings may organize
definitions but never own them. Module documents explain the important guarantees.
Module documents link to the canonical definitions. A reader should not need to read every
acceptance case to understand the Module.

A **requirement** is one decidable Module-wide `SHALL` statement with a stable identity. A
**scenario** is one testable situation in `GIVEN`/`WHEN`/`THEN` steps. A situation-specific
guarantee belongs in that scenario's steps or explanation, not in a second requirement. Define each
obligation once. Link to it. Editorial organization MUST NOT do any of the following to it:

- Weaken it.
- Duplicate it.
- Contradict it.

An **interface** is specified by a canonical contract plus readable behaviour and scenarios, not by
a schema alone. In selected readable context, these MUST be explained, never inferred from shape:

- Inputs.
- Outputs.
- Effects.
- Failures.
- Compatibility.
- Repeat behaviour.

## Composition, dependency and inclusion

- `contains` states structural accountability. A parent explains how its children fulfil the
  responsibility it holds. The parent receives their Specs to do so. A Module has at most one
  parent. Composition is acyclic.
- `uses` states reliance on a provider's promises. It gives the consumer the provider's Specs.
  It implies none of these:
  - Ownership.
  - Deployment.
  - Directory nesting.
  - Shared source.

  Dependencies may cross hierarchy levels. Two Modules may use each other.
- `includes` states what else this Module reads, with a reason. It implies no ownership and no
  dependency.

When a Module relies on a few promises of a large provider, list them in the relation's
`relies_on` and link them from the explanation of the collaboration.

The reader then receives the provider's entry and exactly the documents defining those promises.

## Realization

A `realization` binds exact files or directory prefixes. See [Node types](model.md). Tests are
ordinary implementation files. A test declares the scenarios it verifies **in the test**.
Reading content MUST NOT list verifying tests. Reading content MUST NOT prescribe coverage
declarations. Missing coverage does not cancel a promise. A declared test is not proof of
fulfilment.

## Completeness

The selected context makes every owned and selected document available with both members intact.
Its readable subset must supply the meaning the task needs.

None of the following is proof of sufficient meaning:

- A schema.
- A heading.
- A rendered table.
- A checked diagram.
- A correctly registered file set.

Honest drafts name their unknowns. Until an explicit change to the specification repairs it,
missing necessary meaning remains a gap. None of the following can silently supply a missing
contract:

- Source code.
- Another Module's own selections.
- Publisher summaries.

The one explicit route from code to specification is a `code-to-spec` task
(see [Boundaries](boundaries.md#task-types)). Its changes are ordinary specification changes.
Its changes leave every doubtful intent a reported gap.
