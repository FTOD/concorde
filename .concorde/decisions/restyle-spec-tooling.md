# Decision log: restyle-spec-tooling

Goal: Rewrite the existing Specs and prompts of its scope to Protocol 16.2's Sentence style, unchanged in meaning, with pi on gpt-6.1-sol: Spec tooling and the Protocol


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

Paths: `specs/concorde/spec-tooling/**` (Markdown only), the Protocol sources `protocol/` (all documents including templates, not `manifest.json` by hand), `prompts/guidance/spec/` and `prompts/protocol/`. The Protocol text changes in wording only: run `python3 scripts/concorde.py protocol-manifest --write --bind-project` after it and decide the Protocol version (a patch release such as 16.2.1 fits a wording-only change; record it). Baseline: protocol/ 58 sentence-length, 159 semicolon, 9 one-obligation (check-style.py protocol).

## Task session (2026-10-04)

- Baselines measured on d4423f70: `spec-validation` in `specs/concorde/spec-tooling/**`: 337 `CHK.style.*`
  warnings (180 semicolon, 157 sentence-length, 0 one-obligation), 0 errors project-wide.
  `check-style.py protocol prompts/guidance/spec prompts/protocol`: 235 (65 sentence-length,
  161 semicolon, 9 one-obligation); `protocol/` alone 226, `prompts/guidance/spec` 9.
- Decision: one file per pi call, at most 4 in parallel, biggest files first, after a pilot on
  `spec-mcp/module.md`. pi is told to change only sentences that break a rule, to leave headings,
  anchors, links, code, fences, tables and scenario step kinds untouched, and to self-check with
  `check-style.py`. `protocol/model.yaml` is a schema, not prose: left out.
- Pilot 1 on `spec-mcp/module.md` ended non-`ok`: pi exited 1 with `gateway_concurrency_limit:
  Concurrency limit exceeded for user` (7 other pi processes of parallel tasks share the gateway).
  Its partial rewrite was mechanical (one-word list items, filler such as "Under that condition,",
  statements turned into questions), so it was reverted. Decision: the runner retries with
  backoff, and the prompt asks for fluent text.
- Decision (interpretation of "Lists for three or more"): a short enumeration of names, such as
  error codes or tool names, may stay inline in a sentence of 25 words or fewer, as
  `protocol/style.md` itself does with the requirement keywords. Three or more conditions, cases,
  steps or facts go in a vertical list.

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

## Task session, batch 1 results and batch 2 (2026-10-04)

- Batch 1 (3 lanes, 13:58 to 16:45) ended non-`ok` for several files: the gateway answered most
  attempts with `gateway_concurrency_limit`. `spec/contracts.md` needed all 30 attempts and
  `spec/module.md` exhausted 30 attempts without a clean exit (its partial rewrite is kept and
  finished in batch 2). I stopped the batch after the main agent's lessons arrived.
- Batch 1 broke validator rules: 288 `CHK.scenario.steps` errors (nested lists in scenario steps
  of `spec/scenarios.md` and `views/scenarios.md`) and 4 `CHK.requirement.statement` errors
  (`spec/requirements.md` 3, `spec/errors.md` 1). Decision: both scenario files were reverted and
  are rewritten again under the new prompt. The requirement errors are repaired in review.
- Decision: the pi prompt now carries the validator's statement and scenario-step rules, the main
  agent's drift patterns and the ban on telegraphic text. pi checks a Spec file with a helper that
  filters `spec-validation` to it. Batch 2 runs on 2 lanes.
- Kept from batch 1 for my own review and an independent pi meaning check: `protocol/`
  boundaries, evaluation, format, migration, module, `spec/contracts.md`, `spec/requirements.md`,
  `views/pipeline.md`.
- Mistake, repaired: a stray `cp` overwrote this worktree's `.git` pointer file. I restored it to
  `gitdir: /home/zhenyu/concorde/.git/worktrees/restyle-spec-tooling` and checked `git status`.
