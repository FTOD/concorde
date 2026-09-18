# Development requirements

These precise specifications belong directly to the [Development Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Operation](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Internal operation](module.md#terminology) | Defined in Development operation host. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Development operation host

### req.development.stage-no-reselect — Bound operations preserve their context

An Operation with bound context selection SHALL NOT reselect or expand the frozen context its composing operation gave it.

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

An operation result SHALL distinguish admission, domain and execution outcomes instead of collapsing
them into one generic failure.

### req.development.stage-no-skill — Non-public operations have no installed Skill

A non-public Operation SHALL have no installed Skill.

### req.development.stage-in-process-only — Non-public operations require declared composition

A non-public Operation SHALL be reachable only in-process from an operation that declares it in its
composition.

### req.development.langgraph-control-flow — Orchestration executes as a LangGraph Graph

Every operation's orchestration SHALL execute as a LangGraph Graph of deterministic operations,
Agent invocations and explicitly represented transitions.

The [Harness Module](../harness/module.md) explains Graph execution in [Graphs and feedback](../harness/graphs-and-loops.md); the term's canonical definition is linked above.

### req.development.single-boundary — Every invocation passes through the host adapter

Every operation invocation SHALL pass through this Module's host adapter, with no direct
agent-to-agent channel bypassing it.
