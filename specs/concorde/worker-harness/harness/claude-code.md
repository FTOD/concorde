# Claude Code harness mechanics

The exact files the Harness generates to apply a harness to a Claude Code worker: the
[worker settings](../../glossary.json#concept.worker-settings) with their
[deny rules](../../glossary.json#concept.deny-rules), [write hook](../../glossary.json#concept.write-hook)
and Bash sandbox, and the tool sets per [task type](../../glossary.json#concept.task-type). The [entry](module.md) explains why a harness is applied
this way; the [pi mechanics](pi.md) state what the pi backend generates instead, and
[the run mechanics](../workers/launch.md) of Workers where these files are placed in a
run.

## Worker settings

On the Claude Code backend the [runtime directory](../../glossary.json#concept.runtime-directory)'s `control/settings.json` has this shape; paths are
absolute, `<runtime>` being the runtime directory:

```json
{
  "permissions": {
    "deny": ["Read(//<worktree>/secrets/**)", "Edit(//<worktree>/specs/shop/module.md)", "..."]
  },
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit|Write|MultiEdit|NotebookEdit",
       "hooks": [{"type": "command", "command": "<python> <runtime>/control/write_hook.py"}]}
    ]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["<worktree>", "<user home>", "<primary worktree>", "<each Git administrative path>", "<runtime>/control", "<runtime>/config"],
      "allowRead": ["<each ro and rw path>", "<runtime paths>", "<runtime>/work", "<runtime>/home", "<runtime>/tmp"],
      "allowWrite": ["<each rw path>", "<runtime>/work", "<runtime>/home", "<runtime>/tmp"]
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
| a `.git` entry of the task worktree met by the walk, at any depth | `Read` and `Edit` on the path and below |
| each Git administrative path Workers hands over: the common Git directory, the worktree's Git directory, every `.git` entry of the worktree and the Git directories they point to | `Read` and `Edit` on the path and below |
| inside the user's home and inside the primary worktree, every entry that leads neither to the task worktree, to the runtime directory's `work/` or `home/`, nor to a runtime path | `Read` and `Edit` on the entry and below; a home that holds none of them is denied as a whole |
| `<runtime>/control/` and `<runtime>/config/` | `Read` and `Edit` on the path and below |

The home and primary-worktree rule hides other projects, other task worktrees, the primary
worktree's sources and `.git` and other runs, and `~/.claude`, with the primary worktree inside the
user's home or outside it, such as under `/tmp`. The Git path rule hides the repository's metadata
even where it lies outside both, such as a Git directory a `.git` file points to elsewhere, and
inside a `ro` or `rw` directory of the grant, which the walk does not enter. Paths below a runtime path are left alone. Glob and Grep are governed by the
`Read` rules. A file created after the rules were generated has no rule of its own: the write hook
still refuses to change it unless it is `rw`, and a directory rule hides it when its directory has
no `ro` or `rw` path below it, but otherwise the file tools can read it. The worker cannot create
such a file itself, since it writes only `rw` paths.

### Write hook

The hook is `write_hook.py` copied into the runtime directory's `control/` with the task worktree and the grant's
`rw`, `ro` and `names` lists embedded, generated from the same grant as the deny rules. It receives
Claude Code's PreToolUse JSON on standard input and resolves `tool_input.file_path` to an absolute
path without following a final symbolic link. The rows are tried from the top and the first that
matches decides. The hook sees only the grant, not which Module declares an ungranted path, so its
reason for one covers both cases: an undeclared file and a file of a Module the task is not bound
to.

| Target | Decision | Reason given to the worker |
| --- | --- | --- |
| outside the task worktree | deny | the path is outside the task worktree |
| a `.git` entry of the task worktree at any depth, or below one | deny | Git metadata is not available to workers |
| in the `rw` list | none (the hook exits 0 without output) | — |
| a `ro` path | deny | the path is read-only for this task |
| a `names` path | deny | only the path's name is visible to this task |
| another path in the task worktree | deny | the path is not in this task's grant; a new file outside the bound directories is created and bound to a [Module](../../glossary.json#concept.module) by the task level before a worker fills it, and a file another Module binds needs that Module bound to the task |
| unreadable input or any internal error | deny | the hook could not decide |

A denial is the PreToolUse output with `permissionDecision: "deny"` and the reason as
`permissionDecisionReason`.

## Tool sets

On the Claude Code backend:

| Task type | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test`, `review-architecture` | `Read,Glob,Grep` |
| `specify`, `code-to-spec` | `Read,Glob,Grep,Edit,Write` |
| `implement` | `Read,Glob,Grep,Edit,Write,Bash` |

Every task type whose row in the Protocol's task-type table writes no set gets the read-only set of
the first row, which is how `review-architecture`, reading every Module's Specs and writing nothing,
gets the tools of `review-spec` on both backends. A grant with no writable path, such as a survey's
`code-to-spec` grant with the [Spec](../../glossary.json#concept.spec) side withheld, gets that set too
whatever its task type. WebFetch, WebSearch, the agent tool and notebook editing are never listed. A
`test` worker runs no command itself: its [Operation](../../glossary.json#concept.operation) runs the
[configured checks](../../glossary.json#concept.configured-check) and gives it their results.
