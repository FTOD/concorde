# Decision log: panel-larger-spec-tooling

Goal: Finish the 2026-09-28 panel review's larger items for Spec, Spec review and Views: worked examples, the review memory Design section, split Spec review's bundled scenarios with their tests' @verifies, and the diagrams

## Brief from the main agent (panel-review LARGER items)

These items are the "larger" findings left from the 2026-09-28 `spec_panel` review (decision
history in `/home/zhenyu/concorde/.concorde/tasks/panel-review-fixes.decisions.md`). They are
confirmed real problems that need no design decision but are not small edits. Full review reports
(chair report and verdict per Module) are readable at
`/tmp/claude-1000/-home-zhenyu-concorde--claude-worktrees-panel-review-fixes/dbd505b3-74e1-499b-9440-e3cc4b821993/work/reports/module.<name>.md`
and `module.<name>.verdict.md`.

How to work:
- The project has changed a lot since the review. Check each item against the current Specs and
  code first. If it is already solved or no longer applies, record that here with the reason and
  skip it.
- If doing an item needs a design decision (narrowing or changing a promise, changing behaviour,
  a word choice that is not obvious), do not decide it: escalate to the main agent with options
  and a recommendation. Never narrow a Spec promise to fit the code; a Spec/code difference where
  it is unclear which is intended is escalated.
- Splitting a scenario: keep the original id on the first scenario; each new scenario id needs a
  test with `@verifies`, otherwise spec-validation warns `CONCORDE-COVERAGE-001`. Change the Spec
  and the tests' `@verifies` in the same commit, and only where the existing test really checks
  that scenario's outcome; otherwise add or extend a test.
- Diagrams: `d2 illustrative` blocks, following the diagram rules in the Protocol
  (`.concorde/protocol/`) and the project's Specs. "Don't draw diagrams for trivia": when the prose
  already says it plainly, skipping is fine; record why here.
- Usage items: restructure Usage so it opens with / contains a worked normal path, keeping every
  existing statement true.
- Use the glossary terms (`specs/concorde/glossary.json`) exactly. Edit only files of your
  Modules where possible; if another Module's file (or the glossary) must change, keep the change
  minimal and say so in your report.
- Never commit files a Bash sandbox mounts into the worktree (`.bashrc`, `.claude/...`).
- When done: task-validation and delivery, then report to the main agent: each item done or
  skipped (with reason), the decisions you took on your own, and anything waiting for a decision.

### Items of this task (handover list)

**module.spec**
- B · F16: worked example: one Module with a document, a binding and a use, then `concorde grant ... --type implement`, then one validation run that fixes a finding.
- C · F17: grant computation and initialization, two diagrams.

**module.spec-review**
- A · F16: split out `forced`, `records-judged` and `last-blocker-resolved` from `unchanged` and `memory`.
- B · F8: add a Design subsection "The review memory" (what it holds, why one file per Module, why the reviewer does the matching, why an unbound run doesn't write it, how an unusable memory stays confined to one Module), and trim the Usage paragraph accordingly.
- C · F9: diagram of repeated reviews and the memory.

**module.views**
- C · F26: the preview supervisor state diagram (optional).

### Verdict text for each item (from the review's verification agents)

#### module.spec

##### F16 LARGER — Usage has no worked example
This is real but advisory. It needs a new opening walk-through in module.md Usage: one Module that owns a document, binds `src/a/` and uses a provider; `concorde grant ... --type implement` with its actual entries, terms and identity; then a validation run with one finding fixed. That is well beyond a few sentences.

##### F17 LARGER — No flow view for grant computation and initialization
This needs two new `d2 illustrative` diagrams, beside Grants and Initialization in module.md. Part of the gap is closed: contracts.md #grants now states the computation order explicitly (see F3).



#### module.spec-review

##### F8 LARGER — Design does not explain the review memory
Its rationale is present but sits in Usage (concept.review-memory). What should be done: add a Design subsection "The review memory" covering the state it holds, why there is one tracked file per Module, why the reviewer does the matching, why an unbound run never writes it, and that an unusable memory contains the failure to one Module (`review_memory_unusable`). Then trim the Usage paragraph to the user-facing part. Best done together with F9.

##### F9 LARGER — Flow view for the repeated review
A real branching process: read memory, check the context identity and `--force`, reuse or launch the reviewer, optionally run the checker, merge, derive the outcome, write only when bound. What should be done: add a `d2 illustrative` activity view beside the memory explanation (ideally in the F8 Design subsection).

##### F16 LARGER — Scenarios appending other executions
The tests are already split: two tests verify scenario.spec-review.unchanged and two verify scenario.spec-review.memory. What should be done: split out new scenarios, e.g. `scenario.spec-review.forced` (`--force` launches the reviewer), `scenario.spec-review.records-judged` (a completed review records context identity and run), and `scenario.spec-review.last-blocker-resolved` (outcome `accepted`). Then retarget the second test of each pair in `tests/concorde/spec_review/test_operation.py`. Test edits are outside this Module's Spec files, and new scenarios without retargeted tests would be uncovered.



#### module.views

##### F26 LARGER — Preview supervisor lifecycle as a state diagram
The finding holds: the transitions are all in the prose, which is dense. Adding a `d2 illustrative`
state view (Staging, Running, Restart pending, Failed-waiting, Exited, with change, success, failure,
child-exit and interrupt transitions, in the same words as pipeline.md Preview) is a new diagram, so
I did not add it. It is optional, because the meaning is already complete in the prose.



## Task session log

### Check against the current state (2026-09-29)

All six items still applied: Spec's Usage had no worked example and its Design no flow view of the
grant computation or initialization; Spec review's Usage held the whole review-memory rationale,
Design had no subsection for it, `scenario.spec-review.memory` and `.unchanged` still appended
other executions (the `--force`, "records what it judged" and "last blocker resolved" bullets);
Views' Preview had no state view.

### Decisions taken without the developer

- **Spec F16, worked example from a real run.** Instead of inventing output, I built a throwaway
  project (Shop root with Checkout binding `src/checkout/` and using Inventory) in `$TMPDIR` with
  this branch's `initialize` and `concorde` command, and copied its actual `spec-validation`,
  `registry --write` and `grant --type implement` output into Usage. The finding fixed is
  `CHK.registry.mirror` after adding the `uses`, because Usage already names that repair. The
  example opens Usage; the sentence about `concorde` vs `python3 scripts/concorde.py` moved up to
  precede it. Every existing Usage statement is kept.
- **Spec F17, placement.** Both flow views (grant computation order; propose/apply of
  initialization) are `d2 illustrative` in Design, beside its "Boundaries and grants" and
  "Initialization" paragraphs, since they show how the computation runs; the Protocol puts design
  diagrams in Design.
- **Spec, stale initialization contract (outside the item list, own Module).** While drawing the
  initialization view I found `contracts.md#initialization` said the proposal holds "four files"
  and the entry "the five required sections", but the code (and the root entry's own text
  "This Module declares the project's glossary") writes a fifth file, the empty glossary
  `specs/project/glossary.json`, the root metadata declares it, apply allows writing it, and
  Protocol 15 requires three entry sections. Intent is clear (Protocol 15 moved terms into one
  glossary the root declares; the code does it deliberately), so I corrected the contract text
  rather than escalate. No promise was narrowed.
- **Spec review F16, split.** Kept the original ids on the first scenario of each pair; new
  `scenario.spec-review.last-blocker-resolved`, `.records-judged` and `.forced`. Tests: the
  memory test's second test is retargeted to last-blocker-resolved (and now also asserts the
  Module outcome and the resolution reason); the old combined "records and force" test is split
  into `test_a_completed_review_records_what_it_judged` (records-judged) and a new
  `test_force_reviews_unchanged_specs_again` (forced), which runs `--force` on a memory recording
  the current context identity and checks the reviewer ran and received the open earlier finding.
  A shared helper `reviewed_unchanged` sets up the unchanged memory for both unchanged tests.
