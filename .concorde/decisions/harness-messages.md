# Decision log: harness-messages

Goal: Developer-approved panel-review decisions for the Harness: (harness F18) reword the write-denial reason in write_hook.py and pi_policy.ts (and the tables in claude-code.md/pi.md and tests) so it covers both cases: the path is not in this task's grant; a file no Module declares must first be declared as a pending file through a specify task, and a file another Module declares needs that Module bound; also make pi's .git reason consistent with the hook's; (harness F12) keep the decidable SHALLs in Workers and Task sessions and link them from Harness module.md, define or drop 'a grant it cannot read', and make settings generation raise a SettingsError with a detailed reason for a malformed grant instead of a bare KeyError. Specs and tests.

## Decisions (task session, 2026-09-29)

1. **Wording of the ungranted-write reason (F18).** Options: two reasons chosen by which Module
   declares the path, or one reason covering both cases. Chosen: one reason, `<path> is not in this
   task's grant; a file no Module declares must first be declared as a pending file of a Module
   through a specify task, and a file another Module declares needs that Module bound to the task`,
   identical in `write_hook.py` and `pi_policy.ts`. Reason: the hook and the extension receive only
   the grant's lists, not which Module declares an ungranted path; telling the cases apart would
   need Spec core's declarations inside the harness, which the goal does not ask for.
2. **Making the `.git` write reason consistent.** Options: change pi's `.git` write reason to the
   hook's generic ungranted reason, or give the hook pi's `.git` row. Chosen: the hook now denies
   the task worktree's `.git` with pi's reason `Git metadata is not available to workers`, and the
   hook table in `claude-code.md` gains that row (tried before `rw`), so pi's write table is again
   "the same rows, decisions and reasons" as the hook. Reason: the generic reason would tell a
   worker to declare `.git` through a `specify` task, which is wrong; one shared precise reason is
   the consistent outcome.
3. **"A grant it cannot read" (F12).** Chosen: define it, not drop it. A malformed grant has no
   `entries` list, or an entry that is not an object with a non-empty, worktree-relative path (not
   absolute, no `..`) and a level of `rw`, `ro` or `names`. `GrantView`/new `grant_view()` raise
   `SettingsError("grant_malformed", …)` naming the first bad entry (index and JSON) and what is
   wrong. Workers checks this before writing any settings and fails the run with `grant_malformed`,
   reason `input`; the pi backend also wraps it as a `BackendRefusal`. `tool_set()` was made
   tolerant of non-dict entries so the run record is still written for such a request.
4. **Where the decidable SHALLs live (F12).** Kept in Workers and Task sessions as directed; added
   `req.workers.malformed-grant`, a `grant_malformed` error row and
   `scenario.workers.malformed-grant-refused` in Workers, and a "Where its promises are required"
   section in the Harness entry linking each Workers and Task sessions requirement that covers a
   harness promise. No Task sessions document changed (outside the task's Modules).
5. **Lint.** `ruff check` on the touched packages reports 28 pre-existing findings in files and
   lines this task did not change (e.g. `__all__` order in `settings.py`, present at the base);
   left alone as outside the goal. Formatting passes (`ruff format --check`, Prettier).
6. **Non-ok result.** A first `pytest tests/concorde/harness` run failed
   `test_check_executor.py::CheckCancellationTests::test_host_interrupt_ends_the_tree_and_keeps_drained_output`
   (`CheckCancelled not raised`, alongside a `ProcessLookupError` warning from `/proc`); it passed
   on the immediate re-run and touches no changed file, so it was treated as a timing flake.

## Closed: merged, 2026-09-28T17:30:21Z
