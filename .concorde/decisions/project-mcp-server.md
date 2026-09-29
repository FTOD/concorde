# Decision log: project-mcp-server

Goal: Add one project-level stdio MCP server for the main-session side through which Claude Code sessions manage tasks and traces: task and trace queries, short task writes, non-blocking lock acquisition that answers who holds a busy lock and hands a granted lock to the detached process doing the work, and a register_wait that wakes the asking session through Claude Code channels when a task, run or lock frees, with background Bash as the documented fallback

## Brief (main agent, 2026-09-29)

The developer designed this with the main agent on 2026-09-29. Their decisions, which this task
carries out:

1. **One stdio MCP server per project, on the main-session (Coordination) side.** Not per
   worktree: a server started from any worktree of the project finds the primary worktree through
   Git's common directory (`store.primary_of` / `tracing.layout.primary_worktree` already do this)
   and serves the project's tasks, traces and locks from there. It is a simple stdio server, a
   child process of the Claude Code session that lives as long as the session; no daemon. It is
   a thin presentation: the CLI stays the source of truth and the server adds no rule of its own,
   reading the stores fresh on every call.
2. **The existing Spec MCP server (`concorde spec-mcp`, module.spec-mcp) stays separate and
   unchanged**, per worktree and read-only. Reuse or share its hand-written JSON-RPC session code
   where sensible, but do not merge the two servers.
3. **Tools.** Queries: task list/show, trace show (filterable by node or depth so a large trace
   need not be read whole), a run's result, a workflow report. Short writes with structured input:
   task open, task escalate (the error chain as typed arguments), task close. Long work (merge,
   and anything else that waits or runs checks) is started as a detached process and returns at
   once. Exact tool set and names are the session's to design within this.
4. **Locks go through the server without blocking.** Asking for a lock (for example the merge
   lock to merge a task) is answered at once: granted, or denied with who holds it (which session,
   which task, since when). A granted lock belongs to the session's own work, never to the server:
   the tool that grants it starts the detached process doing the work (e.g. the merge) and hands
   the `flock` to that process (the lock follows the open file description), so it is released
   when that work ends, however it ends. The holder line of the lock file must name the owning
   session and task so the denial can say who uses it (`tracing/locks.py` writes `holder`, `pid`,
   `since` today).
5. **Using the server is recommended, not enforced.** The physical `flock` stays the only lock;
   CLI commands and task sessions may still take locks directly, and both paths see the same lock.
6. **`register_wait` only notifies.** A session registers that it waits for a task (a state such
   as delivered), a run (its end, i.e. its run lock released) or a lock (released); the server
   watches event-driven (blocking on the lock in a thread, or inotify on the record) — never by
   polling in the agent — and wakes that session when it happens. It never hands a lock to the
   woken session; the session asks again and may be denied again.
7. **Waking uses Claude Code channels** (research preview): the server declares the
   `experimental` capability `claude/channel` and sends `notifications/claude/channel` with
   `{content, meta}`. A self-built server must be enabled when the session starts, with
   `--channels server:<name>` and `--dangerously-load-development-channels`; check the current
   Claude Code docs (channels, channels-reference) for the exact flags. Channels need Anthropic
   authentication and may be disabled by organization policy. **Fallback:** when the session was
   not started with channels, `register_wait` says so explicitly and returns the equivalent
   blocking command (e.g. `task merge ... --wait`, `task show`-based waits must not be polling) for
   the agent to run in background Bash. Keep the CLI `--wait` options for that fallback.
8. **Claude Code only.** The main-session side no longer supports pi (tasks drop-pi-main-session
   and drop-pi-workflows, merged). No pi projection of these tools.
9. **Task sessions may use the server too**; the developer does not consider it a problem that a
   task session can reach management tools through it, so no role split and no extra enforcement.
   `concorde task session` should give the task session the server (pass `--mcp-config` / the
   channels flags explicitly, since project-scoped `.mcp.json` servers are not loaded in untrusted
   folders for background sessions). The `concorde` skill keeps saying that task sessions do not
   merge.
