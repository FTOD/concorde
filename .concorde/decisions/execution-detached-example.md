# Decision log: execution-detached-example

Goal: Fix the stale example in Execution's detached-run passage, which still names a task session's background Bash as a sandboxed call (Issue I-07e549dd)

## Brief (main agent, 2026-10-01)

Fix Issue I-07e549dde12655e095abcabcfb422fee (obvious-fix, module.execution): the passage of
`specs/concorde/execution/module.md` on a detached run living only as long as its PID namespace
still gives a task session's background Bash as an example of a sandboxed call. Since
`session-without-sandbox` (merged at a5371ab4) a task session has no OS sandbox. Keep the PID
namespace statement, which still holds for workers and for a main agent running in a sandbox;
correct only the example and anything else in Execution's Specs that says the same. Change no
promise. The task record `resolves` the Issue, so `task merge` closes it; do not close it yourself.

This is also the first task session started without the OS sandbox: prepare your worktree
yourself (CLAUDE.md lists the steps), and report in your delivery message anything about your
environment that did not work as the task-session guidance says, even if you worked around it.
Then build, spec-validation, relevant tests, `task-validation`, `delivery`, report.

## Decisions (task session, 2026-10-01)

- **Rewrote the stale example and named who is sandboxed instead.** The passage's last sentences now
  say that which callers are sandboxed is not Execution's to say, and give the cases: a worker's
  Bash on the Claude Code backend (`req.workers.bash-sandbox`), a main agent's own session, which
  may be, and a task session's calls, which are not
  (`req.task-session.no-sandbox`). A task session is kept as an example, but of starting its runs in
  background Bash rather than detached "because Claude Code may end the processes of a call that
  returned", the reason Issue I-07e549dd itself gives, not because of a namespace. The PID namespace
  statement and every sentence before it are unchanged, and the passage carries no SHALL, so no
  promise changed.
- **Linked `main agent` to the glossary.** Naming the main agent made `specs/concorde/execution/module.md`
  use the term for the first time, which `CHK.term.unlinked` reported as a warning; its first use is
  now linked. `spec-validation` ends with 0 errors and 0 warnings.
- **Left three stale statements outside the task's Modules alone and reported them as Issues**, since
  each belongs to another Module and this task's goal is the Execution passage:
  - `I-cbde7d00eba65a7bbdacf14d8b458844` (module.workers, preferred-fix): Workers' Proxy section and
    `scenario.workers.session-proxy` still justify passing proxy variables and stripping loopback by
    a task session's sandbox and its loopback-only network namespace, which `req.task-session.no-sandbox`
    removed; the code and test comments repeat it.
  - `I-c650cd574f6055fcb645ee1fc885f830` (module.harness, obvious-fix): "Why the Harness is separate"
    says "the same write-hook table and sandbox settings serve a worker and a task session", which the
    same document denies a few sections earlier with "the settings carry no sandbox".
  - `I-fc326b9c1f095e6bac9723e4bcf9de65` (module.workflows, preferred-fix): the test that verifies
    `scenario.execution.detached-namespace` fails on its own premise, reproduced at the base commit
    9218e500 with and without this task's change.
- **Left `scenario.execution.detached-namespace` and `runner.md`'s sandboxed-call sentence as they are.**
  Both state the mechanism generically, without naming a task session, so they stay true wherever the
  sandbox is on; changing the scenario would change what its test declares it verifies, beyond this goal.

## Results that were not ok (task session, 2026-10-01)

- `tests/concorde/workflows/test_workflows.py::SandboxTests::test_a_run_detached_inside_a_pid_namespace_dies_with_it`
  fails with `AssertionError: 'running' != 'finished'`. Pre-existing: it reproduces at the base commit
  9218e500 with this task's change reverted, and this task changes only Markdown prose. Inside the
  test's own `bwrap --unshare-pid` namespace the step finishes at once, `failed` with
  "The configured checks could not be run (check_sandbox_unavailable)", because the read-only check
  boundary is itself a bubblewrap sandbox and cannot be established there. Recorded as
  `I-fc326b9c1f095e6bac9723e4bcf9de65` against module.workflows; it is not in module.execution's
  configured check, which runs `tests/concorde/execution`.
- Reported `I-15b1c594bcb156bab9d5e762a96cd35a` (module.issues, preferred-fix): `issue_list` takes no
  filter and returns all 169 Issues (59,861 bytes), which the MCP client refused as too large, so the
  read the guidance asks for before reporting could not be done in one call; worked around by grepping
  the spilled file.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T12:19:05Z

