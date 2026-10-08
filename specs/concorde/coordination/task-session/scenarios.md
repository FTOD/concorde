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

### scenario.task-session.start-failed — Claude Code starts no session

- GIVEN an open task `severity`
- AND a Claude Code that exits without reporting a started background session
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN the command fails with `session_failed`, carrying Claude Code's output
- AND the task's record and trace are unchanged

### scenario.task-session.start-unrecorded — A session started for a task that closed meanwhile is removed

- GIVEN an open task `severity`
- AND a Claude Code that reports a started background session `33afbc14`
- AND the task closes after that report and before the session is recorded
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `claude rm 33afbc14` runs
- AND the command fails with `task_closed`, saying that the session was removed
- AND when `claude rm 33afbc14` fails, the refusal names `claude rm 33afbc14` to remove it by hand

### scenario.task-session.one-working — A task session that still works refuses another start

- GIVEN an open task `severity` whose trace records the task session `33afbc14`
- AND `claude agents --json --all` lists `33afbc14` in the state `working`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN the command fails with `session_running`, naming `33afbc14`, `working` and
  `claude stop 33afbc14`
- AND no Claude Code session is started
- AND the task's boundary files, record and trace are unchanged

### scenario.task-session.replace-ended — A task session that is done or gone is replaced

- GIVEN an open task `severity` whose trace records the task sessions `33afbc14` and `44bbcd25`
- AND `claude agents --json --all` lists `33afbc14` in the state `done` and does not list
  `44bbcd25`
- WHEN the main agent runs `concorde task session severity --main concorde-8e`
- THEN a new Claude Code session is started and recorded as a third node of the task's trace
- AND the task record names `concorde-8e` as its `main`

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
- AND the session's settings disable `fresh`, `never` and `rejected`, which neither worktree
  approved or which a source rejects

### scenario.task-session.mcp-approve-all — Approving every project server enables all but the rejected

- GIVEN an open task `t1` whose task worktree lies inside the primary worktree
- AND the primary worktree's `.mcp.json` declares `concorde`, `local` and `never`
- AND the task worktree's `.mcp.json` declares `fresh`
- AND the primary worktree's local settings set `enableAllProjectMcpServers` and disable `never`
- WHEN the main agent starts its task session
- THEN the session's settings enable `fresh` and `local`
- AND the session's settings disable `concorde` and `never`

### scenario.task-session.mcp-task-approval — An approval in the task worktree alone counts

- GIVEN an open task `t1` whose task worktree lies inside the primary worktree
- AND the primary worktree's `.mcp.json` declares `concorde` and `docs`
- AND only the task worktree's local settings enable `docs`
- WHEN the main agent starts its task session
- THEN the session's settings enable `docs`
- AND the session's settings disable `concorde`

### scenario.task-session.mcp-unusable-file — An unusable `.mcp.json` names no server

- GIVEN an open task `t1` whose task worktree lies inside the primary worktree
- AND the primary worktree's `.mcp.json` is not JSON
- AND the task worktree's `.mcp.json` declares `concorde` and `local`
- AND the primary worktree's local settings enable `local`
- WHEN the main agent starts its task session
- THEN the session's settings enable `local`
- AND the session's settings disable `concorde`
- AND when the task worktree's `.mcp.json` has no `mcpServers` object instead, the session's
  settings disable only `concorde`
- AND when neither worktree has a `.mcp.json`, the session's settings disable only `concorde` and
  the session starts

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
- AND the hook denies a hook input that is not JSON or names no file
- BUT the settings restrict nothing else
- AND the settings carry no sandbox, so the session's commands reach every path, process, socket and
  network host

### scenario.task-session.closed-log — A closed task's decision log is refused

- GIVEN the hook written for a task session of task `severity`
- AND the task was closed, so its folder moved to the history
- WHEN the hook judges an Edit of the task's decision log at its former path
- THEN the hook denies it with a reason naming the closed task
- AND the task's folder is not recreated

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
- AND no `assistant` record follows that `cost-state` record
- WHEN the task is merged
- THEN the session's node in the history holds the full session id
- AND the node holds the status `ok` with the outcome `done`
- AND the node holds as usage the tokens of the three messages, each counted once
- AND the node holds as usage 3 turns
- AND the node holds as usage the duration from the transcript's earliest record time to its latest
- AND the node holds as usage a cost of 0.42 USD
- AND the node's end is the transcript's latest record time
- AND the node's content gives each model's tokens and the `cost-state` record's `modelUsage`
- AND the node's content counts no unreadable line

### scenario.task-session.cost-unaccounted — A session without a final cost account has no cost

- GIVEN a task `severity` with a task session whose transcript Claude Code keeps
- AND the session's transcript records a `cost-state` record of 0.42 USD followed by an
  `assistant` record
- WHEN the task is merged
- THEN the session's node holds as usage the tokens of every assistant record and a null cost
- AND the node's content holds no `modelUsage`
- AND when a later `cost-state` record of 0.55 USD follows that `assistant` record instead, the cost
  is 0.55 USD
- AND when the transcript has no `cost-state` record, the cost is null

### scenario.task-session.node-unlisted — A session Claude Code no longer lists keeps an unknown status

- GIVEN a task `severity` with a task session whose full session id was recorded at its start
- AND `claude agents --json --all` no longer lists the session
- AND the session's transcript is in Claude Code's project folder of the task worktree
- WHEN the task is merged
- THEN the session's node holds the transcript and its figures
- AND the node's status is `unknown` with no outcome

### scenario.task-session.unreadable-lines — Unreadable transcript lines are counted and only warn

- GIVEN a task `severity` with a task session whose transcript Claude Code keeps
- AND the transcript's last line is half written, no JSON record
- WHEN the task is merged
- THEN the session's node holds the whole transcript and figures from its records alone
- AND the node's content counts 1 unreadable line
- AND the merge's `warnings` name the session, the count and where the transcript is kept
- AND `claude rm <id>` removes the session

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

### scenario.task-session.keep-failed — A transcript that cannot be copied only warns

- GIVEN a task `severity` with a task session whose transcript Claude Code keeps
- AND copying the transcript into the session's node fails
- AND removing the partial copy fails too
- WHEN the main agent closes the task
- THEN the task is closed
- AND the close's `warnings` name the session, the copy's failure, what could not be removed and
  `claude rm <id>`
- AND the session is not removed
- AND the session's node in the history lists no transcript
