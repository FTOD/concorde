---
audience: shared
---

## Concorde Framework execution profile

This profile applies the independent Spec Protocol to Concorde's runtime. Framework configuration
uses `profile_version: 15` for the content/reading document-unit model and registry schema 5 for its JSON
storage. `.concorde/config.json` declares `profile_version`, `registry`, `protocol` and
`operation_configuration`. Its `protocol` binding identifies the accepted version and exact
manifest digest. These configuration and storage versions are Framework compatibility identifiers,
not additional versions of the specification language. Older configurations require explicit
migration; the runtime must not infer their meaning from paths or names.

### P5. One complete Module context per bounded task

A bounded invocation selects one Module and freezes four kinds of context. Its **Spec context** is
the Protocol's one-level union of complete owned document units and explicit Module references; scenario focus
does not trim it. Definitions in included documents retain their original owner. The Protocol
fixes which files are visible, not how they are delivered; this profile chooses the delivery. The
host delivers the Spec context as a **context index and grant**: the invocation's frozen record
lists both source members of every included unit with document identity, owner, source role, digest,
inclusion reasons and the reading entry; reading and metadata members themselves are granted read-only at their project-relative paths, copied
byte-for-byte into a capsule when the phase has no project workspace. No Spec document body is
embedded in an invocation's input, so an invocation pays only for the documents its task opens;
the agent opens the granted files with its own tools, starting from the reading entry, and must not read outside the grant. Native file scope is prompt policy, not OS confinement or proof
of exclusive reads. Actual isolated tester/check subprocess boundaries are separate. Its
**implementation context** is the Protocol-defined set of files bound by the Module's entities:
their exact entries plus every regular file below their directory prefixes, excluding directories
named `node_modules`, `__pycache__`, `.venv`, `build` or `dist`, directories and files whose names
start with a dot, and `.pyc` and `.log` files. Every phase may see the declared entries and the
resulting file names, because the entity declarations are part of the Spec context; only
code-writing and code-review phases receive file contents, in their declared subsets. Its
**resource context** is the set of admitted Operation and Tool contracts the invocation may use
together with the Module's Protocol-defined external references: the vendored documentation and
source of the libraries, services and tools it declares with `references` of kind `external`,
each identified by one tree digest. Every phase sees those entries; planning, task authoring,
code-writing and code-review phases receive their readable files read-only, copied into a capsule
when the phase has no project workspace, with media and archives excluded. No phase receives an
undeclared network or an installed dependency's sources in their place. Its **task context** is the
task, constraints, admitted stage artifacts and lifecycle metadata. Task context travels inline in
the invocation input: stage artifacts and, for a review, the typed changes to the reviewed Module's
own Spec documents or implementation files since the baseline revision. Those changes are derived
from files inside the phase's visible scope, add no file to it and replace no granted file. A
kind may be empty for a phase, but the frozen closure is never empty. Planner and task-author inputs
contain no implementation file contents. The calling session, the user session or its Task subagent, reads and selects complete Module Specs
directly and answers questions within its own task grant. It chooses an explicit Module target for
each retained Operation, rather than asking a discovery worker to route or expand a task. Every
bounded worker is fresh and receives only its selected complete Module context. Additional calling-session
reading never becomes an implicit worker grant.

Assessors, planners and task authors use only the selected Module's complete
project-Spec collection and, for planners and task authors, its declared external references.
They MUST NOT read source code to supply missing Module meaning. Only the
code-writing phase receives the complete implementation context; code review receives its separately
declared read-only subset. Agent instructions, the Protocol rule bundle and Pi integration are not context:
instructions belong to the canonical native Agent, and the Pi session tool exposes compatibility
capability entries for the developer's own agent runtime. All native Agents receive their terminal rules
and Agent specification, and
reads the complete Protocol documents listed with their digests in its frozen context index.

Context identities cover ownership, explicit references, inclusion reasons and document bytes,
Protocol and instructions, declared stage artifacts, declared listing entries and lifecycle
identity. Code-phase context identities additionally cover the bound file names and their current
digests; a code writer may create files below a listed directory without a prior pending
declaration. A changed input requires a new snapshot. Implementation-only changes do not add
implementation knowledge to a planner.

### P6. Gaps and review are tied to the affected contract

Missing required behavior is a Module Spec gap. Name the missing promise, blocked step, Module and
snapshot; continue only independent work. Implementation source cannot resolve that gap implicitly.
A failed execution, an explicit prohibition and a missing runtime value with defined failure
behavior are distinct from an unspecified contract.

