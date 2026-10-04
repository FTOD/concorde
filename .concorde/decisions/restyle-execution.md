# Decision log: restyle-execution

Goal: Rewrite the existing Specs and prompts of its scope to Protocol 16.2's Sentence style, unchanged in meaning, with pi on gpt-6.1-sol: Execution and Worker harness


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

Paths: `specs/concorde/execution/**` and `specs/concorde/worker-harness/**` (Markdown only), `prompts/guidance/execution/`, `prompts/guidance/worker_harness/` and `prompts/workers/common/`. Also fix, from spec-style's report: `prompts/workers/common/spec-format.md` still says the writing guide has "both parts"; it now has four (Required format, Writing guidance, Evaluating a Spec, Sentence style). Record that correction.

## Task session (2026-10-04)

- Baseline, measured with `check-style.py` on the scope's paths (same checks as spec-validation):
  Specs 662 problems (442 sentence-length + 279 semicolon over Specs and prompts together, 0
  one-obligation), prompts 59 (`execution/claude-md.md` 1, `execution/skill.md` 12,
  `worker_harness/claude-md.md` 2, `worker_harness/skill.md` 20, `common/errors.md` 3,
  `common/spec-format.md` 21).
- Decision: one pi call per file (28 files, Specs and prompts), at most 4 in parallel, largest
  first, after a pilot on two files. The pi prompt and runner live in the untracked `.restyle/`
  of the task worktree, removed before delivery. Reason: one document per call keeps each diff
  reviewable and the pi sessions on disjoint files.
- Decision: in scenarios, long steps are split only into further `AND`/`BUT` steps of the same
  kind (the Protocol's scenario format forbids nested lists, every list item being a step). A
  step listing "or" alternatives is not turned into `AND` steps when that would change its meaning.
- Non-ok result: both pilot pi calls (`execution/operations/requirements.md`,
  `worker-harness/harness/pi.md`) exited 1 with `gateway_concurrency_limit: Concurrency limit
  exceeded for user, please retry later` after finishing their edits (both files then had 0 style
  problems). The final reports were lost. Decision: the runner retries a call up to 4 times on a
  gateway error, and runs 3 pi processes in parallel instead of 4, since other rewrite tasks share
  the gateway.
- Decision after reviewing the pilot diffs: the prompt also asks to keep prose wrapped at 100
  columns like the rest of the sources, to introduce every list with a full sentence, and to name
  the actor again instead of an ambiguous "It" after a split. The two pilot files go through the
  refined prompt again with the rest.
- Non-ok results: `workers/scenarios.md`, `execution/runner.md` and `workers/launch.md` each ended
  rc=1 after 4 attempts, every attempt with `gateway_concurrency_limit` (the gateway is shared
  with the other restyle tasks, about 12 pi processes at once). The edits of each attempt persisted:
  runner.md and launch.md reached 0 style problems, workers/scenarios.md 4 (from 19); it gets
  another pass after the batch.
- Meaning differences found in review of launch.md, and how they were resolved: pi had moved
  conditions out of the SHALL sentence into descriptive sentences in 17 requirements
  (validation-after-clean-round, grant-as-data, project-interpreter-first, runtime-paths-exact,
  configured-model, model-map, model-map-whole-operation, placement, deletions-whatever-outcome,
  always-recorded, transcript-kept, cleanup-reported, runtime-removed, trace-failures-reported,
  malformed-grant, read-denials, clean-environment). Resolved by restoring the original normative
  sentence where it already met the style checks, or by a list attached to the SHALL sentence.
  `req.workers.bash-strict-network` had been reversed ("the permission mode denies the request");
  restored to "denied ... the permission mode never approves it". The glossary-audit paragraph had
  turned one `audit_violation` naming every entry into one per entry; restored. Decision: the
  prompt for the files not yet started now forbids moving part of an obligation out of its
  normative sentence and allows a compliant normative sentence to stay unchanged.
- Non-ok: `execution/module.md` rc=1 after 4 gateway-limited attempts, but 0 style problems left.
  Review differences fixed: the `failed` cases of the run result had become "examples"; restored
  as the enumeration they were. The checkout-placement paragraph had lost its "because"; restored.
- `workers/contracts.md` reviewed: no meaning difference, contract fences untouched.
- Non-ok: `checks/service.md` rc=1 after 4 gateway-limited attempts, 1 problem left (a 59-word
  `BUT` step of scenario.checks.checks-files). Fixed by hand: the step's "or" alternatives, each
  refused on its own, became one `BUT` step and two `AND so is ...` steps, which keeps "each of
  these is refused". Review fixes: req.checks.trace-write-reported had split one obligation into
  two descriptive list items; restored as one SHALL sentence with the two places as a list. The
  `CheckError` paragraph had lost its "since"; restored as "because".
- `execution/scenarios.md` reviewed (rc=0, 0 left). Exceptions kept by pi and accepted, each a step
  whose "or" alternatives would become "all of" as `AND` steps (each under 35 words, so no
  warning): scenario.execution.binding-refused GIVEN and its THEN codes,
  scenario.execution.bad-command GIVEN, scenario.execution.run-lock WHEN. One fix: the
  workspace-retired step about removing the lock file while holding the lock was reworded so "it"
  no longer confused the lock with its file.
- Non-ok: `harness/module.md` rc=1 after 4 gateway-limited attempts, 0 problems left. Review
  fixes: (1) pi had reworded the write hook's literal reason quoted in the worked example (the
  string of `src/concorde/worker_harness/write_hook.py`); restored verbatim as an inline code span,
  since its semicolon is the program's text, not prose. Decision: the pi prompt now keeps quoted
  program messages verbatim, as code spans when they break a rule. (2) "Since the brief states the
  grant, a read denial's message is generic" reversed the original causality; restored as "the
  message is generic; the brief therefore states the grant". (3) The malformed-grant conditions
  read "fails these conditions"; made "fails any of these conditions" as the original meant.
