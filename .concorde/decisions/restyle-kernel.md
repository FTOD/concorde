# Decision log: restyle-kernel

Goal: Rewrite the existing Specs and prompts of its scope to Protocol 16.2's Sentence style, unchanged in meaning, with pi on gpt-6.1-sol: Kernel, Tracing, Distribution, Issues and Workflows


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

Paths: `specs/concorde/kernel/**`, `specs/concorde/distribution/**`, `specs/concorde/issues/**` and `specs/concorde/workflows/**` (Markdown only), and `prompts/guidance/kernel/`, `prompts/guidance/distribution/`, `prompts/guidance/issues/` and `prompts/guidance/workflows/`. Baseline worst documents: distribution/module.md 137, workflows/module.md 109.

## Task session (2026-10-04)

- Baseline in scope: `spec-validation` reports 785 `CHK.style.*` warnings (490 sentence-length, 295
  semicolon, 0 one-obligation) and no error. `check-style.py` on the four prompt folders reports 53
  problems (33 sentence-length, 20 semicolon).
- Batching: each document is split outside fences at `##`/`###` headings into chunks of about 1600
  words (78 chunks in all, each prompt file one chunk). One pi call rewrites one chunk file in a
  scratch directory outside the worktree, reading the whole original document for context, and runs
  `check-style.py` on its chunk until it reports nothing. The eight prompt files go in one pi call.
  Four pi processes run at a time, on disjoint chunks. The chunks are then joined back.
- pi runs with `--no-context-files` so that it does not load this checkout's `CLAUDE.md` and its
  task-session rules, which do not concern a rewriting worker, and with only the tools read, edit,
  write and bash.
- Markdown tables stay unchanged: the style checks do not measure them, and their rows and first
  columns are identities. A script checks after each rewrite that headings, fences, tables, HTML
  anchors, front matter, inline code spans and link targets are unchanged, and it lists every change
  of the requirement keyword counts and scenario steps for review.
- A long scenario step may be split into several `AND` steps. The Protocol's scenario format allows
  only steps as list items, so a scenario cannot use a nested list.
- The rewrite's scratch files (chunks, pi logs, meaning checks) live in the worktree's git-ignored `.generated/restyle-scratch/`, so that nothing is written outside the task worktree. It is removed before delivery.

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
- Following the main agent's note on restyle-root, the rewrite, meaning-check and repair prompts now
  name its error rules and drift patterns (one-sentence one-SHALL statements, no nested scenario
  lists, no dropped "only"/"itself"/"alone", no invented actor, no inverted relation, no telegraphic
  compression), and at most 2 pi lanes run from here on. The 4 lanes that ran before the note hit
  `gateway_concurrency_limit` repeatedly; each call retries after 30 to 90 seconds.
- Each chunk goes through rewrite, an independent pi meaning check, and a pi repair round fed by
  that check's list; I then read every final diff against the original myself.
- Non-`ok` results so far: pi timed out (40 minutes) on `distribution/module.md` chunk 3 with 30 problems and on `distribution/contracts.md` chunk 0 with 11
  problems left, and on `distribution/scenarios.md` chunk 2 with none left; the first is rewritten
  again.
- (Correction to the entry above: both timed-out chunks with problems left are rewritten again.)

## Main agent note (2026-10-04): lessons from restyle-coordination

pi made two kinds of drift most often there:

- **A condition moved to the front of a guidance requirement.** "When X, the guidance SHALL tell
  the main agent to do Y" limits the guidance's own obligation, not the instruction it gives. Keep
  the condition inside the instruction: "The guidance SHALL tell the main agent to do Y when X."
- **A series turned into scenario steps.** pi wrote a colon step followed by "AND <item>" steps, or
  lists inside scenario sections. Write the series as complete steps or keep it inline.

A second pi pass that compares the old and the new text catches the first pass's drift reliably.
- Restyle-coordination's lessons (conditions kept inside a guidance instruction, no colon step followed by AND items) are added to the check and repair prompts for the chunks not checked yet; the chunks checked before are scanned for both patterns.

## Task session: rewrite done (2026-10-04)

Commits on `concorde/restyle-kernel`: 680ab945 (Kernel, Tracing, kernel guidance), 01a7094e
(Distribution), 5f7eadf0 (Issues), b987f038 (Workflows).

**Counts.** `spec-validation` in scope: 785 `CHK.style.*` warnings before (490 sentence-length, 295
semicolon), 0 after, and 0 errors. `check-style.py` on the four prompt folders: 53 problems before
(33 sentence-length, 20 semicolon), 0 after. `build` and `build --check` pass. No long sentence was
kept as an exception.

**Not rewritten.** `distribution/scenarios.md` part 2 had no style problem and pi left it as it was.
Several scenarios of `distribution/scenarios.md` that pi had split into "AND alternatively" steps
were restored to their original steps, which the checks accept, and only their two steps over 35
words were split by hand. Markdown tables stay unchanged, as decided above.

**Meaning review.** An independent pi pass listed 276 possible meaning differences; the pi repair
pass judged 200 real and fixed them, and 75 not real (one got no verdict). I then read every diff
of the 78 parts against the original and fixed by hand what both passes had missed or introduced:

- Repair pass error: `prompts/guidance/distribution/skill.md` said the open tasks come with "that
  validation"'s result; restored to the update's result, which `open_tasks` of the update result
  contract confirms.
- Requirement statements that were no longer one sentence with one SHALL (spec-validation errors):
  distribution `one-envelope`, `composed-from-registrations`, `guidance-absent-parts`,
  `receipt-complete`, `protocol-manifest-precondition` (also a list that named actions after a
  colon announcing conditions), `installer-keeps-installation-bound` (its list was "under these
  conditions" but held the purpose), `mcp-current-code` and `mcp-current-serving` (part of the
  obligation had been moved into a later paragraph), `mcp-call-failed`; issues `committed-visible`,
  `main-agent-actor` (the list mixed what is recorded with when), `durable-receipt` (inverted
  "Only after …, SHALL"); kernel `refusals-coded`; tracing `roots-registered`, `history-unchanged`
  (retention had been pulled into the obligation), `conversations-shorter`, `retention-explicit`;
  workflows `one-at-a-time` (inverted word order), `complete-report` (simplified repetition).
- Invalid or misleading scenario steps: nested lists in issues `command-usage` and
  `command-unknown-issue`; "AND alternatively" steps in distribution scenarios (restored as above);
  colon steps followed by AND items in kernel `binding-refused`, `registration-repeated`,
  `registration-dialect`, `typed-embedded-refused`, `transaction-malformed`, `deliveries-listed` and
  tracing `kind-registered`; issues `command-write-failed` (the error chain had become "the write
  error"), `command-list-filtered` (over-split WHEN steps), `store-interrupted-move` (a THEN fact
  had moved into GIVEN).
