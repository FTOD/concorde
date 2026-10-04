# Decision log: restyle-root

Goal: Rewrite the existing Specs and prompts of its scope to Protocol 16.2's Sentence style, unchanged in meaning, with pi on gpt-6.1-sol: root Module, glossary, E2E and Dogfooding


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

Paths: the root Module's documents `specs/concorde/module.md`, `requirements.md`, `scenarios.md`, `development.md`; every concept definition in `specs/concorde/glossary.json` (this task alone edits the glossary: definitions only, never ids, titles, owners, explanation anchors or relations; a definition stays ONE sentence, of 35 words or fewer, with exactly the same meaning, since every session loads it); `specs/concorde/e2e/**` and `specs/concorde/dogfooding/**` (Markdown only); `prompts/development/` and `prompts/dogfooding/`. Baseline: root module.md 102 warnings, glossary 36 sentence-length and 7 semicolon.

## Task session (2026-10-04)

- Baseline measured with `spec-validation` at d4423f70: 442 `CHK.style.*` warnings in the scope
  (154 semicolon, 288 sentence-length, 0 one-obligation; glossary 7 semicolon and 36
  sentence-length, 38 definitions flagged). `check-style.py prompts/development prompts/dogfooding`:
  49 (24 sentence-length, 25 semicolon).
- Batching: one pi call per Markdown document (pi -p on gpt-6.1-sol, thinking medium), up to 4 in
  parallel, largest documents first, after one trial run on `specs/concorde/e2e/requirements.md`.
  Each call reads `protocol/style.md`, rewrites one file in place and iterates with
  `check-style.py` on that file. Reason: one document per call keeps each diff reviewable and the
  files disjoint.
- Glossary: only the 38 definitions that have a `CHK.style.*` warning are rewritten, in one pi call
  that returns a JSON map, applied by script so that ids, titles, owners, anchors and relations
  stay byte-identical. Definitions without a warning stay as they are. Reason: every session loads
  the glossary, so each changed definition is a meaning risk, and the unflagged ones already meet
  the decidable rules.
- Scenario steps: a GIVEN or THEN step that is too long may be split into the step and following
  `- AND` steps. Reason: it keeps every fact on the same side of the WHEN.
- Non-ok result: the first glossary pi call failed with `gateway_concurrency_limit: Concurrency
  limit exceeded for user, please retry later` (exit 1), since the parallel restyle tasks share the
  model gateway. The pi runner scripts now retry such a refusal after a random 30–90 s backoff, up
  to 30 attempts, and the rewrite runs with 3 lanes instead of 4 to leave the gateway room.
- Glossary: pi's rewrite of the 38 flagged definitions reached 35 words mostly by dropping details
  (decision-point, main-agent, project-mcp-server, standard-worker-sequence) and changed
  task-session's meaning ("delegated each task"). I rewrote the definitions myself from pi's
  attempt, checked each with `style_problems`, then had a second pi call list meaning differences.
  It listed 18. I repaired part, optional-integration, task, task-session, model-map,
  operation-catalog, task-brief and workspace-lock. I accepted as minor: decision-log (no longer
  says "Markdown" or "appended", the `.md` path and "holding" carry it), decision-point ("above the
  task" left implicit in the two named settlers), delivery-commit (no longer names Method and
  Coordination as owners of `delivery` and `task deliver`), run-store (worktree and workflow owners
  of the paths left implicit) and step-agent (no longer says Workflows registers the tool).
- Glossary exceptions, kept with their original text because no single sentence of 35 words keeps
  their meaning: concept.main-agent (49 words), concept.task-record (55), concept.workflow-mode
  (52), concept.workspace-binding (49), concept.trace (43), concept.project-mcp-server (78),
  concept.standard-worker-sequence (82), concept.worker-configuration (90). They are 8
  sentence-length warnings. None has a semicolon. Shortening them needs a decision to drop
  details from the definition, which their explanations (mostly in other Modules) would carry.

### Review of the rewrites (task session, 2026-10-04)

For each document I read pi's diff myself, checked its structure by script (headings, links, inline code, code blocks, tables, requirement keywords, scenario steps), and had a second pi call list the meaning differences between the committed text and the new one. Every difference it rated major was repaired. The minor ones I accepted are listed per document.

