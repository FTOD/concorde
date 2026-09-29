# Decision log: restructure-operations

Goal: Restructure the Operation entries (operations, understanding, specification, implementation, code-review, adoption) to Protocol 15.1's recommended order and workflow diagrams, without changing meaning

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
`operations` has a sequence diagram. `adoption` was already edited by `entry-structure` (its
guidance on entry structure); keep that.

## Task session (2026-09-30)

- **Structure.** Every entry now reads Purpose → Core concepts → Overview → details (running the
  Operation, how it is built, what it relies on). Level-2 headings follow the root model; the old
  `Usage`, `Design` and `### Outside` headings are gone. No other document linked those heading
  slugs (grep of `specs/`, `protocol/`, `prompts/`, `docs/`, `src/`), so no alias anchors were
  needed; the one internal link, Operations' `#the-providers`, keeps its heading. Every
  `concept.*`, `realization.*`, `contains-*` and `uses-*` anchor is kept.
- **Core concepts without owned terms.** Implementation and Code review own no glossary concept;
  I still gave them a Core concepts section with the ideas a reader needs first (checks decide,
  code change and test report, checked Modules, pending files; findings and basis, verdict, one
  pass), since the Protocol's recommended order allows other Modules' terms and core ideas there.
- **Operations' sequence diagram.** Converted to a workflow with one container per participant
  (worker, Operation, task level): its point is which level holds the claim and which the evidence,
  not message interleaving. A first attempt with grid lanes rendered with overlapping edges, so
  lanes are containers laid out left to right.
- **New overview diagrams** (illustrative, drawn only from existing prose): Operations' standard
  worker sequence; Specification's who-does-what flow (a lane layout rendered tangled, so it is a
  top-down flow with the participant named in each step); Implementation's implement-vs-test
  comparison; Code review's preparation → review → verdict → next step. Understanding's and
  Adoption's existing diagrams became their overviews. Every diagram was rendered with
  `d2 --layout=elk` and inspected.
- **Tightening.** Repeated term links in the relies-on sections were dropped where the term is
  linked earlier in the entry; duplicated sentences (e.g. Implementation's two `--focus`
  statements) merged. Specification's core concept adds one sentence making explicit that step 1's
  baseline is what later validations compare with, restating the step table.
- No Spec error or gap found that needs reporting.
- **Validation and delivery.** `build --check` clean, `spec-validation` success with no finding,
  `task-validation` ready with no blocking finding and every check passed; `delivery` ok, delivery
  commit `c6180a01`. The worktree shows 18 empty untracked files (`.bashrc`, `.zshrc`,
  `.claude/settings.json`, …); they are the Bash sandbox's placeholder mounts, not task work, and
  were left untouched and uncommitted.

## Main agent on the session's report (2026-09-30)

Accepted, including Core concepts sections for Modules that own no term (the Protocol recommends
the order, it forbids nothing). Merging.

## Closed: merged, 2026-09-29T18:20:25Z
