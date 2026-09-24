# Concorde Framework

## Purpose

Concorde helps a developer and a Claude Code main agent change a project that describes itself in
Specs. Its Spec tooling checks and publishes those Specs, and computes from them exactly what a
task may read and write. Its Operations carry out bounded jobs, such as assessing a Module,
changing its Spec, changing its code, testing or reviewing it, validating a task worktree or
delivering it. Each Operation combines deterministic host steps with headless Claude Code workers
that run under Spec-derived permissions. The main agent stays in charge: it splits work into tasks
with their own worktrees, runs Operations, reads their results and merges what was delivered.
Concorde never chooses the developer's direction and never repairs a Spec on its own. This version
supports only Claude Code; Pi and pi-subagents are not supported.

## Terminology

This entry defines no terms of its own. The words every Module shares, including the four kinds of
context and the task types, are defined in the [shared vocabulary](vocabulary.md), which this
Module also owns; read it first. Each child Module defines the words of its own interface, such as
a [Task](tasks/module.md), an [Operation](operations/module.md) or a
[Grant](spec-tooling/spec/module.md).

## Usage

The developer installs Concorde into a project with the installer, which places the Protocol copy
under `.concorde/protocol/`, the `concorde` command and the main-session guidance, and never writes
the project's Specs. Initialization then proposes an honest first Spec and applies exactly that
proposal. From then on the developer works with the main agent, an ordinary Claude Code session in
the project's primary worktree.

A typical change runs like this. The main agent agrees the direction with the developer and opens
a task: a branch with its own worktree. In that worktree it runs Operations with
`concorde run <operation> --task <task>`: `understand` to assess the Modules involved and plan,
`specify` to change their Specs, `implement` and `test` to change and exercise their code,
`spec_review` and `code_review` for independent review, `validate` to decide readiness and
`delivery` to commit the result with its evidence on the task branch. The main agent then merges
the task branch into the primary branch. Several tasks may run at the same time in their own
worktrees.

Every Operation returns a structured result. When it cannot finish, the result carries an
[error chain](vocabulary.md#concept.concorde.error-chain): the Operation's own detailed account of
the error and why it cannot handle it, with the errors it received from below, such as the worker
run, the worker's own report and the failing checks, nested as its causes, each with its own
reason. Every `concorde` command refuses in the same shape. The main agent reads the whole chain,
decides what it can, records the decision in the task's decision log, and asks the developer only
when a decision has a major impact; then it adds its own link to the chain instead of summarizing
it. When a step needs a promise the Spec does not state, it stops with a Spec gap instead of
inferring it from code; only the developer and the main agent change Specs outside a `specify`
task.

| Command | Use it to | Provided by |
| --- | --- | --- |
| `concorde validate` | check the structure of the Specs | [Spec core](spec-tooling/spec/module.md) |
| `concorde grant` | compute a task type's grant for some Modules | [Spec core](spec-tooling/spec/module.md) |
| `concorde spec-mcp` | let an agent query Modules, context and grants over MCP | [Spec MCP server](spec-tooling/spec-mcp/module.md) |
| `concorde task` | open, list and close tasks | [Tasks](tasks/module.md) |
| `concorde run` | run one Operation in a task worktree | [Operations](operations/module.md) |

## Design

The Spec, not the code, is the shared source of truth between the developer and the agents.
Concorde has three kinds of actors. The developer decides. The main agent has the global view,
works in the primary worktree under no Concorde limits, and normally does not edit the project
itself. Workers do bounded work under a boundary computed from the Specs of the task's worktree.
Between the main agent and the workers stands the Operation host, the deterministic part that
computes the grant, configures and launches the worker, audits what it changed, runs the checks,
and turns the outcome into a result the main agent can trust.

Worker permissions are enforced by the worker's own Claude Code settings: deny rules for the file
tools, a small hook that makes the grant's writable paths the only writable ones, and the Bash
sandbox. These guard against scope drift and mistakes rather than a malicious actor, and their
known limits are stated by the [Harness](harness/module.md). The reasons behind these choices are
in the [design topic](design.md).

<a id="realization.concorde.project-files"></a>

The root binds the **project files** that belong to no single responsibility: README, agent
instructions, licence, repository configuration, the workflow guide under `docs/`, and the CI
workflow that validates this checkout.

<a id="realization.concorde.development-environment"></a>

It binds the **development environment** of this checkout: the Python project and lock, the
pytest configuration and its evidence plugin, shared test support, the reference initializer, the
Claude Code documentation fetcher and the docsite type check, and the tests of that environment,
whose promises are in [Development environment](development.md).

<a id="realization.concorde.error-chain"></a>

It binds the **error chain** shared by every Module: the link type, its schema, the reasons, the
helpers that build links from exceptions and the rendering for a human reader, whose exact shape is
the [error contract](contracts.md#contract.concorde.error), together with its tests.

<a id="realization.concorde.acceptance-tests"></a>

Its **acceptance tests**, under `tests/concorde/acceptance/`, exercise the root's cross-Module
[scenarios](scenarios.md) through the installer and the `concorde` command.

## Relationships

```d2
root: Concorde Framework {
  spectooling: Spec tooling
  harness: Harness
  tasks: Tasks
  operations: Operations
  issues: Issues
  mainsession: Main session
  distribution: Distribution
}
```

Each composite explains its own children: Spec tooling contains the Spec core, the Spec MCP server,
Spec review and Views; the Harness contains Workers and Check execution; Operations contains
Understanding, Specification, Implementation, Code review, Validation and Delivery.

<a id="contains-spec-tooling"></a>

**Spec tooling** is the independent part that maintains Specs and serves them: it loads and checks
them, computes boundary sets and grants, answers agents over MCP, reviews Specs and publishes them
as a site. Every other Module relies on it to refuse a structure that cannot support a trustworthy
boundary. Its core uses no other Module.

<a id="contains-harness"></a>

The **Harness** configures and runs workers: it turns a grant into worker settings, launches and
resumes workers, audits their writes, runs configured checks outside them and keeps run records.
The Framework relies on it so that a worker's answer stays a proposal until the host has checked it.

<a id="contains-tasks"></a>

**Tasks** keeps each task's branch, worktree, record and decision log. The main agent relies on it
to run several tasks side by side without their changes mixing.

<a id="contains-operations"></a>

**Operations** holds the Operation catalog, the `concorde run` command and the host step runner,
and contains the Operation providers. No provider calls the next Operation; the main agent chooses.

<a id="contains-issues"></a>

**Issues** keeps durable, branch-local Issue records and their bookkeeping. A problem worth keeping
survives the task that found it; solving an Issue is ordinary work the main agent runs through
Operations.

<a id="contains-main-session"></a>

The **Main session** Module is the guidance the installer gives the main agent: how to split tasks,
run Operations, read results, keep decision logs and escalate.

<a id="contains-distribution"></a>

**Distribution** builds the package, provides the `concorde` command-line interface and installs
Concorde into a project.
