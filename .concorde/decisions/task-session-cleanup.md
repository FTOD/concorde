# Decision log: task-session-cleanup

Goal: Ending a task removes its Claude Code task sessions from Claude's session list after keeping each transcript in the task's trace, and a close without a merge first stops a Claude Code task session that still runs

## Brief (main agent, 2026-09-29)

Developer's decisions this task carries out:

- Task sessions do not matter to the developer; only main sessions do. Many finished Claude Code
  task sessions make Claude's session list noisy. State this positioning in the Task session Spec,
  not only as an implementation detail.
- Ending a task, by every outcome (`merged` through `task merge`, `--completed`, `--failed`),
  removes every Claude Code task session the task record lists (a task may have had several) from
  Claude's session list with `claude rm <id>`.
- The removal happens after the close has succeeded and is best effort: a failing `claude rm`
  never fails the close; it adds a warning to the result naming the session, the full reason and
  the command to remove it by hand.
- Before removing a session, copy its Claude Code transcript into that session's trace node
  (`sessions/<session>/`), so it moves to the history with the task folder, as a pi task session's
  session file already does. The history must still keep the closed task as it was.
- Also fix the gap found while assessing: a close without a merge (`--completed` / `--failed`)
  stops the runs and a running pi round (`stop_task`, `src/concorde/tasks/store.py`) but never a
  Claude Code task session that still runs, which then keeps working in a removed worktree. Stop it
  first, like the pi round.
- Verify with a real throwaway `claude --bg` session (model spend needs no permission) before
  relying on it: whether `claude rm` deletes the transcript, whether it touches the session's cwd
  (the task worktree is not a Claude-managed worktree), what it does for a busy, idle, done and
  stopped session, and what `claude stop` does to a busy one. Record the observations here.

Left to the task session: where the transcript is found (session id, cwd-derived project folder),
the transcript's file name in the trace node, the warning's shape, and how tests fake `claude`.

Scope: bound to module.tasks and module.task-session. The main-session guidance
(`prompts/main-session/skill.md`, module.main-session) mentions `claude agents` / `claude stop`;
the active task `worker-config-independent` is bound to module.main-session, so do not edit that
guidance here; if you judge a guidance sentence necessary, say so in your report instead.

## Task session, 2026-09-29: probing `claude rm` / `claude stop` (not `ok`)

The brief asks for a real throwaway `claude --bg` probe. It cannot run inside this session's
sandbox: `claude --bg` in a throwaway worktree of this repository fails with
`Couldn't start the session — EROFS: read-only file system, mkdir '/home/zhenyu/.claude/jobs/eedc2f42'`
(the session boundary keeps `~/.claude/jobs` read-only; `claude rm`/`stop` write there too). A
throwaway repository under `$TMPDIR` is refused earlier with `Workspace not trusted`. I removed the
throwaway worktree again. I read the behaviour instead from Claude Code 2.1.284's own bundled
source (`claude.exe`), and escalate the live probe to the main agent, which is not under this
boundary (script in the report).

Observations from the source, to be confirmed live:

- `claude rm <id>` (function behind `cli_bg_rm`) first kills the job through the daemon
  (`op: "kill"`, evict) and refuses (`kill_unconfirmed`, exit 1, "couldn't remove <id> — …") when
  it cannot confirm the kill; so a busy or idle session is stopped by `rm` itself, and an exited one
  (done, stopped, failed) is accepted ("Works on sessions that have already exited").
- It removes a worktree only when the job's state records `worktreePath`, i.e. a Claude-managed
  worktree (`claude --worktree`); a task session is started with `cwd` = the task worktree and no
  `--worktree`, so its cwd is not touched. It then removes the job's state directory
  `~/.claude/jobs/<id>/` and prints `removed <id>`, exit 0.
- Nothing in that path deletes `~/.claude/projects/<cwd-derived>/<session uuid>.jsonl`; whether the
  transcript survives is still to be confirmed live, which is why the copy is made first either way.
- `claude stop <id>` kills the job and prints `stopped <id>` (exit 0), also for a job already gone;
  it exits 1 with `No job matching '<id>'` for an unknown id and `couldn't confirm <id> was stopped
  — …` when the kill is unconfirmed. The conversation is kept.