- `execution/requirements.md` reviewed (rc=0, 0 left). One fix: req.execution.one-result had mixed
  its scope, its "including when refused, fails or is cancelled" and its four exceptions into one
  list, and the explanation's "both with exit status 1" lost the unrecorded run. Rewritten as one
  SHALL sentence with the exceptions as a list, a second SHALL sentence for the refused, failed or
  cancelled run, and "Both runs end with exit status 1".
- `checks/module.md` reviewed (rc=0, 0 left): no meaning difference; one repeated condition merged.
- `execution/contracts.md` reviewed (rc=0 after 8 attempts, 7 gateway-limited): two prose paragraphs, no meaning difference, fences untouched.
- Non-ok: `worker-harness/module.md` rc=1 after 8 attempts (gateway-limited), 0 problems left.
  Reviewed: no meaning difference. Found a rendering defect pi introduces: nested lists inside list
  items followed, without a blank line, by text of the parent item, which Markdown folds into the
  last nested item. Decision: `.restyle/lazyfix.py` inserts the blank line; it runs on every
  restyled file before commit.
- Non-ok: `checks/timing.md` rc=1 after 8 gateway-limited attempts, 0 left. Reviewed: no meaning difference.
- `workers/pi.md` reviewed (rc=0 after 7 attempts, 0 left). Fix: req.workers.pi-sandbox put the
  tool list after "a strict allowlist:", where it read as the allowlist's content; with it,
  req.workers.pi-file-tools and req.workers.pi-denial-reason went back to their original
  sentences, which already met the checks (one keyword, under 35 words).
- `checks/boundary.md` reviewed (rc=0 after 8 attempts, 0 left): no meaning difference; one list introduction reworded for grammar.
- Non-ok: `harness/claude-code.md` rc=1 after 8 gateway-limited attempts, 0 left. Reviewed: no meaning difference.
- Non-ok: `operations/module.md` rc=1 after 8 gateway-limited attempts, 0 left. Reviewed: no meaning difference; two list introductions and the duplicate-name refusal sentence reworded.
- `harness/pi.md` (pilot file, rewritten again with the refined prompt) reviewed: rc=0 after 6 attempts, 0 left, no meaning difference.
- `prompts/workers/common/spec-format.md`: rc=1 after 8 gateway-limited attempts, 0 left. Reviewed:
  no meaning difference. Correction from spec-style's report done: "Use both parts" now names the
  guidelines' four parts (Required format, Writing guidance, Sentence style, Evaluating a Spec),
  all of which `.concorde/protocol/kinds/module.md` appends to the brief. Decision: the schema and
  D2 keyword lists stay vertical lists (style-compliant) rather than over-long sentences, and
  `SchemaKeywordListTests.listed` in `tests/concorde/spec/test_checks.py` now reads either a
  sentence or the list after its marker; the D2 marker became "D2 keywords are these:". Pure
  format change of the test; it still compares the same keyword sets.
