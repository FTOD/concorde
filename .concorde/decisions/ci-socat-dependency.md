# Decision log: ci-socat-dependency

Goal: Fix GitHub Actions Validate source checkout failure in run 36403419564: pi task-session tests fail because socat is absent from PATH. Make the minimal CI system dependency correction (install socat alongside bubblewrap), verify required Linux dependencies, and complete validation and delivery. Keep the change small; do not weaken sandbox checks or skip tests. Read all required Specs and development instructions. Run the full Python suite once on final inputs plus the remaining CI docsite checks where feasible. Do not push or merge from the task session.

## Main agent diagnosis and scope

- GitHub Actions run 36403419564 fails in the full Python suite: 7 failed, 629 passed, 4 skipped. The complete failed-step log identifies `RuntimeError: socat is not on PATH; the sandbox of the session's commands needs it on Linux`.
- The CI configuration installs bubblewrap but omits socat. Treat this as a small environment dependency correction authorized by the developer; bind the task to module.concorde, which owns the CI file. Preserve sandbox requirements and tests.
- Initialize reference submodules before starting the task session, per AGENTS.md. The initializer succeeded for all seven references.
- Use the Concorde CLI task session because concorde_task_session is not available in this main session.

## Task session implementation and preparation

- Add only `socat` beside `bubblewrap` in the CI apt install command and pluralize the step label. This supplies the missing prerequisite without changing sandbox enforcement, tests, or Specs; no additional regression test is warranted for this dependency-list correction.
- Confirmed local `bwrap`, `socat`, `rg`, and `d2` are available and all seven reference submodules are checked out at their pinned revisions. The vendored sandbox-runtime README lists bubblewrap, socat and ripgrep as Linux dependencies; the task-session dependency check specifically requires bwrap and socat. Preserve the existing CI namespace setup.
- Preparation succeeded with `uv sync --locked --group dev` and `npm --prefix docsite ci`. uv used copies after a harmless cross-filesystem hardlink warning. npm reported existing dependency deprecations and 31 audit vulnerabilities (1 low, 25 moderate, 5 high); do not change locked dependencies in this CI-only correction. Report these notices to the main agent.
- The automatic YAML linter reported nine existing line-length findings on unchanged lines 32, 37, 38, 42, 49, 56, 57, 83 and 89. Defer those style findings to avoid unrelated formatting churn; the two changed lines fit within 80 columns. Sandbox-created protected placeholders shown by git status are not task changes and will never be staged.
- Run the full Python suite once with reason=regression and scope=full on the final CI change, then the CI docsite typecheck, tests and validation, followed by required build/spec checks and task validation/delivery. These are self-validation, not independent review.

- The initial full-suite invocation exited 4 before collection: `--reason=regression` is not accepted (choices: manual, local-edit, coherent-change, stable-final, changed-input, failure, independent, bootstrap). Use the supported `--reason=stable-final` for this final-input self-validation; no tests ran in the rejected invocation.

## Verification

- `build` and `build --check` succeeded; `spec-validation` succeeded with 0 errors, 0 warnings and 0 infos.
- The single executed full Python suite on final inputs, `PYTHONPATH=src .venv/bin/python -m pytest --reason=stable-final --scope=full`, passed: 636 passed, 4 skipped in 19.07s. No skip configuration or tests were changed.
- All remaining CI docsite checks passed: `python3 scripts/development/check-docsite-types.py`, `npm test --prefix docsite` (21 files, 257 tests), and `npm --prefix docsite run validate` (32 Modules, 119 documents). The temporary-copy typecheck repeated the existing npm deprecation notices.
- Confirmed installed versions: bubblewrap 0.9.0, socat 1.8.0.0, ripgrep 14.1.0 and d2 v0.9.0. Local Node is 22.23.2 (CI requests Node 20), satisfying the docsite requirement of >=20.
- A probe for `docsite/node_modules/.bin/prettier` exited 1 because the docsite does not install Prettier. Use pinned `npm exec --yes --package=prettier@3.8.1 -- prettier --write` for the changed YAML only. Both formatting passes reported unchanged, so full-suite inputs stayed final. `git diff --check` also passed.

## Delivery

- Inspected and committed the two-line CI correction as `bcd2468b02b18c79a50ef5d64506b5a9c5de8652` (`fix(ci): install socat for sandboxed task-session tests`). Only the named CI path was staged.
- `task-validation` run `r-20260928T093648-task_validation-1ea9577e` returned ok/ready with no blockers or warnings and passing `check.concorde.tests`.
- `delivery` run `r-20260928T093714-delivery-fcfad68b` returned ok, repeated readiness and the configured check successfully, and created delivery commit `38ec10c75790281b7f96da25a14c397e973727f6` with `.concorde/evidence/ci-socat-dependency/1.json`.
- Final branch inspection shows only the CI correction and Delivery evidence relative to the task base. Tracked sources are clean; untracked protected sandbox placeholders are transient and were not staged. No push or merge was performed. Main agent owns checked merge and subsequent hosted CI confirmation.

## Main agent delivery review

- Inspected the session report and complete branch diff: only the two-line CI dependency correction and required Delivery evidence changed. Full suite passed 636 tests with 4 existing skips; docsite typecheck, 257 tests, and publication validation passed. No escalations remain.
- Accept the minimal correction and perform the required checked merge. Existing npm dependency audit notices are outside this CI dependency correction.
- After the checked merge, push the correction to origin/main to complete the requested GitHub Actions repair and inspect the hosted validation result.

## Closed: merged, 2026-09-28T09:38:46Z

## Hosted verification

- Checked merge succeeded with both build and spec-validation and no warnings; pushed main at 38ec10c75790281b7f96da25a14c397e973727f6.
- Hosted run 36404852649 attempt 1 confirms all seven original pi task-session failures are resolved, but fails once in DevelopInstallTests.test_a_normal_install_carries_no_develop_guidance during TemporaryDirectory cleanup: OSError errno 39, Directory not empty: .git, under /tmp/tmptr_192vl/package. Result: 1 failed, 635 passed, 4 skipped.
- The new failure is in temporary Git repository cleanup rather than the corrected sandbox dependency. The fixture synchronously creates and commits a package repository. A background Git maintenance race is a hypothesis, not established by the available log. Rerun the failed job once on unchanged inputs to distinguish a transient cleanup failure before expanding the correction.

- Hosted run 36404852649 attempt 2 completed success on the same commit, including the full Python suite, docsite typecheck, docsite tests and docsite validation. The isolated temporary .git cleanup failure did not recur; no change was made for that unconfirmed race. Deploy project docsite run 36404852543 also succeeded. Primary main is clean and synchronized with origin/main.
