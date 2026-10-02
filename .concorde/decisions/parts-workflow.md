# Decision log: parts-workflow

Goal: Make the workflow part generic over Concorde runs: the step output convention carries decision points, decisions and deviations any Operation fills, each workflow names its last step, workflows are registered by the parts that own them, the brownfield workflow and its script are Method's, and the workflow part provides its own workflow_step and workflow_report tools

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

Since this context was first written, `parts-issues`, `parts-worker-harness` and
`parts-coordination` merged too: the issues, worker harness and coordination parts import only the
kernel; Method holds the standard worker sequence (`src/concorde/method/workers.py`) and
`review_issues.py`; Coordination tells an installed part by asking the worktree's `concorde`
whether it offers the part's command (`coordination/tasks/parts.py`) and hands the merge lock on to
`concorde issues`. `parts-execution` runs in parallel with this task: it makes the Operation and
command catalogs list the definitions installed parts register when their code loads (as the kernel
task did for trace roots and typed values), removes Execution's Spec reads and moves
`execution/operations/provider.py` into Method.

### What this task does (workflow)

Read `specs/concorde/workflows/` (module, contracts `contract.workflows.step-output`, requirements)
and `specs/concorde/method/brownfield.md` first.

- **Generic step output.** Workflows owns the step output convention: a run's output may carry a
  `workflow` object (decision points, decisions, deviations, notes) that any Operation or execution
  command fills; the step engine and the report read only that object and the run results, never an
  Operation's own output fields. Remove the Operation-specific knowledge from `workflows/step.py`
  and `workflows/report.py` (open questions and survey decisions as decision points, spec_review
  verdicts, survey's proposed checks, scaffold's children, `LAST_STEP = {"brownfield": "delivery"}`)
  and give it to the Operations that produce it: Method's survey, code_to_spec, scaffold, reviews,
  validation and delivery fill the `workflow` object; the brownfield script reads what it needs from
  each step outcome's `data` and names its last step. Bump the contract fences the tests compare
  (I-26aa6017, I-447cf2f8: `contract.workflows.step`, `step-request`, `result`) and Method's output
  fences (I-9984951d: scaffold record, readiness, adoption and code review outputs gain the
  `workflow` object).