- Non-ok: `commands/module.md` rc=1 after 8 gateway-limited attempts, 0 left. Reviewed: no meaning lost, but three garbled rewrites (duplicate-name refusal, Command table paragraph, provider admission of Method's commands) were rewritten by hand to say exactly what the original said.
- Non-ok: `guidance/worker_harness/skill.md` rc=1 after 8 gateway-limited attempts, 0 left. Review fix: "Workers validate the whole file" (the Module Workers) had become "workers validate"; restored as "Workers validates". Two sentences starting "Pi" reworded to keep pi's lower-case name.
- Non-ok: `guidance/execution/skill.md` rc=1 after 8 gateway-limited attempts, 0 left. Review fix: the instruction "Start each run in background Bash" had become the description "you start each run"; restored as an instruction.
- `common/errors.md` reviewed (rc=0 after 6 attempts, 0 left): no meaning difference.
- `operations/requirements.md` (pilot file, rewritten again with the refined prompt): rc=1 after 8 gateway-limited attempts, 0 left. Reviewed: no meaning difference; req.operations.model-work-only became two SHALL sentences (declare a worker id; launch at least one AI worker), the original's two obligations. One list introduction reworded.
- `operations/scenarios.md` reviewed (rc=0 after 6 attempts): no meaning difference.
- `guidance/execution/claude-md.md` reviewed (rc=0): no meaning difference.
- `guidance/worker_harness/claude-md.md`: pi's rewrite (rc=0) turned the instructions into repeated "You must"; rewritten by hand as imperatives, same content, 0 problems.
- Verification: a script (`.restyle/verbatim.py`) compared every committed file with its base
  d4423f70: all headings, `<a id>` anchors, link targets, code spans, fences and quotations are
  kept verbatim, the one exception being the write hook's reason in `harness/module.md`, kept
  verbatim as a code span on purpose.
- Decision: an independent read-only pi call (gpt-6.1-sol, medium, `-t read`) lists the meaning
  differences between old and new text of the 12 normative documents (requirements, scenarios,
  contracts-bearing mechanics); each difference it lists is decided here.
- Meaning check of `execution/requirements.md`: one difference, req.execution.no-task-knowledge's "so that" clause had left the SHALL sentence; restored inside it, the three kinds of state as its list.
- Meaning check of `workers/launch.md`, six differences and their resolutions:
  (1) req.workers.bash-no-unsandboxed and (2) req.workers.bash-strict-network had their "so that"
  consequence outside the SHALL sentence: both restored to the original sentence (under 35 words).
  (3) req.workers.model-map-whole-operation had lost "for them": restored as "for those workers",
  the refusal's two contents as the list of the SHALL sentence. (4) The glossary-audit trigger read
  "may own": restored as "When a Module outside the grant owns such an entry". (5) req.workers.
  always-recorded now states the runtime-directory removal with its own SHALL: kept, since in the
  original it was a clause of the same SHALL sentence (after a semicolon), so it was already
  normative. (6) "so that `python` is the project's interpreter" had attached to the brief alone:
  restored as "Both make `python` the project's interpreter".
- Meaning check of `execution/runner.md`, three differences, all fixed: the `worker-run` evidence is again the `cancelled` link's; `submodule` evidence names each submodule "so checked out" (the eligibility conditions); the lobby rule keeps its "because whoever retires the workspace holds that lock". `execution/scenarios.md`: none.
- Meaning check of `checks/service.md`: one difference, step 7's "because" had come to explain a differing digest too; restored as the cause of a digest that can no longer be computed. `workers/pi.md`: none.
- Meaning check of `checks/boundary.md`: one difference, the "so" linking the read-only-mount owner rule to its two outcomes was lost; restored.
- Meaning check of `checks/timing.md`: one difference, `returncode` had become exempt from all three count conditions; the original (and `timing.py`, which checks `value >= 0 or key == "returncode"`) exempts it from "nonnegative" alone. Fixed.
- Meaning check of `harness/claude-code.md`: one difference, the denial outside the task worktree had lost its "reached through a final link" condition; restored as "Such a denial". `operations/scenarios.md`: none. `operations/requirements.md`: the check's output was lost to the gateway; reviewed by hand only.
- Correction of the line above: the meaning check of `operations/requirements.md` did arrive
  (attempt 3). Its one finding, that req.operations.model-work-only now says an unreadable worker
  configuration refuses the run before the worker step, is no difference: the original gave that
  very case with "such as" as an example of a run refused before that step. No change.
- Meaning check of `harness/pi.md`: one difference, "wins inside the wider `allowRead`" had moved
  from the `names` paths to the whole `denyRead` list; restored to the `names` entry alone.
- Meaning check of `execution/module.md`, five differences, all fixed: the Spec-reading admission's
  leaving-out and refusing were tied to Method's definitions alone ("They"), now "Such an
  admission"; the Operations child's replacement had lost its `ok` output qualifier; "the runner
  starts" when the holder lets go is "the run starts"; the submodule condition's "its repository"
  lost its referent; the task session's background Bash lost its "because". Meaning check of
  `worker-harness/module.md`: the worker list was introduced as handling gaps only, while the
  original covers a Spec gap or a path outside the grant; now "handle both".
- Meaning check of `harness/module.md`, three findings: "may read the file with no tool" restored as "No tool lets the worker read the file"; the tool replacement no longer names the check as its actor. Not changed: "Checkout does not use Billing" is the original's meaning, since the example's table gives Billing's Spec no access for that reason.
- Meaning check of `guidance/worker_harness/skill.md`: its one finding was my own earlier repair "Workers validates", which picked one reading of the original's ambiguous "Workers validate"; reverted to the original sentence word for word. Meaning checks with no difference: checks/module.md, commands/module.md, operations/module.md, execution/contracts.md, workers/contracts.md, common/errors.md, guidance/execution/skill.md; common/spec-format.md only the intended four-parts correction.

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
- Non-ok result: `spec-validation` reported 3 errors `CHK.requirement.statement` (the first
  paragraph must be one sentence with SHALL exactly once) in req.execution.waiting-progress,
  workspace-wait-continues and checkout-removed, which pi had split into two SHALL sentences and my
  review missed. Five more sections carried a second SHALL in a later paragraph
  (req.execution.one-result, error-detail, req.operations.model-work-only,
  req.workers.deletion-failure, always-recorded), partly from my own earlier repairs. Decision: all
  eight are again one statement sentence with one SHALL, using an obligation, a colon and a list
  where needed. req.execution.waiting-progress keeps its original actor, the run progress file
  (pi had made it the runner). req.workers.deletion-failure and always-recorded are back to their
  original statements (always-recorded's runtime-directory removal is again an explanation, as in
  the original). A scan now finds no requirement section in the scope with more than one keyword or
  a multi-sentence statement.
- `workers/scenarios.md`: two pi passes (rc=1, gateway-limited) left 4 problems (from 19). Review
  fixes: scenario.workers.git-hidden-outside-home's THEN had become "are exactly these paths:"
  followed by AND steps (a colon introducing steps, and "exactly" added); restored as the original
  single step. scenario.workers.session-proxy's "as an enclosing loopback proxy sets them" had
  become a precondition; restored as a comparison. Exceptions kept, each a `CHK.style.sentence-length`
  warning: the GIVEN of scenario.workers.malformed-grant-refused (49 words), the AND step of
  scenario.workers.invalid-result listing invalid results (42), the WHEN of
  scenario.workers.pi-file-tools-denied (86) and the GIVEN of scenario.workers.model-refused (46).
  Reason: each lists "or" alternatives of one step. As `AND` steps they would say all cases hold
  at once, and the scenario format allows no nested list, so no faithful split exists without
  splitting the scenario itself, which would change its identity.
- `workers/module.md`: two pi passes (99 -> 71 -> 0 problems; the second rc=0 after 7 attempts).
  Review fixes: the brief's list of disabled sources read as what the worker is told; the repair
  text's check details were attached to the wrong alternative; "Unless the configuration chooses
  Claude Code for some workers, a Claude Code main agent runs pi workers" changed which workers run
  on pi, now "runs pi workers, except those the configuration puts on Claude Code"; two sentences
  starting "Pi" reworded.
- Non-ok: full pytest failed 1 test, `GuidanceWithoutPartsTests::test_every_section_stands_without_the_parts_it_may_lack`: the restyled list of Method's execution commands in `guidance/execution/skill.md` stood in a paragraph apart from its guard "Where the method part is installed". Fixed by joining the list to its introducing sentence (no blank line, same rendering); the test passes.
- Non-ok: the full pytest run failed 6 tests of `tests/concorde/main_session/test_guidance.py`, all
  asserting phrases of the Execution and Worker harness guidance that the restyle reworded.
  Decision: pure wording, so the assertions now name the restyled phrases of the same meaning
  (`.restyle/phrases.py` listed each missing literal; assertNotIn literals unchanged). The guidance
  tests pass. Also: "When the project has no file, you take these steps" became the instruction
  "take these steps".
- Meaning check of `workers/module.md`: the resume round's purpose ("so that the worker repairs
  it") had become an assertion of success; restored. Its finding on the model-map location is no
  difference (the original also says "by its absolute path, else ..."). Meaning check of
  `workers/scenarios.md`, five differences, all fixed: brief-review-gaps "return `blocked` only
  when it cannot review at all" restored as the brief's instruction; model-map-checked's timing
  and Operation reference restored; interrupted-run's error again names the interruption;
  blocked-not-resumed and pi-invalid-result-retried regain their "therefore".

## Report 1 to the main agent (concorde-f8), 2026-10-04T09:10:51Z

restyle-execution delivered: b8c809c2 (concorde: deliver restyle-execution) on concorde/restyle-execution. task-validation ready; spec-validation 0 errors; build --check clean; full pytest 1253 passed, 5 skipped.

Counts. CHK.style.* in the scope's Specs (specs/concorde/execution/**, specs/concorde/worker-harness/**): 662 before (sentence-length + semicolon, 0 one-obligation), 4 after (all sentence-length). check-style.py on prompts/guidance/execution, prompts/guidance/worker_harness, prompts/workers/common: 59 before (execution/claude-md 1, execution/skill 12, worker_harness/claude-md 2, worker_harness/skill 20, common/errors 3, common/spec-format 21), 0 after.

Exceptions kept (4), all in specs/concorde/worker-harness/workers/scenarios.md: the GIVEN of scenario.workers.malformed-grant-refused (49 words), the AND step listing invalid results in scenario.workers.invalid-result (42), the WHEN of scenario.workers.pi-file-tools-denied (86), the GIVEN of scenario.workers.model-refused (46). Each lists "or" alternatives of one step: as AND steps they would mean all at once, and scenarios allow no nested list.

Brief's correction done: prompts/workers/common/spec-format.md now names the guidelines' four parts (Required format, Writing guidance, Sentence style, Evaluating a Spec) instead of "both parts".

Meaning differences found and resolved (details per file in the decision log). By my diff review: conditions moved out of SHALL sentences in 17 req.workers.* requirements (restored); req.workers.bash-strict-network reversed (restored); a literal write-hook reason reworded in harness/module.md (restored verbatim as a code span); a reversed causality and "fails these conditions" in harness/module.md; req.execution.one-result mixed scope and exceptions; returncode exemption, Workers/workers, imperatives turned into descriptions in guidance; several garbled list introductions. By the independent read-only pi check (24 files): 30 findings, 26 fixed (lost "so that"/"because" links, "may own" for "owns", a lost "for them", the `ok` qualifier, a denyRead precedence widened to the whole list, a lost final-link condition, returncode exempted from all count rules, check details attached to the wrong alternative, which workers run on pi, the resume round's purpose, and similar); 4 judged no difference (model-work-only "such as" example, Checkout not using Billing, model-map location, the brief-directed four-parts correction). spec-validation also caught 3 CHK.requirement.statement errors (two SHALL sentences); all eight requirements with a second SHALL are again one statement with one SHALL.

Decisions taken without the developer: one pi call per file (28 files, then a second pass for two), 3 parallel lanes, later 2 after your note; runner retries on gateway_concurrency_limit; prompt refinements (100-column wrap, requirement fidelity, verbatim program messages, no lazy nested lists); a blank-line fix for nested lists Markdown would fold; test updates of pure wording only: tests/concorde/spec/test_checks.py SchemaKeywordListTests reads a vertical keyword list (D2 marker now "D2 keywords are these:"), and tests/concorde/main_session/test_guidance.py asserts the restyled phrases of the Execution and Worker harness guidance (same meaning). Note for the merge: test_guidance.py is likely touched by restyle-coordination too.

Non-ok results: most pi calls ended rc=1 with gateway_concurrency_limit, edits kept and reviewed; one pytest failure (guidance-parts guard split from its list), fixed. Nothing open, no escalation, no Issue resolved.

## Closed: merged, 2026-10-04T09:40:27Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b8c809c29cb6684697065a6970ae5223baececd0 into main and closed it as merged. Nobody answers a report after that.
