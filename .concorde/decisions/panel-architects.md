# Decision log: panel-architects

Goal: Add two architects to spec_panel that judge a Module's architecture from the whole project's Specs, have the chair merge reviewers' and architects' findings into tiered findings, and make spec_review and spec_panel report every finding as a project-level Issue in place of the review memory

## Brief (main agent, 2026-10-01)

Third of four tasks that rebuild Concorde's reviews. Already merged on main: `spec-quality-protocol`
(Protocol 16.1: `protocol/evaluation.md` "Evaluating a Spec" with Module quality and architecture
quality between Modules, and the task type `review-architecture` reading every Module's Specs,
`ProjectSpecification`, with code names only) and `project-issues` (project-level Issues in the
primary worktree, every report with a `tier`: `suggestion` | `obvious-fix` | `preferred-fix` |
`decision-needed`, tiers 2-4 blocking; Issue tools on the project MCP server; defects of the Issue
system itself never go through Issues). Read both Specs first. `issue-writes-in-sessions` runs in
parallel (session boundary, Workers, Spec MCP server, Understanding, Dogfooding); do not touch
those Modules.

### The developer's decisions this task carries out

1. **Two architects join `spec_panel`**, worker ids `architect1` and `architect2`, besides the
   reviewers (3 by default). They judge the reviewed Module from the whole project's point of view
   under a `review-architecture` grant: its relations with the other Modules, how well it is
   decoupled, whether its boundaries are clear, and the other architecture criteria of
   `protocol/evaluation.md`. Reviewers keep judging the Module's own Specs as today.
