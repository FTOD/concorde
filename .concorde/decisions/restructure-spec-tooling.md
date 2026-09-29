# Decision log: restructure-spec-tooling

Goal: Restructure the Spec tooling entries (spec-tooling, spec-mcp, spec-review, views) to Protocol 15.1's recommended order and workflow diagrams, without changing meaning

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
`module.spec` is not yours (task `entry-stubs` holds it). Views was just changed by
`hide-implementation-tab` (merged `5fe03445`): its entry's Usage was rewritten for the removed
Implementation documents tab — keep that meaning. Spec review's sample finding texts such as
"Usage names the retry limit…" may stay; change them only if they now mislead, and log it.

## Task session (2026-09-30)

Decisions taken without the developer, all within the brief (reorganization only, no promise,
requirement, scenario, contract, relation or anchor changed; only the four entries were edited):

- **Anchors.** Every `concept.…`, `realization.…`, `contains-…` and `uses-…` anchor is kept. No
  document outside the four entries links to one of their heading slugs (grepped `specs/`, `docs/`,
  `protocol/`, `prompts/`, `src/`); the only heading link, Spec review's own
  `#the-review-memory`, keeps its heading. So headings were renamed freely and no `old-slug`
  anchors were added.
- **No sequence diagrams** existed in the four entries, so none was converted.
- **Spec tooling.** Purpose → Overview (the checked children diagram with the entry-point table,
  and a new illustrative workflow "A Spec change through Spec tooling": lanes Task level, Spec
  core, Spec review; validation errors loop back, `changes_required`/`incomplete` go to the task
  level which decides and reruns `specify`) → Why it is built this way (the three former Design
  paragraphs, each under its own heading) → The children (contains anchors) → Around it. No Core
  concepts heading: the Module owns no concept. The workflow ends `accepted` in "Specs ready for the
  next step" rather than in grant computation, because the entry says every later run computes
  grants from the Specs regardless of the verdict.
- **Spec MCP server.** Purpose → Core concepts (the server root, moved from Usage; "every answer
  is Spec core's", which restates the Purpose and Design's planning-only point with the terms
  linked) → Overview (new illustrative workflow of one tool call with lanes Agent, Server program,
  Spec core; the checked context diagram moved up from Around it) → Using the server
  (registration, tool table, example, failure codes) → Why it is built this way → The server
  program (realization) → Around it (uses-spec).
- **Spec review.** Purpose → Core concepts (review finding, review verdict, review memory at their
  glossary anchors, plus the panel report as a local idea) → Overview: "A Spec review", a new
  illustrative workflow of the step table's steps 1–7 with lanes Spec core, Operation, Worker runs
  (numbers match `operation.md#host-sequence`; failure exits are given in prose because drawing
  every `incomplete` edge made it unreadable); "A Spec panel", a new illustrative workflow with
  lanes Reviewer runs, Operation, Chair run, matching `panel.md#the-panel-graph`; "Its parts", the
  checked realization diagram with the realization anchors → Running a review (both commands) →
  Why it is built this way (the review memory with its existing flow diagram, the panel, what a
  reviewer sees) → Around it. The lane is named "Worker runs", not "Workers", because Workers names
  the Execution code, not the AI process.
- **Views.** Purpose → Core concepts (the bold local ideas: reading collections, canonical page,
  user documents and custom docs as moved from Usage with the hide-implementation-tab meaning kept
  word for word; publication candidate, promotion, published site, site manifest; scaffold
  proposal and site identity) → Overview (the checked parts diagram; "Publishing", the existing
  illustrative candidate workflow moved up; "Scaffolding", a new illustrative workflow of propose
  and apply with the outcomes `invalid`, `unchanged`, `conflict` and the file transaction, taken
  from the entry and `contracts.md` "Apply") → The commands → How it is built (the three
  realizations with their design paragraphs) → Around it.
- **Sample finding texts** "Usage names the retry limit…" in `spec-review/operation.md` and
  `panel.md` were left unchanged: they describe a hypothetical Module's entry, which may still have
  a Usage section under 15.1, so they do not mislead.
- Every new or changed D2 diagram was rendered with `d2` and inspected; the Spec review workflow
  was redrawn once (the first draft with every failure edge was tangled).
- **No error or gap found** in the four entries while reorganizing them.

## Task session: task-validation blocked (2026-09-30)

- Verified on commit `cc6c6c31`: `build`, `build --check` and `spec-validation` succeed with no
  findings; `npm run build` in `docsite/` built, verified (every internal link and anchor) and
  promoted the site.
