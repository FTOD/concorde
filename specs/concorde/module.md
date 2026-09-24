# Concorde Framework

## Purpose

Concorde helps a developer and a main agent change a project that describes itself in
Specs. Spec tooling checks and publishes those Specs and computes what a task may read and write.
Operations carry out bounded jobs, assessing, specifying, implementing, testing, reviewing,
validating and delivering, under Spec-derived permissions, and the main agent stays in charge: it
splits work into tasks, runs Operations and merges what is delivered. Concorde never chooses the
developer's direction or repairs a Spec on its own. The main agent and the workers run on Claude
Code or on pi.

## Terminology

This entry defines no terms of its own. The words every Module shares, including the four kinds of
context and the task types, are defined in the [shared vocabulary](vocabulary.md), which this
Module also owns; read it first. Each child Module defines the words of its own interface, such as
a [Task](tasks/module.md), an [Operation](operations/module.md) or a
[Grant](spec-tooling/spec/module.md).

## Usage

The installer places the Protocol copy under `.concorde/protocol/`, the `concorde` command and the
main-session guidance, but never writes the Specs; initialization proposes and applies an honest
first Spec. The developer then works with the main agent in the primary worktree, opening a task (a
branch and worktree) and running Operations there with `concorde run <operation> --task <task>`:
`understand`, `specify`, `implement`/`test`, `spec_review`/`code_review`, `validate` and `delivery`,
typically ending with the result and its evidence committed on the task branch; the main agent then
merges it, and several tasks may run at once.

Every Operation returns a structured result; a failure carries an
[error chain](vocabulary.md#concept.concorde.error-chain): the Operation's own detailed link saying
why it cannot handle the error, with each error it received nested as a cause with its own reason,
and every `concorde` command refuses in the same shape. The main agent reads the chain, decides what
it can, logs the decision, escalates only a major-impact one, and adds its own link rather than
summarizing. A step needing an unstated promise stops with a Spec gap instead of inferring it from
code; only the developer and the main agent change Specs outside a `specify` task.

| Command | Use it to | Provided by |
| --- | --- | --- |
| `concorde validate` | check the structure of the Specs | [Spec core](spec-tooling/spec/module.md) |
| `concorde grant` | compute a task type's grant for some Modules | [Spec core](spec-tooling/spec/module.md) |
| `concorde spec-mcp` | let an agent query Modules, context and grants over MCP | [Spec MCP server](spec-tooling/spec-mcp/module.md) |
| `concorde task` | open, list and close tasks | [Tasks](tasks/module.md) |
| `concorde run` | run one Operation in a task worktree | [Operations](operations/module.md) |

## Design

The Spec, not the code, is the shared source of truth. Concorde has three actors: the developer
decides; the main agent has the global view and normally does not edit the project itself; workers
do bounded work under a Spec-computed boundary. Between the main agent and the workers, the
Operation host computes the grant, launches and audits the worker, runs the checks and turns the
outcome into a trustworthy result.

Worker permissions are compiled from the grant into the worker's own configuration — on Claude
Code its settings with deny rules, a write hook and the Bash sandbox, on pi a permission extension
with the same sandbox engine — which guard against scope drift and mistakes, not a malicious actor; known
limits are in the [Harness](harness/module.md), reasons in the [design topic](design.md).

The root also binds files of its own, shown with its children in
[Relationships](#relationships):

- <a id="realization.concorde.project-files"></a>**Project files** are what belongs to no single
  responsibility: README, agent instructions, licence, repository configuration and the CI workflow
  that validates this checkout.
- <a id="realization.concorde.user-documents"></a>**User documents** under `docs/` are written for
  the people who use Concorde, starting with the guide to using it. They follow no Spec Protocol
  structure and are never agent context; the docsite publishes them as its
  [user documents](spec-tooling/views/module.md#concept.views.user-docs), the first tab, with
  `docs/README.md` as the site's home page.
- <a id="realization.concorde.development-environment"></a>**Development environment** is this
  checkout's Python project and lock, pytest setup and shared test support, the reference
  initializer, the Claude Code documentation fetcher, the docsite type check, and the tests of that
  environment; see [Development environment](development.md).
- <a id="realization.concorde.error-chain"></a>**Error chain code** is the link type every Module
  shares — schema, reasons, exception helpers and human rendering — whose exact shape is the
  [error contract](contracts.md#contract.concorde.error).
- <a id="realization.concorde.acceptance-tests"></a>**Acceptance tests** exercise the root's
  cross-Module [scenarios](scenarios.md) through the installer and the `concorde` command.

## Relationships

The root contains every other Module and binds the files above; nesting shows both at once:

```d2
root: Concorde Framework {
  spectooling: Spec tooling
  harness: Harness
  tasks: Tasks
  operations: Operations
  issues: Issues
  mainsession: Main session
  distribution: Distribution
  files: Project files {
    "README.md"
    "AGENTS.md"
    "LICENSE"
    "validate-source-checkout.yml"
  }
  userdocs: User documents {
    "docs/"
  }
  devenv: Development environment {
    "pyproject.toml"
    "uv.lock"
    "conftest.py"
    "tests/concorde/development/"
    "init-references.py"
    "fetch-claude-code-docs.py"
    "check-docsite-types.py"
  }
  errors: Error chain code {
    "errors.py"
  }
  acceptance: Acceptance tests {
    "tests/concorde/acceptance/"
  }
}
```

<a id="contains-spec-tooling"></a>

**Spec tooling** maintains and serves Specs — loading, checking, computing boundary sets and
grants, answering agents over MCP, reviewing and publishing them. Every other Module relies on it
to refuse an untrustworthy structure; its core uses no other Module.

<a id="contains-harness"></a>

The **Harness** configures and runs workers — settings, launch, resume, write audit, checks and run
records — so a worker's answer stays a proposal until the host has checked it.

<a id="contains-tasks"></a>

**Tasks** keeps each task's branch, worktree, record and decision log, so several can run side by
side without their changes mixing.

<a id="contains-operations"></a>

**Operations** holds the Operation catalog, the `concorde run` command, the host step runner and the
Operation providers; no provider calls the next one, the main agent chooses.

<a id="contains-issues"></a>

**Issues** keeps durable, branch-local Issue records so a problem worth keeping survives the task
that found it; solving one is ordinary work run through Operations.

<a id="contains-main-session"></a>

The **Main session** Module is the guidance the installer gives the main agent: how to split tasks,
run Operations, read results, keep decision logs and escalate.

<a id="contains-distribution"></a>

**Distribution** builds the package, provides the `concorde` CLI and installs Concorde into a
project.
