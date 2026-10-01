# Decision log: detached-namespace-test

Goal: Make the Workflows test for scenario.execution.detached-namespace verify what it exists to verify: a runner detached inside a PID namespace that ends is killed with it and the step is reported step_lost, instead of failing early because the read-only check boundary cannot be set up inside the test's own bubblewrap namespace.

## Brief (main agent, 2026-10-01)

The developer asked the main agent to look at the Issue store and fix the more important Issues;
this one leaves module.workflows' configured check failing for every task, for a reason unrelated
to the task.

Issue this task resolves: I-fc326b9c1f095e6bac9723e4bcf9de65, `preferred-fix`. The test
`SandboxTests::test_a_run_detached_inside_a_pid_namespace_dies_with_it` in
tests/concorde/workflows/test_workflows.py makes its step slow through a slow configured check, but
inside the test's own bubblewrap PID namespace the read-only check boundary cannot be set up, so
the run ends at once with `check_sandbox_unavailable` and the test never reaches the namespace end.
Fix the test so it verifies scenario.execution.detached-namespace (a runner detached inside a PID
namespace that ends dies with it; the step is reported `step_lost` over `host_ended`): make the
step slow by a means that does not need a nested sandbox, or otherwise keep the run alive until the
namespace ends. Report the fix you chose. If you find the behaviour itself, not the test, is wrong,
or that the fix needs a production-code or Spec change, escalate with what you found before
changing it.

First reproduce the failure at the task's base. Run the Workflows tests and the module's
configured checks before delivery.

## Task session (2026-10-01)

- Reproduced at the base: the test's first call returned `finished`/`failed` with
  `check_sandbox_unavailable` instead of `running`.
- Root cause: the test's PID namespace bound `/` read-write. Inside bubblewrap's user namespace
  the system `/usr/bin/bwrap` shows the unmapped (overflow) owner, and the check executor
  (`src/concorde/harness/check_executor.py`, `_bubblewrap`) deliberately trusts that owner only
  on a read-only mount, so it refused with "a root-owned system bubblewrap installation is
  required". The production behaviour is right; only the test's namespace was unlike Claude
  Code's Bash sandbox it stands for.
- Decision (fix chosen): make the test's namespace like that sandbox, with the system read-only
  (`--ro-bind / /`) and only `tempfile.gettempdir()`, which holds the test project and the check
  scratch, writable. The run's real `task-validation` with its 30 s configured check now starts
  inside the namespace, so the test keeps the scenario's GIVEN as written and reaches the
  namespace end. Rejected alternatives: queueing the run behind a workspace lock the test holds
  (the step itself waits for the workspace lock before starting the run, so the run would never
  start), and a stand-in slow worker (changes what is run away from the scenario's
  `task-validation`). Test-only change; no Spec or production code change.
- Verification: the test passed 3 times in a row; Workflows tests 41/41 passed directly and 41/41
  inside the read-only check boundary (run through `execute_check`, none skipped); `build --check`
  and `spec-validation` succeeded; task-validation r-20261001T123950-task_validation-d3ac228e is
  ready, with 13 configured checks passed.
- Observation: no configured check runs `tests/concorde/workflows` (there is no
  `.concorde/checks/module.workflows.json`), so Issue I-fc326b9c1f095e6bac9723e4bcf9de65's "module.workflows'
  configured check fails" could not be reproduced as a check failure. Adding a checks file is
  beyond this task's goal, so it is recorded as the `suggestion` Issue
  I-3ea49a714b575c97b3eac86e6b678bd0 rather than done here.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T12:44:22Z

detached-namespace-test delivered: delivery commit 2e10a34f7d4718e33fda7060caa3ca47fb765bc4 on concorde/detached-namespace-test (run r-20261001T124234-delivery-b32c254b, ok). The fix itself is commit 47d5102a and changes only tests/concorde/workflows/test_workflows.py.

Resolves Issue I-fc326b9c1f095e6bac9723e4bcf9de65 (added with task resolve).

Cause (reproduced at the base: the first call returned finished/failed with check_sandbox_unavailable): the test's PID namespace bound / read-write. Inside bubblewrap's user namespace, /usr/bin/bwrap shows the unmapped overflow owner. The check executor (check_executor._bubblewrap) deliberately trusts that owner only on a read-only mount, so it refused with "a root-owned system bubblewrap installation is required". The production behaviour is correct; only the test's namespace differed from the Claude Code Bash sandbox it stands for.

Fix chosen (my decision, test-only, no Spec or production change): the test's namespace now makes the system read-only (--ro-bind / /) and keeps only tempfile.gettempdir() writable, which holds the project and the check scratch, as Claude Code's sandbox does. The real task-validation with its 30 s check now starts inside the namespace, so the test keeps the scenario's GIVEN as written, reaches the namespace end and asserts step_lost over host_ended. Two alternatives were rejected. Queueing the run behind a workspace lock held by the test doesn't work, because workflow step itself waits for the workspace lock before starting the run. A slow stand-in worker would move what runs away from the scenario's task-validation.

Verification: the test passed 3 times in a row. Workflows tests passed 41/41 directly, and 41/41 inside the read-only check boundary with none skipped. build --check and spec-validation succeeded. task-validation was ready with 13 configured checks passed.

Still open: no configured check runs tests/concorde/workflows (there is no .concorde/checks/module.workflows.json). The Issue's statement that module.workflows' configured check fails therefore does not hold; the test only failed when run by hand. I recorded this as the suggestion Issue I-3ea49a714b575c97b3eac86e6b678bd0 instead of adding a checks file, which is beyond this task's goal. Nothing needs a decision.

## Closed: merged, 2026-10-01T12:44:21Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 2e10a34f7d4718e33fda7060caa3ca47fb765bc4 into main and closed it as merged. Nobody answers a report after that.
