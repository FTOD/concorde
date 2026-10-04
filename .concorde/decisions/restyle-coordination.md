# Decision log: restyle-coordination

Goal: Rewrite the existing Specs and prompts of its scope to Protocol 16.2's Sentence style, unchanged in meaning, with pi on gpt-6.1-sol: Coordination


## Task brief (main agent, 2026-10-04)

### Developer's decisions this task carries out

Task `spec-style` (merged at d4423f70) added Protocol 16.2's chapter `protocol/style.md`
"Sentence style" and the warning checks `CHK.style.sentence-length` (over 35 words),
`CHK.style.semicolon` and `CHK.style.one-obligation`. Read that chapter first: it is the rule set
for this task. On 2026-10-04 the developer decided:

1. **All existing text is rewritten to the new style now**, not only new or changed text. The
   developer explicitly rejected an incremental migration and does not mind a full rewrite.
2. **`prompts/` follows the same style** as Concorde's own extra requirement
   (`prompts/development/skill.md`, measured with `python3 scripts/development/check-style.py`).
3. **The rewriting is done by pi sessions on project model `gpt-6.1-sol` at reasoning `medium`**:
   `pi -p --no-session --model local-openai/gpt-6.1-sol --thinking medium "<prompt>"`, run from
   your task worktree. Model spend needs no permission (the developer has plenty of GPT tokens).
   There is no Concorde Operation for this, so drive pi directly. You decide how to batch the
   work (one document or a few small ones per pi call works well) and how many pi processes run in
   parallel (at most 4, on disjoint files), each in background Bash.

### What the rewrite must achieve

- **Meaning stays exactly the same.** This is a style rewrite, not a Spec change. Every
  obligation, condition, exception, actor, value, error code, path and term stays. A requirement
  may be split into several sentences or into obligation + colon + list (see the example in
  `style.md`), but no condition may be lost, added or moved to another obligation.
- **Apply every rule of `style.md`**, the decidable ones and the judged ones: one fact per
  sentence, descriptive sentences of 25 words or fewer as the target, lists for three or more
  conditions/cases/items, the condition before the statement, no semicolons, a named actor in the
  active voice in requirements, simple tenses, glossary terms with exactly their defined meaning.
- **Target: zero `CHK.style.*` warnings** in the documents of your scope (and zero problems from
  `check-style.py` on your prompt/protocol paths). A sentence you judge cannot be split without
  losing precision may stay; record each such exception, with its location and reason, in this log.
- **Do not change structure**: requirement and scenario headings and identities, Markdown anchors
  and heading text (metadata `meaning` anchors and links point at them), links and their targets,
  inline code, code fences, contract schemas and examples, D2 diagrams, tables' identities, and
  the `*.md.json` metadata files must stay as they are. Changing them would ripple into the
  registry and other tasks' files.
- **Stay inside your scope's paths below.** Other rewrite tasks run in parallel on the other
  Module subtrees; `specs/concorde/glossary.json` belongs to `restyle-root` alone, and `protocol/`
  with the Protocol copy and manifest to `restyle-spec-tooling` alone.

### How to verify

1. Before trusting a pi rewrite, read its whole diff yourself and compare meaning sentence by
   sentence, above all in `requirements.md`, `contracts.md` and `scenarios.md`. A second pi call
   given the old and new text, asked only to list meaning differences, is a useful independent
   check; you decide the fix for each difference it lists. Repair drift yourself or with another
   pi round.
2. Run `python3 scripts/concorde.py spec-validation` (0 errors, and count your scope's
   `CHK.style.*` warnings), `python3 scripts/development/check-style.py <your prompt paths>`,
   `python3 scripts/concorde.py build --check`, and the tests that read the files you changed
   (some tests may assert prompt or Spec phrases: update a test only when the phrase is pure
   wording, never to hide a meaning change). Run the full pytest once before delivery.
3. Format Markdown under `docs/` with Prettier only if you touch it (you should not need to).
4. Commit verified steps, then `task-validation` and `delivery`.

### Report

In your delivery report give the `CHK.style.*` warning counts of your scope before and after,
the `check-style.py` counts of your prompt/protocol paths before and after, the exceptions you
kept, and every meaning difference the review found with how you resolved it. Record every
decision taken without the developer and every non-`ok` result in this log.

