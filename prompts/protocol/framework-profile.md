---
audience: shared
---

## Concorde Framework execution profile

The following rules specify how Concorde Framework applies the Concorde Spec Protocol during agent work.
They describe the software's routing, execution, verification and delivery behavior, rather than
adding implementation artifacts to the Domain/Service/Module modeling categories. P5–P10 retain
their stable identifiers for existing references and handoffs.

### Runtime rule distribution and publication

Concorde Framework MUST distribute this Concorde Spec Protocol, its Domain/Service/Module definitions,
and its Framework execution profile as identifiable, versioned rule assets. Every installed project MUST bind to an explicit
compatible Protocol version. Initialization, updates, validation, and execution MUST agree on
that binding.

For a Spec target, Concorde MUST automatically include the global principles and the corresponding
kind definition in its context. These additions MUST be visible in the resolved context manifest.
Project-specific rules MAY supplement the global principles but MUST NOT weaken them. Business
facts needed to understand a target must remain available in its Target Spec plus Shared Specs;
an ancestor's or co-referencing entity's remaining Spec cannot become an implicit supplement.

Outer user sessions MUST receive a project-root Protocol entry through the selected installed
integration: Codex `AGENTS.md` explicitly directs reading these principles; Claude `CLAUDE.md`
imports them. The installed rule bundle is the source for Concorde Spec Protocol and Framework execution requirements,
not repeated Skill prose. Installing
new assets MUST NOT silently accept a new project binding. This entry is workflow guidance for the
outer session; it does not admit project Specs or change host-enforced execution permissions.
Internal controlled agents MUST continue to receive Protocol through their bound context with
ambient repository-instruction discovery disabled. They MUST NOT load the root entry instead.

Concorde Framework renders each Domain's declared System overview with Archify's System overview
recipe, validates its source and rendered artifact, and embeds it on the ontology.md main page.
Selecting a Domain in the docsite MUST open that main Spec, independent of document order. The
Framework MUST preserve other generated runtime assets when rebuilding diagrams. Architecture
validation and visual review are distinct; generated views never become agent context authority.
Registered diagram sources accompany their owning target's Spec as explicitly admitted artifacts,
and their identities and bytes participate in context freshness, authoring and review evidence.

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

A capability with one owning lifecycle or mutation result receives exactly one main route and keeps
the user's task and constraints unchanged. Cross-target mutation is routed to a Domain that
coordinates separately bound component work. The read-only `ask` action of `concorde-main` may route
several target readers and combine only their typed results.

The coordinator that selects a target and the worker that consumes that target's complete context
MUST be different fresh agent invocations. The trusted host resolves and transfers the worker
snapshot directly; raw target bodies and private context snapshots MUST NOT pass back through the
coordinator or an ambient public Skill. The global rule entry specified in Runtime rule distribution and publication is public workflow
guidance, not a return channel for a worker snapshot. Typed worker results MAY become declared coordinator inputs for synthesis.

The context manifest MUST identify the target and kind, document order, Target Spec and Shared Specs,
each document's stable identity/reference set/main visibility and content digest,
Protocol and kind-definition versions, rendered role instructions, task input, phase, and any admitted
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
This rule applies during explanation, planning, task decomposition and implementation, not only
context solving. The agent MUST pause steps or judgments that depend on a necessary missing or
ambiguous contract; it MAY continue independent work and MUST NOT silently invent the contract by
convention. Pure queries return gaps without authoring project files. Development flows persist
target/task/phase provenance and unresolved gaps in their existing change state. Unrelated progress
MUST NOT erase them. A fresh successful assessment of the affected step may resolve its gaps while
retaining history; durable issues can be explicitly promoted into the existing Reflection workflow.

Concorde MUST distinguish missing information from an outcome already determined by an explicit
rule, conflicting requirements, and a failed execution. A known prohibition does not establish a
Spec gap. An execution or model failure alone does not prove missing information.
A missing runtime value whose requirement and missing-value behavior are already specified is
an input/admission failure, rather than evidence that the Spec's semantics are incomplete.

A context-solving capability MUST assess the task using its admitted collection. It MUST NOT
expand that collection to make the task appear answerable. A gap is resolved by supplying and
reconciling the missing information through an explicit Spec-authoring task, producing a new Spec
revision, and resolving a new context before the blocked task resumes. Cross-target contract
changes require the affected local views to be reconciled.

Structural validation MUST remain deterministic. A task-specific agent assessment can reveal a
semantic gap, but MUST NOT claim to prove completeness for all possible future tasks.

Independent review has two modes, each in a different fresh session with no project write
authority. Spec review uses the complete admitted Target Spec and Shared Specs, task and scoped
Spec changes to assess representative tasks, necessary public APIs, collaborator promises,
behavior and errors. It MUST NOT inspect code or complete the collection with ungranted Specs.
Code review uses that same target's admitted contracts and registered implementation files, with
scoped code changes, to identify concrete behavioral defects. Blocking Spec findings MUST state
the missing promise, affected judgment, owning target/document and a structured gap. General
suggestions remain nonblocking findings. Reviewers MUST NOT modify source, Spec or tests.

The host binds every review to its actual input version and records task coverage, findings, gaps
and completion. Changed relevant Spec, code or review inputs invalidate prior conclusions. Failed
or incomplete review, not-run/skipped review and a completed review with no findings MUST remain
distinct. The standard development loop requires Spec review after authoring and before dependent
planning, and code review after implementation/checks and before ready. A fast loop MAY disable
review but MUST record the skip; it cannot downgrade an already required review. Required review
failure blocks advancement. Cross-target changes use separately scoped fresh reviewers and only
their authorized typed results for aggregation. Review does not create a second ready/delivery
lifecycle and does not prove that all future tasks are possible.

