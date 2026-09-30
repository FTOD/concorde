# Decision log: adoption-output-paths

Goal: Make adoption workers' output pass the host: the survey's paths (entries, externals, check inputs) must not fail because the worker brief says 'always use absolute paths' while the host accepts only project-relative paths, and code_to_spec decisions must not fail because 'chosen' paraphrases an option instead of copying it

## Brief (main agent, 2026-10-01)

**Defects, seen in an end-to-end run** (SWE-bench psf__requests-5414, test project
/tmp/concorde-e2e/requests-5414, installed from main 9b81045d, brownfield workflow of task
`adopt`). Evidence (read-only): /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/decisions.md, /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/workspace/workflow/reports/1.json, 2.json,
2.md, /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/trace.json and the run nodes below /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/workspace/.

1. **survey `inconsistent_proposal` (36 problems):** the worker wrote every entry, external and
   check input as an absolute path, because the brief (`src/concorde/harness/workers.py`, "The
   task worktree is …; always use absolute paths") tells it to, while the host accepts only
   project-relative paths. The task session reran with a --goal asking for project-relative paths.
2. **code_to_spec `inconsistent_description`** (all three child Modules): each decision's
   `chosen` paraphrased an option instead of copying it verbatim. Reran with a --goal requiring
   verbatim choices.

**Developer's decision:** fix both, generally (not by asking the caller for a better --goal).

**Main agent's recommendation, yours to settle:** for 1, make the brief say that tools take
absolute paths while paths written in the result follow the output contract (project-relative),
and check whether the host should also accept an absolute path inside the worktree by turning it
into the relative one, since that is unambiguous; look for the same conflict in the other
Operations' outputs. For 2, remove the failure mode rather than police it, for example by having a
decision name its chosen option by an identity instead of repeating its text. Keep contracts
versioned; rapid iteration, no compatibility needed. Add tests that fail without the fixes. Escalate
a change outside module.adoption and module.workers.

## Task session (2026-10-01)

- Evidence read: survey `r-20260930T162722-survey-961aeb8a` wrote every child entry, external path
  and check input as `/tmp/concorde-e2e/requests-5414/.claude/worktrees/adopt/<path>` (argv and
  open-question evidence were fine); code_to_spec `r-20260930T163520-code_to_spec-c7bffbc1` and its
  siblings wrote `chosen` as a paraphrase of one of two options, all `decided_by` worker.
- Decision (paths, brief): Workers' brief keeps absolute paths for tools but says every path the
  worker writes in its result is relative to the task worktree. No Operation asks for absolute
  paths in its output; `proposed_deletions` already accepts both (os.path.join), so the worker
  result contract's "lists absolute paths" becomes "paths in the worktree, relative as the brief
  asks, or absolute".
- Decision (paths, host): the survey and code_to_spec hosts also turn a path that starts with the
  task worktree's path (as given, or its real path) into the project-relative one, before any
  check: child entries, external paths, check inputs, open-question evidence, and the path part of
  a promise's `tests`. This is unambiguous, and spec_review's host already does the same for its
  findings. Anything else is left as it is and still reported by the existing checks.
- Other Operations: spec_review/panel already accept absolute paths; specify refuses an absolute
  document proposal and understand's `new_files` carries a path, both asked for "project-relative"
  in their prompts. The brief fix removes the contradiction for them too; their hosts are outside
  this task's Modules and not changed here (noted in the report).
- Decision (decisions): remove the paraphrase failure mode. In the worker's claim (not the output
  contract) every option gets a short identity (`{"id": "keep-root", "text": "..."}`) and `chosen`
  names an option by that identity; the host writes the output decision with the options' texts
  and the chosen option's text, and sets `decided_by` itself: `worker`, or for a decision that
  follows an answer the answer's `answered_by` with the answer as `chosen` (the worker's `chosen`
  is then null and not consulted). The worker never copies text or `decided_by` any more. The
  output contracts keep their shape (Workflows reads `chosen` text), with versions bumped for the
  changed semantics (decomposition 6, spec description 4). An identity rather than an index, so a
  mistake is detected (unknown identity) instead of silently choosing a neighbour.

