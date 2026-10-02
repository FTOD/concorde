# Decision log: parts-layout

Goal: Relocate Concorde's Python code into one directory per part under src/concorde/ with no behaviour change, and add a part-dependency check whose known exceptions the later code tasks remove

## Brief (main agent, 2026-10-03)

### Context

The developer decided (2026-10-03) to split Concorde into independently installable parts; task
`parts-spec` rewrote the Specs accordingly and is merged on the integration branch `parts-split`
(the primary worktree is on it; this task merges there, never into `main`). The Specs now describe
nine parts (root `specs/concorde/module.md`, "The parts"; Distribution's "Parts and their
registrations") and the dependency directions between them (`req.concorde.part-dependencies`). The
code still has the old layout. This is the **first code task, purely mechanical**: it moves the
Python code into one directory per part so that every later code task works on a stable layout and
the import directions can be checked by directory. It changes no behaviour.

Later code tasks, in this order (each its own task, after this one merges): kernel; issues and
worker harness; execution; workflow; method; coordination; distribution (registrations, command
dispatcher, project MCP server host, installer of any part subset, composed guidance).

### Decided by the main agent: the target layout

One Python directory per part under `src/concorde/`, child Modules as subpackages or files inside it:

| Part | Directory | Moves into it |
| --- | --- | --- |
| kernel | `src/concorde/kernel/` | `concorde/errors.py`, `concorde/tracing/` (as `kernel/tracing/`) |
| spec | `src/concorde/spec/` | Spec core stays where it is; `concorde/spec_mcp/` -> `spec/mcp/`, `concorde/views/` -> `spec/views/` |
| worker harness | `src/concorde/worker_harness/` | today's `concorde/harness/` files of Harness and Workers (incl. `pi_permission.ts`, `pi_policy.ts`) |
| execution | `src/concorde/execution/` | stays; `concorde/operations/` -> `execution/operations/`, `concorde/commands/` -> `execution/commands/`, Check execution's `harness/check_executor.py`, `timing.py`, `checks.py` -> `execution/checks/` |
| workflow | `src/concorde/workflows/` | stays |
| issues | `src/concorde/issues/` | stays |
| coordination | `src/concorde/coordination/` | `concorde/tasks/` -> `coordination/tasks/` |
| method | `src/concorde/method/` | `understanding/`, `specification/`, `implementation/`, `code_review/`, `spec_review/`, `adoption/`, `validation/`, `delivery/`, `scaffold/` |
| distribution | `src/concorde/distribution/` | stays, with `concorde/__main__.py`; `concorde/project_mcp/` -> `distribution/project_mcp/` (the Specs make the project MCP server Distribution's host; its tools are untangled in later tasks) |

`src/concorde/dogfooding/` (a developer Module, not a part) stays. Non-Python assets (`prompts/`,
`protocol/`, `docsite/`, `scripts/`) stay where they are; each part's registration will name them
in the distribution task. Deviate from a row only with a recorded reason (e.g. a name clash).

### What the task does

- Move the files with `git mv`, and rewrite every reference: absolute and relative imports
  (including function-level ones), tests, `scripts/` entry points, the build, the installer (it
  ships `src` and places e.g. the pi runtime and the `.ts` permission files), path strings in code
  and prompts, `pyproject.toml`/pyright paths, CI workflows, docs that name source paths.
- **No compatibility re-exports** at old paths (rapid-iteration rule): every importer is updated.
- Update every realization's bound entries in the Specs to the new paths and the Spec text that
  names source paths, then `registry --write`. Where a Module's directory entry would now swallow a
  child Module's directory (e.g. `module.execution` binding `src/concorde/execution/` while
  Operations, Commands and Check execution live inside it, or Kernel and Tracing), bind explicit
  files or the Module's own subdirectory instead, so that no file becomes shared by accident.
- **Part-dependency check.** Add a test (bound where you judge best, e.g. the root's development
  environment or Distribution) that maps each part directory above to its part, parses every
  `concorde.*` import of `src/concorde/` (AST: module-level and function-level, absolute and
  relative) and checks it against the allowed directions of the root's parts table (spec: none;
  kernel: none; worker harness, execution, issues, coordination: kernel; workflow: execution,
  kernel; method: spec, worker harness, execution, workflow, kernel, issues as an optional
  integration; distribution: none, reached only through registrations — until the distribution task
  exists, list its imports as exceptions too). Today's violations are listed explicitly as known
  exceptions, each with the later code task expected to remove it (kernel, issues, worker harness,
  execution, workflow, method, coordination, distribution). The test fails on any import not
  allowed and not listed, and on any listed exception that no longer occurs, so the list can only
  shrink and the last code task empties it.
