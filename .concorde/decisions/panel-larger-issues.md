# Decision log: panel-larger-issues

Goal: Finish the 2026-09-28 panel review's larger item for Issues: split its bundled scenarios (about 9 into about 25) with their tests' @verifies, adding tests where none checks a new scenario

## Brief from the main agent (panel-review LARGER items)

These items are the "larger" findings left from the 2026-09-28 `spec_panel` review (decision
history in `/home/zhenyu/concorde/.concorde/tasks/panel-review-fixes.decisions.md`). They are
confirmed real problems that need no design decision but are not small edits. Full review reports
(chair report and verdict per Module) are readable at
`/tmp/claude-1000/-home-zhenyu-concorde--claude-worktrees-panel-review-fixes/dbd505b3-74e1-499b-9440-e3cc4b821993/work/reports/module.<name>.md`
and `module.<name>.verdict.md`.

How to work:
- The project has changed a lot since the review. Check each item against the current Specs and
  code first. If it is already solved or no longer applies, record that here with the reason and
  skip it.
- If doing an item needs a design decision (narrowing or changing a promise, changing behaviour,
  a word choice that is not obvious), do not decide it: escalate to the main agent with options
  and a recommendation. Never narrow a Spec promise to fit the code; a Spec/code difference where
  it is unclear which is intended is escalated.
- Splitting a scenario: keep the original id on the first scenario; each new scenario id needs a
  test with `@verifies`, otherwise spec-validation warns `CONCORDE-COVERAGE-001`. Change the Spec
  and the tests' `@verifies` in the same commit, and only where the existing test really checks
  that scenario's outcome; otherwise add or extend a test.
- Diagrams: `d2 illustrative` blocks, following the diagram rules in the Protocol
  (`.concorde/protocol/`) and the project's Specs. "Don't draw diagrams for trivia": when the prose
  already says it plainly, skipping is fine; record why here.
- Usage items: restructure Usage so it opens with / contains a worked normal path, keeping every
  existing statement true.
- Use the glossary terms (`specs/concorde/glossary.json`) exactly. Edit only files of your
  Modules where possible; if another Module's file (or the glossary) must change, keep the change
  minimal and say so in your report.
- Never commit files a Bash sandbox mounts into the worktree (`.bashrc`, `.claude/...`).
- When done: task-validation and delivery, then report to the main agent: each item done or
  skipped (with reason), the decisions you took on your own, and anything waiting for a decision.

### Items of this task (handover list)

**module.issues**
- A · F3: split `store-boundary`, `command-report-origin`, `command-close`, `command-usage`, `command-refused`, `store-append`, `store-disposition(-stale/-invalid)`, etc. (about 9 scenarios become about 25).

### Verdict text for each item (from the review's verification agents)

#### module.issues

##### F3 LARGER — scenarios bundle several situations (store-boundary and others)
Real: Protocol says situations with different outcomes get their own scenarios. `store-boundary`
mixes five inputs, three operations and "does not report success"; command-report-origin,
command-close, command-usage, command-refused, store-append, store-disposition,
store-disposition-stale/-invalid mix a success with refusals. Fixing means splitting ~9 scenarios
into ~25 and re-pointing `@verifies` declarations in `tests/concorde/issues/test_store.py` and
`test_command.py` (not our files). For store-boundary, split per case with the concrete code the
code actually raises: malformed report → `invalid_issue`; unsafe evidence path (already defined:
the report contract semantics now spells out "canonical project-relative POSIX path") →
`TypedDataError` `invalid_field` from the library, `invalid_issue` via the CLI; symlinked Issue
directory → `checked_path` raises `TypedDataError` `invalid_field` ("symlink paths are forbidden"),
`invalid_issue` via the CLI; corrupted digest → `invalid_issue`; failed publication → the
transaction's error / `io_error`. Note for that rework: interface "Store operations" says every
refusal is a Spec error "carrying one of the codes under Errors", but library-level path/shape
refusals carry `TypedDataError` codes such as `invalid_field`; the rework should say so.



