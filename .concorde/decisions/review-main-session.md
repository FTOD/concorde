# Decision log: review-main-session

Goal: Fix the spec review findings of the Main session

## Brief (main agent, 2026-09-30)

The developer asked for a spec review after `project-model-names` merged and said: fix the small
problems yourselves, and ask the developer only at the end about what needs their decision.

The unbound `spec_review` run `r-20260929T203136-spec_review-a3b63738` examined main at 14e573aa
and ended `changes_required`. Its result, with every finding's evidence and suggestion, is
`/home/zhenyu/concorde/.concorde/unbound/r-20260929T203136-spec_review-a3b63738/result.json`
(read-only for you); this task covers the findings of module.main-session.

### What to do

- Fix every finding of these Modules, blocking and advisory, except those named below as the
  developer's. Typical fixes: split a requirement that holds several obligations into atomic
  requirements, one SHALL each; split a scenario that mixes situations into scenarios of one
  situation each; correct examples, diagrams and wording that contradict the provider's Spec or the
  code. When a scenario identity changes, update the tests whose verification declarations name it.
  Keep what the Modules promise unchanged unless the finding shows the promise is wrong; when the
  code and the Spec disagree, decide which is right from the other Specs and the developer's earlier
  decisions, and record the decision here.
- Findings that say a provider's contracts were not supplied: check whether the Module's
  declarations omit that contract and add it if so; otherwise report it as a possible spec_review
  defect with evidence. Do not change module.spec-review.
- A finding you judge wrong: do not change the Spec; record why here and in your report.
- Anything else you find that needs the developer (it changes a promise's meaning, the design, or an
  earlier developer decision): leave it unchanged and report it with options and a recommendation.
  Do not escalate and stop: deliver the rest and put every such question in your final report.

### Specific to this task

Leave f.4 (who settles workflow decision points: the glossary's concept.decision-point says every one is the developer's, the guidance lets the main agent settle those its authority covers) UNCHANGED: the developer decides. Give the options and your recommendation. f.2 is decided by the main agent: the developer's owner-only rule is about wakes nobody asked for; state that the owner-only guarantee covers automatic run-end wakes, and that register_wait is a session's explicit request for its own wake, admitted as documented; align Owners prose, requirements and the query scenario. For f.7 (provider contracts not supplied) check the declarations as described in the common brief.

### Process

Create what Git ignores (`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`). Format,
`build --check`, `spec-validation`, `registry --write` if a module block changes, the relevant tests
and once the full pytest suite on the final input. Then run `python3 scripts/concorde.py run
spec_review` once in the task worktree (bound; it reviews this task's Modules and updates their
review memory) and handle its findings the same way, without looping further. Then `task-validation`
and `delivery`, and report to the main agent with SendMessage: what you fixed, the findings you
judged wrong, and the open questions for the developer with options and recommendations.

## Task session (2026-09-30)

Commit f709fcea on `concorde/review-main-session` fixes f.1–f.3 and f.5–f.8 of
`r-20260929T203136-spec_review-a3b63738`; f.4 is left unchanged, as the brief says.

- **f.1 (split requirements).** Every listed requirement now holds one SHALL; each keeps its
  identity for its first duty, and every further duty got a new identity (e.g. `brief-read-first`,
  `reports-by-name`, `task-session-background-runs`, `unbound-examines-head`, `unbound-reads-only`,
  `workflow-restart`, `merge-abort`, `merge-diverged`, `task-session-merge-refusal`,
  `task-session-conflict-merge`, `wait-without-turns`, `project-mcp-preview` … `project-mcp-source-of-truth`,
  `worker-configuration-created`, `model-map-names`, `model-change-commit`, `batched-answers`,
  `ordinary-decisions`, `unbound-failure-task`, `task-session-binds-new-files`,
  `task-session-workflow-pause|decisions|failure|major`). Decision: keep existing identities for
  the first duty so that inbound links (module.md, task-session/module.md) stay valid; no test
  names a requirement. `workflow-pause` keeps its wording "itself or through the developer"
  unchanged, since f.4 is the developer's.
