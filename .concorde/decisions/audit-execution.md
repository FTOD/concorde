# Decision log: audit-execution

Goal: Audit the restyled requirements against Protocol 16.4's requirement rules with the general worker, and fix every drift from their original meaning: Execution, Worker harness and Spec tooling


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

module.execution,module.checks,module.commands,module.operations,module.worker-harness,module.harness,module.workers,module.spec-tooling,module.spec,module.views,module.spec-mcp

## Task session (2026-10-05)

- **Scope widened to every requirement of the task's Modules, wherever it is defined.** Only five
  of the eleven Modules have a `requirements.md` (execution, operations, spec, views, spec-mcp).
  Checks, Workers and Spec define their requirements in other documents as well
  (`execution/checks/{boundary,service,timing}.md`, `worker-harness/workers/{launch,pi}.md`,
  `spec-tooling/spec/errors.md`), and these were restyled by the same tasks. The brief lists
  these Modules, so it means them. Harness, Commands, Worker harness and Spec tooling define no
  requirement, so nothing of theirs is audited. Reason: the goal is to audit "the restyled
  requirements" of these Modules; leaving 109 restyled requirements out would leave the goal half
  done.
- **Baseline.** `git log d4423f70.. --` on each audited file shows only commits of the
  `restyle-execution` and `restyle-spec-tooling` tasks, so the whole text at d4423f70 is the
  baseline; no change since is on purpose.
- **Run plan.** Seven sequential `general --type review-spec --read-only` runs, one per Module:
  execution, operations, checks, workers, spec (requirements.md and errors.md), views, spec-mcp.
  Instruction files live under the job's tmp directory, outside the worktree.
- **Audit run 1, module.execution** (`r-20261005T055438-general-21306016`, 3 min 40 s, `ok`):
  worker reported 7 drifts (3 blocking); reviewer verdict `changes_required` with 4 findings
  (three dropped "so" links in explanations, one added actor in an explanation). The review's
  `changes_required` judges the audit answer, not the Specs; I take worker and reviewer output
  as claims and check each myself before acting.
- **Audit runs 2–3** (`r-20261005T055841-general-425d1160` operations, 52 s, review `accepted`;
  `r-20261005T055933-general-be9a448a` checks, 82 s, review `accepted`). Both match my own pass.
- **Execution findings judged.** Confirmed: binding-read-only (split), one-result (moved-out),
  error-chain (subject-changed, blocking), output-checked (condition-misplaced: "before writing"
  now limited the failing results), workspace-wait-continues (split), unbound-read-only
  (subject-changed: the runner added, blocking), detached-same-run (split), and the reviewer's
  three dropped "so" links (reads-no-spec, detach-failed-ends-runner, run-lock-held).
  Rejected: reviewer F4 on trace-write-reported — the explanation names the runner, which already
  bears that requirement's obligation, so no new actor enters the promise. Not fixed either:
  error-detail and waiting-progress, whose lists hold the objects of one obligation, not
  separate rules.
- **Operations/Checks confirmed:** model-work-only (split); fresh-scratch, measured-input-unchanged,
  timing-passive, timing-unknown (each subject-changed, blocking). Each fix restores the original
  subject, also where it is passive, since 16.4 says choosing an actor changes the promise.
- Committed 7ced4725 (spec-validation: 0 errors, only the 12 earlier warnings).
- **Audit runs 4–7** (`r-20261005T060211-general-b85a706f` workers, 3 min 21 s, review `accepted`;
  `r-20261005T060532-general-19aad399` spec, 2 min 57 s, review `changes_required` with 2
  findings; `r-20261005T060829-general-4be272ef` views, 1 min 3 s, `accepted`, no drift;
  `r-20261005T060933-general-c4f8640c` spec-mcp, 44 s, `accepted`, no drift).
