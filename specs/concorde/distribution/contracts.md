# Distribution contracts

The [part registration](../glossary.json#concept.part-registration) every part gives Distribution,
and the exact results that [Distribution](module.md)'s installer and `concorde update` print when
they succeed. Both print one JSON object on standard output and exit with status 0; every refusal
instead prints `{"error": <link>}` and exits with status 1, as [Refusals](module.md#refusals)
describes. Paths are relative to the project root unless stated otherwise.

## Part registration

Every part declares one registration, plain data that Distribution reads without importing the
part's code beyond the functions the registration names. An entry is a Python function named
`<module>:<function>` relative to the part's package; Distribution calls a command's entry with the
rest of the command line, an MCP tool's entry with the call's JSON object, an idle check's entry with
the project root, and an after-update entry with the project root, and each answers in its own
part's shape.

```concorde-contract
{
  "id": "contract.distribution.part-registration",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["part", "version", "module", "depends_on", "commands", "mcp_tools", "typed_types", "guidance", "install", "idle_check", "after_update"],
    "properties": {
      "part": {"type": "string", "pattern": "^[a-z][a-z-]*$"},
      "version": {"type": "string", "minLength": 1},
      "module": {"type": "string", "pattern": "^module\\.[a-z][a-z0-9-]*$"},
      "depends_on": {"type": "array", "uniqueItems": true, "items": {"type": "string", "pattern": "^[a-z][a-z-]*$"}},
      "commands": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["name", "entry"],
          "properties": {
            "name": {"type": "string", "pattern": "^[a-z][a-z-]*$"},
            "entry": {"type": "string", "minLength": 1}
          }
        }
      },
      "mcp_tools": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["name", "entry", "worktree", "long_work"],
          "properties": {
            "name": {"type": "string", "pattern": "^[a-z][a-z_]*$"},
            "entry": {"type": "string", "minLength": 1},
            "worktree": {"enum": ["primary", "session"]},
            "long_work": {"type": "boolean"}
          }
        }
      },
      "typed_types": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "guidance": {"type": ["string", "null"], "minLength": 1},
      "install": {
        "type": "object",
        "additionalProperties": false,
        "required": ["files", "gitignore", "permissions", "programs"],
        "properties": {
          "files": {"type": "array", "items": {"type": "string", "minLength": 1}},
          "gitignore": {"type": "array", "items": {"type": "string", "minLength": 1}},
          "permissions": {"type": "array", "items": {"type": "string", "minLength": 1}},
          "programs": {"type": "array", "items": {"type": "string", "minLength": 1}}
        }
      },
      "idle_check": {"type": ["string", "null"], "minLength": 1},
      "after_update": {"type": ["string", "null"], "minLength": 1}
    }
  },
  "semantics": "The registration of one part. part is its installer name and version the version of the repository it was built from, the same for every part. module is the top-level Module the part is made of. depends_on names the parts it depends on; the installer installs them with it, and no other part is required for it to work. commands are the concorde subcommands it adds, each routed to its entry; mcp_tools the tools the project MCP server presents for it, each run in a fresh process of the primary worktree's concorde, or of the session's own worktree's when worktree is session, and, when long_work is true, allowed to take locks without waiting and hand them to the process doing the work. typed_types lists the typed value types its code registers. guidance is the build-relative path of its rendered guidance section, or null. install lists what the installer places for it: framework-relative files, .gitignore lines, Claude Code permission rules and programs it needs, such as the pi runtime. idle_check names the function reporting the part's work still running in the project, or null when it has none; after_update the function whose report an update result carries, such as the open tasks, or null. A behaviour or field change increments the version.",
  "example": {
    "part": "coordination",
    "version": "9.0.0",
    "module": "module.coordination",
    "depends_on": ["kernel"],
    "commands": [{"name": "task", "entry": "tasks.cli:main"}],
    "mcp_tools": [
      {"name": "task_show", "entry": "tasks.mcp:show", "worktree": "primary", "long_work": false},
      {"name": "task_merge", "entry": "tasks.mcp:merge", "worktree": "primary", "long_work": true}
    ],
    "typed_types": ["concorde-task-record"],
    "guidance": "generated/main-session/skill.md",
    "install": {
      "files": [],
      "gitignore": [".concorde/tasks/", ".concorde/history/", ".concorde/workspace.json", ".claude/worktrees/"],
      "permissions": [],
      "programs": []
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

## Install result

`python3 scripts/install-concorde.py <project>` prints the receipt it wrote to
`.concorde/install.json`, field for field. Only a binding of the installed files that Spec core
refused adds `binding_error`, which the receipt file never holds.

```concorde-contract
{
  "id": "contract.distribution.install-result",
  "version": 1,
  "schema": {
    "type": "object",
    "required": [
      "version",
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
      "amended",
      "permissions"
    ],
    "additionalProperties": false,
    "properties": {
      "version": {"type": "string", "minLength": 1},
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
      "amended": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "permissions": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
      "binding_error": {
        "type": "object",
        "required": ["code", "message", "reason", "location", "remediation", "causes"]
      }
    }
  },
  "semantics": "The result of a successful install, equal to the receipt .concorde/install.json it wrote except for binding_error. version is the installed package's version from concorde.json; source the absolute path of the Concorde checkout installed from, which concorde update installs from again; mode normal, or develop for a develop install; source_commit the commit installed, the develop source check's commit in a develop install and otherwise the checkout's HEAD, or null outside a Git checkout. framework and command are where the Framework runtime and the command lie. python names Concorde's own environment: its path, the Python requirement concorde.json names under runtime.python, the interpreter uv chose (base, an absolute path) and that interpreter's version. dependencies is null when the install left Concorde's Python dependencies out, and otherwise names the requirements file exported from the package's uv.lock, the SHA-256 of that lock and the number of packages installed. tools holds d2 when the pinned d2 is placed (its release, platform key, the archive's pinned SHA-256 and the program's path) and pi-runtime when the pi runtime is placed (the package, its locked version, the SHA-256 of the lockfile and its folder); a tool left out has no key. pi_runtime is false when the install was made with --without-pi-runtime, a choice concorde update keeps. files lists, sorted, every file Concorde owns in the project, a default an earlier install wrote included; amended lists the project's own files the installer only amends (.gitignore, CLAUDE.md, .mcp.json and, once written, .claude/settings.json); permissions lists the permission rules of .claude/settings.json the installer added and owns. binding_error is present only when Spec core refused to bind the installed files after the receipt was written: it is Spec core's error record (contract.spec.error) and the install has still succeeded. A behaviour or field change increments the version.",
  "example": {
    "version": "9.0.0",
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
    "files": [".claude/skills/concorde/SKILL.md", ".claude/workflows/concorde-brownfield.js", ".concorde/bin/concorde"],
    "amended": [".gitignore", "CLAUDE.md", ".mcp.json", ".claude/settings.json"],
    "permissions": ["Workflow(concorde-brownfield)", "mcp__concorde__workflow_step", "Bash(.concorde/bin/concorde workflow report:*)"]
  }
}
```

## Update result

`concorde update`, and `python3 <checkout>/scripts/install-concorde.py <project> --update`, print
what the update did. Its `update` is the mark it wrote to `.concorde/update.json`, field for field.

```concorde-contract
{
  "id": "contract.distribution.update-result",
  "version": 1,
  "schema": {
    "type": "object",
    "required": ["receipt", "update", "open_tasks", "next"],
    "additionalProperties": false,
    "properties": {
      "receipt": {
        "type": "object",
        "required": ["version", "source", "mode", "source_commit", "files", "amended"]
      },
      "update": {
        "type": "object",
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
      "next": {"type": "array", "minItems": 2, "items": {"type": "string", "minLength": 1}}
    }
  },
  "semantics": "The result of a successful concorde update. receipt is the install result of the update's install (contract.distribution.install-result), the new receipt. update is the mark .concorde/update.json the update wrote: state unvalidated; from and commits.from the version and installed commit before, those of the previous receipt or, when an earlier update's mark was still there, that mark's, each null when the record they come from has none; to and commits.to those just installed, commits.to null outside a Git checkout; protocol null when neither this update nor a kept earlier mark rebound the Protocol binding, and otherwise the binding before (null when the configuration had none) and after, each a {version, digest} object as the project configuration holds it; at the UTC time the mark was written. open_tasks lists what the coordination part's after-update report names, in the order of their folders: the tasks of the primary worktree that have not ended, each with its identity, branch and worktree as its task record names them, null when the record lacks one; it is empty where the coordination part is not installed. next says what the developer does next: commit the updated files, run concorde spec-validation and repair what it reports, and, when the Protocol binding changed and a task is open, merge the primary branch into each open task. A behaviour or field change increments the version.",
  "example": {
    "receipt": {
      "version": "9.0.0",
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
