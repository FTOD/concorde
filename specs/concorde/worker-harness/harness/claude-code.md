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
      "denyRead": ["<worktree>", "<user home>", "<primary worktree>", "<each Git administrative path>", "<runtime>/control", "<runtime>/config", "<each names path listed apart below a ro or rw directory entry>"],
      "allowRead": ["<each ro and rw path>", "<runtime paths>", "<runtime>/work", "<runtime>/home", "<runtime>/tmp"],
      "allowWrite": ["<each rw path>", "<runtime>/work", "<runtime>/home", "<runtime>/tmp"],
      "denyWrite": ["<each ro or names path listed apart below a rw directory entry>"]
    },
    "network": {"allowedDomains": [], "strictAllowlist": true}
  }
}
```

The hook's command names the Python interpreter and the hook's path, each quoted for the shell, so
that a path holding a space or a quote stays one word.

### Deny rules

Claude Code applies `Read` deny rules to its file tools and also to the Bash sandbox: a path a rule
denies is absent for Bash too. Its sandbox's `denyWrite` wins inside a wider `allowWrite`, so a
path the grant lists apart at `ro` or `names` below a `rw` directory entry, which the sandbox
names in `denyWrite`, is read-only for Bash as for the file tools. The sandbox's `denyRead` also
names each path the grant lists apart at `names` below a `ro` or `rw` directory entry, as the lists
it shares with pi must, which hides it from Bash as its `Read` rule already does. The rules are
therefore the one place that hides a path from the file tools, and they must never cover system
directories, the runtime paths or the run's own directories. They are generated from the grant
and the file tree:

| Path | Rules |
| --- | --- |
| a task-worktree file with no level | `Read` and `Edit` |
| a `names` file | `Read` and `Edit` |
| a `ro` file | `Edit` |
| a `rw` file | none |
| a directory covered by a `rw` directory entry with no entry below it of another level | none |
| a task-worktree directory with no `ro` or `rw` path below it | one `Read` and one `Edit` rule on `<dir>/**` instead of rules per file |
| a directory covered by a `ro` directory entry with no entry below it of another level | one `Edit` rule on `<dir>/**` |
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
path with every symbolic link resolved, the final one included, and also a final link whose target
does not exist yet: a write is judged by the file it would change, never by a link's own name, so a
link at a `rw` path lets a write through only when its target is `rw` too, and a link elsewhere lets
one through when its target is `rw`. A path's level is that of the grant's most specific entry for it: its exact entry,
else the longest directory entry above it, as everywhere the Harness reads a grant. The rows are
tried from the top and the first that matches decides; a denial reached through a final link names the file judged followed by
`(the target of the symbolic link <path>)`, and one outside the task worktree says the path is a
symbolic link to that target. The hook sees only the grant, not which Module declares an ungranted path, so its
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
the first row, which is how `review-architecture`, reading every Module's [Specs](../../glossary.json#concept.spec) and writing nothing,
gets the tools of `review-spec` on both backends. A grant with no writable path, such as the
read-only grant of a run that may not change its worktree, every `rw` entry lowered to `ro`, gets
that set too whatever its task type. WebFetch, WebSearch, the agent tool and notebook editing are never listed. A
`test` worker runs no command itself: its [Operation](../../glossary.json#concept.operation) runs the
[configured checks](../../glossary.json#concept.configured-check) and gives it their results.
