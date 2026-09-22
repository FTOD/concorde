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
- AND the refusal is reported as a Host refusal with its lower-level cause

### scenario.harness.worker-selection — Launch each Agent on its configured selection

- GIVEN a project configuration with a default model, thinking level and time limit and per-Agent overrides
- WHEN the Host prepares an Agent call or binds an RPC diagnostic worker
- THEN each value comes from the Agent's entry, else the default, and a missing time limit falls back to the Agent's own
- AND the selection reaches Pi as the model, the thinking level and the deadline of the launch
- BUT an unset model or thinking level keeps Pi's own default

### scenario.harness.worker-selection-reject — Reject a selection no Agent can run

- GIVEN a configuration whose `workers` map names an unknown Agent, or that holds a nonpositive time limit, a model without a provider or an unknown thinking level
- WHEN the configuration is proposed, applied or loaded
- THEN it is rejected with a typed field error naming the offending entry
- AND a rejected proposal or application leaves the stored configuration unchanged

## The Terminal Agent Operation and Studio

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

- GIVEN the Graph catalog and the Studio export
- WHEN a viewer requests the Terminal Agent Operation's nodes, edges and schemas
- THEN it sees the real `terminal_agent` node without running an Agent or reading a project context
- AND State holds only declared data while trusted services stay in Runtime context
- AND no public capability is exposed as a graph

### scenario.harness.graph-execution — Execute the graph that was inspected

- GIVEN a Terminal Agent Operation with a trusted Agent service
- WHEN an embedding executes it
- THEN the same compiled graph that Studio inspects runs its one node
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

### scenario.harness.usage-accounting — Record what each RPC worker launch consumed

- GIVEN an RPC diagnostic worker that settled and reported its session statistics
- WHEN the Host accepts its outcome
- THEN the outcome carries the reported input, cached, output and total tokens, cost and turns, the model and thinking level, the measured wall time and the prompt and context sizes
- AND the Host appends one schema-2 line, labelled with operation, stage, target, Agent, change and launch identity, to the root invocation's `usage.jsonl` in the primary worktree
- AND `concorde usage` and the entry's summary aggregate those lines per step, stage, target, Agent and run
- AND unversioned older lines are counted separately without being rewritten, and unknown formats make the summary incomplete instead of being totalled
- BUT an unreported figure is unknown rather than zero, and a failed write never fails the launch

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

## The RPC diagnostic worker

### scenario.harness.execute-success — Run a bound RPC worker and accept its typed result

- GIVEN a Host-built worker invocation with a verified Agent binding, frozen context, compiled grant and model selection
- WHEN the worker executor runs it
- THEN it first reverifies the binding against the current build, the instructions against the rendered Agent and the context and grant against the Agent's contract, before any process starts
- AND it launches one Pi worker whose `submit_result` tool takes exactly the result schema this Agent may populate
- AND it returns an outcome bound to the invocation and binding digests only for one submitted result that satisfies the result type and the contract

### scenario.harness.execute-failure — Distinguish failed, cancelled, timed-out and invalid runs

- GIVEN a refused preflight or a Pi process that fails before settling, a Host interrupt, a run past its deadline, or a run whose submitted result is missing, repeated or outside the contract
- WHEN the worker executor runs it
- THEN it raises an execution error with outcome `failed`, `cancelled`, `limit_exhausted` or `invalid_completion` respectively
- AND a contract rejection keeps its code, `permission_denied` for fields this Agent may not populate
- AND the caller stops instead of retrying

### scenario.harness.worker-contract — An RPC worker runs only its own contract

- GIVEN an RPC diagnostic worker for one Agent and one selected Module
- WHEN the Host binds it and the executor admits its launch and its result
- THEN its prompt is the Agent's rendered instructions followed by the Protocol files its context lists
- AND a mismatched phase, context or result type, missing required stage artifacts, implementation contents for an Agent without implementation reads and a grant wider than the contract are rejected before a process starts
- AND the submission tool omits optional fields the Agent may not populate and allows only empty values for such required fields
- AND a refused submission does not end the run, so a corrected one can succeed within the same deadline
- AND the Host independently rejects a result with an outcome or a populated field its contract does not permit
- BUT two workers of the same Module never share an invocation, a context identity, a conversation or a write grant

### scenario.harness.pi-rpc-client — Read one Pi RPC run to settlement

- GIVEN a process speaking Pi's RPC protocol
- WHEN the Host runs one prompt through it
- THEN records are split on line feed only, so U+2028 and U+2029 inside a JSON string stay inside it, and a trailing carriage return is dropped
- AND every extension dialog is answered as cancelled, every tool result is collected and the session statistics are read after `agent_settled`
- BUT a process that closes its output before settling raises an RPC error, and a run past its deadline is killed and raises a timeout

### scenario.harness.pi-worker-launch — Launch an RPC worker and admit its single result

- GIVEN a launch with a workspace, grants, tools, a system prompt, a message, a result schema and a Pi model
- WHEN the Pi worker runtime runs it
- THEN Pi starts in RPC mode with sessions, context files, Skills, prompt templates, themes and discovered extensions disabled, the Concorde worker extension loaded and the Host-rendered system prompt in place
- AND the returned value is the details of the single successful `submit_result` call, with usage from Pi's session statistics
- AND a `run_checks` call is answered by the Host's configured-check service
- BUT a run without a submission fails as `invalid_completion`, a run past its deadline as `limit_exhausted`, and an inconsistent launch is refused before any process starts

### scenario.harness.pi-worker-gate — Refuse tool calls outside the grant

- GIVEN an RPC diagnostic worker with read and write grants and a tool list
- WHEN its model reads, searches or writes a path outside the grants, or calls a tool it was not granted
- THEN the worker extension refuses the call with an error naming the policy, and the file is neither read nor changed
- AND calls inside the grants run normally
- AND each `bash` command runs with the provider credential variables unset

### scenario.harness.worker-sandbox — Confine the RPC worker process to its grant

- GIVEN a launch with a workspace, write entries including a pending file and a pending directory, and a run directory
- WHEN the runtime derives the mount plan and starts the Pi process inside it
- THEN the process can write exactly the write entries, the pending placeholders and its run directory, while the rest of the workspace and the host filesystem are read-only
- AND the listed secret locations read as empty, other worktrees of the repository are hidden while its shared Git directory stays readable, the host's temporary directory is private, and the process starts in the workspace with its own home and PID namespace
- AND a pending placeholder left empty is removed after the run, while a written one stays
- BUT a write entry that is a symlink or leaves the workspace is refused before any process starts

### scenario.harness.worker-sandbox-unavailable — An unenforceable sandbox refuses the launch

- GIVEN a host without a trusted bubblewrap installation, or a platform other than Linux
- WHEN an RPC diagnostic worker launch is requested
- THEN it is refused as `worker sandbox unavailable` before any Pi process starts
- BUT this says nothing about native Agent calls, which never use this sandbox

### scenario.harness.pi-worker-delegation — Workers cannot delegate

- GIVEN an RPC diagnostic worker with its tool and file grants
- WHEN it is launched, with or without delegation-depth environment variables
- THEN its Pi catalog contains only the declared non-delegating tools and no ambient Skills, instructions, extensions or child catalogs
- AND a request for a subagent tool, the `concorde` tool, a child definition or a child selection fails instead of starting another worker
- AND depth variables are neither read nor forwarded, so they cannot block or widen the launch
