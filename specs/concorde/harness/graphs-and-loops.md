```concorde-document
{
  "id": "document.harness.graphs-and-loops",
  "owner": "module.harness",
  "main_visible": true
}
```
# Agent Flows, Agent Loops and feedback

Agent orchestration coordinates Agent invocations, Capability calls and control decisions toward
a declared goal. A Flow describes the structure of that coordination; a Loop describes feedback
driven execution. They are related concepts, not interchangeable names.

**Flow** is Concorde's name for an executable LangGraph `StateGraph`. Authored descriptions and
new Python factories use Flow and `build_*_flow`; LangGraph API names such as `StateGraph`,
`get_graph()` and the `graphs` configuration key keep their library spelling. Existing stable
Spec identities, import aliases and persisted `graph` records remain compatible.

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

## Dispatch terminology

**Code-driven** dispatch uses explicit code rules to choose the next action, target Agent and
continue/stop condition. **Model-driven** dispatch uses a model's task and feedback assessment to
choose the next action or delegation. These name the source of a decision. They may alternate
within one Agent loop and nest in either direction across child invocations. Human decisions remain
separate, explicit inputs. Code-driven control does not guarantee reproducible overall output:
models, tools and external state may still vary. Determinism is a property to document where it
applies, not the primary classification of Agents or dispatch.

## G1. Agent Flow

An Agent Flow MUST declare its participating Agent definitions, Capability calls, control nodes,
state and result contracts, and directed transitions. Transitions MUST identify their trigger and
the information they transfer. Conditional branches, parallel execution or joins, when used, MUST
define selection, completion and failure behavior. A sequence of deterministic installation steps
does not become an Agent Flow merely because it has several steps.

The Flow MUST identify which Agent makes each model-assisted decision, which transitions are
code-driven, and which require a human decision. It MUST preserve invocation-local context and
permissions across every handoff. A coordinator receives only admitted results; dispatching an
Agent does not grant access to that Agent's complete private context.

A Flow MAY be exposed as a Capability with a complete external contract. Invoking that Capability
does not expose its internal Agents or grant authority to call arbitrary internal nodes.

## G2. Agent Loop

An Agent Loop MUST define how execution moves through decision, action, observation and feedback,
and how those observations affect the next action. It MUST define completion, revision, waiting,
cancellation, failure and execution-limit conditions. Limits may be time, iterations, resource
budgets or an explicit bounded host policy; an unbounded retry is not an implicit default.

An Agent's Harness supplies its local control-loop mechanism. An Agent Flow may additionally
coordinate loops across several Agents, such as author → reviewer → author. Each invocation's local loop and its enclosing loop MUST have distinguishable state and completion
conditions. There is no fixed outer-Concorde/inner-provider hierarchy: a Codex or Claude Agent can
delegate to a Python-controlled Agent, which can invoke another model-driven Agent. All such edges
use the same host admission, typed feedback and shared tree limits defined in A5.

A retry or revision MUST identify what changed or what recovery condition permits another attempt.
Unchanged blocking feedback MUST not cause endless retries. Stale task, context, policy or result
identity requires re-admission before execution continues. Completion of an inner loop does not
automatically complete the enclosing Flow or authorize delivery.

## G3. AI and human feedback

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

## G4. State, recovery and evidence

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

## Concorde Flow responsibilities

The query Flow coordinates explicit context selection, deterministic source injection and direct answers. The topology Flow
coordinates design, human acceptance and separately bound Spec authors. The development Flow
coordinates authoring, assessment, planning, implementation and independent review, with explicit
repair or human-clarification loops. Reflection handling may select an investigation or development
Flow after a human disposition. Delivery remains a separately authorized deterministic capability.

Existing topic Specs retain their task and authority contracts. The global/lifecycle/stage adapter
and existing Skill names remain compatible identifiers. A stage sequence satisfies only the
transitions it implements and records; a graph library or a function name proves nothing by itself.