Spec review uses complete Module specifications, including both document roles. Code review uses the same Module contracts and authorized code in a
fresh read-only invocation. A review records its exact inputs, coverage, findings and completion.
Changed relevant inputs invalidate it. Skipped, failed, incomplete and successful reviews remain
distinct. A changed canonical Spec document requires review for its owner and every Module whose
resolved context includes it, including Module-reference consumers. Reference and ownership changes
also invalidate their snapshots, plans and reviews. A change to a file listed by several Modules
requires checks for all listing Modules, with separate Module contexts and explicit per-consumer
evidence. Deterministic validation also reads the scenario declarations of the listed tests
and reports every scenario that no test declares, unless its Module binds no implementation file at
all; that coverage is evidence about the tests, never a change to the contract. No passing structural check proves semantic completeness.

### P7. Execution authority is explicit

The host binds each normal Framework invocation to declared context and file permissions. Only
code-writing invocations receive file contents with write authority, and only for the files the
selected Module lists; they never change Spec documents, entity declarations or the registry. Code
review and deterministic checks have separately declared read authority. The registry's reverse
index never grants a writer another Module's Spec or unrelated code. How the host keeps an
invocation within that authority belongs to the Harness Module's Specs, not to this profile. Task-authorized sessions, the user session and its Task subagents, may edit files, including `.concorde`, within their own workspace
and task grant; the directory name creates no blanket host-only prohibition. Truthful evidence,
concurrency safety and bounded worker phase permissions remain mandatory.

An **Agent** is a callable native Pi agent with one canonical Concorde definition, either a Domain Agent or a Task subagent. A **Workflow** is an authored native pi-subagents
composition. An **Operation** is an explicitly selected LangGraph StateGraph flow. Finite non-model
actions are **Host tools/services**. Module ownership, context references and composition remain
independent of these executable kinds. Compatibility `concorde-*` names, `operation_id` fields and
the `operations/` package name do not make every capability a LangGraph Operation.

Context assessment, tasks and implementation use direct native Agents. Plan, independent review
scopes and bounded Issue solving use authored native workflows. Deterministic admission, configured
checks, lifecycle, Issue bookkeeping/disposition and validation remain Host services. No public
native path compiles a mandatory Graph or launches a hidden old Pi-RPC worker. All seven native
Domain Agents are terminal, fresh and explicitly scoped, without recursive task delegation or an extra
coordinating model. Native capacity and tool ceilings remain authoritative.

Model proposals and successful stage-only gates are not domain completion. Host acceptance follows
independent native terminal-artifact correlation and exact current-input/business checks. Expected
implementation edits do not invalidate immutable contract/task identity; failed/cancelled work keeps
partial edits and historical receipts. Native file/network/credential exclusions are prompt-level
policy, not OS confinement or proof of exclusive reads. Actual tester/check subprocess isolation
remains enforced and distinct. Primary status/runs, single-writer lifecycle and explicit integration/
cleanup authorization remain unchanged.

LangGraph stays available for genuine explicitly selected StateGraph Operations and Studio inspection.
`OperationNode` supplies a typed State transition with a trusted native launch/admission service in
Runtime; missing service refuses rather than selecting a model backend. State cannot carry or expand
authority. Parent graphs own reducers and mapping. No fake Graph mirror represents native workflows.
The Graph API is used, never hidden `langgraph.func` task/entrypoint scheduling. Installed LangGraph
health remains verified; optional execution is not permission to delete untested dependencies.

Agent instructions, the Pi session shim, schemas and rule assets are deterministic projections of authored
sources. Generated output is not edited as source. Builds distribute the Module kind definition and
the accepted Protocol binding. Configuration, installation and publication must agree on that
binding. Runtime Agent responsibility files are authored implementation assets, not another category
of project Spec.

### P8. Structure and file listings change together

Direct structural edits reconcile Module parentage, uses, document ownership, explicit references,
interface bindings and file listings as one consistent candidate. The task-authorized calling session
edits the reading, paired metadata and registry directly. A Module's entity entry union equals its
registry `files`, entry for entry, marking absent intended entries pending. Within one Module the
most specific entry owns a file, and a listed directory never contains a registered Spec document.
The reverse index identifies every listing Module before a shared file changes.

Ownership is independent of the editing session: a shared contract is defined once by its owner,
not copied into consumers. Reconcile both members, old and candidate affected contexts, links and
participant versions together. Validate the combined candidate before dependent work; do not claim
a partially edited model is admitted. Fresh reviews use separate complete owner/consumer contexts.
Code-writing workers retain their own listed implementation grant and never edit either Spec member
or the registry. Direct edits confer no successful assessment, review, check or completion evidence;
selected retained Operations re-admit actual current inputs without requiring deleted workflow history.

### P9. Task status and evidence have one primary authority

