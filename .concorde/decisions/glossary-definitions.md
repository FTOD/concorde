# Decision log: glossary-definitions

Goal: Make every glossary definition a short full-grammar sentence that identifies its term, and move the details it drops into the owner Module's explanation


## Task brief (main agent, 2026-10-04)

### Background

Protocol 16.2 added "Sentence style" (`protocol/style.md`). Its sentence-length check also measures
every glossary definition, which the Protocol requires to be one sentence. Task `restyle-root`
(merged) rewrote 30 of the 38 definitions over 35 words to fit. Many of those 30 became
telegraphic. They drop articles and pile up noun chains such as "task-named workspace",
"primary-worktree folder", "a workspace branch's first-parent history" and "by the preparer". Some
lost details, for example `concept.run-store` ("until, if ever, it holds"),
`concept.workspace-lock` and `concept.delivery-commit`. The other 8 stayed over the limit as
exceptions: `concept.main-agent`, `task-record`, `workflow-mode`, `workspace-binding`, `trace`,
`project-mcp-server`, `standard-worker-sequence` and `worker-configuration`. restyle-root's log in
`.concorde/decisions/` lists what it changed. Compare with the definitions at commit d4423f70.

### The developer's decision (2026-10-04)

A definition is **one full-grammar sentence of 35 words or fewer** (target 25) that **identifies
the term**: what it is and what distinguishes it from its neighbours. The details a definition no
longer carries move into the **explanation** paragraph of the owner Module's document, the
glossary entry's `explanation` anchor, unless that paragraph already states them. A detail moves;
it never vanishes. The developer chose this over relaxing the limit, partly because every session
loads the whole glossary.

### What to do

- Rewrite every definition that is telegraphic or over 35 words, among them all 30 changed by
  restyle-root and all 8 exceptions. Also check the other definitions over about 30 words. 57
  definitions are over 30 words now.
- Use full grammar: keep the articles, write no hyphenated noun chains and no stacked possessives,
  and follow `protocol/style.md`.
- Keep ids, titles, owners, explanation anchors, relations and contrasts unchanged. Keep each term's
  meaning and its boundary. A shorter definition must not make the term cover more or less than
  before.
- For each detail you remove, check the owner's explanation paragraph, and add the detail there in
  the Sentence style when it is missing. Those paragraphs sit in many Modules' `module.md` files.
  Edit only the explanation paragraphs of the concepts you change.
- Write the final text yourself. You may use pi (`local-openai/gpt-6.1-sol`, `--thinking medium`)
  for drafts or for an independent meaning check, but restyle-root found that pi drops details from
  definitions.

### Verification

`spec-validation` must report 0 errors and no `CHK.style.*` warning from the glossary. Run
`build --check` and the tests that assert glossary or explanation text, and run the full pytest
once. In your delivery report, list each definition's old and new word count and each detail you
moved, with its destination.

### Left for the session to decide

The exact wording, and whether a detail is identifying (it stays) or explanatory (it moves). If a
definition cannot identify its term in 35 words without losing the term's boundary, escalate it
with the shortest faithful version you found.

## Task session (2026-10-04)

- Worktree prepared (init-references, uv sync, npm ci, build). The Skill tool did not list
  `concorde` and `concorde-development` before the build; I read `generated/skills/*/SKILL.md`.
- Scope decision: I rewrote 44 definitions: the 30 that restyle-root changed (except
  `concept.module`, whose restyled text "with its own Spec, that need not be a package or directory"
  is already a full-grammar sentence of 18 words), the 8 exceptions, and 7 unchanged ones of 34 or
  35 words that could reach the target without loss: capability-context, file-transaction,
  readiness, runtime-directory, step-key, task-type, workflow-step. Reason: these were at the limit
  and shortened cleanly.
- I left 13 definitions of 31 to 33 words unchanged: boundary-set, concorde-defect,
  context-identity, develop-install, grant, resume-round, review-finding, run-directory,
  spec-change, unbound-run, worker, worker-result, workflow-script. Reason: each is already a
  full-grammar sentence that identifies its term. A shorter one would only drop an identifying
  detail or add a meaning risk for a few words.
- I wrote every definition myself, without a pi draft. Each definition is applied by script, so
  ids, titles, owners, anchors and relations stay byte-identical.
- Identifying versus explanatory: I kept what tells the term from its neighbours (for example "one
  process at a time" for the merge lock, "first-parent history … exactly one parent" for the
  delivery commit, "without external material" for the Spec context). I moved field lists, paths,
  exact time spans, actors and examples to the explanation paragraphs.

## Main agent (2026-10-05): the developer relaxed the length limit

The developer said on 2026-10-05 that the glossary may have a looser length limit and need not be
held so strictly. This replaces the "35 words or fewer" bound of the brief. Full grammar stays
required: no telegraphic compression, no dropped articles, no hyphenated noun chains.

