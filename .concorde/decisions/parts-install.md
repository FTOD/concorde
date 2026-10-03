# Decision log: parts-install

Goal: Install any subset of Concorde's parts with their dependencies, record the installed parts in the receipt, keep and extend them on update, place only the installed parts' code, files and guidance, and prove each partial installation works without the parts it does not depend on

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

Since this context was first written, every part's code task merged, and the two distribution
tasks before this one: `parts-registrations` (each part's `src/concorde/<dir>/registration.json`,
contract v2 then v3; the `concorde` command, project MCP server and build composed from the
installed parts' registrations; `part_missing` for an absent part's command or tool, naming
`concorde update --parts <part>` and the installer's `--parts`; installed parts = the keys of the
receipt's `parts` object `{part: version}`, every part when the receipt has none or in the source
checkout; `generated/parts.json`) and `parts-guidance` (`concorde.distribution.guidance` composes
the project skill, the task-session prompt and the `CLAUDE.md` block from a set of registrations;
the installer composes for every part today). This is the last task of the refactor.

### What this task does (installer of any part subset)

Read Distribution's Spec (installation, update, `req.distribution.parts-installable`,
`parts-recorded`, `update-installed-parts`, `one-version`, the install and update result contracts),
the root's `req.concorde.part-alone` and `absent-part-stated`, and the four Issues on this task
first.

- **`--parts`**: the installer and `concorde update` take `--parts <part>[,<part>…]`; the installer
  installs exactly those parts with every part they depend on, transitively, and Distribution,
  refusing before any write a name the package does not build (give it a code in the refusal
  table); without `--parts` it installs every part. `concorde update` installs exactly the
  receipt's parts plus every part the new Concorde makes one of them depend on plus `--parts`
  additions.
