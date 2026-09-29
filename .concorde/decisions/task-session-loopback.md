# Decision log: task-session-loopback

Goal: Establish why workers started from a pi task session cannot reach a model endpoint on localhost (e.g. a local model proxy) while workers started from a main session can, and put the options for letting them reach it to the developer

## Brief (main agent `claude session stuck debug`, 2026-09-29)

Origin: the main session `clear-conversation-state` ran a live pi verification in
`/tmp/concorde-e2e/verify-pi`. Workers started from the pi task session could not reach the
model: the developer's `~/.pi/agent/models.json` points `anthropic` at `baseUrl
http://localhost:8080` (a local model proxy); all four model calls of the specify worker failed
with "Connection error", retries too, so no Operation could run in that task session. Workers
started from a main session with the same model and `models.json` work. Evidence run:
`w-20260929T061931-ebb072` of that project (its runs may be under `.concorde/runs/` or the task's
trace; find it). The developer approved at 2026-09-29T06:34Z a task that reproduces and confirms
the cause first, then proposes fixes and puts the options to the developer. Deferred until
`owner-only-wake` and `tracing` merged; both have.

Hypothesis (unverified): the task session's sandbox runs its commands, and the workers they start,
in their own network namespace with outside traffic relayed through a proxy, while loopback is not
relayed (sandbox-runtime's `parent-proxy.ts` treats loopback that way), so `localhost:8080` inside
the namespace is empty.

Asked of the session:
1. Reproduce and confirm (or refute) the cause, with the evidence. Check also whether a Claude Code
   task session has the same problem for workers it starts.
2. Do NOT loosen the session boundary or the worker sandbox on your own: loosening a boundary is
   the developer's decision. Escalate the options (e.g. let the session sandbox reach loopback, or
   given ports only; start workers outside the session's network namespace; relay loopback through
   the proxy; others you find), each with its security effect and cost, and your recommendation.
3. Known constraint: inside a Claude Code task session's sandbox `~/.pi/agent` is read-only and pi
   refuses to start a turn (EROFS on `auth.json.lock`, see the `owner-only-wake` decision log,
   entry 8, in `.concorde/history/owner-only-wake/decisions.md`). If a live reproduction needs to
   run outside your sandbox, do not work around it: put the exact commands in the escalation for
   the main agent to run from the primary worktree, and carry on with everything else first.
4. After the developer decides, the same task implements the chosen fix, with tests and Spec
   changes in module.harness / module.task-session, and delivers.

## Task session (Claude Code, 2026-09-29)