### Left for the session to decide

Batching, prompts for pi, parallelism (at most 4 pi processes), the order of documents, and which
long sentences are justified exceptions. Escalate together anything that would change the
decisions above, such as a sentence whose only faithful rewrite needs a Spec meaning change.

### Scope of this task

Paths: `specs/concorde/coordination/**` (Markdown only) and `prompts/main-session/`. Baseline worst documents: coordination/main-session/module.md 177 warnings, coordination/tasks/module.md 169.

## Task session (2026-10-04)

### Baseline

- `spec-validation` before: 0 errors. `CHK.style.*` warnings in `specs/concorde/coordination/**`:
  721 (503 `CHK.style.sentence-length`, 218 `CHK.style.semicolon`, 0 `CHK.style.one-obligation`).
- `check-style.py prompts/main-session`: 89 problems (62 sentence-length, 27 semicolon, 0
  one-obligation): claude-md.md 3, skill.md 56, task-session.md 30.

### Decisions on how the rewrite runs

- Each document is cut at its level-2 headings (outside fences) into chunks of at most about 1600
  words, kept in the job's scratch directory with a read-only copy of the original. Each pi call
  rewrites one chunk in place and runs `check-style.py` on it, then the chunks are concatenated
  back. Reason: small inputs keep pi's attention on every sentence, and disjoint chunk files let 4
  pi processes run in parallel without touching the worktree until reassembly.
- The pi prompt states the brief's meaning and structure constraints, plus the Protocol's own
  validity rules: a requirement's first paragraph stays one sentence with exactly one `SHALL`, and
  a long scenario step is split into `AND` steps, never a nested list.
- A pilot on `task-session/requirements.md` runs first, so the prompt can be corrected before the
  other chunks run.
- Pilot result (task-session/requirements.md): pi reached 0 style problems with no exceptions. I
  corrected one drift by hand: in `req.task-session.stopped-before-close` pi had moved the refusal
  into a list item under "under this condition:", which reads as a second rule. The statement is
  now one 33-word sentence keeping the refusal attached to the stop. The pi prompt now forbids that
  pattern and asks to keep the ~100-column wrapping.
- Prompt chunks also get the exact strings that `tests/` assert in that prompt, to keep verbatim, so
  that tests change only where a phrase really had to change.
- Tables are left unchanged, as the brief's structure list says. The style checks do not measure
  them. This keeps the long prose cells of the command table in `tasks/contracts.md` as they are.
- A first queue attempt failed with `gateway_concurrency_limit` (shared with the other restyle
  tasks). The runner now retries with backoff and restores the chunk before each retry.

## Main agent note (2026-10-04): lessons from restyle-root, delivered first

restyle-root found about 40 major meaning drifts in pi's rewrites. Check for these patterns in
particular:

- a dropped "only", "itself" or "alone";
- an invented actor in a requirement, such as "Git SHALL track" or "Coordination SHALL count";
- an inverted relation;
- an obligation moved out of the SHALL statement into description.

pi also broke two Protocol rules that spec-validation enforces as errors:

- A requirement statement must be one sentence with one SHALL. Use an obligation, a colon and a
  list instead.
- Scenario steps may not hold nested lists, and "- AND alternatively" steps are invalid.

Do not compress sentences into telegraphic style to meet the word limit. Keep the articles, write
no hyphenated noun chains such as "primary-worktree folder", and break up long noun clusters.
STE itself forbids omitting sentence parts. A split into two full sentences is always better than
compression.

The shared pi gateway refuses with `gateway_concurrency_limit` under load. Six tasks share it, so
use at most 2 parallel pi lanes and retry with backoff.

## Task session (2026-10-04), after the main agent's note

- Read the note on restyle-root's lessons. Reduced the queue from 4 to 2 parallel pi lanes, added
  the note's drift patterns and the ban on telegraphic compression to the pi prompt for every chunk
  not started yet, and I check every finished chunk for a changed count of "only", "itself",
  "alone", "never", "every" and requirement keywords, besides reading its whole diff.
- So far I read every finished chunk's diff and repaired each meaning drift by hand (list kept in
  the delivery report). Chunks finished before the note get the same keyword-count check and a
  telegraphic-style pass.
