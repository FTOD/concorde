# Concorde Workflow Principles

Protocol 1.0.0. These principles apply to every Concorde project.

### P1. Business scope and implementation structure are separate dimensions

A project MUST distinguish Domain scopes from its Service/Module component structure.

| Concept | Meaning | Primary specification obligations |
|---|---|---|
| Domain | A scope within which a business or problem-space vocabulary, rules, and system behavior are explained. | Define significant entities, their relationships and responsibilities, interaction triggers, invariants, state transitions, completion, failure, and retry semantics where applicable. Explain how the system operates within this scope, including relevant features. |
| Service | A self-contained capability with a clearly specified interaction boundary. | Describe consumer-facing features and their usage, then define complete boundary contracts: entry points, configuration, runtime inputs, results, effects, errors, compatibility, and applicable retry/idempotency behavior. |
| Module | A cohesive implementation responsibility exposed through an explicit API. | Define provided and required APIs, including signatures, types, preconditions, results, state/effect obligations, and failure behavior. Function calls are valid interactions. |

A Service's boundary can use an executable, a file exchange, HTTP, or another explicitly defined
or versioned standard format. Deployment topology is a separate declared property. A Module's
Spec MUST describe its interface rather than its algorithms or private implementation.

Domain MUST NOT be treated as a third component kind in one universal Domain/Service/Module
containment tree. The model MUST distinguish at least:

- Domain scope nesting: one Domain narrows a broader Domain's problem space.
- Component composition: a Service or Module is composed using other Services or Modules.
- Scope participation: a Service or Module participates in a Domain with a stated role.
- Behavioral relationships: entities call, produce, consume, constrain, or otherwise interact
  using named relationships with explicit direction and meaning.

Scope nesting and structural containment MUST be acyclic. They MUST NOT determine each other's
parent relationships. Scope participation MAY overlap: a shared Service or Module can participate
in multiple Domains without acquiring duplicate component identities or implementations. Each
Domain explains the role relevant to its own scope. Participation does not automatically grant
context access or mutation authority.

Every Domain and Service that routes work toward another target MUST state that target's stable ID,
local responsibility, relationship and selection condition in its own Spec. This routing view does
not substitute for the downstream target's complete Spec. It lets a main coordinator decide where
work belongs without reading a Module Spec or relying on registry metadata as hidden business
authority.

For every direct component `participates_in` relationship in the registry, the corresponding Domain
collection MUST contain exactly one machine-readable `concorde-participants` entry with the
component's stable target ID and kind, its Domain-local responsibility, the condition for selecting
it, and the nonempty promises that Domain relies on. A broader Domain MAY repeat a participant from
a nested Domain when it needs that participant locally, but the repeated declaration does not grant
the participant's Spec or code. Deterministic validation MUST reject missing, duplicate, unknown,
kind-mismatched or unrelated declarations. Before Domain planning or task generation, context
solving MUST report a missing direct declaration as a concrete Domain Spec gap and an inconsistent
declaration as conflicting.

Business entities such as Account, Transfer, and Daily Limit MUST have meaningful definitions
and responsibility assignments where they matter. They do not each require a separate Domain,
Service, or Module Spec. A Domain is responsible for explaining, for example, who checks a Daily
Limit, when a Transfer is allowed, what completion means, and which failures permit retry.

### P2. Features and APIs describe the appropriate consumer view

A Service Spec MUST explain its consumer-facing features: what a consumer can accomplish, how
the Service is used, and the associated promises and failures. Its boundary schemas MUST make
those promises executable and unambiguous.

A Module Spec MUST describe its APIs directly. Concorde MUST NOT require authors to wrap each
Module API in an artificial Feature document. Interface signatures and usage examples in a Spec
are permitted contract content; they do not authorize reading implementation source.

A Domain Spec MUST emphasize operating principles and collaborations. It MAY describe features
observable within its scope, including behavior that spans multiple Services or Modules.

