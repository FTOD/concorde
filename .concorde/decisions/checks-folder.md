# Decision log: checks-folder

Goal: Move the configured checks out of .concorde/config.json into one file per Module under .concorde/checks/, and state in Check execution's Spec that a test answers whether the code is right while a check answers what one command produced on exactly this input and whether that result can be trusted.

## 2026-09-29 — main agent, design of the checks folder (decided without the developer)

The developer approved moving checks out of `.concorde/config.json` into their own folder and
adding the test/check sentence; the details below were chosen by the main agent.

1. **One file per Module, named by its id.** Options: one `.concorde/checks.json`; one file per
   check; one file per Module. Chosen: `.concorde/checks/<module id>.json`, because parallel tasks
   usually change different Modules' checks and would otherwise conflict in one array. The folder
   stays under `.concorde/` as project configuration and is never placed beside a Module's Spec or
   code, because a check command is trusted host input and must not land in the writable scope of
   the Module it verifies.
2. **File shape `{"checks": [...]}` without a `module` field in entries.** The file name is the
   Module; repeating it per entry would only add a way to disagree. A file whose name is not a
   registered Module is `unknown_module`; anything in the folder other than `<id>.json` regular
   files is refused with a detailed error.
3. **Order**: files by Module id in byte order, entries in file order ("configuration order").
4. **Configuration profile 18.** A `checks` field left in `config.json` is refused as an unknown
   field whose message names the new location. No migration shim (rapid iteration).
5. **Digests**: wherever the configuration is digested (validation result, readiness
   `config_digest`), the checks files are digested too, so a changed check command invalidates
   evidence exactly as a changed `config.json` did.
6. **No folder means no checks**; initialization writes no checks file.

## 2026-09-29 — non-ok: init-references inside the task worktree

`python3 scripts/development/init-references.py`, run after EnterWorktree, checked out
`references/pi` and then failed on `git submodule init -- references/pi-subagents` with
"could not lock config file /home/zhenyu/concorde/.git/config: File exists"; the lock is a
0-byte read-only file nobody holds, consistent with the worktree-isolated session's sandbox
keeping the shared `.git/config` read-only (DEVELOPING says to run it before entering). The task
changes no reference material, so the remaining submodules were left uninitialized; the lock
file in the primary repository's Git directory was not touched.

Resolved: after ExitWorktree (keep), `init-references.py` run in the task worktree from the
unisolated main session initialized every reference; `.git/config.lock` no longer existed, so it
had been the isolated session's sandbox artifact.

## 2026-09-29 — main agent, further decisions and results

- The configuration order changed with the layout (files by name, then entries), so the check
  service test that asserted the old order now expects `check.a.full` (module.a.json) before
  `check.a.selected` (module.b.json); the order is specified in `service.md` and `contracts.md`.
- The readiness configuration digest became the digest of a canonical map from
  `.concorde/config.json` and every entry of `.concorde/checks/` to its content digest, rather
  than adding a second field to the measured inputs, so the readiness contract keeps its shape.
- The main-session guidance now tells the main agent to drop both `module` and `reason` when it
  copies a survey-proposed check into a checks file (`reason` is survey-only).
- Out of scope, left unchanged: `spec-tooling/spec/contracts.md` still calls the `workers` field
  "worker settings that the Harness reads" (a misuse of the glossary term); the developer is
  discussing merging `workers` with `worker-models.json` in a separate task.
- Results: full pytest suite 681 passed / 4 skipped; `spec-validation` success; `task-validation`
  ready with all 23 configured checks passed; delivery ok (8b22d643).

## Closed: merged, 2026-09-28T18:03:04Z