- `specs/concorde/e2e/requirements.md`: reviewed by me, faithful, no repair.
- `specs/concorde/e2e/module.md`: struct check clean. I repaired one actor slip ("each run starts its launch" → "The case starts each run"). The pi meaning check listed 2 major items, both repaired: `prepare`, not Workers' check, loads the Operations; Claude Code applies allow rules "only once" the repository is trusted (the "only" had been dropped). It also listed 5 minor items, accepted: inline code spans repeated where a sentence was split (`run_failed`, `no_result`, `live_timeout`, `prepare`, `watch`).
- `specs/concorde/dogfooding/module.md`: I repaired three clumsy passages (guidance usefulness, "either explanation", the boundary-case lead-in). The meaning check listed 2 major items, both repaired: the report "is repaired where it was written" (it had been weakened to "lets ... be repaired"), and the main agent, not the command, picks `--run` or `--error-file`.
- `specs/concorde/requirements.md`: I reverted pi's wording of 7 requirement sentences to their original, which already met the rules: part-installation, worker-models-tracked, worker-models-explicit, spec-first, no-wider-than-type, structured-errors and delivery-separate. Reason: pi had invented actors (Git, Coordination, the installer) or inverted the keyword. halves-apart is now one obligation with a list of actors. absent-part-stated is back to one obligation (pi had added a second SHALL NOT). The either/or paragraph about `uses` is now a two-item list. The meaning check listed 2 major items, both repaired by those changes: part-installation's antecedent, and the resume round's feedback order, now the original list. It also listed 1 minor item, accepted: worker-program is split into two SHALL sentences (main, then fallback), which the brief allows.
- `specs/concorde/module.md`: pi exhausted its 30 gateway retries (non-ok: `exit=1 attempts=30`), but the file was finished with 0 style problems, so I reviewed it as is. Repairs from my own review:
  - pi had swapped "task" for "job" in the Protocol-word definition and three later uses. I restored the original word ("a task is the Protocol's word for one worker's bounded job").
  - Two optional-integration examples had lost "only"; restored.
  - "itself" was lost in the main agent's small change; restored.
  - The merge restriction on a task session was restored: it merges only the primary branch into its task branch, and only when asked.
  - End-to-end testing's "headless or through a driver" now describes its runs, not its agents.
  - The meaning check listed 4 major items, all repaired: "some kinds may be empty, but never all five"; "only when the task type grants it" does the implementation context carry contents; adoption works "only through one explicit route"; and the original reasoning about a worker's answer ("rather than another model's opinion") is back in place of pi's ban on model judgement. It also listed 1 minor item, accepted: `delivery` is named where a split sentence needed its subject.
- Non-ok result: `spec-validation` after the first rewrites failed (`invalid`) with two Protocol errors pi introduced:
  - `CHK.requirement.statement` in 5 root requirements (one-version, worker-program, worker-models-install-independent, error-chain, delivery-commit-by-delivery) and in development.md's docs-refresh-whole. Each statement had become two sentences or held two SHALLs.
  - `CHK.scenario.steps` in 8 development.md scenarios, from nested lists inside steps.
  I repaired them. Each statement is again one sentence with one SHALL: the follow-up sentence moved to the next paragraph, or the statement takes a list. docs-refresh-whole went back to its original. development.md's 14 scenario sections went back to their original text, which had no style warning. The pi prompt for the files still queued now states both rules and warns against dropping "only"-type words.
- `specs/concorde/development.md`: besides the above, I repaired four items: "It keeps these times apart" now names the plugin; totals' statement word order; "a submodule still needs registering while that lock is held"; "a short text that is always in context" (pi had written "always available").
  - The meaning check listed 1 major item, repaired: the initializer stops so that a worktree is never left with some references checked out and others not (pi had written "no worktree has only some").