Features and APIs used for selection, traceability, or lifecycle work MUST have stable identities
independent of document paths. A Feature or API belongs to its providing Spec target. Neither its
identity nor its filename creates an independent permission boundary. Concorde MUST NOT require a
separate Feature file or one Feature per Markdown file.

### P3. Every resolved Spec context is a self-contained document closure

Every Domain, Service, and Module MUST have a stable Spec target identity and an explicitly
registered, nonempty collection of Markdown documents. A physical document MAY be referenced by
one target or shared by several targets. Each document MUST declare one globally unique stable
document ID, the exact nonempty set of referencing target IDs, and whether its content is
`main_visible`. The registry remains the deterministic resolution index and MUST contain the same
memberships. Directory traversal, links, scope/component relationships, and another referencing
entity's remaining documents MUST NOT implicitly add context.

The resolved context for one target is the ordered union of its registered documents. Documents
referenced only by that target appear under `Target Spec`; documents referenced by several targets
appear once under `Shared Specs`. This one-hop document inclusion is not recursive entity-context
expansion. The complete resolved context MUST explain the target without requiring an undisclosed
parent, ancestor, child, collaborator, or related entity Spec.

Project knowledge SHOULD avoid unnecessary duplication. Exact shared truth—such as a vocabulary,
schema, invariant, state transition or common completion rule—SHOULD have one canonical shared
document when several targets rely on it. Target-local perspective remains local: a consumer still
explains when and why it uses a capability and how it handles results and failures, while the
provider explains what it offers. Natural-language similarity alone does not prove that two
perspectives are duplicate.

A shared document has collective authority and no implicit unique owner. A single-target author MAY
read it but MUST NOT change it. Changing shared truth requires a coordinated topology application in
which every candidate referencing target receives a separate context and returns identical proposed
bytes. Document identity, membership and `main_visible` changes follow the same reviewed, atomic
path. Any shared change intentionally changes the context identity of every referencing target.

### P4. Global principles and kind definitions are versioned context

Concorde MUST distribute the global workflow principles and the definitions of Domain, Service,
and Module as versioned Protocol assets. Every installed project MUST bind to an explicit
compatible Protocol version. Initialization, updates, validation, and execution MUST agree on
that binding.

For a Spec target, Concorde MUST automatically include the global principles and the corresponding
kind definition in its context. These additions MUST be visible in the resolved context manifest.
Project-specific rules MAY supplement the global principles but MUST NOT weaken them. Business
facts needed to understand a target must remain available in its Target Spec plus Shared Specs;
an ancestor's or co-referencing entity's remaining Spec cannot become an implicit supplement.

Concorde's own business decomposition is an application of these rules. It MUST NOT become a
required Installation/Documentation/Workflow decomposition for other projects.

### P5. Each agent invocation has one explicit, reproducible context

Every bounded worker task MUST bind to one explicit Spec target and a concrete context snapshot
before execution. A Feature or API identifier MAY focus the task within that target, but MUST NOT
silently replace its complete document collection with partial retrieval results.

A main coordinator is a separate agent role with a different context contract. It starts from the
project entry Domain or Service and MAY request additional registered Domain or Service Specs as
needed to understand intent and select work. Its discovery context is an ordered, append-only set of
only the `main_visible` Target Spec and Shared Specs of admitted Domain/Service targets. Each expansion
produces a new context identity covering the exact visible membership and bytes. Sharing a visible
document with a Module does not admit the Module's remaining Spec. The coordinator MUST NOT directly
expand a Module target or read implementation code.
It MAY route work to a Module only when an admitted Domain or Service supplies the Module's stable
ID, responsibility and selection condition. Missing routing facts are a Spec gap in the admitted
Domain or Service that should supply them.

An Operation with one owning lifecycle or mutation result receives exactly one main route and keeps
the user's task and constraints unchanged. Cross-target mutation is routed to a Domain that
coordinates separately bound component work. The read-only `ask` action of `concorde-main` may route
several target readers and combine only their typed results.

