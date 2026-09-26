# Tools

## Purpose

Tools groups the reusable deterministic execution capabilities that Operations and the Workers
host code call to perform specific actions and obtain results. It gives the reader one place to
find these capabilities alongside the AI workers used by an Operation. Its first child, Check
execution, runs configured checks and records their results. Each child owns its interface,
implementation and execution boundary; this composite binds no implementation of its own.

## Terminology

| Term | Definition |
| --- | --- |
| [Tool](../vocabulary.md#concept.concorde.tool) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Evidence](../vocabulary.md#concept.concorde.evidence) | |

## Usage

An Operation combines calls to workers and Tools to complete one job. For example, `implement`
asks a worker to change code, then the Workers host code calls Check execution to run the
configured tests. If a check fails, Workers can pass the recorded failure to the worker in a
resume round. The Tool executes the check; the worker reasons about how to repair the code.
`validate` also calls Check execution, without launching an AI worker.

Call the concrete Tool through its documented interface. Tools introduces no generic command,
dispatcher or result envelope: Check execution already supplies a host-side check service, and
its result belongs to the calling Operation's evidence. Users configure the checks and see their
results through Operations; they need not call the internal service themselves.

A worker can use only the tools its Harness exposes. Being a child of Tools does not make a
service available to an AI worker. In particular, Check execution is called by host code outside
the worker process, and its recorded results stay separate from the worker's claims.

## Design

The execution layers answer different questions: a Workflow orders Operations; an Operation
combines worker jobs and Tool calls; a worker performs model reasoning, while a Tool performs a
specific action through programmed logic. Worker and Tool are peers in this execution model.
The Workers Module includes deterministic management code around its AI processes and can call
Tools as part of that management.

Tools is a composition of cohesive Modules, not one combined permission boundary. Consumers keep
explicit dependencies on the concrete Tool they use. Reading this parent does not recursively
select every child's dependencies, and binding a task to this parent does not grant writes to
its children's code or Specs. New reusable execution services belong as children with their own
interfaces and failure rules, rather than as unrelated functions in one shared implementation.

Deterministic describes how the Tool executes, not a guarantee that repeated calls produce equal
outputs: tests, timeouts and external systems can vary. It also does not classify every subsystem
without AI as a Tool. Tasks owns task state, Spec core interprets declarations and Harness applies
agent boundaries; those responsibilities retain their own Modules. Private helpers, such as an
Operation's diff preparation or Workers' audit, remain with their owner unless made into a
separately specified reusable execution service.

## Relationships

```d2
tools: Tools {
  checks: Check execution
}
```

The composition groups execution services for readers while leaving each service's callers,
implementation bindings and guarantees with its own Module.

<a id="contains-checks"></a>

**Check execution** supplies the callable check service: it selects configured commands, runs
them within its read-only boundary and returns input-bound results and logs. It owns the check
runner, temporary storage, input measurement and failure reporting. Its boundary restricts direct
filesystem writes outside temporary storage, not reads, network, host sockets or credentials;
measuring inputs before and after the run detects changed inputs. A passing command does not
prove that its checks are sufficient or that the code is correct. The child's entry states these
limits and its service and boundary documents specify the precise behaviour.
