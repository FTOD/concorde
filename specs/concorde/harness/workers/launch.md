# Run mechanics

The exact files, command lines, environment, audit, rounds and records of one worker run, and the
requirements they serve. The [entry](module.md) explains why the run is shaped this way; the
worker's answer is fixed by [the worker result contract](contracts.md).

## Inputs

A run is requested with:

| Input | Meaning |
| --- | --- |
| task worktree | Absolute path of the Git worktree the worker works in |
| task type | One of the six Protocol task types; it selects the tool set |
| grant | The frozen grant: every path with its level `rw`, `ro` or `names`, relative to the task worktree, and its context identity |
| instructions | The Operation's task-specific part of the brief |
| checks | The configured checks to run after each round, possibly none |
| runtime paths | Extra absolute paths Bash may read, such as the toolchain, `.venv` or `node_modules` |
| limits | Timeout per round, `--max-turns`, `--max-budget-usd`, and the number of resume rounds (default 3) |
| model | Optionally the model passed with `--model` |

## Run directory layout

The run directory is `.concorde/runs/<run-id>/` in the primary worktree, located through the task
worktree's Git common directory. `<run-id>` is unique and chosen by the host.

| Path | Content | Worker access |
| --- | --- | --- |
| `record.json` | The run record | none |
| `control/settings.json` | The worker settings | none |
| `control/write_hook.py` | The write hook with the `rw` list embedded | none |
| `control/grant.json` | The frozen grant and its context identity | none |
| `control/brief.md` | The brief as sent | none |
| `control/result.schema.json` | The worker result schema | none |
| `config/` | `CLAUDE_CONFIG_DIR`: the credential copy, sessions and transcripts | none |
| `home/` | `HOME` | Bash read and write |
| `tmp/` | `TMPDIR` | Bash read and write |
| `work/` | The working directory | Bash read and write |
| `checks/<round>/<check-id>.log` | Check logs of each round | none |

The host refuses to launch when any deny rule it generated covers `work/`, `home/` or `tmp/`.

## Worker settings

`control/settings.json` has this shape; paths are absolute:

```json
{
  "permissions": {
    "deny": ["Read(//<worktree>/secrets/**)", "Edit(//<worktree>/specs/shop/module.md)", "..."]
  },
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit|Write",
       "hooks": [{"type": "command", "command": "<python> <run>/control/write_hook.py"}]}
    ]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["<worktree>", "<user home>", "<run>/control", "<run>/config"],
      "allowRead": ["<each ro and rw file>", "<runtime paths>"],
      "allowWrite": ["<each rw file>", "<run>/work", "<run>/home", "<run>/tmp"]
    },
    "network": {"allowedDomains": []}
  }
}
```

### Deny rules

Deny rules are generated from the grant and the task worktree's file tree:

| Path | Rules |
| --- | --- |
| a task-worktree file with no level | `Read` and `Edit` |
| a `names` file | `Read` and `Edit` |
| a `ro` file | `Edit` |
| a `rw` file | none |
| a directory with no `ro` or `rw` file below it | one `Read` and one `Edit` rule on `<dir>/**` instead of rules per file |
| `.git` of the task worktree, and the primary worktree's `.git/` | `Read` and `Edit` on the path and below |
| the primary worktree outside the run directory, computed the same way with the run directory as the only kept subtree | `Read` and `Edit` |
| `~/.claude/` | `Read` and `Edit` on `~/.claude/**` |
| `<run>/control/` and `<run>/config/` | `Read` and `Edit` on the path and below |

Glob and Grep are governed by the `Read` rules. A file created after the rules were generated has no
rule of its own; it is still covered by a directory rule or by the write hook.

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

| Task type | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test` | `Read,Glob,Grep` |
| `specify` | `Read,Glob,Grep,Edit,Write` |
| `implement` | `Read,Glob,Grep,Edit,Write,Bash` |

WebFetch, WebSearch, the agent tool and notebook editing are never listed. A `test` worker runs no
command itself: the host runs the configured checks and gives it their results.

## Launch

The first round runs, with `work/` as working directory and the brief on standard input:

```text
claude -p --settings <run>/control/settings.json --tools <tool set>
       --json-schema <worker result schema> --output-format json
       --permission-mode bypassPermissions --allow-dangerously-skip-permissions
       --strict-mcp-config --max-turns <n> --max-budget-usd <x> [--model <model>]
```

A resume round runs the same command with `--resume <latest session id>` and the check failures as
the prompt.

The environment is cleared and then set to exactly:

| Variable | Value |
| --- | --- |
| `PATH`, `LANG` | the host's values |
| `HOME` | `<run>/home` |
| `TMPDIR` | `<run>/tmp` |
| `CLAUDE_CONFIG_DIR` | `<run>/config` |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS` | `1` |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `1` |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `1` |

Before the first round the host copies the user's Claude Code credentials file into `config/`.

The process starts in a new process group. When the round ends for any reason, including a timeout,
the host kills the whole group. From standard output the host reads the JSON envelope's session
identifier, exit status and schema-validated structured output; standard error is kept in the run
record as a bounded tail.

## Audit

