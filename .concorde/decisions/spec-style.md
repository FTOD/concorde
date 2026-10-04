# Decision log: spec-style

Goal: Add Spec writing style rules inspired by ASD-STE100 to the Spec Protocol for every Concorde project, a warning-level structural check for them, a readability dimension for Spec review, and the same style as Concorde's own extra requirement on prompts/


## Task brief (main agent, 2026-10-04)

### Developer's decisions this task carries out

The developer wants Spec English normalized after the style of ASD-STE100 (Simplified Technical
English), adopting its structural rules only, not the whole standard. On 2026-10-04 the developer
decided:

1. **The style rules go into the Spec Protocol** and apply to every Concorde project, not only to
   Concorde's own Specs. They join the Protocol's writing guidance (`protocol/writing.md` and the
   documents it links, owned by `module.spec`).
2. **A structural check reports them at strictness `warning`**, never `error`, as a rule identity of
   `concorde spec-validation`, so existing text does not fail validation.
3. **Spec review gains a readability dimension** in `protocol/evaluation.md` and in the reviewer
   instructions of `module.spec-review` for what no regex decides, such as a requirement that hides
   its actor in the passive voice.
4. **`prompts/` follows the same style as an extra requirement of Concorde's own checkout**, not a
   Protocol rule: state it in the `concorde-development` skill source (`prompts/development/skill.md`,
   owned by `module.concorde`) and make the same checker runnable on the Markdown under `prompts/`,
   so the later rewrite tasks and future changes can measure it.
5. **All existing Specs, the Protocol's own documents and `prompts/` will be rewritten to the new
   style afterwards**, in separate tasks opened after this one merges, by pi sessions on project
   model `gpt-6.1-sol` (pi id `local-openai/gpt-6.1-sol`) at reasoning `medium`. Do NOT rewrite
   existing text in this task beyond the documents you author; but make the rules and the checker
   precise enough that those rewrite sessions can apply and measure them mechanically.

### The rules agreed (write them in the Protocol's own words)

Taken from STE's structural rules, paraphrased; never copy ASD-STE100 text or its dictionary (ASD
forbids redistribution, and the Protocol is copied into every project). Name STE as inspiration.

- One requirement or one fact per sentence; a normative sentence carries one obligation.
- Descriptive sentences of about 25 words at most (STE: 20 procedural, 25 descriptive).
- Three or more conditions, cases or items become a vertical list instead of a run of clauses.
- The condition comes before the command ("When X, the host SHALL Y").
- No semicolons in prose; write separate sentences or a list.
- Requirements name their actor and use the active voice; passive only when the actor is truly
  irrelevant.
- Prefer simple tenses.
- **Keep** the normative keywords MUST, MUST NOT, SHALL, SHOULD, MAY with their Protocol meanings:
  STE-derived rules that ban should/may do not apply.
- The project glossary is the controlled vocabulary: one word for one meaning, as the existing
  "Project terms" rule says. Do not import STE's word list or rules like "make sure that" for
  check/verify/validate, which collide with defined terms.

### Measurements the developer saw (baseline, primary at 86f3f37d)

Over the 132 Spec documents (~310k words, prose only, list items split): median sentence 20 words,
p90 47, 37% over 25 words, 15% over 40, 4% (~430 sentences) over 60, longest 167; 1,903
semicolons; ~3,150 passive-voice hits from a heuristic linter (too noisy to check mechanically).

### Material

Two MIT-licensed repos were assessed (cloned under the main agent's scratchpad; clone them again
if useful): https://github.com/danyuchn/asd-ste100-skill (`scripts/ste-lint.py`, structural-only
linter, does not flag modals) and https://github.com/AminBlg/SimpleEnglish (`evals/ste_lint.py`,
`references/rule-catalog.md`; its plain mode bans should/may and em dashes, which we reject). You
may borrow code from either with MIT attribution, or write the checker yourself; neither knows
Spec Markdown (code spans, fences, tables, headings, anchors, term links), which the check must skip.

### Left for the session to decide (record each in this log)

- The exact sentence-length threshold(s) the check warns at, chosen from measured data (the
  guidance target is ~25 words; the check may warn at a higher bound if 25 is too noisy), and
  which constructs it measures (sentence length, semicolons, possibly very long lists of clauses).
- Rule identities, where the guidance sits in the Protocol documents, Protocol version handling
  (`protocol-manifest --write --bind-project`), and how the checker is exposed for `prompts/`.
