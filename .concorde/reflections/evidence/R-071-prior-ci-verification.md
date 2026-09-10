# R-071: prior CI maintenance verification

Historical pre-merge report; temporary log paths identify original artifacts and are not required to read the captured summary. New merge verification is recorded separately.

CI maintenance verification, 2026-09-10
Workspace: /tmp/concorde-worktree-fpcum8ri/project
Branch: concorde/499465ba-0619-431f-9220-063b7dd5d8da
Base/HEAD before commit: 2c398af9af2510768d945c7cde7da5a57ff8fcfd
Change ID: change.499465ba-0619-431f-9220-063b7dd5d8da

Final changed files (before review/commit):
.github/workflows/validate-source-checkout.yml SHA256 c682b3d40fd15c379162e69616a315b5c82bf965449e4b48f51e86d00d5ec66a
tests/concorde/harness/test_studio_server.py SHA256 5d49d1f0ac2d34615dd8ff1275b3b6722e69a4c2ce72f826f29fa52242d92a8f
Preserved pre-existing AGENTS.md and CLAUDE.md changes: 19 added lines each; excluded from commit. Their combined diff is /tmp/concorde-ci-preserved-handoff.diff, SHA256 6c5695e604410647200e4efbb9a2dc6c8a926568f44531ea2c242c38443b21ef.

Environment: Ubuntu 24.04.4; system Python 3.12.3; uv-managed Python 3.11.15 in .venv; bubblewrap 0.9.0 at /usr/bin/bwrap (root-owned 4755); AppArmor userns restriction was already 0, current profile unconfined. Initial docsite checks used Node 22.23.2; final verification used temporary Node 20.20.2 to match CI's major version. No system sysctl or bwrap permission was modified locally.

SUCCESSFUL CHECKS:
1. uv sync --locked --group dev --python 3.11, exit 0: /tmp/concorde-ci-uv-dev.log.
2. python3 scripts/concorde.py build, exit 0, 37 outputs: /tmp/concorde-ci-build.log.
3. python3 scripts/concorde.py build --check, exit 0, no differences: /tmp/concorde-ci-build-check.log. After final test edit also .venv/bin/python scripts/concorde.py build --check, exit 0: /tmp/concorde-ci-final-build-check.log.
4. python3 scripts/concorde.py validate, exit 0: /tmp/concorde-ci-validate.log. Final candidate checked with .venv/bin/python scripts/concorde.py validate, exit 0: /tmp/concorde-ci-final-validate.log. Both report 0 errors, 40 pre-existing scenario-verification warnings; no semantic completeness claim.
5. PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py', exit 0: Ran 650 tests in 417.739s, OK (skipped=8). /tmp/concorde-ci-unittest.log. Studio opt-in server tests skipped here and separately executed below; final Studio-only assertion edit is covered by the dedicated enabled suite.
6. Separate CI-like Studio environment: UV_PROJECT_ENVIRONMENT=/tmp/concorde-ci-studio-venv uv sync --locked --group studio --python 3.11, exit 0: /tmp/concorde-ci-uv-studio.log. PYTHONPATH=src CONCORDE_TEST_STUDIO=1 /tmp/concorde-ci-studio-venv/bin/python -m unittest tests.concorde.harness.test_studio tests.concorde.harness.test_studio_client tests.concorde.harness.test_studio_server, exit 0: Ran 27 tests in 32.539s, OK, no skips. /tmp/concorde-ci-studio-fixed.log. Original newly exposed stale fixture assertion failure preserved at /tmp/concorde-ci-studio.log.
7. PYTHONPATH=src setpriv --no-new-privs .venv/bin/python -m unittest tests.concorde.harness.test_check_executor, exit 0: 11 tests in 2.828s, OK. /tmp/concorde-ci-sandbox-unprivileged.log. This real-kernel check prevents the system bwrap setuid bit from granting privileges and confirms no dependency on it.
8. npm ci --prefix docsite, exit 0: /tmp/concorde-ci-npm-install.log. Dependency deprecation/audit output retained without unrelated package changes.
9. With Node 20.20.2 prepended to PATH: python3 scripts/development/check-docsite-types.py, exit 0: /tmp/concorde-ci-node20-typecheck.log. Temporary copy from fresh sources; generates sidebar from registry and invokes tsc --noEmit. Original direct npm typecheck failed for missing generated sidebar: /tmp/concorde-ci-docsite-typecheck.log; corrected helper also passed under Node 22: /tmp/concorde-ci-docsite-typecheck-fixed.log.
10. With Node 20.20.2: npm test --prefix docsite, exit 0: 12 test files, 86 tests passed, /tmp/concorde-ci-node20-test.log. Includes real source/consumer publication builds. Initial Node 22 pass: /tmp/concorde-ci-docsite-test.log.
11. With Node 20.20.2: npm --prefix docsite run validate, exit 0: 7 targets, 35 document memberships. /tmp/concorde-ci-node20-validate.log. Initial Node 22 pass: /tmp/concorde-ci-docsite-validate.log.
12. YAML parse and bash -n for all 14 workflow run steps passed: /tmp/concorde-ci-workflow-check.log. git diff --check passed.

BOUNDARIES:
No push, remote CI run, deliver, merge, branch change, other-worktree development, worktree deletion or lifecycle metadata edit. System apt installation/sysctl setup in the YAML has not been run on a GitHub-hosted runner; local preinstalled bwrap and real sandbox tests supply local evidence only. Ubuntu documents the user namespace restrictions at https://discourse.ubuntu.com/t/understanding-apparmor-user-namespace-restriction/58007 . Original runner was Ubuntu 24.04.5 image 20260907.300.1, per /tmp/concorde-ci-build-job-full.log.
Prior Framework blocks remain true: dev-loop invocation fdda40cc-8870-4d8f-9b7e-04194249aad2 execution_failed: 'target_id'; main invocation 820dff66-b38e-4357-9939-0ef7a8943ed1 spec_incomplete (no Module binding for workflow). No lifecycle ready claim or Spec topology changes.

REVIEW AND COMMIT:
Fresh independent read-only review completed successfully, thread 01a08c2a-897e-7d21-82fe-e306226af545. No diff-introduced defect or blocker found. Result: /tmp/concorde-ci-review-result.txt; event log: /tmp/concorde-ci-review-events.jsonl. Review confirmed exact candidate SHA256 values above and preserved handoff diff. Its limitations include unexecuted remote apt/sysctl setup and the existing typecheck helper's generated sidebar wrapper differing from publication; real publication tests passed separately. Older failed run had 68 failures, newer run had 69 failures; causes were the same.
Committed only the two reviewed repair files with message: fix(ci): restore source checkout and Studio validation. Commit short ID: 22251f49. Branch and worktree retained. No push or remote CI execution. AGENTS.md and CLAUDE.md remain as the only tracked uncommitted modifications.
