# Decision log: panel-larger-e2e

Goal: Finish the 2026-09-28 panel review's larger items for E2E and its children: split bundled scenarios with tests, add a worked example and failure reactions to E2E, and the flow diagrams

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

**module.e2e**
- A · F2 (remaining part): split `scenario.e2e.trust` into first trust and trusting again. The current test does not check that a second call changes nothing, so extend the test first.
- B · F8: a worked example: `prepare psf/requests --rev v2.31.0`, then `run ... --via claude`, then `watch`.
- D · F14: say how each Module that e2e uses reacts to failure (a failed install, `init` or `task open` makes `prepare` fail with `command_failed`, leaving a partial project directory; `watch` skips a run directory without a run progress file), plus one sentence of reasoning for each choice `prepare` makes.

**module.dogfood-scenarios**
- A · F5: split `client`, `scenarios-apply` (split out `unknown-scenario`), `fault`.
- C · F6: diagram of preparing a scenario.

**module.headless-sessions**
- C · F11: the wake loop diagram.

**module.swe-bench-cases**
- C · F13: the repair round diagram.

### Verdict text for each item (from the review's verification agents)

#### module.e2e

##### F2 LARGER — scenario.e2e.repositories (and scenario.e2e.trust) fold several situations into one
Real: the only WHEN is listing, while the refusal and the default root have no trigger; `trust`
folds a second invocation into an outcome. Splitting needs new scenario ids, and the coverage
check (CONCORDE-COVERAGE-001, a warning) then requires `@verifies` declarations in
`tests/concorde/e2e/test_e2e.py`, which is outside the files I may edit, so both must change in one
step. Proposed edit to `specs/concorde/e2e/scenarios.md`, replacing the two scenarios:
```
### scenario.e2e.repositories — SWE-bench's repositories are listed
- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer lists the repositories
- THEN the list names SWE-bench's Python repositories, among them `psf/requests` and `pallets/flask`

### scenario.e2e.unknown-repository — A repository SWE-bench does not name is refused
- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer prepares a repository not on the list without `--any`
- THEN preparation is refused with `unknown_repository` naming the known ones

### scenario.e2e.default-root — Test projects live in the temporary directory
- GIVEN an environment without `CONCORDE_E2E_ROOT`
- WHEN the tool resolves the [end-to-end root](../glossary.json#concept.end-to-end-root)
- THEN it is `concorde-e2e` in the system's temporary directory, outside the developer's home

### scenario.e2e.trust — Trusting a test project
- GIVEN a [test project](../glossary.json#concept.test-project) whose repository root Claude Code does not trust, and a configuration with other settings
- WHEN the developer runs `trust` for a directory inside it
- THEN the configuration marks that repository root trusted, keeps every other setting, and a backup of the file exists

### scenario.e2e.trust-again — Trusting a trusted project changes nothing
- GIVEN a test project whose repository root `trust` already marked trusted
- WHEN the developer runs `trust` for it again
- THEN the configuration is unchanged and the result names no newly trusted root
```
and in `tests/concorde/e2e/test_e2e.py`: `@verifies("scenario.e2e.repositories")` →
`@verifies("scenario.e2e.repositories", "scenario.e2e.unknown-repository", "scenario.e2e.default-root")`,
and `@verifies("scenario.e2e.trust")` → `@verifies("scenario.e2e.trust", "scenario.e2e.trust-again")`
(the existing test bodies already assert each outcome; splitting the tests is optional).

##### F8 LARGER — Usage has no worked example or flow view
Real (advisory). Add at the top of Usage a short worked example (`prepare psf/requests --rev
v2.31.0`, `run /tmp/concorde-e2e/requests --via claude`, `watch ...`) with abbreviated JSON results,
and, if wanted, a small `d2` flow prepare → [trust] → run via claude | driver → watch. Several
paragraphs plus a diagram, so not done here.

##### F14 LARGER — collaborations state no failure reaction, no reasoning for `prepare` choices
Real (advisory). What is needed: for Distribution, that a failed install, `init` or `task open`
stops `prepare` with `command_failed` naming the command, status and output and leaves the partial
project directory (which a later `prepare` of the same name refuses); for Execution, that `watch`
skips a run directory without a run progress file; and a sentence of reasoning per `prepare` choice
(shallow fetch: SWE-bench base commits are commits `git clone --branch` does not accept and no
history is needed; the commit before `task open`: the task branches from it). Whether leaving the
partial directory is intended, and why `d2` is left out, should be confirmed by the developer
before it is written as a promise, so not edited here.



#### module.dogfood-scenarios

##### F5 LARGER — `client`, `scenarios-apply` and `fault` bundle a second situation
Real (one situation per scenario), but all three are verified by tests in
`tests/concorde/e2e/test_dogfood.py`, which I may not edit. `scenarios-apply` and `client` are
verified by one test. To do: split into `scenarios-apply` (catalogue read) and a new
`scenario.dogfood-scenarios.unknown-scenario` (`unknown_scenario` naming the known ones);
`client` (default Claude Code and the installer flag per client) and optionally a separate one
for the `--client` override; `fault` (first injection) and a new
`scenario.dogfood-scenarios.fault-reinjected` (`fault_not_applicable` naming file and count). Then
split the tests with matching `@verifies`. "This checkout" in `scenarios-apply` is the working tree
(the test reads `REPOSITORY_ROOT` files), while `prepare` clones the committed checkout. Say
"this checkout's working tree" there when splitting.

##### F6 LARGER — the preparation flow needs an illustrative view
Advisory. Add one `d2 illustrative` flow beside "Running one": prepare (clone → inject and commit
→ build) in `concorde/`; clone, develop install, init and commit in `project/`; baselines in
`dogfood.json`; run with the session in `sessions/<time>/`; evaluate to `evaluation.json`; the
throwaway clone used by `reports_accepted` shown outside the scenario directory. Not a
few-sentence edit.



