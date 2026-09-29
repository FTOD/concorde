# Tracing contracts

The canonical values and layout of [Tracing](module.md): the
[trace node](../glossary.json#concept.trace-node) record `trace.json`, where every node, task and
lock lies, the Tracing configuration, what `concorde trace` prints, and the error link every level
reports with. The [requirements](requirements.md) state the obligations; the
[scenarios](scenarios.md) show them at work.

## Trace node

```concorde-contract
{
  "id": "contract.tracing.node",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "id",
      "kind",
      "started_at",
      "ended_at",
      "status",
      "outcome",
      "usage",
      "error",
      "metadata",
      "artifacts",
      "references",
      "content"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "id": {
        "type": "string",
        "minLength": 1
      },
      "kind": {
        "enum": [
          "task",
          "session",
          "round",
          "merge",
          "merge-check",
          "workflow",
          "step",
          "run",
          "check",
          "worker-run",
          "worker-round"
        ]
      },
      "started_at": {
        "type": "string",
        "minLength": 1
      },
      "ended_at": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "minLength": 1
          }
        ]
      },
      "status": {
        "enum": [
          "running",
          "ok",
          "blocked",
          "failed",
          "unknown"
        ]
      },
      "outcome": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$"
          }
        ]
      },
      "usage": {
        "$ref": "#/$defs/usage"
      },
      "error": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
      },
      "metadata": {
        "$ref": "#/$defs/metadata"
      },
      "artifacts": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/artifact"
        }
      },
      "references": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/reference"
        }
      },
      "content": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "$ref": "#/$defs/typed"
          }
        ]
      }
    },
    "$defs": {
      "count": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "integer",
            "minimum": 0
          }
        ]
      },
      "amount": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "number",
            "minimum": 0
          }
        ]
      },
      "usage": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "tokens_in",
          "tokens_out",
          "tokens_cache_read",
          "tokens_cache_write",
          "cost_usd",
          "turns",
          "duration_seconds"
        ],
        "properties": {
          "tokens_in": {
            "$ref": "#/$defs/count"
          },
          "tokens_out": {
            "$ref": "#/$defs/count"
          },
          "tokens_cache_read": {
            "$ref": "#/$defs/count"
          },
          "tokens_cache_write": {
            "$ref": "#/$defs/count"
          },
          "cost_usd": {
            "$ref": "#/$defs/amount"
          },
          "turns": {
            "$ref": "#/$defs/count"
          },
          "duration_seconds": {
            "$ref": "#/$defs/amount"
          }
        }
      },
      "text": {
        "type": "string",
        "minLength": 1
      },
      "metadata": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "task": {
            "$ref": "#/$defs/text"
          },
          "workspace": {
            "$ref": "#/$defs/text"
          },
          "modules": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/text"
            }
          },
          "branch": {
            "$ref": "#/$defs/text"
          },
          "base_commit": {
            "$ref": "#/$defs/text"
          },
          "commit": {
            "$ref": "#/$defs/text"
          },
          "operation": {
            "$ref": "#/$defs/text"
          },
          "command": {
            "$ref": "#/$defs/text"
          },
          "workflow": {
            "$ref": "#/$defs/text"
          },
          "mode": {
            "$ref": "#/$defs/text"
          },
          "program": {
            "$ref": "#/$defs/text"
          },
          "task_type": {
            "$ref": "#/$defs/text"
          },
          "worker": {
            "$ref": "#/$defs/text"
          },
          "backend": {
            "$ref": "#/$defs/text"
          },
          "model": {
            "$ref": "#/$defs/text"
          },
          "reasoning": {
            "$ref": "#/$defs/text"
          },
          "context_identity": {
            "$ref": "#/$defs/text"
          },
          "grant_digest": {
            "$ref": "#/$defs/text"
          },
          "brief_digest": {
            "$ref": "#/$defs/text"
          },
          "settings_digest": {
            "$ref": "#/$defs/text"
          },
          "check": {
            "$ref": "#/$defs/text"
          },
          "module": {
            "$ref": "#/$defs/text"
          },
          "concorde_commit": {
            "$ref": "#/$defs/text"
          },
          "protocol_version": {
            "$ref": "#/$defs/text"
          }
        }
      },
      "artifact": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "id",
          "path",
          "digest"
        ],
        "properties": {
          "id": {
            "$ref": "#/$defs/text"
          },
          "path": {
            "type": "string",
            "minLength": 1,
            "format": "project-path"
          },
          "digest": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string",
                "pattern": "^sha256:[0-9a-f]{64}$"
              }
            ]
          }
        }
      },
      "reference": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "relation",
          "target"
        ],
        "properties": {
          "relation": {
            "enum": [
              "input",
              "cites",
              "commit",
              "bundle"
            ]
          },
          "target": {
            "$ref": "#/$defs/text"
          }
        }
      },
      "typed": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "type_id",
          "schema_version",
          "data"
        ],
        "properties": {
          "type_id": {
            "$ref": "#/$defs/text"
          },
          "schema_version": {
            "type": "integer",
            "minimum": 1
          },
          "data": {
            "type": "object"
          }
        }
      }
    }
  },
  "semantics": "The record trace.json of one trace node, in the node's folder. id identifies the node: a run or worker run identity, which is unique in the project, or a name unique among the nodes of its kind under the same parent (a task name, a session identity, a round or merge number, a step key, a check identity). kind is one of the kinds of the node kinds table. started_at and ended_at are RFC 3339 UTC times; ended_at is null while the node runs and for a node whose end its producer never observes. status is running until the final write, then ok, blocked or failed, or unknown for a node whose end its producer never observes; outcome is the producer's finer, snake_case account of the end (such as merged, completed, passed, timed_out, cancelled), null while running. usage is what the node itself consumed, never the sum of its children: tokens read (tokens_in), written (tokens_out), read from and written to the prompt cache, the cost in US dollars as the agent program reported it, the agent turns and the node's wall-clock duration; a field is null when the node consumed none of it or its producer cannot observe it. error is the node's error link, following contract.tracing.error, when the node ended blocked or failed and its producer reports that end with a link, such as a run or a worker run; it is null for every other node, and for a node whose failure its parent reports, such as a worker round whose checks failed. metadata holds only the dimensions of the metadata table that the node's kind provides and only facts Concorde observed itself, never a statement taken from a worker result. artifacts lists files of the node's folder, each by a stable id, its path relative to the folder and its digest at the final write (null while the node runs or when the file is still growing). references name nodes of the same level and commits: input (the identity of a run whose output this run admitted), cites (the identity of a run this node cites as the source of what it decided), commit (a Git commit this node created) and bundle (an evidence bundle this node committed, as <commit>:<path>). content is the producer's own record, a typed value of the type the node kinds table names, checked against the type its producer registered; null when the producer records nothing of its own. Children are not listed: they are the trace nodes in the folders below this one. No field by which the node refers to its files or to other nodes holds an absolute path; an error link or a worker's claim the node keeps is kept as it was reported. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "id": "r-20260927T101500-implement-3f2a9c1b",
    "kind": "run",
    "started_at": "2026-09-27T10:15:00.120000Z",
    "ended_at": "2026-09-27T10:21:41.870000Z",
    "status": "ok",
    "outcome": "ok",
    "usage": {
      "tokens_in": null,
      "tokens_out": null,
      "tokens_cache_read": null,
      "tokens_cache_write": null,
      "cost_usd": null,
      "turns": null,
      "duration_seconds": 401.75
    },
    "error": null,
    "metadata": {
      "workspace": "retry",
      "modules": [
        "module.http"
      ],
      "operation": "implement",
      "commit": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
      "concorde_commit": "c467a90a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
      "protocol_version": "15.0.0"
    },
    "artifacts": [
      {
        "id": "result",
        "path": "result.json",
        "digest": "sha256:5555555555555555555555555555555555555555555555555555555555555555"
      },
      {
        "id": "progress",
        "path": "status.json",
        "digest": "sha256:6666666666666666666666666666666666666666666666666666666666666666"
      }
    ],
    "references": [
      {
        "relation": "input",
        "target": "r-20260927T100200-understand-9a0b1c2d"
      }
    ],
    "content": {
      "type_id": "concorde-run-trace",
      "schema_version": 1,
      "data": {
        "kind": "operation",
        "name": "implement",
        "exit_code": 0,
        "steps": [
          {
            "name": "implement",
            "started_at": "2026-09-27T10:15:00.410000Z",
            "ended_at": "2026-09-27T10:21:41.600000Z",
            "outcome": "continue"
          }
        ],
        "worker_runs": [
          "w-20260927T101501-a1b2c3"
        ],
        "summary": "implement finished for module.http."
      }
    }
  }
}
```

### Node kinds

Each kind has one producer, which writes its nodes' records and chooses their content, and one place
below its parent. The folders are relative to the parent node's folder, or to the `.concorde`
directory for the three roots.

| Kind | Producer | Folder | Identity | Metadata it provides | Content type |
| --- | --- | --- | --- | --- | --- |
| `task` | [Tasks](../coordination/tasks/module.md) | `tasks/<task>/`, moved to `history/<key>/` | the task name | `task`, `modules`, `branch`, `base_commit`, `concorde_commit`, `protocol_version` | `concorde-task-trace` |
| `session` | [Task sessions](../coordination/task-session/module.md) | `sessions/<session>/` | the session identity | `task`, `program`, `model` | `concorde-session-trace` |
| `round` | Task sessions | `rounds/<n>/` of a pi session | the round number | `program`, `model` | `concorde-round-trace` |
| `merge` | Tasks | `merges/<n>/` | the attempt number | `task`, `branch`, `commit` | `concorde-merge-trace` |
| `merge-check` | Tasks | `checks/<n>/` of a merge | the check's number | none | `concorde-merge-check-trace` |
| `workflow` | [Workflows](../execution/workflows/module.md) | `workflow/` of a workspace folder | the workflow name | `workspace`, `workflow`, `mode` | `concorde-workflow-trace` |
| `step` | Workflows | `steps/<seq>-<key>/` of the workflow | the [step key](../glossary.json#concept.step-key) | `workspace`, `workflow`, `operation` or `command` | `concorde-step-trace` |
| `run` | [Execution](../execution/module.md) | `runs/<run>/` of a workspace folder, `run/` of a step, or `unbound/<run>/` | the run identity | `workspace`, `modules`, `operation` or `command`, `commit`, `base_commit`, `concorde_commit`, `protocol_version` | `concorde-run-trace` |
| `check` | [Check execution](../execution/checks/module.md) | `checks/<check>/` of a run or a worker round | the check identity | `check`, `module` | `concorde-check-trace` |
| `worker-run` | [Workers](../execution/workers/module.md) | `workers/<worker run>/` of a run | the worker run identity | `modules`, `operation`, `worker`, `task_type`, `backend`, `model`, `reasoning`, `context_identity`, `grant_digest`, `brief_digest`, `settings_digest` | `concorde-worker-run-trace` |
| `worker-round` | Workers | `rounds/<n>/` of a worker run | the round number | `backend`, `model` | `concorde-worker-round-trace` |

A workspace folder, `workspace/` of a task, is no node of its own: the reading command shows it as
a `workspace` node whose children are its workflow and its runs, named after the workspace its runs
record. A node lists in `metadata` only the dimensions its row names; a producer's own [Spec](../glossary.json#concept.spec) defines
its content type.

### Metadata dimensions

| Dimension | Meaning |
| --- | --- |
| `task` | the task the node belongs to, only on Coordination's nodes |
| `workspace` | the workspace a run or workflow worked in, from its binding |
| `modules` | the [Modules](../glossary.json#concept.module) the node worked on |
| `branch`, `base_commit` | the branch and the commit the task or workspace works from |
| `commit` | the commit the node examined (an [unbound run](../glossary.json#concept.unbound-run)) or produced (a merge), or the `HEAD` a bound run started on |
| `operation`, `command` | the Operation or execution command that ran |
| `workflow`, `mode` | the workflow and its mode |
| `program` | the agent program of a session, `claude` or `pi` |
| `task_type`, `worker` | a worker's [task type](../glossary.json#concept.task-type) and [worker id](../glossary.json#concept.worker-id) |
| `backend`, `model`, `reasoning` | the agent program, model and reasoning level a worker or session ran on, as configured; absent when the program's default applied |
| `context_identity`, `grant_digest`, `brief_digest`, `settings_digest` | the identity and digests of what a worker was given |
| `check`, `module` | a check's identity and the Module it checks |
| `concorde_commit` | the commit of the Concorde code that wrote the node, when that code is a Git checkout, or the commit its installation records |
| `protocol_version` | the Spec Protocol version the project configuration binds |

### Writing a node

- The producer writes `trace.json` when the node starts, before the work it records begins, with
  `status` `running`, and again when the node ends, with its end, status, outcome, usage, error,
  artifacts and content. It may rewrite it in between, such as a worker run after each round. Every
  write replaces the file atomically, so a reader never finds half a record.
- The parent creates the child's folder, or names it to the child's process before starting it,
  before the child's first write. A child never records its parent's identity.
- Every artifact path is relative to the node's folder; every other node is named by identity.
- A file that grows while the node runs, such as a transcript or an event stream, is an artifact of
  the node; its content is never copied into `trace.json`.
- The live [progress file](../glossary.json#concept.progress-file) `status.json` of a run, worker run
  or pi [session round](../glossary.json#concept.session-round), and a [run result](../glossary.json#concept.run-result) `result.json`, stay
  separate files of the node's folder, listed among its artifacts.

## Layout

Everything is under the `.concorde` directory of the project's primary worktree, except the unbound
runs and the [Issue](../glossary.json#concept.issue) lock, which are under the `.concorde` of the worktree they belong to. Git
ignores `tasks/`, `history/`, `unbound/` and `locks/`.

```text
.concorde/
├─ tracing.json                  the Tracing configuration (tracked, optional)
├─ evidence/<workspace>/<n>.json evidence bundles, committed with their delivery
├─ locks/                        every lock and nothing else
├─ tasks/<task>/                 a current task
│  ├─ task.json                  the task record
│  ├─ trace.json                 the task's node
│  ├─ decisions.md               the decision log
│  ├─ runtime/                   the task session's boundary configuration, removed at close
│  ├─ sessions/<session>/        session nodes, pi rounds under rounds/<n>/
│  ├─ merges/<n>/                merge attempts, their checks under checks/<n>/
│  └─ workspace/                 the workspace folder the task's binding names
│     ├─ workflow/               the workflow node, answers/, reports/, steps/<seq>-<key>/run/
│     └─ runs/<run>/             runs started directly
├─ history/<key>/                a closed task, the same structure
└─ unbound/<run>/                runs without a workspace
```

A run's folder holds `trace.json`, `status.json`, `result.json`, for a [detached run](../glossary.json#concept.detached-run) the runner's
output `host.out`, what its steps keep (such as `readiness.json` of `task-validation` and `delivery`
or a traceback), `checks/<check>/` and `workers/<worker run>/`. A worker run's folder holds
`trace.json`, `status.json`, `grant.json`, `brief.md`, `transcript.jsonl` once a session exists and
`rounds/<n>/` with each round's `trace.json`, `stderr.log` and `checks/<check>/`. A check's folder
holds `trace.json` and `output.log`.

The history key of a closed task is its name, or `<task>.<n>` with the smallest `n` from 2 that is
free when the history already holds a task of that name, so no closed task ever replaces another.

## Locks

Every lock is a file under `locks/` locked with `flock`, which the kernel releases however its
holder ends. While a process holds it, the file holds one line of JSON naming the holder,
`{"holder": "<what holds it>", "pid": <process>, "since": "<UTC time>"}`, and it is emptied before
it is released; a waiter that gives up names the holder from it. No lock file holds anything else.

| Lock | File | Taken by | Lifetime |
| --- | --- | --- | --- |
| [merge lock](../glossary.json#concept.merge-lock) | `merge.lock` | `task merge`, `task open`, `task close` | permanent |
| Issue lock | `issues.lock` of the worktree | an Issue write in that worktree | permanent |
| task lock | `tasks/<task>.lock` | every change of the task's record | removed by the close that moves the task, while it holds the lock |
| [workspace lock](../glossary.json#concept.workspace-lock) | `workspaces/<workspace>.lock` | every bound run, and `task merge` and `task close` of its task | removed by the close, while it holds the lock |
| workflow lock | `workflows/<workspace>.lock` | a [workflow step](../glossary.json#concept.workflow-step) or report while it reads and writes the workflow node | removed by the close, while it holds the workspace lock |
| [run lock](../glossary.json#concept.run-lock) | `runs/<run>.lock` | the run's runner only, from before its first progress file until after its result | the runner removes it as it exits; a file left by a runner killed with `SIGKILL` is not held |

A run is running exactly when its run lock file exists and a process holds it. An observer tries it
shared and without waiting, or reads the kernel's lock table `/proc/locks` for the file's inode,
from any PID namespace; it never decides by a recorded process identifier. The run lock of a bound
run lies under `locks/` of the `.concorde` its binding names, that of an unbound run under the
`.concorde` of the worktree it started in.

## Tracing configuration

```concorde-contract
{
  "id": "contract.tracing.configuration",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "retention"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "retention": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "unbound_days",
          "history_days"
        ],
        "properties": {
          "unbound_days": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "integer",
                "minimum": 0
              }
            ]
          },
          "history_days": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "integer",
                "minimum": 0
              }
            ]
          }
        }
      }
    }
  },
  "semantics": "The optional, Git-tracked file .concorde/tracing.json of the primary worktree. retention.unbound_days is how many days after it ended an unbound run is kept; retention.history_days how many days after its close a task stays in the history; null keeps them without removal. Without the file, unbound runs are kept 7 days and the history without removal. A malformed file refuses the command that reads it with config_invalid, naming the field. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "retention": {
      "unbound_days": 7,
      "history_days": 90
    }
  }
}
```

Retention removes only what has ended: an unbound run whose run lock is not held and whose node has
an end, and a history folder whose task node has one. It runs when `concorde trace prune` is run and
at the start of every `task open` and `task close`, and never removes a current task.

## Reading traces

```text
concorde trace show [<node>] [--depth <n>] [--format json|tree]
concorde trace list [--history] [--unbound] [--format json|tree]
concorde trace prune [--dry-run]
```

- `<node>` is a task name, a history key, a run identity, a worker run identity or the path of a
  node's folder, absolute or relative to a `.concorde` directory. Without it, `show` shows the task
  whose [workspace binding](../glossary.json#concept.workspace-binding) the current worktree holds. The command looks in the `.concorde` of the
  worktree it runs in, the `.concorde` its workspace binding names and the `.concorde` of the
  primary worktree, in that order, and in each among the current tasks, the history and the unbound
  runs. A node it cannot find is refused with `unknown_node`, naming what it searched.
- `--depth` limits how many levels below the node are shown (default: all); the roll-up always
  covers the whole subtree.
- `list` lists the current tasks, with `--history` also the history and with `--unbound` also the
  unbound runs, each as a node without its children.
- `prune` removes what the retention allows and prints what it removed; `--dry-run` prints it
  without removing anything.
- Output is one JSON value as the view contract defines; `--format tree` prints the same as an
  indented text tree instead. Exit status 0 on success, 1 for a refusal, printed as
  `{"error": <link>}`, and 2 for a malformed command line.

```concorde-contract
{
  "id": "contract.tracing.view",
  "version": 1,
  "schema": {
    "$ref": "#/$defs/view",
    "$defs": {
      "totals": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "tokens_in",
          "tokens_out",
          "tokens_cache_read",
          "tokens_cache_write",
          "cost_usd",
          "turns"
        ],
        "properties": {
          "tokens_in": {
            "type": "integer",
            "minimum": 0
          },
          "tokens_out": {
            "type": "integer",
            "minimum": 0
          },
          "tokens_cache_read": {
            "type": "integer",
            "minimum": 0
          },
          "tokens_cache_write": {
            "type": "integer",
            "minimum": 0
          },
          "cost_usd": {
            "type": "number",
            "minimum": 0
          },
          "turns": {
            "type": "integer",
            "minimum": 0
          }
        }
      },
      "view": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "id",
          "kind",
          "path",
          "status",
          "outcome",
          "started_at",
          "ended_at",
          "duration_seconds",
          "usage",
          "rolled_up",
          "metadata",
          "references",
          "error",
          "children"
        ],
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "kind": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "enum": [
              "running",
              "ok",
              "blocked",
              "failed",
              "unknown",
              "lost"
            ]
          },
          "outcome": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string"
              }
            ]
          },
          "started_at": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string"
              }
            ]
          },
          "ended_at": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string"
              }
            ]
          },
          "duration_seconds": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "number"
              }
            ]
          },
          "usage": {
            "type": "object"
          },
          "rolled_up": {
            "$ref": "#/$defs/totals"
          },
          "metadata": {
            "type": "object"
          },
          "references": {
            "type": "array",
            "items": {
              "type": "object"
            }
          },
          "error": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "object"
              }
            ]
          },
          "children": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/view"
            }
          }
        }
      }
    }
  },
  "semantics": "What concorde trace show prints for a node, and list for each node it lists (with children empty). path is the node's folder, absolute, for the reader to open. status is the node's own, except lost for a node that says running whose producing process has ended: a run whose run lock is not held, and every running node below it. duration_seconds is the node's own duration, or for a running node the time since it started. usage is the node's own usage as recorded; rolled_up sums tokens, cost and turns over the node and every node below it, counting a null as zero. metadata, references and error are the node's own. children are the nodes one level below, in the order they started, cut at the requested depth. A behaviour or field change increments the version.",
  "example": {
    "id": "retry",
    "kind": "task",
    "path": "/home/dev/shop/.concorde/tasks/retry",
    "status": "running",
    "outcome": null,
    "started_at": "2026-09-27T10:00:00Z",
    "ended_at": null,
    "duration_seconds": 1830.5,
    "usage": {
      "tokens_in": null,
      "tokens_out": null,
      "tokens_cache_read": null,
      "tokens_cache_write": null,
      "cost_usd": null,
      "turns": null,
      "duration_seconds": null
    },
    "rolled_up": {
      "tokens_in": 182000,
      "tokens_out": 21400,
      "tokens_cache_read": 1400000,
      "tokens_cache_write": 96000,
      "cost_usd": 3.42,
      "turns": 61
    },
    "metadata": {
      "task": "retry",
      "modules": [
        "module.http"
      ]
    },
    "references": [],
    "error": null,
    "children": []
  }
}
```

## Error link

An [error chain](../glossary.json#concept.error-chain) is a tree of links read from the top. The top
link is written by the actor that reports to the reader, such as the
[Operation](../glossary.json#concept.operation) in its
[run result](../glossary.json#concept.run-result) or the
[main agent](../glossary.json#concept.main-agent) in an escalation; each link's `causes` are the
errors of its children that it could not handle. The order of reading is therefore the order of
responsibility: the reader first learns what the level directly below it could not do and why, then
what that level received, down to where the error started.

```concorde-contract
{
  "id": "contract.tracing.error",
  "version": 5,
  "schema": {
    "$ref": "#/$defs/error",
    "$defs": {
      "error": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "level",
          "actor",
          "code",
          "detail",
          "evidence",
          "attempts",
          "unhandled",
          "options",
          "recommendation",
          "causes"
        ],
        "properties": {
          "level": {
            "enum": [
              "main-agent",
              "task-session",
              "workflow",
              "operation",
              "command",
              "workers",
              "worker",
              "check",
              "component"
            ]
          },
          "actor": {
            "type": "string",
            "minLength": 1
          },
          "code": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$"
          },
          "detail": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/evidence"
            }
          },
          "attempts": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "unhandled": {
            "$ref": "#/$defs/unhandled"
          },
          "options": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "recommendation": {
            "type": "string"
          },
          "causes": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/error"
            }
          }
        }
      },
      "evidence": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "kind",
          "ref",
          "detail"
        ],
        "properties": {
          "kind": {
            "type": "string",
            "minLength": 1
          },
          "ref": {
            "type": "string"
          },
          "detail": {
            "type": "string"
          }
        }
      },
      "unhandled": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "reason",
          "explanation"
        ],
        "properties": {
          "reason": {
            "enum": [
              "permission",
              "decision",
              "scope",
              "capability",
              "exhausted",
              "environment",
              "input"
            ]
          },
          "explanation": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "One error link and, through causes, the chain below it. level names the kind of actor that wrote the link: main-agent, task-session (a session working inside one task worktree for the main agent), workflow (a workflow in one workspace, reporting the runs it started), operation (an Operation run: the Execution runner and the Operation's provider steps), command (a deterministic concorde command: an execution command run, that is the Execution runner and the command's steps), workers (Workers running one worker), worker (the worker's own report, a claim), check (one configured check) or component (a deterministic component a run or command called, such as Git, Tasks, the workspace binding, the run store, Spec core or the Claude Code process). actor identifies it exactly, with the run, workspace, task, check or command concerned. code is a stable snake_case name chosen by the actor. detail describes the error completely: what failed, where, and the exact message or output; it is never only the code. evidence names the paths, commands and outputs that show it, each with a kind, a reference and a detail; evidence of kind trace names as its reference the identity of a trace node, a run or worker run identity, where a deeper analysis starts, and never replaces what the link itself says. attempts lists what the actor tried, in order. unhandled states why the actor could not handle the error itself; its reason is one of the reasons in the table below and explanation names the specifics. options and recommendation are what the actor offers its parent. causes are the errors the actor received from its children and could not handle, each exactly as its child wrote it; independent errors are siblings, and a link without causes is where an error started. A parent never edits or drops a cause. A behaviour or field change increments the version.",
  "example": {
    "level": "operation",
    "actor": "Operation implement r-20260924T093000-implement-5c1e0a77 (workspace severity)",
    "code": "checks_failed",
    "detail": "the implement worker run w-20260924T093001-implement-0f3b2a91 ended failed: checks_failed: 1 configured check(s) still fail after 4 round(s) (3 resume round(s) allowed): check.issues.tests",
    "evidence": [],
    "attempts": [],
    "unhandled": {
      "reason": "decision",
      "explanation": "the Operation used every resume round it is configured with; whether to narrow the goal, change the Spec or allow more rounds is the main agent's decision"
    },
    "options": [
      "run the Operation again with a narrower goal or more --rounds",
      "run understand to check whether the Spec supports the change"
    ],
    "recommendation": "run the Operation again with a narrower goal or more --rounds",
    "causes": [
      {
        "level": "workers",
        "actor": "Workers run w-20260924T093001-implement-0f3b2a91 (implement worker)",
        "code": "checks_failed",
        "detail": "1 configured check(s) still fail after 4 round(s) (3 resume round(s) allowed): check.issues.tests",
        "evidence": [
          {
            "kind": "trace",
            "ref": "w-20260924T093001-implement-0f3b2a91",
            "detail": "the worker run's trace node"
          }
        ],
        "attempts": [
          "round 1: the worker ended ok; failing: check.issues.tests (failed, exit 1)",
          "round 4: the worker ended ok; failing: check.issues.tests (failed, exit 1)"
        ],
        "unhandled": {
          "reason": "exhausted",
          "explanation": "Workers resumes the worker at most 3 time(s) with the failures and does not extend that"
        },
        "options": [],
        "recommendation": "",
        "causes": [
          {
            "level": "check",
            "actor": "check.issues.tests",
            "code": "check_failed",
            "detail": "the configured check check.issues.tests of module.issues failed with exit code 1; its log ends with: FAILED tests/concorde/issues/test_store.py::test_severity_round_trip - KeyError: 'severity'",
            "evidence": [
              {
                "kind": "log",
                "ref": "/home/dev/shop/.concorde/tasks/severity/workspace/runs/r-20260924T093000-implement-5c1e0a77/workers/w-20260924T093001-implement-0f3b2a91/rounds/4/checks/check.issues.tests/output.log",
                "detail": ""
              }
            ],
            "attempts": [],
            "unhandled": {
              "reason": "capability",
              "explanation": "a configured check only measures the code it runs against"
            },
            "options": [],
            "recommendation": "",
            "causes": []
          }
        ]
      }
    ]
  }
}
```

## Reading an error chain

Read a chain from the top: first the account of the actor reporting to you, then the errors it
received as causes. Each level adds its own detailed link and keeps those causes unchanged, so the
account leads back to the failure without losing what earlier levels observed or tried. A link
records the failure, the evidence and attempts, the specific reason that level cannot handle it, and
any options and recommendation it offers. Worker links are claims; the links of runs, commands and
components record observations. Evidence of kind `trace` names the trace node where a deeper
analysis of that level starts.

### Where links appear

| Where | The top link is written by |
| --- | --- |
| `error` of a [workflow result](../glossary.json#concept.workflow-result) | the workflow (`workflow`) |
| `error` of a run result | the Operation (`operation`) or the [execution command](../glossary.json#concept.execution-command) (`command`) |
| `error` of a worker [run record](../glossary.json#concept.run-record) | Workers (`workers`) |
| `error` of a [worker result](../glossary.json#concept.worker-result) | the worker, without `level`, `actor` and `causes`, which Workers adds |
| `error` of a [trace node](../glossary.json#concept.trace-node) | the node's producer, the same link its result or record carries |
| `{"error": …}` printed by a refused `concorde task`, `concorde trace` or `concorde issues` command | the refusing component (`component`) |
| an escalation recorded with `concorde task escalate` (`--by main-agent`, the default) | the main agent (`main-agent`) |
| an escalation recorded with `concorde task escalate --by task-session` | the [task session](../glossary.json#concept.task-session) (`task-session`) |

Spec tooling is the exception: it depends on no other Module and reports with its
[own error record](../spec-tooling/spec/errors.md). A Module that receives a Spec tooling error and
cannot handle it translates it into a `component` link and keeps its causes as nested links.

### Reasons

| Reason | The actor cannot handle the error because |
| --- | --- |
| `permission` | the fix needs a read, write or tool it is not granted |
| `decision` | the fix needs a decision reserved to a higher level |
| `scope` | the fix lies outside its task, its workspace or its bound Modules |
| `capability` | it has no means to repair this kind of error |
| `exhausted` | it used up its allowed rounds, turns, time or budget |
| `environment` | the environment failed and it cannot change it |
| `input` | the input it received is invalid and only its sender can correct it |
