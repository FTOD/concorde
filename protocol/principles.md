# Spec Protocol principles

Concorde Spec Protocol 16.2.0 defines:

- How a project describes itself as a set of Modules.
- What each Module promises.
- How the Modules and their files relate.

The Protocol applies to project Specs, including those of software implementing the Protocol.
The standard's own chapters need not describe themselves as Modules.

## Two purposes

The Protocol exists for two purposes. Every rule in it serves at least one of them. Each chapter
says how its rules do.

1. **Understanding.** A human grasps the backbone of the project quickly from its specification:
   - Its parts.
   - What each is for.
   - How they fit together.
   - How the main flows run.

   The ultimate goal is that a human never needs to read the code to understand the project.
   The specification is enough.
2. **Boundaries.** From the specification, a harness running an AI task can derive exactly what
   the task may read and what it may write. Different tasks need different boundaries. The
   Protocol therefore defines the sets that boundaries are composed from and the task types
   that compose them.

The two support each other. Only if what lies inside it is understandable is a boundary useful.
A Module that a human can understand as one responsibility is also the natural unit of a task.

Four failures undermine these purposes. The rules of the Protocol are designed against them:

1. **Inferred promises.** A reader concludes that something is promised because one of these
   suggested it:
   - A file.
   - A directory.
   - A name.
   - A link.
   - An adjacent paragraph.

   Nothing promised it.
2. **Meaning drift.** The same word denotes different things in different documents, silently.
3. **Authority creep.** Permission to read something becomes permission to change it, or a
   relationship becomes an execution grant.
4. **Fabricated evidence.** Coverage or conformance is claimed by the promise itself rather than by
   anything that ran.

## The model at a glance

A project's specification is **one graph**. Its nodes are the things the specification declares.
Its edges are the relations between them. Everything else in the Protocol is either how the graph
is written down, or something computed from it.

```d2 illustrative
direction: right
parent: Module {
  m: Module {
    d: Document {
      rz: Realization {
        f: Implementation files {shape: cylinder}
      }
      rs: Requirement / Scenario
      k: Contract
    }
  }
}
glossary: Glossary {
  c: Concept
}
provider: Module
t: Test file {shape: cylinder}
parent.m -> provider: uses / includes
parent.m.d -> glossary.c: mentions
glossary.c -> parent.m: owned by
parent.m -> parent.m.d.k: participates
t -> parent.m.d.rs: verifies
```

Nesting shows composition:

- A Module contains Modules.
- A Module owns documents.
- A document defines nodes.
- A realization binds files.

The project's one glossary declares every concept. Each concept names the Module that owns it.

**Nodes.** Seven types, defined in [Node types](model.md):

| Node | What it is |
| --- | --- |
| Module | One responsibility. The unit of ownership, of context and of task boundaries |
| Document | A Markdown reading file paired with its JSON metadata; the unit a Module owns |
| Concept | A named meaning a reader would get wrong without its definition, shared by more than one Module; its title is a term, declared in the glossary |
| Realization | A binding of implementation files to the Module |
| Requirement | One Module-wide `SHALL` obligation |
| Scenario | One concrete situation in `GIVEN`/`WHEN`/`THEN` steps |
| Contract | The versioned agreement for a shared interface |

**Edges.** Thirteen typed, directed relation types are defined in [Relations](relations.md):

- `owns`, `defines`, `contains` and `uses` state who is responsible for what.
- `includes` selects extra reading.
- `binds` joins the specification to code.
- `mentions`, `narrows`, `supersedes`, `contrasts` and `relates` connect meanings and architecture.
- `participates` and `verifies` tie contracts and tests to promises.

**Where the graph is written.** Every node and edge is declared exactly once. Concepts and
relations whose source is a concept are entries of the project's one **glossary**.
Each entry names its owning Module. Everything else is declared in a document owned by the Module
responsible for it. The declaration is in its reading, by a fixed syntax, or in its metadata.
A Module's own relations are in its entry's metadata. The project registry mirrors them for a
global view.

**What is computed from the graph.** Nothing below is declared. All of it is derived:

- **Context** — what a reader of a Module may read. See [Context](context.md).
- **Scope** — what a task bound to a Module may be given to write. See
  [Boundaries](boundaries.md).
- **Boundary** — the read and write sets a task receives, fixed by its task type.
- **Views** — diagrams, indexes and pages a human reads. See [Views](views.md).
- **Checks** — decidable rules that the graph is well formed. See [Checks](checks.md).

A few more words are used throughout:

