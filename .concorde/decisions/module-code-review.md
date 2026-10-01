# Decision log: module-code-review

Goal: Add a Module-scope code review that judges each Module's whole code against all its Specs, may challenge a Spec that is unreasonable or unrealizable, and reports every finding with evidence as a tiered project-level Issue

## Brief (main agent, 2026-10-01)

Last of four tasks that rebuild Concorde's reviews. Already merged on main: Protocol 16.1
(`protocol/evaluation.md`, task type `review-architecture`), project-level Issues with tiers
(`suggestion` | `obvious-fix` | `preferred-fix` | `decision-needed`, tiers 2-4 blocking; Issue
tools on the project MCP server; defects of the Issue system never go through Issues), runs a task
session starts may write Issues, and `panel-architects` (spec_review and spec_panel report every
finding as a tiered Issue from the Operation's host, bound and unbound, workers receive the
Module's earlier review Issues and name the one a finding updates, the host never closes an Issue;
review memory removed). Read `specs/concorde/spec-tooling/spec-review/` and
`src/concorde/spec_review/` and follow the same model for code review.

### The developer's decisions this task carries out

1. **A Module-scope code review.** Besides today's diff-based review of a task's changes,
   `code_review` gets a mode that looks at each named Module as a whole: all of its Specs and all of
   its code (the `review-code` grant already reads the Module's implementation and the whole
   project's code), and judges whether the code is right, with one reviewer worker per Module.
   It is a mode of the existing `code_review` Operation, sharing its worker, checks and report,
   rather than a new Operation (a main agent decision; change it only with a reason).
2. **The reviewer may challenge the Spec.** When the implementation does not match the Spec, the
   reviewer says which side is wrong: an implementation error is reported as it is (a violation or
   defect); a Spec requirement that is unreasonable or cannot be realized is reported as a finding
   that challenges the Spec (a new kind, for example `spec-challenge`), with why it is
   unreasonable or unrealizable. Either way every finding has evidence: the Spec basis it is judged
   against and the code locations that show it.
3. **Every finding is a tiered Issue.** Like the Spec reviews, the Operation's host reports each
   finding through the Issues store, in bound and unbound runs, with its tier, a complete
   description and its evidence; workers receive the Module's earlier code-review Issues and name
   the one a finding updates, the host appends instead of creating; the review never fixes and
   never closes an Issue (resolved ones are listed for the task session). A finding that
   challenges the Spec is usually `decision-needed`. A failure of the Issue system while reporting
   is an error chain in the run result, never an Issue. Main agent decision: the existing
   diff-based mode follows the same model too (tiers instead of severity, findings as Issues), so
   all reviews share one model.
4. **Guidance**: the main-session guidance's "After a review" covers code review too; mention the
   new mode and when to use it (for example a whole-Module check after a large change or on an
   adopted project).

### Left to the task session

Naming of the mode and arguments, the worker brief, how evidence and basis are checked by the host,
and whether the configured checks run in the Module mode. Escalate together anything that changes
other Modules' promises (module.operations' catalog and module.main-session are bound here).

### Verification and delivery

Build, spec-validation, relevant tests and the full suite once at the end, then `task-validation`
and `delivery`. A live Module-mode run on one small Module is welcome as evidence.

## Task session decisions (2026-10-01)

