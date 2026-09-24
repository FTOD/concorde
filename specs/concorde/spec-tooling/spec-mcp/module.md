# Spec MCP server

## Purpose

The Spec MCP server lets an agent ask a project's Specs which Modules exist, what one declares,
whom a change concerns, whether the Specs validate, and what a task type would let a task read and
write: a local, read-only stdio MCP server rooted at one worktree, usable without knowing
Concorde's Python code. It adds no rule of its own — every answer is Spec core's — is not how
workers receive grants, and enforces nothing; workers have no access to it in this version.

## Terminology

| Term | Definition |
| --- | --- |
| Spec MCP server | The local stdio MCP server that answers read-only queries about the Specs of the one worktree it is rooted at. |
| Server root | The worktree whose Specs answer every query of one server process, fixed when the session starts. |
| [Grant](../spec/module.md#concept.spec.grant) | |
| [Context identity](../spec/module.md#concept.spec.context-identity) | |
| [Boundary set](../spec/module.md#concept.spec.boundary-set) | |
| [Impact index](../spec/module.md#concept.spec.impact-index) | |
| [Structural check](../spec/module.md#concept.spec.structural-check) | |
| [Registry](../spec/module.md#concept.spec.registry) | |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Module](../../vocabulary.md#concept.concorde.module) | |

One server, one root: every answer — grants, context identities, boundary sets, impact indexes,
structural findings — is Spec core's.

## Usage

<a id="concept.spec-mcp.server"></a>

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
| `module(id)` | One Module's entry, owned documents, relations and realization entries. |
| `context(id)` | One Module's Spec context, with a digest per member and the selecting relation. |
| `impact(paths)` | Which Modules writing the given documents or files concerns. |
| `validate(target?)` | The structural checks' findings. |

For example, before opening a task the main agent calls `boundary(["module.checkout"], "implement")`
to see what an implementation worker could change, and `impact(["src/checkout/cart.py"])` to see
which other Modules share that file and must be bound too. Exact results are in the
[contracts](contracts.md).

A call fails with a code, never a partial answer: `outside_root`, `no_root`, or one of Spec core's
own codes such as `protocol_mismatch` or `shared_file`. No tool writes, so a call may be repeated at
any time and reads the Specs as they stand.

<a id="concept.spec-mcp.root"></a>

The **server root** is resolved once, at session start: `CLAUDE_PROJECT_DIR` when set, otherwise the
client's single `file://` root; without either, or with several roots and no variable, every call
fails with `no_root`. It never moves during the session, and a path resolving outside it — via `..`,
an absolute path or a symlink — is refused.

## Design

The server is a thin presentation of Spec core: every call loads a fresh repository and calls the
same functions the rest of Concorde uses, trading speed for never answering from a stale model.

```d2
server: Server program {
  "src/concorde/spec_mcp/"
}
```

<a id="realization.spec-mcp.server"></a>

**Server program** runs the stdio MCP session, resolves and holds the root, confines path
arguments, maps each tool to Spec core, and turns every failure into a tool error — a small
hand-written JSON-RPC session with no MCP library dependency, tested over a real stdio connection.

Rooting at one worktree keeps answers honest across concurrent tasks: a branch may declare a
pending file or a `uses` the primary lacks, and only its own server sees it. The running Concorde
package must still carry the Protocol the root binds, or calls fail with `protocol_mismatch`.

Grants are frozen by the Operation host, never the server or a worker: the host calls Spec core
with the task worktree as root and writes the result into the worker's launch configuration, so
`boundary` is planning information only, never an authorization. Workers launch with an empty MCP
configuration, so no worker can reach the server, request a different grant, or learn more than its
brief tells it — querying it from review workers is future work.

The server is read-only by construction — no tool writes, regenerates the registry, confirms
pending entries, or opens a network listener — and `validate` success is evidence about structure
only.

## Relationships

```d2
server: Server program
core: Spec core
server -> core: answers with
```

<a id="uses-spec"></a>

**Spec core** loads the Specs and computes every answer: its
[grants](../spec/module.md#concept.spec.grant) and their
[context identities](../spec/module.md#concept.spec.context-identity) for `boundary`, its
[boundary sets](../spec/module.md#concept.spec.boundary-set) for `context`, its
[impact indexes](../spec/module.md#concept.spec.impact-index) for `impact`, its
[structural checks](../spec/module.md#concept.spec.structural-check) for `validate`, and its
[registry](../spec/module.md#concept.spec.registry) for `modules`/`module`. The server passes on
its own root, confines every path argument, and returns Spec core's result unchanged — a refusal
becomes that failure's code as a tool error, never a partial or cached answer.

Which agents call it is decided by the Main session guidance and each project's `.mcp.json`, not by
the server.
