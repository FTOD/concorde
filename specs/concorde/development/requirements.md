# Development requirements

These precise specifications belong directly to the [Development Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Development capability host

### req.development.stage-no-reselect — Bound capabilities preserve their context

A Capability with bound context selection SHALL NOT reselect or expand the frozen context its composing capability gave it.

### req.development.no-implementation-for-non-code — No implementation contents for non-code phases

A planner, task author or Spec-only reviewer SHALL NOT receive the contents of this Module's or any
other Module's listed implementation files.

### req.development.project-root-is-working-directory — Project root is the entry process's working directory

The host SHALL bind every invocation's project root to the working directory of its entry
process, exactly as resolved and without searching parent directories.

The registry, Spec collections, lifecycle state and listed implementation files an invocation
reads are therefore those of the worktree at that directory. The worktree in which the
developer's agent session started, the worktree whose rendered Skill supplied the instructions
and every other linked worktree are not inputs; see
[invocation worktree binding](scenarios.md#scenario.development.invocation-worktree-binding).

### req.development.distinct-outcomes — Results distinguish admission, domain and execution outcomes

A capability result SHALL distinguish admission, domain and execution outcomes instead of collapsing
them into one generic failure.

### req.development.stage-no-skill — Non-public capabilities have no installed Skill

A non-public Capability SHALL have no installed Skill.

### req.development.stage-in-process-only — Non-public capabilities require declared composition

A non-public Capability SHALL be reachable only in-process from a capability that declares it in its
composition.

### req.development.langgraph-control-flow — Orchestration executes as a LangGraph Flow

Every capability's orchestration SHALL execute as a LangGraph Flow of deterministic operations,
Agent invocations and explicitly represented transitions.

Flow is the terminology defined by Harness in [Agent Flows and Loops](../harness/graphs-and-loops.md).

### req.development.single-boundary — Every invocation passes through the host adapter

Every capability invocation SHALL pass through this Module's host adapter, with no direct
agent-to-agent channel bypassing it.