Before the first round the host records a snapshot of the task worktree: `HEAD`, and the digest of
every tracked change and untracked file that already exists. After each round it runs read-only Git
(`git status --porcelain=v2 -z --untracked-files=all` and the digests of the listed files) and
compares.

| Observation since the snapshot | Verdict |
| --- | --- |
| a changed or new file in the `rw` list | allowed |
| a changed or new file outside the `rw` list | violation |
| a deleted file | violation |
| a changed `HEAD`, index or branch | violation |
| a change under a path Git ignores | not observed |

After the last round, the host removes each pre-created pending file that is still empty and was not
otherwise changed, and deletes each path in `proposed_deletions` that is in the `rw` list, but only
when the audit was clean. A proposed deletion outside `rw` is refused and recorded.

## Rounds

| Worker result and audit | Checks | Next |
| --- | --- | --- |
| audit violation | not run | end `failed` with `audit_violation` |
| `blocked` or `failed`, audit clean | not run | end with the worker's status |
| `ok`, audit clean, no checks given | — | end `ok` |
| `ok`, audit clean, all checks pass | run | end `ok` |
| `ok`, audit clean, a check fails, rounds left | run | resume round |
| `ok`, audit clean, a check fails, no rounds left | run | end `failed` with `checks_failed` |

The resume prompt lists each failing check's identity, status, exit code and the last 20,000 bytes of
its log.

## Run record

`record.json` holds:

| Field | Content |
| --- | --- |
| `run_id`, `task_type`, `worktree` | the run's identity, task type and task worktree |
| `context_identity`, `grant_digest` | the grant's context identity and the digest of `control/grant.json` |
| `settings_digest`, `brief_digest`, `tools` | what the worker was given |
| `started_at`, `ended_at` | UTC times |
| `rounds` | per round: session identifier, prompt kind (`initial` or `check_failures`), exit status, duration, audit verdict with violating paths, and check results with log paths |
| `transcript` | the path of the latest session's transcript under `config/` |
| `stderr_tail` | the last 20,000 bytes of the worker's standard error |
| `worker_result` | the last worker result, verbatim, or null |
| `pending_removed`, `deleted`, `deletions_refused` | paths the host removed or refused to remove |
| `status` | the host's final status: `ok`, `blocked` or `failed` |
| `errors` | host error codes with details |

Host error codes:

| Code | Meaning |
| --- | --- |
| `grant_unavailable` | the grant or its context identity is missing or unreadable |
| `run_directory_denied` | a generated deny rule would cover the worker's own directories |
| `launch_failed` | `claude` could not be started or exited without a JSON envelope |
| `worker_timeout` | a round exceeded its timeout; the process group was killed |
| `worker_result_invalid` | the envelope has no structured output that satisfies the schema |
| `audit_violation` | the audit found a write outside `rw` |
| `checks_unavailable` | the configured checks could not run |
| `checks_failed` | a check still failed after the last round |

## Requirements

### req.workers.frozen-grant — One grant for the whole run

The host SHALL generate a run's settings, write hook, tool set and brief from one frozen grant and keep them unchanged for every round of the run.

### req.workers.write-allowlist — Only `rw` paths are writable by file tools

The write hook SHALL deny every Edit or Write whose target is not in the grant's `rw` list.

### req.workers.read-denials — File tools cannot read what the grant withholds

The deny rules SHALL forbid Read, Glob and Grep every task-worktree path whose level is neither `ro` nor `rw`.

### req.workers.bash-sandbox — Bash runs sandboxed without network

Every Bash command of a worker SHALL run in Claude Code's sandbox with no allowed network domain and with unsandboxed commands disabled.

### req.workers.working-directory — The worker never works in the worktree

A worker's working directory SHALL be its run's `work/` directory, outside the task worktree and outside every path a deny rule names.

### req.workers.clean-environment — Nothing ambient reaches the worker

The host SHALL start every worker round with only the environment variables listed in [Launch](#launch).

### req.workers.no-git — Workers never see Git

A worker SHALL have no access to Git metadata through any tool.

### req.workers.audit-every-round — Every round is audited

The host SHALL audit the task worktree against the grant after every round and before any configured check of that round runs.

### req.workers.violation-ends-run — A violation is never retried

A run whose audit finds a violation SHALL end `failed` without another round.

### req.workers.rounds-for-checks-only — Rounds only repair failing checks

The host SHALL resume a worker only when it ended `ok`, its audit was clean and a configured check failed, and at most the configured number of times.

### req.workers.latest-session — Resume from the newest session

Each resume round SHALL continue the session identifier returned by the previous round.

### req.workers.claims-apart — Worker claims stay claims

The run record SHALL keep the worker result verbatim and separate from the evidence the host observed itself.

### req.workers.host-deletes — Only the host deletes

The host SHALL delete a file only when the worker proposed it, the file is in the `rw` list and the audit was clean.

### req.workers.process-group — No worker process outlives its round

The host SHALL kill the worker's whole process group when a round ends.

### req.workers.always-recorded — Every run leaves a record

The host SHALL write a run record for every run it was asked to start, including one refused before launch.