The coordinator that selects a target and the worker that consumes that target's complete context
MUST be different fresh agent invocations. The trusted host resolves and transfers the worker
snapshot directly; raw target or Protocol bodies MUST NOT pass back through the coordinator or an
ambient public Skill. Typed worker results MAY become declared coordinator inputs for synthesis.

The context manifest MUST identify the target and kind, document order, Target Spec and Shared Specs,
each document's stable identity/reference set/main visibility and content digest,
Protocol and kind-definition versions, Operation instructions, task input, phase, and any admitted
stage artifacts or structured tool results. A context identity MUST cover membership as well as
content. A change to admitted inputs produces a new snapshot rather than silently changing the
meaning of an existing identity.

Task intent, immutable Spec inputs, and explicit execution evidence have distinct roles. Prior
conversation transcripts, free-form predecessor summaries, unrelated Spec excerpts, and arbitrary
tool output MUST NOT become undeclared input channels. Inputs and outputs generated during a stage
MUST follow declared artifact contracts and read/write boundaries.

The trusted host may use the project registry to resolve targets and permissions. That authority
does not grant an agent general access to the registry's other Spec bodies. Explicit shared-document
membership grants only that document, not another target's remaining collection. Cross-target work
MUST use separately bound invocations and explicit data contracts between them. Scope membership,
composition, hyperlinks, and a caller-supplied file path are not permission grants.

### P6. Insufficient information is a Spec gap, not permission to search

When the admitted context lacks information required to carry out a task, the agent MUST report
Spec incomplete for that task. It MUST identify the unresolved question or missing contract,
the step it blocks, the selected Spec target, and the context snapshot used for the judgment.
It MUST NOT infer missing obligations from another Spec or from implementation code.

Concorde MUST distinguish missing information from an outcome already determined by an explicit
rule, conflicting requirements, and a failed execution. A known prohibition does not establish a
Spec gap. An execution or model failure alone does not prove missing information.
A missing runtime value whose requirement and missing-value behavior are already specified is
an input/admission failure, rather than evidence that the Spec's semantics are incomplete.

A context-solving Operation MUST assess the task using its admitted collection. It MUST NOT
expand that collection to make the task appear answerable. A gap is resolved by supplying and
reconciling the missing information through an explicit Spec-authoring task, producing a new Spec
revision, and resolving a new context before the blocked task resumes. Cross-target contract
changes require the affected local views to be reconciled.

Structural validation MUST remain deterministic. A task-specific agent assessment can reveal a
semantic gap, but MUST NOT claim to prove completeness for all possible future tasks.

### P7. Execution enforces the agent's cognitive boundary

All Concorde agent entry points MUST execute through an Operation host that establishes and
enforces their context. This includes exploration, initialization, specification, planning,
implementation, validation, fast loops, and reflection work. A public Skill can initiate an
Operation; it MUST NOT bypass the host to perform the bounded task in an ambient conversation.

Only the implementation phase may expose authorized implementation source to an agent. Code
inspection, debugging, and code review therefore require an implementation invocation. Other
phases consume the declared Spec context and contracted task/evidence inputs. Reflection
investigation or initialization does not create an additional code-reading exception.

The host MUST enforce reads, writes, searches, commands, network access, and tool outputs against
the same task boundary. A context manifest is data; the execution grant is host-issued authority
bound to that data, the phase, and the invocation. Caller configuration and artifact references
MUST NOT supply replacement authority. Unsupported enforcement MUST prevent execution.

Deterministic tools MAY read separately authorized code to compile, test, or otherwise validate
it. Non-implementation agents may receive only the tool's declared validation result, bound to the
relevant checks and revisions. Raw logs, source snippets, and stack traces MUST NOT be injected
automatically. A tool with broader execution access MUST NOT expose an arbitrary read or command
proxy to the agent. When interpreting a failure requires code inspection, Concorde dispatches an
implementation task.