One stable task/change ID owns a change; branch and path are mutable locators, not identity.
Only the primary worktree keeps authoritative local `.concorde/status/` records and durable
`.concorde/runs/` evidence, including candidate executions. A status records mode, goal, base,
candidate, child ownership, phase, blockers and run references. Delivery and ordinary-Git manual
merge are distinct outcomes; cleanup is separate and terminal records survive candidate deletion.
Direct primary tasks need no secondary worktree. These local ignored records are not project
configuration and are never merged between branches. Host persistence uses repository locking and
atomic writes without granting a child access to primary source or index. Missing primary authority
blocks persistence until recovery; it never creates a candidate-local replacement archive.

Evidence binds actual source worktree, branch, commit, dirty input identity and runtime/build/Pi integration
provenance when known. A catalog is not execution evidence. Shared-file and shared-Spec edits
invalidate all affected consumers' evidence. Delivery verifies actual integration, preserves
unrelated changes and confirms pending entries only when they exist. Completed integration with
cleanup pending is not an integration failure. Legacy worktrees, deliveries and candidate-local
runs require explicit collision-checked migration, preserving history and retrying interruption;
old readiness never becomes fresh validation implicitly.

### P10. Fresh task sessions, never session moves

The user session understands needs and coordinates. It may delegate complete tasks
to at most one layer of fresh Task subagents; a Task subagent may run a series of public Operations
and continue one change to delivery, but never delegates tasks or moves worktrees. Bounded
native Domain Agents are terminal pi-subagents agents, distinct from author/tester task delegation.
Every native terminal Domain Agent is a fresh Pi leaf with no delegation tools; its Host-issued
preparation and independent acceptance remain separate from the native model execution. Native
Pi child-safety ceilings apply; insufficient native launch capacity refuses rather than bypassing
a ceiling.
They cannot delegate, create subagents or recursively call Operations. Concorde neither inspects
nor computes cross-runtime current/maximum agent depth for these leaves; absent or legacy depth
variables do not govern launch. Task subagent limits and all worker file/tool grants remain intact. An Operation in an assigned candidate reuses it instead of creating a nested one.
Ordinary consumer projects may use direct primary editing for simple authorized tasks.

The user session decides task scope, worktree ownership, author continuation, checks, independent testing and
integration authorization. One writer owns a worktree at a time and stops writing before testing.
The user session owns lightweight high-level decomposition into work packages, dependencies, file/contract
ownership, independent worktrees, native workflow steps and component/integration/testing gates.
This is not product Concorde plan/tasks and requires no mandatory planner Operation or coordinator
LLM. The user session may author profiles, prompts, tools, workflows and process repairs within task authority
and its own exclusive tree. Native workflow steps remain terminal Pi workers with no child task
delegation. Frozen launches do not adopt edited governance or wider grants retroactively.
Reuse the author within an unfinished coherent stage and feedback cycle. Ordinary milestones do
not require a new session; a completed stage with changed goals/context may use a fresh author
after durable handoff, observed stop, exact ownership release and binding of the actual new child.
Parallel component work stays in separate trees; combined-input integration is a distinct gate. The user session chooses none, targeted or full
independent testing with an explicit scope and reason; an author's self-tests are not independent.
When selected, the project-discovered `tester` is a fresh sibling Task subagent, not a LangGraph node.
It receives only explicitly selected local Pi integration/runtime provenance and its actual grant.
Missing or stale assets block without a primary/global fallback. Selection metadata is not proof
of extension loading, tool use or model execution. Tester keeps governing artifacts read-only,
uses scoped external fixtures, returns failures rather than repairing, and cannot delegate tasks.
Its command tool enforces the OS read-only check boundary rather than unrestricted shell access.
The user session's pi-subagents is a host prerequisite, never a terminal-worker dependency. Passive observation
adds no tools, catalogs, authority or network telemetry. The user session owns durable primary persistence.

Changed relevant inputs/environment invalidate corresponding check evidence; stage reports and
same-tree commits alone do not demand repeated full suites. State the reason for same-input reruns.
Already fully read unchanged complete Specs in valid same-session context need no bundle reread;
new ownership seams and fresh readers retain complete-context obligations. Resource handoffs state
observed capacity, current input including cache, reserve and compaction status or an actual error.
Unknown metrics stay unknown. Cumulative usage, document size and absence of a compact tool do not
establish exhaustion. The user session verifies the need after supported compaction with an observed completion or error; a checkpoint
or a message saying compact is not compaction. After success inject the CURRENT concise task brief
once: goal/grant, accepted decisions, evidence and next step, not obsolete launch instructions.
Host-observed lifecycle/activity/context/compaction stays distinct from worker-reported stage,
objective, completed artifacts, checks/failures, blocker and next action/evidence. Native supervisor,
events/status and primary authority carry meaningful updates without polling, repetitive reports,
fake percentages or activity-as-correctness claims. Quality concerns are labelled separately. Integration requires explicit authorization; cleanup remains separate.

