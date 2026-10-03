# Distribution contracts

The [part registration](../glossary.json#concept.part-registration) every part gives Distribution,
the parts index the build records, and the exact results that [Distribution](module.md)'s installer and `concorde update` print when
they succeed. Both print one JSON object on standard output and exit with status 0; every refusal
instead prints `{"error": <link>}` and exits with status 1, as [Refusals](module.md#refusals)
describes. Paths are relative to the project root unless stated otherwise.

## Part registration

Every part declares one registration, plain data in the file `registration.json` of its own
directory of `src/concorde/`, which Distribution reads without importing anything. An entry is a
Python attribute named `<module>:<attribute>`, the module relative to the part's own package, so
that an entry never leaves its part; Distribution imports a part's code only through the entries of
an installed part's registration. What each kind of entry is called with and answers:

| Entry | Called with | Answers |
| --- | --- | --- |
| a command's `entry` | the rest of the command line, as a list of words, and the project root the global `--project-root` names (default `.`) | with `output` `own`, its exit status, having printed its own output; with `envelope`, Spec core's [shared envelope](../spec-tooling/spec/contracts.md), which `concorde` prints and exits with |
| an MCP tool's `entry` | the call as one JSON object: `tool`, `arguments`, the session's provenance `primary`, `where`, `session` and `channel`, and `long_work` for a call of a tool registered as long work | `{"value": …}` or `{"error": <link>}`, with `watch` (a `concorde` command to run and wake the session with), and for a long work `handover` (the command the call's process becomes, with the locked descriptors it hands on) and `work` (what the server watches of it) |
| `mcp_definitions` | nothing: it is a mapping | each of the part's tool names mapped to its `description` and `inputSchema`, as `tools/list` gives them |
| `renders` | the checkout root the build renders | `{"files": {<path>: {"content", "sources"}}}`, outputs under `generated/`, or `{"refusal": {"code", "message"}}` |
| `install.prepare` | the package root and the project root, before the installer writes anything | `{"files": {<project path>: <bytes>}}` to place, or `{"refusal": {"code", "message"}}`, which refuses the install with that code |
| `install.bind` | the project root, after the receipt was written | `null`, or Spec core's [error record](../spec-tooling/spec/errors.md#contract.spec.error), which the install result carries as `binding_error` |
| `idle_check` | the project root | a list of descriptions of the part's work still running, empty when idle |
| `after_update` | the project root | the list the update result carries, such as the open tasks |

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
  "semantics": "The registration of one part, the file registration.json of its directory of src/concorde/. part is its installer name and module the top-level Module the part is made of; the part carries the version of the package it was built from, the same for every part, which concorde.json names. depends_on names the parts it depends on; the installer installs them with it, and no other part is required for it to work. loads names the part's modules that register what its code provides when they load (typed value types, trace roots, Operation and command definitions, workflows), which Distribution imports for every installed part before it routes a command of a part, answers an MCP tool or renders the build. commands are the concorde subcommands it adds, each routed to its entry, which prints its own output or, with output envelope, answers Spec core's shared envelope for concorde to print. mcp_tools are the tools the project MCP server presents for it, each answered by its entry in a fresh process of the primary worktree's concorde, or of the session's own worktree's when worktree is session; long_work allows it to take locks without waiting and become the work it starts, handing them on; threaded serves its calls on a thread of their own, for calls that wait; requires names parts without which the tool is not presented. mcp_definitions names the mapping from each of its tool names to its description and inputSchema, and mcp_instructions the sentence it adds to the server's instructions. typed_types lists the typed value types its code registers. guidance names the part's guidance sections, or is null when it has none: skill its section of the project skill, task_session its section of the task-session prompt and claude_md its section of the CLAUDE.md block, each the build-relative path of a rendered section, generated/<path> rendered from prompts/<path>, or null when the part contributes no section of that kind; Distribution composes each kind from the sections of a set of parts, Coordination's first and the others in the order of the parts table. renders names the entry through which the build renders the part's own outputs, such as the workflow part's Claude Code workflows. install lists what the installer places for it: files names, relative to the package and to the Framework copy alike, the files the part ships beside its code directory src/concorde/<directory>/, which is always shipped, a path ending with / naming a whole directory, such as the spec part's protocol/ or the worker harness's scripts/available_models.py; defaults the Concorde-owned defaults written where absent, by project path; gitignore its .gitignore lines; permissions the Claude Code permission rules a placed workflow needs, added only when a workflow is placed; programs the programs it needs placed, d2 or pi-runtime; python_dependencies the runtime dependencies of the package's pyproject.toml its code imports, which the installer places, from uv.lock, only where an installed part names one; prepare names the service deciding, before any write, the files it places or refusing the install, and bind the service binding the installed files after the receipt. idle_check names the function reporting the part's work still running in the project, or null when it has none; after_update the function whose report an update result carries, such as the open tasks, or null. Every entry is <module>:<attribute> relative to the part's own package. A behaviour or field change increments the version.",
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

The installer resolves the parts to install by following `depends_on` from the parts named, and
refuses before any write a name no registration of the package carries, or a set whose
dependencies name a part the package does not build. Two parts registering the same command or tool
name are a build error, never resolved by order.

The build records what every part of the package registers in the **parts index**
`generated/parts.json`, `{"schema_version": 1, "parts": {<part>: {"module", "depends_on",
"commands", "mcp_tools"}}}`, so that a project's `concorde` and [project MCP server](../glossary.json#concept.project-mcp-server) name the part of a
command or tool that is not installed without reading that part's registration. The installed parts
are, in a source checkout, every part the package builds, and in a project the parts the receipt
names under `parts`, an object whose keys are the part names, every part when the receipt names
none; Distribution is installed with any part.

## Install result

`python3 scripts/install-concorde.py <project>` prints the receipt it wrote to
`.concorde/install.json`, field for field. Only a binding of the installed files that Spec core
refused adds `binding_error`, which the receipt file never holds.

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
what the update did. Its `update` is the mark it wrote to `.concorde/update.json`, field for field,
or `null` where the spec part is not installed, since the mark waits for a `spec-validation`.

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
