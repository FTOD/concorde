# Decision log: panel-review-fixes

Goal: Repair the small Spec defects confirmed from the 2026-09-28 spec_panel review of every Module (wording, stale statements, internal contradictions with a clear answer, missing rows and links), leaving findings that need a design decision to the developer

## 2026-09-28 — Panel runs and their non-ok results (before this task opened)

- **First attempt, four parallel unbound `spec_panel` runs** (r-20260928T045203-spec_panel-2fa57724,
  -a12ed9ef, -4dde0699, r-20260928T045204-spec_panel-551de9b2), 8 Modules each. Non-ok: 551de9b2
  ended `failed`/`panel_incomplete` for all 8 Modules. Leaf causes: (a) every `reviewer1` on
  `anthropic/claude-opus-5-5` got `400 claude_code_version_too_old` ("Claude Code 2.1.258 does not
  support this model; 2.1.280 required") from the local gateway at localhost:8080, reproduced
  outside Concorde with `pi -p --model anthropic/claude-opus-5-5`; (b) `gateway_concurrency_limit`
  for several `local-openai/gpt-6` reviewers, caused by my choice to run 8 gpt-6 reviewers at once.
  Decision (mine): stopped the other three runs (SIGKILL to their hosts after SIGTERM did not stop
  them) since every panel would be incomplete. Decision (developer): run reviewer1 temporarily on
  `anthropic/claude-fable-5-1` via the git-ignored `.concorde/worker-models.json`.
- **Full run r-20260928T052114-spec_panel-cd841742**, all 32 Modules in one run (sequential Modules)
  to stay under the gateway concurrency limit. Modules module.concorde … module.delivery were
  reviewed with reviewer1 on fable-5-1; after the developer fixed the gateway (verified with a pi
  call) I restored reviewer1 to opus-5-5 from the backup, applying from module.issues on.
- **Non-ok: module.e2e panel stopped** — reviewer3 w-20260928T093721-0acd17 and reviewer1 failed
  the audit with violations `HEAD`, `index`. Cause: another main session fast-forwarded
  `concorde/ci-socat-dependency` into main in the primary worktree at 09:38:35Z while the unbound
  run was auditing that worktree (harness/audit.py compares HEAD and index snapshots). Not a worker
  write. Decision: rerun module.e2e separately after the run; report the audit's inability to tell a
  concurrent merge from a worker change in an unbound primary-worktree run to the developer as an
  open design question (unbound runs take no lock, merges happen in the same worktree).

## 2026-09-28 — How findings are handled

- Decision (mine, within the developer's instruction "fix small confirmed problems, leave what
  needs my decision"): each Module's chair report is verified by a subagent against the Specs and
  code and classified FIXED / DECIDE / LARGER / REJECTED / FIXED-ELSEWHERE-PROPOSED; subagents edit
  only files their Module owns, never the shared glossary; I review every diff, apply proposed
  cross-Module/glossary edits myself, validate and commit. LARGER (real but not small) and DECIDE
  items are not changed and go to the developer. Verdict files are kept per Module and summarised
  below when the work is committed.

## 2026-09-28 — First step: per-Module repairs by the verification agents

- 14 verification agents verified the chair reports of the 22 Modules module.concorde through
  module.adoption (474 findings) and edited only files their Modules own. Verdict files (FIXED /
  DECIDE / LARGER / REJECTED / FIXED-ELSEWHERE-PROPOSED per finding) are kept outside the repository
  and summarised in the final report to the developer.
- Applied with them the one code change the Spec edit requires: the `unsupported_profile` reason in
  `src/concorde/spec/errors.py` now matches Spec core's errors table ("configuration
  profile_version 17 and registry schema_version 3", as `repository_base.py` defines), which
  `tests/concorde/spec/test_errors.py` compares.
- Non-ok: full suite 1 failed / 635 passed: `tests/concorde/e2e/test_cases.py::CaseTests::
  test_grading_runs_the_case_tests_on_a_throwaway_tree` (FAILED expected, `not run` observed). It
  fails identically on main's sources (git archive of main, same interpreter), so it predates this
  task and is unrelated to it; left for the developer.
- An independent review of these edits follows before delivery.

## 2026-09-28 — Second step: approved cross-file edits

- Decision (mine): of the verification agents' proposals for files their Modules do not own, I
  approved and had applied: glossary definitions that the owning Module's repaired Spec and the
  code now contradict (resume-round, main-agent, model-picker, site-build-manifest,
  standard-worker-sequence, write-hook, distribution-command, build, step-agent, decision-point,
  workflow-mode, boundary-set) plus two new entries whose anchors Distribution already defines
  (concorde-unvalidated, pi-runtime); undeclared `uses`/`relies_on` the code relies on (tasks →
  run progress file, delivery → Spec core, distribution → task sessions) with `registry --write`;
  three scenario splits together with their tests' `@verifies`; three small code fixes found by
  the review: `spec_rule` told review-code and understand workers to return `blocked` for a Spec
  gap against their own prompts (now: report a `spec-gap` finding / a Spec gap, with a unit test),
  a wrong comment in `pi_extension.ts`, and the docsite preview not watching the glossary (with a
  vitest case).
- Not approved, left to the developer: redefining `concept.spec-context` (a core term), removing
  the unreachable `not_started` outcomes (contract version bumps), an optional `relies_on`, a
  "Framework" glossary entry.
- Verification: spec-validation 0/0, registry --check clean, build --check clean, ruff/prettier
  clean, docsite tests 258 passed, pytest 639 passed / 1 failed (the pre-existing
  test_grading_runs_the_case_tests_on_a_throwaway_tree, unchanged).

## 2026-09-28 — Third step: independent review of the repairs

- Seven fresh reviewer agents checked commit 6418bc5d against the code (read only). They found 1
  must-fix and about 45 should-fix problems, all applied after each claim was re-checked in code:
  statements still slightly inaccurate after an edit (checked Modules = bound Modules and their
  users, validation resumes without checks, pi's batch-terminate rule, lock in the run store, ...),
  contradictions created with untouched step tables and glossary terms, and dropped words in split
  requirements.
- Two edits by verification agents had silently settled design questions; I reverted them to the
  Spec's original promise and list them as open decisions for the developer:
  (1) `req.delivery.atomic` had been narrowed to the code's `git reset` of the index, giving up the
  promise to restore the index the readiness examined — the promise is restored (its trigger now
  names bundle, staging and commit failures, which the code does undo);
  (2) a newly added `req.main-session.pi-run-view` promised that the pi run view shows every run of
  the project, while the code follows only runs started with `concorde_run` or running at session
  start — the new requirement is removed; whether the view should follow runs started elsewhere
  (as the Usage sentence already claims) is the developer's decision.
- Verification: spec-validation 0/0, pytest tests/concorde 639 passed / 1 known pre-existing failure.

## 2026-09-28 — Fourth step: the last 10 Modules

- The full panel run r-20260928T052114-spec_panel-cd841742 ended `failed`/`panel_incomplete` only
  for module.e2e (the audit false positive logged above); every other Module `changes_required`
  (217 blocking and 424 advisory findings merged from 1124 reviewer findings, 13 rejected).
  module.e2e was rerun alone: r-20260928T110044-spec_panel-08e7f55a ended `ok`,
  `changes_required`, 18 findings. Both panels read the primary worktree (main at 38ec10c7), not
  this branch.
- Six verification agents (with a brief extended by the lessons of the first review) verified the
  reports of module.headless-sessions, swe-bench-cases, dogfood-scenarios, dogfooding,
  coordination, task-session, execution, commands, scaffold and e2e and repaired in owned files.
- Verification: spec-validation 0/0; pytest 639 passed / 1 known pre-existing failure.

## 2026-09-28 — Fifth step: second-round cross-file edits

- Decision (mine): approved and had applied the second round's proposals: glossary definitions
  (concorde-defect, evaluation, test-project), undeclared uses/relies_on (scaffold → Adoption's
  proposal checks, swe-bench-cases → Specification and Spec review, coordination → run progress
  file), the root seam description aligned with Coordination, "status file" for task-session round
  records in main-session, scenario splits with their tests' `@verifies` where the tests really
  check each case (execution, headless-sessions, swe-bench-cases, e2e repositories; the e2e trust
  split was skipped because the test does not check "changes nothing" on the second call), the
  `_untouched` assertions a rewritten dogfood scenario needs, and a small code fix in
  `scripts/e2e/cases.py` (a grading timeout is a detailed `grade_timeout` E2EError instead of a
  raw TimeoutExpired, with a unit test).
- Reverted two verifier edits that weakened or invented promises: the swe-bench-cases order "before
  the case's issue is worked" is back in its SHALL; the unenforced "one headless session at a time"
  clause is removed.
- Verification: spec-validation 0/0, build --check clean, registry --write done, pytest 640 passed
  / 1 known pre-existing failure.

## 2026-09-28 — Sixth step: review of the second round, and split-id references

- Three fresh reviewers checked commit d2435244: 1 must-fix (a wrong claim about how the dogfood
  clone records reports) and 14 should-fix problems, all applied after re-checking in code.
- One more verifier edit had silently settled a design question and is reverted to main's text:
  Task sessions' treatment of a workflow's decision points (verifier made them "the developer's to
  settle" with an invented escalate-and-restart procedure). Open for the developer: may a task
  session settle decision points itself, or run a workflow in no-ask mode?
- Every reference to the original id of a split requirement (relies_on, links, verifies,
  prompts, code) was checked; references that relied on a moved part now also cite the new id
  (execution workspace-busy / no-writing-worker / error-detail, distribution, e2e sessions,
  workflows, views).
- Non-ok, handled: Scaffold's `#uses-adoption` cannot link Adoption's realization of the narrowing
  rule, because the validator requires a linked target in `relies_on` and forbids realizations
  there; the sentence names the rule without the link.
- Verification: spec-validation 0/0, pytest 640 passed / 1 known pre-existing failure.

## 2026-09-28 — Outcome and what is left for the developer

Verdicts over 665 chair findings (32 Modules): 517 fixed in the owning Module, 34 fixed through
approved cross-file edits, 29 rejected after checking, 51 real but larger (left), 34 decisions
(left). Independent reviews found and corrected ~60 imperfect repairs, 3 of which had silently
settled design questions and were reverted.

Decisions for the developer (not changed; per-finding options in the verdict files):
- Introduced by the review itself: Delivery's index restore (`req.delivery.atomic` promises the
  index the readiness examined, code does `git reset`); pi run view following runs started
  elsewhere; task sessions and workflow decision points; redefining `concept.spec-context`;
  removing unreachable `not_started` outcomes (code_review, implement).
- From the verdicts: adoption F5, F20; checks F7, F20, F22, F24; delivery F7, F10; distribution F3;
  dogfooding F5, F6, F7; e2e F5, F7b; execution F7; harness F12, F18; headless-sessions F3b;
  implementation F17; main-session F9; spec-mcp F11; spec F6, F8, F26, F28; tasks F12, F13, F14,
  F17; understanding F2, F10; validation F4b; views F2, F20.
- Operational: an unbound run in the primary worktree fails the worker audit (HEAD/index) when a
  main session merges there meanwhile (module.e2e's first panel); unbound runs take no lock.
- Pre-existing test failure: tests/concorde/e2e/test_cases.py::CaseTests::
  test_grading_runs_the_case_tests_on_a_throwaway_tree fails on main too.

Larger work left (51): ~12 scenario splits that need @verifies changes, ~20 missing flow/state
diagrams, ~7 Usage sections without a worked normal path, and a few Design explanations.

## Closed: merged, 2026-09-28T11:46:46Z

## 2026-09-29 — developer's decision on the open items

The developer approved every recommendation for the 35 open decisions ("全按建议"), including, for
spec-mcp F11, the rationale the main agent proposed (no runtime dependency for a small, fully
specified wire; CLAUDE_PROJECT_DIR is the project directory Claude Code sets while roots may be
several). They are carried out in nine tasks: delivery-commit-verify, checks-validation-cleanup,
spec-tooling-promises, tasks-atomicity, operations-briefs-outcomes, adoption-answers-links,
e2e-fixes, harness-messages, dogfooding-session-guidance.

## 2026-09-29 — The 47 larger items

Carried out in ten tasks, each delivered, independently reviewed against the code and merged:
panel-larger-tasks, panel-larger-task-session, panel-larger-execution, panel-larger-workflows,
panel-larger-commands, panel-larger-operations, panel-larger-e2e, panel-larger-spec-tooling,
panel-larger-distribution, panel-larger-issues (each task's decision log holds its items,
decisions and review rounds). Skipped with reasons: checks F18 and code-review F11 (diagrams
would repeat numbered steps that already state every exit), main-session pi-model-picker and
tasks open-inherits-worker-models (no longer exist or no longer bundle situations), workers F11's
configure-refused half (the command was removed in f99b9dff). Execution F11 and distribution F22,
listed LARGER in the verdicts, were already done before these tasks. Left for the developer:
execution F19 (the word for the runner's rows).
