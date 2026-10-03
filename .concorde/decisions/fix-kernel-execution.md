# Decision log: fix-kernel-execution

Goal: Fix the parts refactor's regressions in the kernel, tracing, execution, Check execution and worker harness parts found by the overall review

## Brief (main agent, 2026-10-03)

### Context

The developer split Concorde into independently installable parts on the integration branch
`parts-split` (primary worktree on it; `main` untouched; decision logs of parts-spec ...
parts-install in `.concorde/decisions/`). Before fast-forwarding `main` to it, the developer had the
whole change reviewed: task `parts-review` (`.concorde/decisions/parts-review.md`) Module-reviewed
every changed Module, verified every finding against code, Spec and `main`, and classified 49 Issues
as regressions of the refactor (11 medium, none high or critical) and about 211 as pre-existing. The
developer decided (2026-10-03): **fix every regression on `parts-split`, plus the two defects that
make reviews unreliable, then merge**; pre-existing Issues wait until after the merge. Four fix
tasks run in parallel, one per group of parts: `fix-spec-root`, `fix-kernel-execution`,
`fix-workflow-method-issues`, `fix-coordination-distribution`.

### Rules

- The Issues this task resolves are on it (`--resolves`); the merge closes them. Read each with
  `concorde issues show` (its latest report is the verified one; parts-review corrected tiers and
  severities). Fix each in the Specs, code and tests as its report says, unless the decision below
  says otherwise. If one turns out not to hold, close it yourself with `not-actionable` and the
  reason, and record why; if fixing one needs a decision with major impact, escalate it.
- Stay in your group's files as far as the fix allows; another task may meet you in a shared file
  (registrations, guidance composition, `tests/concorde/development/`), so keep such edits small. If
  the merge conflicts, the main agent will ask you to merge `parts-split` in.
- Introduce no new regression: every part must still work installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency test must pass, and guidance
  must read correctly whichever parts are installed. Rapid-iteration rule: no shims or dual paths.
- Verify with `build --check`, `spec-validation`, the full suite and smoke runs of what you touched,
  then `task-validation` and `delivery`, and report.

### Your group: kernel, tracing, execution, Check execution, worker harness

Decided by the main agent:
- I-3f709b30: give every Operation and execution-command definition its providing Module identity
  (Method registers each with its own Module, e.g. `module.understanding`), as the Operations and
  Commands concepts promise, and keep the registering part too.
- I-941300cf: the parts register their node kinds with Tracing when their code loads, like trace
  roots and typed values; the Kernel hard-codes none of another part's kinds. Registering parts are
  Coordination, Execution, Workflows, the worker harness and Method: keep each such edit to one
  registration call in their code, since the other fix tasks work in those parts.
- I-e6240816 / I-b0e467d3: restore the protection main's project-wide check-input preflight gave,
  in Check execution, as its Spec says (task-validation's call path included).

## Task session decisions (task-fix-kernel-execution, 2026-10-03)

- **Kernel schema (I-97dec858, I-529eee55, I-b7008b86, I-f16be8b2).** `_admit` refuses `$defs`
  below a contract schema's top, naming its pointer; nested refusals build their pointer one
  component per step (`/properties/x`, `/anyOf/0`). The Kernel contract now states the 100-level
  value-check limit and how each step counts (field, item, `anyOf` alternative, `$ref`, embedded
  `data`), and that artifact and file-transaction paths through a symbolic link are refused
  (`invalid_field` for an artifact, `invalid_proposal` for a transaction, which is what the code
  raises).
- **Guidance (I-39a101dd, I-0542bfbf).** Kernel guidance says tasks and runs exist only with
  Coordination / Execution and that `trace show <folder>` still works. Worker harness guidance
  qualifies Operations (Execution), Method's worker ids and `worker_model_unavailable` (Method),
  and tasks / primary-branch commits (Coordination). I kept the phrase "before any Operation
  runs" because the Coordination main-session Specs and tests quote it verbatim and the sentence
  stays true without Execution; changing it would reach into another group's Module.
- **Node kinds (I-941300cf).** New `kernel/tracing/kinds.py` (`NodeKind`, `register`, `lookup`),
  bound in `realization.tracing.library`. `node.check` refuses a kind no installed part
  registered and metadata outside the kind's dimensions (`node_invalid`), and content of another
  type than the kind's (`content_invalid`). `contract.tracing.node` goes to version 5: `kind` is a
  pattern-checked string, the registration rule is in its semantics and in "Node kinds"; new
  scenario `scenario.tracing.kind-registered`. Each producer registers its kinds right after the
  content type it already registers, which is one `register_kinds(...)` call per producing
  module: Coordination three (tasks/store.py task+session, merge.py merge+merge-check,
  deliver.py delivery+delivery-check, since each type constant lives there), Execution two
  (runs.py run, checks/checks.py check), Workflows one (store.py), worker harness one
  (workers.py). **Method registers none: it produces no trace node** (its checks go through
  Check execution's `check` node), so the brief's mention of Method needed no call.
- **Root places (I-f8772d79, suggestion).** The reader applies a root registered with place
  `primary` only to a `.concorde` that is not a linked worktree's (whose `.git` is a file); the
  reading contract says so. I chose the `.git`-file test over a Git call per directory: it needs
  no subprocess and treats a binding's `.concorde` (the primary's) and non-Git test roots alike.
- **Catalog (I-3f709b30, decided by the main agent; I-e4ba7e37; I-c5588827).** `Provider` gains
  `module`; both catalogs refuse with `invalid_definition` a definition without a `module.<id>`
  identity and an Operation without worker ids, and give `Catalog.module(name)`. Method's
  registration.py sets each definition's Module with `dataclasses.replace` in one place
  (understanding ×2, specification, implementation ×2, spec-review ×2, code-review, adoption ×2,
  validation, delivery, scaffold) so no Method definition file is touched. The Commands and
  Execution Specs now say the providing part names each execution command in its own part
  registration (the preferred fix of I-c5588827). New scenario
  `scenario.operations.definition-complete`.
- **Check execution (I-078aae79, I-b0e467d3, I-d2dec046, I-e6240816).** Checks files are parsed
  with `kernel.schema.decode`; `_timeout` requires a finite number; an input's directories are
  checked with `checked_path` (an input that is itself a link stays `check_input_missing` at
  measurement, as the service Spec distinguishes); `run_checks` materializes `measured` once.
  For the preflight, per the brief ("task-validation's call path included"), Method's
  `run_configured_checks` (src/concorde/method/validation/command.py) calls `validate_checks`
  before the per-Module checks: a problem blocks once as the `check` finding "configured checks",
  even for a Module the run does not check, and the same problem raised again by a Module's own
  checks is not reported twice; the other checks still run. Validation's module.md (step 6 and
  the paragraph on checks files) now agrees with Check execution's service.md. I did not put the
  project-wide judgement inside `run_checks`, since every per-Module group would then fail on one
  unrelated bad input and no check would run.