#### module.headless-sessions

##### F11 LARGER — no activity view of the wake loop
Advisory, and real: the loop branches (idle / wait / resume / exited / no_session /
rounds_exhausted / wait_exceeded). A small `d2 illustrative` activity view beside "Waking the
session" would help. Draw it after F3b is decided, so the timeout exit is right.



#### module.swe-bench-cases

##### F13 LARGER — no activity view of the repair round
Advisory and real. A small `d2 illustrative` view beside "Repairing the adopted Specs" would help:
open task → spec_review → accepted? → (no: specify → spec_review) → task-validation → delivery →
merge, with a side exit "step not ok → stop, task stays open". Draw it after F4 is applied.



## 2026-09-29 — Task session: work done and decisions taken without the developer

Checked each item against the current Specs and code first.

- e2e A (F2): `scenario.e2e.repositories` was already split on main (unknown-repository,
  default-root). Only `trust` was left: split out `scenario.e2e.trust-again`. The old test only
  checked that the second call reported no newly trusted root, so I added a separate test that
  compares the configuration file's bytes before and after the second call and checks the root is
  reported under `already`. Commit 6ee… see `git log` ("split trusting again out").
- e2e B (F8): added "A worked example" to Usage (prepare psf/requests v2.31.0, run --via claude,
  watch) with shortened JSON results taken from the code's real field names. Decision: no flow
  diagram for it. The path is linear (prepare → run → watch) and the prose already says it, so a
  diagram would be trivia.
- e2e D (F14): added one reason per `prepare` choice (fetching only the revision, the `main`
  branch, no `d2`, committing before `task open`, binding the task to the root Module), and what a
  failed step leaves behind (`command_failed`, the partial directory is kept, a later `prepare`
  refuses it with `project_exists`). Also covered Distribution's failure reaction and Execution's
  (`watch` leaves out a run with no run progress file) under "Around it". Decision: this describes
  what the code already does (it cleans nothing up, as the brief stated), and the `d2` reason is
  factual (d2 only renders docsite diagrams and the installer downloads it). Neither changes a
  promise, so I did not escalate. Worded the `watch` sentence without "run directory", which the
  glossary defines as a worker run's directory.
- dogfood-scenarios A (F5): split into scenarios-apply + unknown-scenario, client +
  client-install, fault + fault-reinjected, each with its own test. Found a gap in the old test:
  the shipped scenario names `"client": "claude"`, so the "scenario without a client" GIVEN was
  never exercised. The new client test builds a scenario with no client (SCENARIOS patched to a
  temporary directory). Decision: no separate scenario for the `--client` override. The verdict
  called it optional, and testing it would need a full `prepare` (network clones). Usage already
  states it. scenarios-apply now says "this checkout's working tree", as the verdict asked.
- dogfood-scenarios C (F6), headless-sessions C (F11), swe-bench-cases C (F13): added
  `d2 illustrative` diagrams. The F11 prerequisite F3b (wait_exceeded writes session.json first)
  and the F13 prerequisite F4 (repair-specs split) are both on main, and the diagrams follow them.
  All three were rendered with d2 and checked by eye. The wake loop diagram follows the code's
  order: it waits even on the last round and then ends `rounds_exhausted`.
- Only files of this task's Modules changed. Pre-existing and not touched: ruff SIM117 in
  tests/concorde/e2e/test_cases.py.
- Commits: 48c44986 (trust split), 38c6a714 (worked example, reasons, failure reactions),
  1c710965 (dogfood splits), 14311650 (diagrams). This corrects the placeholder "6ee…" above.
- Verification: tests/concorde/e2e 27 passed; spec-validation 0 errors, 0 warnings; build --check clean.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES. Sent back for small inaccuracies: the reason for the `main`
  branch name, the "not there yet" wording for a run without a run progress file, three edges of
  the dogfood diagram, and a GIVEN clause in `client` that no outcome uses.
- Decision (mine): keep F14's statement that `prepare` leaves a partial project directory. The
  handover the developer gave names that behaviour as what to state; the verdict had asked for
  the developer's confirmation, so the statement and the session's rationale ("the failure is
  the finding") are reported to the developer in the final report.

## 2026-09-29 — Fixes after the main agent's review

The main agent asked for four inaccuracies to be fixed:
1. The `main` branch reason: now gives the branch reason (a merge refuses a detached `HEAD`) and,
   as a separate point, the name reason (`grade --ref` defaults to `main`, scripts/e2e/e2e.py).
2. The `watch` sentence now covers both cases: a runner that has not written its run progress
   file yet, and one that died before writing it (that run stays out of the list).
3. The dogfood diagram: the evaluation.json node now says it is written by `evaluate` and after
   each `run`. The edges into it are labelled "evaluation:" instead of "evaluate:". Added an edge
   from `concorde/` to evaluation.json (its head and status) and one from `concorde/` to
   dogfood.json (the fault commit). Re-rendered with d2 and checked.
4. `scenario.dogfood-scenarios.client`: took the option of dropping the fault clause from the
   GIVEN. Decision: the check that the first scenario's fault covers both backends' write checks
   now lives in the scenarios-apply test, as a check of the shipped scenario that Usage
   describes. It was not deleted, so no coverage is lost.
Verification: tests/concorde/e2e 27 passed; spec-validation 0/0; build --check clean.

## Closed: merged, 2026-09-28T20:01:34Z

## 2026-09-29 — The developer confirmed F14

- The developer chose to keep `prepare` leaving the partial project directory after a failed step
  (option A), as the merged e2e/module.md states.
