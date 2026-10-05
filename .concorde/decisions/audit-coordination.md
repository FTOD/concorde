# Decision log: audit-coordination

Goal: Audit the restyled requirements against Protocol 16.4's requirement rules with the general worker, and fix every drift from their original meaning: Coordination, root, E2E and Dogfooding


## Task brief (main agent, 2026-10-05)

### Background

Six restyle tasks rewrote every Spec with raw `pi -p` on 2026-10-04. Their base commit was
d4423f70; read `.concorde/decisions/restyle-*.md`. An experiment then showed that some of their
rewrites drift in ways the reviews of that time accepted as compliant. The cause was the Sentence
style rules of that time, applied to requirements. Protocol 16.4 (task `style-requirements`) now
fixes this. `protocol/style.md` has the rules "Requirements" and "The links between facts", and
`protocol/evaluation.md` names five drifts:

1. one obligation split into a list of separate rules;
2. a condition, exception or failure clause moved out of the SHALL statement;
3. a condition moved away from what it limits, for example a fronted "Only after X, …";
4. a changed or added subject, an actor the original did not name;
5. a dropped link word (since, because, so that, only, each, every, never, at most, unless and
   the like).

A drift that changes what a requirement requires, or who bears it, is blocking.

### The developer's decision (2026-10-05)

Audit the already-rewritten requirements against the new rules, then fix what the audit finds.

### Scope

Every requirement in the `requirements.md` files of your Modules, listed below. Leave scenarios
and contracts out, unless a requirement fix forces a matching wording change there.

### How

1. **Use the new general worker for the audit.** Run `concorde run general --type review-spec
   --read-only --modules <module> --instruction-file <file>` from your task worktree, one run per
   Module's requirements.md. This one Operation runs the worker and the independent reviewer on
   gpt-6.1-sol at reasoning medium, isolated by the harness.
   - Only one run per workspace at a time, so the runs are sequential within your task.
   - The instruction file must give the five drift patterns, the 16.4 rules, and the ORIGINAL
     text of that requirements.md at d4423f70 (`git show d4423f70:<path>`). The worker cannot
     read Git history.
   - Ask for one finding per requirement id, giving the pattern, the original wording, the current
     wording, and whether it is blocking.
   - Keep the instruction file outside tracked paths, or delete it before you commit.
2. **The baseline is the original meaning at d4423f70**, apart from changes made on purpose
   since then. Check `git log d4423f70.. -- <file>`. For example, `fix-status-locks` changed
   `req.tasks.derived-state`, and `general-worker` changed the Operations Spec. Those are not
   drift.
3. **Check every finding yourself before you act on it.** Worker and reviewer output are claims.
   Also scan for what the audit may miss: statements followed by rule lists, "Only after"
   openings, and requirements whose SHALL count changed.
4. **Fix each confirmed drift**, either by hand or with `concorde run general --type specify
   --instruction-file <file>`, which has its own reviewer. Each fix restores the original meaning
   in a form that follows 16.4. One SHALL sentence may now be long, so prefer restoring the
   original obligation in one statement over a split.
5. **Watch every run closely**, including its result, its host evidence and the trace. This is
   the general worker's first real use. If the general Operation itself misbehaves:
   - Record it as an Issue on `module.general-work`.
   - Tell the main agent in your report.
   - Fix it only if your task owns that Module, which only `audit-method` does.

### Verification and report

Run spec-validation (0 errors), build --check and the tests that assert requirement text, then
the full pytest once. Commit verified steps, then run `task-validation` and `delivery`. Use at most
2 pi gateway lanes in total; the general runs already go one at a time.

In your report, give:

- the requirements audited;
- the findings by pattern, split into confirmed and rejected, with the reason for each rejection;
- the fixes made;
- the requirements you found the audit missed;
- how the general worker behaved (duration, verdicts and any problem).

Record every decision you take without the developer, and every non-`ok` result, in this log.

### Your Modules