- **Not ok:** `task-validation` run `r-20260929T182153-task_validation-e443e799` ended `blocked`
  (`not_deliverable`) with 18 `unbound_finding`s, none about the task's own change: `.bash_profile`,
  `.bashrc`, `.claude/{agents,commands,hooks,launch.json,loop.md,output-styles,routines,
  settings.json,workflows}`, `.gitconfig`, `.idea`, `.profile`, `.ripgreprc`, `.vscode`,
  `.zprofile`, `.zshrc`. They are empty files the Claude Code Bash sandbox created in the task
  worktree (02:20) and mounts read-only over themselves (`/proc/self/mountinfo` shows
  `ro` bind mounts of the same path). `src/concorde/validation/measurement.py` `special_paths`
  skips only sandbox paths that are not a regular file, directory or symlink (the `/dev/null`
  mounts earlier sandboxes used), so these regular empty files count as changed paths. This is a
  Concorde defect in Validation, outside this task's Modules.
- Removing the files from inside the sandbox was refused by the permission classifier; nothing
  was removed and no workaround was applied. Escalated to the main agent with options.

## Escalated to the main agent, 2026-09-29T18:28:33Z

- **task-session** task session (task restructure-spec-tooling): `sandbox_mount_points_unbound`
  task-validation (and so delivery) is blocked only by 18 unbound_finding paths that are empty files the Claude Code Bash sandbox created in the task worktree and bind-mounts read-only over themselves (.bashrc, .bash_profile, .profile, .zshrc, .zprofile, .gitconfig, .ripgreprc, .idea, .vscode, .claude/agents, commands, hooks, launch.json, loop.md, output-styles, routines, settings.json, workflows). Validation's special_paths (src/concorde/validation/measurement.py) only skips sandbox paths that are not regular files (the /dev/null mounts of earlier sandboxes), so these count as changed paths. The task's own change (commit cc6c6c31, the four entries) passes build, build --check, spec-validation and a verified docsite build. Deleting the files from inside the sandbox was refused, and the sandbox recreates them for every command.
  Not handled here (decision): The files belong to the sandbox, not to the task; fixing Validation is a change of module.validation, outside this task's Modules, and removing or excluding the files would override a readiness check, which is not mine to decide.
  Options: Fix special_paths in a separate task (module.validation) to also skip read-only mount points of the sandbox, merge it, then have me merge main into this branch and deliver again; Remove the 18 empty files from the task worktree outside the sandbox and run task-validation and delivery there outside the sandbox; Let me run task-validation and delivery with a per-process Git exclude (GIT_CONFIG_COUNT core.excludesFile) listing exactly those 18 paths
  Recommendation: Option 1 as the real fix, since every task session under this sandbox hits it; option 3 meanwhile if this task should merge now
  Caused by:
  - **command** Command task-validation r-20260929T182153-task_validation-e443e799 (workspace restructure-spec-tooling): `not_deliverable`
    workspace restructure-spec-tooling is not deliverable: 18 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/restructure-spec-tooling/workspace/runs/r-20260929T182153-task_validation-e443e799/readiness.json)
    Not handled here (decision): task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses
    Evidence (blocking): .bash_profile no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .bashrc no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/agents no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/commands no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/hooks no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/launch.json no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/loop.md no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/output-styles no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/routines no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/settings.json no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .claude/workflows no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .gitconfig no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .idea no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .profile no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .ripgreprc no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .vscode no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .zprofile no Module binds this changed path and it is neither a Spec document member nor a control record
    Evidence (blocking): .zshrc no Module binds this changed path and it is neither a Spec document member nor a control record
    Options: repair each blocking finding in the workspace and run task-validation again; run specify for a Spec finding, implement for a code or check finding
    Recommendation: repair the first blocking finding: unbound .bash_profile: no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .bash_profile: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .bash_profile no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .bashrc: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .bashrc no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/agents: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/agents no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/commands: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/commands no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/hooks: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/hooks no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/launch.json: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/launch.json no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/loop.md: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/loop.md no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/output-styles: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/output-styles no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/routines: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/routines no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/settings.json: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/settings.json no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .claude/workflows: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .claude/workflows no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .gitconfig: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .gitconfig no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .idea: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .idea no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .profile: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .profile no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .ripgreprc: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .ripgreprc no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .vscode: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .vscode no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .zprofile: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .zprofile no Module binds this changed path and it is neither a Spec document member nor a control record
    Caused by:
    - **component** Validation: `unbound_finding`
      .zshrc: no Module binds this changed path and it is neither a Spec document member nor a control record
      Not handled here (capability): binding a changed path to a Module is a Spec change, which task-validation never makes
      Evidence (unbound): .zshrc no Module binds this changed path and it is neither a Spec document member nor a control record

