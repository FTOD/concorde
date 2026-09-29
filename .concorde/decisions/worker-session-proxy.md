# Decision log: worker-session-proxy

Goal: Workers started inside a task session (Claude Code or pi) reach their model endpoints, including one on localhost, through the session's proxy, while their tool sandboxes keep no network

## Brief (main agent `claude session stuck debug`, 2026-09-29)

Read first the diagnosis in `.concorde/history/task-session-loopback/decisions.md` (entries 1-13),
which this task implements.

Diagnosis in short: both kinds of task session, Claude Code and pi, run their shell commands and
the workers those commands start inside sandbox-runtime's bwrap with `--unshare-net` (a namespace
holding only `lo`); traffic leaves only through the session proxy (`HTTP(S)_PROXY=…@localhost:<port>`)
and the sandbox sets `NO_PROXY=localhost,127.0.0.1,::1,…`. `PiBackend.environment` and
`ClaudeBackend.environment` drop the proxy variables, so a worker started from any task session
reaches no model endpoint at all; with them passed, NO_PROXY still sends localhost into the empty
namespace. The session proxy lets loopback through (`curl --noproxy '' http://localhost:8080/`
answered 200). A local patch passing the proxy variables to the pi worker and dropping loopback from
NO_PROXY made the understand run ok (`r-20260929T114209-understand-3f992c3c`), with the worker's
tool sandbox still offline. That patch was reverted and is not on any branch.

Developer's decision (option A, 2026-09-29): workers pass on the session's `HTTP_PROXY`/`HTTPS_PROXY`
(and the lowercase forms as present) to the worker process, and, only when that proxy itself is on
loopback, drop `localhost`, `127.0.0.1` and `::1` from `NO_PROXY`/`no_proxy`, so a developer's own
non-loopback proxy keeps sending localhost direct. Both backends, pi and Claude Code. Workers' tool
sandboxes keep no network (`req.workers.bash-sandbox`, `req.workers.pi-sandbox` unchanged). The
developer declined the further narrowing to the model endpoints' hosts only. This makes the
session boundary's promise "network open to every host" hold for the workers a session starts; it
loosens no boundary.

Asked of the session:
- Implement it in module.workers (pi_backend.py, claude_backend.py and their Spec: launch.md / pi.md
  requirements and scenarios), with the task-session / harness Spec text where the session boundary
  or task-session promises mention it.
- Deterministic tests for the environment rules (proxy passed on; loopback dropped only for a
  loopback proxy; no proxy → unchanged), and a live check from inside your own task session: an
  unbound-free, bound `understand` run in your worktree that ends ok on the pi backend, and on the
  Claude Code backend too if a worker configuration lets you choose it without changing tracked
  files for good (revert any temporary change). Worker model spend for this is approved.
- Main-session workers (no proxy in the environment) must behave exactly as before.
- Record decisions and non-ok results in this log, deliver, and report to the main agent.

## Task session (Claude Code, 2026-09-29)

1. **Where the rule lives.** One function, `proxy_environment()` in
   `src/concorde/harness/claude_backend.py` (module.workers), which both `ClaudeBackend.environment`
   and `PiBackend.environment` apply; pi_backend already imports its shared types from there.
   The rule is written once in `launch.md` ("Proxy" under Launch, `req.workers.proxy-passed`) and
   referenced from both environment tables (`launch.md`, `pi.md`).
2. **Which variables pass.** `HTTP_PROXY`, `HTTPS_PROXY`, `http_proxy`, `https_proxy` when set to a
   non-empty value, and `NO_PROXY`/`no_proxy` only alongside at least one of them, so a
   main-session worker with no proxy gets exactly the environment it got before (even when the
   host sets `NO_PROXY` alone). `ALL_PROXY`, `FTP_PROXY`, `GRPC_PROXY` etc. never pass: the brief
   names only the HTTP(S) pair, and both clients reach their endpoints over HTTP(S).
3. **When loopback is dropped.** Only when *every* passed proxy names a loopback host (`localhost`
   or a loopback IP, with or without a scheme, IPv6 in brackets); a mixed set (one proxy on
   loopback, one elsewhere) keeps the lists unchanged, the conservative reading of "only when that
   proxy itself is on loopback". Entries removed: `localhost`, `127.0.0.1`, `::1` and `[::1]`
   (case-insensitive, whitespace trimmed); a list left empty is not passed at all. A malformed
   proxy URL counts as not loopback.
4. **Test hermeticity.** The worker test fixture (`WorkerProject`) now starts from a host
   environment without proxy variables, because inside a task session's sandbox the host sets
   them and the existing "only the listed environment" assertions would otherwise see them.
5. **Spec text outside module.workers.** One explanatory paragraph each in task-session
   `module.md` ("The boundary") and `requirements.md` (`req.task-session.shell-boundary` prose),
   and in harness `module.md` (session boundary summary): the open network is reached through the
   sandbox's proxy on localhost, which workers pass on to their own process, never to their tools.
   No requirement of task-session or harness changes meaning.
6. **Live check, pi backend: ok.** From this Claude Code task session's sandbox, bound
   `concorde run understand --modules module.workers` ended `ok`:
   `r-20260929T120202-understand-e52030ff`, pi worker `w-20260929T120203-5200d1` on the user's pi
   default model, 80 s. Before the fix the same run failed `pi_error` "Connection error."
   (`r-20260929T114104-understand-d63b13b1` in task-session-loopback).
7. **Non-ok (my mistake, repaired):** the first Claude Code attempt
   `r-20260929T120336-understand-cc6c53eb` failed `worker_model_unavailable` / `config_invalid`
   because my temporary `.concorde/workers.json` entry used `operations.understand.backend`
   instead of `operations.understand.workers.worker.backend`. The file was restored with
   `git checkout` right after the run; retried with the right shape.
8. **Live check, Claude Code backend: ok.** With a temporary, uncommitted
   `operations.understand.workers.worker.backend = "claude"` in `.concorde/workers.json` (restored
   with `git checkout` right after; `git status` clean), the same bound understand run ended `ok`:
   `r-20260929T120356-understand-e31cf860`, Claude Code worker `w-20260929T120358-cc794f` on Claude
   Code's default model, its model calls going through this session's proxy.
9. **Delivered.** Full suite 806 passed / 4 skipped; `build --check` and `spec-validation` clean;
   `task-validation` ready (`r-20260929T120512-task_validation-f390f65a`); `delivery`
   `r-20260929T120651-delivery-410d2407` committed `7c997504` on `concorde/worker-session-proxy`
   with `.concorde/evidence/worker-session-proxy/1.json`. Nothing escalated; nothing open.

## Closed: merged, 2026-09-29T12:09:21Z
