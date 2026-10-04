# Spec MCP server

## Purpose

The Spec MCP server lets an agent ask a project's [Specs](../../glossary.json#concept.spec) about:

- Which Modules exist.
- What one declares.
- Whom a change concerns.
- Whether the Specs validate.
- What a [task type](../../glossary.json#concept.task-type) would let a task read and write.

The server is a local, read-only stdio MCP server rooted at one worktree.
An agent can use it without knowing Concorde's Python code.
The server adds no rule of its own. Every answer is Spec core's.
The server is not how workers receive grants. The server enforces nothing.
Workers have no access to it in this version.

## Core concepts

The **server root** is the one worktree whose Specs the server answers from.
The server resolves it once, at session start.
When set, `CLAUDE_PROJECT_DIR` supplies the root. Otherwise, the client's single `file://` root
supplies it. Without either, or with several roots and no variable, every call fails with `no_root`.
The server root never moves during the session.
The server refuses with `outside_root` a path that resolves outside it through any of these:

- `..` components.
- An absolute path elsewhere.
- A symlink whose target lies elsewhere.

Every answer is **Spec core's**. The server loads the Specs of its root through Spec core.
The server returns what Spec core computes, unchanged:

- A [grant](../../glossary.json#concept.grant) with its
  [context identity](../../glossary.json#concept.context-identity).
- A [Spec context](../../glossary.json#concept.spec-context).
- An [impact index](../../glossary.json#concept.impact-index) lookup.
- The findings of the [structural checks](../../glossary.json#concept.structural-check).

A grant it returns is planning information only, never an authorization.

## Overview

The server is a thin presentation of Spec core.
Every call that has a root and acceptable arguments loads a fresh repository.
Every such call calls the same functions the rest of Concorde uses.
This trades speed for never answering from a stale model.
A call refused before that, with `no_root`, `invalid_input` or `outside_root`, loads no Specs.

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
[Main session](../../coordination/main-session/module.md) Module and the Spec core it presents.
The Main session Module's main agent calls the server:

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
`boundary(["module.checkout"], "implement")` to see what an implementation worker could change.
Before opening the task, the main agent also calls `impact(["src/checkout/cart.py"])`.
This shows which other Modules share that file and must be bound too.
When no other Module binds `cart.py`, `boundary` answers with the grant's context identity and its
entries.
The entries include `src/checkout/` at `rw` and the documents the checkout Module's Spec context
selects at `ro`. Any path the grant does not list is denied.

When `impact` names a second Module for `cart.py`, `boundary` for the checkout Module alone is
refused with `shared_file` instead. The main agent then binds that Module to the task as well.
Exact results are in the [contracts](contracts.md).

A call fails with a code, never a partial answer.
The code is one of the server's own codes `no_root`, `outside_root`, `invalid_input`, `system_error`
and `unexpected_error`, or one of Spec core's codes.
Spec core's codes include `protocol_mismatch` and `shared_file`.
The [contracts](contracts.md#session) say when each applies.
No tool writes, so a call may be repeated at any time.
Each call reads the Specs as they stand.

## Why it is built this way

`CLAUDE_PROJECT_DIR` wins over the client's roots because it is the project directory Claude Code
sets for the session. This is one directory by construction.
A client may offer several roots. None of them is marked as the project.
Only when the roots name exactly one directory are they the fallback for a client that sets no
variable.

Rooting at one worktree keeps answers honest across concurrent tasks.
A branch may bind a new file or declare a `uses` the primary lacks.
Only its own server sees it.
Unless the running Concorde package carries the Protocol the root binds, calls fail with
`protocol_mismatch`. `validate` alone does not fail then.
The `validate` tool loads through the validator, which reports Specs it cannot load as a finding.
For this mismatch, its answer is Spec core's validation result with status `invalid`.
That answer has one error finding that describes the mismatch.
Confining path arguments to the root keeps a query from reading or reporting on files of another
worktree.

The [Operation](../../glossary.json#concept.operation) that launches a worker freezes grants,
never the server or the worker. The Operation calls Spec core with its workspace as root.
The Operation writes the result into the worker's launch configuration.
Thus, `boundary` is planning information only, never an authorization.
Workers launch with an empty MCP configuration, so no worker can:

- Reach the server.
- Request a different grant.
- Learn more than its brief tells it.

Querying the server from review workers is future work.

The server is read-only by construction. No tool performs any of these actions:

- Writing.
- Regenerating the registry.
- Opening a network listener.

Success of its `validate` tool is evidence about structure only.

## The server program

```d2
mcp: Spec MCP server {
  server: Server program {
    "src/concorde/spec/mcp/"
  }
}
```

<a id="realization.spec-mcp.server"></a>

**Server program** has these responsibilities:

- Running the stdio MCP session.
- Resolving and holding the root.
- Confining path arguments.
- Mapping each tool to Spec core.
- Turning every failure into a tool error.

The program is a small hand-written JSON-RPC session with no MCP library dependency.
The session is tested over a real stdio connection.
The session is written by hand because its wire is small and fully specified.
The wire is newline-delimited JSON-RPC carrying `initialize`, `ping`, `tools/list` and `tools/call`.
The wire also carries one `roots/list` request to the client.
An MCP library would add a runtime dependency to every project that installs Concorde for that much
protocol.

## Around it

<a id="uses-spec"></a>

**Spec core** loads the Specs. Spec core computes every answer:

- Its [grants](../../glossary.json#concept.grant) and their
  [context identities](../../glossary.json#concept.context-identity) for `boundary`.
- Its [boundary sets](../../glossary.json#concept.boundary-set) for `context`.
- Its [impact indexes](../../glossary.json#concept.impact-index) for `impact`.
- Its [structural checks](../../glossary.json#concept.structural-check) for `validate`.
- Its [registry](../../glossary.json#concept.registry) for `modules`/`module`.

The server does the following:

- Passes on its own root.
- Confines every path argument.
- Returns Spec core's result unchanged.

On a refusal, the server returns that failure's code as a tool error, never a partial or cached
answer.

The Main session guidance and each project's `.mcp.json`, not the server, decide which agents call
it.
