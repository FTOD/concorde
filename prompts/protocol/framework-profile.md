---
audience: shared
---

## Concorde Framework execution profile

This profile applies the Spec Protocol to Concorde's runtime. `.concorde/config.json` declares the
Framework `profile_version`, the path of the project `registry`, the accepted `protocol` binding
(version and exact manifest digest), `operation_configuration` and the project's configured
`checks`. The profile version identifies the Framework's configuration and storage formats; it is
not a version of the specification language. A configuration of another profile version is refused
rather than reinterpreted.

The registry is `{"schema_version": 3, "modules": [...]}`: one record per Module with its `id`,
`title`, `entry` and a mirror of the entry's `module` block. `python3 scripts/concorde.py registry
--write` regenerates the mirrored fields from the entries; which Modules exist changes only by an
explicit registry edit.

### P5. One Module's boundary per bounded task

A bounded invocation is bound to one Module and freezes the Protocol's boundary sets for it.

- **Spec context** is the Module's `SpecContext`: its own documents plus the documents its `uses`,
  `contains` and `includes` select, one level, both members of each. A scenario focus does not trim
  it. The host delivers it as a **context index and grant**: the frozen record lists every selected
  document with identity, owner, member role, digest and the relations that selected it; the
  members are granted read-only in place, or copied byte for byte into a capsule when the phase has
  no project workspace. No Spec body is embedded in an invocation's input. The worker opens the
  granted files itself, starting from the entry, and must not read outside the grant.
- **Implementation context** is the Module's `ImplementationContext`: the names of the files its
  realizations bind. A directory entry covers every regular file below it except directories named
  `node_modules`, `__pycache__`, `.venv`, `build` or `dist`, names starting with a dot, and `.pyc` and
  `.log` files. Every phase sees the names; only code-writing and code-review phases receive
  contents, from the Module's `ImplementationScope`.
- **External context** is the Module's `ExternalContext`: the pinned material under its external
  `includes`, each entry identified by one tree digest. Planning, task authoring, code writing and
  code review receive it read-only, with media and archives excluded. An undeclared network fetch or
  an installed dependency's sources never replaces it.
- **Task context** travels inline: the task, constraints, admitted stage artifacts and lifecycle
  metadata, and, for a review, the typed changes to the reviewed Module's own documents or
  implementation files since the baseline. It adds no source and replaces none.

Assessors, planners and task authors reason from the Spec context and, for planners and task
authors, the external context. They MUST NOT read source code to supply missing meaning. Agent
instructions, the Protocol bundle and the Pi integration are not context; every native Agent
receives its own instructions and reads the Protocol documents listed in its frozen index.

Native file scope is prompt-level policy, not OS confinement or proof of exclusive reads. The
configured-check and tester subprocess boundaries are real OS read-only boundaries and are
separate. The calling session reads and selects Specs within its own task grant; its extra reading
never becomes a worker's grant.

A context's identity covers the selected documents' bytes, the selecting declarations and their
reasons, the Protocol and instructions, stage artifacts, realization entries and lifecycle identity;
code phases also cover the bound file names and digests. Any changed input requires a new snapshot.

### P6. Gaps and reviews are tied to the affected contract

A missing required behaviour is a Spec gap of the owning Module. Name the missing promise, the
blocked step, the Module and the snapshot; continue only independent work. Source code never fills
the gap implicitly. A failed execution, an explicit prohibition and a missing runtime value with
defined failure behaviour are not Spec gaps.

Spec review reads the complete Spec context; code review reads the same Specs and the authorized
code in a fresh read-only invocation. A review records its exact inputs, coverage, findings and
completion; skipped, failed, incomplete and successful reviews stay distinct. When a document
changes, every Module whose Spec context selects it (`selected-by`) needs a fresh review; when a
promise changes, every Module that relies on it (`referenced-by`); when a file bound by several
Modules changes, every binding Module (`implemented-by`) needs its own checks and evidence.
Validation reports scenario coverage from the tests' `verifies` declarations; coverage is evidence
about the tests, never a change to the contract. No structural check proves semantic sufficiency.

### P7. Execution authority is explicit

The host binds each invocation to its declared context and file permissions. Only code-writing
invocations write files, and only within the selected Module's `ImplementationScope`; they never
change Spec documents or the registry. Code review and deterministic checks have separately declared
read authority. How the host keeps an invocation within that authority, and how far it is enforced
today, belongs to the Harness Module's Specs. The user session and its Task subagents may edit any
file within their own workspace and task grant, including `.concorde`; truthful evidence,
concurrency safety and bounded worker permissions remain mandatory.

An **Agent** is a callable native Pi agent with one canonical Concorde definition, either a Domain
Agent or a Task subagent. A **Workflow** is an authored native pi-subagents composition. An
**Operation** is an explicitly selected LangGraph StateGraph flow. Finite non-model actions are
**Host services**. Module ownership and Spec relations are independent of these executable kinds;
`concorde-*` capability names and `operation_id` fields do not make every capability an Operation.

Context assessment, tasks and implementation use direct native Agents. Planning, independent review
scopes and Issue solving use authored native workflows. Admission, configured checks, lifecycle,
Issue bookkeeping and validation are Host services. Native Domain Agents are terminal, fresh and
explicitly scoped, without task delegation or an extra coordinating model; native capacity and tool
ceilings stay authoritative. A model proposal is never domain completion: the Host accepts a result
only after correlating the actual native artifacts with the current inputs. Failed or cancelled work
keeps its partial edits and receipts.

LangGraph is used only for explicitly selected StateGraph Operations and Studio inspection, always
through the Graph API (`StateGraph`, nodes and edges declared before compilation), never
`langgraph.func`. `OperationNode` supplies a typed State transition with a trusted native launch and
admission service in the Runtime; State cannot carry or expand authority.

Agent instructions, the Pi session extension, schemas and rule assets are deterministic build
projections of their sources. Generated output is never edited as source.

### P8. Declarations change together

A structural change edits the owning Modules' entries (`module` blocks), document metadata and
reading together, then regenerates the registry mirror, and validates the combined result before any
dependent work. A shared definition is defined once by its owner and imported or relied upon by
others, never copied. Realization entries name intended files as `pending` until they exist; within
one Module the longest covering entry decides a file's realization, and a bound directory never
contains a Spec document. Before a file bound by several Modules changes, `implemented-by` names
every Module concerned. Code-writing workers never edit Specs or the registry. Direct edits confer
no assessment, review, check or completion evidence.

### P9. Task status and evidence have one primary authority

One stable task ID owns a change; branch and path are locators, not identity. Only the primary
worktree keeps the authoritative local `.concorde/status/` records and durable `.concorde/runs/`
evidence, including candidate executions. A status records mode, goal, base, candidate, child
ownership, phase, blockers and run references. Delivery and ordinary Git merge are distinct
outcomes; cleanup is separate, and terminal records survive candidate deletion. These records are
local, never project configuration, and never merged between branches. Host persistence uses
repository locking and atomic writes without giving a child access to the primary source or index.
Missing primary authority blocks persistence; it never creates a candidate-local replacement.

Evidence binds the actual worktree, branch, commit, dirty input identity and runtime, build and Pi
integration provenance when known. A catalog is not execution evidence. Delivery verifies the
actual integration, preserves unrelated changes and confirms pending entries only when they exist.

### P10. Fresh task sessions, never session moves

The user session understands needs and coordinates. It may delegate complete tasks to at most one
layer of fresh Task subagents. A Task subagent may call a series of capabilities and carry one
change to delivery, but never delegates tasks or moves worktrees. Native Domain Agents are terminal
Pi leaves with no delegation tools; they cannot create subagents or call capabilities. Insufficient
native launch capacity refuses rather than bypassing a ceiling. An Operation in an assigned
candidate reuses it instead of creating a nested one. Ordinary consumer projects may edit the
primary worktree directly for simple authorized tasks.

The user session decides task scope, worktree ownership, continuation of a Task subagent, checks,
independent testing and integration authorization. One writer owns a worktree at a time and stops
writing before testing. The user session's high-level decomposition into work packages,
ownership and gates is not Concorde's product `plan`/`tasks`. Parallel component work stays in
separate worktrees; combining them is a distinct gate. Reuse a Task subagent within one coherent
stage; after a completed stage with changed goals, a fresh one may continue after a durable handoff,
an observed stop and an exact release of ownership.

The user session chooses none, targeted or full independent testing with an explicit scope and
reason; self-tests are not independent. When selected, the project `tester` is a fresh sibling Task
subagent, not a LangGraph node. It receives only explicitly selected local Pi integration and
runtime provenance and its actual grant; missing or stale assets block, without a global fallback.
Tester keeps governing artifacts read-only, uses external scratch, returns failures rather than
repairing them, and runs commands only through the OS read-only check boundary. The user session's
pi-subagents extension is a host prerequisite, never a worker dependency. Passive observation adds
no tools, catalogs, authority or network telemetry.

Changed relevant inputs or environment invalidate the corresponding check evidence; stage reports
and same-tree commits alone do not demand repeated full suites. Already fully read, unchanged Specs
in valid same-session context need not be reread. Resource handoffs state observed capacity,
current input including cache, reserve and compaction status, or an actual error; unknown metrics
stay unknown. After a supported compaction completes, inject the current concise task brief once:
goal and grant, accepted decisions, evidence and next step.

Host-observed lifecycle, activity, context and compaction stay distinct from worker-reported stage,
objective, completed artifacts, checks and failures, blocker and next action. Supervisor updates
carry meaningful changes without polling, repetitive reports or fake percentages. Integration
requires explicit authorization; cleanup remains separate.

Concorde's source repository adds its own source-only maintenance and coordinator prompts and
validation policy. They are not installed as consumer testing instructions.

### Framework authoring and publication conventions

Concorde's own Specs follow the Protocol's layout: one folder per Module under `specs/concorde/`
(Harness children under `specs/concorde/harness/<child>/`), an entry `module.md` with Purpose,
Terminology, Usage, Design and Relationships, optional `module`-role topics, and
`implementation`-role documents for requirements, scenarios, contracts and Graph Specs. Identities
follow `<kind>.<module-short>.<slug>`, where the module short name is the last segment of the
Module identity. Words shared by every Module are defined in the root's `vocabulary.md`.

Reading diagrams use English labels and `accTitle`/`accDescr`. An unmarked flowchart in a `module`
document is a checked flowchart; a conceptual picture is marked `mermaid illustrative`.

The metadata extensions `concorde.operations` (the checked public capability inventory, with State
contracts and composition) and `concorde.agents` (the Agent inventory, with family, distribution
scope, registration and instruction source) live in the Operations and Agents documents that
explain them. Their behaviour is explained in reading; an extension never overrides the Protocol.

Every Operation is explained in the Spec of the Module that owns its behaviour: what it is for, when
to use it, what it takes and returns, when it stops, and its actual StateGraph composition. Every
executable Graph has one **Graph Spec** in its owner's `implementation` documents, written with
LangGraph's concepts as three parts in order, each opening a paragraph with its bold label:
**State.** (the channels, their reducers and the records the nodes read and write), **Nodes.** (a
table of node name, what executes, `in` and `out` state) and **Edges.** (how the next node is
chosen, by a conditional edge reading a named State channel or by a `Command` the node returns, and
where stops and errors lead). A Mermaid flowchart follows, bound to the compiled Graph by
`%% graph: <name>`, whose node identifiers are the compiled node names including `__start__` and
`__end__`, whose node labels state `in:` and `out:` as the Nodes table does, and whose edges carry
their routing condition as a label exactly when the source node has several successors. The
heading carries an explicit `{#anchor}`, and a `module` document of the same Module links to it.
The configured Graph Spec check keeps every Graph Spec equal to its compiled Graph. A Graph Spec
flowchart is not a checked relationship view.

A Python test declares the scenarios it verifies with the `verifies` decorator from
`concorde.spec.verification`, for example `@verifies("scenario.harness.context-freeze")`. A
TypeScript test declares them with an own-line `// verifies:` comment above the test, for example
`// verifies: scenario.views.publish-candidate` above its `it` call; several IDs are separated by
commas or spaces. Declarations are read by parsing, never by running the test. A Module that binds
no implementation file has no test to declare its scenarios, and its scenarios are not reported as
uncovered. No Spec document lists tests. Links inside Specs address definitions by identity, such as
`scenarios.md#scenario.harness.context-freeze`; publication makes every identity an anchor. These
conventions implement the Protocol for this project; they are not requirements on every Protocol
implementation.