## Task session decisions (2026-09-29)

- **Item A · F3 still applies.** Checked against the current `specs/concorde/issues/scenarios.md`
  and code: `store-boundary`, `command-report-origin`, `command-report-check`, `command-append`,
  `command-close`, `command-usage`, `command-refused`, `store-append`, `store-disposition`,
  `store-disposition-stale` and `store-disposition-invalid` still bundle situations with different
  outcomes. The tests are now `module.issues`' own files (`realization.issues.tests`), so
  re-pointing `@verifies` stays inside the task's Module.
- **Split granularity (decided without the developer).** Following the Protocol's rule that
  situations with different successful, failed, repeated or concurrent outcomes get their own
  scenarios: one scenario per distinct outcome (success vs. each refusal code). Argument errors
  that all end in `usage` with exit 2 stay one scenario (`command-usage`), since their outcome is
  the same; `unreadable_file` and `not_a_project` get their own. The first scenario of each split
  keeps the original id. `command-report-check` was split too although the review did not name it,
  because it has the same pass/refuse bundling.
- **store-boundary codes from the code, not the verdict text.** At the library level a report
  that breaks the report schema, an unsafe evidence path and a symlinked Issue directory are
  refused by Spec core with `TypedDataError` code `invalid_field`, while a report that meets the
  schema but breaks an Issue rule (gap subtype, half an append, over 64 KiB) is an `IssueError`
  `invalid_issue`; so "malformed report" becomes two scenarios. A corrupted report digest is
  `invalid_issue` naming the Issue. A failed publication raises the file transaction's
  `SpecError` `system_error`. The interface's "Store operations" sentence ("every refusal ...
  carrying one of the codes under Errors") is corrected to say so, as the verdict asked.
- **Found bug fixed in own code: a failed write reached the command as `system_error`.**
  `apply_files` turns an operating-system write error into `SpecError` `system_error`; the
  command's `except SpecError` branch printed that code with reason `input`, while the interface
  promises `io_error` with reason `environment` for a failed file operation. The Spec is
  unambiguous, so the command now maps `system_error` to `io_error`; a new scenario
  `command-write-failed` with a test covers it.
- **Not added:** scenarios for store-level appends to a closed or unknown Issue and for a receipt
  whose path differs from its Issue's; they were never part of a bundled scenario, and the receipt
  path check is not in the interface. The existing receipt-path assertion moves into its own test
  without a `@verifies`.

## Results

- Commit `1d5ff4ee`: 11 bundled scenarios split (29 → 51 scenarios in `scenarios.md`), every
  scenario declared by a test; interface "Store operations" corrected; command maps
  `system_error` to `io_error`. `build --check`, `spec-validation` (0 findings after linking the
  first use of "typed value") and `tests/concorde/issues` (52 passed) ok.
- Non-`ok` note: `uvx ruff check scripts/issues.py` reports pre-existing EXE001/RUF100 on lines
  this task did not change; left as is (outside the goal). `uvx` needed `UV_TOOL_DIR` under
  `$TMPDIR` in the sandbox.
