# Decision log: review-workers

Goal: Fix the spec review findings of Workers and Operations

## Brief (main agent, 2026-09-30)

The developer asked for a spec review after `project-model-names` merged and said: fix the small
problems yourselves, and ask the developer only at the end about what needs their decision.

The unbound `spec_review` run `r-20260929T203136-spec_review-a3b63738` examined main at 14e573aa
and ended `changes_required`. Its result, with every finding's evidence and suggestion, is
`/home/zhenyu/concorde/.concorde/unbound/r-20260929T203136-spec_review-a3b63738/result.json`
(read-only for you); this task covers the findings of module.workers, module.operations.

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

Leave module.workers f.6 (Claude Code read denial vs Harness's late-created-file limit) UNCHANGED: it touches the boundary and is the developer's decision. Analyse it and give options (narrow the promise to the provider's boundary and state the limit; or close the gap, e.g. a read-side PreToolUse hook checking the grant) with your recommendation and its cost. For f.11 (provider contracts not supplied), first check whether Workers' declarations omit the Harness contracts it relies on; add the missing declaration if so; if the declarations are right, the spec_review Operation failed to supply them: say so with evidence (a Concorde defect in module.spec-review, outside this task).

### Process

Create what Git ignores (`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`). Format,
`build --check`, `spec-validation`, `registry --write` if a module block changes, the relevant tests
and once the full pytest suite on the final input. Then run `python3 scripts/concorde.py run
spec_review` once in the task worktree (bound; it reviews this task's Modules and updates their
review memory) and handle its findings the same way, without looping further. Then `task-validation`
and `delivery`, and report to the main agent with SendMessage: what you fixed, the findings you
judged wrong, and the open questions for the developer with options and recommendations.

## Task session: fixes of the review r-20260929T203136-spec_review-a3b63738 (2026-09-30)

Commit c18dfd92 on `concorde/review-workers`. Every finding of module.workers and module.operations
was fixed except Workers f.6, left unchanged as the brief says (analysis below).

- **Workers f.2 (implement grant with `names`)**: the finding is right; Spec core and the Harness
  give an `implement` grant the project's whole code `ro`, never `names`. The normal-run example,
  `scenario.workers.fenced-run` and `scenario.workers.pi-fenced-run` now give the other Module's
  file `ro`; the example says `names` belongs to task types that do not read code, such as
  `understand`. The fenced-run test no longer overrides the fixture's real grant to `names`. The
  live pi test (`test_pi_live.py`, run only with `CONCORDE_LIVE_PI=1`) still expected
  `src/bmod/secret.py` hidden, which the real implement grant makes `ro`; it now uses
  `checks/a_check.py`, which no Module binds, and its default model is `local-openai/gpt-6-astra`.
- **Non-ok result**: the live pi test could not be verified here: two runs ended `pi_failed` with
  the pi process's "Connection error." from the model service after 4 turns (environment, not a
  boundary outcome). It is not part of the default suite.
- **Workers f.3, f.4 (requirements with several obligations)**: split into one SHALL each. New
  identities: `req.workers.malformed-grant-named`, `req.workers.model-unsettled-refused`,
  `req.workers.model-map-refused`, `req.workers.model-map-named`, `req.workers.model-map-entry`,
  `req.workers.transcript-kept` (states the order before removal), `req.workers.rounds-limited`,
  `req.workers.pi-settings-generated`, `req.workers.pi-config-copies`;
  `req.workers.pi-settings-independent` now holds the "SHALL NOT read the user's pi settings.json"
  part. Same class, done proactively: `req.workers.proxy-passed` now says only "exactly the proxy
  variables that Proxy derives", since the loopback and no-proxy clauses restated that section;
  its meaning, on which the Task session relies, is unchanged.
- **Workers f.5 (failure scenarios without the rounds' precedence)**: `audit-violation` and
  `invalid-result` are qualified (within timeout and limits; valid result / clean audit), and two
  overlap scenarios added with tests: `scenario.workers.violation-and-timeout` (`worker_timeout`
  wins, the detail and the round's audit name the violation) and
  `scenario.workers.violation-and-invalid-result` (`audit_violation` wins, the detail says the
  result was invalid, no worker cause). The code already behaved so. The `@verifies` of
  `scenario.workers.timeout` sat on the interrupted-run test; it now sits on the timeout test.
- **Workers f.7 (scenarios switching setups in THEN/BUT)**: split the four named (`own-proxy` /
  `no-proxy`, `glossary-entries` / `glossary-foreign-entry`, `model-custom-accepted` /
  `model-refused`, `model-not-enabled` / `enabled-models-required`) and, as the same class under
  the Protocol's rule that situations with different outcomes get their own scenarios, also
  `model-level-refused`, `models-listed-mapped`, `models-listed-unmapped`,
  `models-backend-missing`, `models-standalone-missing`, `model-config-v1`, `limits-default`,
  `retired-configuration-beside`, `model-map-relative`, `model-map-checked`, `model-map-invalid`.
  `brief-terms` and `pi-settings-independent` now state their variant in the GIVEN. Tests that
  already covered both halves declare both identities; the four named splits have split tests.
- **Workers f.8, f.9, f.10**: `backend-switch` says configuration resolution chooses `claude` and
  model-map resolution then refuses before launch; the normal-run diagram labels checks "valid ok
  result, clean audit" and records every other outcome; the progress diagram's `ok` edge requires
  passing checks.
- **Workers f.1 (readability)**: Core concepts now hold brief definitions only (every concept
  anchor kept); the detail moved after the overview into new Details sections "Where a run's files
  live", "The brief", "Audit, rounds and record", "Resolving the backend" and the start of
  "Choosing worker models". No promise changed.
- **Workers f.11 (Harness tables not supplied)**: a real omission of Workers' declarations, not a
  spec_review defect: Workers links `harness/pi.md#read-table`, `#write-table` and
  `harness/claude-code.md#tool-sets` but selected only the Harness entry through `uses`
  (`relies_on` names concepts all defined in `harness/module.md`). Added `includes` of kind
  `document` for `document.harness.claude-code` and `document.harness.pi`; registry refreshed.
  This widens the Spec context of tasks bound to Workers by those two read-only documents.
- **Operations f.1**: `req.operations.grant-frozen` split out of `workers-through-workers`.
- **Operations f.2**: `req.operations.model-work-only` now obliges an Operation to ask Workers to
  launch a worker on a run whose worker step settles the grant, backend and model, keeping the
  documented refusals; title "Every Operation has model work".
- **Operations f.3**: `worker-model-unavailable` (invalid configuration) split into it,
  `scenario.operations.worker-backend-missing` and `scenario.operations.worker-model-unmapped`,
  each with its own valid setup; the runner test that covers all three declares all three.
- **Operations f.4**: `worker-model` states that the worker's model has no level of its own and no
  more specific entry sets one (the test's configuration already was so).
- **Operations f.5**: the standard worker sequence's explanation and its overview diagram say that
  checks run when the step asks for them, add the step's own validation and its repair round, and
  distinguish configured checks from a provider's structural validation.
- **Workers f.6, for the developer** (left unchanged): see the task's report; recommendation to
  narrow the Claude Code promise to paths existing when the deny rules are generated.

## Task session: the bound spec_review r-20260929T210131-spec_review-dca24fef (2026-09-30)

Status `ok`, verdict `changes_required`: module.operations `accepted`; module.workers 4 blocking
and 1 advisory findings (review memory f.1–f.5, committed with this step). Handled once, as the
brief says, without another review:

- **f.1** (read denial vs files created after the deny rules) is the earlier f.6: left unchanged
  for the developer.
- **f.2**: `req.workers.pi-file-tools` split; the denial reason is now
  `req.workers.pi-denial-reason`.
- **f.3**: `invalid-result` and `violation-and-invalid-result` now require an agent process that
  ended normally with no process error of its backend, so `pi_failed`/`claude_failed` keep their
  precedence.
- **f.4**: the finding shows a wrong promise: a host killed by `SIGKILL` cannot finish its records
  or remove its runtime directory. The entry, the runtime-directory text, the progress-file text,
  `req.workers.runtime-removed` and `scenario.workers.interrupted-run` now limit finalization to
  interruptions the host can handle, and the entry says a killed host leaves the record `running`
  (shown `lost` by Tracing) and the runtime directory, credential copies included, to the system's
  temporary-file cleaning, as the Execution runner already says of its unbound checkout. No code
  change. Reported to the developer as a known limit touching credentials.
- **f.5** (advisory): ten scenarios whose observations are Claude Code's now state the Claude Code
  backend in their GIVEN.

## Main agent request: who runs Operations (2026-09-30)

From review-main-session's review f.9: `operations/module.md` "Running an Operation" said the main
agent or a task session invokes Operations in its task worktree, against the rule that every task
goes to a task session and the main agent never works inside a task worktree. It now says the task
session runs a task's Operations, directly or through a workflow, in its task worktree, and the main
agent runs only unbound runs of Operations, from the primary worktree.
- **Non-ok result**: the full suite on the final input ran 792 passed, 4 skipped, 1 failed:
  `test_runner.py::RunnerTests::test_a_detached_run_is_announced_and_finishes_on_its_own` raised
  `workspace t1 is busy`: its detached `task-validation` run still held the fixture's workspace lock
  under full parallel load. It passes alone and in two parallel reruns of `tests/concorde/execution`.
  It is a timing flake in a test this task did not change, outside its Modules, so I left it alone
  and report it.

## Closed: merged, 2026-09-29T21:10:59Z
