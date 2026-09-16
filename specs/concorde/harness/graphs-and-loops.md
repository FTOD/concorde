# Capability Flows, loops and feedback

Orchestration coordinates Capability invocations and control decisions toward a declared goal. A Flow describes the structure of that coordination; a Loop describes feedback
driven execution. They are related concepts, not interchangeable names.

**Flow** is Concorde's name for an executable LangGraph `StateGraph`. Every Flow is built with
LangGraph's Graph API, which declares nodes and edges before compilation; the Functional API
(`entrypoint` and `task` from `langgraph.func`) is not used anywhere in Concorde's source or
scripts, because a Flow whose control flow lives inside ordinary Python compiles to a single
opaque node with nothing for a Flow Spec, the Flow Spec check or Studio to inspect. Authored
descriptions and new Python factories use Flow and `build_*_flow`; LangGraph API names such as
`StateGraph`, `get_graph()` and the `graphs` configuration key keep their library spelling.
Existing stable Spec identities, import aliases and persisted `graph` records remain compatible.

A Flow's state is a typed LangGraph state schema: the development and specification Flows carry
the last stage's typed response in `output`, a terminal failure envelope in `result` and the
accumulated artifact references in `artifacts` under a reducer, and each stage node selects its own
transition by returning a `Command` whose `goto` names a declared destination. No node smuggles
routing or evidence through untyped fields. Every model-backed node executes its worker through an
`CapabilityNode`: a State-based node/subgraph adapter whose input schema is generated from the worker contract's
admitted context type and whose output schema is generated from its result type, so the contract is
the graph state, and the Pi worker launch with its admission checks stays a host-private launcher
outside that state. The same `CapabilityNode` factory is exposed for inspection
inside the Flows that run it.

A Flow's compiled nodes and edges are the authority for execution views. Inspection compiles the
same factories used by execution without invoking nodes, reading project contexts or launching
Agents. Branches, repeated Agent decisions, delegation, feedback and stage handoffs belong in Flow
transitions. Ordinary Python inside a node may validate data, prepare a context, perform one Agent
invocation or carry out a deterministic operation. An atomic delivery transaction may remain one
deterministic node so its repository lock and rollback boundary stay intact.

Runtime-dependent Module selection, resume entries and scope produce explicit conditional edges
or bounded Flow variants. A viewer must identify the variant or expose the possible branches; it
must not present hand-authored topology as executed code. Runtime-only host objects and callbacks
are not public inputs or durable checkpoint values. Stateless internal Flows are inspectable but
do not promise internal checkpoint resume; replay re-enters admission through the public boundary.

### Dispatch terminology

**Code-driven** dispatch uses explicit code rules to choose the next action, target Agent and
continue/stop condition. **Model-driven** dispatch uses a model's task and feedback assessment to
choose the next action or delegation. These name the source of a decision. They may alternate
within one Agent loop and nest in either direction across child invocations. Human decisions remain
separate, explicit inputs. Code-driven control does not guarantee reproducible overall output:
models, tools and external state may still vary. Determinism is a property to document where it
applies, not the primary classification of Agents or dispatch.

### G1. Capability Flow

A Flow MUST declare its participating Capabilities, State contracts and directed transitions. Transitions MUST identify their trigger and
the information they transfer. Conditional branches, parallel execution or joins, when used, MUST
define selection, completion and failure behavior. A sequence of deterministic installation steps
does not become model-backed merely because it has several steps.

The Flow MUST identify which model Capability makes each model-assisted decision, which transitions are
code-driven, and which require a human decision. It MUST preserve invocation-local context and
permissions across every handoff. A coordinator receives only admitted results; dispatching an
model Capability does not grant access to its complete private context.

A Flow MAY be exposed as a Capability with a complete external contract. Invoking that Capability
does not expose its internal model workers or grant authority to call arbitrary internal nodes.

### G2. Feedback loop

A loop MUST define how execution moves through decision, action, observation and feedback,
and how those observations affect the next action. It MUST define completion, revision, waiting,
cancellation, failure and execution-limit conditions. Limits may be time, iterations, resource
budgets or an explicit bounded host policy; an unbounded retry is not an implicit default.

A model Capability's Harness supplies its local tool loop. A composed Flow may additionally
coordinate loops across several Capabilities, such as author → reviewer → author. Each invocation's local loop and its enclosing loop MUST have distinguishable state and completion
conditions. Orchestration between workers is always a Flow transition: one worker never starts
another. Inside one worker, delegation is limited to one level of its own declared children, as
defined in A5; a child's work is evidence for its worker, not a Flow step.

A retry or revision MUST identify what changed or what recovery condition permits another attempt.
Unchanged blocking feedback MUST not cause endless retries. Stale task, context, policy or result
identity requires re-admission before execution continues. Completion of an inner loop does not
automatically complete the enclosing Flow or authorize delivery.

