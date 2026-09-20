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
the agent opens the granted files with its own tools, starting from the reading entry, and nothing
outside the grant is readable. Its
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
contain no implementation file contents. The outer agent reads and selects complete Module Specs
directly and answers questions within its own task grant. It chooses an explicit Module target for
each retained Operation, rather than asking a discovery worker to route or expand a task. Every
bounded worker is fresh and receives only its selected complete Module context. Additional outer
reading never becomes an implicit worker grant.

Assessors, planners and task authors use only the selected Module's complete
project-Spec collection and, for planners and task authors, its declared external references.
They MUST NOT read source code to supply missing Module meaning. Only the
code-writing phase receives the complete implementation context; code review receives its separately
declared read-only subset. Agent instructions, the Protocol rule bundle and Pi integration are not context:
instructions belong to a model-backed Operation's execution profile, and the Pi session tool exposes public
Operations for the developer's own agent runtime. Every worker's system prompt is its common worker
rules, then its own role instructions, then the Protocol rule bundle; the bundle's files are also
listed in the index with their digests and readable at their paths.

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
invocation within that authority belongs to the Harness Module's Specs, not to this profile. Task-authorized outer sessions may edit files, including `.concorde`, within their own workspace
and task grant; the directory name creates no blanket host-only prohibition. Truthful evidence,
concurrency safety and bounded worker phase permissions remain mandatory.

Operation is the Framework's only executable entity. Each Operation declares input State, output
State updates, effects, use conditions, execution policy and a permission ceiling. A caller can use
it as a LangGraph node without reconstructing its context policy, permission boundaries, model
execution or result checks. Completeness still relies on trusted Runtime, Host and Harness services;
the common Host/Harness narrow the declared ceiling to the actual task and enforce the grant.
State cannot carry or expand execution authority. Public/internal exposure changes entry availability,
not completeness. Modules own responsibilities and Specs, not necessarily one Operation each.

Every composed Operation's control flow is a LangGraph graph built with the Graph API: a
`StateGraph` whose nodes and edges are declared before it is compiled. The Functional API,
`entrypoint` and `task` from `langgraph.func`, MUST NOT be used, because it keeps control flow
inside ordinary Python where neither a Graph Spec nor Studio can inspect it; a deterministic check
refuses it. Every executable node is an Operation with declared input State and output State
updates. Its implementation may be deterministic code, a model invocation or a compiled subgraph;
these are not separate entity kinds. Composition produces another Operation. The outer agent
chooses which public Operations to invoke and in what order; no development or Spec-authoring
orchestrator is supplied. Operation composition uses one explicit USES relation, distinct from Module
ownership and the explicit references selecting context.
Model instructions, tools and limits are execution configuration, not a parallel Agent identity.
The same graphs are the inspectable Studio surface, and no operation runs control flow outside
them. State channels carry data, not execution authority; runtime context and permission checks
remain separate. Parent graphs define reducers for shared channels explicitly.

Agent instructions, the Pi session shim, schemas and rule assets are deterministic projections of authored
sources. Generated output is not edited as source. Builds distribute the Module kind definition and
the accepted Protocol binding. Configuration, installation and publication must agree on that
binding. Runtime Agent responsibility files are authored implementation assets, not another category
of project Spec.

### P8. Structure and file listings change together

Direct structural edits reconcile Module parentage, uses, document ownership, explicit references,
interface bindings and file listings as one consistent candidate. The task-authorized outer agent
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

The user-facing main session understands needs and coordinates. It may delegate complete tasks
to at most one layer of fresh task subagents; a task child may run a series of public Operations
and continue one change to delivery, but never delegates tasks or moves worktrees. Bounded
Operation workers are terminal Pi agents scheduled by the LangGraph host, not task subagents.
They cannot delegate, create subagents or recursively call Operations. Concorde neither inspects
nor computes cross-runtime current/maximum agent depth for these leaves; absent or legacy depth
variables do not govern launch. Outer task-subagent limits and all worker file/tool grants remain intact. An Operation in an assigned candidate reuses it instead of creating a nested one.
Ordinary consumer projects may use direct primary editing for simple authorized tasks.

Concorde source maintenance defaults to a new candidate and a fresh Concorde-catalog-free maintenance child.
The main stays in its initial worktree and does not use its own Concorde integration to govern that authoring.
Disable inherited/discovered Concorde catalogs for both maintenance and test children; never fork
old Concorde instructions. After the writer builds, checks and commits, it stops writing. The main starts a
separate fresh sibling test child in that same candidate with only explicitly selected candidate
Pi entry, embedded catalog, transitive implementation, build and runtime provenance. Missing, stale, unreadable or out-of-candidate selections
fail closed without name-based fallback. Selection is not proof of extension loading, tool use or model execution. The tester cannot rewrite its governing Pi integration. Failed
tests return to maintenance followed by another fresh tester. One writer owns a worktree at a time.
Maintenance may end through ordinary Git; it is not required to use Concorde delivery. Integration
requires explicit merge authorization and cleanup remains a separate action.

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
owner and direct-consumer evidence. The outer agent edits authored reading and metadata directly
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
`concorde.operations` records the single checked inventory, including State contracts, USES and
optional model execution profiles; its
behavioral explanations remain reading content and unknown extensions cannot override the Protocol.

Every Operation is explained in the Specs of the Module that owns its behavior: that Module's
reading says what the Operation is for, when to use it, what it takes and returns and when it
stops, and whether it runs as one node (deterministic code or one model-backed worker) or as a
Graph. Every executable Graph has one Graph Spec in its owning Module's implementation-role
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