Delivered `execution-detached-example` at `da991cdb` ("concorde: deliver execution-detached-example", parent `9818c398`). Delivery status `ok`, readiness `ready`: 1 changed path, 16 checks passed, 0 warnings, and the workspace changed no code. `spec-validation` ends with 0 errors and 0 warnings.

**The change** — one file, `specs/concorde/execution/module.md`, prose only, no SHALL touched, so no promise changed. The PID-namespace statement and the mechanism before it are untouched. The passage's closing sentences no longer offer a task session's background Bash as a way to keep a *sandboxed* call alive. They now say that which callers are sandboxed is not Execution's to say, and give the cases: a worker's Bash on the Claude Code backend (`req.workers.bash-sandbox`), a main agent's own session, which may be, and a task session's calls, which are not (`req.task-session.no-sandbox`). A task session stays in the passage, but as an example of starting its runs in background Bash rather than detached, for the reason Issue I-07e549dd itself gives: Claude Code may end the processes of a call that returned, not a namespace ending.

**Decisions I took on your behalf** (both in the decision log):

- Naming the main agent made the document use that term for the first time, which `CHK.term.unlinked` reported as a warning; I linked its first use to the glossary. That is why validation now reports no warnings.
- I left `scenario.execution.detached-namespace` and `runner.md`'s "such as that of a sandboxed Bash call" as they are. Both state the mechanism generically without naming a task session, so they stay true wherever the sandbox is on, and changing the scenario would change what its test declares it verifies, beyond this goal.

**Issues.** The task record already resolved `I-07e549dde12655e095abcabcfb422fee`, so your merge closes it; I closed nothing. Four problems I found and did not fix, each owned by a Module outside this task:

- `I-cbde7d00eba65a7bbdacf14d8b458844` — module.workers, preferred-fix. Workers' Proxy section and `scenario.workers.session-proxy` still justify passing the proxy variables and stripping loopback by a task session's sandbox and its loopback-only network namespace, and the code and test comments repeat it. The behaviour still has a purpose for any enclosing loopback proxy, so the better fix is to restate the reason rather than drop the rule. This is the same staleness as the Issue I just fixed, one Module over.
- `I-c650cd574f6055fcb645ee1fc885f830` — module.harness, obvious-fix. "Why the Harness is separate" says "the same write-hook table and sandbox settings serve a worker and a task session", which the same document denies a few sections earlier with "the settings carry no sandbox".
- `I-fc326b9c1f095e6bac9723e4bcf9de65` — module.workflows, preferred-fix. The test that verifies `scenario.execution.detached-namespace` fails on its own premise, `'running' != 'finished'`. It makes the step slow with a configured check and then runs it inside its own `bwrap --unshare-pid` namespace, where the read-only check boundary, itself a bubblewrap sandbox, cannot be established: the step finishes at once, `failed` with `check_sandbox_unavailable`, instead of still running. It is pre-existing — it reproduces at the base commit `9218e500` with my change reverted, and my change is Markdown prose — and it is not in module.execution's configured check, so it blocked nothing here. But the scenario that justifies running every workflow step through the project MCP server is currently unverified.
- `I-15b1c594bcb156bab9d5e762a96cd35a` — module.issues, preferred-fix; the environment note below.

**Environment, as you asked, being the first task session without the OS sandbox:**

- Preparation worked exactly as CLAUDE.md lists, with no workaround: `init-references.py`, `uv sync --locked --group dev`, `npm --prefix docsite ci` and `build`, all exit 0. Bash reached everything the work needed — bubblewrap, pytest, git, npm — and the one sanctioned write outside the worktree, appending to the decision log, worked from the shell. No masked path, no proxy and no per-call namespace got in the way, and nothing in the guidance misdescribed the session.
- One thing did not work as the guidance says, and I filed it. The Issues section tells a session to read `issue_list` and `issue_show` first so it appends instead of duplicating. `issue_list` takes no filter and returned all 169 Issues (157 open, 59,861 bytes); the MCP client refused the result as too large and spilled it to a file. I worked around it by grepping that file for a candidate duplicate. Every session from here on meets this, so it is `I-15b1c594bcb156bab9d5e762a96cd35a` against module.issues.
- Expected, not a defect: in a fresh worktree `.claude/skills/concorde` and `concorde-development` are symlinks into `generated/skills/`, which does not exist until `build`, so the Skill tool did not offer them at session start and they appeared after it — which is what CLAUDE.md says to expect.

Nothing is open that needs a decision from you.

## Closed: merged, 2026-10-01T12:19:57Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit da991cdbe3658223fb5a7d6bc4fc24c7b7c7dc48 into main and closed it as merged. Nobody answers a report after that.