1. **Mode name**: `code_review --scope change|module`, default `change` (today's diff review).
   `--scope module` reviews each named Module whole: one reviewer per Module, under the
   `review-code` grant of that Module alone, with no diff and no base (an unbound run needs only
   `--modules`). Worker id stays `worker` (no catalog change of worker ids, so existing worker
   configurations keep working).
2. **Checks in Module scope**: run, once before the reviewers, the reviewed Modules' *own*
   configured checks (not those of the Modules that use them: the change-impact reason for that
   does not apply to a whole-Module judgement, and the root Module's full suite would run on every
   Module review). Each reviewer receives its own Module's results. Change scope keeps today's
   checks (bound Modules and their users).
3. **One model for both scopes** (main agent decision 3): findings carry a tier instead of a
   severity, the verdict is `accepted | changes_required | incomplete` like Spec review, derived
   from the Issues of a blocking tier that stand (reported now or carried), the output has one entry
   per reviewed Module (outcome, context identity, summary, findings, earlier Issues). Contract
   `contract.code-review.review` goes to version 3.
4. **Finding kinds**: today's five plus `spec-challenge` (a Spec requirement the reviewer judges
   unreasonable or unrealizable, with why; the basis is the challenged passage, the locations the
   code that shows it). Every finding, of any tier, names a basis and at least one location.
5. **Host checks of evidence**: every basis resolves in the reviewed Module's Spec context (change
   scope: the bound Modules'), every location `path[:line[-line]]` names a file of the worktree (or
   a changed path of the diff, for a deleted file) and lines within it, and each finding's Module is
   a reviewed Module. A finding that fails makes its Modules' review `incomplete`
   (`unresolved_evidence`) and nothing is reported for them; the host never corrects a finding.
6. **Earlier Issues**: the open Issues owned by a reviewed Module one of whose reports `code_review`
   made (Spec review keeps its own, `spec_review`/`spec_panel`). Offered to the reviewer in both
   scopes; settled as Spec review settles them (named → appended, resolved → listed, else carried).
7. **Issue classification**: violation, missing-test, spec-challenge → `gap`/`implementation-spec-mismatch`;
   spec-gap → `gap`/`missing-contract`; defect, out-of-scope → `bug`. Evidence = each location plus
   the basis document.
8. **Code placement**: code_review gets its own reporting module (`src/concorde/code_review/`)
   using the Issue store (module.code-review now `uses` module.issues) rather than importing
   `spec_review.reporting`, which is module.spec-review's realization and not bound to this task.
   The settle logic is therefore duplicated (~40 lines); extracting a shared helper is left as a
   `suggestion`.

## Progress (task session, 2026-10-01)

- Committed e59262e0: Spec (code-review, operations catalog row, main-session), worker brief,
  Operation, reporting, tests. Build, `build --check` and spec-validation (0 warnings) pass;
  code_review, main_session, harness/workers and execution tests pass.
- Out-of-scope follow-ups recorded as Issues: I-12e8a5be40ff59c680a2ed46ee94554e (docs, module.concorde,
  obvious-fix), I-dff4a8ecc67f5c2c9509354f07f8b230 (Execution's unbound passage, module.execution,
  obvious-fix), I-23765cae61e558529b5dfd5fe4a22f86 (duplicated review-Issue helpers, suggestion).

## Live Module review and its Issues (task session, 2026-10-01)