- Batch 1's rewrites were too mechanical: one-word lists ("Validation SHALL do the following:
  - Continue."), actors the original does not name ("Validation SHALL NOT represent a validation
  result"), and a second SHALL split out of a statement (`req.spec.context-own-declarations`).
  My attempt to revert them with `git checkout` was denied by the session's permission
  classifier, so I did not discard them. Decision: batch 3 runs pi on all 33 files
  (2 lanes, scenario files last). Where a batch-1 rewrite exists, pi compares it with the original
  sentence by sentence, keeps right sentences and rewrites faulty ones from the original. The
  prompt now also forbids those three patterns by example.

## Main agent note (2026-10-04): lessons from restyle-coordination

pi made two kinds of drift most often there:

- **A condition moved to the front of a guidance requirement.** "When X, the guidance SHALL tell
  the main agent to do Y" limits the guidance's own obligation, not the instruction it gives. Keep
  the condition inside the instruction: "The guidance SHALL tell the main agent to do Y when X."
- **A series turned into scenario steps.** pi wrote a colon step followed by "AND <item>" steps, or
  lists inside scenario sections. Write the series as complete steps or keep it inline.

A second pi pass that compares the old and the new text catches the first pass's drift reliably.

## Task session (2026-10-04, later)

- Applied the restyle-coordination lessons to the pi rewrite prompt (embedded-action conditions,
  no colon step with "AND <item>" steps) and to the meaning-check prompt, from the files batch 3
  starts after this point. Files batch 3 started earlier get the same checks in the meaning-check
  pass.
- Batch 3 ended `ok` for all 33 files at 18:12. Result: 0 errors. 7 `CHK.style.sentence-length`
  warnings remain in scope; `check-style.py` on protocol and prompts reports 0.
- Decision, kept exceptions (7): these GIVEN steps each list alternative fault cases joined by
  "or". Splitting them into AND steps would turn the alternatives into a conjunction, and scenario
  sections allow no nested list. So each stays one step:
  `spec/scenarios.md` steps of `scenario.spec.term-links` (38 words), the glossary-faults scenario
  (45), the relation-faults scenario (47), the invalid-diagram scenario (47) and the
  refused-proposal scenario (38). `views/scenarios.md` lines 24 (57) and 34 (55).
  Exact identities of those exceptions (this corrects the names above):
  `scenario.spec.term-link-invalid`, `scenario.spec.glossary-invalid`,
  `scenario.spec.meaning-relations`, `scenario.spec.validate-architecture-mismatch`,
  `scenario.spec.reject-invalid-proposal`, `scenario.views.load-registry-refused`,
  `scenario.views.reject-reading-collection`.

## Task session: meaning review and fixes (2026-10-04)

