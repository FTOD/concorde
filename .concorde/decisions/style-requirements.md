# Decision log: style-requirements

Goal: Revise the Protocol's Sentence style so that a requirement keeps one obligation with its conditions and exceptions in one SHALL sentence, keeps causal links, and is exempt from the sentence-length bound


## Task brief (main agent, 2026-10-05)

### Why

Six tasks rewrote every Spec to `protocol/style.md`, the Sentence style, with pi. Main is now at
Protocol 16.3; read `.concorde/decisions/restyle-*.md` and `glossary-definitions.md` for the
history. An experiment by the main agent showed that several drifts come from style.md's own rules
when they are applied to requirement statements. The runs are saved under the main agent's
scratchpad `pi-probe/runs/`, but you do not need them. The drifts were:

- **"Lists for three or more"** made pi turn ONE obligation into a list of separate rules: "SHALL
  observe both rules: … - Never write into the history afterwards."
- **"The condition before the statement"** made pi move a condition away from what it limits: "Only
  after X, Task sessions SHALL …", or "When X, the guidance SHALL tell the main agent to do Y"
  when X limits the instruction rather than the guidance.
- **"The actor and the active voice"** made pi change the subject of an obligation, for example to
  "Task sessions SHALL write a boundary that lets…".
- **The 35-word check** made pi cut words that carry meaning, such as each, every, only, "as it
  succeeded", and causal links like since, so and because. It also made pi move failure clauses
  out of the SHALL statement.

### The developer's decision (2026-10-05)

The developer approved revising style.md as follows:

1. **One obligation stays one SHALL sentence, with its conditions, exceptions and failure
   clauses.** A requirement statement is never split into a list of separate rules. The existing
   form "obligation, colon, list of conditions" stays allowed, because its list items are the
   conditions of one obligation, not new obligations. Show the difference with a right and a wrong
   example.
2. **Keep causal and logical links**, such as since, because, so that, only, each, every and
   never. A rewrite must not drop them to shorten a sentence.
3. **Requirement statements are exempt from the sentence-length bound.** Change
   `CHK.style.sentence-length` so that it does not measure the statement sentence of a requirement.
   Descriptive prose keeps 35 words, and concept definitions keep 50.
4. **Clarify how "condition first" and "named actor" apply to a requirement.** A condition stays
   next to what it limits. The subject of an obligation is the party that bears it, and a rewrite
   never introduces an actor that the original did not name.

### What to do

- Update style.md, checks.md, `src/concorde/spec/style.py` and its tests, and migration.md. Bump
  the Protocol version: a check changes, so a minor bump such as 16.4 fits, but you decide. Run
  `protocol-manifest --write --bind-project` and set `protocol/manifest.json`'s version by hand, as
  glossary-definitions had to.
- Update the readability criteria in `protocol/evaluation.md` and the spec-review checklist
  (module.spec-review) so that reviewers flag these drift patterns.
- Do NOT rewrite existing requirements in this task. An audit of the already-rewritten
  requirements may follow later as its own work.
- Verify with spec-validation (0 errors), build --check, the relevant tests and the full pytest, and
  report the `CHK.style.*` counts before and after.

## Task session (2026-10-05)

- Worktree prepared (init-references, uv sync, npm ci, build).
- Baseline `spec-validation`: 0 errors, `CHK.style.sentence-length` 11, `CHK.style.semicolon` 0,
  `CHK.style.one-obligation` 0 (plus 1 pre-existing `CHK.term.unlinked`). All 11 are scenario
  steps, none a requirement statement, so the exemption changes no current count.
- Protocol version 16.4 (manifest and binding `16.4.0`). Reason: a check's statement changes, and
  every specification valid under 16.3 stays valid, as for 16.3.
- What the check skips: the first sentence of the first prose paragraph after a `req.` heading,
  with only blank lines between, which is what `CHK.requirement.statement` reads as the statement.
  The detection lives in `style.py` itself (it reads the heading with syntax's
  `REQUIREMENT_HEADING`) rather than in validation, so that `check-style.py` measures the same way.
  Only the length check skips it: `CHK.style.semicolon` and `CHK.style.one-obligation` still
  measure it. List items below a statement and later explanation sentences stay measured, because
  the developer's decision exempts the statement sentence only.
- style.md structure: a new rule section "Requirements" holds the one-obligation rule, the right
  and wrong example, condition placement and subject preservation. A new rule section "The links
  between facts" holds decision 2, since it applies to every rewrite, not only to requirements.
  Short notes in "One fact in each sentence", "Short sentences", "Lists for three or more", "The
  condition before the statement", "The actor and the active voice" and "What a program measures"
  point to them. I also added one intro sentence: the rules never change what a text means, and the
  meaning wins when a rule would change it. Reason: it states the common cause of all four
  drifts.
