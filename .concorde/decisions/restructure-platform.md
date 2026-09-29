# Decision log: restructure-platform

Goal: Restructure the harness, tracing, issues, distribution and dogfooding entries to Protocol 15.1's recommended order and workflow diagrams, without changing meaning

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

### Task-specific
`harness` has a sequence diagram. `distribution` got one test edit from `entry-structure`.

## Task session (2026-09-30)

Decisions taken without the developer, all within the brief's "reorganization, not a change of meaning":

- **Common shape.** Each of the five entries is now Purpose → Core concepts (one `###` per owned
  concept group, at the unchanged `concept.*` anchors) → Overview (diagrams with short prose) →
  a usage section of details ("Using traces", "Using Issues", "Using Distribution", "Using a develop
  install"; Harness has none, its worked example is in the overview) → "How it is built" (Around it
  with every `uses-*` anchor, design reasons, realizations at their `realization.*` anchors). Text was
  moved as whole paragraphs; the bold lead-ins that duplicated the new headings were dropped.
- **Anchors kept.** No `concept.*`, `uses-*`, `realization.*` or `concept.distribution.update` anchor
  changed. Heading slugs linked from elsewhere are kept as headings: `harness#known-limits-of-v1`,
  `tracing#the-error-chain` (now the core-concept section of the error chain; the design reason
  moved under "Why errors travel as a chain"), `issues#lifecycle`,
  `issues#branch-local-records-and-repair`. `issues#design` (cited as an example in
  `prompts/workers/review-code.md`) is kept by an explicit `<a id="design"></a>` under "How it is
  built", with one sentence of prose because spec-validation reports an anchor without prose.
- **Harness.** The worked example's `shape: sequence_diagram` became a three-lane workflow
  (Workers, Harness, agent program; steps 1–7). The interleaving of messages is not the point
  there, the steps are, so the exception does not apply. Added an illustrative context view of
  which agent Module asks the Harness for what (Workers, Task sessions) and Distribution installing
  the main session's guidance with no Harness. The purpose's "each level asks for…" and the old
  Design intro said the same thing; they are merged into "Where the Harness sits". The checked
  realization diagram is unchanged, moved to the overview as "Its parts".
- **Tracing.** Added an illustrative workflow "Where records live over a task's life" (task open →
  current folder → history on close → conversation records removed after 30 days by default →
  whole folder when configured; unbound runs after 7 days by default; the decision log committed
  to Git on close), drawn only from the existing retention and history text. The producers'
  component view moved to the overview.
- **Issues.** The two checked diagrams (around, inside) moved to the overview as "Structure" with
  one sentence of prose; "Lifecycle" (state diagram, table, rules) and a new "A deferred repair"
  heading carrying the existing lane workflow are in the overview; the disposition commands moved
  to "Closing and reopening" in the details. "Main session declares `session -> issues` above" now
  points to the Structure diagram.
- **Distribution.** Added core-concept paragraphs for the build manifest and the Protocol copy,
  written only from facts the entry already stated (they had anchors but no explanation of their
  own), and moved the command-naming paragraph (distribution commands) into the concepts. Added two
  illustrative overview diagrams: the data flow from checkout through the build to the project, and
  the install as a workflow (decide writing nothing → write steps 2–9, the program-running steps
  dashed, refusal leaves the project unchanged). Removed the installer-program paragraph's verbatim
  repeat of "Only the steps that run those programs … can fail after something was written"; the
  sentence stays in "Installing into a project".
- **Dogfooding.** Added core-concept paragraphs for the develop install with the Concorde
  repository, and for the defect report, from existing facts; moved "whose problem is it / Concorde
  defect" and the boundary-case table into the concepts. The existing lane workflow of a defect's
  path is unchanged (rendered and checked) as the overview. The develop-source refusals moved next to
  "Making a develop install".
- Every added or moved D2 diagram was rendered with d2 0.9.0 and looked at.
- **No errors or gaps found** in these entries' meaning that needed reporting.

Non-`ok` observation: midway through, a `build --check` failed with
`bwrap: Can't find source path /home/zhenyu/concorde/.git/worktrees/hide-implementation-tab/config.worktree`
(another task's worktree was removed while my sandbox config still named it). Since then the
sandbox shows 18 untracked character-device stubs in this worktree (`.bashrc`, `.idea`,
`.claude/settings.json`, …); they do not exist on disk outside the sandbox (the Read tool finds no
`.bashrc`), so they are sandbox mount points, not files. I committed only explicit paths.

## Closed: merged, 2026-09-29T18:19:11Z