10. **Workers have nothing to do with it**: they keep launching with an empty MCP configuration.
11. The server must preserve the error-chain principle: every refusal is a structured error chain
    link, as the CLI's are.
12. No backward compatibility or migration shims.

Also expected: Specs first (Main session owns the server; Tasks, Tracing, Execution, Task session,
Distribution, Harness and the glossary as needed, with scenarios and contracts), then code, tests
over a real stdio connection, the installer/`.mcp.json` registration for projects and for this
checkout, and the `concorde` skill and docs telling the main agent how to start its session with
channels and when to use the server versus the CLI.

Left to the session: tool names and schemas, module placement of the code, how the detached
process receives the lock, the watch mechanism, glossary wording. Escalate decisions that change
the above, anything that needs a new runtime dependency, and anything outside the task's Modules.

## Task session: design decisions (2026-09-29)

Taken by the task session within what the brief left to it.

1. **Name and command.** The server is the *project MCP server*, started as
   `concorde project-mcp`, registered under the MCP name `concorde` (tools reach Claude as
   `mcp__concorde__<tool>`). Its code lives in `src/concorde/project_mcp/`, owned by
   module.main-session. It has its own small JSON-RPC transport instead of subclassing
   `spec_mcp.server.Session`: that class hard-wires its tools, root resolution and an unlocked
   `send`, and the project server must send notifications from watcher threads, so reuse would be
   an override of nearly everything and would couple Main session to module.spec-mcp internals
   (which is outside this task's Modules).
2. **Tools.** Queries `task_list`, `task_show`, `trace_show` (node + depth), `run_result`,
   `workflow_report`, `locks` (who holds the merge lock and each current task's workspace lock).
   Short writes `task_open`, `task_escalate`, `task_close` (completed/failed; `--merged` stays the
   merge's own step), which take their locks without waiting (wait 0) and are refused with
   `merge_busy`/`workspace_busy` naming the holder. Long work: `task_merge` (merge, resume or
   abort). Waiting: `register_wait`.
3. **Lock handover.** `task_merge` takes the task's workspace lock and then the merge lock with
   `LOCK_EX|LOCK_NB` in the server; a busy lock is refused at once with its holder. Granted, it
   starts `concorde task merge <task> ... --wait 0` as a process of its own session
   (`start_new_session`), passing both descriptors (`pass_fds`) and naming them in the environment
   variable `CONCORDE_INHERITED_LOCKS` (`{lock path: fd}`). Tracing's `locks.hold` adopts an
   inherited descriptor when it refers to the same file and holds the lock (a `flock` on the same
   open file description succeeds), marks it non-inheritable so the merge's checks do not keep it
   alive, and removes the variable from its environment. The server closes its own copies right
   after the start, so the lock belongs to the merge process only and the kernel releases it when
   that process ends.
4. **Holder line.** Every holder line gains optional `session` (the Claude Code session id from
   `CLAUDE_CODE_SESSION_ID`, whoever takes the lock: CLI, run or server-started work) and `task`
   (set by Tasks). Execution still never records a task: its runs' lines name the workspace in
   `holder` only.
5. **Watch mechanism, no polling.** A lock or run wait blocks on the lock itself in a thread
   (`flock(LOCK_SH)`, released at once), so a holder that dies wakes it too. A task-state wait uses
   inotify (through ctypes, standard library, no new dependency; Linux only like the rest of
   Concorde's locking) on `locks/workspaces/` to learn each new acquisition of the task's workspace
   lock, then blocks on that lock until it is released and re-reads the task's state: every change
   to `delivered`, `merging`, `closed` or `failed` is made while that lock is held (delivery run,
   merge, close), so `until` admits only those four states.
6. **CLI fallback.** New `concorde task wait (<task> --until <state>[,…] | --run <run-id> | --lock
   merge | --lock workspace --task <task>) [--timeout <s>]` runs the same waits in one blocking
   command, printing one JSON value when it happens. `register_wait` without a channel returns
   exactly this command for background Bash.
7. **Channel detection.** Claude Code does not tell a server whether it was loaded as a channel
   (verified: the `initialize` request carries no such capability, and undelivered notifications are
   dropped silently). The server takes `CONCORDE_CHANNEL=1|0` from its environment when set, else
   looks for `server:concorde` after `--dangerously-load-development-channels` or `--channels` in
   the command lines of its ancestor processes (verified live: an interactive `claude` started with
   `--dangerously-load-development-channels server:probe` is the server's parent and was woken
   from idle by `notifications/claude/channel`). An organization policy that disables channels is
   invisible to it; the guidance says so.
8. **Detached work's output.** The merge's JSON output and standard error go to a private
   temporary directory of the server process (ephemeral runtime files belong in `/tmp`); the
   durable account stays the merge attempt's trace node and the task record. With a channel the
   server wakes the session when the merge process ends, with its output; without one the tool
   returns the output path and the `task wait --lock workspace --task <task>` fallback.
9. **Task sessions.** `concorde task session` writes `runtime/mcp.json` for the task session
   (the server with `CONCORDE_CHANNEL=1`) and passes `--mcp-config` and
   `--dangerously-load-development-channels server:concorde` to `claude --bg`.

## Task session: further decisions and results (2026-09-29)

10. **Spec placement.** The server's contract is a new `contracts.md` of module.main-session with
    the provided contract `contract.main-session.channel-event` (version 1, peer external); the
    glossary gains `concept.project-mcp-server` (owner module.main-session). Tasks documents
    `concorde task wait` and its codes `wait_timeout`, `wait_unreachable`, `wait_failed`; Tracing
    documents the holder line's `session`/`task`, handing a lock on and waiting for a release;
    Task sessions, Distribution, Harness, Coordination and the root are amended. The Harness
    records the developer's choice that the session boundary does not confine the server.
11. **Execution** gains only a pass-through `task` argument on `workspace_lock` for the holder
    line; its own runs never give one, so Execution still knows no task.
12. **Kernel detail found while testing.** After a handover `/proc/locks` keeps naming the
    process that first took the `flock` (the server), not the merge process; the holder line is
    therefore the authority on who holds a handed lock, and the Tracing contract says so. The
    tests check the handover by which process has the lock file open and by killing the server.
13. **Verified live (probe, not the final server):** an interactive `claude` started with
    `--dangerously-load-development-channels server:<name>` (after its one confirmation) is
    woken from idle by `notifications/claude/channel`; in `claude -p` (even stream-json) no
    channel is registered. **Not verifiable from this sandbox:** `claude --bg` with that flag,
    since the sandbox cannot write `~/.claude/jobs`; whether a background session blocks on the
    flag's confirmation prompt is unknown (escalated as a verification request).
14. **Result not ok, handled:** the full suite failed once on
    `tests/concorde/views/test_repository_checks.py::test_real_registry_listing_roots_are_copied`
    after binding this checkout's `.mcp.json` under the root's project files: module.views'
    `docsite/tests/repository/run-checks.py` must copy every bound root file and does not list
    `.mcp.json`. That script is outside this task's Modules, so the checkout's `.mcp.json` was
    left out of commit 28d93c55 and escalated. The Write tool had already created the file in
    the task worktree; the Bash sandbox masks it and cannot delete it, so it stays untracked
    there until the escalation is answered.

15. **Result not ok:** `task-validation` run r-20260929T150605-task_validation-b3b668be ended
    `blocked` (`not_deliverable`) with one blocking finding, the untracked `.mcp.json` of the
    task worktree (unbound), which is item 14; every configured check passed. Delivery waits for
    the answer to the `.mcp.json` escalation. The same run was the first live use of
    `concorde task wait --lock workspace`: it returned when the run released the lock, naming the
    run, its process and this session.

## Escalated to the main agent, 2026-09-29T15:11:51Z

- **task-session** task session (task project-mcp-server): `checkout_mcp_config_outside_modules`
  The brief asks for the project MCP server's .mcp.json registration for this checkout too. Tracking /.mcp.json ({"mcpServers": {"concorde": {"command": "python3", "args": ["scripts/concorde.py", "project-mcp"]}}}, bound under module.concorde's project files) makes tests/concorde/views/test_repository_checks.py::test_real_registry_listing_roots_are_copied fail: module.views' docsite/tests/repository/run-checks.py must copy every bound root file and its FILES tuple lacks '.mcp.json'. That script is outside this task's Modules. Commit 28d93c55 therefore leaves .mcp.json out, but the file exists untracked in the task worktree (created with the Write tool; the Bash sandbox masks it and cannot delete it), so task-validation is blocked on it; everything else passed.
  Not handled here (scope): the one-line fix belongs to module.views, which is not among this task's Modules
  Options: Allow this task to add '.mcp.json' to FILES in docsite/tests/repository/run-checks.py (module.views) and track the checkout's .mcp.json bound under module.concorde's project files; Do not track .mcp.json in this checkout: the main agent deletes the untracked /home/zhenyu/concorde/.claude/worktrees/project-mcp-server/.mcp.json, and developers register the server locally (claude mcp add concorde -- python3 scripts/concorde.py project-mcp)
  Recommendation: Allow the one-line module.views change and track .mcp.json, as the brief asks for the checkout's registration
  Caused by:
  - **command** Command task-validation r-20260929T150605-task_validation-b3b668be (workspace project-mcp-server): `not_deliverable`
    workspace project-mcp-server is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/project-mcp-server/workspace/runs/r-20260929T150605-task_validation-b3b668be/readiness.json)
    Not handled here (decision): task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses
    Evidence (blocking): .mcp.json no Module binds this changed path and it is neither a Spec document member nor a control record
    Options: repair each blocking finding in the workspace and run task-validation again; run specify for a Spec finding, implement for a code or check finding
    Recommendation: repair the first blocking finding: unbound .mcp.json: no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .mcp.json: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .mcp.json no Module binds this changed path and it is neither a Spec document member nor a control record

```json
{
  "level": "task-session",
  "actor": "task session (task project-mcp-server)",
  "code": "checkout_mcp_config_outside_modules",
  "detail": "The brief asks for the project MCP server's .mcp.json registration for this checkout too. Tracking /.mcp.json ({\"mcpServers\": {\"concorde\": {\"command\": \"python3\", \"args\": [\"scripts/concorde.py\", \"project-mcp\"]}}}, bound under module.concorde's project files) makes tests/concorde/views/test_repository_checks.py::test_real_registry_listing_roots_are_copied fail: module.views' docsite/tests/repository/run-checks.py must copy every bound root file and its FILES tuple lacks '.mcp.json'. That script is outside this task's Modules. Commit 28d93c55 therefore leaves .mcp.json out, but the file exists untracked in the task worktree (created with the Write tool; the Bash sandbox masks it and cannot delete it), so task-validation is blocked on it; everything else passed.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "the one-line fix belongs to module.views, which is not among this task's Modules"
  },
  "options": [
    "Allow this task to add '.mcp.json' to FILES in docsite/tests/repository/run-checks.py (module.views) and track the checkout's .mcp.json bound under module.concorde's project files",
    "Do not track .mcp.json in this checkout: the main agent deletes the untracked /home/zhenyu/concorde/.claude/worktrees/project-mcp-server/.mcp.json, and developers register the server locally (claude mcp add concorde -- python3 scripts/concorde.py project-mcp)"
  ],
  "recommendation": "Allow the one-line module.views change and track .mcp.json, as the brief asks for the checkout's registration",
  "causes": [
    {
      "level": "command",
      "actor": "Command task-validation r-20260929T150605-task_validation-b3b668be (workspace project-mcp-server)",
      "code": "not_deliverable",
      "detail": "workspace project-mcp-server is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/project-mcp-server/workspace/runs/r-20260929T150605-task_validation-b3b668be/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": ".mcp.json",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses"
      },
      "options": [
        "repair each blocking finding in the workspace and run task-validation again",
        "run specify for a Spec finding, implement for a code or check finding"
      ],
      "recommendation": "repair the first blocking finding: unbound .mcp.json: no Module binds this changed path and it is neither a Spec document member nor a control record",
      "causes": [
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".mcp.json: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".mcp.json",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  ]
}
```

## Escalated to the main agent, 2026-09-29T15:12:02Z

- **task-session** task session (task project-mcp-server): `bg_channel_unverified`
  concorde task session now starts every task session as: claude --bg ... --mcp-config .concorde/tasks/<task>/runtime/mcp.json --dangerously-load-development-channels server:concorde ... (the brief's item 9). Claude Code documents that this flag 'prompts for confirmation'. Verified live from this sandbox: an interactive claude with that flag (after pressing Enter once) is woken from idle by notifications/claude/channel; claude -p registers no channel. NOT verified: claude --bg with the flag, because this sandbox cannot write ~/.claude/jobs (EROFS). If a background session waits on that confirmation, every task session started after the merge would stall. Suggested check from the primary worktree before merging (it costs one short session): in this task's worktree run 'python3 scripts/concorde.py task session project-mcp-server --main <you> --dry-run' to see the exact command, or start 'claude --bg --name probe-channel --mcp-config /home/zhenyu/concorde/.concorde/tasks/project-mcp-server/runtime/mcp.json --dangerously-load-development-channels server:concorde --permission-mode auto "Call register_wait with lock merge, then say ready"' in a trusted folder and see that it starts, then check claude logs probe-channel; claude rm probe-channel afterwards.
  Not handled here (permission): starting a background Claude Code session needs a write to ~/.claude/jobs, which this task session's sandbox refuses
  Options: The main agent runs the check; if the background session starts, merge as is; If it stalls on the confirmation, answer so and I drop the channel flag from task sessions (they keep the server through --mcp-config and fall back to concorde task wait in background Bash)
  Recommendation: Run the check before merging

```json
{
  "level": "task-session",
  "actor": "task session (task project-mcp-server)",
  "code": "bg_channel_unverified",
  "detail": "concorde task session now starts every task session as: claude --bg ... --mcp-config .concorde/tasks/<task>/runtime/mcp.json --dangerously-load-development-channels server:concorde ... (the brief's item 9). Claude Code documents that this flag 'prompts for confirmation'. Verified live from this sandbox: an interactive claude with that flag (after pressing Enter once) is woken from idle by notifications/claude/channel; claude -p registers no channel. NOT verified: claude --bg with the flag, because this sandbox cannot write ~/.claude/jobs (EROFS). If a background session waits on that confirmation, every task session started after the merge would stall. Suggested check from the primary worktree before merging (it costs one short session): in this task's worktree run 'python3 scripts/concorde.py task session project-mcp-server --main <you> --dry-run' to see the exact command, or start 'claude --bg --name probe-channel --mcp-config /home/zhenyu/concorde/.concorde/tasks/project-mcp-server/runtime/mcp.json --dangerously-load-development-channels server:concorde --permission-mode auto \"Call register_wait with lock merge, then say ready\"' in a trusted folder and see that it starts, then check claude logs probe-channel; claude rm probe-channel afterwards.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "permission",
    "explanation": "starting a background Claude Code session needs a write to ~/.claude/jobs, which this task session's sandbox refuses"
  },
  "options": [
    "The main agent runs the check; if the background session starts, merge as is",
    "If it stalls on the confirmation, answer so and I drop the channel flag from task sessions (they keep the server through --mcp-config and fall back to concorde task wait in background Bash)"
  ],
  "recommendation": "Run the check before merging",
  "causes": []
}
```

## Main agent's answers (2026-09-29)

- Escalation 1 (checkout_mcp_config_outside_modules): option A, decided by the main agent
  (ordinary scope; it follows from the developer's decision to register the server for projects
  and for this checkout). The task session may add `.mcp.json` to `FILES` in
  `docsite/tests/repository/run-checks.py` (module.views) and track the checkout's `.mcp.json`
  under module.concorde's project files. This entry is the authorization for touching
  module.views.
- Escalation 2 (bg_channel_unverified): the probe needs a `claude --bg` session started with
  `--dangerously-load-development-channels` outside the task session's sandbox; the task session's
  sandbox refused it. The main agent puts running the probe to the developer instead of running it
  on the task session's request. The task session waits for the answer before delivery.

## Task session: after the main agent's answers (2026-09-29)

16. Escalation 1 answered with option A: `.mcp.json` added to `FILES` of
    `docsite/tests/repository/run-checks.py` (module.views, as authorized above) and the
    checkout's `.mcp.json` tracked under module.concorde's project files; spec-validation clean,
    views and development tests pass. Delivery waits for the answer to escalation 2, as asked.

## Probe result for escalation 2 (main agent, 2026-09-29, run with the developer's approval)

- `claude --bg --name probe-channel --mcp-config <probe config with CONCORDE_CHANNEL=1>
  --dangerously-load-development-channels server:concorde --permission-mode auto` (Claude Code
  v2.1.284, from the primary worktree) started at once: no confirmation stall; the `concorde`
  server loaded and `register_wait` answered (first call: merge lock free, nothing registered).
- With the merge lock held by `flock -n .concorde/locks/merge.lock sleep 45`, the session called
  `register_wait` again: wait 1 registered, the tool said it would arrive through the channel. The
  lock was released at about 23:58; by 23:59 the idle session had not been woken and showed no
  channel event. So a channel event does not wake a `claude --bg` session (the development channel
  appears not to be active there), while the server believed it was because of CONCORDE_CHANNEL=1.
- Decision (main agent, the fallback the developer's design names): task sessions do not get the
  channel flag or CONCORDE_CHANNEL=1; they keep the server and wait with `concorde task wait` in
  background Bash. Probe session stopped and removed.

17. Escalation 2 answered: drop the channel flag from task sessions. Commit following ca4b1963:
    `concorde task session` no longer passes `--dangerously-load-development-channels`, and its
    `runtime/mcp.json` sets `CONCORDE_CHANNEL=0`, so `register_wait` answers a task session with
    the `concorde task wait` command. The Task sessions and Main session Specs, the skill, the
    task-session prompt, the docs and the tests cite the main agent's probe as the reason.
18. Decision (task session): to make sure no non-interactive session is ever told it has a channel,
    the server's own detection (used when `CONCORDE_CHANNEL` is unset, as with the installed
    `.mcp.json`) now requires the flagged `claude` ancestor to have its standard input on a
    terminal. `CLAUDE_CODE_SESSION_ATTENDED` was considered and rejected: a probe showed it is
    inherited from the launching environment. Verified live with a probe server:
    interactive `claude` with the flag → channel; without the flag → none; `claude -p` with the
    flag → none. Nothing else in the code sets `CONCORDE_CHANNEL=1` (only tests do).

19. Delivered: task-validation r-20260929T160254-task_validation-f332c579 ok (no blocking finding,
    every check passed); delivery r-20260929T160828-delivery-83568e5c ok, delivery commit
    93079bdd with evidence bundle `.concorde/evidence/project-mcp-server/1.json`.

## Closed: merged, 2026-09-29T16:14:38Z