My decisions within that direction:

- A definition is still one full-grammar sentence that identifies its term. Keep an identifying
  detail in the definition rather than moving it out to save words. Move only details that are
  clearly explanatory, such as long field lists, exact paths or time spans, and examples.
- Let the style check measure concept definitions against a bound of **50 words** instead of 35.
  This changes `protocol/style.md`, the "Style" section of `protocol/checks.md`,
  `src/concorde/spec/style.py` and its tests, and needs a Protocol version and
  `protocol-manifest --write --bind-project`. You choose the version. Prose sentences keep 35.
- Reconsider the definitions you already shortened. Where a 35-word cut dropped an identifying
  detail or reads cramped, restore the detail within 50 words.
- A definition still over 50 words is an exception. Record it with its reason, and do not escalate
  it.

### After the main agent's 2026-10-05 relaxation (task session)

- Protocol version: 16.3 (manifest and binding `16.3.0`), committed as 2dfa4dbd. Reason: a check's
  statement changes, which is more than the wording-only patch 16.2.1, and every specification
  valid under 16.2.1 stays valid. `CHK.style.sentence-length` takes the bound as an argument:
  `SENTENCE_LIMIT` 35 for a reading, `DEFINITION_LIMIT` 50 for a concept definition. Also updated:
  `protocol/style.md` (Short sentences, What a program measures), `protocol/checks.md` (statement and
  limits), `protocol/migration.md`, `README.md`, `principles.md`, `model.yaml`, Spec core's
  `validation.md` table and `scenario.spec.style-warnings`, the spec-review checklist, and
  `test_checks.py` (a 72-word definition is reported, 50 words are not, 51 are).
- Non-ok result: the first `spec-validation` after `protocol-manifest --write --bind-project`
  failed with `CONCORDE-SOURCE-008`, because `protocol/manifest.json` keeps its version by hand and
  still said 16.2.1. I set it to 16.3.0 and bound again. Validation then passed.
- Definitions revised under the 50-word bound. 11 went back to their text at d4423f70, which is
  full grammar and fits 50 words, because restyle-root's cut had dropped identifying details:
  capability-context, error-chain, implementation-context, main-agent, main-session-guidance,
  optional-integration, part, readiness, run-result, spec-context, task-brief.
- In 11 others I restored the identifying detail in my own sentence: decision-log (committed to
  the primary branch when the task ends), merge-lock (the operating system releases it), operation
  (registered by its providing part, host steps and service calls), project-mcp-server (a fresh
  process of the current Concorde answers each call), session-boundary (its only restriction),
  standard-worker-sequence (its stages), task (the folder holds record, decision log and trace),
  task-session (the main agent hands it every task, it reports and escalates), task-type (the eight
  types), worker-backend (chosen per worker or Operation, same grant either way),
  worker-configuration (sets backend, model and level per scope, the most specific entry wins),
  workflow-mode (also ends at a step not ended ok, no-ask reports at the end).
- The rest keep the short version, because what they dropped is explanatory: field lists, exact
  paths, time spans and examples (check-result, run-lock, run-store, runtime-directory, trace-node,
  workspace-binding, workspace-lock and others).
- Explanation sentences I had added only for a detail that is now back in its definition are
  reverted, so the explanation diff holds only moved details.
- No definition is over 50 words, so there is no exception.
- Meaning check: a pi call (gpt-6.1-sol, medium) compared each old definition with the new one and
  the explanation paragraph as it stands now. It found no term that is wider or narrower, except
  one slip, which I repaired. I repaired these findings:
  - worker-backend: it says again that the worktree's worker configuration chooses the backend.
  - decision-log: it names the task sessions' reports and the main agent's answers again.
  - history: "after the close" instead of "afterwards", because the close itself removes
    `runtime/`.
  - delivery-commit: the Kernel explanation now says that `delivery` and `task deliver` make the
    commit.

  I accepted two findings as minor. run-store: "until they hold their workspace lock" already
  covers a run that never does. workspace-lock: "a run holds it" means the run's process.
- An earlier pi check on the 35-word drafts was stopped unfinished when the bound changed.

## Report 1 to the main agent (concorde-f8), 2026-10-05T04:11:49Z

glossary-definitions delivered: delivery commit f97c08ce on concorde/glossary-definitions, on top of 2dfa4dbd (Protocol 16.3) and b15d3e3d (glossary and explanations). No escalations. It resolves no Issues.

Verification: spec-validation 0 errors. Its 12 warnings are pre-existing ones in spec/views/workers scenarios.md and workers contracts.md, and none comes from the glossary or a file I changed. build --check is clean. check-style.py on protocol/ and the spec-review prompts reports 0 problems. The full pytest gives 1254 passed and 5 skipped. task-validation is ready.

