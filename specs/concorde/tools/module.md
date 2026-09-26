# Tools

## Purpose

Tools groups the reusable deterministic execution capabilities that Operations and the Workers
host code call to perform specific actions and obtain results. They are the program half of the
bottom of Concorde's five levels, beside the AI workers an Operation launches, and this group gives
the reader one place to find them. Its first child, Check
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

### Its place in the five levels

Tools is the program half of level 5 of the [five levels](../module.md#the-five-levels), beside
the workers that are its agent half. Each level answers a different question: a Workflow orders
Operations; an Operation combines worker jobs and Tool calls into one job; and at the bottom a
worker performs model reasoning while a Tool performs a specific action through programmed logic.
Worker and Tool are peers at that level, and neither calls upward: a Tool never starts an
Operation, a worker or another agent.

```d2
operations: Operations
workers: Workers
tools: Tools {
  checks: Check execution
}
operations -> tools.checks
workers -> tools.checks
```

A Tool is called by programs only. The Operation host, level 4, calls one in a step of its own,
such as Validation running the checks; and the Workers Module, which includes deterministic
management code around its AI processes, calls one from that host code as part of that management,
such as running the checks after a worker's round, on behalf of the Operation that launched the
worker. Every call returns to the step that made it: the result becomes that caller's evidence,
recorded by the host and kept apart from any worker's claims, and a failure comes back as the
Tool's own error link, which the caller puts as a cause under its own link instead of summarizing
it. Belonging to this group makes no Tool available to a worker: Check execution runs outside the
worker process, and a worker sees its result only as far as the host passes it on, such as the log
tail Workers puts into a resume round.

### A composition, not a boundary

Tools is a composition of cohesive Modules, not one combined permission boundary. Consumers keep
explicit dependencies on the concrete Tool they use. Reading this parent does not recursively
select every child's dependencies, and binding a task to this parent does not grant writes to
its children's code or Specs. New reusable execution services belong as children with their own
interfaces and failure rules, rather than as unrelated functions in one shared implementation.
The composition groups execution services for readers while leaving each service's callers,
implementation bindings and guarantees with its own Module, which is why the picture above draws
the callers' dependencies on Check execution itself and none on Tools.

Deterministic describes how the Tool executes, not a guarantee that repeated calls produce equal
outputs: tests, timeouts and external systems can vary. It also does not classify every subsystem
without AI as a Tool. Tasks owns task state, Spec core interprets declarations and Harness applies
agent boundaries; those responsibilities retain their own Modules. Private helpers, such as an
Operation's diff preparation or Workers' audit, remain with their owner unless made into a
separately specified reusable execution service.

### The children

<a id="contains-checks"></a>

**Check execution** supplies the callable check service: it selects configured commands, runs
them within its read-only boundary and returns input-bound results and logs. It is called whenever
an Operation needs to know whether a Module's configured checks pass: by the Workers host code
after a clean audit and between resume rounds, and by Operations such as validation, testing and
code review. It owns the check runner, temporary storage, input measurement and failure reporting.
Its boundary restricts direct filesystem writes outside temporary storage, not reads, network,
host sockets or credentials; measuring inputs before and after the run detects changed inputs and
turns them into a refused result rather than false evidence, and a boundary it cannot establish
refuses the run instead of running a check unconfined. A passing command does not prove that its
checks are sufficient or that the code is correct. As their parent, Tools adds no duty and no
failure reaction of its own: Check execution's callers depend on it directly and handle its
refusals themselves. The child's entry states these limits and its service and boundary documents
specify the precise behaviour.
