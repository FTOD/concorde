# Decision log: parts-guidance

Goal: Split the main-session guidance into Coordination's working method and one guidance section per other part, compose the project skill, the task-session prompt and the CLAUDE.md block from the sections of a given set of parts, and render this checkout's skill from every part

## Brief (main agent, 2026-10-03)

### Context shared by the code tasks

The developer decided (2026-10-03) to split Concorde into independently installable parts: any
part, or any subset, can be installed into a project and works without the parts it does not depend
on. Everything happens on the integration branch `parts-split` (the primary worktree is on it; tasks
merge there, never into `main`). Done so far: `parts-spec` (the Specs describe the nine parts and
their directions: root `specs/concorde/module.md` "The parts", `req.concorde.part-dependencies`,
`part-alone`, `absent-part-stated`), `parts-layout` (one directory per part under `src/concorde/`
and `tests/concorde/development/test_part_dependencies.py`, whose `KNOWN_EXCEPTIONS` lists every
import still breaking the directions, grouped by the code task that removes it; the test fails on a
new violation and on a stale exception) and `parts-kernel` (the kernel library in
`src/concorde/kernel/`: typed values, contract-schema checking, file transactions, digests,
workspace binding, delivery commits, workspace and merge locks, registered trace roots). Read their
decision logs in `.concorde/decisions/`. Remaining code tasks: issues and worker harness (in
parallel), then execution, workflow, method, coordination, distribution.