Protocol 16.3 (manifest and binding 16.3.0), following your 2026-10-05 decision:
- CHK.style.sentence-length measures a concept definition against DEFINITION_LIMIT = 50. A reading keeps SENTENCE_LIMIT = 35.
- Changed: style.md (Short sentences, What a program measures), checks.md (statement and limits), migration.md, README, principles, model.yaml, Spec core's validation.md table, scenario.spec.style-warnings, the spec-review checklist, and test_checks.py (a definition of 50 words passes, 51 is reported).
- I chose 16.3 rather than a patch release because a check's statement changes. Every spec valid under 16.2.1 stays valid.

Definitions: the counts are at d4423f70 / at restyle-root / now. 41 of them changed. No definition is over 50 words, so there is no exception. main-agent (49), capability-context (35) and readiness (35) stay as they were: each is full grammar at d4423f70 and fits the new bound.
- Original text restored (full grammar, within 50): error-chain 41/35→41, implementation-context 45/35→45, main-session-guidance 40/34→40, optional-integration 38/35→38, part 42/33→42, run-result 38/31→38, spec-context 40/35→40, task-brief 40/34→40.
- Rewritten: agent-harness 41/35→26, check-result 36/34→26, decision-log 52/35→46, decision-point 55/35→29, delivery-commit 43/35→30, file-transaction 34/34→28, history 45/35→27, merge-lock 44/35→33, model-map 47/35→29, operation 39/34→38, operation-catalog 39/31→27, part-registration 40/35→21, project-mcp-server 78/78→45, run-lock 39/35→28, run-store 47/34→28, runtime-directory 35/35→25, session-boundary 36/33→37, standard-worker-sequence 82/82→47, step-agent 40/34→28, step-key 34/34→30, task 51/34→40, task-record 55/55→24, task-session 51/35→48, task-type 34/34→36, trace 43/43→23, trace-node 41/35→30, unbound-checkout 41/35→29, worker-backend 31/31→37, worker-configuration 90/90→45, workflow-mode 52/52→44, workflow-step 35/35→23, workspace-binding 49/49→28, workspace-lock 47/34→26.

Details moved, with their destination. Each one was added where the paragraph did not state it already:
- check-result: the check and its Module, and the log's own digest. Added as a list to execution/checks/module.md.
- project-mcp-server: it takes locks without waiting, hands a granted lock to the detached process, and wakes its session through a Claude Code channel. Added to distribution/module.md.
- run-lock: only the runner locks it, from before the first run progress file until after the result, and removes the file on exit. Added to execution/module.md.
- trace-node: the record's fields. Added as a list to kernel/tracing/module.md.
- trace: how the nodes nest (task, workspace, run, worker run). Added as a list there.
- runtime-directory: its contents (configuration, credential copies, home, temporary and working directories). Added to workers/module.md.
- worker-configuration: required for every launch; enabled models with optional levels; entries for all workers, an Operation and one worker id, the most specific entry winning; launch limits; runtime paths. Added to workers/module.md.
- model-map: its path with CONCORDE_MODEL_MAP and XDG_CONFIG_HOME, and the refusal without a backend id. Added to workers/module.md.
- task: the folder moves to the history at the end. Added to tasks/module.md.
- delivery-commit: `delivery` and `task deliver` make the commit. The Kernel explanation now says so.
- Already stated in their explanations: agent-harness (who applies it), decision-point (who settles it, which Operation decides), history (the merge answer, retention, contents), merge-lock (examples), operation-catalog (unbound, changes workspace), part-registration (field list), run-store (paths, lobby), task-record (field list), unbound-checkout (path, removal), workspace-binding (fields, read only), workspace-lock (time span, the preparer), step-agent (asks again), standard-worker-sequence (admission), workflow-step (returns the recorded run).

Decisions I took, each recorded in the decision log with its reason:
- I left 13 definitions of 31 to 33 words unchanged, because each is already full grammar and identifying: boundary-set, concorde-defect, context-identity, develop-install, grant, resume-round, review-finding, run-directory, spec-change, unbound-run, worker, worker-result, workflow-script. module (18) keeps restyle-root's sentence.
- I wrote the text myself. A pi meaning check (gpt-6.1-sol, medium) compared the old definition with the new definition and explanation. I repaired 4 of its findings: worker-backend ("the worktree's" configuration), decision-log (the task sessions' reports and the main agent's answers), history ("after the close", since the close removes runtime/) and delivery-commit (who makes it). I accepted 2 as minor: run-store's lobby wording and workspace-lock's "a run holds it".
- Non-ok result: the first spec-validation after protocol-manifest failed with CONCORDE-SOURCE-008. protocol/manifest.json keeps its version by hand and still said 16.2.1. I set it to 16.3.0 and bound again.

Nothing is open.

## Closed: merged, 2026-10-05T04:12:13Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit f97c08ce764448198423b394592ee46c5781d5a3 into main and closed it as merged. Nobody answers a report after that.
