# Decision log: panel-larger-distribution

Goal: Finish the 2026-09-28 panel review's larger items for Distribution, Dogfooding, Harness and the root Module: split bundled scenarios with their tests' @verifies, open Usage sections with worked normal paths, and the defect cycle diagram

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

**module.distribution**
- A · F14: about 15 bundled scenarios, including `python-dependencies`, `protocol-manifest-bind`, `install`, `install-busy`, `install-pi` and `update`. Tests: `tests/concorde/distribution/test_distribution.py`.
- B · F5: rewrite "Installing into a project" as an ordered normal path (the installer check order has already changed; see the uv and docsite changes).

**module.dogfooding**
- A · F10: split `refused-source` into three, adding the untested `develop_source_not_repository` (needs a test).
- C · F16+F17: one diagram: the defect cycle across two repositories and three actors.

**module.harness**
- B · F6: a worked example: an implement worker's grant, then the settings/extension it generates, then one allowed edit and one denied call with its reason.

**module.concorde**
- B · F8: the root Usage should open with the normal path, not with the table of levels of work.

### Verdict text for each item (from the review's verification agents)

#### module.distribution

##### F5 LARGER — restructure "Installing into a project" into an ordered normal path (~50 lines), after F3 is decided.

(F3 was decided: the interpreter probe, uv and npm checks moved before the first write; see the installer's current check order, and the uv and docsite changes.)

##### F14 LARGER — ~15 bundled scenarios should be split, with @verifies in tests/concorde/distribution/test_distribution.py.



#### module.dogfooding

##### F10 LARGER — refused-source bundles three situations and omits `develop_source_not_repository`
Real, but splitting it means re-pointing `@verifies` in `tests/concorde/dogfooding/test_dogfooding.py`,
which I may not edit. `test_only_a_clean_primary_worktree_on_a_branch_is_installed_from` covers
not_primary, dirty and detached in one test and never exercises `develop_source_not_repository`.
To do: split into `scenario.dogfooding.refused-source` (keep the id for the linked-worktree case,
code `develop_source_not_primary` naming the primary worktree),
`scenario.dogfooding.refused-detached`, `scenario.dogfooding.refused-dirty` and
`scenario.dogfooding.refused-not-root` (`develop_source_not_repository`, e.g. a subdirectory of the
repository). Each gets an otherwise valid source and "BUT nothing is written into the project".
Split the test into four tests with matching `@verifies` and add the not-root case. Precedence
follows `develop_source`'s order: not_repository, then not_primary, then detached, then dirty.

##### F16 LARGER — cross-repository defect cycle needs an activity view
Real but advisory. The cycle has three actors: project main agent, developer, Concorde-repository
session. Add one `d2 illustrative` activity view beside "Reporting a defect" with those three
lanes: observe → classify → write and check report → decision log → hand-off → (limitation:
developer decides) → record in task, fix, close, merge → update → validate → resume. Not a
few-sentence edit.

##### F17 LARGER — two-repository context view
Advisory. Instead of a second diagram, fold it into F16's view: give the project and the Concorde
repository as containers, with the install/update edge (primary worktree → `.concorde/framework/`)
and the defect-report edge (project → developer → Concorde session). That is one diagram and
avoids drawing trivia twice.


#### module.harness

##### F6 LARGER — Worked normal path and illustrative activity view in Usage
The finding is real: the normal interaction is one abstract sentence. The fix is a worked example (for instance an implement worker with one `rw` source, one `ro` Spec and one `names` file → generated settings/extension → launch → one allowed edit and one denied call with its reason), plus a `d2 illustrative` view with lanes for agent Module, Harness and agent program. That is more than a few sentences and adds a diagram, so it was not edited.



#### module.concorde

##### F8 LARGER — Usage leads with the taxonomy, not the normal path
The finding is real: Protocol kinds/module.md says "Start with a coherent normal path", but the root Usage opens with "The levels of work" table and diagram. The small part is fixed: the normal path in module.md now ends with a sentence saying that a read-only Operation such as `understand` or a review may also run in the primary worktree as an unbound run, which is confirmed by the Operations module.md "Unbound" column and line 62. What remains, and is not a small edit: move "### A normal path", with its diagram, workflow paragraph and command table, ahead of "### The levels of work", and consider replacing the catalogue of Operation names with one worked goal.



## Task session log

### Distribution A · F14 — done (commit 4ba27548)

Checked against the current `scenarios.md`: the bundling was still there (and the later
`install-pi`, `pi-runtime-default`, `update-pi` and `install-docsite-template` had the same
pattern). Split into 17 new scenarios: `build-keeps-edited-leftover`, `protocol-manifest-report`,
`install-repeat`, `glossary-import-none`, `install-settings-invalid`,
`update-unvalidated-reported`, `update-unvalidated-cleared`, `install-after-runs-end`,
`install-python-env-failed`, `install-programs-missing`, `python-dependencies-failed`,
`python-dependencies-skipped`, `install-without-d2`, `install-without-pi-runtime`,
`update-add-pi`, `update-keeps-pi-choices`, `install-docsite-template-refused`.

Decisions taken without the developer:
- Kept alternatives that share one outcome together (e.g. `d2_digest_mismatch` or
  `d2_unavailable`; `uv_missing` or `npm_missing` as one `install-programs-missing`; `init --apply`
  or an install finding a declared glossary), since the Protocol asks for separate scenarios only
  where outcomes differ.
- `protocol-manifest-bind` keeps its identity on the bind situation (its name), placed first;
  the report without flags became `protocol-manifest-report`.
- The worker progress file and the dead run in `install-busy` moved from a BUT outcome with no
  precondition into its GIVEN; the "once the run has finished" action became
  `install-after-runs-end`, which the existing test exercises (its last install succeeds with the
  finished, dead and worker files still present).
- Existing tests declare the new scenarios where they already check them (one test may declare
  several); two undecorated tests now declare `install-pi`/`install-repeat` and
  `install-programs-missing`/`update-keeps-pi-choices`. Removed the `install` and `install-pi`
  declarations of the dependency test, which checks neither. Extended one assertion: the edited
  leftover's refusal names the output.
- Added "the result asks for the primary branch to be merged into the open task" to `update`,
  which Usage already promises and the test checks.

### Distribution B · F5 — done (commit e02dcbf3)

Rewrote "Installing into a project" as eight ordered steps following `install()` in
`src/concorde/distribution/install.py` (checks, pinned programs, files, own Python environment and
dependencies, command, guidance, workflows, record), followed by paragraphs on the receipt, the
busy refusal and the task worktree's command. Every earlier statement is kept.

Decisions taken without the developer:
- Listed the refusals the code makes before the first write that the text did not name:
  `invalid_project`, `stale_build` for the guidance, `invalid_descriptor` (all already in code;
  no promise changed). Ordered the checks as the code runs them, and swapped "project's settings"
  and "descriptor's Python requirement" in the Design paragraph to the same order.
- Replaced "whose runner process lives, as its run progress file says" with "whose runner still
  holds its run lock, found through its run progress file", matching the current code and the
  `install-busy` scenario since the run-liveness-lock merge; not a change of promise.
- Added requirement links to the steps (fresh guidance, settings, own permissions, receipt, own
  Python, idle install, busy named), all existing requirements.

### Dogfooding A · F10 — done

Split `scenario.dogfooding.refused-source` (identity kept for the linked worktree,
`develop_source_not_primary` naming the primary worktree) into it, `refused-not-root`
(`develop_source_not_repository`), `refused-detached` and `refused-dirty`, as the verdict proposed.
The one test became four with matching `@verifies`; the new not-root test covers a copy outside
any Git repository and a copy inside a larger repository's worktree.

Decisions taken without the developer:
- The check order (not a root, then linked, then detached, then dirty) is stated in prose under
  `refused-source` rather than as a scenario of its own; the linked-and-detached case stays in the
  `refused-source` test as that precedence's evidence.
- `refused-dirty` says "uncommitted or untracked change", as the requirement and code
  (`--untracked-files=normal`) do.

### Dogfooding C · F16+F17 — done

One `d2 illustrative` view placed before "Reporting a defect", with the project (main agent lane and
`.concorde/framework/`), the developer and the Concorde repository (session lane and primary
worktree) as containers: observe → whose problem → write and check the report → decision log →
hand-off → record and assign → (design limitation: developer decides) → fix and close → merge →
developer tells the main agent → update and validate → merge into open tasks and resume; plus the
install/update edge from the primary worktree to `.concorde/framework/`. Rendered with the pinned
d2 to check it compiles and reads.

Decisions taken without the developer:
- The notice that the fix is merged goes through the developer, as Usage says ("which the
  project's main agent learns from the developer or by listing the Concorde repository's Issues"),
  not as a direct edge from the Concorde repository.
- The `not-actionable` closing path is left to prose, to keep the view on the normal path.

### Harness B · F6 — done

Added "A worked example" to Usage, before "A worker on Claude Code": an `implement` worker of a
Checkout task, its grant (rw source, ro Spec, ro code of another Module, a hidden Spec), the worker
settings / permission extension, one allowed edit and one denied new file with the write hook's
exact reason (from `src/concorde/harness/write_hook.py`), and a `d2 illustrative` sequence with
Workers, the Harness and the agent program.

Decisions taken without the developer:
- The verdict suggested a `names` file in the example; a real `implement` grant has none (checked
  with `concorde grant --type implement`: every path is `ro` or `rw`, since `implement` reads
  `ProjectImplementation`). To stay true, the example uses a path with no level instead and a
  closing sentence says `names` appears in e.g. an `understand` grant.
- The denied call is a Write of a new, undeclared file, where the write hook alone decides and its
  reason is certain; an Edit of a `ro` file is also refused by a deny rule, and which of the two
  Claude Code reports first is not stated in the Specs.
- A sequence diagram rather than an activity view with lanes, since the question is the order of
  messages between the three participants (Protocol's diagram table).

### Root Module B · F8 — done

Moved "### A normal path" (diagram, workflow paragraph and command table included) ahead of
"### The levels of work"; headings, and so the `#the-levels-of-work` links from ten Modules, are
unchanged. Replaced the parenthesised list of Operation names with one worked goal: a task
`retry-limit` bound to `module.payments`, opened with the exact `task open` command, then
`understand --plan`, `specify`, `implement`, `test`, `code_review`, `task-validation`, `delivery`
and `task merge`, with the Operation arguments the main-session skill shows.

Decisions taken without the developer:
- The worked goal reuses the `retry-limit` / payments example that Dogfooding's defect report
  already uses, so the two read as one project; `spec_review` is left out of the worked path (a
  Spec review is optional and the path already shows one review), and `spec_panel` stays in the
  Operations catalog only.

### Verification and delivery

- `build --check` clean; `spec-validation` success with 0 errors and 0 warnings; full suite
  `.venv/bin/python -m pytest -n 8`: 691 passed, 4 skipped.
- `task-validation`: ok, ready, nothing blocking. `delivery`: ok, delivery commit `67a4a479`,
  bundle `.concorde/evidence/panel-larger-distribution/1.json`.
- Non-`ok` side notes: the first preparation command lost `.venv` (re-created with `uv sync`);
  `uvx ruff` needed `UV_TOOL_DIR` under `$TMPDIR` because `~/.local/share/uv/tools` is read-only in
  the sandbox. `ruff check` reports pre-existing PLW1510/ISC004 findings in both test files, not
  introduced here and not a project gate; left alone.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES (nothing dropped or narrowed). Sent back: the check order
  in step 1 (the docsite template is checked before the guidance), the write hook's
  "Concorde grant: " prefix in the harness example, and install-without-pi-runtime's directory
  clause, which its test does not check.
- Observation for the developer, outside this task: the 2026-09-29 decision on distribution F3
  (option b) moved the uv and npm checks before the first write; the interpreter probe still runs
  inside _own_python after the framework copy, and the Spec says so.

### Main agent's review follow-up (three fixes and the optional diagram)

1. Distribution step 1 lists the checks in `install()`'s order: `stale_build` (covering a stale
   guidance render, since `verify_fresh` checks every output), then the docsite template, then a
   missing guidance render (`_guidance`, also `stale_build`).
2. Harness example quotes the reason with the `Concorde grant: ` prefix, which
   `write_hook.main()` and `pi_permission.ts` both add, and says the hook adds it.
3. New test `test_an_install_without_the_pi_runtime_needs_no_npm` verifies
   `install-without-pi-runtime` on a fresh project with no npm and checks that
   `.concorde/tools/pi-runtime` does not exist; the default-runtime test no longer declares it.
4. Optional: the defect-cycle diagram's "merged" edge now leaves the Concorde primary worktree
   (where the fix is merged) for the developer's notice, instead of the session's merge step;
   rendered with d2, the long crossings at the bottom are gone. Decided without the developer: an
   illustrative layout choice that keeps the same meaning.
5. Verified: `spec-validation` 0 errors 0 warnings; Distribution and Dogfooding tests 42 passed.
   Delivered again: `delivery` ok, delivery commit `b0c3759d`, bundle
   `.concorde/evidence/panel-larger-distribution/2.json`.

## Closed: merged, 2026-09-28T20:08:36Z