- Drifted descriptive text: tracing module "These Modules are in: Concorde Tasks" (pi misread "in
  Concorde, Tasks, …"); distribution module step 7 (the workflow's sources had lost their owner),
  the task worktree's Framework copy ("In that case" pointed at the wrong case), `init --apply`
  "only where … does" inversion; issues module merge-lock sentence (who holds the lock was
  inverted); workflows module the guidance section list (modes and reports had become sections of
  their own) and the live-run sentence ("instead" had lost its referent); kernel module "may load
  twice" (was "may be loaded"), the lock's first taker (a lost "because"); and several smaller
  repetitions, dangling pronouns and nested one-word lists, tidied without changing content.

Every remaining difference I found is wording only. The full list of the independent check's
findings with the repair pass's verdicts follows.

### Appendix: independent meaning check and repair verdicts

- `specs/concorde/distribution/contracts.md` (part 01):
  - Session: The explicit restriction to the server's ancestors is lost. With "the session" now the sentence's subject, whose ancestors are checked and where the eight-level count starts become ambiguous; this is a possible meaning c → fixed
- `specs/concorde/distribution/module.md` (part 00):
  - Parts and their registrations: Changes a check of current activity into wording that can describe whether the part's work runs there generally, losing the explicit current-running meaning. → fixed
  - Parts and their registrations: Potential scope change: the original enumeration can be read as illustrative; "These entries are" presents the four entry kinds as exhaustive, potentially excluding other kinds. → fixed
- `specs/concorde/distribution/module.md` (part 01):
  - Reconciling the Protocol manifest: Past-tense comparison becomes present-tense comparison. After `--write` reconciles the digests, the rewrite can mean only remaining differences rather than the differences detected before writing; the reporting time is n → fixed
  - The command line: Possible narrowing: the rewrite specifies one project model name per candidate, whereas the original's plural wording permits multiple names per candidate, although it could also be read as a distributive plural. → fixed
- `specs/concorde/distribution/module.md` (part 02):
  - Serving a call: The waking condition now refers to "that work", apparently the previously named long work, rather than everything watched that outlives the call. This potentially narrows the statement to exclude waits; the later watchin → fixed
  - Serving a call: The registration condition now explicitly limits only the no-wait statement. Lock acquisition, immediate refusal naming the holder, and replacement with the work command become standalone statements, potentially extendin → fixed
  - Serving a call: A qualification identifying the eligible ancestor process becomes a separate assertion about that process. Potentially, the rewrite no longer makes terminal standard input a condition for selecting the command line to in → fixed
  - Serving a call: The explanatory relation between shared locking and server use being recommended rather than enforced is lost; shared locking becomes a separate claim. → fixed
- `specs/concorde/distribution/module.md` (part 03):
  - Installing into a project: Possible condition-scope change: the original explicitly conditions both placements on the spec part; the separate docsite sentence now relies on "also" to carry that condition and can be read as unconditional. → fixed
  - Installing into a project: Possible condition-scope change: the workflow-part condition explicitly governed both workflow installation and permission additions; the rewritten permission statement is separate and no longer explicitly conditional. → fixed
  - Installing into a project: The actor of "It" becomes ambiguous after introducing the workflow part as a sentence subject: it can now mean the workflow part rather than the installer, changing who adds and records permissions. → fixed
  - Installing into a project: The possessive reference becomes ambiguous in the list: "Its own" can now refer to Coordination, the preceding named actor, rather than the installer/Distribution. → fixed
- `specs/concorde/distribution/module.md` (part 04):
  - The pi runtime: The reason for installing the pi runtime becomes ambiguous: "So" now immediately follows the main agent's use of Claude Code, rather than the workers' use of pi with the main agent as a contrast. → fixed
  - Updating an installed Concorde: The preservation condition changes from not having validated successfully to having had no validation. A failed validation keeps the earlier mark, but the rewritten condition can exclude that case. → fixed
  - Updating an installed Concorde: The coordination-part-installed condition no longer explicitly scopes the merge request. The rewrite states that request whenever the Protocol copy changed, including when the coordination part is absent. → fixed
- `specs/concorde/distribution/module.md` (part 05):
  - Refusals: The object forwarded changes from the emitted error-chain link to "the refusal". This potentially obscures whether the caller must forward the structured link itself. → fixed
  - After installing: Potential scope change: the original places both command descriptions within the sentence conditioned on the spec part being installed. The rewritten command descriptions are independent sentences without that explicit c → fixed
  - Why the parts reach Distribution only through registrations: The original hypothetical concerns imports made for the three stated purposes. The rewrite broadens the hypothetical to any imports of each part and adds a claim that those imports would necessarily serve those purposes. → fixed
  - Why the parts reach Distribution only through registrations: The rewrite adds a direct causal inference from parts describing themselves as plain data to Distribution loading only installed-part registrations. The original presents both choices together as consequences of the prec → fixed
- `specs/concorde/distribution/module.md` (part 06):
  - Around it: Potential scope change: the refusal condition now explicitly governs only leaving the Specs to spec-validation; install success and carrying Spec core's error are separate assertions that could be read as unconditional. → fixed
  - Around it: The installed-spec-part condition no longer explicitly scopes calling install.prepare or refusing with invalid_docsite_template; those statements now stand independently. → fixed
  - Around it: Potential reference change: "This" can refer only to the immediately preceding refusal, making that refusal alone ensure template availability rather than the combined inventory-based shipping and rejection behavior. → fixed
  - Around it: The rewrite explicitly assigns run discovery to the idle check; the original leaves the discovery actor unnamed. → fixed
  - Around it: The rewrite assigns the refusal to the installer; the original states the refusal passively without naming its actor. → fixed
- `specs/concorde/distribution/module.md` (part 07):
  - Inside: The stated causal explanation now attaches only to declaring the audience, rather than to including prompts and declaring the audience together. → fixed
  - Inside: The exit statement is no longer explicitly within the envelope-registration condition. Its scope and the antecedent of "its" become ambiguous for non-envelope commands. → fixed
  - Inside: The recovery commands and prohibition are detached from the failed-guidance-write consequence. They can now read as unconditional developer behavior rather than recovery instructions for that failure. → fixed
  - Inside: The original explicitly covers everything capable of refusing an install before a program runs. The rewrite covers only the enumerated checks, losing that exhaustive guarantee. → fixed
  - Inside: Possible scope change: the rewrite explicitly applies "on a fresh project" to all three test targets; the original can attach it only to the installed command. The original scope is ambiguous, so this is not a certain me → not real
- `specs/concorde/distribution/requirements.md` (part 00):
  - req.distribution.build-owned-outputs: The first paragraph is no longer a complete sentence specifying the obligation; the permitted paths are moved into later list items. → not real
  - req.distribution.skills-rendered: The first paragraph is no longer a complete sentence specifying the obligation. Required contents move into list items, and the two skills' composition and source move out of the SHALL statement into descriptive paragrap → not real
  - req.distribution.skills-rendered: "That file" becomes ambiguous: the nearest preceding file is now the development prompt source, rather than the generated SKILL.md output. → fixed
  - req.distribution.build-check-read-only: The first paragraph is no longer a complete sentence specifying the prohibition; the prohibited actions move into later list items. → not real
  - req.distribution.prompt-includes: The first paragraph is no longer a complete sentence specifying the obligation; the expansion target and placeholder substitution move into later list items. → not real
  - req.distribution.safe-includes: The first paragraph is no longer a complete sentence specifying the obligation; all refusal conditions move into later list items. → not real
  - req.distribution.include-audience: The first paragraph is no longer a complete sentence specifying the obligation; the refused cases and audience values move into later list items. → not real
  - req.distribution.include-once: The first paragraph is no longer a complete sentence specifying the obligation. Required diagnostic details move into list items, and the value-independent and include-location scope moves into a later descriptive paragr → not real
  - req.distribution.include-once: An explicit causal relation is added: the original colon presents the two-prompt rule as an explanation or elaboration, without explicitly asserting that non-deduplication causes it. → fixed
  - req.distribution.no-stale-copy: The first paragraph is no longer a complete sentence specifying the obligation; the stale-source and asset-mismatch conditions move into later list items. → not real
  - req.distribution.protocol-manifest-precondition: The first paragraph is no longer a complete sentence specifying the obligation. Both the triggering conditions and the required actions, result and error code move outside that paragraph. → not real
  - req.distribution.one-envelope: The first paragraph is no longer a complete sentence specifying the obligation; its applicability and both exceptions move into later list items. → not real
  - req.distribution.update-installed-parts: The first paragraph is no longer a complete sentence specifying the obligation; all three categories of required parts move into later list items. → not real
  - req.distribution.registration-only: The first paragraph is no longer a complete sentence specifying the obligation; the five actions governed by the registration-only restriction move into later list items. → not real
  - req.distribution.composed-from-registrations: The first paragraph is no longer a complete sentence specifying the obligation; both obligated actors and their exact offerings move into later list items. → not real
  - req.distribution.absent-part-named: The first paragraph is no longer a complete sentence specifying the obligation; the required refusal information moves into later list items. → not real
  - req.distribution.absent-part-named: After the split, "This" can refer to exiting with status 1 rather than to the printed refusal, making the identification of the absence signal ambiguous. → fixed
  - req.distribution.composed-guidance: The installer is introduced as the obligated actor; the original specifies the required state of the installed guidance without assigning its composition to that actor. → fixed
  - req.distribution.composed-guidance: The first paragraph is no longer a complete sentence specifying the obligation. Required contents move into list items, and the exclusion of absent parts moves into a separate second SHALL statement. → fixed
  - req.distribution.guidance-absent-parts: The first paragraph is no longer a complete sentence specifying the obligation; the identification of the obligated sections moves into later list items. → not real
  - req.distribution.glossary-import: The first paragraph is no longer a complete sentence specifying the obligation; the imported glossary and the no-glossary case move into later list items. → not real
  - req.distribution.receipt-complete: The first paragraph is no longer a complete sentence specifying the obligation; the receipt keys, completeness requirements and earlier-default inclusion move into later list items. → not real
  - req.distribution.installer-own-permissions: The first paragraph is no longer a complete sentence specifying the obligation; the only permitted modifications and their qualifying conditions move into later list items. → not real
- `specs/concorde/distribution/requirements.md` (part 01):
  - req.distribution.installer-project-mcp — The installer registers the project MCP server: The required server name and invocation move out of the first-paragraph SHALL statement into a later list; the first paragraph is no longer a complete sentence. → not real
  - req.distribution.own-python — Concorde runs in its own Python environment: Ignoring the caller's settings and user site-packages moves out of the SHALL obligation into a descriptive paragraph. → fixed
  - req.distribution.busy-named — A busy refusal names what runs: The Concorde-specific identification of every running run moves out of the SHALL statement into a descriptive paragraph. → fixed
  - req.distribution.installer-error-links — Installer refusals are error links: Naming the refusal's code and problem moves out of the SHALL obligation into a descriptive paragraph. → fixed
  - req.distribution.installer-error-links — Installer refusals are error links: The rewrite assigns printing to the installer and update command; the original leaves the printing actor unspecified. Also, "every refusal" no longer explicitly limits the refusals to those of these two actors. → fixed
  - req.distribution.installer-no-specs — The installer writes no Spec but its installation realization: The prohibited actions, protected items and exceptions move outside the first-paragraph SHALL NOT statement into subsequent lists; the first paragraph is no longer a complete sentence. → not real
  - req.distribution.installer-keeps-installation-bound — Installed files stay bound: The required binding outcome, its file-selection conditions and its coverage of installation before or after initialization move out of the SHALL obligation into descriptive paragraphs and a list. → fixed
  - req.distribution.installer-keeps-installation-bound — Installed files stay bound: The rewrite explicitly assigns addition and removal to Spec core. The original calls the binding Spec core's but leaves the actor performing these operations unspecified. → fixed
  - req.distribution.update-unvalidated — An update marks the project Concorde unvalidated: The original makes non-marking a consequence of the mark being cleared by spec-validation, with absent validation as supporting context. The rewrite makes absent validation alone the explicit reason, disconnecting the cl → fixed
  - req.distribution.update-mark-kept — An earlier mark is kept until replaced: The required values move outside the first-paragraph SHALL statement into a list; the first paragraph is no longer a complete sentence. → not real
  - req.distribution.installer-fresh-guidance — Only a fresh build is installed: The refusal conditions move outside the first-paragraph SHALL statement into a list, leaving its conditional reference unresolved within that paragraph; the first paragraph is no longer a complete sentence. → not real
  - req.distribution.installer-d2-first — The d2 archive is checked before anything is written: Fetching and checking the pinned archive move outside the first-paragraph SHALL statement into a list; the first paragraph is no longer a complete sentence. → not real
  - req.distribution.installer-programs-first — Missing programs refuse before anything is written: The missing-program conditions and the pi-runtime qualifications move outside the first-paragraph SHALL statement into lists; the first paragraph is no longer a complete sentence. → not real
  - req.distribution.locked-python-dependencies — Only the locked Python dependencies are installed: The required export command, output path and hash-enforcing installation command move out of the SHALL obligation into a descriptive paragraph and list. → fixed
  - req.distribution.installer-docsite-template — The installer ships the docsite template: The selection authority, selection source and mandatory inclusion of `scaffold/` move out of the SHALL obligation into descriptive paragraphs; "selected" is not defined within the obligation itself. → fixed
  - req.distribution.installer-docsite-template-first — An unsafe docsite template installs nothing: Both refusal conditions move outside the first-paragraph SHALL statement into a list; the first paragraph is no longer a complete sentence. → not real
- `specs/concorde/distribution/requirements.md` (part 02):
  - req.distribution.mcp-current-code — Every call answers with the current Concorde: The worktree-selection and arrival-time criteria move out of the SHALL sentence into a later descriptive paragraph, although that sentence explicitly refers to the description. → not real
  - req.distribution.mcp-current-serving — A call is served as the current code registers its tool: The worktree, hand-over, threading and session-worktree obligations move into list items outside the SHALL sentence. The requirement to follow current registration despite a contrary last listing moves into a later descr → not real
  - req.distribution.mcp-tools-changed — The session hears that its tools changed: The exclusion that determines which listing triggers the notification obligation moves out of the SHALL sentence into a later descriptive paragraph. → not real
  - req.distribution.mcp-tools-listed-current — The server lists the current code's tools: Possible timing ambiguity: arrival originally fixes which Concorde supplies the tools; the rewritten arrival condition governs answering, without explicitly fixing the code-selection time. It could be read as selecting t → fixed
  - req.distribution.mcp-channel-override — The environment may decide the channel: Both value-specific classification obligations move out of the SHALL sentence into descriptive list items. → not real
  - req.distribution.mcp-call-failed — A call without an answer is refused: The required command and output-tail contents of the refusal link move out of the SHALL sentence into a later descriptive paragraph. → not real
  - req.distribution.mcp-call-failed — A call without an answer is refused: Possible condition-scope ambiguity: removing the commas permits "without an answer" to modify only "exceeds its time", potentially requiring refusal whenever a process ends, even with an answer. → fixed
- `specs/concorde/distribution/scenarios.md` (part 00):
  - scenario.distribution.composed-guidance — Compose the guidance of a set of parts: Exact composition is weakened to a starting section and relative order; additional content, including extra content from the given parts, is no longer excluded. → fixed
  - scenario.distribution.composed-guidance — Compose the guidance of a set of parts: Exact composition is weakened to a starting section and relative order; additional content from the given parts is no longer excluded. → fixed
  - scenario.distribution.build-workflows — Render every workflow for Claude Code: After the split, "it" can refer to the procedure rather than the generated JavaScript file; the subject of the uniqueness claim becomes ambiguous. → fixed
  - scenario.distribution.protocol-manifest-single-flag — Write or bind alone: Possible scope change: naming the changed assets and preserving the binding are no longer explicitly inside the condition that the second command is run. The scenario sequence may preserve that reading, but the condition → fixed
  - scenario.distribution.part-missing — A command or tool of a part not installed names the part: Possible scope change: the rewrite explicitly excludes `issue_list` from the "for a run" qualifier, whereas the original qualifier could apply to the whole tool list. → fixed
- `specs/concorde/distribution/scenarios.md` (part 01):
  - scenario.distribution.update-adds-programs — An update places what an added part needs: Drops the explicit causal connection between having only the coordination part installed and having neither dependency. The rewrite instead states the project's lack of need as the reason for their absence. → fixed
  - scenario.distribution.install-docsite-template-refused — An unsafe docsite template installs nothing: Changes the grammatical owner of reason `input` from the link to the refusal. The original may have intended the refusal's reason, but that interpretation is uncertain; the rewrite resolves the reference differently. → fixed
- `specs/concorde/distribution/scenarios.md` (part 03):
  - scenario.distribution.install-later-files-bound — Files a later install adds stay bound: Possible scope and reference ambiguity: the original tests other bindings separately for each file; the rewrite puts the condition before the quantified files and uses "its" before identifying its referent, making it les → fixed
- `specs/concorde/issues/interface.md` (part 00):
  - Provenance: Possible narrowing: the original explicitly includes reporting on both together; "either" presents alternatives and makes coverage of the combined case ambiguous. → fixed
- `specs/concorde/issues/interface.md` (part 01):
  - Record file: The rewrite scopes the placement guarantee to handling misplaced records; the original states it for every write. → fixed
  - Record file: The caller-supplied exception no longer explicitly covers the ISO 8601 representation. The separate sentence may require caller-supplied times to be ISO 8601 too; this scope change is potentially ambiguous. → fixed
- `specs/concorde/issues/interface.md` (part 02):
  - Store operations: The antecedent of "other" becomes ambiguous after the split: the primary worktree is no longer the immediately preceding reference, so "other root" could be read relative to the outside-repository case instead. → fixed
  - Store operations: The recovery_failed condition is narrowed, or at least becomes ambiguous: the original refers to the entire rollback, including removing a new record from the index and directory and restoring the record removed from the → fixed
  - Store operations: Publication from the other path becomes a separate, unqualified claim. Originally it applies only to the fallback case where HEAD holds no record at the entry's own path. → fixed
  - Store operations: The original tests whether HEAD holds the entry at the path being restored; the rewrite tests whether HEAD holds the record, without specifying the path. Because the committed record may instead be at the Issue's other p → fixed
- `specs/concorde/issues/interface.md` (part 03):
  - Bookkeeping command: The original explicitly makes both matching output and matching refusal links consequences of calling the actions with the same arguments. The rewrite retains that explicit causal relation only for matching output and ma → fixed
- `specs/concorde/issues/module.md` (part 00):
  - Issues and their reports: The list's "Its" now ambiguously refers to the report rather than the problem. The original ties these attributes to the problem being stated completely. → fixed
  - Issue revisions: The rewrite assigns the refusal to the command, an actor the original passive statement does not specify. → fixed
  - Structure: The split makes "Each" refer to the command and store, leaving "its owner" ambiguous between the reader's owner and the registry's or task records' owner. The original associates the defining Spec with the owner of the f → fixed
- `specs/concorde/issues/module.md` (part 01):
  - Where Issues are kept: Possible weakening: presenting holding the lock as a separate step makes it ambiguous whether the lock must remain held during publication and commitment, as the original requires. → fixed
  - Where Issues are kept: The explicit consequence relation now covers only project versioning; acknowledged records being committed becomes a separate claim. → fixed
  - Failures of the Issue system: The session's waiting forever is no longer explicitly given as a second reason for never reporting the failure as an Issue; it becomes an additional standalone claim. → fixed
- `specs/concorde/issues/module.md` (part 02):
  - Sessions and Issues: The original identifies the session as either the main agent or a task session. The rewrite lists an unqualified session as a separate actor alongside those two, potentially extending tool use to other sessions. → fixed
  - Recording and following up: Possible scope narrowing: "this check" explicitly confines non-resolution to `report --check`; the original statement can also cover checking during report recording. This difference is uncertain because the original's p → not real
- `specs/concorde/issues/module.md` (part 03):
  - Around it: Returning the answer or refusal unchanged is now a separate behavioral claim, no longer explicitly part of what Issues relies on. → fixed
  - Around it: The rewrite specifically requires the merge itself to hold the lock; the original allows holding it or relying on its caller holding it. → fixed
  - Around it: A description restricted to reports that undergo this check becomes a claim that every report with an `origin` undergoes the check before handoff. → fixed
- `specs/concorde/issues/module.md` (part 04):
  - Inside: The temporal qualifier originally selects refusals occurring before publication. Fronting it makes its scope ambiguous: it can instead limit when the record-preservation statement holds. → fixed
  - Inside: Passing store errors unchanged is detached from the model-understanding rationale and from its explicit association with refusals; it becomes a separate claim. → fixed
- `specs/concorde/issues/requirements.md` (part 00):
  - req.issues.caller-provenance — Provenance comes from the command: The first paragraph is no longer a complete requirement sentence. The supply obligation, its exception and the prohibition are moved into later list items. → not real
  - req.issues.main-agent-actor — The command attributes Issue writes to the session: The first paragraph is no longer a complete requirement sentence. The report and disposition scopes, attribution values and calling-context conditions are moved into later list items. → not real
  - req.issues.report-owner-registered — A report names a registered owner: The first paragraph is no longer a complete requirement sentence. All three refusal conditions are moved into later list items. → not real
  - req.issues.report-evidence-present — A report's evidence exists: The first paragraph is no longer a complete requirement sentence. The provenance and missing-evidence conditions are moved into later list items. → not real
  - req.issues.report-evidence-present — A report's evidence exists: The explicit requirement that the missing evidence path belong to the report being refused is lost. The list context suggests that relationship, but no longer states it. → fixed
  - req.issues.tier-required — Every report carries a tier: The first paragraph is no longer a complete requirement sentence. The exhaustive permitted tier values are moved into later list items. → not real
  - req.issues.severity-required — Every report carries a severity: The first paragraph is no longer a complete requirement sentence. The exhaustive permitted severity values are moved into later list items. → not real
  - req.issues.own-failures — The Issue system never reports itself: The first paragraph is no longer a complete requirement sentence. Both required statements about the error chain are moved into later list items. → not real
  - req.issues.specific-refusals — Refusals name what is wrong: The first paragraph is no longer a complete requirement sentence. The kinds of item the message must name are moved into later list items. → not real
  - req.issues.store-writes — Only the store writes Issue records: The first paragraph is no longer a complete requirement sentence. The three kinds of write covered by the obligation are moved into later list items. → not real
  - req.issues.project-level — The primary worktree keeps the project's Issues: "That action" has an ambiguous antecedent: it can refer to the immediately preceding reading and writing rather than to `check`. The original explicitly assigns the checking behavior to `check`. → fixed
  - req.issues.status-folder — A record lies in the folder of its status: The first paragraph is no longer a complete requirement sentence. Both required paths and the movement and commit obligations are moved into later list items. → not real
  - req.issues.status-folder — A record lies in the folder of its status: The rewritten "there" can refer to the immediately preceding wrong folder, rather than the folder required by the Issue's status. The destination becomes ambiguous. → fixed
  - req.issues.archive — Misplaced records are moved into their folder: The first paragraph is no longer a complete requirement sentence. The destination, preservation requirement, single-commit requirement and merge-lock requirement are moved into later list items. → not real
  - req.issues.archive-reported — Archive names what it moved and left: The first paragraph is no longer a complete requirement sentence. The records to name and their required paths or reasons are moved into later list items. → not real
  - req.issues.list-filtered — A listing reads only the Issues asked for: The first paragraph is no longer a complete requirement sentence. The required meanings of all four filters are moved into later list items. → not real
- `specs/concorde/issues/requirements.md` (part 01):
  - req.issues.list-by-severity — A listing can start from the most severe Issues: The first paragraph is no longer one complete sentence with exactly one SHALL. The actual ordering rules have moved out of the requirement statement into separate list items. → not real
  - req.issues.uncommitted-recovered — Uncommitted records are put back before any write: The first paragraph is no longer one complete sentence with exactly one SHALL. Restoration or removal, locking, and the prohibition on committing have moved out of that statement into separate list items. → not real
  - req.issues.no-write-during-merge — No Issue write while a merge is unfinished: The explicit coverage of both lock-ownership cases has moved from the SHALL statement into a later descriptive paragraph. → fixed
  - req.issues.no-write-during-merge — No Issue write while a merge is unfinished: The excluded code source changes from the coordination part's code to Tasks' code. This narrows the prohibition and no longer explicitly excludes other code of the coordination part. → fixed
  - req.issues.own-check — Issues checks its own records: The original requires validation of Issue records and restricts who performs it. The rewrite states exclusivity without explicitly requiring that the records be validated. → fixed
  - req.issues.own-check — Issues checks its own records: The named command and tool, and their execution by the configured check, have moved from the SHALL statement into later descriptive paragraphs. → fixed
  - req.issues.own-check — Issues checks its own records: The rewrite introduces an ambiguous "it": it may refer to the configured check, but the preceding sentence names Spec tooling and concorde spec-validation. The original passive statement does not introduce this actor amb → fixed
  - req.issues.commit-alone — An Issue commit commits its record alone: Inclusion of the old path after a move has moved from the SHALL statement into a later descriptive paragraph. → fixed
  - req.issues.commit-alone — An Issue commit commits its record alone: The archive obligation has moved out of the requirement's first paragraph into a second SHALL statement in a later paragraph. → fixed
  - req.issues.legal-transitions — Dispositions alternate: The rewrite makes the listed cases exhaustive for all dispositions, whereas the original constrains closing dispositions and reopenings specifically. The first paragraph is also no longer one complete sentence with exact → fixed
- `specs/concorde/issues/scenarios.md` (part 00):
  - Issues scenarios: Possible scope change: the separate statements no longer explicitly restrict these valid-argument defaults to arguments the scenario does not name; they can be read as applying even to explicitly supplied arguments. → fixed
  - scenario.issues.command-report-provenance — An Operation records a report with its own provenance: The split introduces repeated references to the provenance file immediately before "that file", making the report-file reference more ambiguous; it can now appear to instruct passing the provenance file to `--file`. → fixed
  - scenario.issues.command-unreadable-task-record — A task record that cannot be read refuses the write: An instruction to carry the error chain in any of three alternative destinations becomes an instruction to use the decision log, with escalation and the run result merely permitted separately. → fixed
- `specs/concorde/issues/scenarios.md` (part 01):
  - scenario.issues.command-usage: Possible logical ambiguity: the original gives alternative invalid-input cases; the rewrite joins them with AND while calling them alternatives, leaving unclear whether any one case suffices. → fixed
  - scenario.issues.command-usage: The original concerns arguments to `list`; the rewrite describes properties of the listing, potentially shifting these invalid-input cases to output properties. → fixed
  - scenario.issues.command-unknown-issue: Possible logical ambiguity: alternative invocations become AND-connected steps, leaving unclear whether each invocation independently triggers the refusal or multiple invocations are required. → fixed
  - scenario.issues.command-write-failed: Possible narrowing: the original's "it" can refer to the write error, whereas the rewrite explicitly prohibits reporting the error chain, potentially leaving reporting the underlying failure itself outside the prohibitio → fixed
  - scenario.issues.command-write-raced: Possible change from a file specifying an append to an append occurring as a GIVEN event before the command runs; the rewrite also makes the file itself the actor performing the append. → fixed
  - scenario.issues.command-list-filtered: Possible scope ambiguity: the row-severity assertion originally modifies the `--sort severity` listing; as a separate step, it can now be read as applying to every listing in the scenario. → fixed
- `specs/concorde/issues/scenarios.md` (part 02):
  - scenario.issues.command-commit-failed — A failed commit is an Issue-system failure, never an Issue: The instruction to carry the error chain in one of these destinations is weakened to identifying possible destinations; the options no longer have to tell the agent to carry it there. → fixed
  - scenario.issues.command-recovery-failed — A record that could not be put back is an Issue-system failure: The instruction to carry the error chain in one of these destinations is weakened to identifying possible destinations; the options no longer have to tell the agent to carry it there. → fixed
- `specs/concorde/issues/scenarios.md` (part 03):
  - scenario.issues.store-boundary: Possibly ambiguous: the original clearly gives three alternative defects; AND steps can make the unknown type a continuing prerequisite despite "alternatively". → fixed
  - scenario.issues.store-report-inconsistent: Possibly ambiguous: the original clearly gives three alternative defects, all subject to satisfying the report schema; the rewrite can make the subtype mismatch a prerequisite for the other cases. → fixed
  - scenario.issues.store-corrupted-record: The split attaches the causal "so" directly to committing the edit rather than to the report being edited and the edit committed, potentially implying that committing causes the content mismatch. → fixed
  - scenario.issues.store-publication-stale: Possibly ambiguous: the original clearly gives alternative operations; AND steps can make creation a prerequisite or preceding operation for append and disposition despite "alternatively". → fixed
  - scenario.issues.store-folders: The explicit `closed/` location now applies only to reads; the separate assertions for `list` and the located path no longer specify that location. → fixed
  - scenario.issues.store-interrupted-move: The original specifies that the deleted record has no other-folder copy and gives both outcomes for that case. The rewrite makes absence of a copy a condition only of leaving the record; the separate refusal step is no l → fixed
- `specs/concorde/issues/scenarios.md` (part 04):
  - scenario.issues.store-check-invalid — The store check fails for an invalid record: Potential meaning ambiguity: the original gives three alternative cases; separate AND preconditions can require all three together, conflicting with "alternatively" and making the scenario's setup unclear. → fixed
- `specs/concorde/kernel/contracts.md` (part 00):
  - Workspace binding: The explicit reason for refusing a binding whose root names the wrong worktree is lost; the copied-binding consequence becomes a separate claim. → fixed
  - Typed values: Possible strengthening: an already-satisfied loading prerequisite becomes an explicit instruction to load the code before checking, which could be read as requiring a loading action even when the code is already loaded. → fixed
  - Typed values: "That type" becomes ambiguous between `example-batch`, now explicitly called "The type" in the preceding sentence, and the embedded `concorde-run-trace` type whose missing registration causes the original failure. → fixed
  - Typed values: The explicit reason for caller selection of the root is lost; the caller's exclusive knowledge becomes a separate claim. → fixed
- `specs/concorde/kernel/contracts.md` (part 01):
  - Registered schemas: Possible reference ambiguity: "it" can refer to the number rather than the JSON text. The original explicitly identifies the JSON text as invalid (`invalid_json`). → no verdict
- `specs/concorde/kernel/contracts.md` (part 02):
  - Library: The explicit causal relation introduced by "since" is lost: the caller's responsibility is now a separate claim rather than the stated reason the operation never writes an error link. → fixed
- `specs/concorde/kernel/module.md` (part 00):
  - Purpose: The actor restricting the allowed path changes from the part calling the transaction to the transaction itself. → fixed
  - The workspace: The explanatory relation is lost: another preparer's freedom to choose the folder is now a separate claim rather than the explanation for parts not knowing it as a task folder. → fixed
  - The workspace: The explicit reason for refusing the binding is lost and becomes a separate claim. → fixed
  - The workspace: The explicit reason for excluding historical and delivery facts from the binding is lost and becomes a separate claim. → fixed
  - Marks and locks of the primary branch: Possible weakening: the original states the criterion used to judge delivery; the rewrite states a sufficient condition without explicitly retaining that criterion as the basis of the judgment. → fixed
  - Marks and locks of the primary branch: The explicit explanatory connection between automatic operating-system release and sessions not needing to release or announce completion is lost. → fixed
- `specs/concorde/kernel/module.md` (part 01):
  - Overview: Possible strengthening: the original limits what parts reach through the Kernel; the rewrite's unqualified "rely only" can exclude reliance on anything besides that convention. → fixed
  - Why a kernel at all: The explicit explanatory relationship between the independent-operation requirement and the two project use cases is lost; the use cases become separate claims. → fixed
  - Why a kernel at all: The claim that shared placement preserves separate installability no longer includes the shared part's lack of behaviour as a qualification; that property becomes a separate claim. → fixed
- `specs/concorde/kernel/requirements.md` (part 00):
  - req.kernel.registration-stable — A registration never changes: Keeping the existing registration in force is separated from the SHALL requirement into a declarative statement, losing its explicit SHALL scope. → fixed
  - req.kernel.transaction-restored — A failed transaction restores what it wrote: The alternative restoration/removal actions become conjunctive obligations. Literally, the rewrite requires attempting restoration even for created files, as well as removing them. → fixed
  - req.kernel.refusals-coded — Every refusal carries a stable code: The original requires the details to be carried by the refusal itself. The rewrite requires providing them for the refusal but does not explicitly require attaching them to it. → fixed
  - req.kernel.refusals-coded — Every refusal carries a stable code: The whole-input emptiness requirement is separated from the SHALL requirement into a declarative statement, losing its explicit SHALL scope. → fixed
- `specs/concorde/kernel/scenarios.md` (part 00):
  - scenario.kernel.transaction-unrestored — A refused restoration is named: The ordered causes are now attributed to the transaction rather than to the `system_error` failure, changing which object must carry the causes. → fixed
- `specs/concorde/kernel/tracing/contracts.md` (part 01):
  - Writing a node: The explicit causal relation between atomic replacement and never reading half a record is lost; the consequence becomes a separate claim. → fixed
  - Writing a node: Possible scope change: the original can require both folder creation and folder naming before process startup; the rewrite explicitly applies that deadline only to naming, allowing creation after startup but before the f → fixed
  - Trace roots: The possessive reference becomes ambiguous after the split: "Its" can now refer to the registration rather than the trace root. The same ambiguity affects "its top nodes," "its folders," and the retention periods "that a → fixed
  - Trace roots: Moving the naming modifier makes its attachment ambiguous: it can now describe the node rather than the lock, obscuring the requirement that the lock be named after a top node's identity. → fixed
- `specs/concorde/kernel/tracing/contracts.md` (part 02):
  - Locks: The explicit reason for using both device and inode is lost; the filesystem-local uniqueness of inode numbers becomes a separate claim. → fixed
  - Locks: Possible scope narrowing: the rewrite explicitly applies "from any PID namespace" only to reading the lock table, whereas the original can apply it to both observation methods. → fixed
- `specs/concorde/kernel/tracing/contracts.md` (part 04):
  - Error link: Possible reference change: "the actor" can refer to the previously named top-link writer rather than the actor responsible for each link, making inability to handle every link's causes a property of the top-link writer. → fixed
- `specs/concorde/kernel/tracing/module.md` (part 00):
  - Purpose: Possible referent change: the rewrite explicitly makes each tree the retention unit, whereas the original's "each" could refer to each trace root. → fixed
  - Trace roots: The exception changes from a specific actor's specific finishing action to the answer itself being exempt from immutability. This can permit other changes to that answer, which the original does not permit. → fixed
  - Trace roots: The rewrite drops the explicit identification of the attempt as belonging to the merge that closed the task, leaving which attempt is meant less explicit. → fixed
- `specs/concorde/kernel/tracing/module.md` (part 01):
  - What a node records: Potential meaning change: the rewrite makes the finer outcome part of the status itself, whereas the original only says it accompanies the status. → fixed
  - What a node records: The original specifies how each artifact is recorded or referenced. The rewrite instead describes what each file has, making the requirement to record both its relative path and digest less explicit. → fixed
  - What a node records: The rewrite explicitly assigns the read to Concorde; the original leaves the reader unnamed. → fixed
  - What a node records: Potential scope change: writing the figures is no longer grammatically part of finishing the node when the task ends. The separate statement leaves its timing less explicit. → fixed
  - Locks are not records: "These" now ambiguously refers to the immediately preceding parts rather than to the locks, potentially classifying the two locks as parts. → fixed
- `specs/concorde/kernel/tracing/module.md` (part 02):
  - Nested by the parent, referenced among peers: The explicit causal relation from placement to the absence of a wrong parent identity is lost; that consequence becomes a separate claim. → fixed
  - Why errors travel as a chain: An assertion that every receiver decides from the received information is weakened to an assertion that the mechanism enables it to do so. → fixed
  - Its realizations: The explicit association of handoff and non-polling waiting with the locks under `.concorde/locks/` is removed. These become independent capabilities; whether this broadens their intended scope is uncertain. → fixed
- `specs/concorde/kernel/tracing/requirements.md` (part 00):
  - req.tracing.node-contract — Every node follows the node contract: A constraint on every record becomes a writing obligation assigned to the trace node, which the glossary defines as a folder. The content-type constraint moves out of the SHALL sentence, and the first paragraph now conta → fixed
  - req.tracing.written-at-start — A node exists from its start: The first paragraph now contains two sentences and two SHALLs instead of one sentence with one SHALL. → fixed
  - req.tracing.written-at-start — A node exists from its start: The explicit consequence relation no longer grammatically includes preservation of the start time; that becomes a separate claim. → fixed
  - req.tracing.reported-usage — Usage is what the agent program reported: The first paragraph is an incomplete lead-in rather than a self-contained requirement sentence; the required figures, null rule and prohibition appear only in the subsequent list. → not real
  - req.tracing.relative-paths — A trace refers to its files and nodes relatively: The first paragraph now contains two sentences and two SHALLs instead of one sentence with one SHALL. → fixed
  - req.tracing.relative-paths — A trace refers to its files and nodes relatively: Potential strengthening: the original constrains how a link or claim is retained if the node keeps it; the rewrite can assert that a node keeps such a link or claim at all. → fixed
  - req.tracing.relative-paths — A trace refers to its files and nodes relatively: Potential narrowing: "them" can refer to the retained error link or worker claim as a whole, whereas the rewrite explicitly prohibits dependence only on their paths. → fixed
  - req.tracing.created-or-found — A reference tells what the node created from what it found: The first paragraph now contains two sentences and two SHALLs instead of one sentence with one SHALL. → fixed
  - req.tracing.created-or-found — A reference tells what the node created from what it found: The explicit consequence relation no longer grammatically includes reaching the existing work; that becomes a separate claim. → fixed
  - req.tracing.no-credentials — Credentials are never retained: The first paragraph no longer identifies the constrained objects in a complete requirement sentence; those objects appear only in the subsequent list. → not real
  - req.tracing.nested-by-parent — A child lies inside its parent: A folder-location constraint becomes an active keeping obligation assigned to the trace node, itself defined as a folder. The first paragraph also leaves its exceptions to the subsequent list rather than forming a comple → fixed
  - req.tracing.nested-by-parent — A child lies inside its parent: The requirement that the location be chosen before the child starts moves out of the SHALL statement into a later descriptive paragraph. → fixed
  - req.tracing.downward-only — The nodes of a workspace never name a task: The first paragraph is no longer a complete requirement sentence; the prohibited objects appear only in the subsequent list. → not real
  - req.tracing.roots-registered — Only registered roots are searched and pruned: The first paragraph no longer states the required operations in a complete sentence; search, list and prune appear only in the subsequent list. → not real
  - req.tracing.holder-named — A holder line names the session and the task: The first paragraph no longer states the required contents or their conditions in a complete sentence; they appear only in the subsequent list. → not real
  - req.tracing.lock-handed-on — A handed lock lives as long as its receiver: The first paragraph now contains two sentences and two SHALLs instead of one sentence with one SHALL. → fixed
  - req.tracing.history-unchanged — A closed root is not changed: The first paragraph now contains three sentences. The limitation on retention moves out of the single requirement sentence into a separate descriptive sentence. → fixed
  - req.tracing.conversations-shorter — Conversation records have their own retention: The first paragraph now contains three sentences and two SHALLs instead of one sentence with one SHALL. → fixed
  - req.tracing.retention-explicit — Traces are removed only at defined points: A restriction on permitted removal mechanisms becomes a positive removal obligation assigned to those mechanisms, without specifying a trigger. The first paragraph also leaves their identities to the subsequent list rath → fixed
  - req.tracing.reader-read-only — Reading changes nothing: The first paragraph no longer identifies the prohibited actions in a complete requirement sentence; they appear only in the subsequent list. → not real
  - req.tracing.error-in-band — An error chain stays whole where it is reported: The first paragraph no longer identifies the obligated objects in a complete requirement sentence; they appear only in the subsequent list. → not real
- `specs/concorde/kernel/tracing/scenarios.md` (part 00):
  - scenario.tracing.show-task — A task's trace with its cost rolled up: The rewrite fixes the parent as the workspace; the original "it" could refer to the task's node. This may change the stated hierarchy, although the glossary supports the workspace interpretation. → fixed
  - scenario.tracing.show-by-identity — A run is found by its identity: The separate assertions can require showing both standalone runs regardless of which identity was supplied. The original can instead mean that each is shown independently when its own identity is supplied; the rewrite ma → fixed
  - scenario.tracing.lost-run — A run whose runner died is lost: Splitting the setup leaves the run lock as the nearest noun before "it", making the reference to the run less clear. → not real
  - scenario.tracing.kind-registered — A node is checked against the registration of its kind: An illustrative registered kind becomes a required member of the scenario's registered kinds. → fixed
  - scenario.tracing.kind-registered — A node is checked against the registration of its kind: Three alternative invalid-write cases become a conjunctive setup requiring all three writes, weakening coverage of each case occurring alone. → fixed
  - scenario.tracing.lock-holder-line — The holder line names the session and the task: The grammatical subject changes from the process to its environment, making "it" ambiguous between the process and the environment as the lock-taking actor. → fixed
- `prompts/guidance/distribution/skill.md` (part 00):
  - Installed parts and updates: Possible referent change: the original's "its result" can refer to `concorde spec-validation`; the rewrite explicitly assigns the task listing to the update. This changes meaning if validation was the intended referent. → fixed
- `prompts/guidance/issues/skill.md` (part 00):
  - Recording: The prohibition originally limits the duplicate-checking read before recording a problem. The standalone prohibition now reads as an unconditional ban on reading the whole project's list. → fixed
  - Fixing: The installation condition explicitly governs both opening the task and naming its Issues in the original. After the split, the naming instruction is no longer explicitly conditional on the coordination part being instal → fixed
  - Fixing: The installation condition originally covers the review's reporting, assigned severity and tier, result lists, and subsequent session handling. The split explicitly conditions only reporting findings; the remaining state → fixed
  - When the Issue system fails: "In that case" can refer specifically to the project-discussion example rather than every failure encountered without a task, potentially narrowing the obligation to show the developer the whole error chain. → fixed
  - When the Issue system fails: The original explicitly conditions both registering the wait and retrying after release on the coordination part being installed. The retry sentence loses that explicit condition, potentially extending the release-depend → fixed
  - When the Issue system fails: The original parenthetical clearly refers to the recover command. After the split, "It" could refer to either the command or the newly mentioned record, making the reference ambiguous. → fixed
- `prompts/guidance/issues/task-session.md` (part 00):
  - Issues / After a review: The installation condition now qualifies only the reporting sentence; the Issue classification and result-content claims are separate, unqualified statements. → fixed
  - Issues / After a review: "Those" restricts the resolved set to earlier Issues in the original. The rewrite drops that restriction and describes all Issues the review found resolved. → fixed
- `specs/concorde/workflows/contracts.md` (part 03):
  - The script's result: The rewrite retains the stopping behavior but loses the explicit explanatory relation between the report's inability to see the run and the procedure stopping, reporting the key as lost and returning the rejected outcome → fixed
  - Starting a workflow step: The original's "so" explains both the detached run's separate process and its lifetime independent of the calls, session and server. After the split, it explains only the separate process; the lifetime guarantee becomes  → fixed
- `specs/concorde/workflows/module.md` (part 00):
  - Workflows and their modes: Nesting the failure case under "any step that needs them" limits failure-triggered stopping to steps needing decision points; the original stops after any non-`ok` step. → fixed
  - Workflows and their modes: The new standalone "It" has an ambiguous reference: it can refer to the workflow instead of whoever started it, obscuring who restarts the workflow. → fixed
  - Steps and their keys: The explicit causal relation between supersession and treating earlier validation or delivery as noncurrent is lost; that consequence becomes a separate claim. → fixed
- `specs/concorde/workflows/module.md` (part 01):
  - The record and the result: The original makes `failed` with `incomplete` the fallback whenever no earlier status applies. The rewrite explicitly conditions that fallback on two cases, leaving other unmatched cases without a specified status. → fixed
  - The record and the result: The separate sentence loses the current-steps restriction on problems and now includes superseded non-`ok` steps, conflicting with the retained statement that superseded steps contribute nothing else. → fixed
  - Scripts and step agents: Possibly ambiguous after the split: `It` can refer to the script rather than the owning part, making the registration actor unclear. → fixed
  - Scripts and step agents: The original states preservation of the refusal as a consequence. The rewrite states a purpose, without explicitly guaranteeing that the refusal stays in the error chain. → not real
  - Its place in the levels of work: The rewrite drops the explicit relationship that a run completes an Operation's job by combining workers, services and host steps. It instead states independently that an Operation combines them. → fixed
- `specs/concorde/workflows/module.md` (part 02):
  - One step, from the script to a run and back: Possible actor/scope change: grammatically, the original attaches the 100-second waiting limit to the server running the command; the rewrite explicitly limits the step agent's wait and leaves the server's wait unspecifi → fixed
- `specs/concorde/workflows/module.md` (part 03):
  - The step command: The missing-key condition no longer explicitly governs launching the run. The split potentially makes launching unconditional, including when the key already exists. → fixed
  - The step command: Adds the claim that status 3 indicates an existing run is still running. The original also permits status 3 while waiting for a lock with no run. → fixed
  - The step command: Potential condition-scope ambiguity: the separate sentence no longer clearly ties returning the outcome to expiry of the wait bound, and could require returning whenever the lock is held. → fixed
  - A retired workspace: The possessive pronoun potentially refers to the step rather than the error link. The original explicitly assigns the cause to the link. → not real
  - A retired workspace: The original restricts this refusal case to a run that actually started and ended before retirement. The rewrite states that timing as a possibility, leaving "that step" potentially unrestricted by whether its run actual → fixed
  - One procedure, rendered as a Claude Code workflow: "It" can refer to the workflow rather than the act of rendering it. The original unambiguously constrains rendering; the rewrite potentially constrains the workflow itself. → not real
- `specs/concorde/workflows/module.md` (part 04):
  - Steps in Claude Code: The stated reason no longer explicitly applies to immediate replay of finished steps; replay becomes a separate claim. → fixed
  - Steps in Claude Code: The explicit "whatever happened in between" qualification no longer covers the workflow's link being on top. → fixed
  - Inside: The reference of "its code" becomes ambiguous: it can now refer to the catalog rather than the procedure-owning part. → fixed
  - Inside: The rewrite no longer explicitly says the tested run is started inside that namespace; executing inside it does not state where it was started. "One" also becomes ambiguous between a step and a run after the preceding bu → fixed
  - Inside: The original identifies the guidance sections themselves; the rewrite describes subjects those sections cover. It also makes reports explicitly belong to the project skill's and task-session prompt's "Workflows", whereas → fixed
- `specs/concorde/workflows/module.md` (part 05):
  - What Workflows relies on: The original locates recording inside the step's node. In the rewrite, "there" can refer to the immediately preceding workspace instead, making the recording location ambiguous. → fixed
  - What Workflows relies on: The original explicitly makes "it" refer to the run lock. The rewrite places "it" before the lock is introduced, after a sentence about the runner's output, making its reference less clear. → fixed
  - What Workflows relies on: The original assigns a separate process to each tool call. The rewrite makes "its own process" refer to the server and could allow reuse of the server's process across calls, weakening the per-call process separation. → fixed
- `specs/concorde/workflows/requirements.md` (part 00):
  - req.workflows.key-idempotent — A step key runs once: The first paragraph is no longer one complete requirement sentence. The three cases that limit permission to start a run have moved into later list paragraphs. → not real
  - req.workflows.restart-generation — A restart runs a step once more: The first paragraph is no longer one complete requirement sentence. The required consequences, including one new run per label and reuse while the step is current, have moved into later list paragraphs. → not real
  - req.workflows.step-lock — A step is looked up, started and recorded at once: The first paragraph is no longer one complete requirement sentence; all three required actions have moved into later list paragraphs. The fronted condition also potentially weakens the locking obligation: it can be read  → fixed
  - req.workflows.workspace-retired — Nothing is written into a retired workspace: The first paragraph is no longer one complete requirement sentence. Both conditions limiting when writes may begin have moved into later list paragraphs. → not real
  - req.workflows.supersede — A rerun supersedes what came after it: The rewrite names `concorde workflow step` as the responsible actor, whereas the original attaches supersession to starting any such new run without naming an actor. → fixed
  - req.workflows.bounded-wait — A step call waits a bounded time: The first paragraph is no longer one complete requirement sentence. The actual time bound and the limitation of the extra 90 seconds to announcing a run the call starts have moved into later list paragraphs. → not real
  - req.workflows.answers-input — An answered step admits the run that asked: The first paragraph is no longer one complete requirement sentence. The run-selection obligation, supersession exception and prohibition on `--input` without an `ok` run have moved into later list paragraphs. → not real
  - req.workflows.no-task — Workflows knows no task: The first paragraph is no longer one complete requirement sentence. Every prohibited action and its object have moved into later list paragraphs. → not real
  - req.workflows.interactive-stops — Interactive runs stop at decision points: The first paragraph is no longer one complete requirement sentence. Both conditions triggering the required stop have moved into later list paragraphs. → not real
- `specs/concorde/workflows/requirements.md` (part 01):
  - req.workflows.no-ask-describe-continues: Possible new pronoun ambiguity: "It" can refer to the intervening `code_to_spec` step rather than the brownfield workflow, changing who delegates the delivery decision. → fixed
  - req.workflows.report-from-records: The first paragraph is no longer one complete sentence; the required sources are moved into subsequent list items. → not real
  - req.workflows.complete-report: The first paragraph is no longer one complete sentence; all specified report contents and their qualifications are moved into subsequent list items. → not real
  - req.workflows.complete-report: Possible scope change: the repeated "that every ... step declared" can require only items declared by all finished current steps, rather than collecting each step's declared items. → fixed
  - req.workflows.chain-on-top: The first paragraph is no longer one complete sentence; the required level, explanation and causes are moved into subsequent list items. → not real
  - req.workflows.lost-step: The first paragraph is no longer one complete sentence; the cases that must be reported lost are moved into subsequent list items. → not real
  - req.workflows.lost-step: Possible weakening of a definition into necessary characteristics: the rewrite no longer clearly says that the listed observations identify a step still starting whose run never started. → fixed
  - req.workflows.lost-first: The first paragraph is no longer one complete sentence; both required actions and the result's status and workflow identity are moved into subsequent list items. → not real
  - req.workflows.lost-first: Possible referent change: the original "it" can refer to the saved result; the rewrite explicitly selects the workspace. → fixed
  - req.workflows.one-source: The first paragraph is no longer one complete sentence; the things that must remain unchanged are moved into subsequent list items. → not real
  - req.workflows.tool-step-command: The first paragraph is no longer one complete sentence; the required executable, working directory and process provenance are moved into subsequent list items. → not real
  - req.workflows.tool-threads: The rewrite names the project MCP server as the obligated actor where the original uses a passive requirement without naming its actor. → fixed
  - req.workflows.script-repeats: The first paragraph is no longer one complete sentence; the waiting limit, call cap and required resolution outcome are moved into subsequent list items. → not real
  - req.workflows.relay-checked: The first paragraph is no longer one complete sentence; all conditions for accepting an outcome are moved into subsequent list items. → not real
  - req.workflows.relay-asked-again: The first paragraph is no longer one complete sentence; both stopping conditions are moved into subsequent list items. → not real
  - req.workflows.step-agent-relays: Possible scope change: the original prohibits bypassing the grant and audit themselves as well as result handling; the rewrite prohibits bypassing the run's handling of those things. → fixed
- `specs/concorde/workflows/scenarios.md` (part 00):
  - scenario.workflows.step-starts — A step starts and records a run: Possible reference change: the original's "whose" can refer to the workspace folder; the rewrite explicitly assigns the record to the step's node. If the original meant the step's node, there is no meaning change. → fixed
  - scenario.workflows.step-adopted — A run its step command did not record is adopted: Possible reference change: the original's "its outcome" can refer to the adopted run or the step; the rewrite explicitly selects the step's outcome. If the original meant the step's outcome, there is no meaning change. → fixed
- `specs/concorde/workflows/scenarios.md` (part 01):
  - scenario.workflows.reviews-reported — The notes of the runs reach the result: The original places the Module's outcome and blocking-finding count within the review note. The rewrite makes the outcome a separate declaration in the step's output, no longer requiring it to belong to the note or to be → fixed
- Non-`ok` result: `test_guidance_parts` failed after the restyle. Three guidance paragraphs (issues skill: `task merge`, `register_wait`; distribution skill: `concorde spec-validation`) no longer named the part in the same paragraph, as req.distribution.guidance-absent-parts requires, because pi split them. Fixed in a separate commit by naming the part again; the Module tests then pass (172).
- Non-`ok` result: the full pytest had 32 failures, all in `tests/concorde/main_session/test_guidance.py`,
  which asserts exact phrases of the issues and workflows guidance. Every failing phrase was pure
  wording: I replaced each with the restyled sentence that carries the same instruction (two
  assertions became two each, where the restyle split one sentence into two), and dropped no
  instruction. The file belongs to Main session's tests; restyle-coordination may touch it too, so
  a merge conflict there is possible and is wording only. Full suite after: 1253 passed, 5 skipped.

## Report 1 to the main agent (concorde-f8), 2026-10-04T11:01:53Z

restyle-kernel delivered: 564d65da on concorde/restyle-kernel.

Commits: 680ab945 Kernel+Tracing+kernel guidance, 01a7094e Distribution, 5f7eadf0 Issues, b987f038 Workflows, 189cb95d guidance part-naming fix, 60f1a2c3 main-session test wording.

Counts: spec-validation CHK.style.* in scope 785 -> 0 (490 sentence-length, 295 semicolon; 0 errors). check-style.py on prompts/guidance/{kernel,distribution,issues,workflows}: 53 -> 0 (33 length, 20 semicolon). No sentence kept as an exception. build, build --check, task-validation ok; full pytest 1253 passed, 5 skipped.

Meaning review: an independent pi pass listed 276 possible differences; the pi repair pass fixed 200 and judged 75 not real. I then read every diff of all 78 parts and fixed by hand what both passes missed or introduced (about 45 places). These were: requirement statements that were no longer one sentence with one SHALL, or that had part of the obligation moved out (about 20 across all five Modules); invalid scenario steps (nested lists, AND alternatively, colon steps followed by AND items); one wrong referent the repair pass introduced (the update's result lists open tasks, not the validation's); a misread list intro in Tracing; and a dropped because/since in several places. The decision log has the full list, and an appendix with every finding of the check and its verdict.

Decisions taken without the developer: chunked rewrite (78 parts, about 1600 words each); pi with --no-context-files; Markdown tables left unchanged; scratch kept in the git-ignored .generated/ inside the worktree and removed before delivery; at most 2 pi lanes after your note; Distribution scenarios whose original steps passed the checks were restored to them rather than split.

Non-ok results: three pi rewrites timed out and were rerun. Pi repair calls hung because stdin was an open socket; I fixed this with </dev/null. test_guidance_parts failed because three guidance paragraphs no longer named their part (req.distribution.guidance-absent-parts), fixed in 189cb95d. 32 main_session/test_guidance assertions quoted the old guidance wording; I updated them to the restyled sentences with no instruction dropped (60f1a2c3).

Open: tests/concorde/main_session/test_guidance.py belongs to Main session's tests, so restyle-coordination may touch it too. A merge conflict there would be wording only. No Issues resolved; no escalations.

## Closed: merged, 2026-10-04T11:02:09Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 564d65da9495f99e77808e2b19ccab41454497ae into main and closed it as merged. Nobody answers a report after that.