## Escalated to the main agent, 2026-09-30T18:13:46Z

- **task-session** task session (task adoption-output-paths): `change_outside_task_modules`
  The adoption worker's decision claim changed shape (options are {id, text} objects and chosen names an option id or null; the output contracts keep their shape). tests/concorde/acceptance/test_flows.py, realization.concorde.acceptance-tests of module.concorde, feeds a fake survey worker a decision in the old shape (options ["yes","no"], chosen "no", decided_by), which the new worker schema rejects (worker_result_invalid), so BrownfieldFlowTests.test_describe_an_existing_codebase_in_no_ask_mode fails without an edit. I changed only that fixture: options [{"id":"yes","text":"yes"},{"id":"no","text":"no"}], chosen "no", no decided_by; no assertion changed. It is committed on the task branch (c5c2931a); the full suite passes (839 passed) and task-validation reports ready. I have not run delivery.
  Not handled here (scope): The brief says to escalate a change outside module.adoption and module.workers; the acceptance tests belong to module.concorde.
  Options: approve the fixture edit; I deliver as committed; add module.concorde to the task's Modules, then I deliver; reject it: keep the old worker claim shape, which brings the paraphrase failure back
  Recommendation: approve: the edit only adapts a fake worker's output to the claim shape that module.adoption owns and changes no promise or assertion of module.concorde

```json
{
  "level": "task-session",
  "actor": "task session (task adoption-output-paths)",
  "code": "change_outside_task_modules",
  "detail": "The adoption worker's decision claim changed shape (options are {id, text} objects and chosen names an option id or null; the output contracts keep their shape). tests/concorde/acceptance/test_flows.py, realization.concorde.acceptance-tests of module.concorde, feeds a fake survey worker a decision in the old shape (options [\"yes\",\"no\"], chosen \"no\", decided_by), which the new worker schema rejects (worker_result_invalid), so BrownfieldFlowTests.test_describe_an_existing_codebase_in_no_ask_mode fails without an edit. I changed only that fixture: options [{\"id\":\"yes\",\"text\":\"yes\"},{\"id\":\"no\",\"text\":\"no\"}], chosen \"no\", no decided_by; no assertion changed. It is committed on the task branch (c5c2931a); the full suite passes (839 passed) and task-validation reports ready. I have not run delivery.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "The brief says to escalate a change outside module.adoption and module.workers; the acceptance tests belong to module.concorde."
  },
  "options": [
    "approve the fixture edit; I deliver as committed",
    "add module.concorde to the task's Modules, then I deliver",
    "reject it: keep the old worker claim shape, which brings the paraphrase failure back"
  ],
  "recommendation": "approve: the edit only adapts a fake worker's output to the claim shape that module.adoption owns and changes no promise or assertion of module.concorde",
  "causes": []
}
```

## Report 1 to the main agent (Tasks plan review operation), 2026-09-30T18:14:02Z

adoption-output-paths: fix committed and validated (c5c2931a, task-validation ready, 839 tests pass); ONE escalation blocks delivery.

WHAT CHANGED
1. Survey paths. The Workers brief no longer says "always use absolute paths". It now says tools take absolute paths, while every path written in the structured result is relative to the task worktree (src/concorde/harness/workers.py; new req.workers.result-paths-relative and scenario.workers.brief-result-paths). The survey and code_to_spec hosts also turn a path that starts with the worktree's absolute path (or its real path) into the project-relative one before checking it: child entries, external paths, check inputs, open-question evidence and promise `tests`. Other paths are left as written and still refused (req.adoption.relative-paths; scenarios survey-absolute-paths, describe-absolute-paths).
2. Decision `chosen`. In the worker's claim, each option is {id, text} and `chosen` names an option id, or is null for a decision an answer settles. The host writes the output decision itself: the option texts, the chosen option's text (or the answer) and decided_by. The worker no longer copies text or decided_by. A paraphrase in `chosen` now fails the result schema itself. An unknown id, or a null choice that no answer settles, fails with inconsistent_proposal / inconsistent_description (req.adoption.decisions-by-host, req.adoption.unchosen-decision-fails, scenario.adoption.decision-by-option). The output contracts keep their shape, so Workflows is unaffected; versions are bumped (decomposition 6, spec description 4). The worker result contract now says proposed_deletions may be relative or absolute; the host already accepted both.
The new tests fail without the fix (checked by reverting src and prompts).

