# Spec MCP server contracts

The exact tools and results of the [Spec MCP server](module.md). They are designed and not yet
implemented. Every path in an argument or a result is a canonical project-relative POSIX path
unless stated otherwise; an absolute path argument is accepted only when it lies inside the server
root and is answered in its project-relative form.

## Session

The server is started as `concorde spec-mcp` and speaks MCP over standard input and output. It
declares the tools capability and no resources or prompts. It resolves its root after the client's
`initialized` notification: `CLAUDE_PROJECT_DIR` when set, otherwise the single `file://` root from
`roots/list`. The root is the real path of that directory and does not change for the life of the
process.

Every tool returns one text content item holding canonical JSON. A failure sets `isError: true`,
and its JSON is `{"code": ..., "message": ...}`:

| Code | When |
| --- | --- |
| `no_root` | no root could be resolved |
| `outside_root` | a path argument resolves outside the root, through `..`, another absolute path or a symbolic link |
| `invalid_input` | an argument is missing, of the wrong type or not a canonical path |
| any Spec core code | loading or the computation failed, for example `protocol_mismatch`, `unsupported_profile`, `invalid_target`, `invalid_task_type`, `unknown_module` or `shared_file` |

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `boundary` | `modules`: nonempty array of Module identities; `task_type`: one of the six task types | the boundary result below |
| `modules` | none | `{"modules": [{"id", "title", "entry", "parent"}]}` in registry order; `parent` is `null` for a root |
| `module` | `id`: a Module identity | `{"id", "title", "entry", "documents", "contains", "uses", "includes", "participates", "realizations", "checks"}`, where `realizations` lists `{"id", "title", "entries", "pending"}` and `checks` the configured check identities |
| `context` | `id`: a Module or scenario identity | `{"module", "context_identity", "sources"}`, with Spec core's source records for the Module, or for the scenario's owner |
| `impact` | `paths`: nonempty array of paths | `{"paths": [{"path", "modules"}], "modules"}`: for a document member the Modules whose Spec context contains it, for any other path the Modules that bind it, and their union |
| `validate` | optional `target`: a Module identity | the envelope of the `validate` command |

`boundary` returns exactly the `context_identity` and `entries` of Spec core's grant for the
server root, the given Modules and the task type. `context` computes its `context_identity` the
same way for its one Module.

```concorde-contract
{
  "id": "contract.spec-mcp.boundary-result",
  "version": 1,
  "schema": {
    "type": "object",
    "required": ["context_identity", "entries"],
    "additionalProperties": false,
    "properties": {
      "context_identity": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
      "entries": {
        "type": "array",
        "uniqueItems": true,
        "items": {
          "type": "object",
          "required": ["path", "level"],
          "additionalProperties": false,
          "properties": {
            "path": {"type": "string", "minLength": 1},
            "level": {"enum": ["names", "ro", "rw"]}
          }
        }
      }
    }
  },
  "semantics": "The grant that one task type gives the listed Modules of the server root: every path the task may know by name, read or write, as a canonical project-relative path sorted by path; a path ending with / covers the files below it, and any path not covered is denied. The context identity names the Spec sources the grant was computed from.",
  "example": {
    "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
    "entries": [
      {"path": "specs/checkout/module.md", "level": "ro"},
      {"path": "specs/checkout/module.md.json", "level": "ro"},
      {"path": "src/checkout/", "level": "rw"}
    ]
  }
}
```

<a id="boundary-participation"></a>

**Participation.** The server provides this contract, version 1, to external callers: the main
agent and agents of other projects. It keeps the result equal to Spec core's grant for the same
root, Modules and task type, and a change to the grant's shape increments the version.
