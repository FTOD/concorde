# Distribution contracts

This document describes:

- The [part registration](../glossary.json#concept.part-registration) every part gives Distribution.
- The parts index the build records.
- The [build manifest](../glossary.json#concept.build-manifest) the build records.
- The session and call protocol of the
  [project MCP server](../glossary.json#concept.project-mcp-server).
- The exact results that [Distribution](module.md)'s installer and `concorde update` print when
  they succeed.

When they succeed, both print one JSON object on standard output. Both then exit with status 0.
Every refusal instead prints `{"error": <link>}`, as [Refusals](module.md#refusals) describes.
Every refusal exits with status 1. Paths are
relative to the project root unless stated otherwise.

## Part registration

Every part declares one registration. The registration is plain data in the file `registration.json`
of the part's own directory of `src/concorde/`. Distribution reads the registration without importing
anything. An entry is a Python attribute named `<module>:<attribute>`. The module is relative to the
part's own package, so that an entry never leaves its part. Distribution imports a part's code only
through the entries of an installed part's registration. The table describes what each kind of entry
is called with and answers:

| Entry | Called with | Answers |
| --- | --- | --- |
| a command's `entry` | the rest of the command line, as a list of words, and the project root the global `--project-root` names (default `.`) | with `output` `own`, its exit status, having printed its own output; with `envelope`, Spec core's [shared envelope](../spec-tooling/spec/contracts.md), which `concorde` prints and exits with |
| an MCP tool's `entry` | the [call object](#contract.distribution.mcp-call): `tool`, `arguments`, the session's provenance `primary`, `where`, `session` and `channel`, how the server routed it (`served`), and `long_work` for a call of a tool registered as long work | the [tool answer](#contract.distribution.mcp-answer): `{"value": …}` or `{"error": <link>}`, with `watch` (a `concorde` command the server runs and wakes the session with), and for long work `handover` (the command the call's process becomes, with the locked descriptors it hands on) and `work` (what the server watches of it), as [Project MCP server](#project-mcp-server) describes |
| `mcp_definitions` | nothing: it is a mapping | each of the part's tool names mapped to its `description` and `inputSchema`, as `tools/list` gives them |
| `renders` | the checkout root the build renders | `{"files": {<path>: {"content", "sources"}}}`, outputs under `generated/`, or `{"refusal": {"code", "message"}}` |
| `install.prepare` | the package root and the project root, before the installer writes anything | `{"files": {<project path>: <bytes>}}` to place, or `{"refusal": {"code", "message"}}`, which refuses the install with that code |
| `install.bind` | the project root, after the receipt was written | `null`, or Spec core's [error record](../spec-tooling/spec/errors.md#contract.spec.error), which the install result carries as `binding_error` |
| `idle_check` | the project root | a list of strings, each describing work of the part still running, empty when idle |
| `after_update` | the project root | the part's open tasks, a list of `{id, branch, worktree}` objects, which the update result lists under `open_tasks` after those of earlier parts in the order of the parts table |

```concorde-contract
{
  "id": "contract.distribution.part-registration",
  "version": 5,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["part", "module", "depends_on", "loads", "commands", "mcp_tools", "mcp_definitions", "mcp_instructions", "typed_types", "guidance", "renders", "install", "idle_check", "after_update"],
    "properties": {
      "part": {"type": "string", "pattern": "^[a-z][a-z ]*[a-z]$"},
      "module": {"type": "string", "pattern": "^module\\.[a-z][a-z0-9-]*$"},
      "depends_on": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[a-z][a-z ]*[a-z]$"}},
      "loads": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*(\\.[a-z_][a-z0-9_]*)*$"}},
      "commands": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["name", "entry", "output"],
          "properties": {
            "name": {"type": "string", "pattern": "^[a-z][a-z-]*$"},
            "entry": {"$ref": "#/$defs/entry"},
            "output": {"enum": ["own", "envelope"]}
          }
        }
      },
      "mcp_tools": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["name", "entry", "worktree", "long_work", "threaded", "requires"],
          "properties": {
            "name": {"type": "string", "pattern": "^[a-z][a-z_]*$"},
            "entry": {"$ref": "#/$defs/entry"},
            "worktree": {"enum": ["primary", "session"]},
            "long_work": {"type": "boolean"},
            "threaded": {"type": "boolean"},
            "requires": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[a-z][a-z ]*[a-z]$"}}
          }
        }
      },
      "mcp_definitions": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/entry"}]},
      "mcp_instructions": {"type": ["string", "null"], "minLength": 1},
      "typed_types": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "guidance": {
        "oneOf": [
          {"type": "null"},
          {
            "type": "object",
            "additionalProperties": false,
            "required": ["skill", "task_session", "claude_md"],
            "properties": {
              "skill": {"$ref": "#/$defs/section"},
              "task_session": {"$ref": "#/$defs/section"},
              "claude_md": {"$ref": "#/$defs/section"}
            }
          }
        ]
      },
      "renders": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/entry"}]},
      "install": {
        "type": "object",
        "additionalProperties": false,
        "required": ["files", "defaults", "gitignore", "permissions", "programs", "python_dependencies", "prepare", "bind"],
        "properties": {
          "files": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*/?$"}},
          "defaults": {"type": "object", "additionalProperties": {"type": "string"}},
          "gitignore": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
          "permissions": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
          "programs": {"type": "array", "uniqueItems": true, "items": {"enum": ["d2", "pi-runtime"]}},
          "python_dependencies": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
          "prepare": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/entry"}]},
          "bind": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/entry"}]}
        }
      },
      "idle_check": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/entry"}]},
      "after_update": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/entry"}]}
    },
    "$defs": {
      "entry": {"type": "string", "pattern": "^[a-z_][a-z0-9_]*(\\.[a-z_][a-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*$"},
      "section": {"oneOf": [{"type": "null"}, {"type": "string", "pattern": "^generated/[a-z0-9_./-]+\\.md$"}]}
    }
  },
  "semantics": "The registration of one part, the file registration.json of its directory of src/concorde/. part is its installer name and module the top-level Module the part is made of; the part carries the version of the package it was built from, the same for every part, which concorde.json names. depends_on names the parts it depends on; the installer installs them with it, and no other part is required for it to work. loads names the part's modules that register what its code provides when they load (typed value types, trace roots, Operation and command definitions, workflows), which Distribution imports for every installed part before it routes a command of a part, answers an MCP tool or renders the build. commands are the concorde subcommands it adds, each routed to its entry, which prints its own output or, with output envelope, answers Spec core's shared envelope for concorde to print. mcp_tools are the tools the project MCP server presents for it, each answered by its entry in a fresh process of the primary worktree's concorde, or of the session's own worktree's when worktree is session, under the protocol of contract.distribution.mcp-call and contract.distribution.mcp-answer; long_work allows it to take locks without waiting and become the work it starts, handing them on; threaded serves its calls on a thread of their own, for calls that wait; requires names parts without which the tool is not presented. mcp_definitions names the mapping from each of its tool names to its description and inputSchema, and mcp_instructions the sentence it adds to the server's instructions. typed_types lists the typed value types its code registers. guidance names the part's guidance sections, or is null when it has none: skill its section of the project skill, task_session its section of the task-session prompt and claude_md its section of the CLAUDE.md block, each the build-relative path of a rendered section, generated/<path> rendered from prompts/<path>, or null when the part contributes no section of that kind; Distribution composes each kind from the sections of a set of parts, Coordination's first and the others in the order of the parts table. renders names the entry through which the build renders the part's own outputs, such as the workflow part's Claude Code workflows. install lists what the installer places for it: files names, relative to the package and to the Framework copy alike, the files the part ships beside its code directory src/concorde/<directory>/, which is always shipped, a path ending with / naming a whole directory, such as the spec part's protocol/ or the worker harness's scripts/available_models.py; defaults the Concorde-owned defaults written where absent, by project path; gitignore its .gitignore lines; permissions the Claude Code permission rules a placed workflow needs, added only when a workflow is placed; programs the programs it needs placed, d2 or pi-runtime; python_dependencies the runtime dependencies of the package's pyproject.toml its code imports, which the installer places, from uv.lock, only where an installed part names one; prepare names the service deciding, before any write, the files it places or refusing the install, and bind the service binding the installed files after the receipt. idle_check names the function reporting the part's work still running in the project, as a list of descriptions, or null when it has none; after_update the function reporting the part's open tasks for the update result's open_tasks, each {id, branch, worktree}, or null. An idle_check or after_update entry that raises or answers anything else is refused with part_failed. Every entry is <module>:<attribute> relative to the part's own package. A behaviour or field change increments the version.",
  "example": {
    "part": "coordination",
    "module": "module.coordination",
    "depends_on": ["kernel"],
    "loads": ["tasks.store"],
    "commands": [{"name": "task", "entry": "tasks.cli:main", "output": "own"}],
    "mcp_tools": [
      {"name": "task_show", "entry": "tasks.tools:answer", "worktree": "primary", "long_work": false, "threaded": false, "requires": []},
      {"name": "run_result", "entry": "tasks.tools:answer", "worktree": "primary", "long_work": false, "threaded": false, "requires": ["execution"]},
      {"name": "task_merge", "entry": "tasks.tools:answer", "worktree": "primary", "long_work": true, "threaded": false, "requires": []}
    ],
    "mcp_definitions": "tasks.tools:TOOLS",
    "mcp_instructions": "Tasks: task_show reads a task; task_merge starts its merge without waiting.",
    "typed_types": ["concorde-task-trace"],
    "guidance": {
      "skill": "generated/main-session/skill.md",
      "task_session": "generated/main-session/task-session.md",
      "claude_md": "generated/main-session/claude-md.md"
    },
    "renders": null,
    "install": {
      "files": [],
      "defaults": {},
      "gitignore": [".concorde/tasks/", ".concorde/history/", ".concorde/workspace.json", ".claude/worktrees/"],
      "permissions": [],
      "programs": [],
      "python_dependencies": [],
      "prepare": null,
      "bind": null
    },
    "idle_check": null,
    "after_update": "tasks.update:open_tasks"
  }
}
```

The installer resolves the parts to install by following `depends_on` from the parts named.
Before any write, the installer refuses:

- A name no registration of the package carries.
- A set whose dependencies name a part the package does not build.

Two parts registering the same command or tool
name are a build error, never resolved by order.

When any of these conditions holds, an `idle_check` or `after_update` entry is refused with
`part_failed`, reason `environment`:

- The entry cannot be imported.
- The entry raises.
- The entry answers anything but the list its row names.

The refusal's detail names:

- The part.
- The entry.
- What went wrong.

When the entry raised, the refusal's cause is the link of the entry's exception.
A failing `idle_check` refuses the install before any write, so the project is left as it was.
A failing `after_update` refuses the update after these steps:

- The update installed.
- The update rebound the [Protocol binding](../glossary.json#concept.protocol-binding).
- The update wrote its mark.

The installation, the binding and the mark stay, so only the update result is lost.

The build records what every part of the package registers in the **parts index**
`generated/parts.json`. The parts index has this form:
`{"schema_version": 1, "parts": {<part>: {"module", "depends_on",
"commands", "mcp_tools"}}}`.
This lets a project's `concorde` and [project MCP server](../glossary.json#concept.project-mcp-server)
name the part of a command or tool that is not installed.
They can do this without reading that part's registration.
In a source checkout, the installed parts are every part the package builds.
In a project, the installed parts are the parts the receipt names under `parts`.
That field is an object whose keys are the part names.
When the receipt names none, every part is installed. Distribution is installed with any part.

## Project MCP server

This section describes the host of the [project MCP server](../glossary.json#concept.project-mcp-server).
It covers the host's session with Claude Code and the protocol between the host and the process
that answers each call.
[Serving a call](module.md#serving-a-call) explains why it works this way.

### Session

The server is started as `concorde project-mcp [--name <name>]`.
The `<name>` is the name it is registered under, `concorde` by default.
The server speaks MCP over standard input and output as newline-delimited JSON-RPC 2.0.
Each line holds one message. The server answers these requests:

- `initialize`
- `ping`
- `tools/list`
- `tools/call`

For any other request, the server answers with the JSON-RPC error `-32601`.
For a line that is no JSON, it answers with the error `-32700` and a `null` identity.
It answers no notification or response.
When the client's `protocolVersion` is one of these values, the server answers `initialize` with
that value:

- `2025-06-18`
- `2025-03-26`
- `2024-11-05`

Otherwise, it answers with `2025-06-18`. The answer also contains:

- The `serverInfo` `{"name": "concorde", "version": "1"}`.
- The capabilities `{"tools": {"listChanged": true}, "experimental": {"claude/channel": {}}}`.
- The server's instructions.

The instructions are the server's own paragraph followed by the `mcp_instructions` of every
installed part in the order of the parts table. The current code gives these instructions at that
moment. They stay the session's instructions until the session ends.

At start the server finds these once:

- **The project** is the primary worktree. It is the parent of the Git common directory of the
  folder `CLAUDE_PROJECT_DIR` names. When that variable is unset, the server uses its working
  directory instead. Outside a Git repository, the server has no project. In that case,
  `tools/list` answers no tool. The server refuses every call with `no_project`.
- **The session** it serves is `CLAUDE_CODE_SESSION_ID`. When that variable is unset, the server
  serves no session.
- **The session's folder** is `CLAUDE_PROJECT_DIR` or else the server's working directory.
  **The session's worktree** is the Git worktree that folder lies in. When the folder lies in no
  Git worktree, the session's worktree is the primary worktree. For a
  [task session](../glossary.json#concept.task-session), it is a task worktree.
- **Whether the session listens to it as a channel** depends on `CONCORDE_CHANNEL` when that
  variable is `1` or `0`. Otherwise, when one of the server's ancestor processes up to eight
  levels up is an interactive Claude Code, the session listens as a channel.
  Such a process meets these conditions:
  - Its program is `claude` or `claude.exe`. The program is the file name of the first word of
    its command line.
  - Its standard input is a terminal (`/dev/pts/…` or `/dev/tty…`).
  - Its command line has `server:<name>` among the whitespace-separated entries of a word after
    `--dangerously-load-development-channels` or `--channels` and before the next word starting
    with `--`.
  Claude Code tells a server neither whether it loaded the server as a channel nor whether an
  event was delivered. Because Claude Code gives neither fact, this detection is the server's
  only knowledge of whether the session listens as a channel. An organization that disables
  channels leaves the server believing it has one.

Every tool result is one `text` content item holding one JSON value.
The JSON value is the answer's `value`, or `{"error": <link>}` for a refusal.
For a refusal, `isError` is true.

### Calls

The server runs none of its tools itself. It runs the `concorde` of a worktree.
It chooses the program in this order:

- When the worktree's `.concorde/bin/concorde` exists, it runs that program.
- Otherwise, when the worktree's `scripts/concorde.py` exists, it runs that script with the
  server's Python.
- Otherwise, it runs the server's own package as `python -m concorde`.

The server runs the program from that worktree with the server's environment.
It uses the program in two ways. These are its own interface with the Concorde it presents,
never commands for anyone else:

- `concorde project-mcp --tools` of the primary worktree prints one JSON object with these fields:
  - `tools` lists every tool the installed parts register whose `requires` are all installed,
    in the order of the parts table. Each tool is `{name, description, inputSchema}` as
    `tools/list` gives it.
  - `digest` is `sha256:` followed by the hexadecimal SHA-256 of `tools` written as compact JSON
    with sorted keys.
  - `serving` gives these fields from each tool's registration:
    - `worktree`
    - `long_work`
    - `threaded`
  - `instructions` gives the instructions.
  The server answers `tools/list` with this object. When the process prints no such object,
  the server answers with no tool. When a call names a tool its last listing lacks, the server
  also fetches the object to learn how the tool is served. It then gives the session nothing.
- `concorde project-mcp --call <tool>` of the worktree the tool is served in answers one call.
  For `primary`, this is the primary worktree. For `session`, this is the session's worktree.
  The process performs these steps:
  - It reads the [call object](#contract.distribution.mcp-call) without `tool` as one JSON object
    on its standard input.
  - It loads the installed parts' registering code.
  - It calls the tool's entry with the call object.
  - It prints one JSON line on its standard output.
  The line holds the entry's [answer](#contract.distribution.mcp-answer) without `handover`,
  with `tools`, the digest of this code's tools. The server reads the last output line that is
  a JSON object with any of these fields:
  - `value`
  - `error`
  - `reroute`

The server routes a call as its last listing says the tool is served.
When the server does not find the tool there, it routes the call with these settings:

- In the primary worktree.
- Without long work.
- On the session's thread.

The call's process compares the call object's `served` with its own registration of the tool.
When they differ, the process runs nothing. Instead, it prints
`{"reroute": <serving>, "tools": <digest>}`, with `serving` as `--tools` gives it.
For that reroute, the server takes that serving as its own. It routes the call again, once.
When the tool is now served `threaded`, the server routes the call on a thread of its own.

A call of a tool served `threaded` is answered on a thread of its own.
Every other call is answered on the thread that reads the session, in the order it arrives.
The `--tools` process and the process of every call but long work may take 300 seconds.
After 300 seconds, the process is stopped. The call is then refused with `call_failed`.
A `workflow_step` call waits at most 100 seconds, so it fits in that time limit.
When an answer's `tools` differs from the digest of the listing the server last gave its session,
the server performs these actions:

- It sends `notifications/tools/list_changed`.
- It takes that digest as listed.
- It answers its next `tools/list` with the current tools.

### Waits and long work

An answer's `watch` asks the server to run `concorde <words>` of the primary worktree, from the
primary worktree. The process is tied to the server. When the server ends, the operating system
ends the process. The tool's value gains `wait`, the server's identity of that wait. This identity
is a decimal string counted from 1 in each server. When the process ends and the server has not
begun to end, the server sends a channel event. The event's `meta` is the watch's `meta` with
`wait` and `event`. The event follows these cases:

- When the process printed one JSON value and exited with status 0, the event is `wait_done`
  with the printed answer.
- When the process printed `{"error": <link>}`, the event is `wait_failed` with the refusal and
  its `code`.
- Otherwise, the event is `wait_failed` with a `call_failed` link.

The process of a call of a `long_work` tool runs in a process session of its own. Its standard
error goes to a file in a private temporary directory of the server. The call object's
`long_work` names that file under `call`. Once the entry has taken the locks the work needs without
waiting, the entry answers with `handover` and `work`. The process then takes these steps:

- It writes its answer line through a copy of its standard output that the change of program
  closes.
- It sends its standard output to the handover's `output`.
- It sends its standard error to the handover's `messages`.
- It reads standard input from the null device.
- It leaves the handover's `descriptors` open across the change of program, as
  [Handing a lock on](../kernel/tracing/contracts.md#handing-a-lock-on) states.
- It replaces itself with the handover's `argv` in its `environment`.

When the operating system refuses that replacement, the process takes these steps:

- It removes these files and folder again:
  - The `output` file.
  - The `messages` file.
  - The handover's `folder`.
- It prints a second line refusing the call with `start_failed`.
- It exits. This releases the locks.

The server never holds a lock.

The server reads the long-work call's output until the output ends. The change of program makes
the output end. The server then watches the work's process. When all these conditions hold,
the server sends a channel event:

- The work's process ends.
- The session has a channel.
- The server has not begun to end.

The event's content names the work's `command` and exit status. The content carries at most 6000
characters of the work's `output`. The event's `meta` is the work's `meta` with these attributes:

- `event`, the work's `event` or `work_ended`.
- `exit_code`.
- `status`, as follows:
  - When the output is `{"error": <link>}`, the status is `refused`.
  - Otherwise, for exit status 0, the status is `ok`.
  - Otherwise, for any other exit status, the status is `failed`.

When the `output` file is gone and the work names `locate`, the server takes these steps:

- It runs `concorde <locate>` of the primary worktree for at most 60 seconds.
- It reads the work's files, `output` and `messages`, where the command's answer's `attempt`
  names them.

A channel event is the notification `notifications/claude/channel` with `params`
`{"content": <text>, "meta": {<name>: <string>}}`. When its session ends, the server takes these
steps:

- It ends every wait it still watches.
- It sends no further event.

Long work goes on and keeps its locks until it ends.

```concorde-contract
{
  "id": "contract.distribution.mcp-call",
  "version": 1,
  "schema": {
    "type": "object",
    "required": ["tool", "arguments", "primary", "where", "session", "channel", "served"],
    "additionalProperties": false,
    "properties": {
      "tool": {"type": "string", "minLength": 1},
      "arguments": {},
      "primary": {"type": "string", "minLength": 1},
      "where": {"type": "string", "minLength": 1},
      "session": {"type": ["string", "null"]},
      "channel": {"type": "boolean"},
      "served": {
        "type": "object",
        "required": ["worktree", "long_work", "threaded"],
        "additionalProperties": false,
        "properties": {
          "worktree": {"enum": ["primary", "session"]},
          "long_work": {"type": "boolean"},
          "threaded": {"type": "boolean"}
        }
      },
      "long_work": {
        "type": "object",
        "required": ["call"],
        "additionalProperties": false,
        "properties": {"call": {"type": "string", "minLength": 1}}
      }
    }
  },
  "semantics": "The call object an MCP tool's entry is called with. The server writes it, without tool, to the standard input of concorde project-mcp --call <tool>, whose process adds tool, the name the call is for. arguments are the tools/call arguments as the session gave them, unchecked: the entry checks them against its input schema. primary is the absolute path of the primary worktree; where the session's folder, CLAUDE_PROJECT_DIR or else the server's working directory; session the Claude Code session the server serves, CLAUDE_CODE_SESSION_ID, or null; channel whether the server judged its session a channel. served is how the server routed the call, which the call's process compares with its own registration of the tool before anything runs. long_work is present only for a call routed as long work and names under call the file receiving the call's process's standard error until it becomes the work. A behaviour or field change increments the version.",
  "example": {
    "tool": "task_merge",
    "arguments": {"task": "fix-checkout"},
    "primary": "/home/dev/shop",
    "where": "/home/dev/shop",
    "session": "4f6c2a1e-8b3d-4c5e-9f70-1a2b3c4d5e6f",
    "channel": true,
    "served": {"worktree": "primary", "long_work": true, "threaded": false},
    "long_work": {"call": "/tmp/concorde-project-mcp-x1y2z3/1-task_merge.log"}
  }
}
```

```concorde-contract
{
  "id": "contract.distribution.mcp-answer",
  "version": 1,
  "schema": {
    "type": "object",
    "oneOf": [{"required": ["value"]}, {"required": ["error"]}],
    "additionalProperties": false,
    "properties": {
      "value": {},
      "error": {"type": "object"},
      "watch": {
        "type": "object",
        "required": ["words", "description", "meta"],
        "additionalProperties": false,
        "properties": {
          "words": {"type": "array", "minItems": 1, "items": {"type": "string"}},
          "description": {"type": "string", "minLength": 1},
          "meta": {"type": "object", "additionalProperties": {"type": "string"}}
        }
      },
      "handover": {
        "type": "object",
        "required": ["argv", "environment", "descriptors", "folder", "output", "messages"],
        "additionalProperties": false,
        "properties": {
          "argv": {"type": "array", "minItems": 1, "items": {"type": "string"}},
          "environment": {"type": "object", "additionalProperties": {"type": "string"}},
          "descriptors": {"type": "array", "items": {"type": "integer", "minimum": 0}},
          "folder": {"type": "string", "minLength": 1},
          "output": {"type": "string", "minLength": 1},
          "messages": {"type": "string", "minLength": 1}
        }
      },
      "work": {
        "type": "object",
        "required": ["command", "output", "messages"],
        "additionalProperties": false,
        "properties": {
          "command": {"type": "string", "minLength": 1},
          "output": {"type": "string", "minLength": 1},
          "messages": {"type": "string", "minLength": 1},
          "event": {"type": "string", "minLength": 1},
          "meta": {"type": "object", "additionalProperties": {"type": "string"}},
          "locate": {"type": "array", "minItems": 1, "items": {"type": "string"}}
        }
      }
    }
  },
  "semantics": "What an MCP tool's entry answers for one call. value is the tool's result, error its refusal, a link of the error contract (contract.tracing.error); exactly one is present. watch, for a value, asks the server to run concorde <words> of the primary worktree and wake the session with its answer: description says what the wait waits for and meta the attributes of its channel event. handover and work are taken only for a value of a tool registered as long_work, the call's locks already taken: handover is the command the call's process becomes, argv run with environment, its standard output going to the file output and its standard error to messages, keeping the open locked descriptors, and folder the folder the process made for the work, removed again with those files when the command cannot be started; work is what the server watches of it: command names it in the channel event, output and messages are its files, event names the event (work_ended when absent), meta the event's attributes, and locate the concorde words whose answer's attempt names output and messages anew once the work moved them. The call's process prints the answer without handover and with tools, the digest of its tools; an entry answering neither value nor error is refused with invalid_answer. A behaviour or field change increments the version.",
  "example": {
    "value": {"registered": true, "channel": true, "waits_for": "task fix-checkout becoming delivered"},
    "watch": {
      "words": ["task", "wait", "fix-checkout", "--until", "delivered"],
      "description": "task fix-checkout becoming delivered",
      "meta": {"kind": "task", "task": "fix-checkout"}
    }
  }
}
```

### Refusals of the host

The host passes on the refusal of the part whose tool was called unchanged. Its own refusals are
links of the [error contract](../kernel/tracing/contracts.md#contract.tracing.error) whose actor is
`Concorde project MCP server (<tool>)`:

| Code | Reason | When |
| --- | --- | --- |
| `no_project` | `environment` | the server found no Git repository at start |
| `part_missing` | `input` | the tool is registered by a part the project has not installed, or requires one; the detail names the part and how to install it, as for a [command](module.md#the-command-line) |
| `invalid_input` | `input` | no part of the package registers the tool; the detail names the tools there are. With reason `environment`, the call's process received no readable call object or one without the session's provenance |
| `invalid_answer` | `environment` | the tool's entry answered neither `value` nor `error` |
| `start_failed` | `environment` | the operating system refused to start the command a long work's process was to become; its locks were released |
| `call_failed` | `environment` | the process of a call could not be started, exited or was stopped after its time without printing an answer, or asked twice to route the call otherwise; the detail names the command and worktree, its exit status and the end of what it printed |
| any other code | `capability` | an unexpected error of the host, or of loading the installed parts' code, as a link built from the exception |

## Build manifest

The build writes the [build manifest](../glossary.json#concept.build-manifest)
`generated/build-manifest.json` after every other output. It does so to let:

- the build tell what is stale.
- `build --check` tell what is stale.
- the installer tell what is stale.
- the spec part tell which files are generated.

```concorde-contract
{
  "id": "contract.distribution.build-manifest",
  "version": 1,
  "schema": {
    "type": "object",
    "required": ["schema_version", "sources", "outputs"],
    "additionalProperties": false,
    "properties": {
      "schema_version": {"const": 1},
      "sources": {
        "type": "object",
        "additionalProperties": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
      },
      "outputs": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "required": ["sha256", "sources"],
          "additionalProperties": false,
          "properties": {
            "sha256": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "sources": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}}
          }
        }
      }
    }
  },
  "semantics": "The record of one build of the checkout. Every path is relative to the checkout root, with / as separator. sources maps every file the build read, concorde.json and every source of an output, to sha256: and the hexadecimal SHA-256 of its bytes. outputs maps every file the build wrote under generated/, the manifest itself excepted, to the digest of its bytes (sha256) and the sorted paths of the sources it was made from, each a key of sources. A build is stale when a source is missing or its digest differs; the installer places the rendered workflow whose every source in a part's code directory lies in an installed part's; a leftover output is removed only while its bytes match its recorded digest; and the spec part's validation exempts every key of outputs from CHK.binds.unbound. The file is JSON with sorted keys and a final newline. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "sources": {
      "concorde.json": "sha256:4b8a2e4ef7224e2b40996cd57223bf50ef4eed202c97e886bac67caced2cc2d7",
      "prompts/main-session/skill.md": "sha256:e1773747ac5006990845689121505e66e659d32b93088118006a521167400aaf"
    },
    "outputs": {
      "generated/main-session/skill.md": {
        "sha256": "sha256:906df1f4e159e4e808527a338fcfb07254e98dab0792a4ed1b0e922070e57754",
        "sources": ["prompts/main-session/skill.md"]
      }
    }
  }
}
```

## Install result

`python3 scripts/install-concorde.py <project>` prints the receipt it wrote to
`.concorde/install.json`, field for field. When Spec core refuses a binding of the installed files,
and only then, the printed result adds `binding_error`. The receipt file never holds this field.

```concorde-contract
{
  "id": "contract.distribution.install-result",
  "version": 3,
  "schema": {
    "type": "object",
    "required": [
      "version",
      "parts",
      "source",
      "mode",
      "source_commit",
      "framework",
      "command",
      "python",
      "dependencies",
      "tools",
      "pi_runtime",
      "files",
      "defaults",
      "amended",
      "permissions"
    ],
    "additionalProperties": false,
    "properties": {
      "version": {"type": "string", "minLength": 1},
      "parts": {
        "type": "object",
        "required": ["distribution"],
        "additionalProperties": {"type": "string", "minLength": 1}
      },
      "source": {"type": "string", "minLength": 1},
      "mode": {"enum": ["normal", "develop"]},
      "source_commit": {"type": ["string", "null"]},
      "framework": {"const": ".concorde/framework"},
      "command": {"const": ".concorde/bin/concorde"},
      "python": {
        "type": "object",
        "required": ["environment", "requirement", "base", "version"],
        "additionalProperties": false,
        "properties": {
          "environment": {"const": ".concorde/framework/python"},
          "requirement": {"type": "string", "minLength": 1},
          "base": {"type": "string", "minLength": 1},
          "version": {"type": "string", "pattern": "^[0-9]+(\\.[0-9]+)*$"}
        }
      },
      "dependencies": {
        "oneOf": [
          {"type": "null"},
          {
            "type": "object",
            "required": ["requirements", "lock_sha256", "packages"],
            "additionalProperties": false,
            "properties": {
              "requirements": {"const": ".concorde/framework/requirements.txt"},
              "lock_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
              "packages": {"type": "integer", "minimum": 0}
            }
          }
        ]
      },
      "tools": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "d2": {
            "type": "object",
            "required": ["version", "platform", "sha256", "path"],
            "additionalProperties": false,
            "properties": {
              "version": {"type": "string", "minLength": 1},
              "platform": {"type": "string", "minLength": 1},
              "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
              "path": {"type": "string", "minLength": 1}
            }
          },
          "pi-runtime": {
            "type": "object",
            "required": ["package", "version", "lock_sha256", "path"],
            "additionalProperties": false,
            "properties": {
              "package": {"const": "@anthropic-ai/sandbox-runtime"},
              "version": {"type": "string", "minLength": 1},
              "lock_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
              "path": {"const": ".concorde/tools/pi-runtime"}
            }
          }
        }
      },
      "pi_runtime": {"type": "boolean"},
      "files": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "defaults": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "amended": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "permissions": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "binding_error": {
        "type": "object",
        "required": ["code", "message", "reason", "location", "remediation", "causes"]
      }
    }
  },
  "semantics": "The result of a successful install, equal to the receipt .concorde/install.json it wrote except for binding_error. version is the installed package's version from concorde.json; parts names every installed part, the parts asked for with every part they depend on and Distribution, each mapped to the version it carries, which is the package's version for every part; source the absolute path of the Concorde checkout installed from, which concorde update installs from again; mode normal, or develop for a develop install; source_commit the commit installed, the develop source check's commit in a develop install and otherwise the checkout's HEAD, or null outside a Git checkout. framework and command are where the Framework runtime and the command lie. python names Concorde's own environment: its path, the Python requirement concorde.json names under runtime.python, the interpreter uv chose (base, an absolute path) and that interpreter's version. dependencies is null when the install left Concorde's Python dependencies out, and otherwise names the requirements file exported from the package's uv.lock, the SHA-256 of that lock and the number of packages installed. dependencies is also null when no installed part needs a Python dependency. tools holds d2 when the pinned d2 is placed (its release, platform key, the archive's pinned SHA-256 and the program's path), which happens only where the spec part is installed, and pi-runtime when the pi runtime is placed (the package, its locked version, the SHA-256 of the lockfile and its folder), only where the worker harness part is; a tool left out has no key. pi_runtime is false when the install was made with --without-pi-runtime, a choice concorde update keeps. files lists, sorted, every file Concorde owns in the project, a default an earlier install wrote included; defaults lists, sorted, those of them that are Concorde-owned defaults, which hold the project's own data: the defaults of the installed parts and every default an earlier receipt recorded that is still in place, whether or not this install's parts or this package still declare it, so that no later install removes it; amended lists the project's own files the installer only amends (.gitignore, CLAUDE.md, .mcp.json and, once written, .claude/settings.json); permissions lists the permission rules of .claude/settings.json the installer added and owns. binding_error is present only when Spec core refused to bind the installed files after the receipt was written: it is Spec core's error record (contract.spec.error) and the install has still succeeded. A behaviour or field change increments the version.",
  "example": {
    "version": "9.0.0",
    "parts": {
      "coordination": "9.0.0",
      "distribution": "9.0.0",
      "execution": "9.0.0",
      "issues": "9.0.0",
      "kernel": "9.0.0",
      "method": "9.0.0",
      "spec": "9.0.0",
      "worker harness": "9.0.0",
      "workflow": "9.0.0"
    },
    "source": "/home/dev/concorde",
    "mode": "normal",
    "source_commit": "3f37048934c2a1b0d9e8f7a6b5c4d3e2f1a0b9c8",
    "framework": ".concorde/framework",
    "command": ".concorde/bin/concorde",
    "python": {
      "environment": ".concorde/framework/python",
      "requirement": ">=3.11",
      "base": "/usr/bin/python3.12",
      "version": "3.12.3"
    },
    "dependencies": {
      "requirements": ".concorde/framework/requirements.txt",
      "lock_sha256": "0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
      "packages": 42
    },
    "tools": {
      "d2": {
        "version": "v0.7.1",
        "platform": "linux-amd64",
        "sha256": "1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809",
        "path": ".concorde/tools/d2"
      },
      "pi-runtime": {
        "package": "@anthropic-ai/sandbox-runtime",
        "version": "0.0.40",
        "lock_sha256": "9f8e7d6c5b4a39281706f5e4d3c2b1a09f8e7d6c5b4a39281706f5e4d3c2b1a0",
        "path": ".concorde/tools/pi-runtime"
      }
    },
    "pi_runtime": true,
    "files": [".claude/skills/concorde/SKILL.md", ".claude/workflows/concorde-brownfield.js", ".concorde/bin/concorde", ".concorde/issues/.gitignore"],
    "defaults": [".concorde/issues/.gitignore"],
    "amended": [".gitignore", "CLAUDE.md", ".mcp.json", ".claude/settings.json"],
    "permissions": ["Workflow(concorde-brownfield)", "mcp__concorde__workflow_step", "Bash(.concorde/bin/concorde workflow report:*)"]
  }
}
```

## Update result

`concorde update`, and `python3 <checkout>/scripts/install-concorde.py <project> --update`, print
what the update did. Where the spec part is installed, the result's `update` is the mark the update
wrote to `.concorde/update.json`, field for field. Where the spec part is not installed, that field
is `null`, since the mark waits for a `spec-validation`.

```concorde-contract
{
  "id": "contract.distribution.update-result",
  "version": 2,
  "schema": {
    "type": "object",
    "required": ["receipt", "update", "open_tasks", "next"],
    "additionalProperties": false,
    "properties": {
      "receipt": {
        "type": "object",
        "required": ["version", "parts", "source", "mode", "source_commit", "files", "amended"]
      },
      "update": {
        "type": ["object", "null"],
        "required": ["state", "from", "to", "commits", "protocol", "at"],
        "additionalProperties": false,
        "properties": {
          "state": {"const": "unvalidated"},
          "from": {"type": ["string", "null"]},
          "to": {"type": "string", "minLength": 1},
          "commits": {
            "type": "object",
            "required": ["from", "to"],
            "additionalProperties": false,
            "properties": {
              "from": {"type": ["string", "null"]},
              "to": {"type": ["string", "null"]}
            }
          },
          "protocol": {
            "oneOf": [
              {"type": "null"},
              {
                "type": "object",
                "required": ["from", "to"],
                "additionalProperties": false,
                "properties": {
                  "from": {"type": ["object", "null"]},
                  "to": {"type": ["object", "null"]}
                }
              }
            ]
          },
          "at": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}
        }
      },
      "open_tasks": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["id", "branch", "worktree"],
          "additionalProperties": false,
          "properties": {
            "id": {"type": "string", "minLength": 1},
            "branch": {"type": ["string", "null"]},
            "worktree": {"type": ["string", "null"]}
          }
        }
      },
      "next": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}}
    }
  },
  "semantics": "The result of a successful concorde update. receipt is the install result of the update's install (contract.distribution.install-result), the new receipt, whose parts are those the previous receipt named (every part when it named none), every part the new Concorde makes one of them depend on and the parts --parts added. update is null where the spec part is not installed, which leaves the Protocol binding alone and writes no mark, and otherwise the mark .concorde/update.json the update wrote: state unvalidated; from and commits.from the version and installed commit before, those of the previous receipt or, when an earlier update's mark was still there, that mark's, each null when the record they come from has none; to and commits.to those just installed, commits.to null outside a Git checkout; protocol null when neither this update nor a kept earlier mark rebound the Protocol binding, and otherwise the binding before (null when the configuration had none) and after, each a {version, digest} object as the project configuration holds it; at the UTC time the mark was written. open_tasks lists what the coordination part's after-update report names, in the order of their folders: the tasks of the primary worktree that have not ended, each with its identity, branch and worktree as its task record names them, null when the record lacks one; it is empty where the coordination part is not installed. next says what the developer does next: commit the updated files; where the update wrote a mark, run concorde spec-validation and repair what it reports; and, when the Protocol binding changed and a task is open, merge the primary branch into each open task. A behaviour or field change increments the version.",
  "example": {
    "receipt": {
      "version": "9.0.0",
      "parts": {"distribution": "9.0.0", "spec": "9.0.0"},
      "source": "/home/dev/concorde",
      "mode": "normal",
      "source_commit": "3f37048934c2a1b0d9e8f7a6b5c4d3e2f1a0b9c8",
      "files": [".claude/skills/concorde/SKILL.md", ".concorde/bin/concorde"],
      "amended": [".gitignore", "CLAUDE.md", ".mcp.json"]
    },
    "update": {
      "state": "unvalidated",
      "from": "8.4.0",
      "to": "9.0.0",
      "commits": {"from": "84ed434e1f2a3b4c5d6e7f8091a2b3c4d5e6f708", "to": "3f37048934c2a1b0d9e8f7a6b5c4d3e2f1a0b9c8"},
      "protocol": {
        "from": {"version": "16.0.0", "digest": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0"},
        "to": {"version": "16.1.0", "digest": "sha256:ea064c091baadd0db50e3f1eec0538be961ea5131816d6bd2d18b41610716995"}
      },
      "at": "2026-10-02T09:30:00Z"
    },
    "open_tasks": [{"id": "fix-checkout", "branch": "concorde/fix-checkout", "worktree": "/home/dev/shop/.claude/worktrees/fix-checkout"}],
    "next": [
      "commit the updated files",
      "run `concorde spec-validation` and repair what it reports; the first validation that passes marks the update validated",
      "merge the primary branch into each open task, whose worktree still carries the previous Protocol copy"
    ]
  }
}
```