### P7. Execution enforces the agent's cognitive boundary

All Concorde agent entry points MUST execute through a capability host that establishes and
enforces their context. This includes exploration, initialization, specification, planning,
implementation, validation, development loops, and reflection work. A Skill can initiate a
capability; it MUST NOT bypass the host to perform the bounded task in an ambient conversation.

The implementation phase may expose authorized implementation source to an agent. The dedicated
code-review phase has the same target implementation visibility with all write authority removed;
it is a read-only implementation role, not a grant to other non-implementation agents. Code
inspection and debugging otherwise require an implementation invocation. Spec review and other
phases consume only their declared Spec context and contracted inputs. Reflection investigation
or initialization does not create an additional code-reading exception.

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

Agent executions MUST start in fresh, controlled contexts. Changing target or review mode, or leaving
implementation/code-review cognition, MUST NOT reuse a conversation that has already seen now-excluded material.
Removing file permissions cannot remove prior cognitive inputs. The guarantee covers admitted
project information and tool access; it does not claim to erase a model's general prior knowledge.

Public context inspection MAY expose target identity, membership, versions and digests for audit,
but MUST NOT return the raw cognitive snapshot or document bodies to the ambient caller. The host
keeps complete snapshots private and supplies them only to the fresh invocation whose policy is
bound to that context.

Capabilities fall into three classes, distinguished by who selects the context. A global capability
receives only the user's intent, at most with routing hints, and lets the host's coordinator
discover main-visible Specs and select the owning target; it may span several targets and stages. A
lifecycle capability is deterministic host behavior with no agent cognition and no context
selection. Every other capability is a stage: it receives an already bound target and one frozen
snapshot, runs one role, never reselects or expands its context, and is composed only in-process by
a capability that declares it. Capabilities expose an executable boundary only through Skills,
and each Skill exposes
exactly one global or lifecycle capability. Stage capabilities MUST NOT be projected as Skills and
have no direct invocation. Context selection therefore happens only inside global capabilities.

Role and Skill instructions are rendered from versioned prompt sources by a deterministic build. A
rendered instruction is a projection: it is never an authoring source, its exact bytes enter the
context identity of every invocation that uses it, and the host MUST refuse to run on a build whose
sources have changed since it was rendered. Spec documents are never assembled from prompts; shared
Spec truth uses registry-declared Shared Specs.

### P8. System topology is main-designed and explicitly accepted

`concorde-main` is the single public entry for global questions and system-structure design; there
is no separate ask capability. For a topology change, its internal coordinator MAY receive the exact
registry metadata and every global kind definition in addition to its append-only, main-visible
Domain/Service discovery collections. Registry metadata supplies current structure, not hidden
business meaning. The coordinator still MUST NOT directly expand a Module or receive implementation
source.

The coordinator produces a complete candidate registry, target-local Spec tasks, migration
constraints and observable acceptance conditions without writing project files. A developer MUST
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
an artifact identity, path and digest. A developer MUST explicitly accept that exact application
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
Delivery MUST be requested in an agent whose initial working directory is either the selected source
worktree or the destination primary worktree. The host MUST reject unrelated third-worktree and
nested delivery sessions; changing cwd or forwarding cannot grant participant membership. Component
completion never independently delivers the enclosing change.

The delivery host MUST bind validation to the exact candidate and actual integration result and
merge into the primary worktree's checked-out branch. It MUST retain the source when requested or
when the source owns the active session; otherwise it removes the temporary worktree and local state.
Failed checks, conflicting merges or stale evidence preserve the candidate and the primary
revision. Local control files and managed worktree prompt blocks MUST NOT enter the delivered tree.
Delivery evidence survives in the primary worktree. A completed merge with unfinished cleanup MUST be
distinguishable and resumable without repeating the merge.


### P10. Copyable agent handoffs

Whenever a Concorde workflow asks the user to open, reopen, or switch to another agent session,
include a self-contained prompt in a fenced text block that the user can copy directly into that
agent. This applies to every such handoff, including worktree changes, primary-worktree delivery
when a new session is actually required, and same-worktree maintenance recovery. Write the prompt
in the user's language and include:

- The intended initial working directory as an absolute path and the branch, when known.
- The original task, accepted scope, and user constraints or authorizations needed to continue.
- What is complete, what remains, and which checks have or have not passed.
- Exact paths to any saved patch or handoff artifacts, whether changes are already applied, and
  whether any artifact is stored in a temporary location.
- The next concrete steps, starting with this worktree's policy and affinity verification where
  applicable; include patch review/application when needed and the expected completion criteria.

Do not make the user reconstruct the task from earlier messages, supply known paths themselves,
or ask a second time for a handoff prompt. State unknown information explicitly rather than
inventing it. Preparing the prompt does not authorize entering or modifying the target worktree
from the old session; the existing worktree and maintenance boundaries still apply.

The runtime supplies facts it knows, including the actual worktree path, branch and change ID when
available, through existing result/error channels. The outer session completes the original task,
accepted scope, progress, checks and artifact details from its conversation before presenting the
localized prompt. A runtime draft with unknown fields does not excuse omitting facts the session
knows. Handoff text is for the new outer user session, not an input channel into controlled workers;
those workers still require fresh host-bound contexts and declared artifact contracts (P5–P7).
This clause does not create new handoff triggers, confirmations or authority. In particular, P9
allows a delivery request from either participating worktree's initial session.