- Verify: `build --check`, `spec-validation`, the full suite (`.venv/bin/python -m pytest`), and a
  smoke run of `python3 scripts/concorde.py --help`, `task list`, `issues list` and `trace show`
  on some history task from the task worktree. Then `task-validation` and `delivery`, and report.

Left to the task session: the test's file name and binding, how the exception list is kept, any
naming detail the table leaves open. Escalate only if the layout above cannot work as stated.

## Task session decisions (2026-10-03)

- **Tests stay where they are.** `tests/concorde/` keeps its layout (e.g. `tests/concorde/harness/`,
  `tests/concorde/tasks/`); only their imports and path strings change. The brief moves code, and
  the tests' realization entries stay valid, so moving them would add churn with no gain.
- **`src/concorde/__main__.py` stays at the package root.** `python -m concorde` is used by the
  task merge's default check, workflow steps, the project MCP server and tests; moving it into
  `distribution/` would change that behaviour. The part-dependency check counts it as
  Distribution's; `src/concorde/__init__.py` (bound by Spec core) belongs to no part.
- **Part directories without code of their own are namespace packages.** `src/concorde/kernel/`,
  `src/concorde/method/` and `src/concorde/coordination/` get no `__init__.py`, so no new file
  needs binding in Modules that bind no code yet (Kernel, Method, Coordination); the later code
  tasks that give those parts code may add one. `src/concorde/execution/checks/` gets an
  `__init__.py`, and Check execution's runner now binds that directory, its own subdirectory.
- **`checks.py` keeps its name** as `src/concorde/execution/checks/checks.py` (row as stated).
- **Execution binds its own files explicitly** (`__init__.py`, `binding.py`, `checkout.py`,
  `context.py`, `runner.py`, `runs.py`) instead of `src/concorde/execution/`, which would now
  swallow Operations, Commands and Check execution.
- **Spec text** naming source paths updated; Kernel's "Code", the Harness package, Execution's
  runner and Operations' catalog paragraphs now say where the code is after this move. Historical
  records (`.concorde/decisions/`, closed Issues) are left unchanged.
- **Part-dependency check** is `tests/concorde/development/test_part_dependencies.py`, bound by the
  root's development environment (its `tests/concorde/development/` entry) and described in
  `specs/concorde/development.md` ("Part dependency check"). It reads the allowed directions from
  the root's parts table, treats method -> issues as the one listed optional integration, counts
  `__main__.py` as Distribution's and `dogfooding/` as no part (nothing may import it, it may import
  nothing), and also checks the `"module:attribute"` strings the Operation and command catalogs
  import by name. Exceptions are kept per (importing file, imported module), grouped by the code
  task expected to remove them: imports of the kernel formats still implemented elsewhere
  (`spec.schema`, `spec.typed_data`, `spec.changes`, `execution.binding`,
  `method.delivery.commits`) under `kernel`; anything into or out of Distribution or Dogfooding
  under `distribution`; every other one under the importing part's own task. Workflow and Method
  have none today. 115 exceptions in all.

## Report 1 to the main agent (concorde-a2), 2026-10-02T20:40:56Z

parts-layout delivered: delivery commit 998c2328 on concorde/parts-layout (steps 21750f90 relocation, 2717030c part-dependency check). Code moved per the brief's table with git mv; every import (module/function level, relative/absolute), catalog string, mock target, __file__ depth, check input (.concorde/checks/module.tracing.json), e2e scenario path and Spec binding/text updated; no compatibility re-exports. Verified: build --check ok, spec-validation success with no findings, full suite 968 passed / 5 skipped, smoke of --help, task list, issues list, trace show adoption-output-paths ok, task-validation ready. Decisions taken (all in the decision log): tests/ stay in their layout; src/concorde/__main__.py stays at the package root so python -m concorde keeps working (counted as Distribution's by the check); kernel/, method/, coordination/ are namespace packages (no __init__.py) so Modules that bind no code yet need no new binding; execution/checks/ gets an __init__.py and Check execution binds that directory; Execution's runner now binds its six own files explicitly; checks.py keeps its name. Part-dependency check: tests/concorde/development/test_part_dependencies.py, bound by the root's development environment and described in specs/concorde/development.md; reads allowed directions from the root's parts table, method->issues is the one optional integration, also checks catalog 'module:attribute' strings, fails on unlisted violations and on stale exceptions. 115 known exceptions keyed by (file, imported module): kernel 25 (imports of spec.schema/typed_data/changes, execution.binding, method.delivery.commits), issues 4, worker harness 7, execution 28, coordination 8, distribution 43 (incl. distribution->dogfooding); workflow and method have none. Nothing open; no escalations; no Issues resolved or reported.

## Closed: merged, 2026-10-02T20:41:15Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 998c2328e25c2b128e0d510a66830d4550886638 into parts-split and closed it as merged. Nobody answers a report after that.