- `prompts/dogfooding/skill.md`: I repaired one inversion ("the spec part, which always comes with the method part" → "which the method part always comes with"). The meaning check found no difference.
- `specs/concorde/e2e/scenarios.md`: pi's rewrite (made after the prompt update) wrote alternatives as `- AND alternatively, …` steps and faked lists as `- AND it names …` steps, which changes OR into AND. I restored the original text of 7 steps (copied-configuration THEN, both root-inside-checkout steps, two headless steps, both runtime-failures steps) and kept pi's sound splits of compound GIVEN/THEN steps. The 42-word WHEN of owners-run-refused is now a WHEN plus an AND that continues it.
- Decision: I stopped the pi queue after that and fixed the remaining scenario warnings myself, 11 in total: root scenarios.md 5, dogfooding 2, cases 1, sessions 3. Each long step became the step plus `- AND` steps that continue it, and each semicolon became two sentences. Reason: pi changes scenario steps badly, and only these few steps needed changing.
- Decision: documents with no `CHK.style.*` warning and no rewrite yet stay as they are: `prompts/dogfooding/claude-md.md`, `prompts/dogfooding/common/observe-runs.md`, `specs/concorde/e2e/cases/requirements.md`, `specs/concorde/e2e/dogfood/requirements.md`, `specs/concorde/e2e/dogfood/scenarios.md`. Reason: their sentences already meet the decidable rules, and a rewrite of requirement statements and scenario steps risks the structural errors seen above for no measured gain. `observe-runs.md` is also matched word for word by the Dogfooding tests.
- `specs/concorde/e2e/sessions/module.md`: I repaired one actor slip (Claude Code, not the tool, ignores an untrusted project's allow rules). The meaning check listed 2 major items, both repaired: the run "that command was still running" ends `cancelled`, and the test procedure "tells the session to record" each decision with its reason and options (pi had made it a claim about the session). It also listed 2 minor items, accepted: inline code spans named where a split sentence needed its subject.
- `prompts/development/skill.md`: I cleaned up two passages, joining code spans that were split across lines and replacing a convoluted "reasons" list with two sentences.
  - The meaning check listed 1 major item, repaired: "verifies each step" had strengthened "verifies, and commits each verified step". It also listed 2 minor items, intended: the code spans that I joined.
- `specs/concorde/dogfooding/requirements.md`: the meaning check listed 1 major item, repaired: "Its only cause is the failure's own error, if any" (pi's conditional had left causes unrestricted when there is no error).
- `specs/concorde/e2e/sessions/requirements.md`: pi had moved the test procedure's contents (claude-works-tasks) and the `wait_exceeded` record (logs-kept) out of the SHALL statement into descriptive sentences, which narrows what is required. I rewrote both, and wake, so that each statement ends in a colon and its list carries every original part. The reason in claude-works-tasks ("because a task session's report would have no receiver") moved to the explanation paragraph. The meaning check found no difference.
- `specs/concorde/e2e/dogfood/module.md`: I removed one conclusion pi had added ("the evaluation records them elsewhere"). The meaning check listed only minor items, all accepted: inline code spans repeated or named as the actor (`prepare`, `edits`, `detail`) where a split sentence needed a subject.
- Non-ok result: 2 Dogfooding tests failed after the prompt rewrites, because they assert prompt fragments word for word (`test_the_guidance_says_how_to_watch_classify_and_report`, `test_the_repository_instructions_take_reports_and_share_the_observation_rule`). I updated 18 fragments to the new wording of the same instruction, which is pure wording. Targeted suites now pass (289 passed).
- `specs/concorde/e2e/cases/module.md`: its pi run was still being restarted after 19 gateway refusals although the file was finished with 0 problems. I stopped it and reviewed the file. The meaning check listed 2 major items, both repaired: "keeping every promise true to the code" constrains the specify run, not only its intent, and the verdict and error of `repair-specs`' output belong to each step, as `scripts/e2e/cases.py` shows. It also listed 2 minor items, accepted: inline code spans named where a split sentence needed a subject.

## Report 1 to the main agent (concorde-f8), 2026-10-04T08:44:04Z

restyle-root delivered: delivery commit fa96b6a9 on concorde/restyle-root (17 verified commits on top of base d4423f70). No escalations.

Counts:
- `CHK.style.*` warnings in scope (spec-validation): 442 before (154 semicolon, 288 sentence-length) → 8 after (8 sentence-length, all in the glossary).
- Root module.md: 102 → 0.
- Glossary: 36 sentence-length and 7 semicolon → 8 sentence-length.
- `check-style.py prompts/development prompts/dogfooding`: 49 before (24 sentence-length, 25 semicolon) → 0.
- spec-validation 0 errors, build --check clean, full pytest 1253 passed and 5 skipped, task-validation ready.

Exceptions kept: 8 glossary definitions that cannot be one sentence of 35 words without losing meaning. Each keeps its original text, and none has a semicolon:
- concept.main-agent (49 words)
- concept.task-record (55)
- concept.workflow-mode (52)
- concept.workspace-binding (49)
- concept.trace (43)
- concept.project-mcp-server (78)
- concept.standard-worker-sequence (82)
- concept.worker-configuration (90)
Shortening them would mean deciding to drop details from the definition, which their explanations (mostly in other Modules) would then carry. That is open for the developer if they want it.

How the work went:
- pi (gpt-6.1-sol, medium) rewrote one document per call, 3 lanes. The shared gateway refused often (`gateway_concurrency_limit`), so the runners retried with backoff. Two runs finished their file but not their final answer.
- I read every diff myself and checked its structure by script. A second pi call listed meaning differences against the committed text.
- About 40 major differences were found and repaired. The recurring ones were a dropped "only" or "itself", invented actors in requirements ("Git SHALL track", "Coordination SHALL count"), inverted relations ("the spec part always comes with the method part"), and obligations moved out of a SHALL statement into description. Every repair is listed per document in the decision log.
- pi also broke two Protocol rules that spec-validation enforces as errors:
  - A requirement statement must be one sentence with one SHALL. This hit 6 requirements.
  - Scenario steps may not contain nested lists, and pi had also written alternatives as `- AND alternatively` steps.
  I repaired them all. After that I fixed the 11 remaining scenario warnings myself instead of using pi.

Decisions I took:
- Only the 38 flagged glossary definitions were rewritten (30 changed, 8 exceptions). I wrote them myself from pi's attempt, because pi's own version dropped details.
- Five files with no warning stay unchanged: `prompts/dogfooding/claude-md.md`, `prompts/dogfooding/common/observe-runs.md` (matched word for word by tests), `e2e/cases/requirements.md`, `e2e/dogfood/requirements.md` and `e2e/dogfood/scenarios.md`.
- `tests/concorde/dogfooding/test_dogfooding.py`: 18 asserted prompt fragments were updated to the new wording of the same instruction. This is pure wording.
- Minor differences the meaning check listed and I accepted: inline code spans repeated or named as the actor where a split sentence needed a subject. Also decision-log, decision-point, delivery-commit, run-store and step-agent each leave one minor detail implicit in their definition.

Resolves no Issues. Nothing else is open.

## Closed: merged, 2026-10-04T08:44:50Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit fa96b6a9c7eec14697fa4bfbd7477de9d2fa23a4 into main and closed it as merged. Nobody answers a report after that.