module.coordination,module.tasks,module.main-session,module.task-session,module.concorde,module.e2e,module.headless-sessions,module.dogfood-scenarios,module.swe-bench-cases,module.dogfooding

## Task session (2026-10-05)

- **Scope.** module.coordination has no requirements.md, so nothing of it is audited. The
  requirements of module.dogfood-scenarios (`specs/concorde/e2e/dogfood/requirements.md`) and
  module.swe-bench-cases (`specs/concorde/e2e/cases/requirements.md`) are byte-identical to d4423f70
  (`git diff d4423f70` is empty), so they cannot have drifted and get no general run. Seven files
  remain: root (23 requirements), tasks (61), main-session (120), task-session (11), e2e (16),
  headless-sessions (10), dogfooding (18).
- **Instruction files.** One per file, generated by a script into the ignored `.generated/audit/`
  of the task worktree (the session boundary refuses writes to the job tmp folder). Each gives the
  five drift patterns, a pattern 0 for any other meaning change, the 16.4 sections Requirements,
  The condition before the statement, The links between facts and The actor and the active voice,
  the answer format (one finding per drifted requirement id with pattern, blocking/advisory,
  original and current wording, proposed repair, plus a clean list of every other id) and the
  whole original file at d4423f70. The tasks instruction names the fix-status-locks paragraph of
  `req.tasks.derived-state` as a change made on purpose.
- **Order.** Smallest file first (task-session), to observe the general Operation on a short run
  before the long ones.
- **Non-`ok` review verdict: Tasks audit run (`r-20261005T060431-general-a33ee314`, verdict
  `changes_required`).** The run itself ended `ok`. The worker (229 s) audited up to
  `req.tasks.merge-nothing-outside`, then degenerated: findings 13 and 14 claim that
  `req.tasks.refusal-detail` is a renamed id, in self-contradicting text, and the Clean list is
  missing. The reviewer (88 s) caught it (F1, F2) and named six drifts the worker omitted (F3 to
  F8: merge-exact-commit, deliver-convention, main-named, report-answered, end-settles-reports,
  old-records-read). This is a model failure on a long answer, not a fault of the general
  Operation, whose review worked as specified. Decision: re-run the Tasks audit in two halves
  (Records and Lifecycle; Merging to the end), with the same instruction plus a range note, so
  that each answer stays short.
- **Tasks re-run.** Part A (`req.tasks.primary-records` to `req.tasks.close-ends-merge-attempt`,
  198 s) ended `accepted` with 4 advisory findings. Part B (`req.tasks.merge-exact-commit` to the
  end, 241 s) ended `changes_required`: its 14 findings are right, and the reviewer's one blocking
  finding is an omission (`req.tasks.escalation-kept`, a split into two cases), which I accept. My
  instructions miscounted the ranges (29 and 32; they are 28 and 33); both reviewers noted it and
  both workers covered the real ranges.
- **Every finding checked by hand against `git diff --word-diff d4423f70`.** I had read all seven
  diffs before the results arrived. Confirmed: every finding of the eight usable runs (5 + 1 + 4 +
  3 + 6 + 10 + 4 + 15 = 48). Rejected: only findings 13 and 14 of the first Tasks run (a renamed
  `req.tasks.refusal-detail` that does not exist). Severity: I treat `req.task-session.removed` and
  `req.e2e.user-setup` as blocking although the worker called them advisory, since their statements
  alone lost a limit (`whose transcript it kept`) or became two obligations (`SHALL` and
  `SHALL NOT`). The repair is the same either way.