1. **Cause confirmed, and wider than the hypothesis.** Both kinds of task session run their shell
   commands, and every worker those commands start, inside sandbox-runtime's bwrap with
   `--unshare-net`: a network namespace holding only `lo`. Outside traffic leaves only through the
   session's proxy (`HTTP_PROXY`/`HTTPS_PROXY=http://…@localhost:<port>`, bridged by socat), and the
   sandbox sets `NO_PROXY=localhost,127.0.0.1,::1,…`. Two things then break a worker's model
   calls:
   - Workers drop the proxy variables: `PiBackend.environment` and `ClaudeBackend.environment`
     (`src/concorde/harness/pi_backend.py`, `claude_backend.py`, owned by module.workers) pass only
     PATH, LANG, HOME, TMPDIR, config dirs and `*_API_KEY`. Without a proxy nothing in the namespace
     resolves or routes, so a worker started from a task session reaches **no** model endpoint,
     loopback or cloud (`curl https://api.anthropic.com` without the proxy variables: "Could not
     resolve host"; with them: HTTP 404 from the API).
   - Even with the proxy variables, `NO_PROXY` sends `localhost` direct, into the empty namespace.
   pi's HTTP client is undici's `EnvHttpProxyAgent`, so it honours both variables.
   Why it works from a main session: its workers run in the host's network namespace.
   The session proxy itself admits loopback: `allowedDomains: ["*"]` matches `localhost`, and
   sandbox-runtime 0.0.77's resolved-address guard lets a loopback name resolve to loopback;
   `curl --noproxy '' http://localhost:8080/` from this session's sandbox answered 200.
2. **Evidence.** In this session's sandbox, `pi -p --model local-openai/gpt-6` with a copy of
   `models.json` (baseUrl `http://localhost:8080/v1`) and the worker's environment: (A) worker env
   → "Connection error."; (B) worker env + proxy variables + `NO_PROXY` without loopback → "PONG";
   (C) worker env + proxy variables + the sandbox's `NO_PROXY` → "Connection error.". A real
   `concorde run understand` from this Claude Code task session failed the same way as the pi
   session's run: `r-20260929T114104-understand-d63b13b1`, worker `w-20260929T114107-c4cea8`,
   `pi_failed` / `pi_error` "Connection error." (4 turns). So a Claude Code task session has the
   same problem for its workers. Nested bwrap works inside the session sandbox, so a worker's own
   tool sandbox is not in the way.
3. **Non-ok (expected):** the understand run above is the reproduction, not a failure to repair.
4. **Experiment, not to be committed:** I patched `PiBackend.environment` locally to pass the proxy
   variables and drop loopback from `NO_PROXY`, to test option "relay through the proxy" end to
   end; the patch is reverted after the run. The fix itself touches module.workers, outside this
   task's Modules, so it is escalated rather than made.
5. **Experiment result.** With the local patch, `concorde run understand` from this task session
   ended `ok` (`r-20260929T114209-understand-3f992c3c`): the pi worker reached `local-openai/gpt-6`
   at `localhost:8080` through the session's proxy, and its own tool sandbox (nested bwrap, no
   network) still worked. The patch is reverted (`git checkout -- src/concorde/harness/pi_backend.py`);
   nothing is committed.
6. **Escalated, not decided:** how workers started inside a task session reach model endpoints.
   Every option changes module.workers (the worker environment) or the session boundary, and the
   brief reserves loosening a boundary for the developer; see the escalation.

## Escalated to the main agent, 2026-09-29T11:43:25Z

