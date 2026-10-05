# Decision log: audit-method

Goal: Audit the restyled requirements against Protocol 16.4's requirement rules with the general worker, and fix every drift from their original meaning: Method


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

module.method,module.adoption,module.code-review,module.delivery,module.implementation,module.scaffold,module.specification,module.spec-review,module.understanding,module.validation,module.general-work

## Task session (2026-10-05)

- Decision: baseline is d4423f70 for all ten Method requirements files that existed then. `git log
  d4423f70..` shows only the restyle-method commits (rewrite + "meaning review found loosened"
  repairs) on each, so no intentional meaning change is excluded from the baseline.
- Decision: `specs/concorde/method/general-work/requirements.md` did not exist at d4423f70 (created
  by `general-worker`, 62ab8f12, after the restyle). It has no original to drift from, so I check
  it by hand against the 16.4 requirement rules instead of with a general run.
- Decision: one instruction file per Module, generated by a script into the job's tmp directory
  (outside the worktree). Each holds the five drift patterns plus "other", the 16.4 sections "One
  fact in each sentence", "The condition before the statement", "The links between facts", "The
  actor and the active voice" and "Requirements", the original file at d4423f70, and asks for one
  finding block per requirement id (pattern, blocking, original, current, why, repair) plus a
  no-drift list.

### Audit runs (2026-10-05, `general --type review-spec --read-only`, one per Module, sequential)

All ten runs ended `ok` (56 s to 172 s each, 05:54 to 06:13 UTC). Both workers ran on pi
`gpt-6.1-sol`, with grants of only `ro`/`names` levels, read-only tools only, and an empty observed
change. Verdicts: `accepted` for eight. `changes_required` for module.spec-review and
module.understanding: those are the reviewers' findings on the audit answers, not run failures.
- spec-review F1 (blocking): the worker missed that `req.spec-review.blank-earlier` also gave the
  passive checking clause an actor. Accepted: the fix restores the passive clause.
- understanding F1 (blocking): `req.understanding.plan-review-verdict` changed only in form. Accepted:
  I reject that finding and leave the requirement unchanged.
- delivery F1 (advisory): the worker's answer said "18 requirements" while there are 17. A count slip
  only.

Worker findings (29): method 2, adoption 2, code-review 6, delivery 7, implementation 2, scaffold 4,
specification 0, spec-review 3, understanding 3, validation 0. I checked each against
`git show d4423f70:<file>`. I confirmed 28 and rejected 1 (plan-review-verdict, form only).

Requirements the audit missed, found by my own pass (diff per requirement, a link-word count, a
SHALL count and a grep for rule-list openings): `req.method.glossary-by-entry` ("so that" became
"Thus"), `req.adoption.no-bash` ("SHALL NOT be given" became "SHALL NOT receive", which moves the
obligation onto the worker), `req.adoption.own-errors-count` ("whether or not the baseline had it"
fronted ahead of its referent), `req.adoption.tests-linked-by-host` ("so" dropped),
`req.code-review.module-scope` (properties of the launched reviewer relabelled as "conditions"),
`req.code-review.spec-challenge` (one finding described as a property list), `req.scaffold.stub-unspecified`
and `req.scaffold.step-output` (part limits fronted, and "so" dropped), `req.understanding.plan-review-read-only`
(list items moved "no configured check" onto another subject), `req.validation.read-only` (object limit
fronted) and `req.validation.step-output` ("so that" became "therefore"). Not counted as drift: the
equivalent rewordings such as two-case lists (`req.method.workspace-specs`, `req.method.grant-as-data`,
`req.implementation.worker-status`) and conditions listed under one statement.

- Decision: each fix restores the original d4423f70 statement in one SHALL sentence (16.4 sets no
  length bound on it) and keeps the restyle's later prose where that prose kept its links. Where a
  statement has three or more conditions, they stay as a list under a statement that ends with a
  colon (`req.delivery.commit-verified`, `req.code-review.evidence-resolves`). The fixes were made
  by hand, not through `general --type specify`, because each one is a near-verbatim restoration
  of known text.
- Decision: `req.general-work.review-material` folds "The worker's answer is given too, marked as a
  claim to check" into its statement. That fact belongs to the one obligation. This is a 16.4
  conformance edit with no meaning change, inside module.general-work, which this task owns.
- No problem of the `general` Operation was observed: grant, read-only lowering, instruction copy and
  digest, brief order, reviewer separation and verdict derivation all behaved as specified. The
  run result's top-level `worker` is the reviewer's result, which Execution's contract specifies as
  "the last worker result". Nothing was recorded as an Issue.

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

