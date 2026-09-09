<!--
Sync Impact Report
- Version: 13.0.0 -> 14.0.0
- Bump rationale: MAJOR; replace Domain/Service/Module kinds with Module and reusable Implementation Specs.
- Modified principles: P1–P10; complete Module contexts, explicit file ownership and per-consumer evidence.
- Added sections: Module architecture, implementation reuse and direct authorized maintenance.
- Removed sections: separate Domain/Service taxonomy and visibility-trimmed cognitive contexts.
- Deferred placeholders: none.
-->

# Concorde Constitution

Version: 14.0.0. Architecture Profile 9; Workspace Protocol 14; Delivery Proposal 10.

## Part A: universal Concorde principles

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

## Concorde Framework execution profile

### P5. One complete Module context per bounded task

A bounded invocation selects one Module and freezes its complete document collection, task,
constraints, phase, Protocol and role instructions. Feature/interface focus does not trim that
collection. Planner and task-author inputs contain no Implementation Specs or source locators.
A global coordinator may discover explicitly admitted Module contracts for routing; each selected
worker is a fresh invocation with only its own complete Module context. Routing metadata and typed
worker results are explicit inputs, not permission to inspect implementation. Coordinator discovery
never loads Implementation Specs. Source-code phases use the selected Module's explicit file bindings.

Context identities cover document membership and bytes, Protocol and instructions, declared stage
artifacts and lifecycle identity. Code-writing context identities additionally cover the referenced
Implementation Specs, file bindings and their current file digests. A changed input requires a new
snapshot. Implementation-only changes do not add implementation knowledge to a planner.

### P6. Gaps and review are tied to the affected contract

Missing required behavior is a Module Spec gap. Name the missing promise, blocked step, Module and
snapshot; continue only independent work. Implementation source cannot resolve that gap implicitly.
A failed execution, an explicit prohibition and a missing runtime value with defined failure
behavior are distinct from an unspecified contract.

Spec review uses Module Specs. Code review uses the same Module contracts and authorized code in a
fresh read-only invocation. A review records its exact inputs, coverage, findings and completion.
Changed relevant inputs invalidate it. Skipped, failed, incomplete and successful reviews remain
distinct. Shared implementation changes require checks for all using Modules, with separate Module
contexts and explicit per-consumer evidence. No passing structural check proves semantic completeness.

### P7. Execution authority is explicit

The host binds each normal Framework invocation to declared context and file permissions. Only
implementation invocations receive Implementation Spec bodies; only code-writing invocations may
change bound source. Code review and deterministic checks have separately declared read authority.
The registry's reverse index never grants a writer another Module's Spec or unrelated code.
Unsupported enforcement fails closed. An outer developer-authorized maintenance session may read
and modify the project directly; its explicit authorization does not silently widen normal worker
permissions or become a project business contract.

Agent instructions, Skills, schemas and rule assets are deterministic projections of authored
sources. Generated output is not edited as source. Builds distribute Module and Implementation
kind definitions and the accepted Protocol binding. Configuration, installation and publication
must agree on that binding. Runtime Agent responsibility files are authored implementation assets,
not another category of project Spec.

### P8. Structure and bindings change together

Topology changes reconcile Module parentage, uses, features, interfaces, document memberships and
Implementation references as one consistent proposal. A shared file has one Implementation Spec
owner. The reverse index identifies every affected Module before a shared implementation change.
A new or changed Module's author sees only that Module's contract collection; code-writing work
receives the separately bound Implementation Specs. Other Module contracts are reviewed separately.
An atomic application checks source versions and preserves prior bytes if applying the proposed
structure fails. Human acceptance is explicit where the selected workflow requires it; direct
maintenance follows the developer's explicit task authorization.

### P9. Candidate and delivery evidence belong to a worktree

One candidate worktree holds one change, including its component progress, gaps and implementation
impact evidence. Partial work is inspectable and resumable, not represented as completed delivery.
Validation and review evidence bind to actual candidate inputs. Shared implementation changes
invalidate evidence for every using Module even if only one Module initiated the change.
Delivery preserves unrelated local changes, checks the actual integration and records incomplete
cleanup separately from a completed merge. No component independently delivers its enclosing change.

### P10. Explicit session handoffs

When the selected workflow requires a new outer session, start it in the intended worktree with
fresh context and that worktree's instructions. Changing cwd does not erase prior cognitive inputs.
Supply a self-contained prompt in the developer's language with the absolute directory, branch,
task, authorizations, completed and remaining work, artifacts, checks and next steps. Start the
session automatically when isolation can be established; otherwise provide a complete copyable
prompt. A direct maintenance task explicitly authorized by the developer does not require a
workflow handoff solely because it updates the Framework's own instructions.

## Part B: Concorde project application

The explicit registry is `.concorde/specs.json`; `module.concorde` is the project entry Module.
Concorde adopts Protocol 2.0.0 and registry schema 2. Every Module owns a self-contained English
Spec collection describing its features, interfaces and internal architecture. Implementation
Specs bind explicit files with one owner per file and may be reused by multiple Modules. Only
code-writing workers receive these Implementation Specs; other workers use their own complete
Module contracts. Shared implementation changes require fresh evidence for every using Module.
Runtime, distribution, self Specs and human publication evolve together. Legacy Profile 7 utilities
may inspect old fixtures deterministically but never supply cognitive inputs to a Profile 9 agent.

### Protocol version cutover and self-consistency

Concorde evolves its own normative Protocol as an explicitly authorized version cutover. The
currently published Protocol governs that published version and ordinary Concorde work, but it is
not the admission or validation authority for the incomplete intermediate state that replaces its
own rules. Requiring the previous Protocol to authorize every step of its replacement would make a
breaking correction depend on the behavior being replaced and can create a self-referential
deadlock.

A Protocol cutover MAY therefore complete the coordinated changes to principles, kind definitions,
schemas, runtime enforcement, Operations, installation assets, self Specs, publication, migration
behavior and executable evidence before running the replacement Protocol's validation. Intermediate
bytes MUST remain an unpublished development state: they MUST NOT be installed, bound by consumer
projects or represented as an adopted Protocol version.

The cutover is complete only when the proposed version is internally coherent, every distributed
and executable authority agrees on its version and meaning, Concorde's own maintained Specs satisfy
that version, and a separate consumer fixture validates the resulting behavior. Validation is then
performed under the completed proposed Protocol, not by treating the previous Protocol as authority
over the transition. This exception applies only to an explicitly authorized normative Concorde
Protocol cutover; it does not waive the active Protocol for ordinary feature work, consumer-project
changes or a partially scoped refactor.
