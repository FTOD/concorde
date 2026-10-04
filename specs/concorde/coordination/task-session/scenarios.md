# Task sessions scenarios

Concrete situations that show the [requirements](requirements.md) of [Task sessions](module.md).
Commands and the session's [trace node](../../glossary.json#concept.trace-node) are defined in the
[contracts](contracts.md). The contracts also define error codes.

## Starting and confining

### scenario.task-session.start — Start a task session

- GIVEN an open task `severity` and a Claude Code
  [main agent](../../glossary.json#concept.main-agent) whose session is named `concorde-7d`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `.concorde/tasks/severity/runtime/` holds a settings file and the hook of its
  [session boundary](../../glossary.json#concept.session-boundary)
- AND `claude --bg` is started in the task worktree with those settings
- AND the session starts with a first prompt naming the task, its goal and `concorde-7d`
- AND the task's [trace](../../glossary.json#concept.trace) holds the started session as the node
  `sessions/<id>/` with its identity and name
- AND the [task record](../../glossary.json#concept.task-record) names `concorde-7d` as its `main`
- AND the first prompt presents that name as the main agent's session when the task session started
- BUT when Claude Code reports no started session, the command fails with `session_failed`, carrying
  Claude Code's output
- AND when Claude Code reports no started session, the task is unchanged
- AND when the task closes after Claude Code started the session but before its recording, the
  command fails with `task_closed` after removing that session with `claude rm` and says so

### scenario.task-session.project-mcp — A task session gets the project MCP server without a channel

- GIVEN an open task `t1`
- WHEN the main agent starts its task session
- THEN `.concorde/tasks/t1/runtime/mcp.json` configures the
  [project MCP server](../../glossary.json#concept.project-mcp-server) `concorde` with
  `CONCORDE_CHANNEL` `0`
- AND `claude --bg` is started with `--mcp-config` naming that file and without any channel flag,
  since a background session is never woken by channel events

### scenario.task-session.mcp-approval — A task session is never asked to approve a project MCP server

- GIVEN an open task `t1` whose task worktree lies inside the primary worktree
- AND the primary worktree's `.mcp.json` declares `concorde`, `local`, `rejected`, `never` and
  `user.tool`
- AND the task worktree's `.mcp.json` declares `legacy`, `managed` and `fresh`
- AND the primary worktree's local settings enable `concorde`, `local` and `rejected` and disable
  `rejected`
- AND the user's settings enable `user_tool`
- AND Claude Code's global configuration enables `legacy` for the primary worktree
- AND a managed settings drop-in enables `managed`
- WHEN the main agent starts its task session
- THEN the session's settings enable `legacy`, `local`, `managed` and `user.tool`
- AND the session's settings disable `concorde`, which the `--mcp-config` server replaces
- AND the session's settings disable `fresh`, `never` and `rejected`, which the primary worktree
  never approved
- AND when the primary worktree's local settings approve every project server, all but `concorde`
  and the servers some source disables are enabled
- BUT a `.mcp.json` that is missing, not JSON or without an `mcpServers` object names no server
- AND with such a file, the session starts with only `concorde` disabled

### scenario.task-session.boundary — The session's boundary confines its writes

- GIVEN the settings written for a [task session](../../glossary.json#concept.task-session)
- WHEN its hook judges an Edit of a file in the task worktree, of the
  [decision log](../../glossary.json#concept.decision-log) and of a file of the primary worktree
- THEN the first two are allowed and the third is denied with a reason naming the task worktree
- AND the hook denies an Edit of an [Issue](../../glossary.json#concept.issue) record, which lies
  outside the task worktree
- AND the hook denies an Edit of a symbolic link in the task worktree that points to a file of the
  primary worktree
- AND the hook allows an Edit of a symbolic link in the task worktree that points inside the task
  worktree
- BUT the settings restrict nothing else
- AND the settings carry no sandbox, so the session's commands reach every path, process, socket and
  network host

## Ending with the task

### scenario.task-session.end-removed — Ending a task keeps and removes its Claude Code sessions

- GIVEN a delivered task `severity` whose trace lists two Claude Code task sessions
- AND Claude Code keeps their transcripts under `projects/` of its configuration folder
- AND one transcript is in the project folder of the task worktree and one is in another
- WHEN the main agent merges the task with `concorde task merge severity`
- THEN each session's node `sessions/<id>/` in the task's history folder holds its transcript, found
  by the session's full session id, as `transcript.jsonl`
- AND each transcript is listed with its digest among its node's artifacts
- AND each session's node holds the folder Claude Code keeps beside its transcript as `transcript/`
- AND after the task closed, `claude rm <id>` ran for each session
- AND the merge's `warnings` name none of those sessions
- AND no session was stopped, since a merge stops nothing

### scenario.task-session.node-finished — A task session's node receives its figures when the task ends

- GIVEN a task `severity` with a task session whose entry in `claude agents --json --all` has the
  state `done` and its full session id
- AND the session's transcript records two API messages, one of them over two records
- AND the session has a subagent transcript with a third message
- AND the session's transcript records a last `cost-state` record of 0.42 USD
- WHEN the task is merged
- THEN the session's node in the history holds the full session id
- AND the node holds the status `ok` with the outcome `done`
- AND the node holds as usage the tokens of the three messages, each counted once
- AND the node holds as usage 3 turns
- AND the node holds as usage the duration from the transcript's earliest record time to its latest
- AND the node holds as usage a cost of 0.42 USD
- AND the node's end is the transcript's latest record time
- AND the node's content gives each model's tokens and the `cost-state` record's `modelUsage`
- BUT for a session whose transcript has no `cost-state` record, the cost is null
- AND for a session Claude Code no longer lists, whose transcript is found by the session id
  recorded at its start, the status stays `unknown`

### scenario.task-session.close-stops — A close without a merge stops a Claude Code task session first

- GIVEN a task `severity` whose Claude Code task session still runs
- WHEN the main agent closes it with `--failed` or `--completed`
- THEN `claude stop <id>` runs while the task worktree still exists, before the close removes it
- AND after the close, the session's transcript is in its node in the history
- AND after the close, `claude rm <id>` removed the session
- AND a session Claude Code answers it no longer knows (`No job matching`) counts as stopped and
  removed

### scenario.task-session.stop-unconfirmed — A session that cannot be stopped keeps the task open

- GIVEN a task `severity` with a Claude Code task session that `claude stop` cannot confirm stopped
- WHEN the main agent closes it with `--completed` and a note
- THEN the close is refused with `session_stop_failed`, naming the session, Claude Code's answer and
  `claude stop <id>`
- AND the task's record and worktree are unchanged

### scenario.task-session.remove-best-effort — A session not removed only warns

- GIVEN a task `severity` with two Claude Code task sessions, one whose `claude rm` fails and one
  whose transcript Claude Code no longer has
- WHEN the main agent closes the task
- THEN the task is closed
- AND the close's `warnings` name the first session with Claude Code's answer and the second with
  where its transcript was looked for
- AND those warnings each give `claude rm <id>` to remove the session by hand
- AND the second session is not removed
- AND the second session's node in the history holds no transcript