2. **Worker models** for the architects, in this branch's `.concorde/workers.json`:
   `architect1` = `gpt-6-astra` with reasoning `high`, `architect2` = `gpt-6.1-sol` with reasoning
   `high` (both already enabled and in the developer's model map). Keep the other entries.
3. **The chair** audits and merges the findings of all reviewers and both architects into the one
   report (every labelled finding accounted exactly once, as today), and gives every final finding
   its tier. The four tiers are those of the Issues Spec: `suggestion` = advisory; `obvious-fix`,
   `preferred-fix`, `decision-needed` = blocking.
4. **Criteria live in the Protocol.** The reviewer checklist (`prompts/workers/spec-review/`) and the
   new architect brief judge by `protocol/evaluation.md` and point to it rather than restating a
   separate bar. Keep what a worker needs to act (finding shape, one-pass rule) in the prompts.
5. **Every final finding becomes an Issue.** `spec_review` (single reviewer, tier given by the
   reviewer and open to the checker's dispute) and `spec_panel` (tier given by the chair) report
   each final finding through the Issues store from the Operation's host, never from a worker, in
   bound and unbound runs alike (Issues are project-level, so an unbound run can report). Before
   reviewing, the workers receive the Module's open Issues that earlier reviews reported, so that a
   problem already recorded is appended to that Issue instead of becoming a new one. The run result
   names each finding's Issue identity. Review Operations only report: they never fix, and never
   close an Issue; an earlier Issue the review finds resolved is listed in the output for the task
   session to close. A failure of the Issue system while reporting is an error chain in the run
   result, never an Issue.
6. **Issues replace the review memory** (`.concorde/reviews/spec/<module>.json`, `f.<n>` ids):
   remove it and its contract, the glossary's `concept.review-memory`, and update the verdict and
   `concept.review-finding` / `concept.review-verdict` accordingly (the verdict follows the
   blocking Issues that stand). Whether the "skip when the context identity is unchanged" shortcut
   survives, and where its record would live, is yours to settle; dropping it is acceptable.
7. **Glossary**: add the Issue tier as a term, owned by `module.issues` (explained in the Issues
   Spec's `#tiers`), now that review Modules use it.
8. **Guidance**: in the main-session guidance (main agent and task session), after a review the
   task session fixes `obvious-fix` Issues itself, fixes `preferred-fix` Issues and reports them,
   and escalates `decision-needed` Issues by their Issue identity; `suggestion` needs no action.
   Fixing is always later work (`specify`, `implement`), never the review's.

### Left to the task session

Naming, prompt structure, the architect brief, how the chair's attempt and accounting grow to the
architects, whether the panel may run with fewer architects (e.g. `--architects 0-2`, default 2),
and how the host matches a finding to an open Issue (the workers name it; the host checks it
exists and belongs to the Module). Escalate together anything that changes other Modules' promises.

### Verification and delivery

Build, spec-validation, relevant tests and the full suite once at the end, then `task-validation`
and `delivery`. A live `spec_panel` run on a small Module is welcome as evidence but optional;
note: until `issue-writes-in-sessions` merges, a run started from your background Bash may be
refused writing Issues by your sandbox; start it through `workflow_step`-free means only if it
works, and otherwise record that it was not run.

## Task session decisions (2026-10-01)

- **No `plan_review`.** Optional per the brief; the change is worked directly, which the development
  skill calls more reliable while Concorde's own Operations are early.
- **Finding shape (every role).** `{module, path, anchor?, line?, dimension, tier, title, problem,
  impact, evidence, suggestion, related?, issue?}`: `severity` gives way to the Issue `tier`
  (`suggestion` advisory, the other three blocking), and `title` and `impact` are added so that
  every final finding states the problem completely as an Issue report needs. `related` (architects)
  names the other Modules an architecture problem concerns; `issue` names the offered open Issue the
  finding is the same problem as. Reviewer dimensions stay the six Module quality dimensions;
  architect dimensions are the six architecture quality dimensions of `protocol/evaluation.md`
  (`responsibilities`, `ownership`, `interfaces`, `dependencies`, `failure-containment`,
  `consistency`) plus `context`. The scope rule stays: a blocking finding about a document the
  reviewed Module does not own becomes a `suggestion` (`finding-scope` evidence).
- **Issues replace the memory, same semantics.** Before its workers run, the host lists the Module's
  open Issues any of whose reports a review Operation (`spec_review`, `spec_panel`) made, and hands
  them to every worker. A worker reports only new problems or earlier Issues that changed (naming
  `issue`), and lists in `resolved` the offered Issues the Specs no longer have; an offered Issue
  neither updated nor resolved is carried and still stands. The host appends a finding that names an
  offered Issue to it (at the revision it reads just before), creates a new Issue otherwise (a
  named Issue that was not offered is ignored and listed), reports nothing for a finding the checker
  disputed, never closes an Issue, and lists resolutions for the task session to close. The outcome
  is `changes_required` when a blocking-tier Issue stands: reported now or carried.
- **Provenance** of a host report: `invocation_id` the run id, `agent` `operation`, `operation`
  `spec_review`/`spec_panel`, `phase` `report`, `target_id` the reviewed Module, `context_id` its
  context identity, `change_id` the workspace (null unbound), `head` the reviewed commit. Report key
  `<module>/<n>`; type `gap`/`missing-contract` for `context`, `gap`/`spec-conflict` for
  `consistency`, `bug` otherwise.
- **Issue-system failure** while reporting makes that Module `incomplete` (`issues_unreported`,
  failed) with the store's refusal as its cause; the Module's findings stay in the payload with
  `issue: null` for those not reported. Never an Issue.
- **The unchanged-Specs shortcut and `--force` are dropped**: their record lived in the memory, and
  a record elsewhere would be new tracked state for little gain.
- **Architects**: `--architects 0-2`, default 2, workers `architect1`/`architect2` under a
  `review-architecture` grant of the reviewed Module, launched in parallel with the reviewers; their
  findings are labelled `a<seat>.<n>` and accounted by the chair like reviewer labels (`r<seat>.<n>`).
  A short architect stops the panel like a short reviewer (`panel_short`). The chair also returns the
  final `resolved` list, each naming an offered Issue.
- **Criteria**: `prompts/workers/spec-review/checklist.md` includes `protocol/evaluation.md` at build
  time and keeps only what a worker needs to act (roles, finding shape, one-pass rule, Issues).
- **Tracked review memories** (`.concorde/reviews/spec/`, 8 files, 36 open findings of which 21
  blocking) are deleted with the memory; they stay in Git history. Migration is escalated.

## Main agent note (2026-10-01): a main-session follow-up from issue-writes-in-sessions

`issue-writes-in-sessions` (merging now) made the primary worktree's `.concorde/issues/` writable
in a task session's Bash sandbox, so runs a task session starts can write Issues, and fixed Workers
refusing every `review-architecture` worker (`grant_unavailable`). `prompts/main-session/task-session.md`
still says the primary worktree's Issues are kept where "your Bash sandbox cannot write": correct
that phrase in this task (module.main-session), keeping the rule that a task session writes Issues
only through the Issue MCP tools. Once that task is merged, merge the primary branch into this task
branch before your final validation so the Workers fix is in.

## Task session decisions, continued (2026-10-01)

- **Criteria delivery.** The build refuses a Protocol include outside `prompts/protocol/`, so the
  checklist no longer restates the bar: the host appends the project's Protocol copy's *Writing
  guidance* and *Evaluating a Spec* (from `.concorde/protocol/kinds/module.md`) to every review
  worker's brief, as Spec writers already receive the guide.
- **Chair grant.** With at least one architect the chair runs under the Module's
  `review-architecture` grant (a superset of `review-spec`), so it can verify architect findings
  against the other Modules' Specs; without architects it keeps `review-spec`. The panel payload
  carries `architecture_identity` beside `context_identity`, and the Issue provenance of a panel
  report names the chair's identity.
- **Payload versions.** `contract.spec-review.payload` 4 (`tier`, `title`, `impact`, `issue`,
  `earlier`, `earlier_issues`; no `severity`, `id`, `memory`) and `contract.spec-review.panel-payload`
  3 (`reviews` by `worker`/`role`/`seat` with `resolved`, labels `r<n>.<m>`/`a<n>.<m>`, report
  findings with `workers` and `issue`), both generated from the code's schemas.
- **Merge of main** (the main agent's request): merged `main` at 44b46dd3 (issue-writes-in-sessions)
  into the task branch; the architect tests pass only with its Workers fix.
- **Guidance phrase** (the main agent's request): the main-session Spec, requirement, skill and
  task-session guidance no longer say a task session's Bash sandbox cannot write the primary
  worktree's Issues; they say a task session never writes an Issue record from Bash, although its
  sandbox lets the runs it starts report their findings.
- **User documentation** `docs/using-concorde.md` (owned by no Module) now describes the reviews'
  Issues and architects instead of the review memory.

## Escalated to the main agent, 2026-09-30T20:31:24Z

- **task-session** task session (task panel-architects): `catalog_outside_modules`
  Removing concept.review-memory (developer decision 6) leaves a dangling glossary link in module.operations' catalog row for spec_review (specs/concorde/execution/operations/module.md:54), so spec-validation fails and delivery is blocked until that row changes. The same Spec still says spec_panel's worker ids are reviewer1..reviewer5 and chair with task type review-spec only, that a bound spec_review changes the reviewed Modules' review memory, and (its #uses-spec-review paragraph) that the provider keeps findings in the review memory. module.workers' entry (specs/concorde/execution/workers/module.md:344) also lists spec_panel's worker ids without architect1/architect2. The edits are wording only: catalog row spec_review 'May change' -> no (it reports its findings as Issues, which the primary worktree keeps); spec_panel task types review-spec, review-architecture for its architects and its chair when it has architects; worker ids add architect1, architect2; the provider paragraph says findings are reported as Issues; Workers' list adds the architects. Everything else of the task is done and verified (build, spec-validation apart from this link, 857 tests).
  Not handled here (decision): module.operations and module.workers are not among the task's Modules, and the brief asks to escalate anything that changes another Module's Spec
  Options: let this task make those wording edits in module.operations' and module.workers' Specs; add module.operations and module.workers to the task's Modules, then I make the edits; make the edits in a separate task and merge it before this one
  Recommendation: let this task make the wording edits: they only restate this task's promises in the catalog, and delivery cannot pass without the catalog row

```json
{
  "level": "task-session",
  "actor": "task session (task panel-architects)",
  "code": "catalog_outside_modules",
  "detail": "Removing concept.review-memory (developer decision 6) leaves a dangling glossary link in module.operations' catalog row for spec_review (specs/concorde/execution/operations/module.md:54), so spec-validation fails and delivery is blocked until that row changes. The same Spec still says spec_panel's worker ids are reviewer1..reviewer5 and chair with task type review-spec only, that a bound spec_review changes the reviewed Modules' review memory, and (its #uses-spec-review paragraph) that the provider keeps findings in the review memory. module.workers' entry (specs/concorde/execution/workers/module.md:344) also lists spec_panel's worker ids without architect1/architect2. The edits are wording only: catalog row spec_review 'May change' -> no (it reports its findings as Issues, which the primary worktree keeps); spec_panel task types review-spec, review-architecture for its architects and its chair when it has architects; worker ids add architect1, architect2; the provider paragraph says findings are reported as Issues; Workers' list adds the architects. Everything else of the task is done and verified (build, spec-validation apart from this link, 857 tests).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "module.operations and module.workers are not among the task's Modules, and the brief asks to escalate anything that changes another Module's Spec"
  },
  "options": [
    "let this task make those wording edits in module.operations' and module.workers' Specs",
    "add module.operations and module.workers to the task's Modules, then I make the edits",
    "make the edits in a separate task and merge it before this one"
  ],
  "recommendation": "let this task make the wording edits: they only restate this task's promises in the catalog, and delivery cannot pass without the catalog row",
  "causes": []
}
```

## Escalated to the main agent, 2026-09-30T20:31:32Z

- **task-session** task session (task panel-architects): `review_memory_findings_dropped`
  Deleting the review memory (developer decision 6) removes the 8 tracked files under .concorde/reviews/spec/ with 36 open findings, 21 of them blocking: module.concorde 5 open (2 blocking), module.distribution 5 (3), module.e2e 3 (1), module.execution 9 (5), module.main-session 9 (6), module.workers 5 (4), module.dogfood-scenarios and module.operations none. They stay in Git history at the task's base commit. They carry severity, not a tier, and some may be stale, so migrating them as Issues would need a tier chosen for each and would create Issues no current review confirmed.
  Not handled here (decision): dropping these findings from the working tree discards recorded review work, which is a major-impact decision
  Options: leave them in Git history and let later spec_review or spec_panel runs of those Modules report what still stands as Issues; migrate every open finding into an Issue now, blocking as decision-needed and advisory as suggestion
  Recommendation: leave them in Git history and re-review those six Modules with spec_panel after this task merges

```json
{
  "level": "task-session",
  "actor": "task session (task panel-architects)",
  "code": "review_memory_findings_dropped",
  "detail": "Deleting the review memory (developer decision 6) removes the 8 tracked files under .concorde/reviews/spec/ with 36 open findings, 21 of them blocking: module.concorde 5 open (2 blocking), module.distribution 5 (3), module.e2e 3 (1), module.execution 9 (5), module.main-session 9 (6), module.workers 5 (4), module.dogfood-scenarios and module.operations none. They stay in Git history at the task's base commit. They carry severity, not a tier, and some may be stale, so migrating them as Issues would need a tier chosen for each and would create Issues no current review confirmed.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "dropping these findings from the working tree discards recorded review work, which is a major-impact decision"
  },
  "options": [
    "leave them in Git history and let later spec_review or spec_panel runs of those Modules report what still stands as Issues",
    "migrate every open finding into an Issue now, blocking as decision-needed and advisory as suggestion"
  ],
  "recommendation": "leave them in Git history and re-review those six Modules with spec_panel after this task merges",
  "causes": []
}
```

## Verification (2026-10-01)

- Build, `build --check`, the Spec review, main-session and full test suites pass on the task branch
  merged with main (857 passed, 4 skipped). `spec-validation` has one error left, the
  `concept.review-memory` link in module.operations' catalog row, escalated (`catalog_outside_modules`).
- **Live `spec_panel` on module.issues, run `r-20260930T203110-spec_panel-d13c3b88`: `failed`
  (not ok).** Three reviewers (review-spec) and both architects (review-architecture) finished,
  35 worker findings; the chair merged them into 10 blocking findings and 6 suggestions and rejected
  3, accounted on its first attempt. Reporting the first Issue failed with the Issue store's
  `io_error` (the file transaction could not write `.concorde/issues/` of the primary worktree from
  this session's Bash sandbox, which started before issue-writes-in-sessions widened it), so the
  Module is `incomplete` with `issues_unreported` over that error, every finding kept in the payload
  with `issue: null`, and nothing written to the primary worktree. Not worked around, as the main
  agent asked. The architects' findings include two this task's escalation already covers
  (Operations' obsolete review-memory account) and real ones about module.issues for a later review.

## Report 1 to the main agent (spec-review quality criteria), 2026-09-30T20:42:44Z

panel-architects: work done and verified except one blocker, two escalations need your answer before task-validation/delivery.

DONE (commits f25f83a1, 81f03f42 on concorde/panel-architects, main 44b46dd3 merged in as you asked):
- spec_panel: architects architect1/architect2 (--architects 0-2, default 2) under the Module's review-architecture grant, in parallel with the reviewers; findings labelled a<n>.<m>, accounted by the chair like r<n>.<m>; the chair runs under review-architecture when there is an architect (to verify their findings), merges everything and gives each finding its Issue tier. Payload v3 adds architecture_identity.
- spec_review and spec_panel report every finding that stands as an Issue from the Operation's host (bound and unbound), never from a worker; workers receive the Module's earlier Issues (open, owned by the Module, reported by a review), name the one a finding updates (`earlier`) and list resolved ones; the host checks a named Issue was offered, appends at the revision read just before, creates otherwise, never closes; resolved ones are listed for the task session. The verdict follows blocking-tier Issues that stand (reported now or carried). An Issue-store refusal makes the Module incomplete (issues_unreported over the store's link), never an Issue. Payload v4.
- Review memory removed: memory.py, its contract, concept.review-memory, the 8 tracked .concorde/reviews/spec/ files. The unchanged-Specs shortcut and --force are dropped (nothing left to record it in).
- Findings carry tier/title/impact instead of severity. The checklist no longer restates a bar: the host appends the project's Protocol copy's Writing guidance + Evaluating a Spec to every review brief (the build refuses a Protocol include in worker prompts).
- workers.json: architect1 gpt-6-astra high, architect2 gpt-6.1-sol high.
- Glossary: concept.issue-tier (owner module.issues, anchored in Issues' #tiers); review-finding and review-verdict updated.
- Main-session guidance/Spec: new "After a review" guidance (req/scenario main-session.review-issues), architect worker ids, and your requested phrase fix: a task session never writes an Issue record from Bash, although its sandbox lets runs it starts report findings (skill, task-session.md, main-session module.md and requirement).
- docs/using-concorde.md (owned by no Module) updated.
- Verification: build, build --check, full suite 857 passed / 4 skipped. spec-validation: one error left, see escalation 1.
- Live spec_panel on module.issues, run r-20260930T203110-spec_panel-d13c3b88: failed (not ok). 3 reviewers + 2 architects finished, 35 findings -> chair's report of 10 blocking + 6 suggestions, 3 rejected, accounted first try. The first Issue write was refused with io_error (my session's sandbox predates issue-writes-in-sessions), so the Module is incomplete with issues_unreported over that chain; nothing written to the primary worktree; not worked around. A run from a newer session should record them.

ESCALATIONS (both recorded; full chains in the decision log):
1. catalog_outside_modules: removing concept.review-memory leaves a dangling glossary link in module.operations' catalog row (specs/concorde/execution/operations/module.md:54), which fails spec-validation and blocks delivery. That Spec also still lists spec_panel's worker ids and task type without architects, says a bound spec_review changes the review memory (row and #uses-spec-review paragraph), and module.workers (workers/module.md:344) lists spec_panel's ids without the architects. Options: (a) let this task make those wording edits; (b) add module.operations and module.workers to the task; (c) separate task merged first. Recommendation: (a).
2. review_memory_findings_dropped: the deleted memories held 36 open findings (21 blocking) for module.concorde, distribution, e2e, execution, main-session, workers; they stay in Git history. Options: (a) leave them in history and re-review those Modules with spec_panel after the merge; (b) migrate them now as Issues (blocking -> decision-needed, advisory -> suggestion). Recommendation: (a).

Issues resolved by this task: none. After your answer I make the edits (if a), rerun spec-validation, task-validation and delivery.

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-01T04:39:51Z

Escalation 1 (catalog_outside_modules): option (a), decided by the main agent: make the wording edits in module.operations' and module.workers' Specs in this task (the dangling concept.review-memory link, spec_panel's worker ids and task types with the architects, the review-memory sentences of spec_review's row and #uses-spec-review). They only keep those Specs consistent with this task's change and change no promise of their own. Escalation 2 (review_memory_findings_dropped): option (a), decided by the developer: leave the 36 open findings in Git history, migrate nothing; after the merge the main agent re-reviews module.concorde, distribution, e2e, execution, main-session and workers with spec_panel. Then rerun spec-validation, task-validation and delivery, and report.

## Task session, after the answer to report 1 (2026-10-01)

- Made the wording edits the main agent decided (escalation 1, option a), commit aa79fa2f:
  module.operations' worker-id paragraph, catalog rows (`spec_review` May change: no; `spec_panel`
  task types `review-spec`, plus `review-architecture` for its architects and for its chair when it
  has an architect; worker ids with `architect1`, `architect2`) and #uses-spec-review (findings
  reported as Issues from the host, bound and unbound; the workspace does not change);
  module.workers' worker-id example with the architects. `spec-validation`: 0 errors, 0 warnings.
- Escalation 2 (developer, option a): nothing migrated; the deleted memories stay in Git history.
- Full suite on aa79fa2f: 857 passed, 4 skipped.
- **Live `spec_panel` on module.issues, run `r-20261001T044130-spec_panel-5cc8e2f7`: `ok`, verdict
  `changes_required`.** reviewer1-3 (review-spec) found 11/7/7, architect1-2 (review-architecture)
  5/4; the chair merged them into 15 findings (1 decision-needed, 4 preferred-fix, 5 obvious-fix,
  5 suggestion), rejected 2, and the host reported each as a new Issue in the primary worktree
  (0 earlier Issues offered). Those Issues are module.issues' and are left for later work.
- Defect seen in that run and fixed (commit 3743e8c1): workers wrote `"earlier": "none"` on new
  findings, which the chair copied, so the host listed 15 `ignored` earlier-Issue names. The host
  behaved as specified; the reviewer checklist and the chair brief now say a new finding has no
  `earlier` at all. The worker schema was not tightened: a schema refusal stops the panel
  (`panel_short`), which a harmless placeholder should not.

## Report 2 to the main agent (spec-review quality criteria), 2026-10-01T05:03:15Z

panel-architects delivered: delivery commit b4a54ba5 on concorde/panel-architects (run r-20261001T045708-delivery-1b7a6c17, ok; task-validation r-20261001T045116-task_validation-5d60bf49 ready).

Done since your answer:
- Escalation 1 (your option a), commit aa79fa2f: module.operations' worker-id paragraph and catalog (spec_review May change: no; spec_panel task types review-spec, plus review-architecture for its architects and for its chair when it has an architect; worker ids add architect1, architect2) and #uses-spec-review (findings reported as Issues from the host, bound and unbound; the workspace does not change); module.workers' worker-id example adds the architects. No promise of either Module changed. spec-validation: 0 errors, 0 warnings.
- Escalation 2 (developer, option a): nothing migrated; the 36 old findings stay in Git history. Re-reviewing module.concorde, distribution, e2e, execution, main-session and workers with spec_panel after the merge is yours, as you said.
- Verification: build, build --check, spec-validation clean; full suite 857 passed, 4 skipped.

Live spec_panel evidence: run r-20261001T044130-spec_panel-5cc8e2f7 on module.issues ended ok, verdict changes_required. 3 reviewers (review-spec) and 2 architects (review-architecture) found 34 findings. The chair merged them into 15 and rejected 2. The host reported each of the 15 as a new Issue in the primary worktree (0 earlier Issues offered): 1 decision-needed (I-94d306a4..., published but uncommitted Issues lack a recovery contract), 4 preferred-fix, 5 obvious-fix, 5 suggestion. They are module.issues' Issues for later work. Two of the suggestions concern Tracing's and Dogfooding's text.

A decision I made without you: the run showed workers writing "earlier": "none" on new findings. The chair copied it and the host listed 15 ignored earlier-Issue names; the host behaved as specified. Fixed in prompts (commit 3743e8c1): the reviewer checklist and the chair brief say a new finding has no `earlier`. I did not tighten the worker schema, because a schema refusal stops the panel (panel_short).

Issues resolved by this task: none. Still open: the 15 new module.issues Issues and the re-reviews above.

## Closed: merged, 2026-10-01T05:03:33Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b4a54ba5667fa3e0324748efa5e9079d54499201 into main and closed it as merged. Nobody answers a report after that.
