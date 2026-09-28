# Spec MCP server

## Purpose

The Spec MCP server lets an agent ask a project's Specs which Modules exist, what one declares, whom
a change concerns, whether the Specs validate, and what a
[task type](../../glossary.json#concept.task-type) would let a task read and write: a local,
read-only stdio MCP server rooted at one worktree, usable without knowing Concorde's Python code. It
adds no rule of its own — every answer is Spec core's — is not how workers receive grants, and
enforces nothing; workers have no access to it in this version.

## Usage

<a id="concept.spec-mcp-server"></a>

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
| `boundary(modules, task_type)` | The grant the task type gives the listed Modules: context identity and `{path, level}` entries (`names`, `ro`, `rw`); an unlisted path is denied. |
| `modules()` | The Modules in registry order. |
| `module(id)` | One [Module](../../glossary.json#concept.module)'s entry, owned documents, relations and realization entries. |
| `context(id)` | One Module's [Spec context](../../glossary.json#concept.spec-context), with a digest per member and the selecting relation, and the glossary entries of its terms. |
| `impact(paths)` | Which Modules writing the given documents or files concerns. |
| `validate(target?)` | The structural checks' findings. |

For example, before opening a task the [main agent](../../glossary.json#concept.main-agent) calls
`boundary(["module.checkout"], "implement")` to see what an implementation worker could change, and
`impact(["src/checkout/cart.py"])` to see which other Modules share that file and must be bound too.
Exact results are in the [contracts](contracts.md).

A call fails with a code, never a partial answer: `outside_root`, `no_root`, or one of Spec core's
own codes such as `protocol_mismatch` or `shared_file`. No tool writes, so a call may be repeated at
any time and reads the Specs as they stand.

<a id="concept.server-root"></a>

The **[server root](../../glossary.json#concept.server-root)** is resolved once, at session start:
`CLAUDE_PROJECT_DIR` when set, otherwise the client's single `file://` root; without either, or with
several roots and no variable, every call fails with `no_root`. It never moves during the session,
and a path resolving outside it — via `..`, an absolute path or a symlink — is refused.

## Design

The server is a thin presentation of Spec core: every call loads a fresh repository and calls the
same functions the rest of Concorde uses, trading speed for never answering from a stale model.

```d2
mcp: Spec MCP server {
  server: Server program {
    "src/concorde/spec_mcp/"
  }
  concept: Spec MCP server / Spec MCP server
  server -> concept: implements
}
```

<a id="realization.spec-mcp.server"></a>

**Server program** runs the stdio MCP session, resolves and holds the root, confines path
arguments, maps each tool to Spec core, and turns every failure into a tool error — a small
hand-written JSON-RPC session with no MCP library dependency, tested over a real stdio connection.

Rooting at one worktree keeps answers honest across concurrent tasks: a branch may declare a
pending file or a `uses` the primary lacks, and only its own server sees it. The running Concorde
package must still carry the Protocol the root binds, or calls fail with `protocol_mismatch`.

Grants are frozen by the [Operation](../../glossary.json#concept.operation) that launches a worker,
never the server or the worker: the Operation calls Spec core with its workspace as root and writes
the result into the worker's launch configuration, so `boundary` is planning information only, never
an authorization. Workers launch with an empty MCP configuration, so no worker can reach the server,
request a different grant, or learn more than its brief tells it — querying it from review workers
is future work.

The server is read-only by construction — no tool writes, regenerates the registry, confirms
pending entries, or opens a network listener — and success of its `validate` tool is evidence
about structure only.

### Around it

The server sits inside Spec tooling, between the Main session that calls it and the Spec core it
presents:

```d2
tooling: Spec tooling {
  mcp: Spec MCP server
  core: Spec core
  mcp -> core
}
session: Main session
session -> tooling.mcp
```

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