Agent executions MUST start in fresh, controlled contexts. Changing a target or leaving an
implementation phase MUST NOT reuse a conversation that has already seen now-excluded material.
Removing file permissions cannot remove prior cognitive inputs. The guarantee covers admitted
project information and tool access; it does not claim to erase a model's general prior knowledge.

Public context inspection MAY expose target identity, membership, versions and digests for audit,
but MUST NOT return the raw cognitive snapshot or document bodies to the ambient caller. The host
keeps complete snapshots private and supplies them only to the fresh invocation whose policy is
bound to that context.

### P8. System topology is main-designed and explicitly accepted

`concorde-main` is the single public entry for global questions and system-structure design; there
is no separate ask Operation. For a topology change, its internal coordinator MAY receive the exact
registry metadata and every global kind definition in addition to its append-only, main-visible
Domain/Service discovery collections. Registry metadata supplies current structure, not hidden
business meaning. The coordinator still MUST NOT directly expand a Module or receive implementation
source.

The coordinator produces a complete candidate registry, target-local Spec tasks, migration
constraints and observable acceptance conditions without writing project files. A maintainer MUST
explicitly accept that digest-bound design before any target author runs. The host then starts a
fresh target-local Spec author for every added or changed target and for every unchanged
Domain/Service whose routing view must change. A Module target's remaining collection is visible only
to its own worker; a main-visible shared truth is not such an expansion.
Worker document output remains host-private and MUST NOT return through main cognition.

Changing document reference membership requires a Spec task for every retained current or candidate
reference. A shared truth change requires every candidate reference to receive its own authoring
context; the host accepts the shared bytes only when all returned proposals are identical. No single
target author gains unilateral shared-document write authority.

The host validates the candidate registry and complete proposed document bytes against an overlay,
then stores one exact digest-bound application with before-digests. The public result exposes only
an artifact identity, path and digest. A maintainer MUST explicitly accept that exact application
before mutation. Application is atomic: stale registry, Protocol, discovery context, source bytes,
target gaps or invalid final structure prevent project writes; failed target authoring leaves the
project unchanged. The trusted host applies the accepted registry and documents together or restores
their previous bytes.

### P9. A candidate change belongs to one worktree and one delivery session

One linked Git worktree MUST own one top-level change, including all of its participating component
work. That mutable worktree is the candidate version. Partial Spec or implementation work MAY remain
there for inspection and recovery, but MUST have explicit host-owned phase, status, component progress
and gap provenance in `.concorde/worktree.json`. It MUST NOT be represented as the accepted primary
revision. Plans, tasks and check evidence belong to that worktree; new work MUST NOT create an
independent attempt lifecycle beneath it. A blocked component author does not require already authored
draft bytes to be discarded. Cross-component agreement is assessed after all affected authors finish
and before component implementation begins. Recovery resumes the recorded phase with current inputs.

The primary Git worktree is a location, independent of its branch's name. It MUST retain basic metadata
for every live linked worktree in `.concorde/worktrees.json`. Main cognition MUST receive the current
workspace identity, candidate status when applicable, and the live worktree inventory. These declared
lifecycle inputs MUST NOT grant access to another worktree's Specs, implementation or conversation.
Managed secondary AGENTS.md and CLAUDE.md guidance supplements the host-enforced context.

Creating a linked worktree from a primary mutation request is a handoff: a new agent MUST be opened in
that worktree before project work continues. Development loops MUST stop at a verified ready candidate.
Delivery MUST be requested in an agent whose initial working directory is the primary worktree.
A secondary session MUST NOT deliver, change cwd, redirect the host or forward an invocation to bypass
this requirement. Component completion never independently delivers the enclosing change.

The primary delivery host MUST bind validation to the exact candidate and actual integration result,
merge into the primary worktree's checked-out branch, then remove the temporary worktree and its local
state. Failed checks, conflicting merges or stale evidence preserve the candidate and the primary
revision. Local control files and managed worktree prompt blocks MUST NOT enter the delivered tree.
Delivery evidence survives in the primary worktree. A completed merge with unfinished cleanup MUST be
distinguishable and resumable without repeating the merge.