### G3. AI and human feedback

Feedback MUST identify its source, subject, relevant task or result revision, finding or decision,
and the transition it can affect. AI feedback and human decisions MUST remain distinguishable.
The representation may use existing typed review, task and acceptance artifacts; this requirement
does not introduce a separate comment store or mandatory feedback report.

| Feedback | Example | Permitted effect |
| --- | --- | --- |
| AI assessment | A context assessor identifies a necessary missing contract | Block the dependent step and name the required information |
| AI review | A reviewer identifies a defect against the bound Spec | Select an admitted repair path and recheck the revised result |
| Human clarification | A developer supplies missing intent or corrects a goal | Produce an explicit task or context revision for fresh admission |
| Human acceptance | A developer accepts a specific topology or delivery proposal | Enable only the transition and effects covered by that acceptance |
| Human rejection or cancellation | A developer rejects a proposal or ends the task | Revise, wait or terminate according to the Flow contract |

AI feedback cannot substitute for a required human acceptance. Human text that merely mentions a
Tool or broader context is not an automatic permission grant. Every transition MUST preserve the
applicable task, context and authority checks. A graph receiving no answer to a required decision
remains waiting; elapsed time is not acceptance.

### G4. State, recovery and evidence

Execution evidence MUST identify the Flow and loop policy, participating Agent invocations,
admitted feedback and selected transitions. It MUST distinguish completed, waiting, blocked,
cancelled, failed and limit-exhausted outcomes. A supported resume operation MUST revalidate the
saved state and feedback against the current task and authority before choosing the next transition.

New development-graph transition records use `source: code-driven|model-driven` for this
classification. A review-selected repair is model-driven; host stops for unchanged feedback,
exhausted repair limits or failed checks/execution are code-driven. Existing `trigger` strings
remain descriptive compatibility labels for historical records, not a second dispatch taxonomy.

Review and check results are evidence about the bound revision. They do not remain valid after
relevant Agent Specs, Harness configurations, capability contracts, project inputs or policies
change. Raw logs and native transcripts remain diagnostics unless explicitly admitted as typed
downstream inputs.

### Flow Specs

Every executable Flow is specified with LangGraph's own three concepts, and nothing else stands
in for them: a **node** is one executing step, an **edge** is one routing decision, and **state**
is what a node reads and writes. A Flow Spec is one section of the owning Module's documents and
has three parts:

1. **State**: the typed channels the Flow carries between nodes and the candidate or lifecycle
   records its nodes read and write.
2. **Nodes**: a table naming each node exactly as the compiled Flow names it, what it executes
   (a deterministic, model-backed or composed Capability with its execution mode), and the state
   it reads (`in`) and writes (`out`).
3. **Edges**: a Mermaid flowchart bound to the compiled Flow by the comment `%% flow: <name>`,
   where `<name>` is the Flow's compiled graph name in the Flow catalog. Its node identifiers are
   the compiled node names, `__start__` and `__end__` included; every node label states the node
   name, then `in:` and `out:`; every edge leaving a node with several successors is labeled with
   the condition that selects it, and an edge leaving a node with one successor carries no label.

The Flow Spec check (`scripts/development/check-flow-specs.py`, the configured
`check.development.flow-specs`) compiles every catalog Flow with inert nodes and reports each
diagram whose nodes, edges, routing labels or state labels disagree with the compiled topology,
and every compiled Flow without a diagram. It also enforces the Graph API rule: a catalog Flow
that is not a compiled `StateGraph`, and any Python file under `src/`, `scripts/` or `capabilities/` that imports
`langgraph.func`, found by parsing the file rather than running it, are errors. A diagram that
passes proves the Spec and the executed topology agree; it proves nothing about whether the
routing conditions are right, which the scenarios and tests of the owning Module cover. The Relationships diagram of a Module's
reading entry remains the entity diagram the Protocol defines; Flow Specs live in other sections
or documents.

## Design

### Concorde Flow responsibilities

The query Flow coordinates explicit context selection, deterministic source indexing and grant, and direct answers. The topology Flow
coordinates design, human acceptance and separately bound Spec authors. Specification Flow independently coordinates authoring and Spec review. Development Flow
consumes it and the sibling Planning, Implementation, Validation and Review providers, with explicit
repair or human-clarification loops. Issue solving may select verification, Spec repair or development
Flow after a human disposition. Delivery remains a separately authorized deterministic capability.

Existing topic Specs retain their task and authority contracts. The capability adapter
and existing Skill names remain compatible identifiers. A stage sequence satisfies only the
transitions it implements and records; a graph library or a function name proves nothing by itself.