- Live run r-20261001T051949-code_review-25f69f0d: `code_review --scope module --modules
  module.code-review`, pi worker, check.code-review.tests passed, status `ok`, verdict
  `changes_required`, 3 Issues reported by the host. The worker gave `"earlier": "new"` placeholders,
  which the host correctly listed as `ignored`. The worker summary also says directory-discovery
  tools failed with a harness socket EPERM on pi, so it read files directly (not this task's Modules).
- I-151815466e82542daae0f5fe1a67ac83 (obvious-fix): a location naming a directory was accepted;
  fixed: a location must be a file or a deleted changed path.
- I-e6635dfe06dc5d81bf4ad7b7ca279b7f (preferred-fix): incomplete Modules lost the reviewer's summary
  and their earlier Issues. Chosen fix: keep the summary of a launched reviewer and list read earlier
  Issues as carried (the contract already defines carried as "neither named nor resolved").
- I-e5c27f13d02d5e8a9efbf71b0a1106ac (preferred-fix): the Spec said a run that stops before any
  reviewer launches carries no report, while the code reports per-Module incomplete outcomes. Chosen
  fix: correct the Spec wording to steps 1-2 (the intended rule, consistent with Spec review), since
  a per-Module report is more useful than none.
- All three added to the task with `task resolve`.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T05:26:31Z

module-code-review delivered: delivery commit ad0316d4 on concorde/module-code-review (task-validation ready, nothing blocking).

What changed:
- `code_review --scope change|module` (default `change`). `--scope module` gives each named Module its own reviewer, under that Module's `review-code` grant alone, judging its whole code and tests against all its Specs. It has no diff and refuses `--base` (`base_in_module_scope`). Unbound, it needs only `--modules`.
- Both scopes now work like Spec review. Each finding has an Issue tier and a kind; the new kind `spec-challenge` is for a requirement the reviewer judges unreasonable or unrealizable, and is usually `decision-needed`. Every finding must name a basis and at least one file:line location, and the host checks them. If one doesn't hold, that reviewer's Modules are `incomplete` (`unresolved_evidence`) and nothing is reported for them.
- The host reports every finding as an Issue, in bound and unbound runs. It appends to an earlier `code_review` Issue when the reviewer names one, and it never closes an Issue.
- The verdict is `accepted`, `changes_required` or `incomplete`, derived from the blocking Issues that stand. A refusal of the Issue store is an error chain (`issues_unreported`), never an Issue.
- Contract `contract.code-review.review` is now version 3.
- The guidance covers the new mode and when to use it, and code_review in "After a review". There is a new requirement and scenario `req/scenario.main-session.module-code-review`.

Decisions I made (reasons in the decision log):
1. Kept the existing worker id `worker`, so no worker-config change is needed.
2. A Module review runs only each reviewed Module's own checks, not the checks of Modules that use it.
3. Issue types: violation, missing-test and spec-challenge → gap/implementation-spec-mismatch; spec-gap → gap/missing-contract; defect and out-of-scope → bug.
4. code_review has its own Issue reporting and declares `uses module.issues`. I did not import spec_review's helpers, because that code belongs to module.spec-review, which this task doesn't bind. The duplication is recorded as suggestion I-23765cae61e558529b5dfd5fe4a22f86.
5. The Operations catalog row was updated; worker ids are unchanged.

Verification:
- build, `build --check` and spec-validation pass (0 errors, 0 warnings).
- The full suite passes: 869 passed, 4 skipped.
- Live run r-20261001T051949-code_review-25f69f0d: `code_review --scope module --modules module.code-review` on pi. Status `ok`, its check passed, and the host reported 3 Issues.
- I fixed all three and added them to the task with `task resolve`, so the merge closes them:
  - I-151815466e82542daae0f5fe1a67ac83 (obvious-fix): a directory was accepted as a location; a location must now name a file.
  - I-e6635dfe06dc5d81bf4ad7b7ca279b7f (preferred-fix): an incomplete Module now keeps its reviewer's summary and lists its earlier Issues as carried.
  - I-e5c27f13d02d5e8a9efbf71b0a1106ac (preferred-fix): I corrected the Spec wording to the intended rule. Only a run that stops before the review step carries no report; per-Module incomplete outcomes are still reported, as in Spec review.

Open, outside this task's Modules:
- I-12e8a5be40ff59c680a2ed46ee94554e (obvious-fix, module.concorde): docs/ do not mention `--scope module`.
- I-dff4a8ecc67f5c2c9509354f07f8b230 (obvious-fix, module.execution): Execution's unbound-run passage says `code_review` (with `--base`).
- Seen in the live run: the pi reviewer reported that directory-discovery tools failed with a harness socket EPERM, so it read files directly. Not investigated here.
- The reviewer wrote `"earlier": "new"` placeholders; the host correctly listed them as ignored.

No escalations.

## Closed: merged, 2026-10-01T05:27:04Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ad0316d4fa2ac827d051c643327714624964ddb1 into main and closed it as merged. Nobody answers a report after that.
