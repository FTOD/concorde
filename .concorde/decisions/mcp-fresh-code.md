# Decision log: mcp-fresh-code

Goal: Make the project MCP server answer every query and short write with the current Concorde code of the command it presents, so a merge or concorde update during a session never leaves its tools running stale code

## Brief (main agent, 2026-10-01)

Resolves Issue I-25910d5440ce53f49f087bfe835e4f85 ("Project MCP server keeps serving the Concorde
code it started with", severity high, tier preferred-fix). Read it with
`python3 scripts/concorde.py issues show I-25910d5440ce53f49f087bfe835e4f85` first.

Cause, established by the main agent: the main session's server process started at 20:31 +0800;
commit 920c9539 added the Issue report's `severity` at 21:09; the server's in-process
`concorde.issues` code then refused every record carrying it (`invalid_issue`, "severity: unknown
field"), while `python3 scripts/concorde.py issues list` answered correctly.

The developer asked the main agent to find the cause and fix it. Direction decided by the main
agent (ordinary scope: the server's internal structure; the promise only gets stronger):

- Every query and short write answers with the code that the `concorde` command of the primary
  worktree would run at the time of the call. Preferred way: run the presented command as a
  process of its own per call (the server keeps passing the session's provenance and its
  structured arguments), so the answer and the refusal are literally the command's own.
- The long-lived server keeps only what needs a long-lived process: the MCP protocol, the
  channel, the waits it registered and the merge or step processes it watches. Where those run
  Concorde code (lock and task-state checks of register_wait, the merge watcher), choose whether
  they also run as fresh processes (for example `concorde task wait` as a child the server
  watches) and record the choice.
- State the promise in module.main-session's Spec (requirement and scenario: Concorde's code
  changes between two calls of the same session, and the second call answers with the new code)
  and test it.

Left to the task session (record each choice here): the per-call mechanism and how a tool
call's arguments and the session's provenance reach the child process, the cost per call, how a
failing child process is reported as an error chain link, and whether the server's own protocol
code should notice that it is outdated. Work within module.main-session; escalate a change any
other Module would need.

## Task session decisions (2026-10-01)

- **Per-call mechanism.** Every tool call, queries, short writes, Issue tools, `task_merge`,
  `register_wait` and `workflow_step` alike, runs as a fresh process of the primary worktree's
  `concorde` at the time of the call (its `.concorde/bin/concorde`, or `python3
  scripts/concorde.py` in Concorde's checkout, as Workflows' `concorde_command` finds it):
  `concorde project-mcp --call <tool>`. Reason: one internal entry reuses the existing tool code
  and its refusal mapping unchanged (no per-tool translation into command lines, and `run_result`,
  `workflow_report` and `locks` have no command of their own), while the code that answers is
  always the current one. The structured arguments and the session's provenance (primary
  worktree, session's folder, Claude Code session id, channel) go to the child as one JSON object
  on standard input; it prints one JSON answer (`value` or `error`) on standard output.
- **What stays in the long-lived server.** The MCP framing, `initialize`/`tools/list`, finding the
  primary worktree, channel detection, the channel notifications, the wait processes it watches
  and the merge processes it reaps. No Tasks, Tracing or Issues code runs in the server process.
- **Waits run fresh too.** A registered wait is `concorde task wait …` of the primary worktree,
  run as a child the server watches, its printed answer or refusal becoming the `wait_done` or
  `wait_failed` event; the check whether it already happened runs in the call's process. Reason:
  waits read task records, whose format may change. The wait process is tied to the server
  (parent-death signal, and terminated when the session's stdin closes), so no wait outlives its
  session.
- **The merge.** The call's process validates, takes both locks without waiting, writes the
  holder lines, prints the start and then execs `concorde task merge` of the primary worktree in
  place, so the merge process is the very process the server started (exact exit status for
  `merge_ended`, same pid as the holder lines) and inherits both locked descriptors. If the exec
  fails, it prints `start_failed` instead and exits, releasing both locks.
- **A failing child** (no JSON answer, an exit before answering, a start refused by the OS, or no
  answer within its time limit) is refused with the server's own `call_failed` link (reason
  `environment`) naming the command, its exit status and the end of its standard error.
- **Noticing outdated code.** Each answer carries a digest of the current code's tool list; when it
  differs from the list the server last served, the server sends `notifications/tools/list_changed`
  (declared `listChanged: true`) and answers the next `tools/list` from the current code. The
  server's own protocol code (framing, instructions text) is not replaced during a session:
  it carries no record format or rule, and the next session starts with the new one.
- **A lock wait names the holder it was registered for.** The fresh `concorde task wait` may start
  after the holder already released the lock, and then answers `held_by: null` (seen in
  `scenario.main-session.project-mcp-wait-channel`, whose test failed on it at first). So the
  call's `waits_for`, which the event's text repeats, names the holder line the call saw;
  the command's own answer is passed on unchanged.
- **Time limits.** An ordinary call's process may take 300 s, a `workflow_step` call's its wait
  plus 120 s (the step command inside keeps its own wait plus 60 s); one that exceeds it is
  stopped and refused with `call_failed`.
- **Cost per call.** Measured on this machine: a fresh process adds about 0.1 s
  (`project-mcp --tools` 0.10–0.12 s); `issue_list` answered in 0.19 s and `task_list` in
  0.47 s, of which 0.42 s is `list_tasks` itself. Accepted: the session's calls are few and
  interactive.
- **Test of the promise.** The new test gives the test project a `.concorde/bin/concorde` that runs
  a copy of `src/`, changes that copy between two calls of one session (a changed `task_list`
  and an added tool) and checks the second answer, the `tools/list_changed` notice and the new
  listing, then a broken launcher's `call_failed`. The wait-ends-with-server check was verified to
  fail with the parent-death signal removed.
- **Other Modules' wording left as is.** Tracing's module.md says the server "gives the locks it
  took to the merge it starts" and Workflows' module.md calls the step command "the server's own
  child"; both still hold loosely (the call's process takes the locks and becomes the merge; the
  step command is a child of the call's process). Not changed, since they are other Modules'.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T15:52:08Z

mcp-fresh-code delivered: delivery commit 7af24722 on concorde/mcp-fresh-code (work in 5168d6d4); resolves Issue I-25910d5440ce53f49f087bfe835e4f85 (preferred-fix, taken as the Issue's preferred fix). The project MCP server no longer runs any tool in its own process: every tools/call (and tools/list) runs `concorde project-mcp --call <tool>` (`--tools`) of the primary worktree's current `concorde` (.concorde/bin/concorde, or scripts/concorde.py here) as a fresh process, arguments and the session's provenance as one JSON object on stdin. register_wait's watch runs that `concorde task wait` as a child tied to the server (parent-death signal, terminated at session end); task_merge's call process takes both locks, answers, then execs `concorde task merge` keeping them (same pid as the holder lines, exact exit status for merge_ended). New: call_failed refusal for a call process without an answer; the server declares listChanged and sends tools/list_changed when the current code's tools differ from those it listed. Spec of module.main-session: Current code section, req project-mcp-current-code / -tools-changed / -call-failed / -wait-ends, scenario project-mcp-fresh-code (test changes the primary's Concorde between two calls of one session), contracts and glossary definition updated. Decisions (all in the decision log): the per-call mechanism above; waits and merge also run fresh; a lock wait's waits_for names the holder seen at registration (the fresh wait may start after release); limits 300 s per call, wait+120 s for workflow_step; ~0.1 s extra per call measured; the server's own protocol code and instructions are not replaced mid-session. Checks: full suite 878 passed, 4 skipped; build --check and spec-validation ok; task-validation ready. Open, not mine: Tracing's module.md ("gives the locks it took to the merge it starts") and Workflows' module.md ("the server's own child") still hold only loosely; no change made there. Note: sessions running now keep the old server until they restart once after the merge.

## Closed: merged, 2026-10-01T15:52:24Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 7af24722547f7d691fe90f2b60bbfd86c87892ae into main and closed it as merged. Nobody answers a report after that.
