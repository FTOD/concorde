# Spec MCP server requirements

The Module-wide obligations of the [Spec MCP server](module.md). The headings group them by
subject; each requirement belongs to the Module as a whole.

## Root

### req.spec-mcp.one-root — One root per session

The server SHALL answer every query of a session from the Specs of the one server root it resolved
when the session started.

### req.spec-mcp.no-root-no-answer — No root, no answer

The server SHALL fail every tool call with `no_root` when it could resolve no single server root.

### req.spec-mcp.root-confined — Paths stay inside the root

The server SHALL refuse with `outside_root` every path argument that resolves outside the server
root.

A path resolves outside the root through `..` components, an absolute path elsewhere, or a symbolic
link whose target lies elsewhere.

## Answers

### req.spec-mcp.spec-core-answers — Every answer is Spec core's

Every successful tool result SHALL equal what Spec core computes for the server root and the same
arguments.

In particular, `boundary` returns the context identity and entries of Spec core's grant, so the
server adds no rule about what a task may read or write.

### req.spec-mcp.current-sources — Answers reflect the current Specs

The server SHALL load the root's Specs anew for every tool call.

### req.spec-mcp.no-partial-answer — Failures are whole

A tool call whose Specs cannot be loaded or whose request Spec core rejects SHALL return a tool
error carrying Spec core's code and no result.

## Safety

### req.spec-mcp.read-only — The server never writes

The server SHALL NOT create, change or delete any file.

### req.spec-mcp.stdio-only — Local transport only

The server SHALL communicate only through its standard input and output.