- Full pytest (2026-10-04, after the prompts commit): 1 failed, 1252 passed, 5 skipped. The failure,
  `tests/concorde/execution/test_runner.py::RunnerTests::test_a_detached_run_is_announced_and_finishes_on_its_own`
  (`AssertionError` at line 1305, progress file not found after the announcement), reads none of
  this task's files and passed alone 3 times. Recorded as Issue I-7f491393d6e85610886f47c0426cf37f
  (module.execution, decision-needed, low). This task does not fix it.

## Task session (2026-10-04): result of the rewrite

### Counts

- `CHK.style.*` warnings in `specs/concorde/coordination/**`: 721 before (503 sentence-length, 218
  semicolon), 0 after. `spec-validation`: 0 errors before and after.
- `check-style.py prompts/main-session`: 89 before (62 sentence-length, 27 semicolon), 0 after.
- Structure check against the task's base: every heading, fence, table, link target and HTML
  anchor is unchanged, no `*.md.json` changed, and no inline code span was removed.

### How it was verified

- I read the whole diff of every one of the 62 chunks myself and repaired each meaning drift by
  hand (list below). For every chunk, an automatic count compared "only", "itself", "alone",
  "never", "not", "unless", "before", "after", "once" and the requirement keywords between the old
  and new text. No "only", "itself" or "alone" was dropped.
- A second pi call (same model) compared old and new text of every requirements, contracts and
  scenarios chunk and listed meaning differences. I checked each listed difference: the real ones
  are repaired (marked "found by the pi meaning review" below), and the few I kept are named with
  the reason.
- `build --check` passes. The guidance tests (`tests/concorde/main_session/test_guidance.py`)
  assert prompt phrases. Their strings now follow the new wording, each still asserting the same
  rule. `tests/concorde/distribution/test_guidance_parts.py` required two paragraphs to keep naming
  the part whose command they mention. I rejoined one split paragraph and kept one command series
  inline for that.

### Exceptions kept

- No sentence over 35 words and no semicolon in prose remains, so no measured exception.
- Judged rule "lists for three or more", kept inline on purpose:
  - Series inside scenario steps stay inline, because a scenario section may hold no nested list.
    Turning items into `AND <item>` steps changes the scenario.
  - Series inside "This illustrates …" sentences of scenario sections stay inline for the same
    reason.
  - Sentences that introduce a D2 diagram or a fence with a colon stay right before it.
  - Short series of code spans, such as "`checks`, `resume` and `abort` are the command's
    `--check`, `--resume` and `--abort`", stay inline. In prompts this also applies where a test
    asserts the phrase ("deliver again and report"), and where the part-guard test needs "where
    the spec, execution and method parts are installed" in the same paragraph as the commands.
- Tables, including the long prose cells of the command table in `tasks/contracts.md`, are
  unchanged. The brief lists them as structure, and the style checks do not measure them.

