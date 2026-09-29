# Decision log: remove-legacy-migration

Goal: Remove the one-off migration of the pre-tracing records now that this checkout is migrated: scripts/development/migrate-legacy-records.py, its tests and realization.tracing.legacy-migration in the Tracing Spec
# remove-legacy-migration: brief (main agent, 2026-09-29)

The developer asked for this cleanup. Task `legacy-records-history` (merged at c2d108b6) added a
one-off migration, and the main agent has since run it on the primary worktree:
- 152 old tasks moved into `.concorde/history/`.
- The old run store archived to `~/concorde-old-records-2026-09-29.tar.zst` and removed.

Its Spec paragraph says the script is removed once the checkout is migrated.

## Goal
Remove all of the following, and anything else that exists only for the migration (check
references, the checks file of module.tracing, the docsite and the user documents):
- `scripts/development/migrate-legacy-records.py`
- `tests/concorde/tracing/test_legacy_migration.py`
- `realization.tracing.legacy-migration` in `specs/concorde/tracing/module.md` and its `.json`

The migrated history stays as it is.

## Task session (2026-09-29)

- Removed `scripts/development/migrate-legacy-records.py`, `tests/concorde/tracing/test_legacy_migration.py`,
  the `realization.tracing.legacy-migration` paragraph of `specs/concorde/tracing/module.md` and its
  entity and its `relates` relation to `concept.history` in `module.md.json`.
- Searched the whole worktree for other references (checks file of module.tracing, docsite, `docs/`,
  registry): none. `.concorde/evidence/legacy-records-history/1.json` is kept: it is the delivery
  record of the earlier task, not part of the migration.
- Verified: `registry --check`, `spec-validation`, `build --check` all succeed; tracing tests 19 passed.

## Closed: merged, 2026-09-29T10:57:37Z