**How an optional integration works (main agent's decision, 2026-10-03).** A part never imports the
Python code of a part it does not depend on, not even guarded by `ImportError`: that is what
`req.concorde.part-dependencies` says ("import code of ... only the parts it depends on"). An
optional integration reaches the other part only through what that part publishes as a contract:
its `concorde` command (JSON in and out, as its Spec defines), or a file format its Spec defines,
read (never written) by the relying part. Whether the other part is installed is told by the host
or the format itself: the `concorde` command refuses a command of an absent part with a stable code
naming the part (`req.distribution.absent-part-named`; until the distribution task builds the
dispatcher, treat "command not available" the same way), and an absent format's files simply do not
exist. The relying part then skips the feature with a plain statement naming the missing part
(`req.concorde.absent-part-stated`). A process that holds a lock the other part's command needs
hands it on as Tracing's "Handing a lock on" describes. The parts-layout test's allowance of
`method -> issues` imports is withdrawn accordingly: remove it from the test when your task removes
the last such import (the issues task does).

**Rules for every code task.** Rapid-iteration rule: no compatibility re-exports, shims, transitional
adapters or dual paths; refactor boldly. Keep record formats the Specs did not change readable, since
the primary worktree's existing `.concorde/` records (tasks, history, Issues, locks) must still read
after the merge. Remove every exception your task makes stale and add none (moving one to another
group is fine when its remaining reason belongs to another task). If a Spec is wrong or silent in a
detail the code needs, fix the Spec in your task and record why; escalate only a conflict with the
developer's decisions above. Verify with `build --check`, `spec-validation`, the full suite
(`.venv/bin/python -m pytest`) and smoke runs of the commands you touched from the task worktree,
then `task-validation` and `delivery`, and report.

Since this context was first written, every part's code task merged, and `parts-registrations`
too: each part has `src/concorde/<dir>/registration.json` (contract
`contract.distribution.part-registration` v2, with a `guidance` field); the `concorde` command,
the project MCP server and the build are composed from the installed parts' registrations; an
absent part's command or tool is refused with `part_missing`; `generated/parts.json` indexes every
part's commands and tools; `KNOWN_EXCEPTIONS` is gone. Today only Coordination registers guidance:
`generated/main-session/skill.md`, rendered from `prompts/main-session/skill.md`, which still
describes every part. After this task, one more task does the installer of any part subset, the
receipt's `parts`, the update and partial-install acceptance tests; it will place the guidance this
task composes for the parts it installs.

### What this task does (guidance)

Read `req.distribution.composed-guidance`, Distribution's guidance and installation sections, Main
session's Spec (it owns the main-session guidance) and the current `prompts/main-session/skill.md`,
`task-session.md` and `claude-md.md` first.

- **Split the guidance by part.** Coordination keeps its working method (discussing, splitting work
  into tasks, task sessions, decision logs, deciding and escalating, merging, closing, reporting,
  its project MCP tools). Every other part gets its own guidance section, registered through its
  registration's `guidance` and kept with that part's prompts: spec (Spec queries,
  `spec-validation`, `grant`, the project terms and glossary), execution (runs, Operations vs
  execution commands, unbound runs, reading results and error chains), method (the Operations and
  their typical order, `task-validation`/`delivery`, Module reviews, brownfield), workflow
  (workflows, modes, `workflow_report` now taking the workspace `folder`), issues (recording,
  tiers, severities, fixing, failures of the Issue system), worker harness (worker models,
  `workers.json`, the model map), kernel and distribution only if they have something a main agent
  must know (e.g. `concorde update`). Each section must read correctly whether or not the other
  parts are installed: where it mentions another part, say what happens without it (e.g.
  Coordination: deliver with `task deliver` where Method is absent, with `delivery` where it is
  present; merges run `spec-validation` only with the spec part). Keep the substance and the
  wording of today's text wherever it stays true; this is a split, not a rewrite.
- **Compose from a set of parts**: the project skill is Coordination's working method followed by
  every other installed part's section in the order of the parts, or, without Coordination, the
  installed parts' sections alone (`req.distribution.composed-guidance`); the task-session prompt
  and the `CLAUDE.md` block are composed the same way (e.g. the glossary import only with the spec
  part; the task session's delivery step by whether Method is installed). Provide this as
  Distribution's composition over registrations (build and installer use the same code); the
  installer of this task still installs every part, so it composes for all of them, and the next
  task passes the subset.
- **This checkout** renders its skills from every part, so `.claude/skills/concorde` (via
  `generated/skills/concorde/SKILL.md`) reads as one complete guidance after the merge, and the
  `concorde-development` skill keeps working; check the rendered skill end to end for dangling
  references between sections.
- Update Main session's and Distribution's Specs to say where each part's guidance lives and how it
  is composed, and the user documents (`docs/`) where they describe the guidance.

Bound Modules: Main session, Distribution, and each part's top Module whose guidance prompt it now
registers. Nothing runs in parallel with this task.

## Task session decisions (2026-10-03)

- **Registration field.** `guidance` becomes `null` or an object `{skill, task_session, claude_md}`,
  each the build-relative path of a rendered section (`generated/<path>.md` from `prompts/<path>.md`)
  or `null`, since one part contributes up to three sections (the project skill, the task-session
  prompt, the `CLAUDE.md` block). `contract.distribution.part-registration` goes to version 3.
  Reason: the brief asks all three to be composed per part; one path cannot name three sections.
- **Where the sections live.** Coordination keeps `prompts/main-session/{skill,task-session,claude-md}.md`
  (Main session owns them); every other part's sections are `prompts/guidance/<part directory>/`,
  rendered to `generated/guidance/<part directory>/`, and bound in that part's top Module's metadata.
- **Order.** Coordination first, then the others in the order of Distribution's parts table (spec,
  kernel, worker harness, execution, workflow, issues, method, distribution), which Distribution's
  Spec already names as the order; a part the table lacks would follow by name. The composition adds
  nothing of its own between the sections: it is the sections joined by one blank line, the skill
  under its front matter.
- **One composition code.** `concorde.distribution.guidance` composes the three outputs from a set
  of registrations; the build composes for every part (`generated/skills/concorde/SKILL.md` and the
  task-session prompt `generated/guidance/task-session.md`, which `task session` reads), and the
  installer composes for the parts it installs (still every part) and writes the task-session
  composition into its Framework copy at that same path, so the next task only passes the subset.
- **Frame without Coordination.** Distribution's own section, present in every install, says what
  `concorde` is, that the guidance and commands come only from the installed parts (`part_missing`)
  and how `concorde update` is used, so a skill composed without Coordination still says what
  `concorde` means. The glossary import of the `CLAUDE.md` block is added only with the spec part.
- **Bindings.** Each other part's `prompts/guidance/<part directory>/` is bound by a new
  `realization.<top module>.guidance` of that part's top Module (Spec tooling, Kernel, Worker
  harness, Execution, Workflows, Issues, Method, Distribution), each described in its `module.md`;
  `src/concorde/distribution/guidance.py` joins `realization.distribution.build`.