| Term | Meaning |
| --- | --- |
| Declared | Written in the specification: a node or relation stated at its declaration site |
| Derived | Computed from declarations, never written by hand |
| Declaration | The single place where a node or relation is stated |
| Owner | The Module entitled to change a node; every node has exactly one |
| Entry | A Module's `module.md` document, the start of reading it and the home of its own relations |
| Reading | The Markdown member of a document, written for humans |
| Metadata | The JSON member of a document, holding identities and declarations |
| Registry | The project-wide index of Modules, a checked mirror of their entries |
| Glossary | The project's one file of concept entries, each with its owner and one-sentence definition |

## Axioms

### A1. Every node has one identity, one owner and one explanation

Every declared node MUST have:

- A stable project-wide identity.
- Exactly one owning Module.
- Nonempty explanatory prose in a document its owner owns.

A declaration without an explanation is invalid, not merely incomplete. Identity survives title
and path changes.

*Serves both:* a reader always finds the explanation. A harness always knows whose write set a
node lies in.

### A2. Every relation is typed, directional and declared exactly once

A relation MUST have:

- A registered type.
- An explicit source and target.
- One declaration site fixed by its type.

The same fact MUST NOT be declarable in two places. The only permitted copy is a mirror the
Protocol names, the project registry. Its equality with the declarations is checked.
Except for a **term link**, the following MUST NOT create a relation:

- A filename.
- A path.
- A title.
- A prose sentence.
- An unchecked diagram.
- A directory neighbourhood.
- A link.

A term link is a link to a glossary entry, which is the declaration of `mentions`.

*Serves both:* nothing is promised by accident. Boundaries depend only on declarations.

### A3. Reading, writing and proving stay separate

Read sets and write sets are derived from different declarations. Being able to read a document
never makes it writable. A provider's Specs are readable by its consumers.
They are writable only within the provider's own scope. Realization bindings put file **names**
in the read side.
Only through a task boundary do contents become readable or writable. Evidence is never produced
by specification content.

*Serves boundaries:* this is the rule against authority creep.

### A4. Every relation declares what context it grants and what it requires

A relation type MUST declare `context_grants` and `context_requires`. For every Module, its
declared relations MUST grant everything its declared relations require. The reconciliation is a
structural check, defined in [Context](context.md).

*Serves both:* a reader of a Module has every definition its Spec relies on. A harness that
grants the Module's read set grants a self-sufficient one.

### A5. Evidence originates from what ran, never from what was promised

An evidence relation MUST be declared by the artifact that executes, not by the specification
that the artifact verifies. A specification MUST NOT declare its own coverage.

*Serves both:* a reader can trust that coverage was not merely claimed. Coverage cannot be
claimed from inside the write set of the Module whose promises it covers.

### A6. Views are derived or checked

A published diagram, index or navigation tree is derived from declared relations. A diagram written
in reading is either **checked** or **illustrative**. A checked one asserts only declared
relations. An illustrative one is explicitly marked and excluded from the model.
See [Views](views.md).

*Serves understanding:* pictures a human relies on cannot silently diverge from the model.

### A7. No inference, no recursion

The model is assertional. Every check operates on declared relations only. Unless its type says
so, no relation is transitive, symmetric or invertible. Derived indexes are never a source of
obligations. Document selection is one level and never recursive. The only closure is over the
glossary. A selected definition brings the definitions it links. This adds sentences, never
documents.

*Serves boundaries:* every set is computable. Every member is attributable to a declaration.

## Conformance

A conformance claim identifies its Protocol version. It distinguishes three claims that cannot
substitute for one another:

- **Structural conformance.** Identities, ownership, pairing, declaration sites, cardinalities,
  checked views and the context reconciliation all hold. This is machine-decidable.
  See [Checks](checks.md). It is what makes boundaries computable.
- **Semantic sufficiency.** The readable content explains the following to the intended reader:
  - The responsibility.
  - Its correct use.
  - Its design.
  - Its obligations.

  The Modules together form an architecture a reader can understand and a task can rely on.
  This is what makes the specification understandable. It is not machine-decidable.
  It is judged against the criteria of [Evaluating a Spec](evaluation.md).
- **Implementation conformance.** The realization satisfies the requirements and scenarios. This is
  established by evidence, never by structure.

Passing structural checks MUST NOT be reported as either of the other two. Missing meaning is an
attributed gap. To repair it, a reader MUST NOT read outside its boundary or infer a promise from
source code. The one sanctioned route from code to specification is a `code-to-spec` task
(see [Boundaries](boundaries.md#task-types)). The task describes an existing realization under its
own rules. It leaves every doubtful intent as a reported gap.

## What the Protocol does not define

The Protocol does not define:

- Which task type a harness assigns to a piece of work and how it enforces the resulting boundary.
- Docsite pages, navigation, themes and interaction.
- The serialization and location of the project registry.
- Tool configuration.
- Worker wire formats.
- Context delivery.

These are separate agreements. A change in any of them is not a Protocol version change.
