# Decision log: stale-text-cleanup

Goal: Remove text made stale by recent changes: the task-session sandbox still given as a reason in Workers, Harness and the installer, and code_review described as a change review only in Execution's Spec and the user documents, now that it also has --scope module.

## Brief (main agent, 2026-10-01)

The developer asked the main agent to look at the Issue store and fix the more important Issues;
this task gathers the text that recent merges left stale (session-without-sandbox and
module-code-review). No behaviour changes: text, comments and docs only.

Issues this task resolves, with their tiers (fix each yourself; report the fix you chose for the
`preferred-fix` one):

- I-cbde7d00eba65a7bbdacf14d8b458844, `preferred-fix` (Workers): the proxy rule is justified by a
  task session's sandbox, which no longer exists. Keep the behaviour (passing the host's proxy
  variables, stripping loopback from the no-proxy lists when every proxy is a loopback host) and
  restate its reason as any enclosing loopback proxy, such as a developer's local model proxy or
  a sandboxed main agent; retitle and re-set-up scenario.workers.session-proxy accordingly and fix
  the comments in src/concorde/harness/claude_backend.py and
  tests/concorde/harness/workers/test_workers.py.
- I-c650cd574f6055fcb645ee1fc885f830, `obvious-fix` (Harness): "Why the Harness is separate" says
  the sandbox settings serve a task session; only the write-hook table is shared.
- I-14aba3400a315638beb54fcae9787846, `suggestion` (Distribution): the STEP_RULES comment in
  src/concorde/distribution/install.py gives the sandbox as the reason; give the reason the
  Workflows Spec now gives.
- I-12e8a5be40ff59c680a2ed46ee94554e, `obvious-fix` (root, user docs): docs/using-concorde.md and
  docs/README.md describe code_review only as a change review; mention `--scope module`, that
  findings become Issues, and that the unbound form needs `--base` only for a change review.
- I-dff4a8ecc67f5c2c9509354f07f8b230, `obvious-fix` (Execution): the unbound-run passage lists
  `code_review` (with `--base`) only; write it as the main-session Spec does.

While there, if you meet other passages in these Modules that still give the task-session sandbox
as a reason, fix them too and list them in your report. Do not touch specs/concorde/issues/ or the
main-session guidance: task issue-list-filters is changing them in parallel.

## Task session decisions (2026-10-01)

- I-cbde7d00eba65a7bbdacf14d8b458844 (preferred-fix): kept the proxy behaviour and restated its
  reason in Workers' Proxy section as any enclosing loopback proxy (a developer's local model proxy
  or a sandboxed main agent's session proxy), dropping the task-session sandbox and the "main
  session has no proxy" sentence in favour of "a worker started with no proxy in its environment".
  Kept the scenario id `scenario.workers.session-proxy` (renaming it would move the identity for a
  wording fix; "session" still fits a sandboxed main agent's session) and retitled it "A worker
  started behind a loopback proxy uses that proxy" with a GIVEN naming an enclosing loopback proxy.
  Renamed the test constant `SESSION_PROXY` to `LOOPBACK_PROXY` and the two verifying tests to
  `test_a_(pi_)worker_behind_a_loopback_proxy_uses_it`; fixed the comment at `PROXY_VARIABLES` and
  the `proxy_environment` docstring in claude_backend.py and the fixture comment in test_workers.py.
- I-c650cd574f6055fcb645ee1fc885f830: "Why the Harness is separate" now names only the shared
  write-hook table.
- I-14aba3400a315638beb54fcae9787846: STEP_RULES comment now gives Workflows' reason (the step
  runs as the MCP server's own process so it outlives the step agent's short call).
- I-12e8a5be40ff59c680a2ed46ee94554e: docs/README.md and docs/using-concorde.md describe
  `--scope module`, findings recorded as Issues, and `--base` only for an unbound change review.
- I-dff4a8ecc67f5c2c9509354f07f8b230: Execution's unbound-run passage now reads "`code_review` (a
  change review with `--base`, a Module review without)", as the main-session Spec does.
- Out of scope: specs/concorde/execution/commands/validation/module.md (module.validation, not
  bound) still names a task session as the session whose Bash sandbox leaves placeholder files;
  recorded as Issue I-cdf641f04c305727a70ed67bb9a25afe (obvious-fix). No other passage in the bound
  Modules still gives the task-session sandbox as a reason.
- Verification: spec-validation 0 findings, build --check no differences, Workers and Distribution
  tests 114 passed, 4 skipped; Prettier and ruff clean.

## Closed: merged, 2026-10-01T12:43:49Z