### Meaning drifts found and repaired
- main-session/contracts.md (register_wait): pi made "The server" the actor of "runs that same `concorde task wait`" and of "never takes or hands over a lock for the session", where the old subject was `register_wait`. The server does take and hand over locks for `task_merge`, so this contradicted the glossary. Restored `register_wait` as the subject of both.
- main-session/module.md (worker models): pi wrote "Only when the developer asks, the guidance tells the main agent to change the file", which scopes "only" over the guidance. Restored "tells the main agent to change the file only when the developer asks".
- main-session/module.md (Purpose): "the project MCP server beside it" (the guidance) became "beside the main agent". Restored "beside the guidance".
- main-session/module.md (Issues): "recurrence uses `issue_reopen`" became "the closer uses `issue_reopen`", naming an actor the old text did not. Restored an actorless "A recurrence uses `issue_reopen`".
- main-session/module.md (project MCP server, Issues): "each as `concorde issues` does and without waiting for the merge lock" covered all six Issue tools; pi limited it to the three write tools. Restored "All six tools work as `concorde issues` does, without waiting…".
- main-session/module.md (Task sessions receive the server): "register a wait, which answers it" became "the wait answers it". Restored `register_wait` as the subject.
- main-session/module.md (merge diagram caption): the caption "A merge through the server … with who holds the locks" became the claim "A merge … shows who holds the locks". Rewrote it as "The diagram below shows a merge …".
- main-session/module.md (Why it is built this way): "its delivering command's checks, `delivery`'s readiness where the method part is installed" is an apposition (the checks are that readiness). pi made it "checks and … readiness", two things. Restored the apposition with "which are".
- main-session/requirements.md (req.main-session.new-files): pi's list "create every new implementation file … as follows: - Outside the directories its Modules' realizations bind." read as an instruction on where to create files, where the old text restricts which files are meant. Rewrote it as the obligation about "every new implementation file the work needs outside the directories …" with a two-item list: create before launching the filling worker, with the least valid content.
- main-session/requirements.md (realization entry): pi used a one-item list and put "Before launching the worker" in front of the guidance's SHALL. Restored one sentence that ends "… before launching that worker".
- main-session/module.md (Use the project's terms): "tells … to raise a missing definition" became the fact "those sessions raise it". Restored "It also tells them to raise …".
- main-session/scenarios.md: pi turned series inside scenario steps into a step ending in a colon followed by `AND <item>` steps (for example "WHEN an agent reads how to wait for any of these:" then "AND a run"), which changes what the scenario says. Restored the inline series where the step was short enough, or split it into complete steps ("AND to use `--abort` when …"). The prompt for the remaining chunks now forbids this.
- main-session/scenarios.md chunk 2 ran on the first prompt and turned many series into colon steps followed by `AND <item>` steps, and "This illustrates" sentences into lists of `AND [link]` items. I discarded that output and re-ran the chunk with the corrected prompt.
- task-session/module.md (Purpose): "Task sessions is how the main agent delegates …: it starts a task session for every task" (it = Task sessions) became "The main agent starts a task session for every task". Restored Task sessions as the subject.
- task-session/module.md (Workflows, Execution): "level 3, which a task session may start" and "level 4, which a task session runs directly" became "start Workflows" and "runs Execution", naming the Modules; "which stays the main agent's" (merging and closing) became "The task stays the main agent's"; "has rebound" became "rebounds". Restored each.
- tasks/module.md (Inside, task state): two sentences that introduce a D2 diagram with a colon were turned into a list placed between the sentence and the diagram ("The diagram shows how these fit together: - Record. - Log. - State.", and a list of the states as if they were what the state is derived from). Restored single introducing sentences. Also removed a duplicated `worktree_not_ignored` sentence pi wrote twice, and restored "each bound Module the worktree does not register" where pi wrote "unregistered".
- tasks/requirements.md (merge requirements): pi wrote several requirement statements in a telegraphic style ("close eligible Issues and report failures without blocking completion", "use its process's starting Concorde code", "paths in ended tasks' worktrees … in other delivered tasks' worktrees that wait") and split `req.tasks.merging-recorded` into a list that repeated itself. Rewrote each as a full obligation with a colon list. pi also turned "as far as the filesystem allows, which records who wrote nothing" into "This records who wrote nothing", which inverts the sense. Restored "The filesystem records nothing about who wrote a change."
- main-session/contracts.md (refusals), found by the pi meaning review: pi's "Otherwise, it is the tool's own `component` link" generalized the old "or the tool's own link" to every refusal not of Tasks (a Tracing refusal keeps its own link). Now "When the tool itself refused, …". The review also caught my own earlier repair "The tools' own refusal codes are:", wrong because the table also lists forwarded Tasks and Tracing codes. Now "The refusal codes are:".
- main-session/requirements.md, found by the pi meaning review: "only these activities take place in the primary worktree" widened "only housekeeping … and the commit … are made" to every activity. Now "only these changes are made". In `req.main-session.workflows`, "for the task session to start inside the task worktree" had moved out of the SHALL statement. It is back in the statement ("which the task session starts inside the task worktree"). "they were taken" (decisions and problems) had narrowed to "the decisions"; restored "they".
- main-session/requirements.md, found by the pi meaning review: in about a dozen statements pi had fronted the condition of an instruction ("When X, the guidance SHALL tell the main agent to do Y"), which makes the condition limit the guidance's obligation instead of the instructed action. Restored the condition inside the instruction ("SHALL tell the main agent, when X, to do Y" or "… to do Y when X") in merge-interrupted, merge-abort, task-session-merge-refusal, merge-conflict, update-merge, task-session-primary-merge, unbound-failure-task, task-session-plan-review-iterates, task-session-plan-review-disagreement, task-session-workflow-failure, task-session-reports, task-session-report-resent, reconcile-after-restart and project-mcp-no-channel. In project-mcp-presentation, the primary-worktree sources and "adds no other rule of its own" were back under the SHALL. "has written its answer" was restored (pi's "writes" excluded the overlap), and so was "its session to listen to it as a channel".
- main-session/requirements.md (Issues), found by the pi meaning review: the severity requirement had become "SHALL give every session that records an Issue and the main agent these instructions", giving both instructions to both; restored one instruction per recipient. The recovery rule had split "which `uncommitted_change` or a merge's `primary_dirty` names" off the record it qualifies; restored.
- tasks/contracts.md (commands), found by the pi meaning review: splitting "`merge`'s `rollback_failed`, a `check_failed` whose checks created paths, and a close that failed after the merge" into bullets dropped "`merge`'s" from the last two. Restored it on each bullet.
- main-session/scenarios.md, found by the pi meaning review: in scenario.main-session.change-through-task, three facts the task-session guidance tells the session were reassigned to "the main agent is told". Restored the task-session guidance as the teller. In the new-file scenario, "a new Spec document is not prepared this way" had become something "both say"; restored as a plain BUT step.
- main-session/scenarios.md (update-merge), found by the pi meaning review: my own repair "it makes only two merges of the primary branch into its task branch" counted merges and narrowed the exclusivity. Restored the old sentence, which fits the limit.
- main-session/scenarios.md (unbound runs), found by the pi meaning review: "these Operations run in a worktree without a binding" and "have `workspace` null" applied to the Operations generally. Now "such unbound runs". The review also said that splitting "fix an `obvious-fix` Issue alone and a `preferred-fix` one, reporting the fix it chose" ties the reporting to `preferred-fix` alone. Kept as it is, since the requirement it illustrates, req.main-session.issues-preferred-fix-reported, says exactly that.
- tasks/requirements.md (merge recovery and Issues), found by the pi meaning review: fronting "When the primary branch's head is the merge commit" on the `--abort` bullet seemed to condition the return to delivered as well; restored the condition after the reset. "A failure of the Issues … never keeps the merge from ending the task's sessions" had moved under the SHALL statement's "once its checks pass" conditions; it is a sentence of its own again, as its clause was. The review also flagged my "The filesystem records nothing about who wrote a change" as unlike the literal "which records who wrote nothing". Kept, since the module's own text ("nothing in it records who wrote a change") gives that meaning.
- task-session/scenarios.md (node figures): I rewrote "whose transcript records … a subagent transcript" as "the session has a subagent transcript", since the module says the subagent transcripts lie beside the transcript. The pi meaning review flagged this as a difference. Kept, for that reason.
- task-session/requirements.md, found by the pi meaning review: in req.task-session.transcript-kept, "never write into the history afterwards" had become a step of "handling the transcript"; it is an obligation of its own again. In req.task-session.removed, "as a best effort whose failure leaves the close as it succeeded" had left the SHALL statement; it is back in its list. "leaves the status `unknown`" had become "stays `unknown`"; now "is `unknown`".
- tasks/scenarios.md (merge refusals), found by the pi meaning review: my own repair had dropped an "or", so the branch and worktree conditions could read as qualifying "a task that is not delivered". Restored each "or".
- Besides these, many smaller repairs of wording or grammar were made without a meaning change,
  for example lowercase link text at the start of list items, a duplicated sentence, and "rebounds"
  for "has rebound".

