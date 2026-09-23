# Spec MCP server scenarios

Concrete situations of the [Spec MCP server](module.md). Exact tools and results are in the
[contracts](contracts.md).

## Session

### scenario.spec-mcp.configured-session — A Claude Code session connects

- GIVEN a project whose `.mcp.json` registers `concorde spec-mcp` with `CLAUDE_PROJECT_DIR` set to `${CLAUDE_PROJECT_DIR}`
- WHEN a Claude Code session opens in the project's primary worktree
- THEN the server resolves the primary worktree as its root
- AND lists the tools `boundary`, `modules`, `module`, `context`, `impact` and `validate`

### scenario.spec-mcp.client-root — The client's root is used without the variable

- GIVEN a server started without `CLAUDE_PROJECT_DIR`
- WHEN the client reports exactly one `file://` root through `roots/list`
- THEN the server resolves that directory as its root

### scenario.spec-mcp.no-root — Without a root the server answers nothing

- GIVEN a server started without `CLAUDE_PROJECT_DIR` whose client reports no root or several roots
- WHEN any tool is called
- THEN the call fails with `no_root`
- AND no Specs are loaded

## Answers

### scenario.spec-mcp.boundary — Asking for a grant

- GIVEN a root whose Module A binds `src/a/` and uses Module B
- WHEN the client calls `boundary` with Modules `["module.a"]` and task type `implement`
- THEN the result equals the context identity and entries of Spec core's grant for the same root, Module and task type
- AND `src/a/` is listed as `rw` and A's and B's selected documents as `ro`
- BUT no file is written and no grant is stored

### scenario.spec-mcp.boundary-refused — A grant Spec core refuses

- GIVEN a root in which Modules A and D both bind `src/shared.py`
- WHEN the client calls `boundary` with Modules `["module.a"]` and task type `implement`
- THEN the call fails with `shared_file`, naming the file and Module D
- AND no entries are returned

### scenario.spec-mcp.queries — Reading the model

- GIVEN a root with several registered Modules
- WHEN the client calls `modules`, `module` for one of them, `context` for it and `impact` for one of its bound files
- THEN each result equals Spec core's registry records, Module descriptor, Spec context records and binding Modules for the same root
- AND every path in the results is project-relative

### scenario.spec-mcp.validate — Validating through the server

- GIVEN a root whose Specs have one structural error
- WHEN the client calls `validate`
- THEN the result is the `validate` command's envelope with status `invalid` and that finding
- BUT no file is written

### scenario.spec-mcp.current-specs — A Spec change is seen at once

- GIVEN a server that has answered `context` for Module A
- WHEN a document A selects is changed on disk and `context` is called again
- THEN the second result carries the new digest and a different context identity

### scenario.spec-mcp.worktree-answers — Two worktrees answer differently

- GIVEN one server rooted at the primary worktree and one rooted at a task worktree whose Module A declares an additional pending entry
- WHEN both are asked for the `implement` boundary of Module A
- THEN only the task worktree's answer lists the pending entry
- AND the two answers carry different context identities

## Refusals

### scenario.spec-mcp.outside-root — Paths outside the root are refused

- GIVEN a server rooted at a worktree
- WHEN the client calls `impact` with a path containing `..` that leaves the root, an absolute path in another directory, or a path through a symbolic link that points outside the root
- THEN each call fails with `outside_root`
- AND nothing outside the root is read

### scenario.spec-mcp.unloadable-specs — Specs that cannot be loaded

- GIVEN a root whose configuration binds a Protocol other than the running package's
- WHEN any tool other than `validate` is called
- THEN the call fails with `protocol_mismatch`
- AND no partial or earlier answer is returned
