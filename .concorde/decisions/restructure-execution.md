# Decision log: restructure-execution

Goal: Restructure the Execution entries (execution, workflows, workers, checks, commands, validation, delivery) to Protocol 15.1's recommended order and workflow diagrams, without changing meaning

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
`module.scaffold` is not yours (task `entry-stubs` holds it); `workflows` has a sequence diagram.

## Task session (2026-09-30)

### Decisions taken without the developer

- **Order of every entry.** Purpose → Core concepts (each concept explained at its glossary anchor,
  the bold term now linked, since the validator asks for a link at first use) → Overview (diagrams
  with short prose) → details under headings of my choice (usage and commands, the result, "How it
  is built" for design reasons and realizations, then "The children" / "What <Module> relies on" at
  the unchanged `contains-*`/`uses-*` anchors). Command walk-throughs stay in the owning Module, after
  concepts and overview.
- **Anchors kept.** Every `concept.*`, `realization.*`, `contains-*` and `uses-*` id is unchanged.
  Heading slugs linked from outside are kept: Workers' `#two-backends-from-one-grant` and
  `#choosing-worker-models` (from `pi.md`, `contracts.md`); Check execution's `#design` (from
  `boundary.md`) is now an explicit `<a id="design"></a>` under "What the boundary enforces", placed
  before prose because a bare anchor before a heading raised `CHK.node.explained`.
- **Execution.** New illustrative diagrams: the seam (preparer writes the binding, Execution reads
  it and writes the run store and delivery commits, the preparer reads them) and a workflow of a
  run's life (the runner paragraph's steps, bound/unbound branches, refusals). Added a two-sentence
  core-concept statement at `concept.execution-runner` (from the glossary definition); the step
  paragraph moved to Overview. The overview children subsection is titled "Five children" so that its
  slug does not collide with the details section "The children".
- **Workflows.** The `shape: sequence_diagram` ("one step over time") is converted to a workflow
  diagram with five lanes (task level, workflow script, step agent, workflow commands, Execution
  runner): the point is the ask-again loop and the start-once rule, not message interleaving, so the
  sequence-diagram exception does not apply. Added a short step-key explanation in Core concepts
  that points to the exact rule kept under "The step command". Brownfield flow diagram moved to
  Overview; step table and walk-through to "Using a workflow".
- **Workers.** Existing diagrams kept (the normal run is already a workflow diagram); concepts
  grouped as host/worker, where a run lives, what the worker gets, what the host checks and keeps,
  backends, configuration. Its first "The file holds…" sentence of Choosing worker models now says
  "The worker configuration holds…" since it no longer follows the concept paragraph.
- **Check execution, Commands, Validation, Delivery.** New illustrative workflow diagrams: one call
  of the check service (digest, boundary, run, log, re-digest; sandbox refusal and `stale_evidence`);
  a task's last two runs (task-validation preview, repair, delivery, delivery commit); the nine
  readiness steps with their failed/blocked/ok ends; the ten delivery steps with their ends.
- Every added or changed D2 diagram was rendered with the docsite's options (`--layout=elk
  --theme=0`) and inspected; a sentence-level diff against each old entry shows no sentence dropped
  (only bold lead-ins, heading lines and the new connective prose differ).

### Real errors found, not fixed here (reorganization only)

Since the evidence bundle was dropped (Delivery: "The commit carries no evidence file of its own"),
these statements are stale and should be repaired by a task that may change meaning:

1. `execution/workers/module.md` says twice that "Delivery later lists these records' identities in
   a workspace's evidence" (run record concept and "Its place in the levels of work"), and "The
   Operation providers, Spec review and Delivery use this Module" — Delivery declares no `uses` of
   Workers and lists no run records.
2. `execution/module.md` says `delivery` "commits it with its evidence" (Runs concept) and "commits
   the workspace's changes with their evidence" (`contains-commands`); `execution/commands/module.md`
   says the same at `contains-delivery`.
3. "Delivery cites the runs that led to it" (`commands/module.md`, execution command concept) and
   "delivery must cite the run that decided the readiness it committed" (`execution/module.md`, Why
   commands are runs): Delivery decides its readiness itself and cites no earlier run.

### Verification

`build`, `build --check` and `spec-validation` succeed with no finding; `npm --prefix docsite run
validate` and `run build` succeed, so every diagram renders. `task-validation`: ok, ready.
`delivery`: ok, delivery commit `613fb5a0` on `concorde/restructure-execution`.

## Main agent on the session's report (2026-09-30)

Accepted; merging. The three stale statements (evidence bundle leftovers in Workers, Execution and
Commands; "Delivery cites the runs") go to a follow-up task that may change meaning.

## Closed: merged, 2026-09-29T18:22:52Z
