# Decision log: restructure-e2e

Goal: Restructure the end-to-end testing entries (e2e, headless-sessions, dogfood-scenarios, swe-bench-cases) to Protocol 15.1's recommended order and workflow diagrams, without changing meaning

## Brief (main agent, 2026-09-30)

### Why
The developer found Module entries hard to read: a mandatory Purpose / Usage / Design skeleton put
entry-point walk-throughs first and split "what the system is" from "why", burying the core ideas;
sequence diagrams felt heavy. Task `entry-structure` (merged as `090c764b`) changed the Spec
Protocol to 15.1.0 accordingly and rewrote the root entry `specs/concorde/module.md` as the model
to follow. The developer then asked that **every** Module entry be restructured the same way; this
task does the entries of the Modules it is bound to.

### The rules (read `protocol/module.md` "The entry" and `protocol/migration.md` "Version 15.1")
- No section is required; the whole entry is the design. Follow the recommended order:
  1. **Purpose** — short plain prose.
  2. **Core concepts** — the Module's own terms explained at their glossary anchors
     (`<a id="concept.…">`), other Modules' terms linked. Omit the heading when the Module owns no
     concept worth explaining.
  3. **Overview** — diagrams of the main structure, functions and flows, each with short prose.
  4. **Details** — headings of your choice: parts, collaborations with children and providers (at
     the `contains`/`uses` meaning anchors), entry points and commands, errors, design reasons.
- Command-level walk-throughs belong to the Module that owns the commands (so they stay in your
  Module if it owns them), but after the concepts and overview, never as the opening.
- Every process is a **workflow diagram** by default (lanes per participant when useful); a
  sequence diagram only when the interleaving of messages is itself the point. Convert any
  `shape: sequence_diagram` in your entries unless that exception clearly applies (log why).
- Render every D2 diagram you add or change and look at it before keeping it.
- The reader requirements of `protocol/module.md` still hold.

### Constraints
- This is a **reorganization, not a change of meaning**: no promise, requirement, scenario,
  contract or behaviour changes. Tighten prose and remove repetition where it is safe; when you find
  a real error or gap, do not fix it here — log it and report it.
- Keep **every anchor id** stable (`concept.…`, `realization.…`, `contains-…`, `uses-…` and any
  heading slug that other documents link to — grep `specs/` for `<entry path>#` before renaming a
  heading). If a heading must be renamed, add an explicit `<a id="old-slug"></a>`.
- Edit only the documents of your bound Modules. Do not change `specs/concorde/glossary.json`
  definitions; do not touch code. Several restructuring tasks run in parallel on disjoint Modules.
- Run `python3 scripts/concorde.py build` and `spec-validation`, then `task-validation` and
  `delivery` in the task worktree, and report to the main agent with a one-paragraph summary per
  entry (new structure, diagrams converted, anything logged).

## Task session (2026-09-30)

- **Structure of all four entries.** Each now reads Purpose → Core concepts → Overview → details
  (the commands with their walk-throughs, "Why it is built this way", Files, children or "Around
  it"). The former Usage and Design sections were dissolved into these; every anchor id
  (`concept.…`, `realization.…`, `contains-…`, `uses-…`, `owners-case`, `live-sessions`) is kept.
  `owners-case` and `live-sessions` now stand directly below their new headings, because an anchor
  followed by a heading fails `CHK.node.explained` (seen as two warnings, then repaired).
- **No sequence diagrams existed** in these entries; the two existing flowcharts (the session round
  and wake, the repair-specs round) were already workflow diagrams and are kept unchanged, as are
  the checked children diagram of End-to-end testing and the "what each command makes" data-flow
  view of Dogfood scenarios.
- **New illustrative workflow diagrams, rendered and inspected:** End-to-end testing's "test project
  from preparation to removal" (lanes for the tool, headless run, driver run and test project, which
  shows the two runs differ only in what sits between workflow steps) and the owners-case phase
  (first drawn with lanes, which was too wide and tangled; redrawn as one top-down column);
  Dogfood scenarios' prepare → run → evaluate flow (the session step labelled as the *expected*
  behaviour, since the session may fail it); SWE-bench cases' "working a case" with a lane per
  participant (left-to-right kept after comparing with a top-down layout).
- **Core concepts chosen:** test project, the headless/driver run pair and the testing conditions
  (e2e); headless session and rounds, the headless note and test procedure, unsettled runs and the
  wake, live session (sessions); dogfood scenario with its example, scenario directory, evaluation
  (dogfood); a case and working a case (cases). Only the three glossary concepts carry anchors;
  the others are bold local ideas, no glossary change.
- **Moved, not changed:** e2e's "not in the test suite" paragraph moved from Design into Purpose as
  its non-goal; the list of children moved from Purpose into the Overview beside the children
  diagram; the uses sections of e2e were reordered Distribution, Workflows, Execution, Main session,
  Tasks.
- **Found error, not fixed as such (for the main agent):** the e2e "Around it" introduction said
  "End-to-end testing relies on three providers to set a test project up, run it and follow it",
  but the Module declares five `uses` (Workflows, Main session, Tasks, Execution, Distribution); the
  sentence predates the owners case. The reorganized text names the three it meant (Distribution,
  Workflows, Execution) and adds that the owners case relies on Main session and Tasks, which only
  states the declared relations; no promise changed.
- **Gap noted, not fixed:** the checked children diagram of End-to-end testing draws no edge for the
  parent's `uses` of Main session and Tasks. A checked diagram need not be complete, so it is left
  as it was.
- **Verification and delivery.** `build`, `build --check`, `spec-validation` (no findings) and
  `tests/concorde/e2e` (33 passed) on commit `294f0736`; `task-validation` ready with nothing
  blocking; `delivery` ok, delivery commit `8c99a33a`. The task worktree also shows untracked dotfiles
  (`.bashrc`, `.claude/agents`, `.idea`, …) this session did not create; they were left alone and are
  not in any commit.

## Closed: merged, 2026-09-29T18:12:41Z