### After the main agent's note (2026-10-05)

- Searched for `### req.`: no requirement of my Modules lives outside their `requirements.md`.
- Applying "restore the original subject, even a passive one": `req.spec-review.host-verdict` and
  `req.specification.observed-facts` had become "The Operation SHALL …", although their original
  subjects were the verdict and the Spec change's facts ("SHALL be derived/computed by the
  Operation"). Both are restored (commit after the first delivery c0c01365). No other statement
  changed its subject. Every other statement whose wording before SHALL differs only puts a
  condition of the whole obligation first.
- Applying "a list of the objects or properties of one obligation is fine": I classify my extra
  findings `req.code-review.module-scope` and `req.code-review.spec-challenge` (property lists) as
  advisory, not splits. I keep their restorations, since the restored text is the original wording
  and follows 16.4.
- The first delivery c0c01365 came before this note. I validate and deliver again.

## Report 1 to the main agent (concorde-f8), 2026-10-05T06:48:20Z

audit-method delivered: 1162c6d6 (concorde: deliver audit-method) on concorde/audit-method; earlier delivery c0c01365 was superseded after your note. Commits: 9bf29d7e (fixes), 0a45c47d (two passive subjects).

Audited: every `### req.` of the 11 Modules (152 requirements; none live outside requirements.md). Ten files against d4423f70; no intentional change since (only restyle-method commits). general-work/requirements.md did not exist at d4423f70, so I checked it by hand against 16.4 only.

General worker audit (10 runs, review-spec --read-only, sequential): all ok, 56-172 s each (~19 min total). Verdicts: 8 accepted, 2 changes_required (reviewer findings on the audit answer, both valid). Grants were ro/names only, tools read-only, observed change empty, instruction copied with digest, brief order correct. No misbehaviour of `general`, so no Issue. Note: run result's top-level `worker` is the reviewer's result, as Execution's contract specifies ("last worker result"). The worker's blocking labels were inconsistent across runs (splits "yes" in delivery/code-review, "no" in scaffold/spec-review).

Findings by pattern (worker, 29): split 21, clause-moved-out 6 (with split), subject-changed 2, link-dropped 2, other 0. Confirmed 28. Rejected 1: req.understanding.plan-review-verdict, form only (the reviewer said so too). Reviewer added 1 confirmed: req.spec-review.blank-earlier also had its passive checking clause given an actor.

Missed by the audit, found by my own pass (diff, link-word count, SHALL count, rule-list grep): method.glossary-by-entry ("so that" -> "Thus"), adoption.no-bash ("be given" -> "receive", subject), adoption.own-errors-count (limit fronted), adoption.tests-linked-by-host ("so" dropped), code-review.module-scope and code-review.spec-challenge (property lists, advisory), scaffold.stub-unspecified and scaffold.step-output (part limits fronted, "so" dropped), understanding.plan-review-read-only (items changed subject), validation.read-only (object limit fronted), validation.step-output ("so that" -> "therefore"), and after your note spec-review.host-verdict and specification.observed-facts (passive subject replaced by "The Operation").

Fixes: 41 requirements restored to their d4423f70 statement in one SHALL sentence, conditions back in it, links restored. Lists remain only for 3+ conditions under one statement ending in a colon (delivery.commit-verified, code-review.evidence-resolves). The restyle's later prose was kept where it kept its links. Plus general-work.review-material: the "worker's answer, marked as a claim" folded into its statement (16.4 conformance, no meaning change). Fixes made by hand, not via general --type specify, since each is a near-verbatim restoration.

Verification: spec-validation 0 errors, 0 warnings in Method (12 elsewhere, unchanged); build --check clean; no test asserts Method requirement text; full pytest 1270 passed, 5 skipped; task-validation ready; delivery ok.

Decisions taken alone (all in the decision log): baseline d4423f70 for all ten files; general-work checked by hand; instruction files kept in the job tmp dir; hand fixes; module-scope and spec-challenge restorations kept although property lists are advisory. Open: nothing. No Issues resolved or recorded.

## Report 2 to the main agent (concorde-f8), 2026-10-05T06:48:36Z

Correction to report 1: the audit covered 177 requirements, not 152. The worker's 29 findings by pattern (one finding can carry several patterns): split 23, clause-moved-out 9, link-dropped 3, subject-changed 2, other 0. Everything else in report 1 stands.

## Closed: merged, 2026-10-05T06:49:01Z

The merge answered report(s) 1, 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 1162c6d6d9f985862c9cd10dee8e9d8755c548ef into main and closed it as merged. Nobody answers a report after that.