### Decisions taken without the developer

- Scenario steps: a long step is split only into complete `AND`/`BUT` steps, never into a colon
  step followed by item steps.
- Guidance requirements keep the condition inside the instruction ("SHALL tell the main agent,
  when X, to do Y"), not fronted onto the guidance's obligation. This is the one exception to "the
  condition before the statement" in this scope, since fronting it changes which obligation the
  condition limits.
- Test strings in `test_guidance.py` follow the new wording (30 asserted strings). Each still asserts the
  same rule.

### Final checks

- Full pytest on the final commit 002084c0: 1 failed, 1252 passed, 5 skipped. The failure,
  `tests/concorde/tasks/test_wait.py::WaitTests::test_a_task_that_ended_elsewhere_ends_the_wait`
  (`wait_timeout` instead of `wait_unreachable`), reads none of this task's files and passed alone
  3 times. The earlier full run failed only on a different test (Issue
  I-7f491393d6e85610886f47c0426cf37f). Both are load-dependent. The wait one may be a lost wake-up
  in `concorde task wait`, so I recorded it as Issue I-d0e67ee6eaae595f9ee627a0a0b1b1b6
  (module.tasks, decision-needed, medium). This task, a style rewrite, does not fix either.

## Report 1 to the main agent (concorde-f8), 2026-10-04T09:58:44Z

restyle-coordination is delivered at c7f5fb22 (concorde: deliver restyle-coordination). Nothing is escalated and no decision is pending.

Counts:
- CHK.style.* in specs/concorde/coordination/**: 721 before (503 sentence-length, 218 semicolon), 0 after. spec-validation: 0 errors.
- check-style.py prompts/main-session: 89 before (62 sentence-length, 27 semicolon), 0 after.
- Structure check against base d4423f70: every heading, fence, table, link target and anchor is unchanged, no *.md.json changed, and no inline code span was removed.

How it was done: pi (local-openai/gpt-6.1-sol, medium) rewrote 62 chunks, at most 4 lanes and then 2 after your note. I read every chunk's diff myself and repaired each drift by hand. A word-count check of only/itself/alone/never/keywords found no dropped "only", "itself" or "alone". A second pi pass compared old and new text of every requirements, contracts and scenarios chunk; I checked each difference it listed.

Meaning differences found and how they were resolved (full list in the decision log, "Meaning drifts found and repaired"):
- Fronted conditions on guidance requirements, about 15 statements. "When X, the guidance SHALL tell the main agent to do Y" limits the guidance's obligation, not the instruction. I put the condition back inside the instruction, and did the same in scenario steps.
- Clauses that had left the SHALL statement were put back: project-mcp-presentation, workflows, transcript-kept, removed and others.
- Invented or swapped actors were restored. Examples: "the server never hands over a lock" (it is register_wait); facts told to the task session reassigned to the main agent; "start Workflows" instead of "start this level".
- Scenario structure: series became colon steps plus "AND <item>" steps, and "This illustrates" became lists inside scenario sections. Restored as complete steps or inline series. One chunk was discarded and re-run with a corrected prompt.
- Telegraphic statements ("close eligible Issues … without blocking completion", "its process's starting Concorde code") were rewritten as full obligations with lists. "which records who wrote nothing" had been inverted into "This records who wrote nothing" and is restored.
- Lists placed between a colon sentence and its D2 diagram were restored as single introducing sentences.
- Kept after checking, with reasons in the log: the preferred-fix reporting split (matches req.main-session.issues-preferred-fix-reported), "the session has a subagent transcript" (the module says they lie beside the transcript), and "The filesystem records nothing about who wrote a change".

Exceptions kept: no measured one remains. Judged list-rule exceptions are kept inline: series in scenario steps and in "This illustrates" sentences (scenario sections hold no nested list), sentences that introduce a diagram, and short code-span series. In prompts this includes phrases tests assert and one paragraph that the part-guard test needs to name the parts. Tables are unchanged, as the brief lists them as structure.

Decisions taken without the developer (in the log): the chunking and prompt design; 30 asserted strings in tests/concorde/main_session/test_guidance.py now follow the new wording, each still asserting the same rule; guidance requirements keep the condition inside the instruction.

Tests: build --check passes and the affected suites pass (235 passed). Two full pytest runs each had one different load-dependent failure in tests that read none of these files. Both pass alone 3/3 and are recorded as Issues, not fixed here:
- I-7f491393d6e85610886f47c0426cf37f (module.execution, decision-needed, low): the detached-run test checks the progress file too early.
- I-d0e67ee6eaae595f9ee627a0a0b1b1b6 (module.tasks, decision-needed, medium): a task wait may miss a close made 0.3 s after it starts. This may be a real lost wake-up.

Lessons for the other restyle tasks: the fronted-condition pattern on "SHALL tell" statements and the scenario colon-step pattern are what pi did most often here, and the second pi review pass catches the first reliably.

## Closed: merged, 2026-10-04T09:59:07Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit c7f5fb221afc06f054a36c750f5367288f9115cc into main and closed it as merged. Nobody answers a report after that.
