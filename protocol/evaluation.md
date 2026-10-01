# Evaluating a Spec

This is the evaluation part of [Spec writing guidelines](writing.md). [Required format](format.md)
defines the structure a Spec must have and [Writing guidance](module.md) what its content must
communicate; this chapter states how a Spec is judged good. It serves understanding: a Spec that
passes every structural check can still leave its reader unable to rely on it, and only a judgment
of its content finds that.

## A judgment, not a check

Evaluation is a judgment of meaning, and it is **not deterministic**. Two careful evaluations of
the same Specs may notice different problems, weigh them differently and word them differently.
The criteria below make evaluations comparable in what they look for; they do not make them
decidable, and no criterion is a [structural check](checks.md) or can become one. A result of
evaluation is never structural conformance, and never implementation conformance either: it is
evidence about [semantic sufficiency](principles.md#conformance) only, bound to the exact Specs it
read. An evaluation that found no problem shows that it found none, not that none exists.

A problem is established by the text of the Specs that shows it: the passage, the declaration or
the absence the evaluation can point to. An impression that cannot be tied to the Specs is not a
problem.

Evaluation happens at two levels, each read from its own boundary:

| Level | What is judged | What is read |
| --- | --- | --- |
| [Module quality](#module-quality) | one Module's own documents, for the reader of that Module | the Module's `SpecContext` and external context, as a `review-spec` task receives them |
| [Architecture quality](#architecture-quality) | how the project is divided into Modules and how they rely on each other | every Module's Specs, `ProjectSpecification`, as a `review-architecture` task receives them |

Neither level reads code contents (see [Task types](boundaries.md#task-types)). A Spec is judged by
what it tells its reader; whether the code does what the Spec says is implementation conformance,
established by evidence. Code never repairs a Spec's missing meaning.

## Blocking and advisory problems

Every problem is **blocking** or **advisory**:

- **Blocking**: a reader of the Module, or a task bound to it, could not rely on the Spec as
  written. The Spec leaves them unable to act, or leads them to act wrongly: a requirement that
  joins two obligations, a scenario whose outcome cannot be observed, an entry that never shows
  how a normal interaction goes, two documents or two Modules that contradict each other, a term
  used in two meanings, a responsibility two Modules both claim or none owns, a dependency that is
  relied upon but not declared.
- **Advisory**: the Spec can be relied upon, but could serve its reader better: wording that could
  be clearer without changing what a reader would do, an order that makes the reader wait for the
  idea they need, a diagram that would make a relationship easier to follow, a boundary that could
  be drawn more cleanly without any task being misled today.

Whether a problem is blocking depends on its effect on a reader and a task, not on the size or
difficulty of the repair. A missing diagram alone is advisory; when the meaning a picture would
show is itself missing or contradictory, the missing meaning is the problem, and a picture alone
cannot supply it. The Protocol defines no further grading: what is done with a problem once found, who repairs it and
whether it must be decided by someone else, belongs to the tools and the project's own process.

## Module quality

Module quality is judged for the [intended reader](module.md#the-intended-reader): someone with
general software knowledge who does not know the project's code or history, and who must be able to
explain, from the Module's Specs alone, what it is for, when and how to use it, a normal
interaction and its result, the important stopping conditions, and why its design supports its
guarantees. Only the Module's own documents are judged; a problem seen in a provider's or an
included document concerns that other Module, and its own evaluation judges it. The criteria fall
into six dimensions.

### Readability

- The entry lets a reader understand the Module quickly, in the
  [reading order](module.md#the-entry) the guidance recommends: first what the Module is for, who
  relies on it and where its promises stop, in short plain prose; then the core concepts; then
  overview diagrams of its main structure, functions and flows; then the details. The Protocol
  requires no section, so the order is judged, not the headings.
- Where the Module has entry points, a reader can follow a coherent normal path from an input to
  its result before errors, repetition and cancellation, with a concrete illustration wherever an
  abstraction would hide a decision the reader has to make. A reader never has to assemble
  instructions from formal statements.
- Operational detail stays with the Module that owns it: a parent shows its children's process at
  the level of its own concepts and leaves their commands to them.
- Unknowns and unsupported behaviour are stated honestly, never invented to fill a structure.

### Obligations

- Each requirement is one decidable Module-wide obligation, with exactly one `SHALL` or
  `SHALL NOT`: not two obligations joined in one sentence, and not a guarantee that holds only in
  one situation, which belongs in a scenario.
- Each scenario is one testable situation whose `THEN` steps state observable outcomes.
- Each obligation is defined once. Module-role prose explains the important guarantees and links
  to them, and never weakens, duplicates or contradicts one.
- An interface is specified by behaviour: its inputs, outputs, effects, failures, compatibility and
  repeat behaviour are explained in readable text, not left to be inferred from a schema's shape.

### Design

- The entry explains why the decomposition, state, control and data flow, collaboration and
  failure containment fulfil the guarantees, connecting each significant choice to a problem it
  prevents. A list of names in call order is not an explanation.
- Every child and every provider has an explanation of its responsibility, when the collaboration
  applies, the promises relied upon, and the Module's own duties and failure reactions. A declared
  relation with a link and no explanation does not meet this.
- Significant choices are told apart from incidental current implementation and from open
  questions.

### Views

- A diagram answers one clear question, stands next to the prose it complements and uses the same
  terms. The kind of view suits the question: a process is a workflow by default, and a sequence
  diagram is used only when the interleaving of messages is the point.
- A checked diagram asserts only declared relations; any other view is marked illustrative and
  claims no authority beyond its prose. A load-bearing collaboration is never described only in an
  illustrative diagram.
- A place where a diagram would make relationships, order, branching, state or data clearer is a
  problem of readability; no count or kind of diagram is required.

### Terminology

- Every term the Module owns has one clear one-sentence definition and an explanation, is used with
  that meaning throughout, and says so where it could be confused with another term or with common
  usage.
- Every term a reader needs is linked where a document first uses it, before the rest relies on
  it.
- A concept is declared only for a word whose meaning in the project is narrower than or different
  from its ordinary sense and that another Module uses; any other word is explained in its owner's
  own document. Deciding which concepts exist is part of the Module's quality, not a formality.

### Context

- The Module's context holds every document and definition its Specs rely on. A promise the Module
  relies on whose defining document its declarations do not select is a gap of the Module, repaired
  by an explicit selection, never by reading outside the boundary.
- An evaluation that needed a document it was not given names that document and why it needed it,
  instead of guessing its content.

## Architecture quality

Architecture quality is judged between Modules, from every Module's Specs read together. It asks
whether the division of the project into Modules serves both of the Protocol's purposes: whether a
reader understands the project as a set of responsibilities that fit together, and whether the
boundaries built from those Modules fit the tasks the project actually needs. Each problem names
every Module it concerns; a problem between two Modules concerns both. The criteria fall into six
dimensions.

### Responsibilities

- Each Module is drawn around one responsibility and one axis of change, as
  [Choosing Module boundaries](module.md#choosing-module-boundaries) explains: a capability, a use
  case, a boundary with one collaborator. Things that change together are in one Module, and a
  Module does not collect things only because they are the same kind of artifact.
- Each Module is cohesive: its purpose can be said in one plain sentence, and every part of it
  serves that purpose. A Module whose parts change for unrelated reasons is two Modules.
- A typical change of the project needs the write sets of one Module, or of a few whose
  collaboration it changes, not slices of many.
- Siblings are drawn at comparable levels of abstraction, and each Module's Specs stay at one
  level: a Module that orchestrates others relies on their promises and does not restate their
  internal steps.

### Ownership

- Every concept, promise and responsibility the project relies on has exactly one owner. Two
  Modules that promise the same thing, or both describe themselves as responsible for the same
  decision, overlap; one of them owns it and the other relies on it.
- Nothing the project relies on is left unowned: every step of a main flow, every record several
  Modules share and every rule a guarantee depends on is promised by some Module. A responsibility
  that every Module assumes another carries is a gap.
- A boundary between two Modules is clear: from their Specs alone a reader can tell, for any piece
  of behaviour in the project, which Module promises it.

### Interfaces

- Modules are decoupled: a consumer relies on a few, stable promises of its provider, named where
  it can with `relies_on`, and not on the provider's internal structure, records or order of steps.
- An interface between Modules is narrow and defined by behaviour, through a contract where it is
  shared and through readable promises in every case. A consumer that could only work by knowing
  how its provider is built has an interface that is too wide.
- A consumer's account of what it relies on agrees with what the provider actually promises.

### Dependencies

- Every reliance is declared. A Module whose Specs rely on another Module's promises declares `uses`
  of it; a dependency stated only in prose, or only visible in the code, is undeclared, and its
  impact on the consumer cannot be derived from declarations.
- The direction of each dependency is sensible: it follows who relies on whom. A general Module
  does not depend on a specific consumer in order to serve it, and a provider does not gain a
  relation to a consumer only so that its own Specs can describe that consumer's use.
- Mutual `uses` between two Modules are acceptable, because two Modules may rely on each other's
  promises: a cycle of `uses` alone is not a problem. What is judged is whether each reliance is
  real, declared and explained.

### Failure containment

- Each Module states how it reacts when a collaborator it relies on fails, refuses or is
  unavailable, and what its own consumers then observe. A failure crosses a boundary between
  Modules as a stated outcome, never as undefined behaviour of the consumer.
- A Module's failure cannot silently corrupt another Module's state or promises: where a failure
  leaves work half done, the Spec says which Module detects it and how it is recovered.

### Consistency

- Promises that several Modules make about the same thing agree: the same record, limit, state,
  flow or term is described the same way wherever it appears, and a statement in one Module never
  contradicts its owner's.
- The same kind of problem is solved the same way across Modules unless a Spec explains the
  difference: errors are reported, identities formed and repeated invocations handled alike.
- A parent explains how its children together fulfil its responsibility, and what it says of each
  child agrees with that child's own Specs.