- **Missed by the audit, found by my scan (11, all advisory, all fixed):**
  `req.task-session.recorded` (fronted "Only after"), `req.e2e.headless-granted` (the means
  `--allowedTools` fronted as if a condition), `req.e2e.owners-deadline` ("by then" fronted before
  what it refers to), `req.concorde.worker-program` ("one of these programs"),
  `req.concorde.halves-apart` (the bearers moved into a list after the obligation),
  `req.concorde.operations-are-ai` ("each of its runs" lost, the exception fronted),
  `req.tasks.worktree-ignored` (fronted "Unless" whose "its" precedes "a task"),
  `req.tasks.one-worktree` (the branch name and place split into list items),
  `req.main-session.task-session-quiet-before-validation` ("every run of its workspace" became
  "every workspace run", and "before" doubled), `req.main-session.workflows` (the purpose "for the
  task session to start" became a fact), `req.main-session.task-session-plan-review-iterates`
  ("until" as a list item).
- **Fix method.** By hand, through one patch script, not through `general --type specify`: each fix
  restores the d4423f70 statement as one SHALL sentence. Where the original had a semicolon I
  replaced it with a comma or a list of cases (`req.main-session.issues-recovery`,
  `req.tasks.merge-recovery`, `req.tasks.old-records-read`). Explanatory paragraphs stay as
  restyled, except where a fix made a sentence redundant (`req.main-session.worktree-own-concorde`'s
  examples list, `req.main-session.project-mcp-no-wait`'s "required lock" sentence) and the dropped
  "but" of `req.tasks.shared-config-kept`. 59 fixes in 7 files. One list item of
  `req.tasks.merge-recovery` was split into two sentences after `CHK.style.sentence-length` warned
  of 41 words. Scenarios and contracts needed no matching change.

## Main agent note (2026-10-05): requirements outside requirements.md

audit-execution found that several Modules keep requirements in other documents, which the restyle
also rewrote. In its Modules these were `checks/{boundary,service,timing}.md`,
`workers/{launch,pi}.md` and `spec/errors.md`. Your scope is every requirement of your Modules,
wherever it is defined. Find them with a search for `### req.`.

Two drifts slipped past the general audit there. Both were found by the session's own pass:

- "while the process runs" had become "during execution";
- a limit had been moved away from the route it limited.

Its lessons:

- Restore the original subject, even a passive one. Choosing an actor is a Spec change.
- A list of the objects or properties of ONE obligation is fine. Only a list of separate rules is
  a split.

## Task session (2026-10-05), after the main agent's note

- **task-validation** on c8dffcde: `ok`, ready, no blocking finding.
- **Widened scope.** Outside the requirements.md files, only `specs/concorde/development.md`
  (module.concorde) holds requirements of my Modules: six, restyled by f96692c5. A general run
  (`review-spec --read-only`, 80 s, `accepted`, instruction with the main agent's list rule) found
  two advisory drifts, the same two my own pass found: `req.concorde.test-prior-compare` (the
  condition and the `null` case became two recording rules) and `req.concorde.test-counting` (the
  subtest failure and `collected` became list items). Both restored. Clean: test-evidence,
  test-fingerprints, test-prior, docs-refresh-whole (their lists enumerate recorded objects).
- **Applying the main agent's lessons to my earlier fixes.** Subjects: every fix already restored
  the original subject, passive ones included (`req.concorde.absent-part-stated`,
  `req.dogfooding.clean-primary-source`, `req.e2e.never-installed`,
  `req.main-session.project-mcp-no-wait`, `req.main-session.project-mcp-errors`). Lists: I
  reverted `req.tasks.one-worktree` to its restyled list of the branch's and worktree's
  properties, which is no split, so it leaves my "missed by the audit" list (10 remain). I keep
  `req.concorde.halves-apart` restored: its restyled list named the bearers after "...of a task:",
  where they read as the records, so the reader could not tell who bears the obligation.

## Report 1 to the main agent (concorde-f8), 2026-10-05T06:50:44Z

audit-coordination delivered: b8d92c1b (concorde: deliver audit-coordination). task-validation ok/ready, spec-validation 0 errors (12 pre-existing warnings elsewhere), build --check ok, full pytest 1270 passed / 5 skipped.

AUDITED (271 requirements): requirements.md of root (23), tasks (61), main-session (120), task-session (11), e2e (16), headless-sessions (10), dogfooding (18), plus development.md of module.concorde (6) after your note. dogfood-scenarios (3) and swe-bench-cases (4) are byte-identical to d4423f70, so no run. module.coordination has no requirements. No other file of my Modules holds `### req.`.

FINDINGS OF THE AUDIT RUNS, all checked by hand against git diff --word-diff d4423f70 (I read all diffs before the results came):
- Confirmed: 50. Split obligation / clause moved out of the statement (patterns 1, 2): 36, e.g. tasks deliver-convention, main-named, report-answered, end-settles-reports, merge-default-check, merge-workspace-locked, e2e user-setup, root detailed-errors, error-chain, one-version. Changed or added subject (4): 9, e.g. root absent-part-stated ("the part that owns the integration"), worker-models-per-worktree, e2e never-installed ("Concorde"), dogfooding clean-primary-source ("Concorde"), task-session boundary/no-sandbox/mcp-approval, main-session project-mcp-no-wait, project-mcp-errors. Condition displaced (3): 3, main-session worktree-own-concorde, dogfooding ok-run-defect, issue-system-defect. Dropped link word (5): 2, tasks shared-config-kept ("but"), merge-nothing-outside. Ten were rated blocking by the worker; I also rate task-session.removed and e2e.user-setup blocking (the statement alone lost "whose transcript it kept" / became SHALL + SHALL NOT).
- Rejected: 2, findings 13 and 14 of the first Tasks run, which claimed req.tasks.refusal-detail was a renamed id. It is not; the worker had degenerated.
- MISSED by the audit, found by my scan, all advisory, all fixed (10): task-session.recorded (fronted "Only after"), e2e.headless-granted, e2e.owners-deadline, concorde.worker-program ("one of these programs"), concorde.halves-apart (bearers listed after "...of a task:", where they read as records), concorde.operations-are-ai ("each of its runs" lost), tasks.worktree-ignored, main-session.task-session-quiet-before-validation ("every run of its workspace"), main-session.workflows (purpose became a fact), main-session.task-session-plan-review-iterates ("until" as a list item).

FIXES: 60 repairs in 8 files, by hand through one patch script (not general --type specify). Each restores the d4423f70 statement as one SHALL sentence with its original subject, passive ones included. Where the original had a semicolon, a comma or a list of cases replaced it (issues-recovery, merge-recovery, old-records-read). Explanations stay as restyled. Following your note, I reverted my fix of tasks.one-worktree (a property list of one obligation). Scenarios and contracts needed no change. Commits c8dffcde and 5ebe7cb5.

GENERAL WORKER: 10 runs, review-spec --read-only, gpt-6.1-sol medium, one at a time. Read-only grants (no rw), host observed no change in any run, worker 80 to 229 s, reviewer 31 to 88 s, runs 80 to 321 s. Verdicts: 8 accepted, 2 changes_required. (1) Tasks in one run (61 ids): after 12 good findings the worker degenerated into a fabricated renamed-id finding and dropped its Clean list; the reviewer caught it (F1, F2) and added 6 omitted drifts. I re-ran Tasks in two halves: A accepted, B changes_required for one omission (escalation-kept), which I accepted. (2) main-session (120 ids) completed in one run. Lesson: keep one run to ~60 requirements or fewer. The general Operation itself behaved as specified (review caught both problems), so no Issue on module.general-work. Usage is on the round nodes (the worker-run node's usage is null by design).

DECISIONS I took: splitting the Tasks re-run; fixing by hand; treating advisory drifts as fixes too; keeping halves-apart; instruction files kept in the ignored .generated/audit/ (the session boundary refuses the job tmp folder). All are in the decision log. Nothing open, no escalation.

## Closed: merged, 2026-10-05T06:51:07Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b8d92c1bf121fc7283c9c78fa4e127d86b33afe7 into main and closed it as merged. Nobody answers a report after that.
