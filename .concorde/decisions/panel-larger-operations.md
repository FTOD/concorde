# Decision log: panel-larger-operations

Goal: Finish the 2026-09-28 panel review's larger items for Operations and its five Operations: add the flow and state diagrams the review asked for, skipping those the prose already makes plain

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

**module.operations**
- C · F8: the standard worker sequence diagram.

**module.adoption**
- C · F15: the adoption path diagram.

**module.code-review**
- C · F11: the eight steps diagram.

**module.implementation**
- C · F13: the implement loop and its exits diagram.

**module.specification**
- C · F9: the repair loop and the relaunch diagram.

**module.understanding**
- C · F14: statuses and branches diagram.

### Verdict text for each item (from the review's verification agents)

#### module.operations

##### F8 LARGER — Flow diagram of the standard worker sequence
Real and advisory. Add a `d2 illustrative` flow next to the (now corrected) workers.md step table. Lanes: step (freeze grant, settle model) and Workers (settings/brief/pending, launch, audit, ok-and-clean gate, optional checks, bounded resume loop back to launch, record). Terminals: ok, blocked and failed. Keep the conditions in prose. This is a new diagram, so I did not add it.



#### module.adoption

##### F15 LARGER — no activity view of the adoption path
The finding is real and is a new diagram. Next to the three commands in Usage, add a
`d2 illustrative` view: survey → inspect proposal (answers → survey rerun) → scaffold →
code_to_spec per Module, providers first → answered reruns → `implement` for deviations.



#### module.code-review

##### F11 LARGER — Process diagram for the eight-step Design
Real and advisory. Add a `d2 illustrative` flow beside the Design table. Lanes: Operation, Spec core, Check execution and Workers. Main path: grant → diff → checks → brief → reviewer → audit → basis/verdict → output. Dashed edges go to `failed` (grant, base, checks unavailable, launch/timeout, audit, unresolved basis) and to `blocked`. Show that a failing check continues to the review. This is a new diagram, so I did not add it.



#### module.implementation

##### F13 LARGER — Flow diagram for the implement loop and exits
This is a request for a new `d2 illustrative` activity view next to the step table: main path, resume loop, and the audit-violation, blocked/failed and rounds-exhausted exits converging on steps 8–10. It is new diagram work. The prose and table corrections under F4, F8 and F20 make the current text consistent in the meantime.



#### module.specification

##### F9 LARGER — Show both loops together (diagram)
The main request, a `d2 illustrative` flow next to the step table showing the repair loop, the 5a relaunch and the exits, is new diagram work. I only fixed the contradictory parts. Step 7's stop column now reads "a new error left after the last repair round of a worker that ended `ok`". The Design says repair rounds follow only rounds where the worker ended `ok` with a clean audit, that the limit is two per worker launch, and that the second worker gets its own two. Still open: add the flow diagram and consider putting the repair loop into the table.



#### module.understanding

##### F14 LARGER — Illustrative status/branching view in Usage
This is real: the reader must track run status and sufficiency across three paragraphs. The fix is a `d2 illustrative` view beside the status paragraph: run → worker assessment (`blocked` if unassessable) → host checks (launch/timeout/audit, unknown Module, inconsistency → `failed`) → `ok`, branching to sufficient+plan, sufficient without plan, and insufficient → gaps → `specify` → reassess. That is a new diagram, not a few sentences. Its content depends on the F2 decision (whether a sufficient plan may start with `specify`), so it is best drawn after F2 is settled.


## Task session log (2026-09-29)