Concorde's source repository adds its own source-only maintenance/coordinator prompts and validation
policy. They are not installed as consumer testing instructions.

### Framework authoring and publication conventions

Every Concorde Module's `module.md` starts with Purpose, Terminology, Usage, Design and Relationships as
level-2 headings. The entry and explanatory topic companions have `document.role: module` and
contain no formal requirement/scenario definitions or canonical structured contracts. Those belong
in directly Module-owned implementation-role companions. Both roles remain complete Spec reading,
not separate ownership or context scopes. Companion topics do not repeat a mandatory entry template.
Each Markdown source has one schema-2 `.md.json` companion with explicit document identity, owner,
role, and entity, dependency and participant declarations. Mechanical fields
stay there; readable responsibilities, conditions, guarantees and obligations have local anchors
referenced by metadata. Group adjacent anchors on one line when a coherent explanation covers
several entities. Do not replace the retired JSON inventory with another giant human inventory.

Both source members are indexed, granted whole and byte-bound. A metadata-only change invalidates
owner and direct-consumer evidence. The task-authorized calling session edits authored reading and metadata directly
within its task authorization, reconciling the registry and topology as needed. Validate the complete
combined candidate, not isolated files. Preserve stable identity and unique ownership through
relocation and structural change. No private author result or topology application artifact is
required. Bounded code writers never edit either member.

A requirement is one Module-wide SHALL statement with a stable heading ID. A scenario has ordered
GIVEN/WHEN/THEN steps and its own situational guarantees, not attached requirements. Internal
constraints remain normative; link rather than duplicate obligations. The Relationships view uses
English labels, accTitle and accDescr, a nonempty subset of local entity titles and labeled edges.
Explain its scope; inventory coverage is not a readability requirement or proof of completeness.
Files are bound in entity metadata, using owned package directory prefixes and exact shared files;
the registry listing remains their exact union. Project-owned metadata extensions
`concorde.operations` records the checked compatibility capability-adapter inventory, including
State contracts and USES; `concorde.agents` separately records the Agents-owned nine-Agent inventory,
including family, distribution scope, registration and canonical instruction source. Their
behavioral explanations remain reading content and unknown extensions cannot override the Protocol.

Every Operation is explained in the Specs of the Module that owns its behavior: that Module's
reading says what the Operation is for, when to use it, what it takes and returns and when it
stops, and its actual StateGraph composition. Public compatibility capability adapters do not
become Operations merely because their wire names contain operation. Every executable Graph has one Graph Spec in its owning Module's implementation-role
documents, not its explanation-first topics. Module-role reading explains the conceptual sequence
and its reasons, with clearly labeled conceptual diagrams when useful, and links to this exact
Graph Spec. The Graph Spec is written with LangGraph's concepts as three parts in order, each
opening a paragraph with its bold label: **State.** (the channels, their reducers and the records
the nodes read and write), **Nodes.** (a table of node name, what executes, `in` and `out` state)
and **Edges.** (how the next node is chosen, by a conditional edge reading a named State channel or
by a `Command` the node returns, and where stops and errors lead). A Mermaid flowchart follows,
bound to the compiled Graph by `%% graph: <name>`, whose node identifiers are the compiled node
names including `__start__` and `__end__`, whose node labels state `in:` and `out:` as the Nodes
table does, and whose edges carry their routing condition as a label exactly when the source node
has several successors. The configured Graph Spec check keeps every Graph Spec's parts, Nodes table
and diagram equal to its compiled Graph and requires its owner's module-role reading to link to its
heading anchor. Publication shows Operations and Graph Specs only inside their owners' Specs; no
separate Operation or Graph page repeats them.

A Python test declares the scenarios it verifies with the `verifies` decorator from
`concorde.spec.verification`, for example `@verifies("scenario.harness.context-freeze")` on the test
function or method. A TypeScript test declares them with an own-line `// verifies:` comment above
the test, for example `// verifies: scenario.views.publish-candidate` above its `it` call; several
IDs are separated by commas or spaces, and the following `it`, `test` or `describe` title names the
declaring test. A test may name several scenarios in either language, and the declaration is read by
parsing, never by compiling or running the test. A Module whose entities bind no implementation file
has no test to declare its scenarios, and its scenarios are not reported as uncovered. No Spec
document lists tests. Links inside Specs address definitions by ID
(`scenarios.md#scenario.harness.context-freeze`, `requirements.md#req.harness.permission-no-widen`); publication
turns every scenario, requirement, entity and canonical contract ID into an anchor. Rendered views
and navigation are derived and create no ownership or context inclusion. Links to canonical shared
definitions remain links in rendered pages, never transclusions; the site exposes owner and
reference provenance. These conventions implement the Protocol's requirements for this project; they
are not requirements on every Protocol implementation.
