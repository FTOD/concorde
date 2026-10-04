# Decision log: restyle-method

Goal: Rewrite the existing Specs and prompts of its scope to Protocol 16.2's Sentence style, unchanged in meaning, with pi on gpt-6.1-sol: Method


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

Paths: `specs/concorde/method/**` (Markdown only), `prompts/workers/` except `prompts/workers/common/`, and `prompts/guidance/method/`. Also fix, from spec-style's report: the specification and adoption module documents list the writing-guide bundle's contents without Evaluating a Spec and Sentence style; bring those lists up to date (a factual correction, record it).

## Task session (2026-10-04)

### Baseline

- `spec-validation` before: 0 errors; scope `specs/concorde/method/**` has 744 `CHK.style.*`
  warnings (452 `sentence-length`, 292 `semicolon`, 0 `one-obligation`).
- `check-style.py prompts/guidance/method prompts/workers/* (except common)` before: 126 problems
  (50 `sentence-length`, 76 `semicolon`).

### Decisions

- **Bundle contents fix** (factual correction from the brief): `adoption/module.md` and
  `specification/module.md` now list the writing-guide bundle as "the overview, Required format,
  Writing guidance, Sentence style, Evaluating a Spec and templates", matching the chapters of the
  rendered `kinds/module.md`. In `specification/module.md`, "The two parts cover" became "Together
  they cover", since the list now has more than two parts. Committed on its own before the restyle.
- **Batching**: one pi call per file (each edits the file in place with its tools, and checks
  itself with `check-style.py <file>`, which measures any Markdown file). A shared prompt names
  the structural elements that must stay byte for byte. A local script then compares headings,
  fences, tables, front matter, includes, HTML anchors, inline code spans, link texts and targets
  and placeholders against HEAD, and counts requirement keywords.
- **Verification**: a second pi call per file (read-only tools) lists meaning differences between
  old and new text; I read every diff myself and decide each difference.
- **Gateway refusals**: the first pilot call failed with `gateway_concurrency_limit: Concurrency
  limit exceeded for user` because the parallel restyle tasks share the same gateway. The runner
  retries such refusals with a growing pause; I run at most 2-3 pi processes at a time.

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

## Task session (2026-10-04, continued)

- Read the main agent's lessons from restyle-root. The pi prompt now states
  `CHK.requirement.statement` (one sentence, one SHALL, whole obligation in the statement, colon
  and list when long), the scenario rule (every list item is a step, no nested list), the drift
  patterns (dropped only/itself/alone, invented actor, inverted relation, obligation moved out of
  the statement, telegraphic compression) and a per-file spec-validation self-check. The meaning
  review prompt checks the same patterns. Reduced to 2 pi lanes: the prompt lane was stopped
  mid-file (`survey.md` partly edited, `test.md` and `understand.md` not started) and goes into a
  later pass.
- Several pi calls exhausted 12 retries on `gateway_concurrency_limit` after partly editing their
  file (`adoption/module.md`, `spec-review/module.md`, `delivery/module.md`,
  `prompts/workers/spec-review/checklist.md`). A later pass completes them with the current prompt.
- `delivery/requirements.md` was rewritten before the lessons and has 5 `CHK.requirement.statement`
  errors. It is reverted to its original and rewritten again with the current prompt.
- My review of pi's prompt rewrites found no meaning change. It found style defects that I repaired
  by hand: inverted sentences ("Only when ..., return `blocked`"), one-word items made into lists,
  needless repetition of a subject or condition, a misplaced "such as" example in
  `guidance/method/task-session.md`, and lines after a nested list that Markdown would render
  inside the last list item ("lazy continuation") in `plan-review.md`. A local detector now finds
  the last kind in every changed file.
- Interpretation of `style.md` "Lists for three or more": a series of single words or short noun
  phrases inside one fact ("record, close or reopen an Issue", "naming, wording or style") stays
  inline. A list is used for three or more conditions, cases, steps, clauses or long items.
- Meaning drifts found in my review and repaired: `adoption/contracts.md` "names none when an
  answer settles the decision" (no choice) had become "names no options"; `method/module.md`
  "a Spec that cannot be loaded is refused" had gained the invented actors "Spec core refuses" and
  "Method translates" (restored to the passive), and the Brownfield procedure realization had
  become the actor that registers the workflow instead of holding the module that does.
- `workers.md`: repaired "the worker's own options, when it gave any" (had become a condition that
  left the no-options case open), "which reads the round's worker result" (had been widened from a
  review's citation check to every step validation) and "it computes" (actor made explicit: the
  step).
