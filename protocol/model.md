# Node types

This chapter defines every kind of thing a specification may declare. [Relations](relations.md)
defines how they may be connected. The machine-readable vocabulary of both is
[`model.yaml`](model.yaml). The decision procedures are in [Checks](checks.md).

Each node type exists because a human reader needs the thing it names explained, a harness needs
it to compute a boundary, or both. Each section says which.

The model has **seven node types** and three **value types**. Because the specification makes no
promise about a value type, it has:

- No identity.
- No owner.
- No explanation.

## Common obligations

| Field | Meaning |
| --- | --- |
| `id` | Stable, project-wide unique, matching `^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$` |
| `type` | One of the seven node types below |
| owner | Exactly one Module identity, derived from the defining document or declared for a document |
| explanation | Nonempty prose in a document the owner owns; where it lives depends on the node type |

An ID prefix does not establish ownership. Titles and paths may change without changing identity.
An explanation cannot be outsourced. It is never a URL or a path into another document.

Nodes are declared at one of three sites:

- A **concept** is an entry of the project [glossary](#the-glossary). The entry names its owner.
  It points to its explanation in a document that owner owns.
- A **realization** is a record in a document's metadata. The record points to its explanation
  with a local `meaning` anchor.
- **Reading-declared** nodes (`requirement`, `scenario`, `contract`) are located by reading syntax.
  Their defining section is their explanation.

A Module and the documents it owns are declared in the `module` block of its entry's metadata.
They are mirrored in the project registry.

## module

**What it is.** One cohesive software responsibility, and the unit of context selection.

**Understanding.** A reader learns the system as a set of responsibilities, each explained by one
owner, independent of how files happen to be arranged.

**Boundaries.** A Module is what a task is bound to. Its read sets and write sets are all computed
from it. Thus, "who promises this" and "what a task on it may read and write" have one answer that
survives file movement. Because a reader cannot detect meaning that was silently withheld, the
Protocol deliberately accepts over-inclusion in read sets.

**Fields.** The entry's `module` block declares `id` (the entry's owner) and `title`.
The registry mirrors these fields. Its owner is itself. Its explanation is its entry document.
The entry document opens with its purpose.

**Constraints.** A Module MUST own exactly one document whose role is `module` and whose reading
path ends in `module.md`. That document is its **entry**. A Module need not do any of these:

- Correspond to a package.
- Correspond to a directory.
- Correspond to a service.
- Correspond to a process.

Its realization may do any of these:

- Span physical files.
- Share physical files.
- Omit physical files.

A composite Module may bind no implementation of its own. A composite Module may also bind files,
such as end-to-end tests of its own promises.

## document

**What it is.** A reading Markdown file **paired** with its metadata file. The pair is one node.

**Understanding.** Prose and the declarations it justifies cannot be separated.
Thus, metadata never becomes a second, unreviewed specification.

**Boundaries.** The pair is the unit of:

- Owning the pair.
- Selecting the pair.
- Writing the pair.

A boundary always contains both members or neither.

**Fields.** `id`, `owner` and `role` are stated in the metadata and agree with the owner's `owns`.
`role` is exactly `module` or `implementation`, with no default. A document explains itself.
It has no separate explanation.

- `module` — the entry and explanatory topics cover:
  - The Module's responsibility.
  - The Module's correct use.
  - The Module's design.
  - The Module's collaborations.
- `implementation` — the precise requirements, scenarios and canonical contracts. These are
  specifications, not source code. They are reading content like any other document.

**Constraints.** Both members share:

- The same owner.
- The same identity.
- The same inclusion provenance.

Registering the reading path registers its exact companion. Role is document organization only.
Role MUST NOT act as any of these:

- An ownership level.
- A context filter.
- A separate Spec kind.

The two roles serve understanding. Explanation is not buried under acceptance cases.
Precise obligations are not diluted into prose.

## concept

**What it is.** One named meaning a reader would get wrong without its definition, shared by more
than one Module. A concept can be:

