# Decision log: installed-files-stay-bound

Goal: Files a later install or update adds to a project, such as the pi files of an install with --pi after init, are bound like the files installed before init, so spec-validation reports no CHK.binds.unbound for them

## 2026-09-29 — main agent: brief

Observed in a real headless verification on 2026-09-29. `/tmp/concorde-e2e/verify-pi` was
prepared with `scripts/e2e/e2e.py prepare psf/requests --rev v2.32.3`, which installs Concorde
without `--pi` and runs `concorde init`, which creates `realization.project.concorde-installation`
binding the installed files. Then `scripts/install-concorde.py <project> --without-d2 --pi` was
run again. The pi files that install added (`.pi/agents/…`, `.pi/extensions/concorde/…`,
`.pi/skills/concorde/SKILL.md`) were then reported by spec-validation as five `CHK.binds.unbound`
findings, and the task working in that project had to add them to the installation realization by
hand. The same happens whenever a later install or `concorde update` adds files that the
installation record `.concorde/install.json` lists but that init never bound: adding `--pi` later,
or a newer Concorde that installs more files.

Do:

1. Reproduce it in a fresh test project under /tmp: install, init, then install again with
   `--pi`; also update to a Concorde that adds a file, if that is cheap to simulate. Also confirm
   that installing with `--pi` before init leaves nothing unbound.
2. Fix it generally, so the installation's files stay bound across installs and updates without
   hand edits. For example, install and update keep the installation realization's bindings equal
   to the receipt's files; or the binding of installed files follows the installation record
   instead of a list frozen at init. Choose within Distribution and Spec core and log the choice.
   Keep the rule that an installed file is bound only by its exact path and never granted `rw`
   (`CHK.binds.installed`). If the fix needs a change of what either Module promises beyond this,
   gather every such question with options and a recommendation into one escalation.
3. Specify the behaviour (requirement, scenario, test) and verify it with a real install. Real
   runs, including ones that cost model usage, need no permission; run what the verification needs.

Other main sessions have tasks open on other Modules (owner-only-wake, tracing); do not touch
their Modules.

## 2026-09-29 — task session: reproduction

Reproduced in `/tmp/claude-1000/repro-bound` (a two-file Git project): install without `--pi`,
`init --propose/--apply` (binds `.claude/skills/concorde/SKILL.md` and
`.claude/workflows/concorde-brownfield.js` in `realization.project.concorde-installation`),
commit, install again with `--pi`, commit: `spec-validation` is `invalid` with five
`CHK.binds.unbound` (`.pi/agents/concorde-report.md`, `.pi/agents/concorde-step.md`,
`.pi/extensions/concorde/index.ts`, `.pi/extensions/concorde/pi_runs.ts`,
`.pi/skills/concorde/SKILL.md`). The reverse also holds: a file a newer Concorde no longer installs
and that is removed stays an entry of the realization and fails `CHK.binds.exists`.

## 2026-09-29 — task session: decision — where the fix lives

Chosen: the brief's first example. Spec core gains one function that brings the Concorde
installation realization in step with the installation record, and the installer (install and
`concorde update`, which installs) calls it after writing the receipt when the project is
initialized. It adds, as exact entries, every installed file that exists and that no realization
binds by its exact path, and removes the entries that no longer exist; it never unbinds an existing
file. When no installation realization exists but files need binding, it creates one in the root
Module the way init does. It writes only that realization's metadata member (and, only when it
creates the realization, the root entry document's explaining paragraph) in one file transaction.

Rejected: (a) deriving the realization's entries from the receipt at load time — the Protocol's
realization has only literal `entries`, so this would be a Protocol change and would make the
metadata disagree with the effective binding; (b) exempting installed files from
`CHK.binds.unbound` like control records — contradicts the goal ("bound like the files installed
before init") and changes what init and grants promise; (c) a separate housekeeping command —
validation would still fail between install and running it.

Consequence for promises: `req.distribution.installer-no-specs` ("the installer never writes
Specs") is narrowed to allow exactly this write. The brief proposed this approach, so I proceed,
but I flag it in my report as a change of a Distribution promise for the developer to confirm.
When the Specs cannot be loaded, the installer binds nothing and leaves the project as it is
(spec-validation reports why), so an install never fails after writing because of the Specs.

## 2026-09-29 — task session: implementation and verification

Committed `1b9e0e9b` on `concorde/installed-files-stay-bound`: `bind_installation` in
`src/concorde/spec/initialize.py`, called by `install()` in `src/concorde/distribution/install.py`
after the receipt is written (so plain installs and `concorde update` both bind); new
`req.distribution.installer-keeps-installation-bound`, `req.spec.installation-follows-record`,
scenarios `scenario.distribution.install-later-files-bound`,
`scenario.spec.installation-follows-record`, `scenario.spec.installation-created`, with tests; the
Distribution entry and `req.distribution.installer-no-specs` now say the installer writes no Spec
but this realization.

Decisions taken on the way: the binding reads the registry and metadata JSON directly instead of
loading a SpecRepository, because after an install that brought a new Protocol copy the binding
mismatches until update rebinds it, and loading would refuse; an entry whose file exists but that
the receipt no longer lists stays bound (never unbind an existing file); a realization whose every
entry is gone is left for `CHK.binds.exists` rather than removed; the install result reports nothing
new — the changed metadata member shows in `git status`, and `concorde update`'s `next` already says
to commit the updated files.

Verified with real installs from this worktree into Git projects under `/tmp/claude-1000/`:
install → init → install `--pi` → commit: `spec-validation` `success`, the five pi files are exact
entries of `realization.project.concorde-installation`, the root entry unchanged; install `--pi`
before init → `success`; install → init → `concorde update --pi` (with the real pi runtime) →
`success` with only `CONCORDE-UPDATE-002`; an update with nothing new leaves the Specs unchanged.
`build --check` ok, `spec-validation` success, full suite 756 passed, 4 skipped.

Not done, outside the task's Modules: `docs/using-concorde.md` (bound by `module.concorde`) still
says "The installer never writes your Specs or your registry"; it should add "except the Concorde
installation realization, which it keeps in step with the files it installs". Also not handled: an
installed file that falls under another realization's directory entry (for example a project that
bound `.pi/` as a directory before a later `--pi`) is bound, so not `CHK.binds.unbound`, but that
directory entry fails `CHK.binds.installed`, which only the project can fix by splitting it.

## 2026-09-29 — task session: delivered

`task-validation` ok (ready, nothing blocking); `delivery` ok, delivery commit `72f0e002`
(bundle `.concorde/evidence/installed-files-stay-bound/1.json`). Reported to the main agent.

## 2026-09-29 — main agent: delivery 72f0e002 reviewed, promise change goes to the developer

The task session's decision 1 narrows Distribution's promise req.distribution.installer-no-specs
("the installer writes no Spec") to "no Spec but its installation realization". Changing what a
Module promises to its users is a major-impact decision under the escalation policy, so the main
agent puts it to the developer before merging, together with the matching wording of
docs/using-concorde.md.

Developer (2026-09-29): approved the promise change and the docs/using-concorde.md wording; merging.

## Closed: merged, 2026-09-29T07:00:52Z