- **Grant (I-5b2ba600).** Entries present but no list are `grant_malformed` (only a missing
  `entries` is `grant_unavailable`), and a grant entry with a field other than `path` and `level`
  is `grant_malformed`; the malformed-grant scenario names the extra-field case.
- **Not filed.** spec-validation's result still claims "configured check input availability and
  path safety": already Issue I-48fb0384 (Spec tooling, another group), so no new report.

## Report 1 to the main agent (项目架构分离建议), 2026-10-03T06:31:07Z

fix-kernel-execution delivered: delivery commit 284900dc on concorde/fix-kernel-execution (task-validation ready with 20 checks passed; full suite 1029 passed; build --check and spec-validation clean apart from 2 old Distribution warnings).

The task fixes all 16 Issues on it (the merge closes them):
- Kernel: I-97dec858 ($defs only at a contract schema's top), I-529eee55 (refusal pointers built one component at a time), I-b7008b86 (contract states the 100-level value-check limit), I-f16be8b2 (contract states that symlinked paths are refused), I-39a101dd (Kernel guidance covers installs without Coordination or Execution).
- Tracing: I-941300cf, done as you decided. New kernel/tracing/kinds.py. Tracing names no node kind itself any more. Every node write is checked against its kind's registration: unregistered kind or extra metadata gives node_invalid, wrong content type gives content_invalid. contract.tracing.node goes to version 5. New scenario.tracing.kind-registered. Each producer adds one register_kinds call next to the content type it already registers: Coordination in tasks/store.py, merge.py and deliver.py; Execution in runs.py and checks/checks.py; Workflows in store.py; worker harness in workers.py. Method needs none because it writes no trace node. I-f8772d79: a root registered for the primary worktree is no longer searched in a linked worktree's .concorde.
- Operations: I-3f709b30, done as you decided. Provider has a module field. Both catalogs refuse a definition without one, and Catalog.module() returns it. Method sets each definition's Module in registration.py alone, so its definition files are untouched. I-e4ba7e37: an Operation without worker ids is refused. I-c5588827: took the preferred fix. The Commands and Execution Specs now say the providing part names its execution commands in its part registration. New scenario.operations.definition-complete.
- Check execution: I-078aae79: checks files are parsed with kernel decode, and the timeout must be finite. I-b0e467d3: an input under a symlinked directory is refused as invalid_check. I-d2dec046: measured file lists are read once. I-e6240816/I-b0e467d3 protection: task-validation now calls validate_checks before the per-Module checks. A bad input anywhere in the project blocks once, as the check finding "configured checks", even for a Module that is not checked. The same problem is not reported a second time, and the other checks still run. This takes a small edit in method/validation/command.py and Validation's module.md (step 6), which your brief allowed as "task-validation's call path".
- Worker harness: I-5b2ba600: entries that are present but not a list now give grant_malformed, and a grant entry with fields other than path and level is refused. I-0542bfbf: worker harness guidance now says which part each mention needs.

Decisions I made (all in the decision log):
(1) The worker-harness guidance keeps "before any Operation runs". The main-session Specs and tests quote it word for word, and it is still true without Execution.
(2) A root's place is detected from the .git file, with no Git call.
(3) The full-project input check is not inside run_checks. Otherwise one bad input would stop every Module's checks.
(4) Small edits outside my group, which may conflict: one register_kinds call each in the Coordination and Workflows files above, method/registration.py, method/validation/command.py, and the Validation, Commands and Execution Spec text.

Not filed: spec-validation still claims to check configured-check inputs, which it no longer does. That is already Issue I-48fb0384, in another group.

Open: none.

## Closed: merged, 2026-10-03T06:31:52Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 284900dc0f48e64014a848c896f471439cc0782f into parts-split and closed it as merged. Nobody answers a report after that.
