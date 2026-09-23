# Agent execution scenarios

Concrete situations that show what the [requirements](requirements.md) mean in practice. Exact
records and limits are in [interfaces](interfaces.md).

## Agent calls and acceptance

### scenario.harness.native-result-gate — A submission is a proposal, not completion

- GIVEN a prepared Agent call with a Host-issued invocation identity and proposal location
- WHEN the Agent submits its result with `structured_output` and the call's plain gate runs `stage`
- THEN the result gate stores exactly one proposal after checking its shape and business identity
- AND staging rechecks the stored bytes and current inputs and prints one bounded canonical control document with `state: staged` and `accepted: false`
- AND neither submission nor staging changes any task state
- AND a separate acceptance step verifies the run's native records and the current inputs before it calls the provider's acceptance
- AND a repeated or concurrent acceptance never applies the provider's acceptance a second time
- BUT a missing, duplicate, oversized, foreign, aliased or changed proposal is never accepted
- BUT cancellation or failure before acceptance revokes it without undoing files already changed
- BUT a failed or uncertain acceptance requires a new request instead of a retry

The digests and rechecks detect changed inputs; they do not show what the Agent read.

### scenario.harness.native-terminal-evidence — Reconcile every child before accepting a Workflow

- GIVEN a Workflow run bound to its run identity, session and ticket, with the child keys, Agents, proposal digests and gate commands the Host issued
- WHEN finalization reads the Workflow's native status record and each child's native metadata
- THEN it requires exactly one completed, successful child per issued key, each with matching run, Agent and proposal identities and a passed gate whose control document is bound to that proposal
- AND a failed child with a passing gate, an emitted success flag, missing or duplicated children, or a lost metadata or status write blocks acceptance
- AND the check does not depend on a Workflow receipt that pi-subagents writes only after the final step
- AND stopping before the provider's acceptance leaves no accepted result, while stopping after it keeps the accepted result as a separate fact from the cancelled Workflow
- BUT a producer other than the pinned pi-subagents release, or a record carrying a version field, is refused rather than reinterpreted

These records establish cooperative provenance; a process running as the same user could still
rewrite them.

### scenario.execution.preflight-refusal — A launch outside the prepared shape never starts

- GIVEN a prepared Agent call
- WHEN native preflight resolves a different Agent file, an inherited project or global context, a Skill, a nested subagent permission or a tool outside the Agent's allowed list
- THEN the Host refuses the launch before the model starts
- AND the refusal is reported in the `native-preflight` layer of the causal feedback record
- AND a refusal by pi-subagents' own preflight is a Host refusal that keeps pi-subagents' reasons as its causes

### scenario.harness.worker-selection — Launch each Agent on its configured selection

- GIVEN a project configuration with a default model, thinking level and time limit and per-Agent overrides
- WHEN the Host prepares an Agent call
- THEN each value comes from the Agent's entry, else the default, and a missing time limit falls back to the Agent's own
- AND the selection reaches Pi as the model, the thinking level and the deadline of the launch
- BUT an unset model or thinking level keeps Pi's own default

### scenario.harness.worker-selection-reject — Reject a selection no Agent can run

- GIVEN a configuration whose `workers` map names an unknown Agent, or that holds a nonpositive time limit, a model without a provider or an unknown thinking level
- WHEN the configuration is proposed, applied or loaded
- THEN it is rejected with a typed field error naming the offending entry
- AND a rejected proposal or application leaves the stored configuration unchanged

## The Terminal Agent Operation

### scenario.harness.agent-node — The Operation is typed by the Agent's contract

- GIVEN an Agent whose worker profile names a typed input and a typed result
- WHEN the Host builds its Terminal Agent Operation
- THEN the graph's input channels are exactly the input type's top-level fields and its output channels exactly the result type's
- AND the node validates the input before calling the service and the returned result after it, including the fields this Agent may populate
- AND the same factory without a service compiles an inspectable graph that starts no process

### scenario.harness.optional-operation — The Agent service is supplied explicitly