- **Workflows registered by their owners.** The workflow catalog lists the workflows the installed
  parts register when their code loads (name, description, script, last step), the same way the
  execution task registers Operations; Method registers `brownfield`; the build renders the
  registered workflows' scripts (Distribution's build, an existing exception, may load Method's
  registering module until the distribution task replaces that wiring). `brownfield.js` moves to
  Method (bound by Method's realization).
- **Its own tools.** The `workflow_step` and `workflow_report` tool code moves out of
  `distribution/project_mcp/tools.py` into the workflow part (the project MCP server host still
  presents them through its existing wiring, a distribution exception, until the distribution task
  reads registrations). Keep the tools' behaviour and the step agents' contract unchanged.
- The `workflow` part may import only execution and the kernel; remove every exception this makes
  stale.

Bound Modules: Workflows, and Method's Modules whose outputs or scripts change. The execution task
runs in parallel on `execution/` and Method's provider registration; where you meet it in one file
keep yours minimal, and if the merge conflicts, the main agent will ask you to merge `parts-split`
in.

## Task session decisions (2026-10-03)

1. **Contract versions.** `contract.workflows.step` v6 (drops `created_modules` and `ready`; adds the
   run's declared `blocking` and `data`; `decision_points` counts declared points not settled),
   `step-request` v6 (answer ids follow the convention's generic `<prefix>.<name>` pattern instead of
   `d.`/`q.` only), `result` v8 (drops `open_questions`, `reviews`, `proposed_checks`; lists the
   declared `decisions`, `decision_points`, `deviations` and `notes` with step and run; `pending`
   has the convention's point shape). Method's fences gain a required `"workflow": {"type":
   "object"}` whose fields the convention defines (decomposition v7, spec-description v5, scaffold
   record v3, readiness v7, spec-review payload v6, panel payload v5, code-review review v5). Reason:
   the brief and I-26aa6017/I-447cf2f8/I-9984951d; the Method fences say "the convention, not this
   contract, defines its fields", so they do not copy its schema.
2. **Code layout.** `workflows/output.py` holds the step output convention (schema, `declared`,
   `step_output` builder); `workflows/tools.py` the `workflow_step`/`workflow_report` tool code;
   Method's `src/concorde/method/brownfield/` (`__init__.py` registering, `brownfield.js`), bound by a
   new realization `realization.method.brownfield` ("Brownfield procedure", since the title
   "Brownfield workflow" is the concept's). Review notes are built by `review_issues.review_output`.
3. **Last step at render.** Claude Code's workflow `meta` admits only name, description, whenToUse
   and phases, so the build renders the registered last step as a constant `LAST_STEP` beside
   `WORKFLOW` instead of a `meta` field; Workflows' module text and req.workflows.last-step say so.
   The report reads the last step from the catalog; a workflow no installed part registers is
   reported `failed`/`incomplete` saying so. The adapter no longer requires `args.module` (the
   brownfield script checks its own argument).
4. **Registration wiring.** Until Distribution reads part registrations, `distribution/build.py` and
   the `workflow` branch of `distribution/cli.py` import `concorde.method.brownfield` to register it
   (two new entries in the distribution exception group, as the brief allows for the build and as
   the `trace` branch already does); `distribution/project_mcp/tools.py -> workflows.step` became
   `-> workflows.tools`.
5. **`workflow_report` takes `folder`, not `task`.** The brief said to keep the tools' behaviour, but
   the merged Spec (contracts "MCP tools") gives `workflow_report` an optional absolute workspace
   `folder` (default: the session worktree's binding) and answers `{folder, number, path, report}`,
   and req.workflows.no-task forbids Workflows to read a task record, which the old `task` argument
   needed. Implemented the Spec; the main agent passes `<task folder>/workspace` from `task_show`.
6. **Validation status.** req.validation.step-output said a not-ready run ends `ok`, while
   Validation's module, scenarios and code end it `blocked`. Kept `blocked` and reworded the
   requirement and the readiness prose: every run that decided a readiness carries the `workflow`
   object (`data.ready`, `blocking` when not ready). The report treats a declared `blocking` on the
   last step as `blocked` whatever the status.
7. **Invalid convention object.** A finished run's `workflow` object that breaks the convention makes
   `concorde workflow step` answer a `component` link `invalid_step_output` (reason `input`) and the
   report `report_failed`; added to the contracts' error text.
8. **Survey decisions.** Every decision is listed under `decisions`, and the worker-taken ones also
   as decision points with the same identity, as the convention requires.

## Report 1 to the main agent (concorde-a2), 2026-10-02T22:28:06Z

parts-workflow delivered: delivery commit 11c38fd45c8e2fd74ddfade0dcf94fdf1904782f on concorde/parts-workflow (work commit 1be936b0). Verified: build --check ok, spec-validation ok (0 findings), full suite 1003 passed / 5 skipped, task-validation ready, smoke runs of `workflow report`, `workflow step --json` and the project-mcp `workflow_step`/`workflow_report` calls.

What changed:
- Workflows reads only the `workflow` object of a run's output (new workflows/output.py: contract.workflows.step-output schema, `declared`, `step_output`). step.py/report.py have no Operation knowledge left (no survey/scaffold/spec_review/task-validation names, no LAST_STEP table). Fences bumped: contract.workflows.step v6 (created_modules/ready replaced by the declared `blocking` and `data`), step-request v6 (generic answer ids), result v8 (decisions, decision_points, deviations, notes, pending in the convention's shapes; open_questions/reviews/proposed_checks gone).
- Workflow catalog is a registry (`catalog.register(Workflow(...))`); Method registers `brownfield` (last step `delivery`) from the new package src/concorde/method/brownfield/ (registering __init__.py + brownfield.js, moved there), bound by new realization.method.brownfield. The build renders the registered last step as `const LAST_STEP` beside `WORKFLOW` (Claude Code's meta takes only name/description/whenToUse/phases); the report reads it from the catalog, and a workflow no installed part registers is reported failed/incomplete saying so. The adapter no longer requires args.module.
- Method fills the object: survey (worker decisions and open questions as points, all decisions, proposed checks as `proposed-check` notes), code_to_spec (questions as points, decisions, deviations), scaffold (`data.created_modules` with uses), task-validation (`data.ready`, `blocking` not_ready), spec_review / spec_panel / code_review (one `review` note). Method fences bumped (decomposition v7, spec-description v5, scaffold record v3, readiness v7, spec-review payload v6, panel payload v5, code-review review v5), each with `"workflow": {"type": "object"}` as their prose says the convention defines its fields.
- workflow_step/workflow_report code moved to src/concorde/workflows/tools.py; distribution/project_mcp/tools.py presents them via its existing wiring.
- Part-dependency exceptions (distribution group only): `project_mcp/tools.py -> workflows.step` became `-> workflows.tools`; added `distribution/build.py -> method.brownfield` and `distribution/cli.py -> method.brownfield` (the dispatcher's `workflow` branch loads Method's registration, as its `trace` branch already does for trace roots), to be replaced when Distribution reads part registrations. The workflow part imports only execution and kernel.

Decisions taken on your behalf (all in the decision log, entries 1-8):
1. `workflow_report` now takes an optional absolute `folder` (default: the session worktree's binding's workspace folder) and answers {folder, number, path, report}, not `task`. The brief said keep tool behaviour, but the merged Spec's MCP tools table says folder, and req.workflows.no-task forbids Workflows to read a task record, which the `task` argument needed. The main agent passes `<task folder>/workspace` from task_show. Prompts/main-session/skill.md (Coordination's) lists the tool without arguments, so nothing there needed changing.
2. req.validation.step-output said a not-ready task-validation ends `ok`, but Validation's module, scenarios and code end it `blocked`. Kept `blocked`; reworded the requirement and readiness prose: every run that decided a readiness carries the object.
3. A `workflow` object breaking the convention: step command answers `invalid_step_output` (component, input), report answers `report_failed`; added to the Errors text.
4. Survey lists every decision under `decisions` and worker-taken ones also as decision points (same id), as the convention requires.

Issues resolved by this task (already on its resolves list): I-26aa6017, I-447cf2f8, I-9984951d.

Merge note: parts-execution changes execution/commands/catalog.py, which step.py still imports as `COMMANDS` to tell commands from Operations; I left that line unchanged so a conflict should stay small. Nothing is open for the developer.

## Closed: merged, 2026-10-02T22:28:30Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 11c38fd45c8e2fd74ddfade0dcf94fdf1904782f into parts-split and closed it as merged. Nobody answers a report after that.
