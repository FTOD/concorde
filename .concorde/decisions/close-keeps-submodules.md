# Decision log: close-keeps-submodules

Goal: Stop task close and merge from deinitializing submodules in the repository-wide Git configuration, so ending one task no longer unregisters the references every other worktree uses

## Brief (main agent, 2026-09-30)

### The defect
`src/concorde/tasks/store.py` (worktree removal on close/merge, ~line 1402) runs
`git submodule deinit --all` in the task worktree before `git worktree remove --force`. In a
linked worktree without `extensions.worktreeConfig`, `deinit` removes the `submodule.<name>`
sections from the **repository-wide** `.git/config` that every worktree shares. So each task that
ends unregisters all reference submodules for the primary worktree and every other task worktree.
Observed on 2026-09-30: after several merges, `.git/config` holds no `submodule.references/*`
section (only stale `reference/*` ones), and preparing the next task (`scripts/development/
init-references.py`) must register them again — which fails whenever a running task session's
Bash sandbox holds the placeholder `.git/config.lock` (see task `init-references-lock`, merged
`1e42111f`, and its Issue I-84382b27cf4c5fcd9b6cf6c79909530a). The deinit itself also writes the
shared config and can hit the same lock.

### What to do
- Make ending a task remove its worktree (with its submodule checkouts) without touching the
  shared `.git/config`: e.g. check each submodule for local changes yourself (refusing without
  `--force` as today), then `git worktree remove --force`; or another Git-native way (the
  developer prefers Git's own mechanisms over reimplementation). Keep today's refusal of local
  submodule changes and the detailed error chain.
- Also check whether the worktree's `.git/worktrees/<task>/modules/` (the per-worktree submodule
  Git dirs made by `init-references.py`) are removed with the worktree, and that nothing leaks.
- Update Tasks' Spec (requirements/scenarios/contracts about closing with submodules) and tests.
- Record the defect as an Issue owned by `module.tasks`, close it on this branch with the fix as
  evidence.
- Do not clean up the stale `submodule.reference/*` sections of `.git/config` (primary-worktree
  housekeeping, the main agent's call); just mention them.

## Task session (2026-09-30)

- **Fix chosen:** dropped `git submodule deinit --all` from `close_locked` and kept only
  `git worktree remove --force` (forced whenever the worktree has `.gitmodules`), Git's own way to
  remove a worktree holding submodule checkouts. Reason: reproduced with git 2.43 that deinit in a
  linked worktree deletes the `submodule.<name>` sections of the shared `.git/config`, while the
  forced removal leaves the configuration unchanged and deletes `.git/worktrees/<task>/modules/`
  with the rest of the worktree's administrative directory, so nothing leaks.
- **Refusal of local submodule changes kept** by the close's existing dirty check (`git status`),
  now run with `--ignore-submodules=none` so a submodule `ignore` setting cannot hide a change the
  forced removal would discard (the old deinit refused that case; plain status did not). This also
  applies to the derived active/delivered state, which already counted a change inside a submodule.
- **Spec:** new `req.tasks.shared-config-kept`; `worktree_failed` wording in requirements and
  contracts no longer speaks of deinitialized submodules; `scenario.tasks.close-submodules` now
  promises the shared configuration unchanged and the submodule repository removed;
  `scenario.tasks.close-submodules-dirty` covers `ignore = all`. The extended test fails on the old
  code (config section gone; `worktree_failed` instead of `dirty_worktree` under `ignore = all`).
- **Issue** I-accf29633c59514fa461d83949e5da8f (owner `module.tasks`) recorded and closed resolved
  with commit 01298edc as evidence.
- **Observed, not changed (outside the task):** the primary `.git/worktrees/` holds leftover
  directories of ended tasks (decision-log-closing, restructure-*, worker-config-followups, …) that
  contain only `commondir` and `config.worktree`: these are mount points Claude Code's Bash sandbox
  creates for its deny list (like the `.git/config.lock` placeholder), not remains of the close;
  `git worktree prune` would remove them. The stale `submodule.reference/*` sections the brief
  mentions were not visible in `.git/config` from this worktree (only `submodule.references/*`
  now), left to the main agent as the brief says.

## Main agent on the session's report (2026-09-30)

Accepted, including the stricter `--ignore-submodules=none` dirty check. The stale
`submodule.reference/*` sections were already removed by the main agent with the developer's
approval. The leftover `.git/worktrees/<ended task>/` stubs are left until no task session runs
(running sandboxes bind those paths). Merging.

## Closed: merged, 2026-09-29T18:49:33Z