- **f.2** as the main agent decided: `single-owner` now covers wakes nobody asked for;
  `register_wait` is stated as a session's explicit request for its own wake, admitted as the
  contracts document; `claude-sees-by-query`, the Owners prose and the query scenario (GIVEN: the
  first session registered no wait) aligned. Guidance (`skill.md` Owners paragraph) aligned too.
- **f.3.** Decision: equivalence now covers queries and short writes "as the command does when it
  waits for no lock" (the code calls them with `wait=0`, so the old promise was also inexact for
  `task_open`/`task_close`); two new requirements specify `task_merge`'s start envelope and
  `register_wait`'s registration; module.md, contracts.md intro and the skill's "source of truth"
  sentence aligned.
- **f.5.** Split `scenario.main-session.merge-delivered` into merge-delivered (choosing the path),
  `merge-command` (CLI `--wait`, background Bash, retry on `merge_busy`/`workspace_busy`, the
  `workspace_busy` line moved from merge-interrupted) and `merge-through-server` (immediate
  refusal, `register_wait` or its fallback command, retry). Added the retry instruction to the
  skill's `task_merge` bullet, which lacked it; tests split accordingly.
- **f.6.** "the one change" removed in requirements, module.md and the skill; the commit is named
  one of the primary-worktree exceptions `tasks-own-changes` lists.
- **f.7.** Judged right: the `uses` of module.tasks and module.tracing listed only concepts, so the
  contract documents contracts.md incorporates were not selected. Added `contract.tasks.record`,
  `contract.tracing.error` and `contract.tracing.view` to `relies_on` (selecting both contract
  documents) and linked them from the meaning sections; registry regenerated. Not a spec_review
  defect.
- **f.8.** Added an illustrative d2 sequence diagram (session, server, merge process) with the
  busy/wait/retry, handover and end branches beside "The project MCP server".

### Bound spec_review `r-20260929T205742-spec_review-77f38f86` (changes_required, 6 blocking)

Handled once, without re-reviewing, as the brief says:

- **f.1** further splits: `no-work-in-task-worktree`, `project-mcp-merge-answer`,
  `project-mcp-wait-answer`, `worker-configuration-committed`, `answer-once`, `report-decisions`,
  `unbound-failure-escalated`, `task-session-keeps-branch`; `merge-conflict` narrowed to having the
  session merge the primary branch. Every requirement holds one SHALL.
- **f.2** (escalation-policy "and on no other" contradicted workflow-mode, small-change and the
  worker-configuration question): dropped "and on no other"; the explanation and module.md's
  Escalation policy name those choices and approvals as the developer's besides. Promise not
  widened: they were already required elsewhere.
- **f.3** "steps that finished are not run again" contradicted Workflows (an answered step and its
  successors run anew): corrected in `workflow-restart` and in both guidance texts.
- **f.4** command equivalence now covers only rows that name a command (`task_list`, `task_show`,
  `trace_show`, short writes); new `project-mcp-record-queries` for `run_result`,
  `workflow_report`, `locks`; contracts intro aligned.
- **f.5** `run_result` row now states the lost run (running false, result null), which the code
  already answers. Decision: no new scenario/test for it (clarification of existing behaviour).
- **f.6** `project-mcp-fallback` restricted to waits not yet satisfied, matching the code and
  contracts (an already-satisfied wait answers at once, channel or not).
- **f.7** module.md now names the refused commands, the `--resume`/`--abort` exemption and that
  `list`/`show` stay available.
- **f.8** added the GIVEN that no process holds the locks during the calls.
- **f.9** concerns module.operations ("either the main agent or a task session can invoke
  Operations ... in its task worktree"), outside this task's Modules: not changed, reported to the
  main agent.

## Closed: merged, 2026-09-29T21:05:48Z
