# Tracing contracts

The canonical values and layout of [Tracing](module.md) include:

- The [trace node](../../glossary.json#concept.trace-node) record `trace.json`.
- The trace roots and where every node and lock lies.
- The Tracing configuration.
- What `concorde trace` prints.
- The error link every level reports with.

The [requirements](requirements.md) state the obligations.
The [scenarios](scenarios.md) show them at work.

## Trace node

```concorde-contract
{
  "id": "contract.tracing.node",
  "version": 5,
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
        "type": "string",
        "pattern": "^[a-z][a-z0-9-]*$"
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
              "found_commit"
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
  "semantics": "The record trace.json of one trace node, in the node's folder. id identifies the node: a run or worker run identity, which is unique in the project, or a name unique among the nodes of its kind under the same parent (a task name, a session identity, a round or merge number, a workflow step's folder name, a check identity). kind is a kind an installed part registered, as the node kinds table lists them for Concorde's parts; a node of a kind no installed part registered is refused. started_at and ended_at are RFC 3339 UTC times; ended_at is null while the node runs and for a node whose end its producer never observes. status is running until the final write, then ok, blocked or failed, or unknown for a node whose end its producer never observes; outcome is the producer's finer, snake_case account of the end (such as merged, completed, passed, timed_out, cancelled), null while running. usage is what the node itself consumed, never the sum of its children: tokens read (tokens_in), written (tokens_out), read from and written to the prompt cache, the cost in US dollars, and the agent turns, each as the agent program reported it, and the node's duration_seconds, the wall-clock time Concorde observed between its start and its end, which the library computes from started_at and ended_at at the final write when the producer gives none and the node's end was observed; a field is null when the node consumed none of it or its producer cannot observe it. error is the node's error link, following contract.tracing.error, when the node ended blocked or failed and its producer reports that end with a link, such as a run or a worker run; it is null for every other node, and for a node whose failure its parent reports, such as a worker round whose checks failed. metadata holds only the dimensions of the metadata table that the node's kind registered, a node listing another being refused, and only facts Concorde observed itself, never a statement taken from a worker result. artifacts lists files of the node's folder, each by a stable id, its path relative to the folder and its digest at the final write (null while the node runs or when the file is still growing); a conversation record listed there may be missing once retention removed it from the history. references name nodes of the same level and commits: input (the identity of a run whose output this run admitted), cites (the identity of a run this node cites as the source of what it decided), commit (a Git commit this node created) and found_commit (a Git commit an earlier node created, which this node found and reports as its outcome instead of creating one). commit is only ever what the node itself created; a node that reports existing work names it with found_commit, never with commit. content is the producer's own record, a typed value of the content type its kind registered, refused when it is of another type, and checked against the schema its producer registered for that type; null when the producer records nothing of its own. Children are not listed: they are the trace nodes in the folders below this one. No field by which the node refers to its files or to other nodes holds an absolute path; an error link or a worker's claim the node keeps is kept as it was reported. A behaviour or field change increments the version.",
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

Each kind has one producer. The producer writes its nodes' records. The producer chooses their
content. Each kind has one place below its parent. When its code loads, the part a producer belongs
to registers its kinds with Tracing's library. It registers them as it registers the types of its
[typed values](../../glossary.json#concept.typed-value). Each kind's registration includes its
content type and the metadata dimensions it provides. Tracing names no kind itself. A write is
refused as a defect of its producer in these cases:

- When no installed part registers the node's kind, the write is refused with `node_invalid`.
- When a metadata dimension is not one its kind provides, the write is refused with `node_invalid`.
- When the content is of another type than its kind's, the write is refused with `content_invalid`.

The table lists the kinds of Concorde's parts. When a kind's part is not installed, that kind simply
never occurs. For the top nodes of a [trace root](#trace-roots), the folders are relative to the
`.concorde` directory. For other nodes, the folders are relative to the parent node's folder.

| Kind | Producer | Folder | Identity | Metadata it provides | Content type |
| --- | --- | --- | --- | --- | --- |
| `task` | [Tasks](../../coordination/tasks/module.md) | `tasks/<task>/`, moved to `history/<key>/` | the task name | `task`, `modules`, `branch`, `base_commit`, `concorde_commit`, `protocol_version` | `concorde-task-trace` |
| `session` | [Task sessions](../../coordination/task-session/module.md) | `sessions/<session>/` | the session identity | `task`, `model` | `concorde-session-trace` |
| `merge` | Tasks | `merges/<n>/` | the attempt number | `task`, `branch`, `commit` | `concorde-merge-trace` |
| `merge-check` | Tasks | `checks/<n>/` of a merge | the check's number | none | `concorde-merge-check-trace` |
| `delivery` | Tasks | `deliveries/<n>/` of a task, for `task deliver` | the attempt number | `task`, `branch`, `commit` | `concorde-delivery-trace` |
| `delivery-check` | Tasks | `checks/<n>/` of a delivery | the check's number | none | `concorde-delivery-check-trace` |
| `workflow` | [Workflows](../../workflows/module.md) | `workflow/` of a workspace folder | the workflow name | `workspace`, `workflow`, `mode` | `concorde-workflow-trace` |
| `step` | Workflows | `steps/<seq>-<key>/` of the workflow | its folder name `<seq>-<key>`, one node per attempt of a [step key](../../glossary.json#concept.step-key) | `workspace`, `workflow`, `operation` or `command` | `concorde-step-trace` |
| `run` | [Execution](../../execution/module.md) | `runs/<run>/` of a workspace folder, `run/` of a step, `unbound/<run>/`, or `lobby/<run>/` until a bound run enters its workspace | the run identity | `workspace`, `modules`, `operation` or `command`, `commit`, `base_commit`, `concorde_commit`, `protocol_version` | `concorde-run-trace` |
| `check` | [Check execution](../../execution/checks/module.md) | `checks/<check>/` of a run or a worker round | the check identity | `check`, `module` | `concorde-check-trace` |
| `worker-run` | [Workers](../../worker-harness/workers/module.md) | `workers/<worker run>/` of a run | the worker run identity | `modules`, `operation`, `worker`, `task_type`, `backend`, `model`, `reasoning`, `context_identity`, `grant_digest`, `brief_digest`, `settings_digest` | `concorde-worker-run-trace` |
| `worker-round` | Workers | `rounds/<n>/` of a worker run | the round number | `backend`, `model` | `concorde-worker-round-trace` |

A workspace folder, `workspace/` of a task, is no node of its own. The reading command shows the
folder as a `workspace` node. That node's children are its workflow and its runs. The reading command
names that node after the workspace its runs record. Because the folder has no record, it has no
status of its own. The reading command shows its status as follows:

- While any of its children runs, it shows `running`.
- When it has children but none runs, it shows the status of its most recently started child,
  `lost` included.
- Without children, it shows `unknown`.

A node lists in `metadata` only the dimensions its row names. A producer's own
[Spec](../../glossary.json#concept.spec) defines its content type.

### Metadata dimensions

| Dimension | Meaning |
| --- | --- |
| `task` | the task the node belongs to, only on Coordination's nodes |
| `workspace` | the workspace a run or workflow worked in, from its binding |
| `modules` | the [Modules](../../glossary.json#concept.module) the node worked on |
| `branch`, `base_commit` | the branch and the commit the task or workspace works from |
| `commit` | the commit the node examined (an [unbound run](../../glossary.json#concept.unbound-run)) or produced (a merge), or the `HEAD` a bound run started on |
| `operation`, `command` | the Operation or execution command that ran |
| `workflow`, `mode` | the workflow and its mode |
| `task_type`, `worker` | a worker's [task type](../../glossary.json#concept.task-type) and [worker id](../../glossary.json#concept.worker-id) |
| `backend`, `model`, `reasoning` | the agent program, model and reasoning level a worker or session ran on, as configured; absent when the program's default applied |
| `context_identity`, `grant_digest`, `brief_digest`, `settings_digest` | the identity and digests of what a worker was given |
| `check`, `module` | a check's identity and the Module it checks |
| `concorde_commit` | the commit of the Concorde code that wrote the node, when that code is a Git checkout, or the commit its installation records |
| `protocol_version` | the Spec Protocol version the project configuration binds |

### Writing a node

- When the node starts, before the work it records begins, the producer writes `trace.json` with
  `status` `running`. When the node ends, the producer writes `trace.json` again with the following:
  - Its end.
  - Its status.
  - Its outcome.
  - Its usage.
  - Its error.
  - Its artifacts.
  - Its content.

  The producer may rewrite `trace.json` in between, such as a worker run after each round. Every
  write replaces the file atomically. Because of this atomic replacement, a reader never finds half
  a record. When the operating system
  refuses a write, that refusal never changes the work the node records. A refusal while the
  library inspects the node's artifacts for that write is such a refusal too. The library keeps an
  account of each such failure. Each account names the following:
  - The file.
  - The moment: start, update or end.
  - The error.

  The producer reports every such failure in its own result, as evidence or a warning.
- Before starting the child's process, the parent creates the child's folder or names it to that
  process. This happens before the child's first write. A child never records its parent's identity.
- Every artifact path is relative to the node's folder. Every other node is named by identity.
- A file that grows while the node runs, such as a transcript or a log, is an artifact of the node.
  The file's content is never copied into `trace.json`.
- The live [progress file](../../glossary.json#concept.progress-file) `status.json` of a run or worker
  run stays a separate file of the node's folder. A
  [run result](../../glossary.json#concept.run-result) `result.json` also stays a separate file of
  the node's folder. Both files are listed among the node's artifacts.

## Trace roots

A part that keeps the top nodes of traces registers each **trace root** with Tracing in its
[part registration](../../glossary.json#concept.part-registration). Each registration names the
following:

- The trace root's name.
- The trace root's folder relative to a `.concorde` directory.
- Whether that directory is the primary worktree's or the one of the worktree a node started in.
- The kind of the trace root's top nodes.
- Whether the trace root's folders are **current** (still written) or **closed** (never changed again).
- Which option of `concorde trace list` lists the trace root's top nodes: always, `--history`,
  `--unbound` or none.
- The node's field that dates its end.
- The retention periods that apply to the trace root.
- The kind of lock whose holder says the node is still written. The lock is named after a top node's identity.
- The files that count as the trace root's **conversation records**.

Tracing performs the following actions on the registered roots of the installed parts and no other
folder:

- Searches.
- Lists.
- Prunes.

When its code loads, a part registers its roots with Tracing's library. The registration comes from
a module its part registration names among those Distribution loads. Before Distribution routes
any command of a part, including `concorde trace`, Distribution loads those modules.
Concorde's parts register these:

| Root | Folder | Registered by | Top nodes | State | Listed | Retention |
| --- | --- | --- | --- | --- | --- | --- |
| current tasks | `tasks/<task>/` of the primary worktree | Coordination ([Tasks](../../coordination/tasks/module.md)) | `task` | current | always | none: a current task is never pruned |
| history | `history/<key>/` of the primary worktree | Coordination | `task` | closed | with `--history` | `conversation_days` for its conversation records, then `history_days` for the folder |
| unbound runs | `unbound/<run>/` of the worktree the run started in | [Execution](../../execution/module.md) | `run` | current until it ended | with `--unbound` | `unbound_days` after the run ended and while its run lock is not held |
| lobby | `lobby/<run>/` of the `.concorde` the run's binding names | Execution | `run` | current until it ended or entered its workspace | never; found by its identity | `unbound_days` after the run ended and while its run lock is not held |

## Layout

The layout below combines the registered roots with Tracing's own `locks/` and `tracing.json`.
Except for unbound runs and their [run locks](../../glossary.json#concept.run-lock), these lie under
the `.concorde` directory of the project's primary worktree. The exceptions lie under the
`.concorde` of the worktree they started in. Every write of an [Issue](../../glossary.json#concept.issue) takes the
primary worktree's [merge lock](../../glossary.json#concept.merge-lock), as [Locks](#locks) says.
Git ignores `locks/` and every root's folder:

- `tasks/`
- `history/`
- `unbound/`
- `lobby/`

Coordination decides what lies inside a task's folder. The tree shows that content as Concorde's
parts lay it out.

```text
.concorde/
├─ tracing.json                  the Tracing configuration (tracked, optional)
├─ decisions/<key>.md            each ended task's decision log, committed by Tasks (tracked)
├─ locks/                        every lock and nothing else
├─ tasks/<task>/                 a current task
│  ├─ task.json                  the task record
│  ├─ trace.json                 the task's node
│  ├─ decisions.md               the decision log
│  ├─ runtime/                   the task session's boundary configuration, removed at close
│  ├─ sessions/<session>/        session nodes
│  ├─ merges/<n>/                merge attempts, their checks under checks/<n>/, and the
│  │                             output.json and messages.log of a merge the server started
│  └─ workspace/                 the workspace folder the task's binding names
│     ├─ workflow/               the workflow node, answers/, reports/, steps/<seq>-<key>/run/
│     └─ runs/<run>/             runs started directly
├─ history/<key>/                a closed task, the same structure
├─ unbound/<run>/                runs without a workspace
└─ lobby/<run>/                  bound runs that do not hold their workspace's lock yet, and those
                                 refused before they held it
```

Until a bound run holds its workspace's lock, its node lies in the **lobby**. Once the run holds
the lock, its node moves whole to its place in the workspace folder. This prevents writing anything
of a run that may never be admitted into a workspace folder. While a close holds that lock, it
moves the workspace folder to the history
([Execution's lobby](../../execution/runner.md#the-lobby)). A run refused or cancelled before it held
the lock keeps its node in the lobby. That run is no run of the workspace's folder. It is found by
its identity.

A run's folder holds:

- `trace.json`
- `status.json`
- `result.json`
- For a [detached run](../../glossary.json#concept.detached-run), the runner's output `host.out`
- What its steps keep (such as `readiness.json` of `task-validation` and `delivery` or a traceback)
- `checks/<check>/`
- `workers/<worker run>/`

A worker run's folder holds:

- `trace.json`
- `status.json`
- `grant.json`
- `brief.md`
- Once a session exists, `transcript.jsonl`
- `rounds/<n>/`

Each round's folder holds:

- `trace.json`
- `stderr.log`
- `checks/<check>/`

A check's folder holds `trace.json` and `output.log`. A merge attempt's folder holds `trace.json`
and `checks/<n>/`. For a merge the project MCP server started, the folder also holds:

- The merge's standard output `output.json`
- The merge's standard error `messages.log`

After the close moves the folder to the history, the merge that closed the task finishes these
output files.

Tasks chooses the history key of a closed task. When the task's name is free, the key is its name.
When that name is taken, the key is `<task>.<n>` with the smallest free `n` from 2.
The name is taken when either condition holds:

- The history already holds a task of that name.
- A [decision log](../../glossary.json#concept.decision-log) `decisions/<name>.md` exists.

Thus, no closed task ever replaces another in the history or in Git.

Coordination registers a task's **conversation records** for its history. These are the transcripts
of its task sessions and worker runs. They comprise every file `transcript.jsonl` and every folder
`transcript/` in the task's folder, at any depth.

## Locks

Every lock is a file under `locks/` locked with `flock`. However its holder ends, the operating
system releases the lock. While a process holds the lock, the file holds one line of JSON naming
the holder: `{"holder": "<what holds it>", "pid": <process>, "since": "<UTC time>"}`.
When the holder's environment names a session in `CLAUDE_CODE_SESSION_ID`, the line includes
`"session": "<Claude Code session>"`. When the taker names the task it works for, the line includes
`"task": "<task>"`. Before the lock is released, the file is emptied. A waiter that gives up names
the holder from the file, with its session and task. No lock file holds anything else. Execution
never names a task. The holder lines of Execution's runs name the workspace in `holder` only.
Only Tasks and the [project MCP server](../../glossary.json#concept.project-mcp-server) name a task.

| Lock | File | Taken by | Lifetime |
| --- | --- | --- | --- |
| [merge lock](../../glossary.json#concept.merge-lock) | `merge.lock` | `task merge`, `task open`, `task close` and every write of an [Issue](../../glossary.json#concept.issue) | permanent |
| task lock | `tasks/<task>.lock` | every change of the task's record | removed by the close that moves the task, while it holds the lock |
| [workspace lock](../../glossary.json#concept.workspace-lock) | `workspaces/<workspace>.lock` | every bound run, and `task merge` and `task close` of its task | removed by the close, while it holds the lock; a run that waited for it takes the removed file and is refused, never the file a later taker creates |
| workflow lock | `workflows/<workspace>.lock` | a [workflow step](../../glossary.json#concept.workflow-step) or report while it reads and writes the workflow node, and `task close` of its task and the close that ends its `task merge`, each after the workspace and merge locks | removed by the close, while it holds the lock; a step or report that waited for it takes the removed file and is refused, never the file a later taker creates |
| [run lock](../../glossary.json#concept.run-lock) | `runs/<run>.lock` | the run's runner only, from before its first progress file until after its result | the runner removes it as it exits; a file left by a runner killed with `SIGKILL` is not held |
| merge attempt lock | `attempts/<task>.lock` | `task merge` of the task only, from before it waits for its other locks until it has written its answer, and the [project MCP server](../../glossary.json#concept.project-mcp-server)'s call that hands it to that merge | the merge removes it as it ends; a file left by a merge killed with `SIGKILL` is not held |

<a id="handing-a-lock-on"></a>

**Handing a lock on.** A process that holds a lock may hand it to a process it starts or to the
program it replaces itself with by `exec`. It passes the locked descriptor to that process.
The receiving process inherits the same open file description and, with it, the `flock`.
The handing process names the descriptor in the receiving process's environment variable
`CONCORDE_INHERITED_LOCKS`, a JSON object `{"<lock file>": <descriptor>}`. The library in the
receiving process reads and removes the variable once. This prevents any process it starts in turn
from believing it inherited the locks. When the library takes a lock named there, it checks both
conditions:

- The descriptor refers to the lock file there now.
- The descriptor holds that file's lock.

When both conditions hold, the library performs these steps:

- It adopts the descriptor without waiting.
- It marks the descriptor not inherited by the processes it starts.
- It writes its own holder line.

Otherwise, it closes the descriptor and takes the lock as usual.
Once the handing process closes its own descriptor or replaces itself, the lock is released
exactly when the receiving process ends. The operating system's lock table keeps naming the
process that first took the lock. Therefore, the holder line, not `/proc/locks`, says who holds a
handed lock.

**Waiting for a release.** A process that waits for a lock to be released performs these steps:

- It opens the lock's file.
- It asks for a shared `flock`, blocking, in a thread of its own.
- It lets go of the shared lock at once.

When the holder releases the lock or dies, the operating system grants the shared lock. A lock
whose file is missing is free. When a holder lets go, a lock whose file was removed while that
holder held it, such as a run lock, is released.
To learn when a lock is next taken, a process watches the lock's directory through the operating
system's file change notification. The file changes are:

- Taking a lock writes its holder line.
- Releasing a lock empties the file.
- A close removes the file.

A run is running exactly when its run lock file exists and a process holds it.
From any PID namespace, an observer uses either method:

- It tries the lock shared and without waiting.
- It reads the operating system's lock table `/proc/locks` for the file's device and inode.

It uses both the device and inode since an inode number is unique only within its filesystem.
The observer never decides by a recorded process identifier. The run lock
of a bound run lies under `locks/` of the `.concorde` its binding names. The run lock of an unbound
run lies under the `.concorde` of the worktree it started in.

## Tracing configuration

```concorde-contract
{
  "id": "contract.tracing.configuration",
  "version": 4,
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
          },
          "conversation_days": {
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
  "semantics": "The optional, Git-tracked file .concorde/tracing.json of the primary worktree. retention.unbound_days is how many days after it ended an unbound run, or a run that never left the lobby, is kept; retention.history_days how many days after its close a task stays in the history; retention.conversation_days how many days after its close a task in the history keeps its conversation records (the layout names them), everything else of it staying as long as history_days allows; null keeps them without removal. Each period may be left out. Without the file, or for a period it leaves out, unbound runs and the runs of the lobby are kept 7 days, the history without removal and its conversation records 30 days: a file holding only conversation_days keeps the defaults of the other two. Each period applies to the trace roots registered with it: unbound_days to Execution's unbound runs and lobby, history_days and conversation_days to Coordination's history; a period of a root no installed part registers is ignored. A malformed file refuses the command that reads it with config_invalid, naming the field. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "retention": {
      "unbound_days": 7,
      "history_days": 90,
      "conversation_days": 30
    }
  }
}
```

Retention removes only what ended, root by root as each was registered:

- When all these conditions hold, retention removes an unbound run or a run of the lobby:
  - The period `unbound_days` after the run's end is over.
  - The run's run lock is not held.
  - The run's node has an end.
- A history folder whose task node has an end.
- The conversation records of such a history folder.

Each period applies to the roots that name it. A period of a root no installed part registers is
read and ignored. When `concorde trace prune` runs, retention runs. Whenever a part that registers
a root asks for retention, retention runs. Tasks asks for retention at the start of every
`task open` and `task close`. Retention never removes anything of a current folder.

## Reading traces

```text
concorde trace show [<node>] [--depth <n>] [--format json|tree]
concorde trace list [--history] [--unbound] [--format json|tree]
concorde trace prune [--dry-run]
```

- `<node>` is one of the following:
  - A task name.
  - A history key.
  - A run identity.
  - A worker run identity.
  - The path of a node's folder, absolute or relative to a `.concorde` directory.

  Without `<node>`, `show` shows the task whose
  [workspace binding](../../glossary.json#concept.workspace-binding) the current worktree holds.
  The command looks in these directories, in this order:
  - The `.concorde` of the worktree it runs in.
  - The `.concorde` its workspace binding names.
  - The `.concorde` of the primary worktree.

  In each directory, the command looks among the registered roots by the place each was registered
  with. The command never looks for a root of the primary worktree's `.concorde` under a linked
  worktree's `.concorde`. The command looks for a root of the worktree a node started in under any
  of these directories. In Concorde these roots are:
  - The current tasks.
  - The history.
  - The unbound runs.
  - The lobby.

  A task name and a history key can be the same text: a task closed into `history/<name>/` and a
  later task of that name. In each directory, the command tries a name among the roots in the
  order their parts registered them, and takes the first node it finds. In Concorde that order is
  the current tasks, the history, the unbound runs and the lobby, so the current task is shown.
  The closed task is shown by its folder, `history/<key>`.

  The command accepts a folder only when it lies in the folder of a registered root that the
  command looks for in a searched directory, or in the workspace folder the current worktree's
  binding names. The command refuses any other folder, absolute or relative, with `unknown_node`
  even when the folder exists.

  When the command cannot find a node, it refuses the node with `unknown_node`. The refusal names
  what the command searched.

  The command reads a node's children as the nearest folders below it that hold `trace.json`,
  whatever those folders are named. Tracing reserves no folder name. The command reads only the
  stored `schema_version` 1 of the [node contract](#contract.tracing.node), and it migrates no
  record. When the requested node's `trace.json` is missing, cannot be read, is no JSON object, has
  another `schema_version` or breaks the node contract, the command refuses the node with
  `node_unreadable`. The refusal names the file and the reason. When such a record lies below the
  requested node, or is a top node that `list` lists, the command does not refuse. It shows that
  node with status `unreadable` and its `reason`, as the [view contract](#contract.tracing.view)
  says, and goes on reading. Its totals then count only the nodes it could read.
- `--depth` limits how many levels below the node are shown (default: all). The roll-up always
  covers the whole subtree.
- `list` lists the top nodes of the registered roots in this order:
  - Those each root's registration lists always.
  - With `--history`, also those each root's registration lists with that option.
  - With `--unbound`, also those each root's registration lists with that option.

  This order applies whichever `.concorde` directory each root lies in. Each top node appears as a
  node without its children. `list` uses the same `.concorde` directories and the same places as
  `show`. In Concorde these roots are:
  - The current tasks.
  - The history.
  - The unbound runs.

  An option whose roots no installed part registers lists nothing.
- `prune` removes what the retention allows under the same `.concorde` directories and by the same
  places as `show`. It uses the [Tracing configuration](#tracing-configuration) of the primary
  worktree. Thus, an unbound run is pruned from the worktree it started in. It prints
  `{"removed": [<path>…], "failed": [{"path": <path>, "error": <text>}…], "dry_run": <boolean>}`.
  The output names the paths it removed, folders and conversation records alike. It also names
  each path the operating system did not let it remove wholly, with the error. The next prune
  tries each such path again. With `--dry-run`, `prune` prints what it would remove without
  removing anything.
- Output is one JSON value:
  - `show` prints one view object of the [view contract](#contract.tracing.view): the node with
    its children.
  - `list` prints one JSON array. It holds one view object per top node it lists, in the order
    above, each with `children` empty. When it lists nothing, the array is empty: `[]`.
  - `prune` prints the object given above.

  For example, `concorde trace list --unbound` in a project with one current task and one unbound
  run prints:

  ```json
  [
    {
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
      "reason": null,
      "children": []
    },
    {
      "id": "r-20260927T090000-understand-00000001",
      "kind": "run",
      "path": "/home/dev/shop/.concorde/unbound/r-20260927T090000-understand-00000001",
      "status": "ok",
      "outcome": "ok",
      "started_at": "2026-09-27T09:00:00Z",
      "ended_at": "2026-09-27T09:04:10Z",
      "duration_seconds": 250.0,
      "usage": {
        "tokens_in": null,
        "tokens_out": null,
        "tokens_cache_read": null,
        "tokens_cache_write": null,
        "cost_usd": null,
        "turns": null,
        "duration_seconds": 250.0
      },
      "rolled_up": {
        "tokens_in": 41000,
        "tokens_out": 3900,
        "tokens_cache_read": 210000,
        "tokens_cache_write": 18000,
        "cost_usd": 0.61,
        "turns": 12
      },
      "metadata": {
        "operation": "understand",
        "modules": [
          "module.http"
        ]
      },
      "references": [],
      "error": null,
      "reason": null,
      "children": []
    }
  ]
  ```

  With `--format tree`, output is instead a summary of that value as an indented text tree. For
  `list`, the tree holds one top line per listed node, or `(no traces)` when it lists none. Each node occupies one line with:
  - Its kind.
  - Its identity.
  - Its status.
  - Its outcome.
  - Its duration.
  - Its rolled-up cost and tokens.
  - Its metadata naming what ran.
  - Its error's code.
  - For an `unreadable` node, its reason.

  The JSON output alone carries every field. Exit status is:
  - 0 on success.
  - 1 for a refusal, printed as `{"error": <link>}`.
  - 2 for a malformed command line.

```concorde-contract
{
  "id": "contract.tracing.view",
  "version": 3,
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
          "reason",
          "children"
        ],
        "properties": {
          "id": {
            "type": "string",
            "minLength": 1
          },
          "kind": {
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
              "lost",
              "unreadable"
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
          "reason": {
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
  "semantics": "What concorde trace show prints for a node, and list for each node it lists (with children empty). path is the node's folder, absolute, for the reader to open. status is the node's own, except lost for a node that says running whose producing process has ended: a run whose run lock is not held, and every running node below it, whether it is shown below that run or addressed directly; a workspace node, which has no record, is running while any of its children runs, otherwise has the status of its most recently started child, and unknown without children. duration_seconds is the node's own duration, or for a running node the time since it started. usage is the node's own usage as recorded; rolled_up sums tokens, cost and turns over the node and every node below it, counting a null as zero. metadata, references and error are the node's own. A node below the requested one, or a top node list lists, whose trace.json cannot be read, is no JSON object, has a schema_version other than 1 or breaks contract.tracing.node, is shown with status unreadable: its id is its folder's name, its kind, outcome, times, duration and error are null, its usage is all null, its metadata and references are empty, and reason is the read error, naming the file; its children are still read, and its rolled_up sums only theirs. reason is null for every other node. children are the nodes one level below, in the order they started, cut at the requested depth. A behaviour or field change increments the version.",
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
    "reason": null,
    "children": []
  }
}
```

## Error link

An [error chain](../../glossary.json#concept.error-chain) is a tree of links read from the top. The actor
that reports to the reader writes the top link. Examples are the
[Operation](../../glossary.json#concept.operation) in its
[run result](../../glossary.json#concept.run-result) or the
[main agent](../../glossary.json#concept.main-agent) in an escalation. Each link's `causes` are the
errors of its children that the link's writer could not handle. The order of reading is therefore the order
of responsibility. The reader first learns what the level directly below it could not do and why.
The reader then learns what that level received, down to where the error started.

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

Read a chain from the top. First read the account of the actor reporting to you, then the errors it
received as causes. Each level adds its own detailed link. Each level keeps those causes unchanged.
The account therefore leads back to the failure without losing what earlier levels observed or
tried. A link records:

- The failure.
- The evidence and attempts.
- The specific reason that level cannot handle the failure.
- Any options and recommendation it offers.

Worker links are claims. The links of these actors record observations:

- Runs.
- Commands.
- Components.

Evidence of kind `trace` names the trace node where a deeper analysis of that level starts.

### Where links appear

| Where | The top link is written by |
| --- | --- |
| `error` of a [workflow result](../../glossary.json#concept.workflow-result) | the workflow (`workflow`) |
| `error` of a run result | the Operation (`operation`) or the [execution command](../../glossary.json#concept.execution-command) (`command`) |
| `error` of a worker [run record](../../glossary.json#concept.run-record) | Workers (`workers`) |
| `error` of a [worker result](../../glossary.json#concept.worker-result) | the worker, without `level`, `actor` and `causes`, which Workers adds |
| `error` of a [trace node](../../glossary.json#concept.trace-node) | the node's producer, the same link its result or record carries |
| `{"error": …}` printed by a refused `concorde task`, `concorde trace` or `concorde issues` command | the refusing component (`component`) |
| an escalation recorded with `concorde task escalate` (`--by main-agent`, the default) | the main agent (`main-agent`) |
| an escalation recorded with `concorde task escalate --by task-session` | the [task session](../../glossary.json#concept.task-session) (`task-session`) |

When a component reports an exception it has no recovery for, it writes a `component` link through
Tracing's library. The link's detail is the exception's type and message. For a command that failed,
the detail also includes these, each named:

- Its exit status.
- Its standard output.
- Its standard error.

When a stream is longer than 20,000 characters, the link quotes the stream from its end. The quote
says how many characters it leaves out. When the component keeps a traceback file, named in the
link's evidence, that file holds the whole streams too.

Spec tooling is the exception. It depends on no other Module. It reports with its
[own error record](../../spec-tooling/spec/errors.md). When a Module receives a Spec tooling error and
cannot handle it, the Module translates the error into a `component` link. The Module keeps the
error's causes as nested links.

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

## Library

The [tracing library](module.md#realization.tracing.library) gives every producer the same
operations on these contracts. It is the Python package `concorde.kernel.tracing`. The error chain
code is the module `concorde.kernel.errors`. Their callables are those of the installed Concorde,
which installs every part from one checkout. They promise no compatibility with another version.
A name that starts with `_` belongs to no promise.

Each operation is one callable of a module of that package, named in the table as
`<module>.<callable>` with its arguments. Arguments after `*` are passed by name. These
conventions hold for every operation:

- A path argument is a `pathlib.Path`. `concorde` is a `.concorde` directory. A record is a
  `dict` holding JSON values.
- Each module refuses with its own exception. The exception carries a stable `code`, except
  `LockBusy` and `LockGone`, and `str()` of it is the whole message. The table names each.
- A lock is held by a context manager. The `with` block holds it. The lock is released when the
  block ends, however it ends. The block receives the seconds spent waiting. A `wait` of `None`
  waits as long as the lock is held. An operating-system error of the lock file passes as
  `OSError`.
- A failed write of a node's `trace.json` is no refusal. `Node` keeps its account in the list
  `failures`, as [Writing a node](#writing-a-node) says.

| Operation | Call | Takes | Returns | Refuses with |
| --- | --- | --- | --- | --- |
| Register node kinds | `kinds.register(*kinds)`, each a `kinds.NodeKind(kind, content_type, metadata)` | each kind's name, its content type and the tuple of its metadata dimensions | nothing; an equal kind registered again changes nothing | `kinds.KindError`: `invalid_kind`, `duplicate_kind` (the first registration stays) |
| Look a kind up | `kinds.lookup(kind)`, `kinds.registered()` | a kind's name, or nothing | its registration or `None`; every registered kind | nothing |
| Register a trace root | `roots.register(root)`, with `roots.TraceRoot(name, folder, place, kind, state, listed, ...)` | the fields of [Trace roots](#trace-roots) | nothing; an equal root registered again changes nothing | `roots.RootError`: `invalid_root`, `duplicate_root` |
| Find a folder or a lock file | `layout.run_folder(workspace, run_id)`, `layout.worker_folder(run, worker_run)`, `layout.round_folder(parent, number)`, `layout.checks_folder(parent)`, `layout.check_folder(checks, check_id)`, `layout.step_folder(workflow, number, key)`, `layout.lock_file(concorde, kind, name=None)` | the parent's folder or the `.concorde` and the names of [Layout](#layout) | the path, never created | `ValueError` for a lock that needs a name and has none or an unsafe one |
| Make a node | `node.Node(folder, identity, kind, *, metadata=None, references=None, content_type=None, content=None, started_at=None)` | the folder its parent chose, its identity, its kind, and its content type when it records content | the node, not written yet, `running`, started now unless `started_at` says otherwise | `node.TraceError`: `node_invalid` (a metadata dimension that does not exist), `content_invalid` |
| Name an artifact or a reference | `Node.keep(identity, relative, *, measured=True)`, `Node.refer(relation, target)` | a file of the folder, or a relation and its target | nothing; a repeated identity or reference is kept once | nothing; the next write refuses what breaks the node contract |
| Write the node's start | `Node.start()` | nothing | the node | `TraceError`: `node_invalid`, `content_invalid` |
| Write the node again while it runs | `Node.update(*, content=None, **metadata)` | new content or metadata | nothing | `TraceError`: `node_invalid`, `content_invalid` |
| Write the node's end | `Node.finish(status, *, outcome=None, error=None, used=None, content=None, ended_at=None, **metadata)` | the status, the finer outcome, the error link, the node's own usage fields | the record as written | `TraceError`: `node_invalid`, `content_invalid` |
| Check, write or read a record | `node.check(record)`, `node.write(folder, record)`, `node.read(folder)` | a whole record, or a folder | the record; the path of the `trace.json` written; the record or `None` when none can be read | `TraceError`; `write` passes an operating-system error as `OSError` |
| Take a lock | `with locks.hold(path, holder, *, wait=0, waiting=None, task=None, retake=True) as waited:` | the lock file, the holder's name, how long to wait, a callable told the holder once when the wait begins, the task, and whether to take a file its holder replaced meanwhile | holds it for the block | `locks.LockBusy` (`holder`, `entry`, `waited`), `locks.LockGone` (with `retake` false) |
| Hand held locks on | `with locks.handed_on(*paths) as (environment, descriptors):` | lock files this process holds through `hold` | the variables to add to the started process's environment and the descriptors it must inherit, as [Handing a lock on](#handing-a-lock-on) says | `ValueError` for a lock this process does not hold |
| Read a lock's holder | `locks.holder(path)`, `locks.entry(path)` | a lock file | its holder line as text, or as an object; `None` when nobody holds it | nothing |
| Wait for a lock's release | `locks.wait_released(path, timeout=None)` | a lock file and the longest wait in seconds | `True` once nobody holds it, `False` when the timeout passed first | nothing |
| Wait for files to change | `watch.Changes(directory, names=None)`, then `.wait(timeout=None)` and `.close()` | a directory and the file names to watch | `True` once one changed since the last call, `False` when the timeout passed first | `watch.WatchError` |
| Tell a run lost | `reader.run_alive(concorde, run_id)` | the `.concorde` whose `locks/` holds the run lock, and the run's identity | whether its runner still runs | nothing |
| Find, show or list nodes | `reader.concorde_directories(here)`, `reader.locate(address, searched, extra=None)`, `reader.view(folder, concorde, *, depth=None)`, `reader.listing(concorde, *, history=False, unbound=False)` | as [Reading traces](#reading-traces) says | the directories searched; the node's folder and its `.concorde`; one view; the list of views | `reader.ReadError`: `unknown_node`, `node_unreadable` |
| Prune | `retention.prune(concorde, *, dry_run=False)` | a `.concorde` | `{"removed": [...], "failed": [...]}` | `retention.ConfigError`: `config_invalid` |
| Build an error link | `errors.link(level, actor, code, detail, *, reason, explanation, evidence=(), attempts=(), options=(), recommendation="", causes=())`, `errors.from_exception(actor, error, *, code="unexpected_error", reason="capability", explanation="", trace=None)` | the fields of the [error contract](#contract.tracing.error) | the link | `ValueError` for a level or reason the contract does not name |
| Check or render a chain | `concorde.kernel.schema.validate(link, errors.ERROR_SCHEMA)`, `errors.render(link)` | a link | nothing; the chain as indented text | `KernelError` `invalid_field` |

For example, the check service registers its node kind `check` when its code loads. The kind's
content type is the check's own typed value, and its metadata dimensions are `check` and
`module`. Registering it again changes nothing. For one check of a run, the service asks
`layout.checks_folder` and `layout.check_folder` for the folder below the run's node. It makes a
`Node` of kind `check` there. It names its log with `keep` and writes the start with `start`.
When the check ends, it writes the end with `finish("ok", outcome="passed", used=...)`. When
the operating system refused a write, the work goes on. The service then reads the node's
`failures` and reports each in its own result.