```json
{
  "level": "task-session",
  "actor": "task session (task restructure-spec-tooling)",
  "code": "sandbox_mount_points_unbound",
  "detail": "task-validation (and so delivery) is blocked only by 18 unbound_finding paths that are empty files the Claude Code Bash sandbox created in the task worktree and bind-mounts read-only over themselves (.bashrc, .bash_profile, .profile, .zshrc, .zprofile, .gitconfig, .ripgreprc, .idea, .vscode, .claude/agents, commands, hooks, launch.json, loop.md, output-styles, routines, settings.json, workflows). Validation's special_paths (src/concorde/validation/measurement.py) only skips sandbox paths that are not regular files (the /dev/null mounts of earlier sandboxes), so these count as changed paths. The task's own change (commit cc6c6c31, the four entries) passes build, build --check, spec-validation and a verified docsite build. Deleting the files from inside the sandbox was refused, and the sandbox recreates them for every command.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The files belong to the sandbox, not to the task; fixing Validation is a change of module.validation, outside this task's Modules, and removing or excluding the files would override a readiness check, which is not mine to decide."
  },
  "options": [
    "Fix special_paths in a separate task (module.validation) to also skip read-only mount points of the sandbox, merge it, then have me merge main into this branch and deliver again",
    "Remove the 18 empty files from the task worktree outside the sandbox and run task-validation and delivery there outside the sandbox",
    "Let me run task-validation and delivery with a per-process Git exclude (GIT_CONFIG_COUNT core.excludesFile) listing exactly those 18 paths"
  ],
  "recommendation": "Option 1 as the real fix, since every task session under this sandbox hits it; option 3 meanwhile if this task should merge now",
  "causes": [
    {
      "level": "command",
      "actor": "Command task-validation r-20260929T182153-task_validation-e443e799 (workspace restructure-spec-tooling)",
      "code": "not_deliverable",
      "detail": "workspace restructure-spec-tooling is not deliverable: 18 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/restructure-spec-tooling/workspace/runs/r-20260929T182153-task_validation-e443e799/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": ".bash_profile",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".bashrc",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/agents",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/commands",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/hooks",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/launch.json",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/loop.md",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/output-styles",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/routines",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/settings.json",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".claude/workflows",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".gitconfig",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".idea",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".profile",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".ripgreprc",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".vscode",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".zprofile",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        },
        {
          "kind": "blocking",
          "ref": ".zshrc",
          "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses"
      },
      "options": [
        "repair each blocking finding in the workspace and run task-validation again",
        "run specify for a Spec finding, implement for a code or check finding"
      ],
      "recommendation": "repair the first blocking finding: unbound .bash_profile: no Module binds this changed path and it is neither a Spec document member nor a control record",
      "causes": [
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".bash_profile: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".bash_profile",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".bashrc: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".bashrc",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/agents: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/agents",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/commands: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/commands",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/hooks: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/hooks",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/launch.json: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/launch.json",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/loop.md: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/loop.md",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/output-styles: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/output-styles",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/routines: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/routines",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/settings.json: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/settings.json",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".claude/workflows: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".claude/workflows",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".gitconfig: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".gitconfig",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".idea: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".idea",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".profile: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".profile",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".ripgreprc: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".ripgreprc",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".vscode: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".vscode",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".zprofile: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".zprofile",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        },
        {
          "level": "component",
          "actor": "Validation",
          "code": "unbound_finding",
          "detail": ".zshrc: no Module binds this changed path and it is neither a Spec document member nor a control record",
          "evidence": [
            {
              "kind": "unbound",
              "ref": ".zshrc",
              "detail": "no Module binds this changed path and it is neither a Spec document member nor a control record"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "binding a changed path to a Module is a Spec change, which task-validation never makes"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  ]
}
```

## Main agent's answer to the escalation `sandbox_mount_points_unbound` (2026-09-30)

Diagnosis by the main agent: the session still has a background sandboxed command running for
8+ minutes, an `until ! pgrep -f "docusaurus build" … grep … $TMPDIR/docsite.log` polling loop
(bwrap pids 1017354/1017361). While any sandbox of the session lives, Claude Code's sandbox runtime
defers removing its mount-point placeholders, so the 18 empty read-only files stay on the host as
regular files (seen on the host at 02:20) and the Validation run sees them as new paths; the same
lingering sandbox keeps `.git/config.lock` in place and blocks preparing other tasks. Earlier
restructuring tasks had the same placeholders as `/dev/null` character devices, which Validation
already skips.
Decision (ordinary scope): none of the three options. The session stops that background command
(TaskStop or kill of its own command; no file removal), then reruns task-validation and delivery.
Option 3 (excluding paths from a readiness check) is refused. Making Validation robust to
regular-file placeholders of a live sandbox is opened separately as task `validation-sandbox-paths`.

## Task session on the main agent's answer (2026-09-30)

Stopped my leftover background polling loop (`until ! pgrep -f "docusaurus build" …`), which never
ended because `pgrep -f` matched its own command line and so kept a sandbox alive; no other
background command of mine was running. Removed no files. Re-running task-validation and delivery.
- task-validation run after stopping the loop: ok, ready. delivery run
  `r-20260929T183536-delivery-0ff5ebf1`: ok, delivery commit `92af01d9` on
  `concorde/restructure-spec-tooling`.

## Closed: merged, 2026-09-29T18:40:58Z
