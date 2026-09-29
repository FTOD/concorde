# Decision log: init-references-lock

Goal: Let scripts/development/init-references.py prepare a task worktree while other task sessions run: skip git submodule init for a submodule already registered in the shared .git/config, so preparing a task never takes the config lock that a running task session's sandbox holds

## Brief (main agent, 2026-09-30)

### Why
While preparing task `hide-implementation-tab`, `python3 scripts/development/init-references.py`
failed at `git submodule init -- references/pi` (exit 128): `error: could not lock config file
/home/zhenyu/concorde/.git/config: File exists`. The task session of `entry-structure` was running a
sandboxed Bash command; Claude Code's sandbox runtime keeps `.git/config` read-only by
`--ro-bind /dev/null <repo>/.git/config.lock`, which makes an empty 0444 `config.lock` on the host
for the duration of the command (it removes it afterwards, see
`references/sandbox-runtime/src/sandbox/linux-sandbox-utils.ts`, `cleanupBwrapMountPoints`). The
script calls `git submodule init` for every reference of every new task worktree, although the
submodule URLs live in the repository-wide `.git/config` that all worktrees share and are already
registered; `git submodule init` takes the config lock even when nothing changes. So preparing a
task fails whenever any task session runs a sandboxed command. Details and the main agent's own
mistake (it deleted the placeholder while that bwrap still ran) are in the decision log of
`hide-implementation-tab`. The developer judged it a Concorde bug and asked to fix it directly.

### What to do
- Fix `scripts/development/init-references.py` so preparing a worktree writes the shared
  `.git/config` only when it must: skip `git submodule init` when `submodule.<name>.url` (and
  whatever else `init` would set) is already present — reading config takes no lock. Check whether
  anything else in the script writes shared config (e.g. `submodule.<name>.active`) and handle it
  the same way. When a write is really needed and the lock is busy, fail with a detailed error that
  names the lock and says a running task session's sandbox may hold it — never delete the lock.
- Add or adjust tests under `tests/concorde/development/`.
- Update the Spec text that describes the reference initializer (`specs/concorde/development.md`
  and/or the root entry's "Development environment" realization) and the development guidance
  (`prompts/development/skill.md`, step 2 of "How work is organized") if what they say changes.
- Record the defect as an Issue owned by `module.concorde` with
  `python3 scripts/issues.py report --file <report> --task init-references-lock`, then close it on
  this branch with `--reason resolved` and the fix as evidence before delivery.

### Coordination note
Task `entry-structure` also holds `module.concorde` and is rewriting `specs/concorde/module.md`,
removing `specs/concorde/core-concepts.md` and changing `protocol/`. The main agent opened this task
in parallel because the files it needs are disjoint (decision taken without the developer's explicit
say on the overlap; the developer asked for the fix now). Do **not** edit `specs/concorde/module.md`
unless unavoidable; prefer `specs/concorde/development.md`. If a merge conflict arises later, the
main agent will ask you to merge main into this branch.

## Task session (2026-09-30)

- **Finding that corrects the brief's premise.** With git 2.43.0, `git submodule init -- <path>`
  does *not* take `.git/config.lock` when nothing changes: it writes `submodule.<name>.active` only
  when the submodule is not active (and a missing `active` counts as active once `url` is set) and
  `url` only when unset. Reproduced in a scratch repository and in this worktree's own sandbox,
  where `.git/config.lock` was present (0444, 0 bytes) and `git submodule init -- references/pi`
  exited 0. So the recorded failures (hide-implementation-tab, checks-folder, delivery-smoke,
  operation-caller-wording) happened when a submodule really needed registering. The order of the
  current `.git/config` (every `references/*` section writes `active` before `url`, as `init` does,
  and the file was last written at 01:46, around the hide-implementation-tab re-run) suggests the
  sections had been removed before, e.g. by a `git submodule deinit`; this is inference, not
  verified. The fix therefore matters mainly for its explicit registration check and its error.
- **Fix.** `init-references.py` now reads the registration (`url`, `active`, and `update` when
  `.gitmodules` gives one; a `submodule.active` pathspec is left to Git) and runs `git submodule
  init` only for an unregistered submodule. It registers every missing submodule before cloning
  any, so a busy lock stops it before it leaves references half prepared. When a registration is
  needed and `config.lock` of the common Git directory exists, it stops with a `SystemExit` naming
  the submodule, `config` and the lock, saying a session's sandbox may hold it, to run again when
  that command ends and never to delete the lock; a failed `git submodule init` or one that left
  the submodule unregistered (Git sets `active` "gently", ignoring a lock error) is reported with
  Git's output. Nothing else in the script writes the shared config (the clone, sparse-checkout
  and checkout write only the submodule's own Git directory under `.git/worktrees/<wt>/modules/`).
- **Testability.** `git()` resolves its default `cwd` from `ROOT` at call time, so a test can point
  the script at a scratch repository.
- **Spec and guidance.** Added a paragraph and `scenario.concorde.references-registered-once` to
  `specs/concorde/development.md` (External references); `specs/concorde/module.md` untouched. Step
  2 of `prompts/development/skill.md` now says the script registers only unregistered submodules,
  refuses a new registration while another session's sandbox holds the lock, to rerun then and
  never delete the lock. The main-session and task-session prompts were left as they are: they
  still hold (the preparation may write the shared configuration).
- **Tests.** `tests/concorde/development/test_init_references.py` (3 tests, verifying the new
  scenario): a registered submodule is checked out under a held lock with `.git/config` unchanged;
  an unregistered one under a held lock is refused in detail with nothing cloned and the lock kept;
  an unregistered one without the lock is registered and checked out.
- **Issue.** Recorded `I-84382b27cf4c5fcd9b6cf6c79909530a` (owner `module.concorde`) and closed it
  `resolved` with commit 46ff8e2e, the test file and the scenario as evidence (commit a88eb6e1).
- **Delivered.** `task-validation` ready (check.concorde.tests passed, no blocking findings);
  `delivery` ok, delivery commit 42f2c3c9 on `concorde/init-references-lock`.

## Main agent on the session's report (2026-09-30)

Accepted the session's correction of the brief: `git submodule init` takes no config lock when a
submodule is already registered (git 2.43), so the recorded failures happened only when a
registration was missing; why the registrations were missing is unverified. The fix's real value is
registering only what is missing, before any clone, and refusing a needed registration under a held
lock with a detailed error. Merging with the build and spec-validation checks.

## Closed: merged, 2026-09-29T17:59:15Z