- **Sections chosen.** spec: "Project terms", "Specs" (spec-validation, grant, registry --write,
  Spec MCP server, translating Spec tooling's error record), task-session terms and Spec tooling's
  errors, block sentence on terms. kernel: "Traces and error chains" (`trace show`, reading a chain).
  worker harness: "Worker models" and its block sentence. execution: "Runs", "Read results",
  "Unbound runs" and the block sentence on unbound runs. workflow: "Workflows" (skill and task
  session, with `workflow_report` taking the workspace `folder` and `workflow_step`) and a block
  sentence. issues: "Issues" (skill and task session; "After a review" conditioned on Method).
  method: "Operations" (order, workers' environment, Module review, reviews with or without Issues,
  brownfield) and the task session's "Method's Operations" (environment, `plan_review`,
  `task-validation`/`delivery`, reviews), block sentence on brownfield. distribution: "Installed
  parts and updates" and a block sentence. Coordination keeps the rest; its delivery and merge text
  now names `task deliver` where Method is absent and `spec-validation` only with the spec part.
- **Spec wording aligned.** Main session's "Guidance by part" table and guidance realization;
  `req.main-session.task-session-quiet-before-validation` and `...-primary-merge` now say
  "validate and deliver" (Method's commands where installed, `task deliver` otherwise);
  Distribution's composed-guidance, glossary-import (only with the spec part), skills-rendered and
  build-owned-outputs (`generated/guidance/`) requirements, build-skills scenario and new
  `scenario.distribution.composed-guidance`; Task sessions' Spec names the composed prompt's path.
- **Test reading.** `tests/concorde/main_session/test_guidance.py` now checks the guidance composed
  of every part (whichever part's section states a rule), and six expectations follow wording that
  became part-aware.

## Report 1 to the main agent (concorde-a2), 2026-10-02T23:56:36Z

parts-guidance delivered: delivery commit d8ba43e4d0c9 on concorde/parts-guidance (work in d4cd0d32). task-validation ready with nothing blocking; build --check ok, spec-validation success (two unlinked-term warnings in distribution/contracts.md:154 and scenarios.md:124 that predate this task), full suite 1015 passed, 5 skipped.

What changed:
- Registration `guidance` is now null or {skill, task_session, claude_md}, each a generated/<path>.md section or null (contract.distribution.part-registration v3).
- Coordination keeps its working method in prompts/main-session/{skill,task-session,claude-md}.md. Each other part has prompts/guidance/<part dir>/: spec (Project terms, Specs, Spec tooling's errors), kernel (Traces and error chains), worker harness (Worker models), execution (Runs, Read results, Unbound runs), workflow (Workflows, workflow_report with `folder`, workflow_step), issues (Issues; "After a review" only where Method is installed), method (Operations, workers' environment, plan_review, task-validation/delivery, reviews with or without Issues, brownfield), distribution (what `concorde` is, part_missing, concorde update). Each section says what happens where a part it mentions is missing. Examples: delivery is Method's `delivery` or else `task deliver`; a merge runs spec-validation only with the spec part; the glossary import comes only with the spec part.
- The new src/concorde/distribution/guidance.py composes each kind: Coordination first, then the parts table order (spec, kernel, worker harness, execution, workflow, issues, method, distribution), sections unchanged and joined by a blank line. The skill gets the front matter, and its description says "main agent" only with coordination. Without coordination there is no task-session prompt. The build composes every part into generated/skills/concorde/SKILL.md and generated/guidance/task-session.md, which `task session` now reads. The installer composes the installed registrations (still every part) into the skill, the CLAUDE.md block, and its Framework copy's generated/guidance/task-session.md. The next task only has to pass the subset.
- This checkout's .claude/skills/concorde reads as one complete guidance. I checked the composed skill and task-session prompt end to end for cross-references between sections. The concorde-development skill still works.
- Specs: Main session's "Guidance by part" table and its sources; the two task-session requirements now say "validate and deliver". Distribution: guidance composition, build, install step 6, and the composed-guidance, glossary-import, skills-rendered and build-owned requirements, plus the build-skills and new composed-guidance scenarios. Task sessions now names the composed prompt's path. Each part's top Module gained a realization.<module>.guidance binding its prompts. docs/using-concorde.md is updated.

My decisions (all recorded in the decision log): the object-shaped `guidance` field; where the sections live; the table order; the installer writing the task-session prompt into the Framework copy; Distribution's section carrying what `concorde` means when Coordination is absent; binding each part's sections to its top Module.

Nothing is open, no escalations, and no Issues are resolved.

## Closed: merged, 2026-10-02T23:56:54Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit d8ba43e4d0c9b03317cd0774742f148e838dc1ac into parts-split and closed it as merged. Nobody answers a report after that.
