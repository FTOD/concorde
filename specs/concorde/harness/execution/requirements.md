# Agent execution requirements

These are the Module-wide obligations of Agent execution. The [entry](module.md) explains why they
exist; [interfaces](interfaces.md) states the exact records and limits they refer to.

## Agent calls and acceptance

### req.execution.proposal-not-completion — A proposal is not a result

An Agent call's proposal SHALL NOT be accepted as a result before the acceptance step has verified
the run's native records and rechecked the current inputs.

Submission and staging never change task state. The acceptance step (`accept` for a single call,
`finalize` for a Workflow) reads pi-subagents' records of the run itself, as defined in
[native terminal evidence](interfaces.md#native-terminal-evidence), and calls the provider's
acceptance only after those checks pass.

### req.execution.single-proposal — One proposal per call

A result gate SHALL hold at most one proposal per call, never replacing one it has stored or
refused.

A submission that pi-subagents rejects against the output schema never reaches the Host, so the
Agent may correct it within the same run and deadline.

### req.execution.settling-not-completion — Ending a run is not completing it

An Agent call that ends without exactly one valid submitted result SHALL NOT be treated as
completed.

### req.execution.no-retry — No automatic retry

No execution failure SHALL cause an automatic retry, with the same or with wider permissions.

A failed or uncertain acceptance is final for its call; a further attempt is a new request that
passes admission again. Files a programmer changed before a failure stay in the candidate.

### req.execution.preflight-shape — Launch only the prepared shape

An Agent call SHALL be refused before its model starts unless native preflight resolves exactly the
prepared Agent file, a fresh context without inherited project context, global context or Skills,
no nested subagents, and no tool outside the Agent's allowed list.

The allowed list is `read`, `grep`, `find`, `ls`, `report_issue` and `structured_output`, plus
`edit`, `write`, `bash` and `run_checks` for the programmer and `run_checks` for the code reviewer.
This bounds which tools exist; it does not bound which files those tools reach.

### req.execution.terminal-agents — Agents do not delegate

An Agent SHALL NOT delegate a task, create a subagent or invoke a Concorde capability.

For Agent calls this is enforced by the tool ceiling and preflight above. A shell command that
starts another program is prohibited by the Agent's instructions only.

### req.execution.producer-pinned — Read only the reviewed native producer

The Host SHALL read native terminal evidence only from a pi-subagents installation whose package
identity and selected source digests equal the pinned adapter contract.

### req.execution.model-selection — Each Agent runs on its own selection

Every Agent launch SHALL use the model, thinking level and time limit resolved for that Agent from
the project configuration.

## Graphs

### req.execution.graph-api-only — Graphs use the Graph API

Every Graph that Concorde compiles SHALL be built with LangGraph's Graph API as a `StateGraph`.

No Python source under `src/`, `scripts/`, `agents/` or `operations/` imports LangGraph's
Functional API (`langgraph.func`), because a Graph written with it hides its control flow inside
ordinary Python where no Graph Spec or check can inspect it. The Graph Spec check parses
these files without running them.

### req.execution.graph-spec-agreement — Every Graph has one matching Graph Spec

The Graph Spec check SHALL report every catalog Graph that does not have exactly one Graph Spec
whose diagram, parts and Nodes table agree with its compiled topology.

The precise rules are in [the Graph Spec check](interfaces.md#graph-spec-check).

### req.execution.operation-service-explicit — The Operation runs only a supplied service

The Terminal Agent Operation SHALL refuse to execute unless its embedding supplies the Agent service
through Runtime context or the graph factory, never through State.

## Diagnostics

### req.execution.diagnostics-passive — Diagnostics never change outcomes

Recording timing SHALL NOT change the outcome, the retry behaviour or the authority of the
work it describes.

Values that were not reported are recorded as unknown, not zero. Records contain no prompts,
source text, tool output, environment values or command arguments.
