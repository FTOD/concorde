# Task sessions scenarios

Concrete situations that show the [requirements](requirements.md) of [Task sessions](module.md).
Commands, the session's [trace node](../../glossary.json#concept.trace-node) and error codes are defined in the [contracts](contracts.md).

## Starting and confining

### scenario.task-session.start — Start a task session

- GIVEN an open task `severity` and a Claude Code [main agent](../../glossary.json#concept.main-agent) whose session is named `concorde-7d`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `.concorde/tasks/severity/runtime/` holds a settings file and a [write hook](../../glossary.json#concept.write-hook)
- AND `claude --bg` is started in the task worktree with those settings and a first prompt naming the task, its goal and `concorde-7d`
- AND the task's [trace](../../glossary.json#concept.trace) holds the started session as the node `sessions/<id>/` with its identity and name
- BUT when Claude Code reports no started session, the command fails with `session_failed`, carrying Claude Code's output, and the task is unchanged

### scenario.task-session.project-mcp — A task session gets the project MCP server without a channel

- GIVEN an open task `t1`
- WHEN the main agent starts its task session
- THEN `.concorde/tasks/t1/runtime/mcp.json` configures the [project MCP server](../../glossary.json#concept.project-mcp-server) `concorde` with `CONCORDE_CHANNEL` `0`
- AND `claude --bg` is started with `--mcp-config` naming that file and without any channel flag, since a background session is never woken by channel events

### scenario.task-session.boundary — The session's boundary confines its writes

- GIVEN the settings written for a [task session](../../glossary.json#concept.task-session)
- WHEN its write hook judges an Edit of a file in the task worktree, of the [decision log](../../glossary.json#concept.decision-log) and of a file of the primary worktree
- THEN the first two are allowed and the third is denied with a reason naming the task worktree
- AND the sandbox lets Bash write only the task worktree, the Git directory, the task's folder and `.concorde/locks/` of the primary worktree and package caches
- AND the sandbox allows every network host

## Ending with the task

### scenario.task-session.end-removed — Ending a task keeps and removes its Claude Code sessions

- GIVEN a delivered task `severity` whose trace lists two Claude Code task sessions, whose transcripts Claude Code keeps under `projects/` of its configuration folder, one in the project folder of the task worktree and one in another
- WHEN the main agent merges the task with `concorde task merge severity`
- THEN each session's node `sessions/<id>/` in the task's history folder holds its transcript as `transcript.jsonl`, listed with its digest among the node's artifacts, and the folder Claude Code keeps beside it as `transcript/`
- AND after the task closed, `claude rm <id>` ran for each session, and the merge's `warnings` name none of them
- AND no session was stopped, since a merge stops nothing

### scenario.task-session.close-stops — A close without a merge stops a Claude Code task session first

- GIVEN a task `severity` whose Claude Code task session still runs
- WHEN the main agent closes it with `--failed` or `--completed`
- THEN `claude stop <id>` runs while the task worktree still exists, before the close removes it
- AND after the close, the session's transcript is in its node in the history and `claude rm <id>` removed the session
- AND a session Claude Code answers it no longer knows (`No job matching`) counts as stopped and removed

### scenario.task-session.stop-unconfirmed — A session that cannot be stopped keeps the task open

- GIVEN a task `severity` with a Claude Code task session that `claude stop` cannot confirm stopped
- WHEN the main agent closes it with `--completed` and a note
- THEN the close is refused with `session_stop_failed`, naming the session, Claude Code's answer and `claude stop <id>`
- AND the task's record and worktree are unchanged

### scenario.task-session.remove-best-effort — A session not removed only warns

- GIVEN a task `severity` with two Claude Code task sessions, one whose `claude rm` fails and one whose transcript Claude Code no longer has
- WHEN the main agent closes the task
- THEN the task is closed
- AND the close's `warnings` name the first session with Claude Code's answer and the second with where its transcript was looked for, each with `claude rm <id>` to remove it by hand
- AND the second session is not removed, and its node in the history holds no transcript
