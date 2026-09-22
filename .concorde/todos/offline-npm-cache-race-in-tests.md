# Offline npm installs in tests race on a shared, possibly empty npm cache

Status: being fixed inside `change.b0b2efdc-1909-42cd-8bba-0fd533eb358d` (pytest migration)
at the user's request before that change merges. Delete this note once the merged fix is
verified; keep it if the fix is deferred or only partially lands.

## Observation (independent testers bf712e4d and 9229121b, 2026-09-22)

Under the framework's own tester harness (`src/concorde/harness/check_executor.py:511` points
`npm_config_cache` at an empty per-command scratch directory) the end-to-end tests that
provision a managed runtime fail nondeterministically with

    npm error code ENOTCACHED ... typebox-1.1.38.tgz ... cache mode is 'only-if-cached'

- The product installer deliberately runs `npm ci` offline
  (`src/concorde/distribution/managed_runtime.py:204 _offline_environment`,
  `NPM_CONFIG_OFFLINE=true`); tests inherit that through
  `tests/concorde/support/managed_runtime.py:49`.
- On a developer machine the ambient `~/.npm` cache already holds typebox because the
  README bootstrap runs `npm ci --prefix pi`; the failure never shows there.
- Under the harness the cache is only populated when
  `tests/concorde/harness/test_tester_tmp.py:222` installs with `NPM_CONFIG_OFFLINE=false`
  into the shared scratch cache. With `-n 16` every offline `npm ci` scheduled before that
  moment fails; the count varied from 10 (cycle 1) to 4 (cycle 2). Affected units:
  `ConsumerInstallEndToEndAcceptance` (setUpClass), `InstalledWorkerRuntimeTests` x2,
  `DistributionTests::test_installed_framework_runs_complete_real_graph_and_checks_for_pi`,
  `NativeLocalInstallationTests::test_source_and_installed_provider_supply_independent_git_worktree_installs`.

## Agreed behavior

Tests that need the locked Pi extension dependencies must obtain them deterministically,
without depending on which xdist worker happens to run first and without an online install
racing to fill a shared cache. Preferred direction: a test-support step that seeds the npm cache
in use from local, already-vendored material (`pi/node_modules`, which bootstrap guarantees, or
the locked tarball) before any offline `npm ci`, guarded by a file lock so parallel workers
cooperate; when neither the cache nor local material holds the package, fail or skip with an
explicit reason naming the missing input, never silently. No product runtime behavior change
(the offline policy of the installer stays); do not alter the tester harness's scratch-cache
boundary.

## Non-goals

- Making the installer download online.
- Changing `check_executor.py`'s scratch npm cache for testers.

## References

- Tester reports: `/tmp/pi-subagents-uid-1000/async-subagent-runs/bf712e4d-e85c-4de6-a8d7-b48d742e79d4`,
  `/tmp/pi-subagents-uid-1000/async-subagent-runs/9229121b-fcf4-48a2-be8e-1c63ca64f549`
- Status record: `.concorde/status/change.b0b2efdc-1909-42cd-8bba-0fd533eb358d.json`