- The transcript is `<config>/projects/<cwd with every non-alphanumeric character as '-'>/<session
  uuid>.jsonl`, with an optional sidecar folder `<session uuid>/` (subagent transcripts,
  `tool-results/`); the short id `claude --bg` prints (the recorded `reported_id`) is the uuid's
  first 8 characters (seen for every job `claude agents --json --all` lists).

## Task session, 2026-09-29: design decisions within the brief

- Transcript lookup: in `$CLAUDE_CONFIG_DIR` (default `~/.claude`) `projects/`, the folder derived
  from the task worktree's path first, then every project folder, for exactly one
  `<reported id>*.jsonl`; no `claude agents` call, so the lookup needs no daemon.
- File names in the session's trace node: `transcript.jsonl`, and its sidecar folder, when
  present, as `transcript/`; both recorded as artifacts of the session node.
- The copy is made before the task folder moves to the history, for every outcome, so the history
  is never written after the move. A session whose transcript cannot be found or copied is not
  removed (so nothing is lost) and gets a warning; `claude rm` runs only after the move.
- Warnings are strings, like `task merge`'s; `task close` now prints
  `{"record": …, "warnings": […]}` like `task merge` instead of the bare record, so it can carry them.
- A close without a merge runs `claude stop <id>` for every Claude Code task session of the task
  before it waits for the workspace lock, beside the pi round's stop. `No job matching` counts as
  already gone; any other failure refuses the close (`session_stop_failed`) before anything
  changed, like a pi stop that fails, since removing the worktree under a session that may still
  run is the gap the brief closes.
- Tests fake `claude` with an executable on `PATH` that logs its arguments and answers like Claude
  Code, and a temporary `CLAUDE_CONFIG_DIR` holding a transcript.

## Task session, 2026-09-29: further decisions while implementing

- Order of the stops in a close without a merge: the Claude Code task sessions first, then the
  runs and the pi round, so a session cannot start a new run after the runs were stopped.
- `contract.task-session.session-trace` stays version 1: the typed value's data (program, name,
  main, model, reported_id) is unchanged; the transcript is a file and artifact of the node, which
  `contract.tracing.node` already admits. Its semantics now names the transcript files. Bumping the
  version would also make every session node of a task open today (version-1 content) fail the
  typed-value check when the close rewrites it to add the artifact.