- **Spec review F8/F9.** Design subsection "The review memory" (state held, one file per Module,
  why the reviewer matches, why unbound runs never write, `review_memory_unusable` confined to its
  Module) with the repeated-review activity view; Usage keeps the user-facing part and links to it.
  Rationale statements were checked against `src/concorde/spec_review/operation.py` (memory read
  before the reviewer, unchanged case writes nothing, unbound adds read-only evidence, unusable
  memory fails only that Module with the option "repair or remove ... then run spec_review
  again").
- **Views F26 (optional), done.** Added the state view beside Preview in `pipeline.md`. The
  interrupt transition is stated in the lead sentence rather than drawn from every state, because
  three extra edges made the layout unreadable; states and transitions follow the prose and
  `docsite/scripts/preview.ts`.

### Noted, not changed

- `spec-validation`'s `result.summary` also carries `infos`, while `contracts.md#validation-result`
  says it holds "the counts of errors and warnings". Minor; left for a later Spec core task.

### Delivery

task-validation: ready, no blocking finding or warning. Delivered as `d537589a` with `.concorde/evidence/panel-larger-spec-tooling/1.json`. Full suite 689 passed / 4 skipped; `build --check` clean; docsite build renders every new d2 block.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES; the contracts.md#initialization correction (five files,
  three sections) was confirmed against initialize.py and the Protocol. Sent back: the worked
  example's glossary term would draw CHK.concept.local, the example's grant omits the installer
  files the root binds without saying so, the review memory's last_run wording, and invalid_input
  missing from the initialization view.

### Fixes after the main agent's review

The main agent's review found four inaccuracies, fixed in one commit:
1. Worked example: Hold must be used by another Module or `CHK.concept.local` warns. The run the
   example was taken from already had Inventory link Hold (exactly one error, no warning), but
   the prose did not say so; it now does, and names the warning.
2. Worked example: the example project is uninstalled; added that an installed project's root
   binds the installer's files, which a real grant lists as `ro`, so "every other path is denied"
   is not misread.
3. Spec review Design: "the runs that first and last reported or resolved it", matching the code
   and operation.md.
4. Initialization view: `invalid_input` added to the refusals.

Re-delivered as `a3ab993e` with `.concorde/evidence/panel-larger-spec-tooling/2.json`; task-validation ready, no blocking finding or warning; `build --check` clean.

### Second review fix

The worked example said the project "is not yet installed", which cannot hold: initialization refuses a project without the Protocol copy (`not_installed`), so an initialized project is installed. It now says the root binds no files of its own and the example leaves out the installer's files; the later sentence says a real project's root binds them and the grant lists them as `ro`.

Re-delivered as `5b7c99d4` with `.concorde/evidence/panel-larger-spec-tooling/3.json`; task-validation ready, no blocking finding or warning.

## Closed: merged, 2026-09-28T20:32:15Z
