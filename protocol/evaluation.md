# Evaluating a Spec

This is the evaluation part of [Spec writing guidelines](writing.md). [Required format](format.md)
defines the structure a Spec must have. [Writing guidance](module.md) defines what its content must
communicate. This chapter states how a Spec is judged good. It serves understanding. A Spec that
passes every structural check can still leave its reader unable to rely on it. Only a judgment of
its content finds that.

## A judgment, not a check

Evaluation is a judgment of meaning. It is **not deterministic**. Two careful evaluations of the
same Specs may differ in these ways:

- They may notice different problems.
- They may weigh them differently.
- They may word them differently.

The criteria below make evaluations comparable in what they look for. They do not make them
decidable. No criterion is a [structural check](checks.md) or can become one. A result of
evaluation is never structural conformance, and never implementation conformance either. It is
evidence about [semantic sufficiency](principles.md#conformance) only, bound to the exact Specs it
read. An evaluation that found no problem shows that it found none, not that none exists.

A problem is established by the text of the Specs that shows it. The evaluation can point to any
of the following:

- The passage.
- The declaration.
- The absence.

An impression that cannot be tied to the Specs is not a problem.

Evaluation happens at two levels, each read from its own boundary:

| Level | What is judged | What is read |
| --- | --- | --- |
| [Module quality](#module-quality) | one Module's own documents, for the reader of that Module | the Module's `SpecContext` and external context, as a `review-spec` task receives them |
| [Architecture quality](#architecture-quality) | how the project is divided into Modules and how they rely on each other | every Module's Specs, `ProjectSpecification`, as a `review-architecture` task receives them |

Neither level reads code contents (see [Task types](boundaries.md#task-types)). A Spec is judged by
what it tells its reader. Whether the code does what the Spec says is implementation conformance,
established by evidence. Code never repairs a Spec's missing meaning.

## Blocking and advisory problems

Every problem is **blocking** or **advisory**:

- **Blocking**: a reader of the Module, or a task bound to it, could not rely on the Spec as
  written. The Spec leaves them unable to act, or leads them to act wrongly:
  - A requirement that joins two obligations.
  - A scenario whose outcome cannot be observed.
  - An entry that never shows how a normal interaction goes.
  - Two documents or two Modules that contradict each other.
  - A term used in two meanings.
  - A responsibility two Modules both claim or none owns.
  - A dependency that is relied upon but not declared.
- **Advisory**: the Spec can be relied upon, but could serve its reader better:
  - Wording that could be clearer without changing what a reader would do.
  - An order that makes the reader wait for the idea they need.
  - A diagram that would make a relationship easier to follow.
  - A boundary that could be drawn more cleanly without any task being misled today.

Whether a problem is blocking depends on its effect on a reader and a task, not on the size or
difficulty of the repair. A missing diagram alone is advisory. When the meaning a picture would
show is itself missing or contradictory, a picture alone cannot supply the missing meaning that
is the problem.

The Protocol defines no further grading. The following belong to the tools and the project's own
process:

- What is done with a problem once found.
- Who repairs it.
- Whether it must be decided by someone else.

## Module quality

Module quality is judged for the [intended reader](module.md#the-intended-reader). This reader has
general software knowledge and does not know the project's code or history. From the Module's
Specs alone, the reader must be able to explain:

- What it is for.
- When and how to use it.
- A normal interaction and its result.
- The important stopping conditions.
- Why its design supports its guarantees.

Only the Module's own documents are judged. A problem seen in a provider's or an included document
concerns that other Module. Its own evaluation judges it. The criteria fall into six dimensions.

### Readability

- The entry lets a reader understand the Module quickly, in the
  [reading order](module.md#the-entry) the guidance recommends:
  - First, short plain prose about:
    - What the Module is for.
    - Who relies on it.
    - Where its promises stop.
  - Then, the core concepts.
  - Then, overview diagrams of its main structure, functions and flows.
  - Then, the details.

  The Protocol requires no section, so the order is judged, not the headings.
- Where the Module has entry points, a reader can follow a coherent normal path from an input to
  its result. The reader meets this path before errors, repetition and cancellation. On the path,
  a concrete illustration stands wherever an abstraction would hide a decision the reader has to
  make.

  A reader never has to assemble instructions from formal statements.
- Operational detail stays with the Module that owns it. A parent shows its children's process at
  the level of its own concepts. The parent leaves their commands to them.
- Unknowns and unsupported behaviour are stated honestly, never invented to fill a structure.
- The sentences follow [Sentence style](style.md). The style checks report:
  - Sentences that are long.
  - Semicolons.
  - Sentences with more than one requirement keyword.

  An evaluation does not report them again. It judges the rules that no program decides:
  - A requirement and every statement of behaviour name the actor and use the active voice.
  - Each sentence carries one fact, even when it is short.
  - Three or more conditions, cases or items stand in a list, not in a run of clauses.
  - A condition comes before the statement it limits.
  - Simple tenses say what is true and what happens.
- A text in this style still says what it means. An evaluation reports each of these drifts, which
  a rewrite for shorter sentences can cause:
  - One obligation split into separate rules, such as a list whose items are obligations of their
    own instead of conditions of the statement.
  - A condition, exception or failure moved out of the statement of its requirement.
  - A condition moved away from what it limits, such as a limit of one action placed before the
    subject of the whole obligation.
  - The subject of an obligation changed to a party that does not bear it, or an actor that the
    text did not name before.
  - A dropped word that links or limits facts, such as "since", "because", "so that", "only",
    "each", "every" or "never".
- While a reader still understands it correctly, a sentence that breaks the style is advisory.
  When the reader cannot tell who must act or what is required, it is blocking. A requirement that
  hides its actor in the passive voice is an example. A drift that changes what a requirement
  requires or who bears it is blocking too.

### Obligations

- Each requirement is one decidable Module-wide obligation, with exactly one `SHALL` or
  `SHALL NOT`. It is not two obligations joined in one sentence. A guarantee that holds only in
  one situation belongs in a scenario, not a requirement.
- Each scenario is one testable situation whose `THEN` steps state observable outcomes.
- Each obligation is defined once. Module-role prose explains the important guarantees. It links
  to them. Module-role prose never does any of the following:
  - Weaken an obligation.
  - Duplicate an obligation.
  - Contradict an obligation.
- An interface is specified by behaviour. Readable text explains its inputs, outputs, effects,
  failures, compatibility and repeat behaviour.
  These are not left to be inferred from a schema's shape.

### Design

- The entry explains why the following fulfil the guarantees, connecting each significant choice
  to a problem it prevents:
  - The decomposition.
  - The state.
  - The control and data flow.
  - The collaboration.
  - The failure containment.

  A list of names in call order is not an explanation.
- Every child and every provider has an explanation of:
  - What its responsibility is.
  - When the collaboration applies.
  - Which promises are relied upon.
  - What the Module's own duties and failure reactions are.

  A declared relation with a link and no explanation does not meet this.
- Significant choices are told apart from incidental current implementation and from open
  questions.

### Views

- A diagram answers one clear question. It stands next to the prose it complements. The diagram
  uses the same terms. The kind of view suits the question. A process is a workflow by default.
  Only when the interleaving of messages is the point is a sequence diagram used.
- A checked diagram asserts only declared relations. Any other view is marked illustrative. It
  claims no authority beyond its prose. A load-bearing collaboration is never described only in an
  illustrative diagram.
- A place where a diagram would make relationships, order, branching, state or data clearer is a
  problem of readability.
  No count or kind of diagram is required.

### Terminology

- Every term the Module owns has one clear one-sentence definition and an explanation. The term
  is used with that meaning throughout. Where it could be confused with another term or with
  common usage, it says so.
- Every term a reader needs is linked where a document first uses it, before the rest relies on
  it.
- Only when a word's meaning in the project is narrower than or different from its ordinary sense
  and another Module uses it is a concept declared.

  Any other word is explained in its owner's own document. Deciding which concepts exist is part
  of the Module's quality, not a formality.

### Context

- The Module's context holds every document and definition its Specs rely on. If the Module relies
  on a promise whose defining document its declarations do not select, the Module has a gap. An
  explicit selection repairs the gap. Reading outside the boundary never repairs it.
- When an evaluation needed a document it was not given, it names that document and why it needed
  it, instead of guessing its content.

## Architecture quality

Architecture quality is judged between Modules, from every Module's Specs read together.
It asks whether the division of the project into Modules serves both of the Protocol's purposes.
The first purpose is that a reader understands the project as a set of responsibilities that fit
together. The second purpose is that the boundaries built from those Modules fit the tasks the
project actually needs.

Each problem names every Module it concerns. A problem between two Modules concerns both. The
criteria fall into six dimensions.

### Responsibilities

- Each Module is drawn around one responsibility and one axis of change, as
  [Choosing Module boundaries](module.md#choosing-module-boundaries) explains:
  - A capability.
  - A use case.
  - A boundary with one collaborator.

  Things that change together are in one Module. A Module does not collect things only because
  they are the same kind of artifact.
- Each Module is cohesive. Its purpose can be said in one plain sentence. Every part of it
  serves that purpose. A Module whose parts change for unrelated reasons is two Modules.
- A typical change of the project needs the write sets of one Module, or of a few whose
  collaboration it changes, not slices of many.
- Siblings are drawn at comparable levels of abstraction. Each Module's Specs stay at one level.
  A Module that orchestrates others relies on their promises. It does not restate their internal
  steps.

### Ownership

- The following each have exactly one owner:
  - Every concept the project relies on.
  - Every promise the project relies on.
  - Every responsibility the project relies on.

  If two Modules promise the same thing or both describe themselves as responsible for the same
  decision, they overlap. One of them owns it and the other relies on it.
- Nothing the project relies on is left unowned. Each of the following is promised by some Module:
  - Every step of a main flow.
  - Every record several Modules share.
  - Every rule a guarantee depends on.

  A responsibility that every Module assumes another carries is a gap.
- A boundary between two Modules is clear. From their Specs alone, a reader can tell which Module
  promises any piece of behaviour in the project.

### Interfaces

- Modules are decoupled. A consumer relies on a few, stable promises of its provider, named where
  it can with `relies_on`. The consumer does not rely on any of the following of the provider:
  - Its internal structure.
  - Its records.
  - Its order of steps.
- An interface between Modules is narrow and defined by behaviour. Where it is shared, a contract
  defines it. Readable promises define it in every case. A consumer that could only work by knowing
  how its provider is built has an interface that is too wide.
- A consumer's account of what it relies on agrees with what the provider actually promises.

### Dependencies

- Every reliance is declared. A Module whose Specs rely on another Module's promises declares
  `uses` of it. A dependency stated only in prose, or only visible in the code, is undeclared. Its
  impact on the consumer cannot be derived from declarations.
- The direction of each dependency is sensible: it follows who relies on whom. A general Module
  does not depend on a specific consumer in order to serve it. A provider does not gain a relation
  to a consumer only so that its own Specs can describe that consumer's use.
- Mutual `uses` between two Modules are acceptable, because two Modules may rely on each other's
  promises. A cycle of `uses` alone is not a problem. Each reliance is judged on whether:
  - The reliance is real.
  - The reliance is declared.
  - The reliance is explained.

### Failure containment

- For each of these cases, each Module states how it reacts and what its own consumers then
  observe:
  - A collaborator it relies on fails.
  - A collaborator it relies on refuses.
  - A collaborator it relies on is unavailable.

  A failure crosses a boundary between Modules as a stated outcome, never as undefined behaviour
  of the consumer.
- A Module's failure cannot silently corrupt another Module's state or promises. Where a failure
  leaves work half done, the Spec says which Module detects it and how it is recovered.

### Consistency

- Promises that several Modules make about the same thing agree. Wherever it appears, each of the
  following is described the same way:
  - The same record.
  - The same limit.
  - The same state.
  - The same flow.
  - The same term.

  A statement in one Module never contradicts its owner's.
- Unless a Spec explains the difference, the same kind of problem is solved the same way across
  Modules:
  - Errors are reported alike.
  - Identities are formed alike.
  - Repeated invocations are handled alike.
- A parent explains how its children together fulfil its responsibility. What it says of each
  child agrees with that child's own Specs.
