# Spec MCP server

## Purpose

The Spec MCP server lets an agent ask a project's [Specs](../../glossary.json#concept.spec) which
Modules exist, what one declares, whom a change concerns, whether the Specs validate, and what a
[task type](../../glossary.json#concept.task-type) would let a task read and write: a local,
read-only stdio MCP server rooted at one worktree, usable without knowing Concorde's Python code. It
adds no rule of its own — every answer is Spec core's — is not how workers receive grants, and
enforces nothing; workers have no access to it in this version.

## Core concepts

The **server root** is the one worktree whose Specs the server answers from. It is resolved once,
at session start: `CLAUDE_PROJECT_DIR` when set, otherwise the client's single `file://` root;
without either, or with several roots and no variable, every call fails with `no_root`. It never
moves during the session, and a path resolving outside it — via `..`, an absolute path elsewhere or
a symlink whose target lies elsewhere — is refused with `outside_root`.

Every answer is **Spec core's**: the server loads the Specs of its root through Spec core and
returns what Spec core computes, a [grant](../../glossary.json#concept.grant) with its
[context identity](../../glossary.json#concept.context-identity), a
[Spec context](../../glossary.json#concept.spec-context), an
[impact index](../../glossary.json#concept.impact-index) lookup or the findings of the
[structural checks](../../glossary.json#concept.structural-check), unchanged. A grant it returns is
planning information only, never an authorization.

## Overview

The server is a thin presentation of Spec core: every call that has a root and acceptable
arguments loads a fresh repository and calls the same functions the rest of Concorde uses, trading
speed for never answering from a stale model. A call refused before that, with `no_root`,
`invalid_input` or `outside_root`, loads no Specs.

```d2 illustrative
direction: down
agent: "Agent" {
  call: "Calls a tool"
}
server: "Server program" {
  root: "Server root resolved\nat session start?" {shape: diamond}
  args: "Arguments acceptable\nand inside the root?" {shape: diamond}
  refuse: "Tool error: no_root,\ninvalid_input or outside_root\n(no Specs loaded)" {shape: page}
  error: "Tool error with\nSpec core's code" {shape: page}
  answer: "Spec core's result,\nunchanged" {shape: page}
}
core: "Spec core" {
  load: "Load a fresh repository\nfrom the root"
  compute: "Compute the answer"
  refused: "Refused?" {shape: diamond}
}
agent.call -> server.root
server.root -> server.refuse: no
server.root -> server.args: yes
server.args -> server.refuse: no
server.args -> core.load: yes
core.load -> core.compute -> core.refused
core.refused -> server.error: yes
core.refused -> server.answer: no
```

The server sits inside Spec tooling, between the
[Main session](../../coordination/main-session/module.md) Module, whose main agent calls it, and
the Spec core it presents:

```d2
tooling: Spec tooling {
  mcp: Spec MCP server
  core: Spec core
  mcp -> core
}
session: Main session
session -> tooling.mcp
```

## Using the server

A project using Concorde registers the **Spec MCP server** for Claude Code in its `.mcp.json`:

```json
{
  "mcpServers": {
    "concorde-spec": {
      "command": "concorde",
      "args": ["spec-mcp"],
      "env": {"CLAUDE_PROJECT_DIR": "${CLAUDE_PROJECT_DIR}"}
    }
  }
}
```

| Tool | Returns |
| --- | --- |
| `boundary(modules, task_type)` | The [grant](../../glossary.json#concept.grant) the task type gives the listed Modules: [context identity](../../glossary.json#concept.context-identity) and `{path, level}` entries (`names`, `ro`, `rw`); an unlisted path is denied. |
| `modules()` | The Modules in [registry](../../glossary.json#concept.registry) order. |
| `module(id)` | One [Module](../../glossary.json#concept.module)'s entry, owned documents, relations and realization entries. |
| `context(id)` | One Module's [Spec context](../../glossary.json#concept.spec-context), or that of a scenario's owner, with a digest per member and the selecting relation, and the glossary entries of its terms. |
| `impact(paths)` | Which Modules writing the given documents or files concerns. |
| `validate(target?)` | The [structural checks](../../glossary.json#concept.structural-check)' findings. |

For example, before opening a task the [main agent](../../glossary.json#concept.main-agent) calls
`boundary(["module.checkout"], "implement")` to see what an implementation worker could change, and
`impact(["src/checkout/cart.py"])` to see which other Modules share that file and must be bound too.
When no other Module binds `cart.py`, `boundary` answers with the grant's context identity and its
entries, such as `src/checkout/` at `rw` and the documents the checkout Module's Spec context
selects at `ro`; any path it does not list is denied. When `impact` names a second Module for
`cart.py`, `boundary` for the checkout Module alone is refused with `shared_file` instead, and the
main agent binds that Module to the task as well. Exact results are in the [contracts](contracts.md).

A call fails with a code, never a partial answer: one of the server's own codes `no_root`,
`outside_root`, `invalid_input`, `system_error` and `unexpected_error`, or one of Spec core's codes
such as `protocol_mismatch` or `shared_file`; the [contracts](contracts.md#session) say when each
applies. No tool writes, so a call may be repeated at any time and reads the Specs as they stand.

## Why it is built this way

`CLAUDE_PROJECT_DIR` wins over the client's roots because it is the project directory Claude Code
sets for the session, one directory by construction, while a client may offer several roots and
none of them is marked as the project; the roots are the fallback for a client that sets no
variable, and only when they name exactly one directory.

Rooting at one worktree keeps answers honest across concurrent tasks: a branch may bind a new file
or declare a `uses` the primary lacks, and only its own server sees it. The running Concorde package
must still carry the Protocol the root binds, or calls fail with `protocol_mismatch`.
`validate` alone does not fail then: it loads through the validator, which reports Specs it cannot
load as a finding, so its answer is the `spec-validation` envelope with status `invalid` and one
error finding that describes the mismatch. Confining path arguments to the root keeps a query from
reading or reporting on files of another worktree.

Grants are frozen by the [Operation](../../glossary.json#concept.operation) that launches a worker,
never the server or the worker: the Operation calls Spec core with its workspace as root and writes
the result into the worker's launch configuration, so `boundary` is planning information only, never
an authorization. Workers launch with an empty MCP configuration, so no worker can reach the server,
request a different grant, or learn more than its brief tells it — querying it from review workers
is future work.

The server is read-only by construction — no tool writes, regenerates the registry or opens a
network listener — and success of its `validate` tool is evidence about structure only.

## The server program

```d2
mcp: Spec MCP server {
  server: Server program {
    "src/concorde/spec_mcp/"
  }
}
```

<a id="realization.spec-mcp.server"></a>

**Server program** runs the stdio MCP session, resolves and holds the root, confines path
arguments, maps each tool to Spec core, and turns every failure into a tool error — a small
hand-written JSON-RPC session with no MCP library dependency, tested over a real stdio connection.
The session is written by hand because its wire is small and fully specified: newline-delimited
JSON-RPC carrying `initialize`, `ping`, `tools/list` and `tools/call`, and one `roots/list` request
to the client. An MCP library would add a runtime dependency to every project that installs
Concorde for that much protocol.

## Around it

<a id="uses-spec"></a>

**Spec core** loads the Specs and computes every answer: its
[grants](../../glossary.json#concept.grant) and their
[context identities](../../glossary.json#concept.context-identity) for `boundary`, its
[boundary sets](../../glossary.json#concept.boundary-set) for `context`, its
[impact indexes](../../glossary.json#concept.impact-index) for `impact`, its
[structural checks](../../glossary.json#concept.structural-check) for `validate`, and its
[registry](../../glossary.json#concept.registry) for `modules`/`module`. The server passes on
its own root, confines every path argument, and returns Spec core's result unchanged — a refusal
becomes that failure's code as a tool error, never a partial or cached answer.

Which agents call it is decided by the Main session guidance and each project's `.mcp.json`, not by
the server.