- `task-validation` ok, ready. `delivery` ok: delivery commit `abb6ede5`, evidence
  `.concorde/evidence/panel-larger-issues/1.json`.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES; the system_error → io_error change was judged justified
  (the interface's Errors table has only io_error/environment; no consumer of the old output).
  Sent back (decision, mine, under the brief's "never narrow a promise"): restore the command-level
  cases dropped from command-refused (append to a closed Issue; close/reopen/append on an unknown
  Issue) and "BUT writes nothing" in command-not-a-project; stop "Store operations" claiming its
  three kinds are complete; map a file transaction's stale_proposal to the promised stale_issue
  (module.md, req.issues.revision-checked); keep the failed-write scenarios checked under root.

## Main agent's review, 2026-09-29: fixes

1. **Narrowing undone (command level).** `command-unknown-issue` now covers `show`, `close`,
   `reopen`, `close --duplicate-of` and an appending `report --file` naming an absent Issue, and
   its test runs all five. A new scenario `command-append-closed` covers appending to a closed
   Issue (`closed_issue`) and has its own test. I added a new scenario instead of widening
   `command-close-closed`, so that that id keeps meaning what it says.
2. **`command-not-a-project`**: "BUT writes nothing" restored. The test now runs `list`, `show`,
   `check`, `report`, `close` and `reopen` against a project that already holds an Issue.
   `assert_refused` now compares the bytes of every record, not only their names.
3. **Interface "Store operations"** now names every failure path. Issue-rule refusals raise
   `IssueError`, including a record changed during publication, reported `stale_issue`. Spec
   core's value checks raise `TypedDataError invalid_field` with the field. A record path through
   a symbolic link raises the same error without a field. A write refused inside the file
   transaction raises `system_error`. An `OSError` outside the transaction (read, lock, directory
   fsync) propagates unchanged. The paragraph also says how the command reports each of them.
4. **`stale_proposal` mapped to `stale_issue`, in the store rather than only in the command.**
   Options were: map it in the command only, or in the store. The promise in module.md ("A stale
   transaction is refused, reported `stale_issue`") and `req.issues.revision-checked` are promises
   of the Issue store, so `_publish_text` now turns the file transaction's `stale_proposal` into
   an `IssueError` `stale_issue` naming the Issue. That also fixes the command's output. New
   scenarios `store-publication-stale` and `command-write-raced` have patch-based tests: a racing
   writer changes the record between the store's read and `apply_files`.
5. **Checked under root too.** `store-failed-publication` and `command-write-failed` each have a
   patch-based test that makes `os.replace` refuse Issue records with EROFS. The command's test
   runs in-process so that the patch reaches its store calls. The chmod-based tests stay as a
   second, real-filesystem check that skips under root.
- Review fixes verified: `tests/concorde/issues` 57 passed; `spec-validation` 0 findings;
  `build --check` ok. Work commit `9941c50c`. `delivery` ok: delivery commit `ddd44c43`,
  evidence `.concorde/evidence/panel-larger-issues/2.json`.

## 2026-09-29 — Main agent: independent review of delivery 2

- Independent review MERGE-WITH-NOTES: all five requests satisfied. Sent back for a last small
  round: make the new stale_issue wrap a structural error-chain link (path and the stale_proposal
  as a typed cause, per the developer's error-chain rule), a message that fits a creation race,
  and "Store operations" no longer promising that every IssueError names its Issue.

## Main agent's second review, 2026-09-29: fixes

1. **Structural error chain.** `_publish_text` now raises `IssueError(..., "stale_issue",
   path=<record path>, causes=(error,))`, so `record()`, `describe()` and `where()` keep the file
   transaction's `stale_proposal` as a typed cause and name the record file. The tests assert the
   cause code, the path, `record()["causes"]` and `where()`.
2. **A race on creation has its own wording.** The message says "was created by another program
   while this write was creating it" when the store was creating the record, and "was changed by
   another program after this write read it" otherwise. The racing writer in the tests can now
   also create the file, and a new test covers creation. I widened `store-publication-stale` to
   "created or changed" and to the creation of an Issue, instead of adding a scenario, because
   the outcome is the same.
3. **Interface, first bullet of "Store operations".** Rather than list what each message names
   (an earlier draft of that list was untrue too: the unknown-`status` message does not name the
   value), it now promises only what holds everywhere: every `IssueError` message states what is
   wrong, and a refusal that concerns one stored Issue (a read, an append, a disposition or a
   publication) also names that Issue. Checking that promise showed one gap: the store's record
   size refusal in `_publish_text` did not name the Issue. It now does ("Issue <id>: the record
   would exceed the admitted size of 16 MiB").
- Second-review fixes verified: `tests/concorde/issues` 58 passed; `spec-validation` 0 findings;
  `build --check` ok. Work commit `2d0fb252`. `delivery` ok: delivery commit `051615c1`, evidence
  `.concorde/evidence/panel-larger-issues/3.json`.

## Closed: merged, 2026-09-28T20:08:10Z