- pi meaning check, pass 1, on all 33 changed files (base d4423f70): 9 files had no difference,
  24 had about 80 listed items. I decided each one. I fixed every real drift by restoring the
  original wording or the original attachment of a condition, and I rejected pure pedantry. Fixed:
  - Conditions detached from their scope: `protocol/evaluation.md` (entry-point condition of the
    illustration), `protocol/views.md` ("typically" inside and outside diagrams),
    `protocol/principles.md` (checked/illustrative diagrams written in reading),
    `views/pipeline.md` (shape/edge classes only for a checked block, the fragment rule only for
    glossary links), `spec/contracts.md` (TypeScript-only declaration syntax, `python` absent
    only when propose names none), `spec/module.md` (the never-read-implementation qualifier),
    `views/scenarios.md` (owner-or-below rule only for contained Modules' groups).
  - Actors the original did not name: `protocol/evaluation.md` (term usage),
    `protocol/boundaries.md` (entries added/changed/removed), `spec-tooling/module.md` ("Views
    leaves the previous site"), `spec/module.md` (declarations "parsed, never run").
  - Obligations moved out of their statement or weakened: `protocol/boundaries.md` (honest unknown
    and open question tied back to the MUST NOT with "Instead"), `protocol/principles.md` (evidence
    relation MUST be declared by the executing artifact), `spec/requirements.md`
    (`req.spec.link-fragments`-style "every link" restored, the `covered-by` exception scoped to
    verification declarations again), `views/requirements.md` (nesting "only where" restored),
    `spec-mcp/requirements.md` (tool error statement restored), `spec/contracts.md` (grant
    failure, "must have loaded").
  - Wrong scope or relation: `protocol/relations.md` (a concept's explanation document is the
    selected one, not "the defining one"), `protocol/model.md` (contract boundary list, read side),
    `prompts/guidance/spec/task-session.md` ("use … in Specs, code…" had become "defined in"),
    `spec-tooling/module.md` (double negation "does none of the following: never …"),
    `spec/scenarios.md` (the error names the three new locations), `views/contracts.md`
    (template digest line order, every template file in the set).
  - A literal value: `views/pipeline.md` had changed the illustrative label the publisher emits.
    It is now the exact string of `docsite/plugins/scoped-content/render.ts` in inline code,
    semicolon included, since a semicolon in inline code is no prose.
  - "include" made several closed enumerations open: `spec-tooling/module.md` Part entries,
    `spec/module.md` install contribution, `spec-mcp/module.md` example entries. Restored as closed.
- Also from my own reading, restored over-split text: a 25-item list of JSON Schema keywords
  (`protocol/format.md`), nested single-character lists in `safe_path`, one-word action lists
  ("SHALL NOT perform any of these actions: Create the file"), and two multi-sentence or
  example-only scenario steps in `spec/scenarios.md`.
- Rejected as no meaning change: `templates/module.md` (glossary entry vs glossary names the
  owner), `spec-mcp/module.md` "The server resolves it" (the server is the only resolver in that
  text), `spec/module.md` "take files over from the root Module".
- Decision: Protocol version 16.2.1, a patch release for a wording-only change. Set by hand in
  `protocol/manifest.json` `version` and `PROTOCOL_VERSION` in `src/concorde/spec/repository_base.py`,
  as 16.2 did. `protocol/README.md` and a short `migration.md` section name it. Then `build` and
  `protocol-manifest --write --bind-project` (both `success`).
- Second pi meaning-check pass started on the normative documents (requirements, contracts,
  scenarios, errors, and Protocol format, boundaries and checks).
- Full pytest (non-`ok`): 1 failed, 1252 passed, 5 skipped. The failure was
  `tests/concorde/main_session/test_guidance.py::test_a_spec_tooling_error_is_translated_before_it_is_escalated`.
  It asserts phrases shared by the skill and the task-session guidance about translating a Spec
  tooling error, and pi had worded `prompts/guidance/spec/skill.md` and `task-session.md`
  differently. Decision: both prompts use the same wording again (the skill's field list form).
  The test's phrases are updated for wording only and still assert every element: the six record
  fields, "no link", `invalid_error`, the `component` link with `level` and `actor`, `causes` and
  `--error-file`. That test file belongs to the Main session Module's tests. It is a wording-only
  update the brief allows. Rerun: 38 passed.
- Second pi meaning-check pass on 12 normative documents: 6 clean. Fixed the rest:
  - "Only when …, X SHALL …" fronting had turned necessary conditions into triggers. In
    `req.spec.protocol-binding`, `req.spec.init-explicit-envelope`, the keep-only-if-valid
    requirement and `req.spec.grant-installed-read-only` the condition again limits the action
    ("SHALL admit a project only when all these conditions hold:"). A search of every changed file
    found the same comma-fronted form in `protocol/module.md` (sequence diagram) and
    `views/contracts.md` (deploy workflow, `start` exit), now fixed too. The inverted form
    "Only when A is B" keeps its meaning and stays.
  - Also fixed: `protocol/boundaries.md` ("some changes are valid only if…", the review-architecture
    apposition), `spec/contracts.md` (`shared_files` finds entries, not files),
    `spec/requirements.md` (installation exceptions qualify the files again, "running the test
    sources"), `views/contracts.md` ("replace, delete or reach outside the files listed above").
  - Rejected: `spec-mcp/requirements.md` (an inline list became a vertical list, same meaning);
    `spec/requirements.md` file transaction ("part-way" qualifies all three interruptions, as in the
    original); `spec/scenarios.md` "such as" became concrete violations. That scenario's THEN steps
    already report "the broken link", so the named violations were concrete in the original.
  (The keep-only-if-valid requirement above is `req.spec.init-validated`.)

## Report 1 to the main agent (concorde-f8), 2026-10-04T10:53:43Z

restyle-spec-tooling delivered: a0efb85a on concorde/restyle-spec-tooling (commits 2102a571, 179b304a, 1499eb85). task-validation ready, delivery ok.

Counts. spec-validation in specs/concorde/spec-tooling/**: 337 CHK.style warnings (180 semicolon, 157 sentence-length) -> 7 (sentence-length only), 0 errors project-wide. check-style.py on protocol/ + prompts/guidance/spec + prompts/protocol: 235 (65 length, 161 semicolon, 9 one-obligation) -> 0.

Kept exceptions (7): GIVEN steps that list alternative faults joined by "or". AND steps would turn them into a conjunction, and scenario sections allow no nested list: scenario.spec.term-link-invalid (38 words), .glossary-invalid (45), .meaning-relations (47), .validate-architecture-mismatch (47), .reject-invalid-proposal (38), scenario.views.load-registry-refused (57), scenario.views.reject-reading-collection (55).

Protocol 16.2.1 (my decision): a wording-only patch. Bumped protocol/manifest.json version and PROTOCOL_VERSION in src/concorde/spec/repository_base.py, as 16.2 did. README and migration.md name it. Then protocol-manifest --write --bind-project. Every other task branch will need the new binding/Protocol copy from main after this merge.

Meaning review. pi rewrote all 33 files (2 lanes, 3 batches: batch 1 was too mechanical and broke CHK.scenario.steps and CHK.requirement.statement, so it was redone in repair mode under your restyle-root/-coordination lessons). An independent pi meaning check ran on all 33 files, a second pass on the 12 normative ones, and I read the diffs. About 95 listed items: I fixed every real drift and rejected about 8 as pedantic. Main classes fixed: conditions detached from their scope or fronted onto SHALL ("Only when X, the loader SHALL admit" -> "SHALL admit only when", 6 places plus 2 found by search), actors the original did not name (5), obligations moved out of their statement (5), "include" opening closed enumerations (3), wrong relations or scope (task-session "use in Specs, code…" had become "defined in"; relies_on concept document; double negation; shared_files entries), and one literal: the illustrative-diagram label the publisher emits, now quoted exactly from render.ts in inline code. Over-split text (a 25-item keyword list, nested one-character lists, one-word action lists) was restored. Full list in the decision log.

Outside the scope paths: tests/concorde/main_session/test_guidance.py (Main session tests) quoted the old wording of the Spec tooling error paragraph. I updated it for wording only; it still asserts every element. The two prompts now share one wording again. Also src/concorde/spec/repository_base.py for the version.

Non-ok results, all logged: gateway_concurrency_limit on many pi attempts (retried); my git checkout to revert batch 1 was denied by the permission classifier (repaired in place instead); a stray cp overwrote the worktree's .git pointer (restored at once, verified). Full pytest: 1253 passed, 5 skipped. build --check clean.

Open: nothing to decide. No Issues resolved or opened.

## Closed: merged, 2026-10-04T10:54:05Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit a0efb85af6e31153338016afd93f8ed516f35c4c into main and closed it as merged. Nobody answers a report after that.
