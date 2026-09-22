# Operations, workers and their environment

An Agent is a callable native Pi role; a worker is one fresh bounded role execution. Native Workflows
order Agent calls; an Operation is a separately selected typed StateGraph boundary. The [Harness Module](module.md) prepares that execution
and checks its result. This distinction lets a graph
combine ordinary code and model work without treating a model's answer as permission to act.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Harness](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker profile](module.md#terminology) | Defined in Harness. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |

## One bounded job

A caller chooses an operation and supplies its task. The host determines the allowed information,
tools and files, then starts a fresh worker. The worker returns a result for that job; it does not
inherit the previous worker's conversation. Only explicitly accepted results pass to the next step.

For example, a planner receives specifications and produces a plan. The programmer later receives
accepted tasks and the allowed implementation files. Sharing a change does not give the planner
those code files or let the programmer rewrite the specifications it is meant to implement.

## Why configuration and permission are different

Model choice and reasoning time affect how a job is performed. They do not decide what the worker
may read or change. The host checks both the declared maximum permissions and this particular job's
allowed scope before launch, then rejects a result that does not match the job.

Workers are terminal nodes: they do their own admitted work, never delegate or recursively call
capabilities. Authored native workflows own their model ordering; optional StateGraphs own only
their explicitly selected composition. Outer task-session delegation limits do not
become cross-runtime depth requirements for these leaves.

## Read next

[Execution](execution.md) explains the worker lifecycle and its actual security limits.
[Permissions](permissions.md) explains how access is narrowed. Canonical role definitions are in [Agents](../agents/module.md); task-result types
and terminal-worker mechanisms are in Harness's execution reference, not prerequisites for this introduction.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#agents-and-harnesses-operations-and-harnesses).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
