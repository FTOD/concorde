# Operations, workers and their environment

An Operation is executable behavior with a complete contract; a worker is one fresh agent
execution used by a model-backed Operation. The [Harness Module](module.md) prepares that execution
and checks its result. This distinction lets a graph
combine ordinary code and model work without treating a model's answer as permission to act.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Operation](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Harness](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker profile](module.md#terminology) | Defined in Harness. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

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

Some workers have named helpers for a limited subtask. Helpers use fresh conversations and the
parent's bounded access, cannot delegate again, and report back to the parent. The parent remains
responsible for its submitted result. This is different from a Graph selecting another operation.

## Read next

[Execution](execution.md) explains the worker lifecycle and its actual security limits.
[Permissions](permissions.md) explains how access is narrowed. Exact profiles, task-result types
and helper rules are in the Module's execution reference, not prerequisites for this introduction.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#agents-and-harnesses-operations-and-harnesses).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