- Report the per-rule warning counts on the current Specs and on `prompts/` in your delivery
  report, since the rewrite tasks will be sized and verified by them.

Escalate together anything that would change these decisions.

## Task session decisions (2026-10-04)

- **Sentence-length threshold: the check warns above 35 words; the guidance target stays 25.**
  Measured on the 132 Spec documents with the final checker (same prose rules as the check):
  11,204 sentences, median 19, p90 47; >25: 36.0%, >30: 27.3%, >35: 20.2%, >40: 14.8%, >60: 4.0%.
  A sample of 36–40-word sentences all read as clearly too long; 30–35 were borderline. 25 as the
  check bound would leave permanent noise after the rewrite on acceptable 26–30-word sentences;
  35 is achievable for the rewrite sessions and leaves 25–35 to the reviewer's judgment. Fixed
  in the Protocol, not configurable.
- **Constructs measured (three warning checks):** `CHK.style.sentence-length` (>35 words),
  `CHK.style.semicolon` (any semicolon in prose), `CHK.style.one-obligation` (more than one of
  MUST/SHALL/SHOULD/MAY, each with an optional NOT, in one sentence; uppercase only). No check for
  "three or more clauses become a list", passive voice or condition order: no proxy was precise
  enough; Spec review judges them.
- **What counts as prose:** fences, headings, table rows, YAML front matter, HTML comments and
  HTML anchors are skipped; blockquote markers stripped; a link counts as its text; an inline
  code span counts as one word and its contents are never searched for semicolons or keywords;
  each paragraph and each list item is split with the existing `SENTENCE_BREAK` rule of
  `CHK.concept.definition`. Tables are skipped as the brief asked.
- **Concept definitions are measured too** (findings on the glossary path with the concept as
  subject): a definition is one sentence, and 36 of 108 definitions exceed 35 words, so the
  rewrite tasks need them measured.
- **Placement:** new Protocol chapter `protocol/style.md` "Sentence style", the fourth part of the
  Spec writing guidelines (writing.md, README, `prompts/protocol/kinds/module.md` bundle, so
  writer and reviewer workers receive it). Checks table section `## Style` in checks.md with two
  Limits rows; model.yaml lists the checks on `document` and `concept`. STE named as inspiration
  only; no STE text or dictionary copied.
- **Protocol version 16.2.0 (minor):** every 16.1 Spec stays valid; migration section added;
  `protocol/manifest.json` version edited by hand (the manifest command keeps the version), then
  `protocol-manifest --write --bind-project`.