Each item was checked against the current Specs and code (`src/concorde/harness/workers.py`
round loop, `src/concorde/specification/operation.py`, `src/concorde/implementation/operation.py`)
before drawing. Every diagram is a `d2 illustrative` block, rendered locally with `d2 --layout elk`
(the docsite's layout) to check syntax and legibility; back edges are written `a <- b` so ELK keeps
the forward order top to bottom.

- **module.operations · F8 — done.** Flow added in `workers.md` after the outcome→status table,
  with lanes "Provider step" (steps 1–2) and "Workers" (3–8), the resume loop (step 7), and the
  terminals `ok`, `blocked`, `failed`. Decision: checks and the step's own validation are drawn
  as one node, because separate nodes made ELK place the back edges unreadably; the step table
  already separates them. The "ok, unless a later provider step stops the run" caveat stays in the
  table rather than in the diagram.
- **module.adoption · F15 — done.** Activity view added in Usage after the three commands: survey →
  task level inspects the proposal (answers → survey rerun) → scaffold → code_to_spec per Module →
  inspect each description (answers → code_to_spec rerun) → `implement` for deviations. The
  existing records diagram is kept and now has its own lead-in sentence. Decision: the
  "providers first, surveyed Module last" order is labelled as the brownfield workflow's, since
  Adoption itself leaves the order to the task level or a workflow (Workflows Spec states it).
- **module.code-review · F11 — skipped (diagram), wording clarified instead.** The eight steps are
  strictly linear and the table's "Stops when" column already gives every exit with its status; a
  flow would repeat the table. The one point the review said a diagram should show — a failing
  check continues to the review — is now stated in step 3's stop column ("a check that fails goes
  on to the reviewer"), restating the existing prose ("a failing check is for the reviewer to
  interpret"); no promise changed.
- **module.implementation · F13 — done.** Flow added after the implement step table: main path,
  the step-7 resume loop, and the exits (pre-create failure, launch error/timeout, audit violation,
  worker blocked/failed, rounds used up) converging on steps 8–10; a grant failure ends with no
  worker launched, which matches `implement_step` returning before steps 8–9 when no worker run
  exists.
- **module.specification · F9 — done, and the repair loop put into the table.** Flow added after
  the step table showing the per-launch repair loop (validate after each `ok`/clean round, at most
  two resumes per launch), the single 5a relaunch, the refusal exit and the audit-violation exit
  that skips steps 6–8. Following the verdict's "consider putting the repair loop into the table",
  step 4's row now names the repair rounds, worded like code_to_spec's step 5; it restates the
  Design prose, no promise changed.
- **module.understanding · F14 — done.** Status/branch view added in Usage after the status
  paragraph. The F2 dependency is settled in the current text ("the new promises become the plan's
  `specify` steps and are never Spec gaps"), so the sufficient-with-plan branch says the plan may
  start with `specify`.

Observation outside this task (not acted on): `workers.md`'s error table gives `checks_failed` the
reason `decision`, while Workers' own link in `harness/workers.py` uses `exhausted`; the table may
describe the Operation's link rather than Workers', so it may be consistent. Reported to the main
agent for a check, not changed.

Validation: `spec-validation` 0 errors, 0 warnings; `build --check` no differences.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES; sent back for diagram precision: specification's step 7→8
  edge showing only `blocked`; workers.md's checks→record edge hiding the checks_failed exit;
  adoption's "one Module at a time" narrowing Usage's `--modules` list; launch error drawn after
  the audit; specification's end-of-run node inside the round loop and missing step-4 exits.
  The session's checks_failed observation is not a mismatch (Operation's link `decision`,
  Workers' link `exhausted`).

## Fixes after the main agent's review (2026-09-29)

Checked each against `src/concorde/harness/workers.py` (launch at 590–603 returns before the audit;
timeout, limit reached and invalid result are decided after it; `checks_failed` at 778–797;
deletions in `_finalize`, the record in `finish`) and re-rendered each diagram with d2.

1. specification: step 7 now has a normal edge "no new error: the worker's status" and a separate
   dashed edge "a new error left after an ok worker: blocked".
2. workers.md: "a check still fails, rounds used up" is its own dashed exit into the run record;
   the other label now says "validation rounds used up", and the `failed` terminal lists the exits
   it collects, checks still failing first.
3. adoption: "one Module at a time" moved into the parenthesis that attributes the order to the
   brownfield workflow, so the node no longer narrows `--modules <id>[,<id>…]`.
4. workers.md: the launch error is an exit of the launch node; the audit edge lists violation,
   timeout, limit reached, invalid result, worker blocked or failed.
5. specification: the loop's step 5 is now "Audit against the grant"; proposed deletions and the
   run record are one node after the loop ("5 Proposed deletions after a clean audit, run
   record"), which the 5a branch and step 6 leave from. Step-4 exits are named: launch error from
   the launch node, and timeout, limit reached and invalid result from the audit.

Decision (not asked): the implementation diagram had the same imprecision as item 4 ("launch error
or timeout" on the launch node), so it now matches the code: the launch error comes from the launch
node, and timeout, limit reached and invalid result come after the audit.

The main agent confirmed the `checks_failed` reason is not a mismatch (the table gives the
Operation's link); no change.

## Closed: merged, 2026-09-28T20:00:26Z
