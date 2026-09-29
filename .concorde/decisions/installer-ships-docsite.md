# Decision log: installer-ships-docsite

Goal: Make the installer place the docsite template in .concorde/framework/docsite by the Views template inventory rule (views.docsite_template.template_files, plus scaffold/), so concorde docsite --propose works in a normally installed project (today it fails with CONCORDE-DOCSITE-002: template root missing, reproduced in /tmp/concorde-install-check); declare the rule in Distribution's Spec, align Views' template-inventory wording, and add a test that an install carries the template and docsite --propose succeeds

## 2026-09-29 00:22 +0800 — second agent stopped: worktree already being worked on

A subagent the main agent launched for this task prepared the worktree (`uv sync --locked --group
dev`, `npm --prefix docsite ci`, `build`: all ok) and then found another Claude Code session
actively changing the same worktree (uncommitted edits to install.py, Distribution and Views Specs
and test_distribution.py written 00:20–00:21, and a live `scripts/concorde.py spec-validation`
process, pid 3297665, with this worktree as cwd). Options: (a) continue and edit the same files,
(b) stop without touching sources and report to the main agent. Chose (b): two writers in one task
worktree would overwrite each other's edits and commits. At that moment the other session's
`test_an_installed_concorde_proposes_the_docsite_scaffold` failed (non-ok): it asserts envelope
status `success`, but `docsite --propose` returns status `proposal`, so the test's expectation, not
the installer, is wrong; also it reads `envelope["result"]["files"]` whereas the files are under
`result.proposal.files`.

## 2026-09-29 — main agent: duplicate worker, and a task-session start that looked refused

- Non-ok (main agent's mistake): `concorde task session <task> --main ...` printed an error chain
  whose last lines asked for workspace trust ("have the developer run claude once in the task
  worktree and accept the trust prompt"); reading only the tail, I took the start as refused and
  launched a subagent in this worktree as well. The task session had in fact started (a Claude Code
  session in this worktree since 00:18; the task record's `sessions` stays `[]`). The subagent saw
  the session's edits, changed no source and stopped. To examine: why the command reports an
  error while the session runs, and why the start is not recorded in the task record.
- The subagent's review points were sent to the task session to address before delivery.

## 2026-09-29 — task session: decisions and non-ok results (commit f1352563)

- **How the installer selects the template.** Options: (a) copy `docsite/` with its own ignore
  patterns, (b) call Views' `template_files` (plus `verify_package_root`) and write exactly those
  bytes under `.concorde/framework/docsite/`. Chose (b): the goal and `req.views.template-inventory`
  require one shared rule, and (a) would repeat it.
- **When an unsafe template is refused.** Chose to compute the inventory right after the build
  freshness check, before any write, and refuse with `invalid_docsite_template`, reason `input`
  (only a different Concorde checkout corrects it). This keeps Distribution's rule that everything
  that can refuse an install is decided before the first write. Declared as the new requirement
  `req.distribution.installer-docsite-template-first`, next to `…-installer-docsite-template`,
  because a requirement may hold only one SHALL.
- **New scenario** `scenario.distribution.install-docsite-template`, verified by two new tests in
  `tests/concorde/distribution/test_distribution.py`. The shared test helper `package_copy` now
  also copies the docsite template, taken from Views' inventory.
- **Main agent's review, point 1** (test expected status `success` and `result.files`): the
  test's expectations were wrong. Fixed to status `proposal` and `result.proposal.files`.
- **Point 2:** Distribution's `uses` of `module.views` now relies on `req.views.template-inventory`
  and `contract.views.scaffold-proposal` (the contract that defines the template inventory), with
  links from `#uses-views`. Ran `registry --write`.
- **Point 3:** reworded `req.views.template-inventory` to name Distribution's installer and the
  one rule Views defines. Added a rationale paragraph saying where each side uses the files.
- **Point 4 (the receipt's `files`):** no change. The receipt's `files` lists no file under
  `.concorde/framework/` (not `src/`, `scripts/` or `generated/`); the whole framework copy is
  recorded by the `framework` key, and the docsite template is part of that copy. I confirmed this
  in the real install below. Listing only the docsite files would break that convention.
- **Point 5, end-to-end reproduction** in a fresh project `/tmp/claude-1000/docsite-install-check`
  (`$TMPDIR`: the sandbox allows no other place under /tmp). Steps: `git init`, then a plain
  `python3 scripts/install-concorde.py` from this worktree (exit 0, real d2, pi runtime and
  dependencies). `.concorde/framework/docsite/` then held 53 files, `scaffold/deploy-docsite.yml`
  among them. `concorde init --propose/--apply` succeeded. `concorde docsite --propose
  --github-pages` returned status `proposal` with 54 files, no conflicts and only the info finding
  CONCORDE-DOCSITE-009 (no GitHub origin). `concorde docsite --apply` succeeded and wrote
  `docsite/` and `.github/workflows/deploy-docsite.yml`, and `spec-validation` returned success.
  My first `--apply` attempt returned `invalid` (CONCORDE-DOCSITE-004, "expected a canonical
  project-relative POSIX path"). That was my invocation, not a defect: I passed a proposal path
  outside the project, as `init --apply` expects, whereas `docsite --apply` takes a
  project-relative path. The retry with a project-relative path succeeded.
- **Non-ok, outside this task:** the full suite has one failure,
  `tests/concorde/e2e/test_cases.py::CaseTests::test_grading_runs_the_case_tests_on_a_throwaway_tree`
  (`{'test_calc.py::test_add': 'FAILED'} != {... 'not run'}`). It fails identically on the
  untouched base commit fee38b9e (checked from a `git archive` copy). It belongs to
  module.swe-bench-cases, not to this task's Modules, so I left it alone.
- **Untracked character devices** (`.bashrc`, `.zshrc`, `.gitconfig`, `.claude/`, `.mcp.json`, …)
  appear in the worktree. They are the sandbox's bind mounts, not work, so I staged explicit paths
  only.

## Closed: merged, 2026-09-28T16:34:12Z
