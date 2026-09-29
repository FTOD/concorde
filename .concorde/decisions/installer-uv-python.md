# Decision log: installer-uv-python

Goal: Make uv a required installer dependency and let uv own Concorde's Python: the installer creates .concorde/framework/python with uv (e.g. uv venv --python <minimum version from concorde.json/pyproject>, letting uv provide a managed CPython when none fits) instead of '<user python> -m venv', removes the --python option and the python_too_old/python_unusable checks that depended on the user's interpreter, and checks every cheap precondition (uv present, npm present when the pi runtime is installed) before the first write so that only environment creation and dependency or npm installation can fail after writing (resolves distribution F3); update Distribution's Spec, the install/update docs and every caller of --python (install-concorde.py, concorde update, develop installs, e2e tooling), with tests

## Decisions (task session, 2026-09-29)

- **Source of the Python requirement.** Options: hard-coded `MINIMUM_PYTHON`, `pyproject.toml`'s
  `requires-python`, or `concorde.json`'s `runtime.python`. Chose `runtime.python` of
  `concorde.json` (the package descriptor the installer already reads, and was already `>=3.11`
  but unused), passed verbatim as `uv venv --python ">=3.11"` so uv reuses a fitting installed
  interpreter and downloads a managed CPython only when none fits. A missing value refuses with
  `invalid_descriptor` before any write. Also corrected the descriptor's stale `runtime.venv`
  (`.concorde/.venv`) to the real `.concorde/framework/python`.
- **uv invocation.** `uv venv --no-project --python <requirement> <target>` with cwd the project:
  `--no-project` keeps the project's own `requires-python` out of the choice. Did not pass
  `--no-config`, so the developer's user-level uv settings (mirrors, download policy) still apply.
- **What `run` fakes.** Environment creation always runs real `uv venv` (tests exercise it for
  real, including a `python_env_failed` case via `UV_PYTHON_DOWNLOADS=never` and an unsatisfiable
  requirement); `run` still replaces only `npm ci` and the dependency-installation uv calls.
- **Receipt `python`.** Now `{environment, requirement, base, version}`: `base` is the real path of
  the interpreter uv chose. `concorde update` no longer keeps a previous base; it recreates the
  environment with uv for the new checkout's requirement.
- **Cheap preconditions before the first write.** Order: stale build, guidance, develop source,
  running Concorde, descriptor requirement, settings, then `uv` on PATH (every install, also with
  `--without-dependencies`), then `plan_pi_runtime` (new in `tools.py`: lockfile readable, npm
  needed only when the same lock's runtime is not already in place), then the d2 download.
  Errors say "nothing was written"; new requirements `installer-programs-first` and
  `uv-owns-python`.
- **Installer's own interpreter.** The build and `scripts/install-concorde.py` themselves still run
  on the developer's `python3` and need 3.11+ (they import `datetime.UTC` etc.); making them re-exec
  under uv is outside this goal, so the docs now say "Python 3.11 or later, to build Concorde and
  run its installer" plus uv as a requirement.
- **e2e tooling.** `scripts/e2e/e2e.py`'s `--python` is `concorde init --python` (the project's
  interpreter for checks), not the installer's; neither e2e.py nor dogfood.py passed `--python` to
  the installer, so nothing there changed.

## Non-ok results

- Full suite (`.venv/bin/python -m pytest`): 641 passed, 1 failed:
  `tests/concorde/e2e/test_cases.py::CaseTests::test_grading_runs_the_case_tests_on_a_throwaway_tree`
  (`{'test_calc.py::test_add': 'FAILED'} != {'test_calc.py::test_add': 'not run'}`). Cause: this
  session's environment sets `FORCE_COLOR=3`, so the graded pytest prints ANSI-colored summary
  lines that `cases.grade` does not parse. With `FORCE_COLOR` unset the file passes (5 passed).
  Unrelated to this task and outside module.distribution (it belongs to module.swe-bench-cases);
  left unchanged and reported as open.
- `ruff check` on `tests/concorde/distribution/` reports 10 pre-existing PLW1510 findings
  (`subprocess.run` without `check`) on lines this task did not introduce; left unchanged.

## 2026-09-29 — main agent: merge conflict with installer-ships-docsite

- Non-ok: `task merge` refused with `merge_conflict` in install.py and Distribution's module.md and
  requirements.md, because installer-ships-docsite had merged first. Resolved in this worktree by
  merging main: install.py keeps both (the docsite template is copied with the runtime; uv creates
  the environment); requirements.md keeps both sets of new requirements; module.md combines the
  docsite template sentence with the uv-owned environment and lists the docsite template among the
  pre-write checks.
- Verification after the merge: spec-validation 0/0, build --check clean, registry --write done,
  full pytest with FORCE_COLOR unset 648 passed (the grading test fails only when FORCE_COLOR is
  set, as the task session found — a swe-bench-cases defect, handled separately).

## Closed: merged, 2026-09-28T16:43:51Z
