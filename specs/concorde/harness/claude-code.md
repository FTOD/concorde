# Claude Code harness mechanics

The exact files the Harness generates to apply a harness to a Claude Code agent: the worker
settings with their deny rules, write hook and Bash sandbox, the tool sets per task type, and the
task-session settings. The [entry](module.md) explains why a harness is applied this way; the
[pi mechanics](pi.md) state what the pi backend generates instead, and
[the run mechanics](../agents/workers/launch.md) of Workers where these files are placed in a run.

## Worker settings

On the Claude Code backend `control/settings.json` has this shape; paths are absolute:

```json
{
  "permissions": {
    "deny": ["Read(//<worktree>/secrets/**)", "Edit(//<worktree>/specs/shop/module.md)", "..."]
  },
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit|Write|MultiEdit|NotebookEdit",
       "hooks": [{"type": "command", "command": "<python> <run>/control/write_hook.py"}]}
    ]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["<worktree>", "<user home>", "<run>/control", "<run>/config"],
      "allowRead": ["<each ro and rw path>", "<runtime paths>", "<run>/work", "<run>/home", "<TMPDIR>"],
      "allowWrite": ["<each rw path>", "<run>/work", "<run>/home", "<TMPDIR>"]
    },
    "network": {"allowedDomains": [], "strictAllowlist": true}
  }
}
```

### Deny rules

Claude Code applies `Read` deny rules to its file tools and also to the Bash sandbox: a path a rule
denies is absent for Bash too. The rules are therefore the one place that hides a path from a
worker, and they must never cover system directories, the runtime paths or the run's own
directories. They are generated from the grant and the file tree:

| Path | Rules |
| --- | --- |
| a task-worktree file with no level | `Read` and `Edit` |
| a `names` file | `Read` and `Edit` |
| a `ro` file | `Edit` |
| a `rw` file | none |
| a task-worktree directory with no `ro` or `rw` path below it | one `Read` and one `Edit` rule on `<dir>/**` instead of rules per file |
| a directory covered by a `ro` directory entry with no `rw` path below it | one `Edit` rule on `<dir>/**` |
| the task worktree's `.git` | `Read` and `Edit` on the path and below |
| inside the user's home, every entry that leads neither to the task worktree, to the run's `work/` or `home/`, nor to a runtime path | `Read` and `Edit` on the entry and below; a home that holds none of them is denied as a whole |
| `<run>/control/` and `<run>/config/` | `Read` and `Edit` on the path and below |

The home rule hides other projects, other task worktrees, the primary worktree's `.git` and other
runs, and `~/.claude`. Paths below a runtime path are left alone. Glob and Grep are governed by the
`Read` rules. A file created after the rules were generated has no rule of its own; it is still
covered by a directory rule or by the write hook.

### Write hook

The hook receives Claude Code's PreToolUse JSON on standard input and resolves `tool_input.file_path`
to an absolute path without following a final symbolic link.

| Target | Decision | Reason given to the worker |
| --- | --- | --- |
| in the `rw` list | none (the hook exits 0 without output) | — |
| a `ro` path | deny | the path is read-only for this task |
| a `names` path | deny | only the path's name is visible to this task |
| another path in the task worktree | deny | the file is undeclared; it must first be declared as a pending file of a Module through a `specify` task |
| outside the task worktree | deny | the path is outside the task worktree |
| unreadable input or any internal error | deny | the hook could not decide |

A denial is the PreToolUse output with `permissionDecision: "deny"` and the reason as
`permissionDecisionReason`.

## Tool sets

On the Claude Code backend:

| Task type | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test` | `Read,Glob,Grep` |
| `specify`, `code-to-spec` | `Read,Glob,Grep,Edit,Write` |
| `implement` | `Read,Glob,Grep,Edit,Write,Bash` |

A grant with no writable path, such as a survey's `code-to-spec` grant with the Spec side withheld,
gets the read-only set of the first row whatever its task type. WebFetch, WebSearch, the agent tool and notebook editing are never listed. A `test` worker runs no
command itself: the host runs the configured checks and gives it their results.

## Task-session settings

A Claude Code task session's settings, `.concorde/tasks/<task>.session/settings.json`, hold the
write hook and the Bash sandbox of its [session boundary](module.md#concept.harness.session-boundary):

- a PreToolUse hook on Edit, Write, MultiEdit and NotebookEdit, `session_hook.py` copied beside
  the settings with the task worktree and decision log embedded, which allows a path inside the
  task worktree or the decision log and denies any other with a reason naming the task worktree;
  any failure denies;
- the sandbox enabled, with sandboxed Bash commands approved without asking and unsandboxed
  commands disabled, `allowWrite` the task worktree, the
  repository's Git directory, the primary worktree's `.concorde/runs/` and `.concorde/tasks/`, and
  the user's package caches, and the network open to every host (`allowedDomains` is `*`);
- no deny rules: reads stay open.
