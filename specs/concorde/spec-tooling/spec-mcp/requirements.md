# Spec MCP server requirements

The Module-wide obligations of the [Spec MCP server](module.md). The headings group them by
subject. Each requirement belongs to the [Module](../../glossary.json#concept.module) as a whole.

## Root

### req.spec-mcp.one-root — One root per session

The server SHALL answer every query of a session from the [Specs](../../glossary.json#concept.spec) of the one
server root it resolved when the session started.

### req.spec-mcp.no-root-no-answer — No root, no answer

When the server could resolve no single server root, it SHALL fail every tool call with `no_root`.

### req.spec-mcp.root-confined — Paths stay inside the root

The server SHALL refuse with `outside_root` every path argument that resolves outside the server
root.

A path resolves outside the root through any of these:

- `..` components.
- An absolute path elsewhere.
- A symbolic link whose target lies elsewhere.

## Answers

### req.spec-mcp.spec-core-answers — Every answer is Spec core's

Every successful tool result SHALL equal what Spec core computes for the server root and the same
arguments.

In particular, `boundary` returns the
[context identity](../../glossary.json#concept.context-identity) and entries of Spec core's grant.
The server therefore adds no rule about what a task may read or write.

### req.spec-mcp.current-sources — Answers reflect the current Specs

The server SHALL load the root's Specs anew for every tool call that passes the root and argument
checks.

A call refused before that, with `no_root`, `invalid_input` or `outside_root`, loads no Specs.

### req.spec-mcp.no-partial-answer — Failures are whole

A tool call whose request is rejected, or whose Specs a tool other than `validate` cannot load,
SHALL return a tool error carrying the failure's code and no result.

The failure's code is one of the server's own codes or Spec core's, as the
[contracts](contracts.md#session) list them. For Specs it cannot load, `validate` reports the load
failure the way Spec core's validation result does.
The result has status `invalid` and an error finding that describes the load failure.

## Safety

### req.spec-mcp.read-only — The server never writes

The server SHALL NOT create, change or delete any file.

### req.spec-mcp.stdio-only — Local transport only

The server SHALL communicate only through its standard input and output.