- **Readability dimension:** `readability` already existed as a Module quality dimension
  (`protocol/evaluation.md`, spec-review's `DIMENSIONS`), so I extended it with the sentence-style
  criteria instead of adding a new dimension enum value, which would have changed spec-review's
  contracts for nothing. Style findings are advisory unless a reader cannot tell who must act or
  what is required (e.g. a requirement hiding its actor in the passive voice). The reviewer
  criteria now also include the Sentence style chapter (`CRITERIA` in spec_review/operation.py),
  and the checklist tells reviewers not to repeat what the checks report and to group instances
  of one kind in one document into one finding (avoids hundreds of low Issues per Module).
- **Checker exposure for prompts/:** shared code `src/concorde/spec/style.py` (module.spec,
  Validator realization); development script `scripts/development/check-style.py` (module.concorde,
  development environment) runs the same checks on any Markdown paths (default `prompts/`),
  prints `path:line: rule: message` plus per-rule and per-file counts, `--format json`, exit 1
  when problems. It also measures `protocol/`, which spec-validation does not read (the Protocol
  chapters are not Spec documents), so the Protocol rewrite task can use it. The requirement
  itself is in `prompts/development/skill.md` and `specs/concorde/development.md`
  (`scenario.concorde.check-style`): a change adds no new style problem to a prompt.
- **Fixture text changed:** two semicolons in Spec test fixtures (`tests/concorde/support/spec_project.py`,
  `tests/concorde/spec/test_checks.py`) became periods so the "fixture conforms" tests keep
  asserting only the coverage warning.
- **Size note:** spec-validation now returns ~3,700 warnings on Concorde's Specs (~1.4 MB JSON);
  task-validation and specify keep warnings in their results. Accepted as temporary until the
  rewrite tasks; traces are not tracked by Git.
- **Not changed (outside this task's Modules):** `prompts/workers/common/spec-format.md`
  (module.workers) still says the guide has "both parts"; specification/adoption module docs list
  the bundle's contents without Evaluating a Spec / Sentence style. Writers still receive the
  chapter through the bundle. Natural to fix in the prompts rewrite task.

## Report 1 to the main agent (concorde-f8), 2026-10-04T05:41:46Z

spec-style delivered: delivery commit 9d3ffc51 on concorde/spec-style (work commit cf438dcb; delivery run r-20261004T053415-delivery-d1a3f7a5). Verified: build --check, protocol-manifest --write --bind-project, spec-validation success (0 errors), full pytest 1253 passed / 5 skipped, task-validation ready (0 blocking, 25 checks).

What changed:
- Protocol 16.2.0 (minor; every 16.1 Spec stays valid; migration section added). New chapter protocol/style.md "Sentence style", the fourth part of the Spec writing guidelines (writing.md, README, the kinds/module bundle, so writer and reviewer workers receive it). It is written in the Protocol's own words, names ASD-STE100 as inspiration only and copies no STE text. Rules: one fact per sentence (one requirement keyword at most), descriptive sentences of 25 words or fewer, a list for three or more conditions, cases or items (with a requirement example: obligation, colon, then the list), the condition before the statement, no semicolons, a named actor in the active voice, simple tenses, and the glossary as controlled vocabulary. MUST/SHALL/SHOULD/MAY keep their Protocol meanings, and STE's should/may ban does not apply.
- Three warning checks in checks.md "## Style" and model.yaml (document and concept): CHK.style.sentence-length (>35 words), CHK.style.semicolon and CHK.style.one-obligation (>1 uppercase keyword, NOT included). They measure every document's prose and every concept definition. Fences, headings, tables, front matter, comments and anchors are skipped. A link counts as its text, inline code counts as one word and is never searched. Sentences are split with the existing CHK.concept.definition sentence-break rule. Code: src/concorde/spec/style.py (Validator realization), wired into validation.py; scenario.spec.style-warnings with tests.
- Readability: protocol/evaluation.md's existing readability dimension now judges the non-decidable rules: passive voice and hidden actor, one fact per sentence, lists, condition order, tenses. A style problem is advisory unless the reader cannot tell who must act or what is required, as with a requirement that hides its actor. spec_review's CRITERIA appends the Sentence style chapter. The reviewer checklist says not to repeat what the checks report, and to group the instances of one kind in one document into one finding. The spec-review module.md says the same.
- prompts/: the requirement is in prompts/development/skill.md and specs/concorde/development.md (scenario.concorde.check-style): a change adds no new style problem to a prompt. The checker for it is scripts/development/check-style.py [paths…] [--format json] (default prompts/, exit 1 on problems), which uses the same code. It also measures protocol/, which spec-validation does not read.

Decisions I made (details in the decision log):
- The check warns above 35 words, and the guidance target stays 25. On the Specs, 36% of sentences are over 25 words, 20% over 35 and 15% over 40. Sampled sentences of 36–40 words were all clearly too long. A bound of 25 would leave permanent noise on acceptable sentences of 26–30 words.
- No check for passive voice, condition order or clause runs, since no proxy was precise enough. Review judges them.
- Concept definitions are measured too.
- The existing readability dimension is extended rather than a new enum value added.
- Two fixture semicolons in tests became periods.
- Size note: spec-validation now returns about 3,700 warnings on our Specs (about 1.4 MB JSON) until the rewrite.

Baseline warning counts for the rewrite tasks:
- Specs (spec-validation, 123 of 132 documents plus the glossary): sentence-length 2303 (36 of them glossary definitions), semicolon 1388 (7 in the glossary), one-obligation 0. Worst documents: coordination/main-session/module.md 177, coordination/tasks/module.md 169, distribution/module.md 137, workflows/module.md 109, module.md 102.
- prompts/ (check-style.py, 33 of 40 files, 385 problems): sentence-length 205, semicolon 180, one-obligation 0.
- protocol/ (check-style.py protocol, 15 files): sentence-length 58, semicolon 159, one-obligation 9.

Open, outside this task's Modules, with no decision needed:
- prompts/workers/common/spec-format.md (module.workers) still says the writing guide has "both parts".
- The specification and adoption module docs list the bundle's contents without Evaluating a Spec or Sentence style.
- Writers still receive the chapter through the bundle. These fit the prompts and Specs rewrite tasks.

No escalations. No Issues resolved.

## Closed: merged, 2026-10-04T05:42:07Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 9d3ffc51ae152d93c9b226165cdbd65663f9de06 into main and closed it as merged. Nobody answers a report after that.