- **Place only the installed parts**: the Framework copy holds only the installed parts' code
  directories and assets (and Distribution's), so code of a part that is not installed is
  physically absent; ignore rules, permission rules, programs (the pi runtime only with the worker
  harness), install services (the Protocol copy and binding and the docsite template only with the
  spec part), `.mcp.json`, the composed skill, task-session prompt and `CLAUDE.md` block all come
  from the installed parts' registrations only. Concorde's own Python environment gets only the
  third-party dependencies the installed parts need, if they differ.
- **Receipt and results**: the receipt names every installed part with its version
  (`parts: {part: version}`, the shape `parts-registrations` reads); the install and update
  result contracts carry the installed parts (I-f5f3e191, I-42b2f22d) and an update without the
  spec part writes no validation mark and says so (I-b916fce5); bump the fences and their tests.
- **Proof by acceptance tests** (bound by the root's acceptance tests or Distribution's, your
  choice), each installing from this checkout into a fresh temporary Git project and exercising the
  parts through the installed `.concorde/bin/concorde`:
  - spec alone: `spec-validation`, `registry`, `grant`, `docsite`-level smoke; `task`, `run`,
    `issues` refused with `part_missing`;
  - coordination alone (kernel and Distribution come with it): `task open` with plain-label
    Modules, `task deliver --check …`, `task merge`, `task close`, in a project with no Specs;
  - issues alone: report, list, show, close, reopen;
  - execution and workflow without Method: no Operation registered, `run <name>` refused naming it,
    `workflow` reports no registered workflow;
  - worker harness alone: the configuration reader and model map refusals work without Method;
  - method with its dependencies (no coordination, no issues): an unbound or workspace run up to
    the worker launch with a fake worker program as the existing tests use, reviews keeping
    findings in the run result because Issues is absent;
  - every part: as today.
  Each also checks that the installed Framework copy contains no other part's code and that the
  composed guidance holds only the installed parts' sections. Add the root scenarios that
  illustrate a partial installation (I-5c88bfa8), each verified by one of these tests.
- **Develop installs** (`--develop`, Dogfooding) keep working, with `--parts` too.
- Update `docs/` where it describes installing Concorde.

Bound Modules: Distribution and the root (for its scenarios). Nothing runs in parallel with this
task. If a partial installation fails because a part still needs a part it does not depend on, fix
that part (it is a real defect of the refactor) and record it.

## Task session decisions (2026-10-03)

- **What a part ships.** The Framework copy is `concorde.json`, each installed part's code directory
  `src/concorde/<dir>/` and the paths its registration lists under `install.files` (a path ending in
  `/` is a whole directory), nothing else. Distribution lists `scripts/concorde.{py,sh,ps1}`,
  `scripts/install-concorde.py`, `src/concorde/__init__.py`, `__main__.py` and `generated/parts.json`;
  spec `protocol/` and `generated/protocol/`; method `generated/workers/`; issues `scripts/issues.py`;
  worker harness `scripts/available_models.py`. Prompt sources, guidance renders (the installer
  composes them from the package), `scripts/development/`, `scripts/e2e/`, the build manifest and
  Dogfooding's code (used only by the installer from the package) are no longer copied: no runtime
  code reads them from the copy (checked by grepping every package-root read). Reason: "code of a
  part that is not installed is physically absent" needs a per-part list, and `install.files` was
  already the contract's field for it, unused until now.
- **Registration contract v4**: `install.python_dependencies` (method: `langgraph`), `install.files`
  holds framework paths (pattern, `/` for directories), `install.programs` limited to `d2` and
  `pi-runtime`. d2 is placed only with a part naming it (spec), the pi runtime only with the worker
  harness, the Python dependencies (whole runtime lock, all or nothing, then `import <name>` for each
  named one) only where a part names one; otherwise `dependencies` is null.
- **Workflows by part**: a render is placed when the workflow part is installed and every source of
  it under `src/concorde/<dir>/`, as the build manifest records, lies in an installed part's
  directory (brownfield needs method and workflow). Permission rules = `Workflow(<name>)` plus the
  installed parts' `install.permissions` (the workflow part's step-agent rules, formerly the
  installer's constant), only when a workflow is placed.
- **Refusal `unknown_part`** (input): a `--parts` name, a receipt part, or a dependency the package
  does not build. A missing shipped path refuses with `stale_build`.
- **Narrower reinstall** removes files the previous receipt owned that this install no longer places
  (e.g. a dropped part's workflow, the Protocol copy without spec), except any part's Concorde-owned
  default (project data). Idle checks ask the union of the previously installed and the new parts.
- **Update keeps choices without a new receipt field**: d2 / Python dependencies stay left out only
  when the updated install had a part needing them and placed none; a moot opt-out is not recorded,
  so they come with a part added later. `pi_runtime` stays the recorded choice. Receipt without
  `parts` = every part (old receipts). Without the spec part the update neither rebinds nor marks:
  `update` null, `next` only "commit the updated files" (update-result v2, install-result v2 with
  `parts`).
- **`--parts`** takes comma-separated names, repeatable, exact part names (`worker harness` quoted);
  `concorde update --parts` passes them to the installer's `--update`.
- **Scenarios**: Distribution `install-parts`, `install-unknown-part`, `update-installed-parts`,
  `update-without-spec`; root (I-5c88bfa8) `spec-alone`, `coordination-without-method`,
  `method-without-issues` under a new "Installing some of the parts" section. Acceptance tests in
  `tests/concorde/acceptance/test_parts.py`.
- **Defects the partial installs found, fixed in their parts** (brief: "fix that part"):
  (1) Issues refused every project without `.concorde/config.json`, the spec part's configuration,
  so the issues part alone could not work (`not_a_project`). Issues now accepts
  `.concorde/config.json` or the installation receipt `.concorde/install.json` as the project mark
  (`issues/command.py`, Issues interface table and `scenario.issues.command-not-a-project`, test
  extended). (2) Execution's unbound runs need `.claude/worktrees/` ignored
  (`checkout_unavailable`), a rule only Coordination contributed, so Method without Coordination
  could not run an unbound review. Execution's registration now contributes `.claude/worktrees/`
  too (deduplicated), stated in Execution's and Distribution's Specs.
- Acceptance tests (`tests/concorde/acceptance/test_parts.py`, real installs through
  `install()` with uv, exercised through the installed `.concorde/bin/concorde`): spec alone
  (+ update, update --parts issues), coordination alone (open with `module.app` label in a project
  without Specs, `task deliver --check`, `task merge`, `task close --completed`, update without
  spec), issues alone (report/list/show/close/reopen), workflow+execution without Method (`run`
  refused as unknown operation, a workflow step's run refused, no workflow placed), worker harness
  alone (configuration and model map refusals from the copy's own code; available_models), method
  without coordination and issues (unbound `spec_review` keeps the finding, says the issues part is
  not installed). Every one checks the receipt's parts, the copy's code directories, the guidance
  sections and the ignore rules. Distribution CLI tests for `--parts` and `unknown_part`; a develop
  install with `--parts` in Dogfooding's tests. "Every part" stays covered by the existing tests.

## Report 1 to the main agent (concorde-a2), 2026-10-03T00:29:27Z

parts-install delivered: delivery commit 465d0624991f on concorde/parts-install (work in 45f16608 installer and f92118f2 acceptance tests and fixes). task-validation ready; build --check ok; spec-validation success (the two older unlinked-term warnings at distribution/contracts.md:156 and scenarios.md:124 remain); full suite 1024 passed, 5 skipped. Resolves I-f5f3e191, I-b916fce5, I-42b2f22d and I-5c88bfa8, all already on the task.

What changed:
- --parts PART[,PART…], which can be repeated and uses exact part names (quote 'worker harness'), on install-concorde.py and on `concorde update`. Install = the named parts plus everything they depend on, transitively, plus Distribution; every part without --parts. Update = the receipt's parts (every part when the receipt has none) plus the new dependencies plus the --parts additions. A part the package does not build is refused before any write with the new code unknown_part (input).
- The Framework copy holds concorde.json, each installed part's src/concorde/<dir>/ and the paths its registration ships under install.files (a trailing `/` means a directory). Nothing else is copied: no prompt sources, guidance renders, scripts/development or e2e, build manifest or dogfooding code, none of which the copy reads.
- Installed only when an installed part needs them: d2 (spec), the pi runtime (worker harness), the Python dependencies (method's langgraph; `dependencies` is null otherwise), and workflows. A workflow is placed only when the workflow part and every part its sources lie in, per the build manifest, are installed. Its permission rules are Workflow(name) plus the installed parts' install.permissions. Guidance, ignore rules, defaults and idle checks already came from the selected registrations.
- A narrower reinstall removes files the previous receipt owned that it no longer places. Concorde-owned defaults stay.
- Contracts: part-registration v4 (install.python_dependencies; files as framework paths; programs limited to d2 and pi-runtime), install-result v2 (`parts` {part: version}), update-result v2 (`update` is null and `next` is only "commit the updated files" without the spec part, which neither rebinds nor marks). Distribution's Spec, the refusal table, new Distribution scenarios (install-parts, install-unknown-part, update-installed-parts, update-without-spec), root scenarios spec-alone, coordination-without-method and method-without-issues (I-5c88bfa8), and docs/ are updated.
- tests/concorde/acceptance/test_parts.py has six acceptance tests. Each makes a real install (uv venv) from a package copy into a fresh Git project and exercises it through .concorde/bin/concorde: spec alone (+ update, update --parts issues); coordination alone (open, deliver --check, merge, close, update without spec); issues alone (report, list, show, close, reopen); workflow and execution without Method; worker harness alone; method without coordination and issues (an unbound spec_review keeps its finding and says the issues part is absent). Each also checks the receipt's parts, the copy's code directories, the composed skill and CLAUDE.md sections, and the ignore rules. Distribution has CLI tests for --parts and unknown_part, and Dogfooding a test of a develop install with --parts.

Defects the partial installs exposed, fixed in their parts as the brief asks:
(1) Issues refused any project without the spec part's .concorde/config.json (not_a_project), so issues alone could not work. It now accepts config.json or the receipt .concorde/install.json (Issues interface and scenario updated).
(2) Execution's unbound checkouts need .claude/worktrees/ ignored (checkout_unavailable), and only Coordination's registration contributed that rule. Execution now contributes it too (Execution and Distribution Specs say so).

Decisions I took (all in the decision log): the shipped-paths scheme above; the update keeps d2 or the Python dependencies left out only when the updated install had a part needing them and placed none, so a moot opt-out is not recorded and no new receipt field is needed (pi_runtime stays the recorded choice); workflow ownership by build-manifest sources; removal of stale owned files on a narrower reinstall; the unknown_part code.

Open: nothing blocking, no escalations. Note: tests/concorde/tasks/test_store.py, which this task did not touch, fails `ruff format --check`.

## Closed: merged, 2026-10-03T00:29:41Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 465d0624991f26aedba4bee807f06567b5748cef into parts-split and closed it as merged. Nobody answers a report after that.
