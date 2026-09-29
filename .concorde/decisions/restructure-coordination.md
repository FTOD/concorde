# Decision log: restructure-coordination

Goal: Restructure the Coordination entries (coordination, main-session, tasks, task-session) to Protocol 15.1's recommended order and workflow diagrams, without changing meaning

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
`task-session` has a sequence diagram. The root entry's former command walk-through was removed
because Main session, Tasks and Task sessions already specify it: keep those walk-throughs here.

## Task session (2026-09-30)

### Decisions taken without the developer
- **Structure of each entry.** Every entry now reads Purpose → Core concepts → Overview (diagrams
  with prose) → details → design reasons → providers/children. Coordination owns no concept, but
  its Core concepts section introduces the terms it is built from (task, main agent vs task session
  with the existing comparison table, workspace binding), since the brief allows linking other
  Modules' terms there. Task sessions likewise explains the root's task session and the Harness's
  session boundary in a short Core concepts section.
- **Diagram layout.** Lane workflows are drawn as a D2 `grid-columns` of lanes with invisible spacer
  cells aligning the rows, the technique of the root entry; a plain ELK layout of lane containers
  tangled the edges (rendered and rejected). Every added or changed diagram was rendered with
  `d2 --layout elk` and inspected.
- **Sequence diagram converted.** Task sessions' "How a task session travels over time" was a
  `shape: sequence_diagram`; its point is the steps and hand-offs, not message interleaving, so it
  is now a four-lane workflow (Main agent, Tasks, Session starter, Task session).
- **Other diagrams.** Coordination's small Usage flow became a four-lane workflow (Developer, Main
  agent, Task session, Execution) that also shows escalations, the merge-conflict return and closing
  without a merge, which its prose already described. Main session's representative flow (retry
  limit) was redrawn as a three-lane grid because ELK tangled it; nodes and edges are unchanged.
  All other diagrams (state diagram, merge flow, checked structure/context views) are unchanged,
  only moved into Overview or beside their details.
- **Anchors.** Every `concept.*`, `uses-*`, `contains-*`, `realization.*` anchor and the explicit
  anchors `owners`, `channels`, `waiting`, `decision-log-in-git`, `ending-claude-sessions` are kept;
  heading slugs linked from elsewhere (`main-session/module.md#issues`,
  `#the-project-mcp-server`) are kept as headings of the same name. Tasks' "Waiting" heading was
  named "Waiting for a task, a run or a lock" so the explicit `waiting` anchor stays unique.
- **Concept placement.** Tasks' merge-lock explanation (the flock paragraph) moved to Core concepts
  at `concept.merge-lock`; the merge command walk-through stays under "Merging". Main session's
  project-MCP-server concept paragraph is in Core concepts, the tools and channels under "The
  project MCP server". Main session's `uses-workers` moved from "Inside" to the providers down the
  levels.

### Found, not fixed (reorganization only)
- `specs/concorde/coordination/task-session/module.md`, `uses-main-session`: "Task sessions
  configures [the project MCP server] for every task session it starts, as a channel" contradicts
  the same entry's "Starting a session" ("It comes without a channel, and its configuration says so
  (`CONCORDE_CHANNEL=0`)") and Main session's Channels paragraph. Kept verbatim; the phrase "as a
  channel" looks like a leftover and should probably read "without a channel".

### Non-ok results
- `task-validation` `r-20260929T181517-task_validation-6105dd33` failed with `checks_unavailable` /
  `check_sandbox_unavailable` for `check.distribution.tests`: the session had not run
  `uv sync --locked --group dev` in the worktree (development skill step 3), so `.venv` was missing.
  Ran `uv sync` and `npm --prefix docsite ci`, then validated again.
- `task-validation` `r-20260929T181608-task_validation-24bd6cbe`: ok (ready). `delivery`
  `r-20260929T181706-delivery-59ccfe61`: ok, delivery commit `011b4005` on
  `concorde/restructure-coordination`.

## Main agent on the session's report (2026-09-30)

Accepted; merging. The contradiction found in `task-session/module.md` (uses-main-session says the
project MCP server is configured "as a channel" for task sessions, against "without a channel …
CONCORDE_CHANNEL=0" elsewhere) is left for a follow-up change proposed to the developer.

## Closed: merged, 2026-09-29T18:19:23Z