- I chose a neutral example (`req.runner.remove-checkout`) for the right and wrong forms rather
  than the history drift itself, because "write once and never change" could read as two
  obligations.
- Severity: evaluation.md, the spec-review checklist and module.spec-review say a drift that
  changes what a requirement requires or who bears it is blocking. Other drifts follow the existing
  rule (advisory while a reader still understands correctly).
- The `CHK.style.sentence-length` remediation now adds "keep every word that carries meaning".
- Spec core: validation.md (Style family row and the measured-prose paragraph) and
  `scenario.spec.style-warnings` (a BUT step: the statement of a requirement is not measured) are
  updated. Two tests verify it: a long statement is not reported while a long explanation sentence
  and list item below it are, and a statement still gets the semicolon and one-obligation warnings.

## Report 1 to the main agent (concorde-f8), 2026-10-05T04:47:15Z

style-requirements delivered: delivery commit 29b75fd5 on concorde/style-requirements, on top of 6329fddb (Protocol 16.4). No escalations. It resolves no Issues.

Verification: spec-validation 0 errors. build --check clean. check-style.py on prompts/ and protocol/ reports 0 problems. The style tests pass. The full pytest gives 1256 passed and 5 skipped. task-validation is ready (25 checks).

CHK.style.* counts, before / after: sentence-length 11 / 11, semicolon 0 / 0, one-obligation 0 / 0. The 11 are pre-existing scenario steps (spec, views and workers scenarios.md). None is a requirement statement, so the exemption changes no current count. The one CHK.term.unlinked warning is pre-existing.

What changed (Protocol 16.4, manifest and binding 16.4.0):
- style.md: a new rule "Requirements". One obligation stays one SHALL sentence with its conditions, exceptions and failures, whatever its length. A list below the statement gives conditions, never new obligations. It has a right and a wrong example (req.runner.remove-checkout). A condition stays next to what it limits (example: "merge a task only after its delivery"). The subject is the party that bears the obligation (example: "The guidance SHALL tell each task session to ..."). A rewrite never introduces an actor the text did not name, since choosing one is a Spec change.
- style.md: a new rule "The links between facts". Keep since, because, so, so that, only, each, every, never, at most, when, unless, until and except. Carry the link into a split sentence. One intro sentence says the rules never change what a text means, and the meaning wins. Short pointers were added in One fact, Short sentences, Lists, Condition first, Actor and What a program measures.
- CHK.style.sentence-length no longer measures a requirement's statement: the first sentence of the first paragraph after a req. heading, with only blank lines between, as CHK.requirement.statement reads it. The semicolon and one-obligation checks still measure it. Explanation sentences and list items below the statement are still measured. Prose keeps 35 words and definitions keep 50. The detection is in style.py, so check-style.py measures the same way. The remediation hint adds "keep every word that carries meaning".
- checks.md: the statement and the limits row. migration.md: the 16.4 section. README, principles and model.yaml: the version.
- evaluation.md (readability), prompts/workers/spec-review/checklist.md and specs/concorde/method/spec-review/module.md: reviewers report five drifts. These are a split obligation, a condition moved out of the statement, a condition moved away from what it limits, a changed or added subject, and a dropped link word. A drift that changes what a requirement requires or who bears it is blocking. Other drifts stay advisory while a reader still understands correctly.
- Spec core: validation.md (the Style row and the measured-prose paragraph), and scenario.spec.style-warnings, which gains the BUT step "the statement of a requirement is not measured for length". Two new tests: a long statement is not reported while the explanation and the list item are, and a statement still gets the semicolon and one-obligation warnings.

Decisions I took (each is in the decision log with its reason):
- Version 16.4 rather than a patch, because a check's statement changes and every 16.3-valid spec stays valid.
- Only the statement sentence is exempt, not its condition list items, because the decision names the statement sentence. The condition items are usually short.
- The links rule is general, not requirement-only, because pi dropped links in prose too.
- I used a neutral example rather than the history drift, because "write once and never change" could read as two obligations.
- Drifts that change a requirement's meaning or bearer are blocking.

Open: as the brief says, no existing requirement was rewritten. Auditing the requirements that earlier restyles changed, for example by searching for statements followed by rule lists or for moved "Only after" conditions, remains possible later work.

## Closed: merged, 2026-10-05T04:47:34Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 29b75fd5863b4ba4236ea935d6a67af0dcefa17b into main and closed it as merged. Nobody answers a report after that.
