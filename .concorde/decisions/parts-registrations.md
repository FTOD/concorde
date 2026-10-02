# Decision log: parts-registrations

Goal: Give every part its part registration and compose the concorde command, the project MCP server and the build from the registrations of the installed parts, so that Distribution imports no part except through registration entries and an absent part's commands and tools are refused naming it

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

Since this context was first written, every other code task merged: `parts-issues`,
`parts-worker-harness`, `parts-coordination`, `parts-execution` and `parts-workflow`. Every part but
Distribution now imports only the parts it depends on; `KNOWN_EXCEPTIONS` holds only the
`distribution` group (Distribution's own imports of parts, and the temporary wiring the other tasks
left for this one: `distribution/cli.py` loading `method.registration` and `method.brownfield`
before `run`, execution commands and `workflow`, loading Tasks and Execution so their trace roots
register before `trace`, `distribution/build.py` loading `method.brownfield`, and the project MCP
server importing the tools' code). Parts register what their code provides when it loads (typed
value types, trace roots, Operation and command definitions, workflows). Coordination tells an
installed part by asking the worktree's `concorde` whether it offers the part's command
(`coordination/tasks/parts.py`, accepting `part_missing` or `part_not_installed` or argparse's
`invalid choice`); Method's `review_issues._absent` expects `part_not_installed` with exit 2 on
stderr, which today's dispatcher never produces. This is the first of two distribution tasks; the
second, after it, does the installer of any part subset, the receipt and update, the composed
guidance and partial-install acceptance tests.

### What this task does (registrations)

Read `specs/concorde/distribution/` (module "Parts and their registrations", "Commands named by their
owner", "The project MCP server", "Why the parts reach Distribution only through registrations";
contracts `contract.distribution.part-registration`; requirements `parts-*`, `registration-only`,
`composed-from-registrations`, `absent-part-named`, `unique-names`, `mcp-*`) first.

- **A registration per part**, plain data in the registration contract's shape, inside each part's
  own directory and importing nothing (e.g. a JSON file): spec, kernel, worker harness, execution,
  workflow, issues, coordination, method (and Distribution's own commands `build`,
  `protocol-manifest`, `update`, `project-mcp`). Extend the contract where the code needs it and
  the Spec is silent, e.g. how the host loads a part's code so it registers its types, trace roots,
  definitions and workflows, and the installer services I-5cb4068f names (Protocol preparation,
  docsite template validation, installed-file binding), each conditional on its part being
  installed. Bump the contract version and record each addition.
- **Which parts are installed**: in this source checkout every part the package builds; in an
  installed project the parts the receipt names (the second task writes that list; read it now,
  treating a receipt without one as every part, with no compatibility beyond that).
- **The `concorde` command composed from registrations**: routes each command to its part's entry,
  loading the installed parts' code that registers things first; refuses a command a part of the
  package registers but the project has not installed with **one** stable code, `part_missing`,
  naming the part and how to install it (`req.distribution.absent-part-named`); align
  `coordination/tasks/parts.py` and `method/review_issues.py` to exactly that refusal (code, exit
  status, where the link is printed) and drop the other spellings they accept.
- **The project MCP server host presents the registered tools**: each tool's code lives in the part
  that registers it (Coordination's `task_*`, `task_merge`, `locks`, `register_wait`, `trace_show`,
  `run_result` where execution is installed; Issues' `issue_*`; Workflows' `workflow_step`,
  `workflow_report`, already in `workflows/tools.py`); the host keeps its own promises (current code
  per call, the session's worktree for `worktree: session` tools, lock hand-off for `long_work`,
  watching and waking) unchanged.
- **The build** renders the registered parts' guidance and workflows and fails when two parts
  register one command or tool name.
- **Distribution depends on no part**: remove the whole `distribution` group of `KNOWN_EXCEPTIONS`
  (including `install.py -> dogfooding.develop`, `project_defaults.py`, `prompt_resolver.py`).
  Distribution reaches a part's code only through the entries its registration names (dynamic
  import by entry is Distribution's privilege, `req.distribution.registration-only`); where it needs
  a format of another part (an error link, a typed value) it meets that format itself, as the spec
  part does. Extend the part-dependency test so it also checks that every registration entry points
  into the registering part's own directory and that `KNOWN_EXCEPTIONS` ends empty (delete it).
