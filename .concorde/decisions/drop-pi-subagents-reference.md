# Decision log: drop-pi-subagents-reference

Goal: Remove leftovers of pi main-session support: the unused reference submodule references/pi-subagents (.gitmodules, the gitlink, specs/concorde/development.md and any reference tooling that lists it) and directories in docsite/tests/repository/run-checks.py that no longer exist, such as pi

## Brief (main agent, 2026-09-30)

The developer approved this cleanup ("清理") after drop-pi-main-session, drop-pi-workflows and
project-mcp-server merged; the drop-pi-workflows session reported both leftovers.

- Remove the reference submodule `references/pi-subagents`: nothing uses it since pi main
  sessions and the pi workflow rendering are gone. Remove it from `.gitmodules` and the index
  (`git rm`), from `specs/concorde/development.md` (line ~34 lists it) and from any reference
  tooling, check or Spec that still names it. Keep the other pi references that worker-side pi
  still needs (pi, pi-packages, sandbox-runtime, ...); escalate if you are unsure whether one is
  still needed.
- `docsite/tests/repository/run-checks.py`: remove entries of `DIRECTORIES` (and `FILES`) that no
  longer exist in the repository, such as `pi` (check `agents`, `operations`, `reference` too),
  keeping the check's purpose intact.
- The shared `.git/config` is read-only for you: its `submodule.references/pi-subagents` entry and
  `.git/modules/references/pi-subagents` are removed by the main agent after the merge. Do not try
  to write them.
- Small task: verify with build --check, spec-validation and the relevant tests, then
  task-validation and delivery.

## Task session (2026-09-30)

- Removed `references/pi-subagents` from the index (`git rm --cached`), its `.gitmodules` section
  (edited in place: `git config -f .gitmodules --remove-section` failed with "Device or resource
  busy" because the sandbox mounts `.gitmodules`, so the file was edited with the Edit tool) and
  the stale sparse checkout directory in this worktree. `scripts/development/init-references.py`
  reads `.gitmodules` and lists no reference by name, so it needed no change; no Spec metadata,
  check or test named pi-subagents. The other references stay (pi, sandbox-runtime, pi-packages,
  swe-bench, langgraph, langgraph-docs).
- `specs/concorde/development.md`: dropped pi-subagents from the list of submodule references.
- `docsite/tests/repository/run-checks.py`: removed the `DIRECTORIES` entries `agents`,
  `operations`, `pi` and `reference`, none of which exists; every `FILES` entry exists.
- `tests/concorde/views/test_repository_checks.py` asserted `"agents"` is in `DIRECTORIES`; it now
  asserts every `DIRECTORIES` entry is a directory of the repository, so a stale entry fails the
  test instead of being copied silently as nothing.
- Verified: build, build --check, spec-validation (0 findings), init-references --check, and
  tests/concorde/views/test_repository_checks.py + test_docsite_template.py (18 passed, run with
  the primary worktree's .venv and PYTHONPATH=src since this worktree has no .venv).
- `task-validation` `r-20260929T163404-task_validation-01bdd160` failed with
  `check_sandbox_unavailable` (check.concorde.tests): the worktree had no `.venv`. Ran
  `uv sync --locked --group dev` and validated again.
- `task-validation` `r-20260929T163432-task_validation-60eac7c5` ready (no blocking findings);
  `delivery` `r-20260929T163847-delivery-57b447e2` committed `1f061513` on
  `concorde/drop-pi-subagents-reference` with `.concorde/evidence/drop-pi-subagents-reference/1.json`.

## Merge attempt 1 (main agent, 2026-09-30)

`task merge` ended `check_failed`: after merging 1f061513 the checks left `references/pi-subagents/`
uncommitted in the primary worktree (the primary's submodule checkout outlived its gitlink); the
merge was undone, main back at 93079bdd, task delivered again. Main agent's fix: run the planned
post-merge housekeeping first — `git submodule deinit -f references/pi-subagents` in the primary
worktree, which clears the checkout and the `.git/config` section — then merge again, and remove
`.git/modules/references/pi-subagents` after the merge.

## Closed: merged, 2026-09-29T16:44:11Z
