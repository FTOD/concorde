# Decision log: main-delegates-tasks

Goal: Task sessions work every task that is not a small change; tasks never ask the developer in place but stop and report all needed decisions upward; the installer adds the Concorde block to an existing AGENTS.md; the Concorde checkout loads the product skill plus a concorde-development skill instead of DEVELOPING.md

## 2026-09-29 — main agent: brief and the developer's decisions this task implements

The developer decided the following in the main session (these are the developer's decisions, not
the task session's to revisit):

- **D1. Every task is worked by a task session.** Every change that is not a small change runs as
  a task worked by a task session, even when there is only one task. The main agent no longer
  carries a task out itself by entering its worktree (drop the EnterWorktree / ExitWorktree and the
  pi "address the task worktree explicitly" method from the product guidance). The main agent keeps:
  discussing, opening tasks, starting and answering task sessions, unbound runs in the primary
  worktree, merging, closing, reporting, Issues, worker configuration.
- **D2. Small changes (product rule).** A very small change (a typo, a one-line fix, a wording
  correction) may be made by the main agent directly in the primary worktree, only after it has
  said what it would change and why it is small and the developer has approved that specific
  change. The existing housekeeping (`registry --write`) and the `workers.json`-alone commit stay.
  This replaces the inconsistent "only trivial housekeeping" (Main session Spec) vs "changes no Spec
  meaning and no code behaviour" (skill) wording.
- **D3. A task never asks in place.** A task has no interactive mode. When work in a task needs a
  developer decision, the task stops and reports upward, gathering as many of the decisions it
  needs as possible into one report rather than one at a time. The main agent decides which it may
  settle itself (escalation policy) and asks the developer the rest from the main session (at once,
  e.g. AskUserQuestion), then answers the task session with all answers. Consequences to carry out:
  the workflow mode `interactive` no longer means "ask the developer in place"; a workflow run by a
  task session may stop at decision points (`awaiting_decision`, with every pending point of the
  step) and the task session then escalates every needed decision in one round (Claude Code: one
  SendMessage after recording the escalations; pi: the round ends `escalated`) instead of the
  current "send the chain and wait for its answer before continuing". `no-ask` stays. Status words
  already exist per level: a run's `blocked` ("needs a decision above it"), a workflow's
  `awaiting_decision`, a round's `escalated`; add no new status.
- **D4. Merge conflicts are resolved by the task session.** On `merge_conflict` the main agent
  tells (answers) the task session to merge the primary branch into its own task branch, resolve,
  run task-validation and delivery again and report; that is the only merge a task session may
  make. Update the task-session guidance ("never merge, rebase or switch branches") and the main
  agent's merge section accordingly; check the session boundary allows it.
- **D5. AGENTS.md (installer, option (a)).** pi reads only the first of `AGENTS.override.md`,
  `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md`, `CLAUDE.MD` per directory (pi `core/resource-loader.js`,
  `loadContextFileFromDir`), so a project with its own `AGENTS.md` never shows the Concorde
  `CLAUDE.md` block to pi. The installer (and `concorde update`) SHALL also write the same delimited
  Concorde block into the project's `AGENTS.md` when that file exists, replacing it in place and
  recording the file under `amended`, and SHALL never create `AGENTS.md` (creating it would make pi
  skip the project's own `CLAUDE.md`). Regardless of `--pi`.
- **D6. The Concorde checkout uses skills.** The checkout loads the product main-session skill
  (`concorde`) plus a new `concorde-development` skill holding what is checkout-specific (today's
  `DEVELOPING.md`: preparation, build and protocol-manifest, formatting and verification, merge
  `--check`s, defect reports). `CLAUDE.md` and `AGENTS.md` keep a short always-on part (skills are
  loaded on demand, so the hard rules must stay in context): the core rules, the instruction to
  load both skills before any work, and in `CLAUDE.md` the glossary import. The skill frontmatter
  moves from the installer into the build so the installer and the checkout use the same rendered
  skill. Author the development skill as a prompt source that `@include`s Dogfooding's observe-runs
  fragment, and update `req.dogfooding.one-observation-rule` and the root Module's file bindings
  (`DEVELOPING.md`) to match. The checkout's rules follow D1-D4 (its current Claude Code "For a
  single task: EnterWorktree" section goes; its pi AGENTS.md already delegates).

Main agent's own decisions (without the developer):

- One task rather than several: D1-D6 all change the main-session guidance, Distribution and the
  glossary, so separate tasks would overlap on the same Modules and files and could not run at once.
- Left to the task session, to decide and log: the new name of the workflow mode that stops at
  decision points (if `interactive` is renamed; update `concept.workflow-mode`); how the checkout
  places the rendered skills (tracked symlinks into `generated/` vs. build-written ignored files;
  verify that both Claude Code and pi load whichever is chosen); whether the AGENTS.md block omits
  the `@glossary` import line (it is Claude Code syntax; pi gets terms from the extension).
- Out of scope: the "where to find logs and traces" gap in the skill was raised but not approved.

## 2026-09-29 — task session: decisions taken without the developer

- **Workflow mode name: `interactive` kept, redefined.** Options: rename it (`ask`, `stop`) or keep
  it. Kept, with `concept.workflow-mode` redefined: the workflow ends at a decision point "so that
  its decisions are settled above the task, through the main agent, before it goes on". Reason: the
  developer still interacts (through the main agent) while the workflow waits, so the word stays
  true; a rename would reach `scripts/e2e/e2e.py` and the e2e Specs, which belong to module.e2e,
  outside this task's Modules, plus the workflow contracts and scripts, for no change in behaviour.
- **Default mode of a task session's workflow.** The task session runs a workflow in the mode the
  brief names, and `interactive` when the brief names none. Reason: D3 sends every decision upward,
  and interactive is the mode that does; the main agent asks the developer the mode and names it.
- **The task's brief lives in the decision log.** The main agent records the brief (the developer's
  decisions, workflow and mode, what is left to the session) in the decision log before starting
  the session, and the task-session guidance says to read the log first (new
  `req.main-session.task-brief`). Reason: `concorde task session` passes only the goal, and this is
  how this very task was briefed; it needs no new command option.
- **A pending workflow's points are escalated with the report as `--error-file`.** The
  `awaiting_decision` report's `error` link already names every pending point (Workflows' error
  table), so one escalation carries them all.