- **I-232a51ae**: Spec core stops reading `.concorde/checks/` (the checks files are Check
  execution's): remove its checks reading, the Module descriptor's `checks` field, the Spec MCP
  contract's checks and `CONCORDE-CHECK-001`, with the spec Specs and tests.
- Keep the guidance text itself as it is (the next task splits it per part), but make the build
  render each part's registered guidance path.

Bound Modules: Distribution, and each part's top Module where its registration lands. Nothing runs in
parallel with this task.

## Task session decisions (2026-10-03)

- **Registration files.** Each part's registration is `src/concorde/<directory>/registration.json`
  (nine parts, Distribution's own included); Distribution reads it with `json` and imports a part
  only through its entries (`concorde.<directory>.<module>`), each relative to the part's own
  package, so the dependency test sees no import. `tests/concorde/development/test_part_dependencies.py`
  lost `KNOWN_EXCEPTIONS` and `CODE_TASKS` and now also checks that each registration names its part
  and the parts-table dependencies, and that every entry lies in the part's own directory and exists.
- **Contract version 2** (`contract.distribution.part-registration`), additions the code needed and
  the Spec was silent on: `loads` (modules imported for every installed part before routing a part
  command, answering a tool or rendering the build: how parts register types, trace roots,
  definitions, workflows); command `output` (`own` or `envelope`, the latter answering Spec core's
  shared envelope for `concorde` to print); per tool `threaded` and `requires` (a tool presented only
  with those parts, e.g. `run_result` requires execution); part-level `mcp_definitions` (the
  description/inputSchema mapping) and `mcp_instructions` (the part's sentence of the server's
  instructions); `renders` (the build's entry, the workflow part's); `install.defaults`,
  `install.prepare` and `install.bind` (the installer services of I-5cb4068f). Removed `version`:
  every part carries the package's version from `concorde.json`, so a per-file copy could only drift.
- **Entry signatures.** Commands are called `(words, project_root)`; MCP tools with one JSON object
  (`tool`, `arguments`, `primary`, `where`, `session`, `channel`, `long_work`) and answer
  `{"value"}`/`{"error"}` plus `watch`, `handover`, `work`; the host does the exec of a long work
  generically (`work` names its command, files, event and a `locate` command for files the work
  moved), so `task_merge` stays Coordination's and the host knows no tool.
- **Absent part refusal.** One refusal: `{"error": <link>}` on stdout, code `part_missing`, exit
  status 1, link built by `distribution.cli.part_missing`, naming the part and `concorde update
  --parts <part>` / the installer's `--parts` (the second task implements `--parts`). A tool of an
  absent part, or one requiring an absent part, gets the same link from the MCP host.
  `coordination/tasks/parts.py` and `method/review_issues.py` accept exactly that; the test fakes
  (`installed_parts.py`, the reviews' `NO_ISSUES`) print the real link. A command no part of the
  package registers still answers one `failed` envelope (scenario refused-command-line).
- **Which part a missing command belongs to** comes from the build's parts index
  `generated/parts.json` (every part's commands and tools), so the dispatcher never loads a
  registration of a part that is not installed (req.distribution.registration-only).
- **Installed parts**: source checkout = every part; installed project = keys of the receipt's
  `parts` object (`{part: version}`, my choice of shape for the second task to write, recorded in the
  contract), every part when the receipt has none; Distribution always.
- **Formats met by Distribution itself** (`distribution/formats.py`): the error link and Spec core's
  envelope/error record. Prompt front matter is parsed by Distribution's own small parser (prompts
  only ever carry `audience:`).
- **Protocol copy** stays Distribution's own (its concept): built from the tracked manifest, read as
  a format; written only where the spec part is in the package's registrations. The spec part's
  install services are only the docsite template (`spec/installation.py:prepare`) and the binding
  (`bind`). The update rebinds the configuration from the copy's manifest bytes itself.
- **Dogfooding** is no part: the installer reaches its develop check through `concorde.json`'s
  `develop.check` entry (`concorde.dogfooding.develop:check`).
- **Code moves**: task tools → `coordination/tasks/tools.py`, Issue tools → `issues/tools.py`,
  Issues command line → `issues/cli.py` (`scripts/issues.py` is a thin wrapper), spec commands →
  `spec/commands.py`, open tasks after update → `coordination/tasks/update.py`, run idle check →
  `execution/idle.py`, method execution-command entries in `method/registration.py`,
  `workflows/catalog.py:build_renders`. Realization `realization.main-session.project-mcp` now binds
  the task tools; the host `src/concorde/distribution/project_mcp/` got Distribution's new
  `realization.distribution.project-mcp`; Spec core got `realization.spec.commands`.
- **I-232a51ae** fixed: Spec core no longer reads `.concorde/checks/` (checks reading, descriptor
  `checks`, `CONCORDE-CHECK-001`, checks digests in `source_digest`, the Spec MCP `module` query's
  `checks`); Method's survey and scaffold read existing check ids from Check execution. Removed the
  two Spec-core tests of that behaviour (Check execution has its own).
- **New scenarios**: `scenario.distribution.part-missing`, `composed-from-installed-parts`,
  `build-refuses-name-conflict`, each verified in `tests/concorde/distribution/test_distribution.py`
  (`PartsTests`), plus a test that every registration satisfies the contract schema.
- The installer still installs every part (the subset installer is the second task); it already
  takes ignore rules, defaults, install services, idle checks and after-update reports from the
  package's registrations.

## Report 1 to the main agent (concorde-a2), 2026-10-02T23:26:25Z

parts-registrations delivered: delivery commit b93effd4 on concorde/parts-registrations (after 8d470c38 code, dd46d479 Specs + I-232a51ae). task-validation ready; build --check, spec-validation and the full suite (1014 passed, 5 skipped) green. Resolves I-232a51ae (Spec core stops reading .concorde/checks/) and I-5cb4068f (installer services in the registration).

What changed:
- Every part has src/concorde/<dir>/registration.json (nine, Distribution's own included). Distribution imports a part only through its entries (concorde.<dir>.<module>); KNOWN_EXCEPTIONS and CODE_TASKS are gone from test_part_dependencies.py, which now also checks each registration names its part, the table's dependencies, and entries inside its own directory.
- concorde is composed from the installed parts: entry(words, project_root), output own or envelope; Distribution's two steps around spec-validation and init --apply kept. The absent-part refusal is one: {"error": <link>} on stdout, code part_missing, exit 1, naming the part and `concorde update --parts <part>` / installer --parts (second task implements --parts). coordination/tasks/parts.py and method/review_issues.py accept exactly that; the test fakes print the real link. An unknown command still gives one failed envelope.
- Project MCP server host presents the installed parts' tools: tool code moved to coordination/tasks/tools.py, issues/tools.py, workflows/tools.py; host keeps current code per call, session-worktree tools, generic long-work hand-over (task_merge's locks) and watching/waking; instructions composed from each part's sentence. A tool of an absent part (or run_result without execution) is refused part_missing.
- Build renders workflows through the workflow part's renders entry after loading every part, renders each registered guidance root, writes the parts index generated/parts.json, refuses a name two parts register.
- Installer takes ignore rules, defaults, idle checks (execution/idle.py), after-update report (coordination/tasks/update.py) and the spec part's install services (docsite template, binding) from registrations; Dogfooding via concorde.json develop.check. Protocol copy stays Distribution's own, written where the spec part is present.
- Contract version 2 (fields loads, output, threaded, requires, mcp_definitions, mcp_instructions, renders, install.defaults/prepare/bind; per-file version removed: parts carry concorde.json's). New scenarios part-missing, composed-from-installed-parts, build-refuses-name-conflict, verified.

Decisions I took (all in the decision log): the shapes above; installed parts = keys of the receipt's `parts` object ({part: version}), every part when absent (the second task should write that shape); the absent part of a command/tool is named from the build's parts index so no absent registration is read; realization moves (main-session project-mcp now binds the task tools, Distribution got realization.distribution.project-mcp, Spec core realization.spec.commands).

Open, nothing blocking: the installer still installs every part (second task), and Issues I-42b2f22d, I-b916fce5, I-f5f3e191 (receipt/update results recording parts) stay for the second task. No escalations.

## Closed: merged, 2026-10-02T23:26:41Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b93effd4e7acc11a2b6c6803ed19a5e1018a822f into parts-split and closed it as merged. Nobody answers a report after that.