- A domain word.
- A boundary actor.
- An external standard.
- A participant in a collaboration.

Its title is the **term** the specification uses for it.

**Understanding.** Meaning is what crosses Module boundaries. A concept gives a word one owner and
one canonical sentence. The whole project shares one list of them, so a reader finds one meaning
per word everywhere. A tool checks these as declarations instead of prose conventions:

- Specializing a concept.
- Retiring a concept.
- Colliding concepts.

**Boundaries.** A reader receives the definition of every concept its documents link and of every
concept its declarations name, never the whole glossary.

See [Context](context.md#term-selection). The definition is one sentence.
The extended explanation lives in a document of the owner. It is read only through one of these:

- A `uses` of the owner.
- A `contains` of the owner.
- An `includes`.

`referenced-by` makes the impact of changing a definition computable.

**Fields.** One entry of the glossary:

| Field | Meaning |
| --- | --- |
| `id` | Identity; a concept identity begins `concept.` |
| `title` | The term, unique in the project under the normalization of `CHK.contrasts.required` |
| `owner` | The Module entitled to change the meaning |
| `definition` | One sentence: the canonical meaning, written once. It MAY link other concepts by term link |
| `explanation` | `<reading path>#<anchor>`: the extended explanation, in a `module` document the owner owns |
| `retired` | Optional object `{"reason": "..."}`; the term is kept only for migration readers |
| `external_conflict` | Optional prose naming a conflicting usage outside this project |

The entry also declares `narrows`, `supersedes`, `contrasts` and `relates` relations whose source
is the concept. See [Relations](relations.md#meaning).

**Which words are concepts.** A word earns a glossary entry only when both hold:

- **It is not common sense.** Its meaning in the project is narrower than, or different from,
  ordinary usage. Thus, a reader who takes the word in its ordinary sense would misread it.
- **It crosses a Module boundary.** A Module other than its owner uses it. The words of the Module
  that declares the glossary are the project's core terms and are exempt from this condition.

Any other word is written in its ordinary sense. When the owner needs it in a narrower sense, the
owner's own document explains it where it is first used.
Unless other Modules reason about them, these are not concepts:

- The name of an operation.
- The name of a command.
- The name of a rule.
- The name of a component.
- A record whose shape a contract already gives.

`CHK.concept.local` reports a concept no other Module uses. No check decides whether a word is
common sense.

**Constraints.** A concept MUST NOT bind implementation. A concept MUST NOT stand for another
Module. A collaboration with another Module is a `uses` or `contains` relation.
A naming collision with another Module is a `contrasts` relation.

**Who owns a word.** Owning a concept means being entitled to change its meaning.
Its entry lies in the owner's write set. A change concerns every Module whose context holds the
definition. Ownership does not mean inventing the word or using it most. Every concept has exactly
one owner, chosen as follows:

- A word of a provider's own interface belongs to the provider.
- A word several Modules use with one meaning belongs to their nearest common ancestor in the
  composition tree, or to the root. When the owner is hard to name, move the word one level up.
- A project has one meaning per term. A word two Modules use differently needs two terms, such as
  `Session round` and `Headless round`. When a reader could confuse them, the terms are connected
  by `contrasts` or `narrows`.

## The glossary

**What it is.** The project's one JSON file of concept entries. It is not a node.
It has no owner. Each of its entries has one. A project declares it by the `glossary` field of its
root Module's `module` block. See [Required format](format.md#glossary).
A project without concepts needs no glossary.

**Understanding.** A reader looks words up in one place and never meets two definitions of one
term. A publisher renders the glossary as a page. Every term link leads there.

**Boundaries.** The glossary is the declaration site of every concept.
Thus, it is a shared file with entry-level ownership. A task bound to a Module may change the
entries that Module owns and add entries naming it as owner, and nothing else in the file.

See [Boundaries](boundaries.md#the-glossary). Definitions reach a reader one by one, as
[term selection](context.md#term-selection) chooses them, never as the whole file.

## realization

**What it is.** A declaration binding exact implementation paths or directory prefixes to this
Module.

**Understanding.** A reader learns where a promise is realized without inferring it from directory
names.

**Boundaries.** Its entries are the Module's `ImplementationScope`: the code a task bound to the
Module may be given to change. Only paths that exist are bound. A new file is created before it is
bound, or below a bound directory.

**Fields.** `id`, `type`, `title`, `meaning`, `entries` (exact project-relative paths, or directory
prefixes ending in `/`).

**Constraints.** Every entry MUST exist. Within a Module no two realizations list the same
entry. The longest covering entry determines which realization a file belongs to. A directory
entry binds present and future regular files below it under the tool's deterministic exclusion
rule. None of these may be bound:

- A document member.
- Generated output.
- A project-control record.

A bound directory MUST NOT contain a document member. Several Modules MAY bind the same path.
Each keeps its own promises. A change concerns all of them.

A realization records what exists, never an intent. A path that does not exist yet is not bound.
On the read side, listing a path grants its **name**. Contents are readable or writable only
through a task boundary. See [Boundaries](boundaries.md).

## requirement

**What it is.** One decidable, Module-wide obligation.

**Understanding.** A Module-wide promise is stated once, exactly, and survives the churn of the
situations that demonstrate it.

**Boundaries.** Its identity lets an exact promise be named in:

- Reviews of the promise.
- Tasks concerning the promise.
- Evidence of the promise.

**Constraints.** A heading in an `implementation` document declares a requirement.
The heading supplies `id` and title. The section is its explanation.
Its statement is one sentence containing `SHALL` or `SHALL NOT` exactly once.
Because two obligations under one identity make partial satisfaction undecidable, they MUST be
split.

## scenario

**What it is.** One concrete situation with:

- Preconditions of the situation.
- A trigger for the situation.
- A promised outcome of the situation.

**Understanding.** A concrete situation shows what a requirement means in practice.
The step grammar keeps a situation from quietly growing into a Module-wide obligation.

**Boundaries.** A requirement cannot be executed. A scenario is what tests declare they verify.
A task focused on a scenario is bound to the scenario's owner.
The task receives that owner's whole boundary.

**Constraints.** A heading in an `implementation` document declares a scenario.
The heading supplies `id` and title. When their outcomes differ in any of these ways, situations
get their own scenarios:

- Successful outcomes.
- Failed outcomes.
- Repeated outcomes.
- Concurrent outcomes.

A Module-wide obligation is defined once as a requirement and linked, never restated in steps.

## contract

**What it is.** The canonical, versioned agreement for a shared interface: an API, command,
protocol, event or file boundary.

**Understanding.** A shared interface is stated once, with one owner.
Every participant says which version it conforms to.

**Boundaries.** Participants are declared, so the impact of a contract change and the multi-Module
write boundary it needs are computable.

Without a version, a participant bound to an older meaning is undetectable.

**Fields.** `id`, `version` (positive integer), `schema`, `semantics`, `example`, all inside one
`concorde-contract` fence in an `implementation` document. Its explanation is `semantics` together
with the prose of the section containing the fence.

**Constraints.** The schema vocabulary is explicit and offline.
A schema MUST NOT load Spec documents or remote resources. The example MUST satisfy the schema.
A behaviour or schema change increments `version`. For that change, every participant is reconciled
atomically.

## Value types

These appear as relation targets or attributes but are not nodes.

| Value | Where it appears | Why it is not a node |
| --- | --- | --- |
| **path literal** | `binds`, external `includes`, `verifies` | A path carries no promise and has no owner in the Spec's sense. |
| **anchor** | `meaning` of realizations and reified relations, `explanation` of concepts | It has no identity of its own; only its declaration refers to it. |
| **digest** | context identity | It is a measurement of a source member, not a declared thing. |