DECISIONS I TOOK (details in the decision log)
- Option identities rather than an index: a wrong identity is detected, while an off-by-one index would silently record the neighbouring option.
- For an answered decision the host records the answer and ignores whatever option the worker named. The only answer check left is that the decision is listed.
- The brief keeps "The task worktree is X;" with its semicolon. Three fake workers in tests (acceptance/fake_router.py, spec_review/fake_reviewer.py, spec_review/fake_panelist.py) parse that sentence, so keeping it avoids editing them.

OTHER OPERATIONS (not changed; outside this task)
spec_review and spec_panel already accept absolute paths. specify refuses an absolute document proposal, and understand's plan new_files carries a path; both prompts ask for project-relative paths. With the brief no longer contradicting that, these should be fine. Their hosts could accept absolute paths too, in a later task if wanted.

ESCALATION 1 (decision needed before I deliver)
- **task-session** task session (task adoption-output-paths): `change_outside_task_modules`
  The adoption worker's decision claim changed shape (options are {id, text} objects and chosen names an option id or null; the output contracts keep their shape). tests/concorde/acceptance/test_flows.py, realization.concorde.acceptance-tests of module.concorde, feeds a fake survey worker a decision in the old shape (options ["yes","no"], chosen "no", decided_by), which the new worker schema rejects (worker_result_invalid), so BrownfieldFlowTests.test_describe_an_existing_codebase_in_no_ask_mode fails without an edit. I changed only that fixture: options [{"id":"yes","text":"yes"},{"id":"no","text":"no"}], chosen "no", no decided_by; no assertion changed. It is committed on the task branch (c5c2931a); the full suite passes (839 passed) and task-validation reports ready. I have not run delivery.
  Not handled here (scope): The brief says to escalate a change outside module.adoption and module.workers; the acceptance tests belong to module.concorde.
  Options: approve the fixture edit; I deliver as committed; add module.concorde to the task's Modules, then I deliver; reject it: keep the old worker claim shape, which brings the paraphrase failure back
  Recommendation: approve: the edit only adapts a fake worker's output to the claim shape that module.adoption owns and changes no promise or assertion of module.concorde

Once you answer, I run delivery and report the delivery commit.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-09-30T18:14:24Z

Escalation 1 (change_outside_task_modules), settled by the main agent: approved. The fixture edit in tests/concorde/acceptance/test_flows.py only adapts a fake worker's output to the claim shape module.adoption owns and changes no promise or assertion of module.concorde. Deliver as committed.

- Main agent's answer to escalation 1 (2026-10-01): approved; the fixture edit in
  tests/concorde/acceptance/test_flows.py stays as committed in c5c2931a. Running delivery.

## Report 2 to the main agent (Tasks plan review operation), 2026-09-30T18:16:16Z

adoption-output-paths delivered: delivery commit d3c6beddd8a1d10b5ce7b9c597ba533dd04fb9c3 on concorde/adoption-output-paths (on top of c5c2931a), after your approval of escalation 1 (acceptance test fixture edit kept). Delivery validated the workspace again: ok. Nothing else is open; the task is ready for task merge.

## Closed: merged, 2026-09-30T18:16:26Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit d3c6beddd8a1d10b5ce7b9c597ba533dd04fb9c3 into main and closed it as merged. Nobody answers a report after that.
