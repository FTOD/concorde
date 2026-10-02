# Decision log: parts-execution

Goal: Make the execution part depend on the kernel alone: catalogs assembled from the definitions installed parts register, no Spec reads in the runner, Check execution generic with its Spec-aware selection in Method, and Method's remaining code moved out of Execution

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

Since this context was first written, `parts-issues` and `parts-worker-harness` merged too: the
issues and worker harness parts import only the kernel; Method holds the standard worker sequence
(`src/concorde/method/workers.py`, its `operation(...)` helper, admission, grant projection,
instructions, round validation) and `review_issues.py`; Execution no longer launches workers
(`Provider.runtime_paths` resolver). `parts-coordination` runs in parallel with this task (on
`coordination/`, the Issue store's in-process `locked=True` path, Tasks' tests).

### What this task does (execution)

Read `specs/concorde/execution/` (module: run result, Modules as names, unbound runs, "Three children,
and the parts around them"; runner.md; Operations; Commands; Check execution) and Method's root first.

- **The execution part depends on the kernel alone.** Remove the remaining `execution` group of
  `KNOWN_EXCEPTIONS` (`checks/checks.py -> spec.*`, `commands/catalog.py -> method.*`,
  `context.py -> spec.errors`, `operations/catalog.py -> method.*`, `runner.py -> spec.*`).
- **Catalogs from registered definitions.** The Operation catalog and the command catalog list the
  definitions the installed parts register; Execution provides no definition of its own. Do it the
  way the kernel task did trace roots and typed values: a part registers its definitions when its
  code loads (Method registers its Operations and its execution commands `task-validation`,
  `delivery`, `scaffold`); two parts registering one name are refused naming both. Until the
  distribution task gives the parts registrations, Distribution's CLI (already an exception) loads
  Method's registering module before it dispatches `run` or an execution command, including in a
  detached runner process; keep that wiring minimal and obvious for the distribution task to
  replace. An Operation or command no installed part registers is refused naming it.
- **No Spec reads in Execution.** The runner treats a run's Modules as names (`--modules` or the
  binding's); checking them against the Specs (leaving out the binding's Modules the workspace no
  longer registers, refusing a named one it does not) is Method's admission, as Execution's Spec
  says. `context.py`'s `spec_cause` and the runner's Spec loading move to Method.
- **Check execution is generic**: running a Module's configured checks in the read-only check
  boundary and recording check results, with the checks file format `.concorde/checks/<module>.json`
  its own; which Modules' checks a change needs (bound files, the impact index, verification
  declarations) is Method's (Validation and the round validation) and moves there.
- **Method's remaining code in Execution** (`execution/operations/provider.py`, the prompt and brief
  helpers of worker-backed providers) moves into `src/concorde/method/`, with the Specs' realization
  paragraphs saying so.
- **Issues** on the task: I-a673d832 (the Operations framework overrides a provider's
  classification of residual validation; restrict mandatory `failed` to hard execution failures and
  validation designated to fail the run, leaving the rest to the providing Operation's contract) and
  I-9669db1a (worker-sequence scenarios still in Operations and checks-file scenarios still in Spec
  core: move each scenario to its owner — Method, Check execution — with its tests' `verifies`).

Bound Modules: Execution, Operations, Commands, Check execution, and Method's Modules where code
lands. Coordination's task, in parallel, does not touch these; if you meet it in one file, keep
yours minimal there.

## Task session decisions (2026-10-03)

- **Catalogs.** `execution/operations/catalog.py` holds a small `Catalog` (definitions by name with
  the part that registered each); `OPERATIONS` and Commands' `COMMANDS` are its two instances.
  `register(part, definition)` accepts the same definition again and refuses another one under a
  registered name with `duplicate_definition`, naming both parts; a definition of the other kind is
  refused too. Method registers in `src/concorde/method/registration.py`, which imports its
  providers and registers every Operation and command when it loads.
- **Distribution wiring (minimal, for the distribution task to replace).** `distribution/cli.py`
  imports `concorde.method.registration` before it dispatches `run`, an execution command or
  `workflow` (whose steps tell commands from Operations by the command catalog), through one helper.
  This adds `("distribution/cli.py", "method.registration")` to the distribution group of
  `KNOWN_EXCEPTIONS`: the brief asks for exactly this import, and the distribution group is where its
  remaining reason belongs (Distribution reaches parts only through registrations). The detached
  runner is started as the host's `concorde` command (`python -m concorde [run] <name> …`), so it
  loads the registrations the same way; `runner.py` loses its `__main__` entry.
- **Module admission.** The runner sets the run's Modules as names (`--modules`, else the binding's,
  else none) and calls the definition's `admit` after admitting the inputs (runner.md row 4 order).
  A definition's admission refuses by raising `execution.context.Refused`, which carries its own
  code, actor, reason, explanation and options; the runner makes it the usual `refused` result.
  Method's admission (`method/specs.py`, with `spec_cause`/`spec_finding` moved there) does what the
  runner did: drop removed binding Modules with `removed-module` evidence, `modules_removed`,
  `specs_unloadable`, `unknown_module`; `requires_loaded_specs` becomes the admission's
  `diagnoses_specs` flag (task-validation, delivery).
- **Check execution generic.** `run_checks(worktree, *, modules, trace_directory, measured=None,
  tests=None, python=None, stage, kinds)` as the check service Spec states; it reads and validates
  the checks files itself (`configured_checks`, `validate_checks`) and has its own `CheckError`.
  Method's Spec-aware selection (`checked_modules`, `affected_modules`, `verified_tests`, the
  implementation files measured, the configured `python`) moves to `src/concorde/method/checks.py`,
  whose `run_module_checks` every Method caller uses.