- GIVEN a Terminal Agent Operation
- WHEN a trusted embedding supplies an Agent service in Runtime context and invokes the graph synchronously or asynchronously
- THEN the graph calls that service once and returns the validated typed result
- AND a missing service refuses execution, and no State field can supply one
- AND a synchronous invocation refuses a service that returns an awaitable

### scenario.harness.graph-inspection — Inspect the graph without gaining authority

- GIVEN the Graph catalog
- WHEN a viewer requests the Terminal Agent Operation's nodes, edges and schemas
- THEN it sees the real `terminal_agent` node without running an Agent or reading a project context
- AND State holds only declared data while trusted services stay in Runtime context
- AND no public capability is exposed as a graph

### scenario.harness.graph-execution — Execute the graph that was inspected

- GIVEN a Terminal Agent Operation with a trusted Agent service
- WHEN an embedding executes it
- THEN the same compiled graph that the Graph catalog builds for inspection runs its one node
- AND a failed service or a rejected result stops the graph without an output update
- BUT public capabilities keep running as Agent calls and Workflows, not through this graph

### scenario.harness.operation-state — Only declared channels cross an Operation boundary

- GIVEN a capability's State adapter or a Terminal Agent Operation embedded in a larger parent State
- WHEN the parent graph runs it
- THEN only the declared input channels reach it and only its declared output channels leave it
- AND trusted hosts and services stay in Runtime context rather than State

### scenario.harness.operation-result-state — Host failures stay explicit in State

- GIVEN a capability invoked through its State adapter
- WHEN admission or execution returns a blocked or failed result envelope
- THEN the `result` channel carries that envelope and its errors unchanged
- BUT no successful output is invented

## Graph Specs

### scenario.harness.graph-specs — Every Graph Spec equals its compiled Graph

- GIVEN the Graph catalog compiled with inert nodes
- WHEN the Graph Spec check reads every flowchart bound with `%% graph: <name>` in the registered Spec documents
- THEN each bound diagram's nodes and edges equal the compiled ones, start and end included, a node with several successors labels each edge with its condition and a node with one successor labels none, and every executing node's label states its `in:` and `out:` state
- AND its section is in an implementation document and states its State, Nodes and Edges parts once each and in that order, with a Nodes table naming exactly the compiled nodes with the same state as their labels
- AND the section heading carries an explicit anchor that a module document of the same Module links to
- AND every compiled Graph has exactly one bound diagram and every bound name is a compiled Graph
- BUT a passing check shows only that Spec and code have the same shape, not that the routing is right

### scenario.harness.graph-api-only — Every Graph is built with the Graph API

- GIVEN the Graph catalog and the Python sources under `src/`, `scripts/`, `agents/` and `operations/`
- WHEN the Graph Spec check compiles each catalog Graph and parses each source file without running it
- THEN a catalog Graph that is not a compiled `StateGraph` is an error naming the Graph
- AND an import of `langgraph.func` or of its `entrypoint` and `task` decorators is an error naming the file and line
- AND a file that cannot be parsed is an error rather than a pass

## Diagnostics

### scenario.harness.diagnostic-spans — Timing does not change execution

- GIVEN nested or concurrent runtime work, or a failing timing sink
- WHEN spans record success, error, cancellation or incomplete work
- THEN each span keeps its monotonic duration, wall timestamp, span, parent and process identities and any available invocation identities
- AND no prompt, source text, tool output, environment value or command argument is recorded
- AND missing counts stay unknown, overflow of the bounded trace is counted, and a sink failure marks the trace incomplete without changing the result or causing a retry
- AND analysis unions intervals per process and never subtracts clocks of different processes

### scenario.harness.session-observation — Observe a session without adding authority

- GIVEN a user, maintenance or tester session that loads passive observation
- WHEN the session makes model requests, calls tools, waits or compacts
- THEN it records measured intervals and the reported context, usage, cache, reserve and compaction figures as session entries, keeping unknown values unknown
- AND observation adds no tool, prompt change, setting, child session or network telemetry
- AND reasons the user session supplies for a handoff or a test stay diagnostic facts, not grants