- **Workers judged.** Confirmed 10: malformed-grant, write-allowlist, working-directory-not-denied,
  latest-session, error-chain (moved-out); malformed-grant-named, working-directory,
  model-map-named, model-map-entry, refusal-reason (subject-changed, blocking). Rejected:
  always-recorded — the moved clause ("a run whose node could not be written still has its
  runtime directory removed") is a separate fact without SHALL, already required by
  req.workers.runtime-removed; the obligation itself stays whole.
- **Spec judged.** Confirmed 5: digest-per-assessment and init-explicit-envelope (link-dropped),
  registry-mirror-only and installation-follows-record (split), init-installation-apart
  (condition-misplaced: the amended-files exception limits the files, not the whole obligation).
  Rejected 2, with the reviewer: transaction-restore-reported and transaction-system-errors — the
  lists give the properties of the one required error, not separate rules. The audit missed 2
  that I confirmed: transaction-all-or-nothing ("while the process runs" became "during
  execution", losing the contrast with a killed process) and no-owner-imports (the limit "for a
  type of the spec part's own Modules" was moved away from the registration route it limits).
- **Own scan** (keyword counts, action lists after SHALL, fronted "Only", lost link words) found
  nothing further: every lost "so"/"since"/"unless" became "therefore", "except" or a condition
  list, and every fronted "Only" limits the whole obligation.
- Committed 640b3ba3. Started a verification run of the general worker over the 32 repaired
  requirements against their originals, since hand fixes had no reviewer.
- **Verification run** `r-20261005T061154-general-941e5783` (1 min 35 s, `ok`): 32 repaired
  requirements audited against d4423f70, 0 drift, review `accepted`.
- `build --check` success; `spec-validation` 0 errors; full pytest 1270 passed, 5 skipped.
- **The general Operation behaved as specified in all 8 runs**: read-only grants, 0 changed
  files and clean audits, the instruction copied and digested, the verdict in `review.verdict`.
  Durations ranged from 44 s to 3 min 40 s. Only the worker run node's `usage` is null, because
  the figures sit on the round nodes, as Tracing specifies. The worker's stderr carries pi's
  benign "No project session found … creating a new session". No Issue recorded.

## Report 1 to the main agent (concorde-f8), 2026-10-05T06:30:29Z

audit-execution delivered: 2a152de6 (`concorde: deliver audit-execution`) on concorde/audit-execution. Fix commits: 7ced4725 (Execution, Operations, Checks) and 640b3ba3 (Workers, Spec core). Checks: spec-validation 0 errors (only the 12 earlier warnings), build --check ok, full pytest 1270 passed / 5 skipped, task-validation ready, delivery ok.

REQUIREMENTS AUDITED (225). The scope was widened, a decision I logged: Checks, Workers and Spec also keep requirements outside requirements.md, which the same restyle rewrote. Files: execution/requirements.md (44), operations/requirements.md (6), checks/{boundary,service,timing}.md (18), workers/{launch,pi}.md (70), spec/requirements.md + errors.md (57), views/requirements.md (36), spec-mcp/requirements.md (8). Harness, Commands, Worker harness and Spec tooling define no requirement. Baseline: every file at d4423f70; no change since was on purpose (only restyle-execution and restyle-spec-tooling commits).

CONFIRMED AND FIXED (32 requirements). Each fix restores the original meaning, mostly the original sentence; a fronted condition stays only where it limits the whole obligation:
- split (8): execution binding-read-only, workspace-wait-continues, detached-same-run; operations model-work-only; spec registry-mirror-only, installation-follows-record (both had "SHALL do the following:" + action lists).
- moved-out (6): execution one-result (the "including when refused/fails/cancelled" clause); workers malformed-grant, write-allowlist, working-directory-not-denied, latest-session, error-chain.
- condition-misplaced (2): execution output-checked ("Before writing results failing…" limited the wrong action); spec init-installation-apart (the amended-files exception was fronted before the subject).
- subject-changed (12, all blocking): execution error-chain (the run result made an actor), unbound-read-only (the runner added); checks fresh-scratch (the check runner), measured-input-unchanged (the service), timing-passive and timing-unknown (the "timing recorder"); workers malformed-grant-named, model-map-named, model-map-entry, refusal-reason (the host or configuration reader added), working-directory (the worker made to bear it). The original subjects are restored, passive ones included, since 16.4 says choosing an actor changes the promise.
- link-dropped (5): execution reads-no-spec, detach-failed-ends-runner, run-lock-held ("so" in explanations); spec digest-per-assessment ("so"), init-explicit-envelope (the reason "any caller can compute the digest").
- other (2, found by me, missed by the audit): spec transaction-all-or-nothing ("while the process runs" had become "during execution"); no-owner-imports (the limit "for a type of the spec part's own Modules" was moved away from the registration route).

REJECTED (6 audit findings):
- execution trace-write-reported (reviewer: "added actor"): the explanation names the runner, which already bears that requirement's SHALL.
- workers always-recorded (moved-out): the moved clause is a separate fact without SHALL, already required by req.workers.runtime-removed.
- spec transaction-restore-reported and transaction-system-errors (split): the lists give properties of the one required error, not rules. The reviewer took the same view.
- my own candidates execution error-detail and waiting-progress: their lists hold the objects of one obligation.

MISSED BY THE AUDIT: only the two "other" Spec drifts above. My mechanical scan (SHALL counts, action lists after SHALL, fronted "Only", lost link words) found nothing further. Views and Spec MCP: no drift, by both the audit and my own pass.

GENERAL WORKER: 8 runs, all `ok`, one at a time, on pi gpt-6.1-sol at reasoning medium. They were 7 audits (execution 3m40s, operations 52s, checks 82s, workers 3m21s, spec 2m57s, views 63s, spec-mcp 44s) and 1 verification of the 32 fixes (1m35s: 0 drift, review accepted). Review verdicts: accepted 5, changes_required 2. Execution got 4 reviewer findings: 3 sound "so" links I adopted and 1 rejected. Spec got 2 sound false-positive calls. The worker's quality was high: its findings matched my independent pass closely, with quoted originals and sensible repairs. No misbehaviour: read-only grants, 0 changed files, clean audits, the instruction kept and digested. Notes, none a defect, so no Issue on module.general-work: the run summary is the runner's generic "general finished for …" and does not name the verdict (it is in output.review.verdict); usage is null on the worker run node because the figures sit on the round nodes, as Tracing specifies; pi's stderr warns "No project session found … creating a new session", which is benign.

DECISIONS I MADE: the scope widening, the baseline, every confirm and reject above, the hand fixes plus a general verification run instead of `general --type specify`, and leaving the pre-existing second SHALL in req.spec.typed-closed as it is (it was so at d4423f70, so it is no drift). All are in the decision log. Nothing open; no escalation; no Issues resolved or opened.

## Closed: merged, 2026-10-05T06:31:01Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 2a152de6dc7ef391091e8ee429fe14832a018fc3 into main and closed it as merged. Nobody answers a report after that.
