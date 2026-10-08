# Spec MCP server contracts

The exact tools and results of the [Spec MCP server](module.md). Unless stated otherwise, every
path in an argument or a result is a canonical project-relative POSIX path. Only when an absolute
path argument lies inside the server root is it accepted. An accepted absolute path argument
is answered in its project-relative form.

## Session

The server is started as `concorde spec-mcp`. The server speaks MCP over standard input and output,
as newline-delimited JSON-RPC 2.0. It supports the MCP revisions `2025-06-18`, `2025-03-26` and
`2024-11-05`. The `initialize` result names the revision the client requested when the server
supports it. Otherwise, the result names the newest of the three, and a client that cannot use it
ends the session, as MCP's version negotiation says. The result declares the tools capability and
no resources or prompts.

After the client's first `initialized` notification, the server resolves its root once:

- When set, `CLAUDE_PROJECT_DIR` provides the root. The server sends no `roots/list`.
- Otherwise, when the client declared the roots capability in `initialize`, the server sends one
  `roots/list` request. The root is the one `file://` root of the reply, when the reply lists
  exactly one root and that root is a `file://` URI.
- Otherwise, the session has no root. Every tool call then fails with `no_root`, whose message
  says which case applied:
  - The client declared no roots capability.
  - The reply is a JSON-RPC error.
  - The reply lacks a `roots` list.
  - The list holds no root, several roots or one root that is not a `file://` URI.

The server waits for the reply to `roots/list` without a time limit. Requests that arrive
meanwhile are answered, in their order, once the reply has arrived. When the input ends before the
reply, the session ends. The root is the real path of the chosen directory. The root does not
change for the life of the process. A later `initialized` notification resolves nothing. A
malformed message never ends the session. When the server cannot answer a request, it answers with
a JSON-RPC error and reads the next message.

Every tool returns one text content item holding canonical JSON. A failure sets `isError: true`.
Its JSON is `{"error": <record>}`, where the record is Spec tooling's
[error record](../spec/errors.md#the-error-record). The record contains:

- The code.
- A concrete message.
- The location (the argument as `field`, the path or identity concerned).
- The reason.
- The remediation.
- Every cause.

| Code | When |
| --- | --- |
| `no_root` | no root could be resolved; the message says why: no roots capability, a refused or malformed `roots/list` reply, the number of client roots, a root that is not a `file://` URI, or a root that is not a directory |
| `outside_root` | a path argument resolves outside the root, through `..`, another absolute path or a symbolic link; the message names what it resolved to |
| `invalid_input` | the call's params or its `arguments`, when present, are not an object, an argument is missing or of the wrong type (an optional argument given as `null` among them), the tool is unknown or its name is not a string, or a path names the root itself; the message names the argument and the value |
| `system_error` | the operating system refused to read the [Specs](../../glossary.json#concept.spec); the cause names the path |
| `unexpected_error` | a defect of the server; the record names where it was raised |
| any Spec core code | loading or the computation failed, for example `protocol_mismatch`, `unsupported_profile`, `invalid_target`, `invalid_task_type`, `unknown_module`, `shared_file` or `installed_file`, with Spec core's record unchanged |

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `boundary` | `modules`: nonempty array of [Module](../../glossary.json#concept.module) identities; `task_type`: one of the eight [task types](../../glossary.json#concept.task-type) | the boundary result below |
| `modules` | none | `{"modules": [{"id", "title", "entry", "parent"}]}` in registry order; `parent` is `null` for a root |
| `module` | `id`: a Module identity | `{"id", "title", "entry", "documents", "contains", "uses", "includes", "participates", "realizations"}`, where `realizations` lists `{"id", "title", "entries"}`; a Module's [configured checks](../../glossary.json#concept.configured-check) are Check execution's and not listed |
| `context` | `id`: a Module or scenario identity | `{"module", "context_identity", "sources", "terms"}`, with Spec core's [source and term records](../spec/contracts.md#spec-context-records) for the Module, or for the scenario's owner |
| `impact` | `paths`: nonempty array of paths | `{"paths": [{"path", "modules"}], "modules"}`: for a document member the Modules whose [Spec context](../../glossary.json#concept.spec-context) contains it, for the glossary the Modules that have terms, for any other path the Modules that bind it, and their union |
| `validate` | optional `target`: a Module identity | Spec core's [validation result](../spec/contracts.md#validation-result), as `validate_repository` returns it, with `tool` `spec-validation`: without the update findings the `spec-validation` command adds in a project a `concorde update` marked, whose mark it never touches; Specs that cannot be loaded, such as a `protocol_mismatch`, give status `invalid` with one error finding describing the failure and its record as `result.load_error`, not a tool error |

`boundary` returns exactly the `context_identity` and `entries` of Spec core's grant for:

- The server root.
- The given Modules.
- The task type.

`context` computes its `context_identity` the same way for its one Module.

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

**Participation.** The server provides this contract, version 1, to external callers: the
[main agent](../../glossary.json#concept.main-agent) and agents of other projects. The server keeps
the result equal to Spec core's grant for the same root, Modules and task type.
A change to the grant's shape increments the version.
