# Development scenarios

These precise specifications belong directly to the [Development Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Capability](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Public capability](module.md#terminology) | Defined in Development capability host. |
| [Internal capability](module.md#terminology) | Defined in Development capability host. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Harness](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Development capability host

### scenario.development.execute-capability — Successful capability execution

- GIVEN an installed `concorde-*` Skill names one registered public Capability
- AND stdin carries a well-formed `concorde-capability-invocation@3` envelope in `execute` mode
- WHEN the host admits the request
- THEN it selects the capability's declared execution Flow and obtains every Agent invocation it needs, bound to current instructions, context and compiled authority, from Harness
- AND it returns a `concorde-capability-result@3` with status `succeeded` and the capability's own typed output

See [single boundary](requirements.md#req.development.single-boundary) and [distinct outcomes](requirements.md#req.development.distinct-outcomes).

### scenario.development.execute-unregistered — Unregistered or private capability refused

- GIVEN a `capability_id` that names no registered Skill, or a non-public capability invoked directly instead of through its composing capability
- WHEN the host admits the request
- THEN it refuses the request with `unknown_capability`
- AND no Agent is launched and no project file changes

See [non-public capabilities have no installed Skill](requirements.md#req.development.stage-no-skill) and
[non-public capabilities require declared composition](requirements.md#req.development.stage-in-process-only).

### scenario.development.execute-blocked-launch — Stale build or unenforceable permission blocks launch

- GIVEN the recorded build manifest no longer matches its sources, or the compiled policy for the bound Agent cannot be enforced by the Pi worker extension gate
- WHEN the host would otherwise launch an Agent for an admitted request
- THEN it blocks the request with `stale_build` or the applicable permission error before any process starts
- AND any existing candidate is preserved unchanged

### scenario.development.describe-policy — Preview a capability's grants without executing it

- GIVEN a request with `mode: describe-policy`
- WHEN the host processes it
- THEN it returns status `described`, naming the bound Agent, Harness, `agent_binding_digest`, `instructions_digest` and effective loop timeout for each previewed stage
- AND no Agent is launched and no project file changes

### scenario.development.invocation-worktree-binding — An invocation binds to the worktree at its working directory

- GIVEN a public Skill submits an invocation through the entry script from some working directory
- WHEN the host admits the request
- THEN it binds the project root to exactly that directory, without searching parent directories
- AND it reads the registry, every Spec collection, the lifecycle state and the listed implementation files from that worktree alone
- AND a working directory at a Git worktree root yields workspace kind `primary` or `change`, and a directory outside any Git repository yields kind `unversioned`
- AND a working directory inside a Git worktree that is not its root is refused with `workspace_mismatch` and no Agent is launched
- BUT the worktree in which the developer's agent session started, the worktree whose rendered Skill supplied the instructions and every other linked worktree contribute no registry, document or file to the invocation

See [project root is the entry process's working directory](requirements.md#req.development.project-root-is-working-directory).

### scenario.development.workspace-inventory — The primary inventory reads only linked worktrees' lifecycle state

- GIVEN the primary worktree and one or more live linked worktrees, some managed by their own `.concorde/worktree.json` and some not
- WHEN a capability invoked in the primary worktree resolves its `workspace` metadata
- THEN `active_worktrees` lists every live linked worktree from Git's worktree inventory with its path, branch, head and lock status
- AND a managed worktree contributes only the change_id, target, task summary, phase, status and outcome recorded in its own `.concorde/worktree.json`, and an unmanaged worktree is reported with status `unmanaged`
- AND the same inventory is persisted to the primary's `.concorde/worktrees.json`
- BUT no linked worktree's registry, Spec document or implementation file is read, so a candidate's draft Spec edits stay invisible to the primary until they are delivered
- AND a capability invoked in a linked worktree instead sees kind `change` with its own candidate identity and status

### scenario.development.worktree-handoff — Mutating request in the primary worktree hands off

- GIVEN a mutating capability request is admitted while the current session's worktree is the primary worktree
- WHEN the host would otherwise start development work there
- THEN it creates an isolated worktree from the committed HEAD and returns `worktree_handoff_required` with its path, branch, base commit and change_id
- AND it does not copy uncommitted primary changes or continue the originating session in the new worktree
- AND the error carries a complete Framework execution profile P10 prompt with real worktree identity, the submitted task and constraints, and the current preparation and check status

### scenario.development.flow-specs — Every Flow Spec equals its compiled Flow

- GIVEN the Flow catalog compiles every executable Flow with inert nodes
- WHEN the Flow Spec check reads every Mermaid flowchart bound with `%% flow: <name>` in the registered Spec documents
- THEN each bound diagram's node identifiers are exactly the compiled nodes including start and end, its edges are exactly the compiled edges, each edge leaving a node with several successors carries its routing condition and each edge leaving a node with one successor carries none, and every executing node's label states its in and out state
- AND every compiled Flow has exactly one bound diagram and every bound name is a compiled Flow
- BUT a passing check proves only that the Spec and the executed topology agree, not that the routing is right

### scenario.development.graph-api-only — Every Flow is built with the Graph API

- GIVEN the Flow catalog compiles every executable Flow with inert nodes
- WHEN the Flow Spec check inspects each compiled Flow and parses every Python file under `src/` and `scripts/` without executing it
- THEN each compiled Flow is a compiled `StateGraph` of LangGraph's Graph API
- AND no file imports LangGraph's Functional API, `langgraph.func` or its `entrypoint` and `task` decorators
- AND a Flow of any other kind, an import of the Functional API and a file that cannot be parsed are each an error finding naming the Flow or the file and line

### scenario.development.flow-execution — Execute the inspected Flow

- GIVEN an admitted capability request through a local or Studio entry
- WHEN the host executes the request
- THEN the same compiled Flow definitions select its capability branch, Agent stages and feedback transitions
- AND discovery expansion, topology authors, component work and Issue resolutions advance through bounded Flow transitions
- AND failed admission or a stopping outcome prevents dependent nodes from running
- AND existing task identity, context isolation, review requirements and delivery authorization remain enforced
- AND a change to the Flow that schedules scoped reviews invalidates their recorded input identity

### scenario.development.flow-bounds — Preserve domain limits across Flow composition

- GIVEN a Flow whose admitted work requires more than LangGraph's default scheduling limit
- WHEN the host executes its bounded discovery, batch or review-repair transitions
- THEN the configured scheduling allowance permits the admitted sequence to reach its domain completion or limit outcome
- AND exhausting a declared domain limit does not silently restart the Flow or widen its authority

## Capability registry

### scenario.development.capability-state — One executable identity and State boundary

- GIVEN a registered deterministic, model-backed or composed Capability
- WHEN its node is embedded in a LangGraph with a larger parent State
- THEN only declared input channels reach its implementation and only declared output updates leave it
- AND trusted hosts and launchers remain in Runtime context rather than State
- AND a model invocation still validates phase, artifacts, output fields and effective authority
- AND its composition dependencies use the same Capability inventory

### scenario.development.capability-result-state — Host graph failures remain explicit

- GIVEN a host-backed Capability invoked through its State interface
- WHEN admission or execution returns a blocked or failed capability envelope
- THEN the result channel preserves that envelope and its errors without inventing successful output
- AND its external Skill adapter preserves the existing versioned wire contract