- **Issue writes and Issue-conflict resolution move to the task session** (the main agent names
  them in the brief or its answer), since the main agent no longer works in a task worktree.
- **`concorde_run`'s task argument is kept.** The pi tool can still start a run in a task worktree;
  the guidance no longer tells the main agent to use it that way (only for unbound runs). Removing
  the argument would change the pi extension and its tests for no gain in this task; left as is.
- **AGENTS.md block omits the glossary import.** `@path` is Claude Code syntax (Claude Code reads
  CLAUDE.md, not AGENTS.md), and pi gets the terms from Concorde's pi extension.
- **Skill front matter in the build.** New owned outputs `generated/skills/<name>/SKILL.md`
  (header + the prompt root's render; descriptions in `build.SKILLS`) and `generated/development/`;
  the installer copies `generated/skills/concorde/SKILL.md` and appends Dogfooding's section in a
  develop install. Prompt front matter stays `audience` only, since the resolver admits no other key.
- **Checkout skill placement: pi via `.pi/settings.json` `skills`, Claude Code via tracked symlinks
  `.claude/skills/<name>` -> `../../generated/skills/<name>`.** Both verified in a scratch repo:
  `claude -p` answered from a symlinked skill; pi's RPC `get_commands` listed `skill:<name>` loaded
  from a settings path. Build-written ignored files were rejected: the build runs in task worktrees,
  where the session sandbox forbids writing `.claude/skills`, so every task session's build would
  fail. The symlinks themselves could NOT be created here (see "Open" below).
- **The development skill source is bound by the root Module** as the new realization
  `realization.concorde.development-guidance` (`prompts/development/skill.md`), and described in
  `development.md` with `scenario.concorde.development-skills` (tested in
  `tests/concorde/development/test_pi_settings.py`).
- **Outside this task's Modules, forced by removing DEVELOPING.md:** dropped `DEVELOPING.md` from
  the inputs of `check.views.repository-regressions` (`.concorde/checks/module.views.json`) and
  from the file list `docsite/tests/repository/run-checks.py` copies (module.views). Without it
  spec-validation fails (`missing_source`) and the Views check would crash copying a missing file.
  One line each, no promise changed; reported to the main agent.
- **User guide updated** (`docs/using-concorde.md`, root Module): task sessions for every task,
  batched questions, small changes, the AGENTS.md block.

## Open (for the main agent / developer)

- **`.claude/skills/concorde` and `.claude/skills/concorde-development` symlinks are missing.** The
  session sandbox forbids any write under `<worktree>/.claude/skills` (Claude Code protects that
  directory), so they cannot be created in this task, and working around it (e.g. adding them to
  the index with Git plumbing) would defeat that protection. Until they exist, CLAUDE.md tells
  Claude Code sessions to read `generated/skills/<name>/SKILL.md` directly; pi is unaffected.
  Creating them is a two-symlink small change for the developer to approve (or make) on main:
  `ln -s ../../generated/skills/concorde .claude/skills/concorde` and the same for
  `concorde-development`, then commit.

## 2026-09-29 — task session: delivered

full suite 751 passed, 4 skipped; task-validation ready (23 checks passed); delivery commit cc4a492421eb2e85421ee9a14970bfe12cffe5d0 (.concorde/evidence/main-delegates-tasks/1.json).

## Closed: merged, 2026-09-29T05:30:23Z
