# Spec MCP server

## Purpose

The Spec MCP server lets an agent ask questions about a project's Specs while it works: which
Modules exist, what one of them declares and selects, whom a change concerns, whether the Specs
validate, and above all what a task type would allow a task bound to some Modules to read and
write. It is a local server that speaks the Model Context Protocol over standard input and output,
so the main agent, or an agent in any project that uses Concorde, can use it without knowing
Concorde's Python code. It answers only from the Specs of the one worktree it is rooted at, and it
only reads. It adds no rule of its own: every answer is Spec core's. It is not how workers receive
their grants, it enforces nothing, and in this version workers have no access to it.

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

An agent connects to one server, whose root decides every answer; the answers are grants, context
identities, boundary sets, impact indexes and structural findings, all computed by Spec core.

## Usage

<a id="concept.spec-mcp.server"></a>

A project that uses Concorde registers the **Spec MCP server** for Claude Code in its `.mcp.json`:

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

Claude Code starts the command when a session opens and expands `${CLAUDE_PROJECT_DIR}` to the
directory the session was opened in. A main agent in the primary worktree therefore talks to a
server rooted at the primary worktree, and an agent opened in a task worktree to one rooted there.

The server offers six tools. `boundary(modules, task_type)` returns the grant that the task type
gives the listed Modules, as its context identity and a list of `{path, level}` entries with level
`names`, `ro` or `rw`; a path that is not listed is denied. `modules()` lists the Modules in
registry order, `module(id)` returns one Module's entry, owned documents, relations and realization
entries, and `context(id)` its Spec context with a digest per member and the relation that
selected it. `impact(paths)` tells which Modules writing the given documents or files concerns, and
`validate(target?)` runs the structural checks and returns their findings. For example, before
opening a task, the main agent calls `boundary(["module.checkout"], "implement")` to see which
files an implementation worker would be able to change, and `impact(["src/checkout/cart.py"])` to
see which other Modules share that file and must be bound too. The exact results are in the
[contracts](contracts.md).

A tool call fails with a code and a message instead of a partial answer: `outside_root` for a path
outside the root, `no_root` when no root could be resolved, and Spec core's own codes, such as
`protocol_mismatch` when the root's Specs cannot be loaded or `shared_file` when a writable file is
also bound by a Module the request left out. No tool writes a file, so a call can be repeated at
any time; each call reads the Specs as they are at that moment.

<a id="concept.spec-mcp.root"></a>

The **server root** is resolved once, when the client has initialized the session: the directory
named by `CLAUDE_PROJECT_DIR` when it is set, otherwise the single `file://` root the client
reports through the MCP `roots/list` request. Without either, or with several client roots and no
variable, every tool call fails with `no_root`. The root never moves during the session, and a path
argument that resolves outside it, whether through `..`, an absolute path elsewhere or a symbolic
link, is refused.

## Design

The server is a thin presentation of Spec core. It loads a fresh repository from its root for every
call and passes the call to the same library functions the rest of Concorde uses, so an agent sees
exactly what the Operation host and the validator would compute from the same Specs. Loading on
every call trades a little speed for never answering from a stale model, which matters because the
main agent often asks just after a Spec changed.

<a id="realization.spec-mcp.server"></a>

The **Server program** runs the stdio MCP session, resolves and holds the root, confines path
arguments, maps each tool to Spec core and turns every failure into a tool error. It is a small
hand-written JSON-RPC session in `src/concorde/spec_mcp/` with no MCP library dependency, and its
tests exercise it over a real stdio connection to `concorde spec-mcp`.

Rooting the server at one worktree keeps answers honest when several tasks run at once. A task
branch may declare a new pending file or a new `uses` that the primary does not have yet; a server
rooted in that task worktree answers with that change, while the primary's server does not.
Which version of the server code runs does not change what the Specs mean, except that the running
Concorde package must carry the Protocol the root binds; otherwise every call fails with
`protocol_mismatch` rather than answering under other rules.

Grants are frozen by the Operation host, never by the server or a worker. The host calls Spec core
directly with the task worktree as root and writes the result into the worker's configuration at
launch; the server's `boundary` answer is information for planning and never authorizes anything.
Workers are launched with an empty MCP configuration, so in this version a worker cannot reach the
server, cannot ask for a different grant and cannot learn more than its brief tells it. Letting
review workers query the server is future work.

The server is read-only by construction: it offers no tool that writes, it never regenerates the
registry or confirms pending entries, and it opens no network listener. Structural success that
`validate` reports remains evidence about structure only.

## Relationships

```d2
program: Server program
root: Server root
core: Spec core
grant: Spec core / Grant
identity: Spec core / Context identity
program -> root: is rooted at
program -> core: answers with
program -> grant: returns
program -> identity: returns
```

The Server program implements the Spec MCP server concept. The picture shows only what the server
itself does; which agents call it is decided by the Main session guidance and by each project's
`.mcp.json`, not by the server.

<a id="uses-spec"></a>

**Spec core** loads the Specs and computes every answer. The server relies on its
[grants](../spec/module.md#concept.spec.grant) and their
[context identities](../spec/module.md#concept.spec.context-identity) for `boundary`, on its
[boundary sets](../spec/module.md#concept.spec.boundary-set) for `context`, on its
[impact indexes](../spec/module.md#concept.spec.impact-index) for `impact`, on its
[structural checks](../spec/module.md#concept.spec.structural-check) for `validate`, and on its
[registry](../spec/module.md#concept.spec.registry) for `modules` and `module`. The server's duty is
to pass Spec core its own root, never another worktree, to confine every path argument before
calling it, and to return Spec core's result unchanged. When Spec core refuses to load the Specs or
rejects a request, the server returns that failure's code as a tool error and never a partial or
cached answer.
