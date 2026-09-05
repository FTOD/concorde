> Adopted in the Profile 8 refactor. The shipped Protocol, explicit registry and runtime are the active implementation of this approved proposal.

# Domain scopes, component contracts, and explicit Spec contexts

Status: proposed global Concorde Protocol amendment. This document records the design for
review; it does not activate a new Source Profile or claim that the current runtime enforces
these rules. The adoption target is every Concorde project, including Concorde itself.

Reviewed base: `e48f8aaaf201ab42a7058f5e5373529b6591e5f4`.

The maintainer clarified two central decisions:

- Domain is a business/problem scope. Domain and Service/Module describe different dimensions.
  Service features, Module APIs, and Domain operating principles need distinct specification views.
- The restriction on reading implementation code applies to an agent's cognitive inputs.
  Deterministic tools may read authorized code to execute checks without exposing that code to
  an agent in another phase.

The proposed MUST/MUST NOT clauses below are global workflow principles. Concorde-specific
decomposition and migration notes follow separately.

## Proposed global principles

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

### P3. Every Spec is a self-contained document collection

Every Domain, Service, and Module MUST have a stable Spec target identity and an explicitly
registered, nonempty collection of Markdown documents. Their filenames and division into
documents are unconstrained by the Protocol. Membership MUST be explicit; directory traversal,
links, and scope or component relationships MUST NOT implicitly add documents.

The complete collection MUST explain that target without requiring its parent, ancestors,
children, collaborating components, or other Domains' Specs. This obligation applies to each
target's stated responsibilities and supported uses. A Domain's completeness is about the system
within its scope; it does not require enumerating every participating component's private details.

Necessary overlap between Specs is permitted and expected. If A uses B:

- A explains when and why it uses B, the contract it requires, the data it sends, and how it
  handles B's results and failures.
- B explains how callers may use it and the obligations and behavior it provides.

Each side MUST contain the information needed from its own perspective. A link to the other side
cannot substitute for that information. Shared contract identities and versions support
compatibility checks on common facts and obligations; the two descriptions need not use identical
wording. Structured checks establish the compatibility they actually cover, while semantic review
must report its evidence and limitations.

A parent's explanation of organization and a child's explanation of its own behavior MAY repeat
facts. Relationship references support navigation and consistency checking without becoming
context inheritance. A named external standard does not grant permission to fetch its contents;
task-relevant usage rules must be available in the admitted Spec context.

### P4. Global principles and kind definitions are versioned context

Concorde MUST distribute the global workflow principles and the definitions of Domain, Service,
and Module as versioned Protocol assets. Every installed project MUST bind to an explicit
compatible Protocol version. Initialization, updates, validation, and execution MUST agree on
that binding.

For a Spec target, Concorde MUST automatically include the global principles and the corresponding
kind definition in its context. These additions MUST be visible in the resolved context manifest.
Project-specific rules MAY supplement the global principles but MUST NOT weaken them. Business
facts needed to understand a target must remain available in that target's own document collection;
an ancestor's Spec cannot become an implicit global supplement.

Concorde's own business decomposition is an application of these rules. It MUST NOT become a
required Installation/Documentation/Workflow decomposition for other projects.

### P5. Each agent invocation has one explicit, reproducible context

Every agent task MUST bind to one explicit Spec target and a concrete context snapshot before
execution. A Feature or API identifier MAY focus the task within that target, but MUST NOT silently
replace its complete document collection with partial retrieval results.

The context manifest MUST identify the target and kind, document membership and content digests,
Protocol and kind-definition versions, Operation instructions, task input, phase, and any admitted
stage artifacts or structured tool results. A context identity MUST cover membership as well as
content. A change to admitted inputs produces a new snapshot rather than silently changing the
meaning of an existing identity.

Task intent, immutable Spec inputs, and explicit execution evidence have distinct roles. Prior
conversation transcripts, free-form predecessor summaries, unrelated Spec excerpts, and arbitrary
tool output MUST NOT become undeclared input channels. Inputs and outputs generated during a stage
MUST follow declared artifact contracts and read/write boundaries.

The trusted host may use the project registry to resolve targets and permissions. That authority
does not grant an agent general access to the registry's other Spec bodies. Cross-target work
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

## Context Operations and lifecycle consequences

The following Operation names and split are proposed implementation choices:

| Operation | Responsibility | Contracted outcome |
|---|---|---|
| `concorde-resolve-context` | Deterministically resolve a Spec target, validate explicit membership and versions, and materialize a context snapshot. | A typed snapshot manifest or a typed resolution rejection; never a best-effort partial context. |
| `concorde-context-solve` | Assess the supplied task against that snapshot and identify specific missing information. | A task-specific assessment, with structured gaps when applicable; never an expanded retrieval set. |

An Operation remains a stable callable definition with an associated Skill and at least one
executable Python script, with one designated primary entry point. Configuration, typed runtime
input, typed result, and host-derived execution context remain separate. Deterministic Operations
need not invoke an LLM or artificially compose two Skills. Composite Operations declare their
children, mappings, and gates explicitly.

Lifecycle selection should bind an owning Spec target and an optional Feature/API focus rather
than depend on `feature_path`. A change/invocation identity remains distinct from the durable
Feature or API identity. The exact attempt migration and new wire schemas belong to the coordinated
runtime change; this proposal does not silently retire existing Feature identities.

## Applying the model to Concorde

Concorde's initial Domain scopes should explain the following business spaces:

| Domain scope | Operating concepts and behavior |
|---|---|
| Installation | Packages, installed instances, configuration, upgrades, and installation receipts. |
| Documentation | Spec publication, navigation, diagrams, builds, and publication outcomes. |
| Concorde Workflow | Spec targets, contexts, Operations, changes, validation, and Reflections. |

Services and Modules are described in a separate component model. For example, a validation
Service can participate in Workflow and Documentation; its parsing or contract-checking Modules
belong to the component structure. Each participating Domain explains the validation role relevant
to its scope. The Service's own Spec contains its complete features and boundary promises; its
Module Specs contain their complete APIs. None implicitly loads the others.

The current Understanding, Lifecycle, Reflections, Capabilities, Distribution, and Auto-Docs
partition must be reconsidered using these two dimensions. Existing code locations may remain
where useful. Domain participation and component identity must not be inferred from directories.

## Adoption and evidence

Adoption requires one reconciled change to global principles, distributed kind definitions, source
registry/model, initialization and migration, context Operations, lifecycle inputs, execution
policies, Skills and projections, documentation publication, and executable evidence. Until that
change is complete, this proposal is not an active replacement for the existing Protocol.

Acceptance must include a separate consumer project as well as Concorde itself. Evidence must cover:

- Nested scopes and component composition represented independently, including one component's
  explicit participation in multiple scopes.
- Arbitrarily named Markdown collections, Service and Domain features, and direct Module APIs.
- Each target remaining understandable without ancestors, collaborators, or implementation;
  repeated contract views checked for the compatibility they actually claim.
- Exact context membership, version and digest handling, and rejection of undeclared retrieval.
- A missing rule producing a specific Spec gap while a known prohibition remains distinguishable.
- Spec-only planning and verification-agent inputs, with code visible only in implementation.
- Deterministic checks executing against authorized code while exposing bounded results.
- No bypass through public Skills, child invocations, raw tool output, or reused conversations.
- Concorde's installed workflow consuming the same Protocol assets and rules as the consumer
  fixture, with real enforcement evidence distinguished from model-process test doubles.