- `code-review/module.md`: "listed under `rejected` with the reason, as host evidence names each failed check" (an analogy) had become "for that finding, host evidence names each failed check"; restored.
- `validation/module.md`: "a timeout's exit code becomes null and the log digest is dropped" had become a timeout-only drop of the log digest (the readiness contract keeps no log digest for any check); restored as a general drop. A lost "since" (why `binding_required`) restored.
- **Scenario documents are not given to pi.** Pi's rewrite of `adoption/scenarios.md` (which had
  no style warning) moved THEN/AND content, such as "naming each Module ..." and "which `linked_tests`
  lists", out of the steps into prose after them, and put two sentences into one step. A step is a
  verifiable promise, so that moves meaning out of the scenario: reverted. Decision: in
  `*scenarios.md` I fixed by hand only the 13 steps and intro sentences over 35 words, splitting a
  step only into consecutive `AND`/`BUT` steps of the same kind that keep every condition; all other
  steps stay as written. The pi prompt now forbids any change inside a scenario section, and the
  remaining queues hold no scenario document.
- `code-review/requirements.md`: `no-closing` had absorbed its descriptive half ("it lists the earlier Issues ... resolved") into the SHALL statement as "while listing"; restored as an explanation paragraph. `earlier-issues` listed the Issue's content as a condition; restructured. `diff-within-grant` was already compliant (30 words) and was restored unchanged.
- `adoption/requirements.md`: "the worker left unchanged or had deleted" (causative: deleted through its proposal) had become "or deleted"; restored. `relative-paths` restructured (pi's version mixed the condition into the list of claims).
- `brownfield.md`: "decides from a step's status, its mode" (the workflow's mode) had become "the mode of that step" (steps have no mode); restored as "the workflow's mode".

## Main agent note (2026-10-04): lessons from restyle-coordination

pi made two kinds of drift most often there:

- **A condition moved to the front of a guidance requirement.** "When X, the guidance SHALL tell
  the main agent to do Y" limits the guidance's own obligation, not the instruction it gives. Keep
  the condition inside the instruction: "The guidance SHALL tell the main agent to do Y when X."
- **A series turned into scenario steps.** pi wrote a colon step followed by "AND <item>" steps, or
  lists inside scenario sections. Write the series as complete steps or keep it inline.

A second pi pass that compares the old and the new text catches the first pass's drift reliably.
- `scaffold/requirements.md`: `vendored-external` had turned its purpose ("so that no worker describes or reviews it") into a third obligation; restored as an explanation. `no-overwrite` had fronted its "since" reason onto both refusals; it explains only why an existing folder holding no file is refused, restored there. `step-output` list made parallel.
- `adoption/module.md`: "a name defined there more than once" pointed at "inside a function" after the split; made explicit ("in those places"). "validates after each round and resumes the worker with the errors" had become "validates with the errors"; restored.
- `spec-review/module.md` (partly rewritten by the first prompt): "a worker ends `blocked` only when
  it cannot review at all" had been inverted into "when a worker ends `blocked`, it cannot review
  at all"; "after its second attempt the Module is `incomplete`" had lost its condition (the
  report still loses a finding); a new numbered list 1–8 claimed the step table's numbers, which
  belong to the diagram; "reported again only when it changed" was garbled. All restored.
- `delivery/module.md` (partly rewritten by the first prompt): two dropped "only" restored ("is
  reported only once its workspace is ready again", "reports the head as delivered only when");
  "Git restores" was an invented actor (Delivery restores, with Git's commands); "These failures
  include" made a complete list open; "A delivery is recorded once, in the commit that makes it" had
  been garbled. All restored.
- `prompts/workers/survey.md` (partly rewritten by the first prompt, then completed): the sub-items of `decisions` and `open_questions` had lost their indentation, which broke the bullet list apart; a code span ran across a line at the wrong indentation; "give a path to two children only when" and "return `blocked` only when" had been inverted. Repaired by hand.
- Meaning review (pi, old vs new) of `guidance/method/skill.md` and `task-session.md`: three sentences split off from a conditional sentence had left the condition ("where the coordination part is installed", "without that part", "otherwise") behind. Accepted; the condition is carried over ("In that case, ...", ", where you read them").
- Meaning review of `panel-spec.md`: accepted DIFF 2 (`earlier` belongs in the changed finding). Rejected DIFF 1: the original's colon listed the reasons that define "does not hold", and "for any of these reasons" keeps that same closed set.
- Meaning review of `adoption/module.md`: accepted all three (escalation settles decisions *and*
  open questions; each item is its own decision point; the decorators-only rule and its
  "otherwise" apply only to a file that already binds `verifies`). Fixed.
- Meaning review of `adoption/requirements.md`: 15 DIFFs. Rejected 12 (1-4, 6-10, 12, 14, 15): they
  flag the "obligation, colon, list" form as moving conditions out of the statement, but that form
  is the one `style.md` prescribes and the main agent's lessons ask for, and the list completes the
  one-sentence statement. Accepted 3: DIFF 5 (`modules-by-host`: "which only `scaffold` does, from
  an admitted survey" back in the statement, with "be able to"), DIFF 11 (a decision point of kind
  `decision` keeps its decision's identity, without implying every decision has one), DIFF 13 (the
  fronted "its Concorde installation" was ambiguous).
- Meaning review of `code-review/module.md`: accepted all three ("reported again only when it changed" is necessary, not sufficient; `--base` is required for an unbound *change* review, not every unbound run; the refusal condition covers both "keeps no `earlier`" and "is carried"). Fixed.
- Meaning review of `code-review/requirements.md` (14 DIFFs, from before the review prompt knew
  the colon-list form): rejected 8 colon-list DIFFs (1, 3, 5, 6, 9, 10, 12, 13). Accepted 6: the
  reviewer runs *under* the grant (2); "its" made the reviewer's (4); "rather than as a defect" is a
  reporting rule, not a claim (7); "after the resume round" limits only the rejected findings, not
  "still report every other finding" (8); `no-closing` keeps "it lists the resolved earlier Issues"
  in its statement, after a colon (11, which reverses my own earlier choice); "with those citations
  to correct" restored (14).
- Meaning review of `delivery/module.md`: accepted all five (the blocked case is "a head whose
  workspace is not ready", not the unverified head; "one at a time"; "binds a new file only once it
  has created it" is a precondition, not an obligation; the intent-to-add entries are those of
  `git ls-files`' paths the tree lacks; the Kernel gives a lock as well as conventions, and
  Coordination recognizes Delivery's commits). Fixed.
- Meaning review of `implementation/module.md`: accepted all five (the three-round fallback only
  without `--rounds`; "edits stay uncommitted" under the same "returned a result" condition; the
  home-directory exclusion limits the symbolic-link rule; "after a clean audit" kept to performing
  deletions, "It refuses the rest" left as open as the original; Workers, not the run record, is
  the last defence). Fixed.
- Meaning review of `implementation/requirements.md` (an entry is named *by* the check's identity;
  "the resume round is given only when", necessary not sufficient) and `method/module.md` (the
  step's own validation "if it has one" covers both branches; the admission helper's realization
  item rejoined; the survey/scaffold/code-to-spec roles stated independently of "usually";
  Distribution loads the modules *before* it routes): all accepted and fixed.
- Meaning review of `method/requirements.md` (the described-after claim kept under the no-cycle condition; "its worker" made "the worker describing it") and `scaffold/module.md` ("kept only if", necessary not sufficient): accepted and fixed.
- Meaning review of `scaffold/requirements.md`: accepted DIFF 2 (naming "the existing file or the folder" kept in the statement, as the original's choice), DIFF 3 (`parent-narrowed` back to its state form, "every file ... SHALL be bound by", with no invented actor), DIFF 4 ("each with the `uses`" kept per Module, 35 words). Rejected DIFF 1: "so that no worker describes it" is the purpose of `vendored-external`, not an obligation, and returning it to the statement would exceed 35 words; it stays as the explanation paragraph.
- Meaning review of `spec-review/module.md`: accepted DIFF 1 (the Operation also appends the Writing guidance and Sentence style) and DIFF 3 (the error link is the worker's or audit's). Rejected DIFF 2: the original already made the grant the reader ("a grant ..., which reads every Module's Specs").
- Meaning review of `spec-review/operation.md`: accepted both (the report's provenance; the earlier Issue the unreported finding named). Fixed.
- Meaning review of `spec-review/requirements.md`: accepted both ("Spec review's" Issue reports; "that Operation's payload contract"). Fixed.
- Meaning review of `specification/module.md`: accepted all four (a file is never declared before
  it exists, correcting my own "ahead of that run"; the clean-round condition covers the resume
  too; the worker's own link ends the chain whenever the worker cannot make the change; "an owned
  document is deleted only by proposing it" restored). Fixed.
- Meaning review of `understanding/module.md`: accepted DIFF 2 (`status` named as the subject).
  Rejected DIFF 1: the assessment contract has one `sufficient` for the whole assessment, so
  keeping sufficiency out of "for each bound Module" is right.
- Meaning review of `validation/contracts.md` (escaping rules kept to the double-quoted record) and `understanding/requirements.md` (the Operation runs no configured check, rather than the reviewer "has" none): accepted and fixed.
- Meaning review of `validation/module.md`: accepted DIFF 1 (`task-validation` is the execution command, not the Module). Rejected DIFF 2 ("which ... names `system_error`" attaches to the operating-system error in the original) and DIFF 3 (my deliberate earlier correction: the readiness contract keeps no log digest for any check result).
- Meaning review of `workers.md`: accepted all five (the configuration "is read", no invented reader; "at once" covers the whole check; the prohibitions are Workers', not the whole worker harness's; the step's request conditions running the checks too; "the record's" remediation and causes). Fixed. All 45 rewritten files have now had the old-vs-new meaning review.
- The full test suite failed 8 assertions of `tests/concorde/main_session/test_guidance.py` on
  phrases of the Method guidance. Decision: where the original phrase fits the style, the guidance
  uses it again ("instead: one reviewer per named Module ...", "for a whole-Module check after a
  large change, on code written before its Specs ...", "in a workspace bound to that Module",
  "open a task bound to it and have its task session ...", "so escalate it rather than change the
  promise", "create it yourself", the label "**Have your plan reviewed when it deserves it.**").
  Where the asserted phrase itself breaks the style (a semicolon, a colon run of clauses), I updated
  the test literal to the new wording of the same instruction, and added two assertions for the
  disagreement steps the old literal covered. The test file is the main-session Module's, outside
  this task's Modules: a pure wording update, flagged for the merge in case another restyle task
  touches the same file. Full suite after: 1253 passed, 5 skipped.

## Report 1 to the main agent (concorde-f8), 2026-10-04T10:56:53Z

restyle-method delivered: 188eb1e1 (concorde: deliver restyle-method) on concorde/restyle-method. task-validation ready, full pytest 1253 passed / 5 skipped, build --check clean, spec-validation 0 errors.

COUNTS
- CHK.style.* in specs/concorde/method/**: before 744 (452 sentence-length, 292 semicolon), after 0.
- check-style.py on prompts/guidance/method + prompts/workers (without common/): before 126 (50 sentence-length, 76 semicolon), after 0.
- Exceptions kept: none.

WHAT CHANGED
- 41 Spec documents and 13 prompt files rewritten by pi (gpt-6.1-sol, medium), each diff read by me, then a second pi pass (old vs new, read-only) listed meaning differences on all 45 pi-rewritten files.
- Scenario documents: not given to pi (it moved THEN/AND content out of steps into prose). I split by hand only the 13 steps/intro sentences over 35 words into AND/BUT steps keeping every condition; adoption/specification/understanding/validation scenarios unchanged (no warnings).
- Factual correction from spec-style: adoption/module.md and specification/module.md now list the writing-guide bundle as overview, Required format, Writing guidance, Sentence style, Evaluating a Spec and templates.
- prompts/guidance/method/claude-md.md unchanged (27 words, no problem).

MEANING DIFFERENCES FOUND AND RESOLVED (details per file in the decision log)
- My own review: ~20 drifts repaired, e.g. dropped "only" (delivery/module x2), inverted "blocked only when" (spec-review/module), invented actors ("Spec core refuses", "Git restores", "the reader"), a purpose turned into an obligation (scaffold vendored-external), "had deleted" weakened, "names none" read as "names no options" (adoption/contracts), log-digest drop scoped to timeouts (validation/module), garbled list structure in prompts/workers/survey.md.
- pi meaning review: about 50 further findings accepted and fixed, almost all one pattern: a split sentence left a condition, quantifier or referent behind ("In that case" carried over, "only when" kept necessary not sufficient, "its" made explicit). Rejected with reasons: the reviewer's flags of the prescribed "obligation, colon, list" form (12 in adoption/requirements, 8 in code-review/requirements), and 6 others where the original said the same or the change was a checked correction (logged one by one).

DECISIONS TAKEN WITHOUT THE DEVELOPER (all in the log)
- Batching/parallelism: one pi call per file, then max 2 lanes after your note; retries with backoff on gateway_concurrency_limit; several partial edits were completed or reverted and rerun.
- "Lists for three or more": short series of one or two words inside one fact stay inline.
- Scenario documents restyled by hand only where a check fires.

NEEDS YOUR ATTENTION AT MERGE
- tests/concorde/main_session/test_guidance.py (main-session Module, outside this task's Modules) changed: 8 asserted phrases of the Method guidance. Where the old phrase fits the style, the guidance uses it again; where the phrase itself breaks the style (semicolon, colon run) the literal now carries the new wording of the same instruction, plus 2 added assertions. Pure wording; may conflict with restyle-coordination if it touches the same file.

No Issues resolved or opened by this task. Nothing open.

## Closed: merged, 2026-10-04T10:57:14Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 188eb1e1437fa55e862ea97a45d4a0231636c832 into main and closed it as merged. Nobody answers a report after that.