- **Provider helpers.** `execution/operations/provider.py` moves to `src/concorde/method/prompts.py`.
- **Non-ok smoke run.** `r-20261002T220213-task_validation-97d14bce` (a detached `task-validation`
  started to smoke the detached runner's new `python -m concorde` entry) ended `failed` with
  `inputs_changed`: I was editing the worktree while it ran. The detached path itself worked (it
  loaded Method's registrations and ran the checks); no action needed.
- **I-9669db1a.** The eleven worker-sequence scenarios move from `execution/operations/scenarios.md`
  to a new Method document `specs/concorde/method/scenarios.md` as `scenario.method.*`; Operations'
  scenarios now show its catalog (`scenario.operations.registered`, `scenario.operations.unique-names`).
  Spec core's `scenario.spec.checks-files` and `scenario.spec.check-input-missing` become Check
  execution's `scenario.checks.checks-files` and `scenario.checks.check-input-missing`, verified by
  the check service tests.
- **I-a673d832.** `req.operations.status-mapping` now makes `failed` mandatory only for hard
  execution failures and for round validation that designates its report a failure (a check still
  failing); other residual validation is the providing Operation's to classify (Adoption's
  `blocked`). The worker harness already behaved this way (`RoundValidation.failure` vs `repair`),
  so the change is the Spec's alone.
- **New scenario `scenario.execution.modules-as-names`** shows the runner reading no Spec for a
  definition without admission, and Method's admission refusing an unregistered named Module with
  its own link (`Method (Module admission)`), since that is the behaviour this task introduces.
- **Spec core's leftover reading of checks files** (its code still reads `.concorde/checks/`,
  exposes check ids and reports `CONCORDE-CHECK-001`, although its Spec says the spec part reads no
  other part's format) is outside this task's Modules: reported as Issue
  I-232a51ae40ca5d2c86f15cf6fdd0518f (module.spec, obvious-fix, low). Its tests keep running
  without the moved scenarios' `verifies`.
- Both task Issues are added to the task with `task resolve`; verification: `build --check`,
  `spec-validation` (0 findings), full suite 999 passed, CLI smoke runs (unknown Operation,
  `run <command>`, `task-validation --modules`, a detached `task-validation`).

## Report 1 to the main agent (concorde-a2), 2026-10-02T22:20:57Z

parts-execution delivered: delivery commit bcbeb0df (on 2d84c2de) on concorde/parts-execution; task-validation ready; build --check, spec-validation (0 findings) and the full suite (999 passed) green. Ready to merge.

What changed
- The execution part imports only the kernel: the whole `execution` group of KNOWN_EXCEPTIONS is gone.
- Catalogs from registered definitions: execution/operations/catalog.py has a small `Catalog` (OPERATIONS; Commands' COMMANDS has the same shape). `register(part, definition)` accepts the same definition again and refuses another under a registered name with `duplicate_definition`, naming both parts. Method registers its 10 Operations and 3 commands in src/concorde/method/registration.py when it loads. An Operation or command no installed part registers is a command-line error naming it.
- Distribution wiring (minimal, for the distribution task to replace): distribution/cli.py `load_definitions()` imports method.registration before `run`, an execution command or `workflow` (workflow steps tell commands from Operations by the command catalog). This adds ("distribution/cli.py", "method.registration") to the distribution group of KNOWN_EXCEPTIONS. The detached runner is now `python -m concorde [run] <name> …` (the host's concorde command), so it loads the registrations the same way; runner.py has no __main__ entry any more.
- No Spec reads in the runner: the runner takes the Modules as names and calls the definition's `admit` after admitting the inputs; an admission refuses by raising execution.context.Refused (own code, actor, reason, options). Method's admission (method/specs.py, which also takes over spec_cause/spec_finding) does what the runner used to do: removed-module, modules_removed, specs_unloadable, unknown_module. The cause actor is now `Method (Module admission)`. `requires_loaded_specs` became `admission(diagnoses_specs=True)` (task-validation, delivery).
- Check execution is generic, as service.md states: run_checks(worktree, *, modules, trace_directory, measured, tests, python, stage, kinds); it reads and validates its own checks files (configured_checks, validate_checks) and has its own CheckError (no longer a SpecError). Method's Spec-aware selection (affected/checked Modules, implementation files, verified tests, the configured python) is in src/concorde/method/checks.py `run_module_checks`, which every Method caller uses.
- execution/operations/provider.py moved to src/concorde/method/prompts.py. Realization paragraphs and metadata follow (new realization.method.definitions; Operations' realization is now "Catalog"); Commands and runner.md say how a definition's admission refuses.

Issues
- Resolves (added with task resolve): I-a673d83201615619b5987484a0a57374 (req.operations.status-mapping makes `failed` mandatory only for hard failures and for validation designated to fail the run; anything else is the providing Operation's to classify; the code already behaved this way) and I-9669db1a5a835db9b880fadb89b0a112 (the 11 worker-sequence scenarios moved to a new specs/concorde/method/scenarios.md as scenario.method.*; Operations' scenarios now cover its catalog; scenario.spec.checks-files and check-input-missing became scenario.checks.checks-files and scenario.checks.check-input-missing, with new tests).
- New: I-232a51ae40ca5d2c86f15cf6fdd0518f (module.spec, obvious-fix, low). Spec core's code still reads .concorde/checks/, shows check ids and reports CONCORDE-CHECK-001, although its Spec leaves the checks files to Check execution. That is outside this task's Modules.

Decisions I made (also in the decision log)
- The order is inputs first, then Module admission, as runner.md row 4 says (it used to be the other way round).
- I added scenario.execution.modules-as-names with a test, for the new runner behaviour.
- One smoke run that was not ok: a detached task-validation ended inputs_changed because I was editing the worktree while it ran. The detached path itself worked.

Open: nothing for this task. No escalations.

## Answer to report(s) 1 of the task session, 2026-10-02T22:21:50Z

Merge refused with merge_conflict in tests/concorde/development/test_part_dependencies.py (parts-coordination merged first: it removed the coordination group and coordination/tasks/merge.py -> distribution.install). Merge the primary branch parts-split into concorde/parts-execution, resolve keeping both tasks' removals and your distribution-group entry for method.registration, run build --check, spec-validation and the full suite, then task-validation and delivery again, and report.
- **Merge of parts-split (main agent's answer to report 1, merge_conflict).** Merged parts-split
  into concorde/parts-execution (83377f55). The one conflict, `KNOWN_EXCEPTIONS` in
  tests/concorde/development/test_part_dependencies.py, resolved by dropping both the coordination
  group (removed by parts-coordination) and the execution group (removed here), keeping the
  distribution group with parts-coordination's removal of `coordination/tasks/merge.py ->
  distribution.install` and this task's `distribution/cli.py -> method.registration`. Coordination's
  new code reaches Execution and Method only through the `concorde` command, which still loads
  Method's registrations first. Verified: build --check, spec-validation (0), full suite 1005 passed.
- **Second merge of parts-split (after parts-workflow merged).** The task-validation started after
  the first merge was stopped before it finished (its input was about to change). Merged parts-split
  again (2e1275b0). Conflicts resolved keeping both tasks' changes: Method's metadata holds both
  `realization.method.definitions` and parts-workflow's `realization.method.brownfield`;
  distribution/cli.py's `workflow` branch calls `load_definitions()` and imports
  `method.brownfield`; KNOWN_EXCEPTIONS' distribution group lists both `distribution/cli.py ->
  method.brownfield` and `-> method.registration`. workflows/step.py and store.py keep using
  `COMMANDS` (`in` and iteration work on the catalog); the project MCP server's workflow_step still
  runs `concorde workflow step`, which loads the registrations. Verified: build --check,
  spec-validation (0), full suite 1011 passed.

## Report 2 to the main agent (concorde-a2), 2026-10-02T22:43:48Z

parts-execution delivered again: delivery commit 8c035284, on top of merge 2e1275b0 of the current parts-split (after parts-coordination and parts-workflow), on concorde/parts-execution. task-validation ready; build --check, spec-validation (0 findings) and the full suite (1011 passed) green. Ready to merge. This answers your answer to report 1 and your update after it.

Conflict resolutions, keeping both tasks' changes:
- tests/concorde/development/test_part_dependencies.py: the coordination group and the execution group are both gone. The distribution group keeps parts-coordination's removal of merge.py -> distribution.install, parts-workflow's build.py/cli.py -> method.brownfield and project_mcp/tools.py -> workflows.tools, and this task's cli.py -> method.registration.
- src/concorde/distribution/cli.py: the workflow branch calls load_definitions() (Method's registrations, for the command catalog) and imports method.brownfield, as parts-workflow added.
- specs/concorde/method/module.md.json: holds both realization.method.definitions (this task) and realization.method.brownfield (parts-workflow).
- workflows/step.py and store.py keep using COMMANDS unchanged: `in` and iteration work on the new catalog. The project MCP server's workflow_step still runs `concorde workflow step`, which loads the registrations first.

I stopped the task-validation started after the first merge before it finished, because the second merge would have changed its input. Everything is in the decision log.

Issues: unchanged from report 1. The task resolves I-a673d83201615619b5987484a0a57374 and I-9669db1a5a835db9b880fadb89b0a112; I-232a51ae40ca5d2c86f15cf6fdd0518f (module.spec) is filed for later.

Open: nothing. No escalations.

## Closed: merged, 2026-10-02T22:44:03Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 8c035284c93823ab120c9924e226554c2ce41eb2 into parts-split and closed it as merged. Nobody answers a report after that.
