---
audience: shared
---

# Concorde Spec Protocol

Concorde Spec Protocol 2.0.0 defines Module Specs and Implementation Specs. P1–P4 define the
specification model; P5–P10 below describe the Framework that applies it. Concorde's own project
uses the same model as consumer projects.

### P1. A Module has features, interfaces and an internal domain

A **Module** is a cohesive responsibility with an explicit set of provided features and interfaces
for using them. A feature explains an observable capability, its promises and its failures. An
interface can be an API, function, command, file, protocol, event or another explicitly described
exchange. Every Module Spec MUST explain the inputs, outputs, effects, errors, compatibility and
applicable retry or idempotency behavior of its interfaces. Feature and interface identities are
stable, local to the providing Module and independent of document paths.

A Module's **architecture** is its internal design. Its **domain** is this internal model: the
relevant concepts, submodules, responsibilities, directed relationships, collaborations, rules,
state transitions and completion or failure conditions. Domain is a view within a Module, not a
separate target kind. The same Module definition applies recursively to every submodule. Business
entities and external actors may be described within that model without becoming software modules.

Each Module has at most one structural parent. Parent relationships MUST be acyclic. Using another
Module does not make it a submodule. When A and B share C, C is an independent sibling of A and B,
with one identity and one structural parent. The registry declares `parent` separately from `uses`.
The containing Module explains composition; each consumer explains the promises it relies on.
A leaf Module may be realized directly by implementation files; a composite Module may also have
its own coordination code. Deployment topology and source-file layout do not determine Module
identity or parentage.

A Module that routes work or depends on another Module MUST state that Module's stable ID,
responsibility, selection condition and relied-upon promises in its own Spec. Machine-readable
`concorde-dependencies` declarations describe direct `uses` and child relationships. These local
promises make planning possible without loading the provider's Spec. A hyperlink is navigation,
not an instruction to expand an agent's context.

### P2. Implementation Specs bind reusable implementations to files

An **Implementation Spec** describes one implementation and binds an explicit, nonempty set of
project-relative files. It defines their implementation responsibilities, interfaces, dependencies,
constraints and relevant verification. Files may contain code, tests, configuration or authored
runtime assets. Generated output and project control files are not authoring sources.

Each implementation file MUST be bound to exactly one authoritative Implementation Spec. File
bindings are explicit file paths, not directories, recursive discovery or implicit ownership of
future files. A declared file may be pending creation; implementation completion must materialize
required outputs. One Implementation Spec may bind several files. Several Modules may reference
the same Implementation Spec, and one Module may reference several Implementation Specs.
Reusing implementation does not merge Modules, create another structural parent, or require a
shared Module when the reusable object is code rather than an independently provided capability.

The registry records Module-to-Implementation references and Implementation-to-file bindings. The
Framework derives the reverse Implementation-to-Module index. Changes to a binding, an
Implementation Spec or a bound file invalidate affected implementation evidence for every user.
Every affected Module's relied-upon contract must be checked in its own context. Source reuse
never grants one Module authority to change another Module's Spec.

### P3. A Module Spec is a complete, explicit context

Each Module has a stable identity and an explicitly registered nonempty Markdown collection. It
registers exactly one local `module.md` reading entry. The complete collection describes features,
usage interfaces and internal architecture; authors may split topics across additional documents.
An architecture diagram may clarify the internal domain, but a diagram or heading is not proof of
semantic completeness. Initialization may create an honest stub that marks unknown facts.

Every physical Spec document declares a globally unique document ID, its exact registered target
references and main visibility in a `concorde-document` block. An explicitly shared Module document
is part of each referring Module's own collection; it does not grant any other document. An
Implementation Spec's documents cannot also be Module Spec documents. Implementation reuse is by
Implementation Spec identity, never by copying the same binding into several owners.

The Module's own complete collection is its sole project-Spec context for non-code work. Readers,
Spec authors, assessors, planners and task authors MUST be able to determine behavior and tasks
from that Module Spec alone. They MUST NOT read Implementation Specs or implementation source to
fill in missing meaning. A missing promise is a Module Spec gap and must be corrected there.
Neither parent, child, dependency, feature focus nor a directory walk adds context implicitly.

Only the code-writing implementation phase appends the explicitly referenced Implementation Specs
and their bound files to the Module's contract context. Implementation detail does not supply
missing Module semantics. Code review checks code against the Module contract; it does not expand
non-code phases into implementation cognition. Changes to code do not silently alter a Module's
promised behavior.

### P4. Versioned agreement and conformance

A project binds to one explicit Protocol version and digest. Profile 9 uses registry schema 2:
Module targets, one `parent`, explicit `uses`, Module features and interfaces, and a separate
Implementation Spec collection with document and file bindings. Older profile structures require
an explicit migration; names or directory ancestry are not sufficient to infer the new design.

Deterministic checks establish identity, membership, single-parent composition, unique file
ownership, dependency declarations and interface consistency. They do not prove every future task
is specified or every implementation is correct. Behavioral review and configured tests supply
additional, revision-bound evidence. The Framework's own Specs follow these same rules.

@include prompts/protocol/framework-profile.md