- A merge stops no Claude Code task session (the brief's stop is for closes without a merge); its
  `claude rm` after the close kills one that still runs, so the kept transcript may lack only what
  such a session wrote after the copy.
- New scenarios `scenario.task-session.end-removed`, `close-stops`, `stop-unconfirmed`,
  `remove-best-effort` and requirements `req.task-session.stopped-before-close`,
  `transcript-kept`, `removed`; the Tasks contracts name the new close output, the merge's added
  warnings and `session_stop_failed`.
- Verified: `spec-validation` success with no findings, `build --check` without differences, the
  full suite 811 passed, 4 skipped.
- Not changed, outside this task's Modules: `prompts/main-session/skill.md` (module.main-session)
  and `docs/using-concorde.md` do not say that `task close` now prints `{"record", "warnings"}`
  and that a warning names a Claude Code task session to remove by hand; proposed to the main
  agent in the report.

## Task session, 2026-09-29: live probe for the main agent to run

The live probe this session could not run (see above). Save it to a file and run it with bash from
the primary worktree, outside a task session's sandbox; it spends a few cents of haiku, starts four
throwaway background sessions in a throwaway linked worktree (like a task worktree, not
Claude-managed), and removes them and the worktree at the end.

```bash
#!/usr/bin/env bash
set -u
root=$(git rev-parse --show-toplevel)
probe=$(mktemp -d /tmp/concorde-rm-probe.XXXXXX)
git -C "$root" worktree add --detach "$probe/wt" HEAD >/dev/null
cd "$probe/wt" || exit 1
folder="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/$(printf '%s' "$probe/wt" | sed 's/[^A-Za-z0-9]/-/g')"
start() { # name prompt -> short id
  claude --bg --name "$1" --model haiku --permission-mode auto "$2" 2>&1 |
    sed 's/\x1b\[[0-9;?]*[ -\/]*[@-~]//g' | sed -n 's/.*backgrounded · \([0-9A-Za-z-]*\) ·.*/\1/p'
}
state() { claude agents --json --all | python3 -c "import json,sys; print([x.get('state') for x in json.load(sys.stdin) if x['id']=='$1'])"; }
done_id=$(start probe-done "Reply with the single word ok and do nothing else.")
busy_id=$(start probe-busy "Run exactly this shell command and wait for it: sleep 300")
stop_id=$(start probe-stopped "Run exactly this shell command and wait for it: sleep 300")
idle_id=$(start probe-idle "Say hello, then wait for my next message.")
echo "ids: done=$done_id busy=$busy_id stopped=$stop_id idle=$idle_id"
sleep 60   # one-off probe: let each session reach its state
for id in "$done_id" "$busy_id" "$stop_id" "$idle_id"; do echo "$id state before: $(state "$id")"; done
echo "--- claude stop $stop_id (busy):"; claude stop "$stop_id"; echo "exit=$?"; echo "state: $(state "$stop_id")"
echo "--- claude stop $done_id (already done):"; claude stop "$done_id"; echo "exit=$?"
echo "--- claude stop deadbeef (unknown):"; claude stop deadbeef; echo "exit=$?"
echo "transcripts before rm:"; ls -la "$folder"
for id in "$done_id" "$busy_id" "$stop_id" "$idle_id"; do
  echo "--- claude rm $id:"; claude rm "$id"; echo "exit=$?"
  echo "state after: $(state "$id")"
  ls "$folder"/"$id"*.jsonl >/dev/null 2>&1 && echo "transcript kept" || echo "TRANSCRIPT GONE"
  test -d "$probe/wt" && echo "cwd kept" || echo "CWD GONE"
done
echo "--- claude rm $done_id again:"; claude rm "$done_id"; echo "exit=$?"
pgrep -af "sleep 300" || echo "no sleep 300 left running"
cd "$root" && git worktree remove --force "$probe/wt" && rm -rf "$probe"
```

What the implementation relies on, to check in its output: `claude stop` exits 0 for a busy and
for a done session and answers `No job matching` for an unknown id; `claude rm` exits 0 for done,
busy, stopped and idle sessions, kills the busy one (no `sleep 300` left), keeps the cwd, and
answers `No job matching` when run again. Whether the transcript survives `rm` does not matter to
the implementation (it copies first), but is worth recording here.

## Task session, 2026-09-29: delivered

`task-validation` ok (run r-20260929T123514-task_validation-2735e5c8, ready, no blocking finding);
`delivery` ok: delivery commit 1e532f04e4fad7b498e989a6bfb850e30fd3c2ec on top of 9447c86f, bundle
`.concorde/evidence/task-session-cleanup/1.json`. Still open: the live probe above, which the main
agent runs before merging.

## Main agent, 2026-09-29: live probe results (Claude Code 2.1.284)

The probe script's id extraction failed (its `sed` found no id in `claude --bg`'s output, while
`session.py`'s STARTED pattern works, as this task's own session start showed), so its stop/rm
steps ran with empty ids; the four throwaway sessions were found by name with
`claude agents --json --all` and probed by hand, with a plain directory (not a worktree) holding a
marker file recreated as their cwd:

- `claude stop` on a running (`blocked`) session: `stopped <id>`, exit 0, state `stopped`; on a
  `done` session: `stopped <id>`, exit 0; on an unknown or removed id: `No job matching '<id>'.
  Run 'claude agents' to list running sessions.`, exit 1.
- `claude rm` on `done`, `blocked` (running, twice) and `stopped` sessions: `removed <id>`, exit 0;
  each disappears from `claude agents --all`; no `sleep 300` left running.
- `claude rm` keeps the transcript `~/.claude/projects/<cwd-derived>/<uuid>.jsonl` and does not
  touch the cwd (marker kept). A second `claude rm`: `No job matching '<id>'`, exit 1.

This confirms every behaviour the implementation relies on. Probe sessions and directory removed.

## Closed: merged, 2026-09-29T12:40:15Z
