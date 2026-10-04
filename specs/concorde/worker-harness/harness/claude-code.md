# Claude Code harness mechanics

This document describes the exact files the Harness generates to apply a harness to a Claude Code
worker. It also describes the tool sets per [task type](../../glossary.json#concept.task-type). The
files provide these mechanisms:

- [worker settings](../../glossary.json#concept.worker-settings) with their
  [deny rules](../../glossary.json#concept.deny-rules)
- [write hook](../../glossary.json#concept.write-hook)
- Bash sandbox

The [entry](module.md) explains why a harness is applied this way. The [pi mechanics](pi.md) state
what the pi backend generates instead. [The run mechanics](../workers/launch.md) of Workers state
where these files are placed in a run.

## Worker settings

On the Claude Code backend, the
[runtime directory](../../glossary.json#concept.runtime-directory)'s `control/settings.json` has
this shape. Paths are absolute. `<runtime>` is the runtime directory:

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

The hook's command names the Python interpreter and the hook's path, each quoted for the shell.
This quoting keeps a path holding a space or a quote as one word.

### Deny rules

Claude Code applies `Read` deny rules to its file tools and also to the Bash sandbox. A path a rule
denies is absent for Bash too. Its sandbox's `denyWrite` wins inside a wider `allowWrite`. The
sandbox names in `denyWrite` a path the grant lists apart at `ro` or `names` below a `rw` directory
entry. That path is read-only for Bash as for the file tools.

The sandbox's `denyRead` also names each path the grant lists apart at `names` below a `ro` or `rw`
directory entry. The lists it shares with pi require this. This hides the path from Bash as its
`Read` rule already does. The rules are therefore the one place that hides a path from the file
tools. The rules must never cover these directories or paths:

- system directories
- the runtime paths
- the run's own directories

The rules are generated from the grant and the file tree:

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

Whether the primary worktree is inside the user's home or outside it, such as under `/tmp`, the
home and primary-worktree rule hides these entries:

- other projects
- other task worktrees
- the primary worktree's sources and `.git` and other runs
- `~/.claude`

Even where the repository's metadata lies outside both, the Git path rule hides it. This includes a
Git directory a `.git` file points to elsewhere. The rule also hides metadata inside a `ro` or `rw`
directory of the grant, which the walk does not enter. Paths below a runtime path are left alone.
Glob and Grep are governed by the `Read` rules.

A file created after the rules were generated has no rule of its own. Unless the file is `rw`, the
write hook still refuses to change it. When the file's directory has no `ro` or `rw` path below it,
a directory rule hides the file. Otherwise the file tools can read it. Since the worker writes only
`rw` paths, the worker cannot create such a file itself.

### Write hook

The hook is `write_hook.py` copied into the runtime directory's `control/`, generated from the
same grant as the deny rules. The hook embeds these values:

- the task worktree
- the grant's `rw` list
- the grant's `ro` list
- the grant's `names` list

The hook receives Claude Code's PreToolUse JSON on standard input. It resolves
`tool_input.file_path` to an absolute path with every symbolic link resolved, the final one
included. It also resolves a final link whose target does not exist yet. A write is judged by the
file it would change, never by a link's own name. A link at a `rw` path lets a write through only
when its target is `rw` too. When its target is `rw`, a link elsewhere lets a write through.

As everywhere the Harness reads a grant, a path's level is that of the grant's most specific entry
for it. This is its exact entry, else the longest directory entry above it. The rows are tried from
the top. The first row that matches decides. A denial reached through a final link names the file
judged followed by `(the target of the symbolic link <path>)`. Such a denial outside the task
worktree says the path is a symbolic link to that target.

The hook sees only the grant, not which Module declares an ungranted path. Its reason for an
ungranted path covers both an undeclared file and a file of a Module the task is not bound to.

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

The Claude Code backend uses these tool sets:

| Task type | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test`, `review-architecture` | `Read,Glob,Grep` |
| `specify`, `code-to-spec` | `Read,Glob,Grep,Edit,Write` |
| `implement` | `Read,Glob,Grep,Edit,Write,Bash` |

When its row in the Protocol's task-type table writes no set, every task type gets the read-only
set of the first row. This gives `review-architecture` the tools of `review-spec` on both backends.
The `review-architecture` task type reads every Module's [Specs](../../glossary.json#concept.spec)
and writes nothing.

Whatever its task type, a grant with no writable path gets that set too. An example is the read-only
grant of a run that may not change its worktree, with every `rw` entry lowered to `ro`. The tool
sets never list these tools:

- WebFetch
- WebSearch
- the agent tool
- notebook editing

A `test` worker runs no command itself. Its [Operation](../../glossary.json#concept.operation) runs
the [configured checks](../../glossary.json#concept.configured-check) and gives the worker their
results.