- **task-session** task session (task task-session-loopback): `worker_network_in_session`
  Confirmed cause (decision log entries 1-5): a task session, Claude Code or pi, runs its shell commands and every worker they start inside sandbox-runtime's bwrap with --unshare-net, a network namespace holding only lo; outside traffic leaves only through the session proxy (HTTP_PROXY/HTTPS_PROXY=http://...@localhost:<port>), and the sandbox sets NO_PROXY=localhost,127.0.0.1,::1,... Workers then fail twice over: (1) PiBackend.environment and ClaudeBackend.environment (module.workers) drop the proxy variables, so a worker started from a task session reaches NO model endpoint, loopback or cloud; (2) even with them, NO_PROXY sends localhost direct into the empty namespace. Main-session workers run in the host namespace, so they work. Reproduced live from this Claude Code task session: run r-20260929T114104-understand-d63b13b1 failed pi_error 'Connection error.' exactly like the pi session's w-20260929T061931-ebb072. The session proxy already admits loopback (allowedDomains * matches localhost; curl --noproxy '' http://localhost:8080/ from the session sandbox answered 200). A local, reverted patch passing the proxy variables to the pi worker and dropping loopback from NO_PROXY made the same run end ok (r-20260929T114209-understand-3f992c3c), with the worker's own no-network tool sandbox still working. Which way should workers started inside a task session reach model endpoints?
  Not handled here (decision): Every option changes module.workers (the worker environment) or the session boundary; the brief reserves loosening a boundary for the developer, and module.workers is outside this task's Modules.
  Options: A. Relay through the session proxy: workers pass on HTTP(S)_PROXY from their launch environment and, when that proxy is the sandbox's loopback bridge, drop localhost/127.0.0.1/::1 from NO_PROXY, on both backends. Security: widens nothing, since every session command can already reach loopback and every host through that proxy; workers' tool sandboxes keep no network. Cost: small (module.workers environment, tests, Spec text in module.workers/task-session/harness); also fixes cloud endpoints; needs clients that honour proxy variables (pi and Claude Code do).; B. Forward listed loopback ports only: A's proxy variables plus a socat forwarder in the namespace for each loopback port named by the model endpoints (pi models.json baseUrls, ANTHROPIC_BASE_URL) or listed in workers.json, relaying through the proxy. Security: narrowest for worker processes, though the session proxy admits all loopback anyway. Cost: moderate (forwarder lifecycle, port configuration, collisions); works for clients that ignore proxy variables.; C. Share the host network with a pi session's commands (no --unshare-net). Security: widens the pi session boundary: raw TCP/UDP anywhere, the host namespace's abstract Unix sockets (X11, D-Bus) and binding host ports. Cost: small for pi, but Claude Code has no such setting on Linux, so CC task sessions stay broken.; D. Start workers outside the session's namespace through a launcher that concorde task session starts on the host and runs reach over a Unix socket. Security: worker processes leave both the session's network and write sandbox, confined only by their grant. Cost: large (new long-lived process, IPC, lifecycle on both programs).
  Recommendation: A: it reaches every endpoint a main session's worker reaches, adds no reach the session does not already have, and is a small change; drop loopback from NO_PROXY only when the proxy itself is on loopback, so a developer's own corporate proxy keeps sending localhost direct.
  Caused by:
  - **operation** Operation understand r-20260929T114104-understand-d63b13b1 (workspace task-session-loopback): `pi_failed`
    the understand worker run w-20260929T114107-c4cea8 ended failed: pi_failed: round 1: the pi process ended with an error (pi_error) before a structured result
    Not handled here (environment): the failure lies in the environment the Operation runs in, which it cannot change
    Options: repair the environment named in the cause and run the Operation again
    Recommendation: repair the environment named in the cause and run the Operation again
    Caused by:
    - **workers** Workers run w-20260929T114107-c4cea8 (understand worker): `pi_failed`
      round 1: the pi process ended with an error (pi_error) before a structured result
      Not handled here (environment): Workers does not retry a failed pi process
      Evidence (transcript): /home/zhenyu/concorde/.concorde/tasks/task-session-loopback/workspace/runs/r-20260929T114104-understand-d63b13b1/workers/w-20260929T114107-c4cea8/transcript.jsonl
      Evidence (trace): w-20260929T114107-c4cea8 /home/zhenyu/concorde/.concorde/tasks/task-session-loopback/workspace/runs/r-20260929T114104-understand-d63b13b1/workers/w-20260929T114107-c4cea8
      Caused by:
      - **component** pi process (pi -p): `pi_error`
        pi ended without a worker result: exit code 0, 4 turn(s), reported cost 0.0, last stop reason error, error message: Connection error.; standard error ends with: Warning: No project session found with id 'w-20260929T114107-c4cea8'; creating a new session with that id.
        Not handled here (environment): pi reported an error of the model service or its own execution

```json
{
  "level": "task-session",
  "actor": "task session (task task-session-loopback)",
  "code": "worker_network_in_session",
  "detail": "Confirmed cause (decision log entries 1-5): a task session, Claude Code or pi, runs its shell commands and every worker they start inside sandbox-runtime's bwrap with --unshare-net, a network namespace holding only lo; outside traffic leaves only through the session proxy (HTTP_PROXY/HTTPS_PROXY=http://...@localhost:<port>), and the sandbox sets NO_PROXY=localhost,127.0.0.1,::1,... Workers then fail twice over: (1) PiBackend.environment and ClaudeBackend.environment (module.workers) drop the proxy variables, so a worker started from a task session reaches NO model endpoint, loopback or cloud; (2) even with them, NO_PROXY sends localhost direct into the empty namespace. Main-session workers run in the host namespace, so they work. Reproduced live from this Claude Code task session: run r-20260929T114104-understand-d63b13b1 failed pi_error 'Connection error.' exactly like the pi session's w-20260929T061931-ebb072. The session proxy already admits loopback (allowedDomains * matches localhost; curl --noproxy '' http://localhost:8080/ from the session sandbox answered 200). A local, reverted patch passing the proxy variables to the pi worker and dropping loopback from NO_PROXY made the same run end ok (r-20260929T114209-understand-3f992c3c), with the worker's own no-network tool sandbox still working. Which way should workers started inside a task session reach model endpoints?",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Every option changes module.workers (the worker environment) or the session boundary; the brief reserves loosening a boundary for the developer, and module.workers is outside this task's Modules."
  },
  "options": [
    "A. Relay through the session proxy: workers pass on HTTP(S)_PROXY from their launch environment and, when that proxy is the sandbox's loopback bridge, drop localhost/127.0.0.1/::1 from NO_PROXY, on both backends. Security: widens nothing, since every session command can already reach loopback and every host through that proxy; workers' tool sandboxes keep no network. Cost: small (module.workers environment, tests, Spec text in module.workers/task-session/harness); also fixes cloud endpoints; needs clients that honour proxy variables (pi and Claude Code do).",
    "B. Forward listed loopback ports only: A's proxy variables plus a socat forwarder in the namespace for each loopback port named by the model endpoints (pi models.json baseUrls, ANTHROPIC_BASE_URL) or listed in workers.json, relaying through the proxy. Security: narrowest for worker processes, though the session proxy admits all loopback anyway. Cost: moderate (forwarder lifecycle, port configuration, collisions); works for clients that ignore proxy variables.",
    "C. Share the host network with a pi session's commands (no --unshare-net). Security: widens the pi session boundary: raw TCP/UDP anywhere, the host namespace's abstract Unix sockets (X11, D-Bus) and binding host ports. Cost: small for pi, but Claude Code has no such setting on Linux, so CC task sessions stay broken.",
    "D. Start workers outside the session's namespace through a launcher that concorde task session starts on the host and runs reach over a Unix socket. Security: worker processes leave both the session's network and write sandbox, confined only by their grant. Cost: large (new long-lived process, IPC, lifecycle on both programs)."
  ],
  "recommendation": "A: it reaches every endpoint a main session's worker reaches, adds no reach the session does not already have, and is a small change; drop loopback from NO_PROXY only when the proxy itself is on loopback, so a developer's own corporate proxy keeps sending localhost direct.",
  "causes": [
    {
      "level": "operation",
      "actor": "Operation understand r-20260929T114104-understand-d63b13b1 (workspace task-session-loopback)",
      "code": "pi_failed",
      "detail": "the understand worker run w-20260929T114107-c4cea8 ended failed: pi_failed: round 1: the pi process ended with an error (pi_error) before a structured result",
      "evidence": [],
      "attempts": [],
      "unhandled": {
        "reason": "environment",
        "explanation": "the failure lies in the environment the Operation runs in, which it cannot change"
      },
      "options": [
        "repair the environment named in the cause and run the Operation again"
      ],
      "recommendation": "repair the environment named in the cause and run the Operation again",
      "causes": [
        {
          "level": "workers",
          "actor": "Workers run w-20260929T114107-c4cea8 (understand worker)",
          "code": "pi_failed",
          "detail": "round 1: the pi process ended with an error (pi_error) before a structured result",
          "evidence": [
            {
              "kind": "transcript",
              "ref": "/home/zhenyu/concorde/.concorde/tasks/task-session-loopback/workspace/runs/r-20260929T114104-understand-d63b13b1/workers/w-20260929T114107-c4cea8/transcript.jsonl",
              "detail": ""
            },
            {
              "kind": "trace",
              "ref": "w-20260929T114107-c4cea8",
              "detail": "/home/zhenyu/concorde/.concorde/tasks/task-session-loopback/workspace/runs/r-20260929T114104-understand-d63b13b1/workers/w-20260929T114107-c4cea8"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "environment",
            "explanation": "Workers does not retry a failed pi process"
          },
          "options": [],
          "recommendation": "",
          "causes": [
            {
              "level": "component",
              "actor": "pi process (pi -p)",
              "code": "pi_error",
              "detail": "pi ended without a worker result: exit code 0, 4 turn(s), reported cost 0.0, last stop reason error, error message: Connection error.; standard error ends with: Warning: No project session found with id 'w-20260929T114107-c4cea8'; creating a new session with that id.",
              "evidence": [],
              "attempts": [],
              "unhandled": {
                "reason": "environment",
                "explanation": "pi reported an error of the model service or its own execution"
              },
              "options": [],
              "recommendation": "",
              "causes": []
            }
          ]
        }
      ]
    }
  ]
}
```

## Escalated to the main agent, 2026-09-29T11:43:33Z

- **task-session** task session (task task-session-loopback): `task_modules_scope`
  Every fix option changes the worker environment built in src/concorde/harness/pi_backend.py and claude_backend.py, which module.workers owns (its requirements req.workers.* and launch.md describe that environment). This task binds only module.harness and module.task-session, so it cannot implement the chosen fix, its tests and its Spec change in module.workers as it stands.
  Not handled here (decision): Changing a task's Modules, or opening another task, is the main agent's step; a task session never goes beyond its task's Modules.
  Options: Add module.workers to this task's Modules; this session then implements the chosen option with tests and Spec changes in module.workers, module.task-session and module.harness, and delivers; Close this task as completed with the diagnosis and open a new task bound to module.workers (plus module.task-session/module.harness for the Spec text) for the fix
  Recommendation: Add module.workers to this task, so the diagnosis, experiment and fix stay in one decision log.

```json
{
  "level": "task-session",
  "actor": "task session (task task-session-loopback)",
  "code": "task_modules_scope",
  "detail": "Every fix option changes the worker environment built in src/concorde/harness/pi_backend.py and claude_backend.py, which module.workers owns (its requirements req.workers.* and launch.md describe that environment). This task binds only module.harness and module.task-session, so it cannot implement the chosen fix, its tests and its Spec change in module.workers as it stands.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Changing a task's Modules, or opening another task, is the main agent's step; a task session never goes beyond its task's Modules."
  },
  "options": [
    "Add module.workers to this task's Modules; this session then implements the chosen option with tests and Spec changes in module.workers, module.task-session and module.harness, and delivers",
    "Close this task as completed with the diagnosis and open a new task bound to module.workers (plus module.task-session/module.harness for the Spec text) for the fix"
  ],
  "recommendation": "Add module.workers to this task, so the diagnosis, experiment and fix stay in one decision log.",
  "causes": []
}
```

## Main agent `claude session stuck debug`, answers (2026-09-29)

12. **Escalation 1 `worker_network_in_session`: the developer chose option A** — workers pass on
    the session's HTTP(S)_PROXY and, when that proxy is on loopback, drop localhost/127.0.0.1/::1
    from NO_PROXY, on both backends; workers' tool sandboxes keep no network. The developer did
    not want the further narrowing to the model endpoints' hosts only. Before choosing, the
    developer asked what a task session confines (writes only; reads and network open by design)
    and which workers need the network (every worker process for its model calls, never its tools).
13. **Escalation 2 `task_modules_scope`: decided by the main agent without the developer** —
    option 2: close this task as completed with the diagnosis and open a new task bound to
    module.workers, module.task-session and module.harness for the fix. Reason: a task's Modules
    cannot be changed by any command, and `pi-worker-default-model` was changing the same
    `pi_backend.py` in parallel until it merged (435784ba). The new task's brief points at this
    decision log so the diagnosis and experiment carry over.

## Closed: completed, 2026-09-29T11:54:17Z

Diagnosed: workers started inside any task session (Claude Code or pi) run in the session sandbox's network namespace and lose the session proxy variables, so they reach no model endpoint; the developer chose option A (relay through the session proxy), implemented in task worker-session-proxy
