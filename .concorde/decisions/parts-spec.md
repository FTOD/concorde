# Decision log: parts-spec

Goal: Restructure Concorde's Specs so Concorde is made of independently installable parts (spec, kernel, worker harness, execution, workflow, issues, coordination, method, distribution) with the agreed dependency directions, before any code change

## Brief (main agent, 2026-10-03)

### Context

The developer wants Concorde split into parts so that a later project can use only some of them,
and stressed what "independent" means: **each part can be installed into a project on its own, or
in any subset, and every installed part works without the parts it does not depend on**. Import
layering alone is not enough. The whole refactor happens on the integration branch `parts-split`
(the primary worktree is checked out on it; this task merges there, never into `main`). It runs
Spec first: this task changes the Specs; later tasks change the code to match.

### The developer's decisions (2026-10-03), which this task carries out

The parts and the only dependency directions allowed between them:

| Part | Holds | Depends on |
| --- | --- | --- |
| spec | Spec tooling: Spec core (Protocol, loading, validation, registry, glossary, grants, impact index), Spec MCP, Views | nothing. It keeps **its own copy** of the small data utilities it uses (schema validation, typed values, file transaction, digest) rather than sharing the kernel's; duplication is accepted to decouple. Its own error types stay. |
| kernel | the shared contracts parts cooperate through without importing each other: error chain, trace node, typed values, file transaction, digest, locks, delivery-commit convention (see below for more) | nothing |
| worker harness | today's Harness and Workers together: launching, bounding, auditing and recording one worker under a grant; worker configuration and model map. The developer chose the name "worker harness" (not "runtime", which collides with the glossary's Runtime directory). | kernel only. It receives the grant as data (it computes no grant and reads no Spec) and the round validation as a callback from its caller. |
| execution | runs: runner, run store, run result, workspace binding and locks, detached and unbound runs, the Operation framework and the execution-command framework, Check execution | kernel only. It does not launch workers itself. |
| workflow | its own part: step engine, step keys, modes, decision points, workflow record, report, workflow scripts and their Claude Code adapter | execution (+ kernel). A step is only ever a Concorde run. Operation-specific knowledge now in Workflows (what counts as a decision point: open questions, survey decisions; spec_review verdicts; survey's proposed checks; scaffold children; `LAST_STEP`) moves out to a generic output convention that every Operation can fill and every workflow script can name (e.g. its last step). It provides its own `workflow_step` MCP tool instead of relying on Coordination's project MCP server. |
| issues | its own part (developer's choice) | kernel only |
| coordination | main session, tasks, worktrees, merge, task sessions, main-session guidance | kernel only; issues, execution, workflow and method are optional integrations |
| method | the concrete Spec-driven development work: Operation providers (understand, plan_review, specify, implement, test, code_review, spec_review, spec_panel, survey, code_to_spec), execution commands (task-validation, delivery, scaffold), the brownfield workflow script, worker prompts, and the standard worker sequence that takes a grant from Spec core and hands it to the worker harness | spec + worker harness + execution + workflow; issues optional |
| distribution | build, packaging, the installer and `concorde update`, composing whichever parts are selected | the parts only through a registration contract (see below) |

Dogfooding and End-to-end testing stay developer-facing Modules as now.

Further decisions:

- **Independent installation is a promise.** Each part is its own installable package declaring
  only its real dependencies; the installer installs any subset (dependencies pulled in
  automatically) and records which parts are installed; `concorde update` updates those. Each part
  contributes its own CLI subcommands, guidance (skill text), MCP tools and `.concorde/` files; a
  missing part's commands, tools and guidance are simply absent. Every cross-part feature is an
  optional integration that works, or is skipped with a clear statement, when the other part is
  absent: e.g. a merge closing resolved Issues only with issues installed; reviews reporting
  Issues only with issues installed, else findings stay in the run result; the merge's
  spec-validation check only with spec installed; `--modules` and an Issue's Module being plain
  labels when spec is absent.
- **One repository, one version number for all parts for now**; no separate release cadence.
- **Rapid-iteration rule**: no compatibility shims, transitional adapters or dual paths; refactor
  boldly.
- Earlier standing decisions still hold and must survive the restructure: Execution knows no
  task (the workspace binding is the seam; task state is derived by Coordination); an Operation
  exists only where a model works, otherwise it is an execution command; errors travel as error
  chains; Tracing's nesting rules (task -> workflow -> run -> worker round, links downward only);
  one global glossary with owners; context and permission computed from the Specs (now: computed by
  spec, applied by worker harness, sequenced by method).

### Couplings the main agent found in the code (for the Spec to resolve; code tasks fix them)

Import scan of `src/concorde` on 2026-10-03:
- Nearly every package imports `spec.schema`, `spec.typed_data`, `spec.changes`, `spec.repository.digest`
  only as generic data utilities -> kernel (spec keeps its own copy).
- `harness/models.py:142` imports `operations.catalog` (a lower layer reaching up).
- harness uses `spec.grants`, `spec.glossary` (`plain_definition` for briefs, `ownership_violations`
  in the audit), `spec.verification`, and `harness/checks.py` uses `SpecRepository`/`bound_by`:
  Spec-aware parts move to method (grant computation, brief's glossary text, the glossary
  ownership audit, which Modules' checks run).
- `execution/context.py:363` calls `run_worker`; `execution/context.py`/`runner.py` build
  `SpecRepository` and grants; `execution/checkout.py` reads worker config runtime paths.
- `operations/review_issues.py` writes Issues directly -> an optional sink.
- `issues/store.py` uses `tasks.store` for the merge lock -> the lock belongs in kernel.
- `tasks/store.py` uses `delivery.commits` (delivery-commit recognition) and `tasks/merge.py`
  uses `distribution.install.UPDATE_STATE`.
- `workflows/step.py:336-361` and `workflows/report.py` (lines ~87-480) hold Operation-specific
  knowledge (see the workflow row).
- The project MCP server (`src/concorde/project_mcp/`) serves tasks, traces, locks, Issues and
  `workflow_step` from one Coordination-owned server.

### Left to this task session (decide, record each choice with its reason here)

Recommendations, not decisions:
- **Module tree.** Each part is a top-level child Module of the root, with the folder tree
  matching (it is a validated registry projection). Suggested: `spec-tooling/` (Spec core, Spec
  MCP, Views; Spec review moves out to method), `kernel/` (new; Tracing may become its child or be
  folded in), `worker-harness/` (new parent of Harness and Workers), `execution/` (runner,
  Operation framework, command framework, Check execution), `workflows/` (moved to top level),
  `issues/`, `coordination/`, `method/` (new parent of the Operation providers, Validation,
  Delivery, Scaffold, Spec review), `distribution/`, `dogfooding/`, `e2e/`. Names of new Modules
  are yours; keep existing Module ids and requirement/scenario ids stable wherever their meaning
  holds, to limit churn in tests' `verifies` declarations and links.
- **Kernel contents.** The contracts both sides of a seam need: error chain, trace node, typed
  values, file transaction, digest, lock primitives and the lock conventions several parts take
  (the merge lock, which Issues also takes, perhaps renamed for what it guards; the workspace lock;
  the run lock), the workspace binding format, the delivery-commit convention, run-result
  envelope fields others read. Glossary owners move accordingly.
- **Shell.** The `concorde` CLI dispatcher and the project MCP server host are part-agnostic and
  load what installed parts register (commands, MCP tools, typed value types, install
  contributions, guidance). Recommended home: distribution (always installed, depends on no part)
  with the registration contract in kernel; decide and record.
- **Delivery without method.** Coordination needs a way to deliver a task when method (which owns
  `delivery`/`task-validation`) is not installed. Recommendation: the delivery-commit convention is
  a kernel contract; method's `delivery` is the validated producer; Coordination states what a
  coordination-only install does (e.g. its own minimal deliver that runs the configured checks or
  none). Choose and record.
- **Session boundary** moves from Harness to Coordination (task sessions); it is not a worker
  harness concern.
- **Guidance.** The `concorde` skill splits into per-part guidance composed at install; state in
  the Specs which part owns which guidance (main-session guidance stays Coordination's).
- **Glossary.** A term for the installable unit is probably needed (the developer calls it a
  "part"); revise definitions that assume everything is installed (Agent harness "derived from the
  Specs", Task "bound as the workspace", Merge lock, Delivery commit, Project MCP server, Operation
  catalog "fixed list", Workflow script "rendered as a Claude Code workflow" etc.).
- Requirements, scenarios and contracts of every moved or changed Module must agree with the new
  structure; realizations keep binding today's code paths (code tasks move the code and update the
  binds), unless a bind is plainly wrong already.
- How to do it: edit Specs directly (Operations are optional and may be less reliable for a
  restructure this size). Once the structure validates, consider one `spec_panel` (or
  `spec_review`) of the root and the new parents, fix blocking findings within this goal and record
  the rest as Issues. Model spend needs no permission.

Escalate to the main agent, all together, only decisions that would contradict the table above,
drop an existing capability, or change how the developer works with the main agent; decide the
rest. Verify with `build --check`, `spec-validation` and the tests the Spec changes touch (ids,
links, verifies), then `task-validation` and `delivery`, and report.

## Task session decisions (2026-10-03)

1. **Module tree.** Each part is a top-level child of the root with the folder tree matching:
   `spec-tooling/` (Spec core, Spec MCP, Views), `kernel/` (new `module.kernel`, child Tracing at
   `kernel/tracing/`), `worker-harness/` (new `module.worker-harness`, children Harness and
   Workers), `execution/` (runner; Operations and Commands as frameworks only; Check execution),
   `workflows/` (top level), `issues/`, `coordination/`, `method/` (new `module.method`: children
   understanding, specification, implementation, code-review, spec-review, adoption, validation,
   delivery, scaffold), `distribution/`, plus Dogfooding and End-to-end testing as developer
   Modules, not parts. All existing Module ids kept. Reason: the brief's recommendation; the folder
   tree must project the registry. Done mechanically first (commit c92456c4), links, owns paths,
   glossary explanations and the registry rewritten by script; tests that read Spec files by path
   follow the new paths.
2. **Shell and registration contract in Distribution, not Kernel.** The `concorde` dispatcher and
   the project MCP server host are Distribution's (present in every installation), and the part
   registration contract is Distribution's too. Reason: the spec part must depend on nothing, not
   even the kernel; a registration is plain data satisfied by shape, and the consumer that loads it
   owns its format, as the receiving worker harness owns the grant's input format. New glossary
   terms: Part, Optional integration (root), Part registration (Distribution); Project MCP server
   now owned by Distribution.
3. **Kernel contents.** Typed value and file transaction (moved from Spec core; Spec core keeps a
   private copy of the formats), workspace, workspace binding (contract renamed
   `contract.kernel.workspace-binding`), workspace lock, merge lock (from Tasks; name kept, since
   renaming would ripple through `merge_busy`, `--lock merge` and code), delivery commit
   recognition and verification (from Delivery). Run result, run store and run lock stay
   Execution's: only parts depending on Execution read them; Coordination reaches them through an
   optional integration with execution. Tracing stays Kernel's child; History moves to Tasks, and
   Tracing knows trace roots the parts register.
4. **Delivery without Method.** Coordination gets `concorde task deliver <task> [--check ...]`,
   which runs the given checks and commits a delivery commit by the Kernel's convention, and which
   refuses (`delivery_by_method`) wherever the method part is installed, so a workspace Method could
   validate is never delivered without validation. `req.concorde.delivery-commit-by-delivery`
   reworded accordingly (id kept).
5. **Agent harness** moves to the root (it spans the three agent levels); **Session boundary** to
   Task sessions with its own hook (`session_hook.py`); **Write hook** stays Harness's, defined for
   workers only.
6. **Workflow output convention.** Workflows owns a generic step output convention
   (`workflow.decision_points`, `decisions`, `deviations`, `notes`) that any Operation fills;
   decision points are what the producing Operation declares; a workflow script names its last
   step. The brownfield workflow concept, its procedure text (new `method/brownfield.md`) and its
   script move to Method. Workflows registers its own `workflow_step`/`workflow_report` tools.
7. **"Kernel" names the part**, so Spec text meaning the operating system kernel says "the
   operating system".
8. **No new scenarios in this task.** Delivery refuses a workspace that changed code (the test
   path updates count) while an added scenario lacks a verifying test, and no code changes here;
   new promises are requirements now, and the code tasks add scenarios with their tests. Existing
   scenario ids are kept so tests' `verifies` still resolve.
9. **Root requirements added**: `req.concorde.part-dependencies`, `req.concorde.part-alone`,
   `req.concorde.absent-part-stated`, `req.concorde.one-version`.
10. **Method of work.** The lead writes the root, Kernel, Worker harness and Method entries and the
    glossary; six forks of this session then revise the existing Modules per part in parallel on
    disjoint files (A kernel/Tracing+Execution, B worker harness, C workflow, D coordination+issues,
    E method children, F spec tooling+distribution+developer Modules), following the plan kept in
    the worktree's ignored `.generated/parts-spec/plan.md`.

## Integration and review (2026-10-03)

11. Forks A–F delivered their revisions (commit 5c717b60). Integration choices: `trace_show` and
    `run_result` stay Coordination's tools (fully specified there; `run_result` only where execution
    is installed), Distribution's parts table corrected to match; `task deliver`'s node kinds
    `delivery`/`delivery-check` added to Tracing's table; the three `workflow_step` requirements
    removed from Main session became `req.workflows.tool-step-command`, `-tool-bound-only`,
    `-tool-threads`; the host requirements (current code, tools changed, `call_failed`) moved from
    Main session to Distribution as `req.distribution.mcp-*`; `req.operations.workspace-specs`,
    `req.operations.models-placed-first` and `req.workers.glossary-by-entry` moved to Method as
    `req.method.*` with `req.method.grant-as-data` and `req.method.issues-optional` added.
12. **Contract fences compared with the code by tests keep their current versions.** Fork C had
    moved `contract.workflows.step`, `step-request` and `result` to the generic step output
    convention, which failed `test_the_schemas_are_the_contracts` (a configured check that would
    block delivery). Restored those three fences; the prose and the new
    `contract.workflows.step-output` state the target, and the code task bumps the fences with the
    code. Full suite otherwise: 964 passed.
13. Non-ok result: `spec_panel` r-20261002T190724-spec_panel-89d5bab4 on the root, Kernel, Worker
    harness and Method: `changes_required`, 40 blocking findings and 17 suggestions, all recorded as
    Issues by the Operation. Four forks (R, K, W, M) fix the obvious/preferred ones within this goal
    and settle the decision-needed ones this restructure created when the developer's decisions
    already answer them; pre-existing ones that only moved with the text stay recorded.

14. Forks R, K, W, M answered the panel (commit 9a60675f). Fixed or settled 36 Issues, added to the
    task with `task resolve`. Decision-needed Issues settled within the brief's delegation (none
    contradicts the parts table, drops a capability or changes how the developer works):
    I-fa8c61d6… (root grant promises cover grants Method computes; the harness alone enforces what
    it is given), I-eddceec1… (part dependencies are package dependencies; a format another part
    defines that a part meets itself, and Distribution's host promises, are not dependencies),
    I-54f88b22… (Distribution's `build`/`protocol-manifest` share Spec tooling's error-envelope
    exception), I-92f008bc… (Kernel defines its own registered-schema dialect), I-7b5f86b6… (a file
    transaction's caller excludes other writers by the lock its records require),
    I-e553cef9… (Kernel's delivery convention covers marker/ancestry/verification only; each
    delivering command owns its content rules), I-f6190dbd… (a standalone caller of the worker
    harness must keep other writers out of the worktree; Execution's workspace lock does it in
    Concorde). Left open, pre-existing and only moved with the text: I-5badf523… (brownfield cycle
    policy; recommend ordering strongly connected groups), I-d0783a18… (scaffold effects of a
    superseded survey; recommend a fresh workspace), I-4d84ba09… and I-28f9a76b… (development.md),
    I-b3d59e10… (Kernel scenarios: requirements added, scenarios wait for the code task's tests).
15. Recorded for the code tasks: I-26aa6017… (Workflows fences), I-9984951d… (Method output
    fences), I-4c0a0969… (Tracing node kinds enum), I-42b2f22d… (Distribution result fences),
    I-9669db1a… (scenarios still in Operations and Spec core because tests name them).
    Full suite 964 passed, 5 skipped; spec-validation and build --check clean.

## Report 1 to the main agent (concorde-a2), 2026-10-02T20:09:03Z

parts-spec delivered at d40ca6b1 on concorde/parts-spec (task-validation ready; spec-validation 0 findings; build --check clean; full suite 964 passed, 5 skipped). No escalations.

What changed (Specs only, plus tests' Spec paths):
- Tree: each part is a top-level child of the root: spec-tooling/, kernel/ (new module.kernel, child Tracing), worker-harness/ (new module.worker-harness: Harness + Workers), execution/ (runner, Operation and command frameworks, Check execution), workflows/, issues/, coordination/, method/ (new module.method: understanding, specification, implementation, code-review, spec-review, adoption, validation, delivery, scaffold), distribution/; Dogfooding and End-to-end stay developer Modules. All existing Module ids kept.
- Root: parts table with the agreed dependency directions; new terms Part, Optional integration (root), Part registration (Distribution); req.concorde.part-dependencies, part-alone, absent-part-stated, one-version; req.concorde.delivery-commit-by-delivery now allows Coordination's task deliver where Method is absent.
- Kernel owns typed value, file transaction, workspace, workspace binding (contract.kernel.workspace-binding), workspace lock, merge lock (name kept), delivery commit recognition; Spec core keeps its own copy of the formats. Tracing knows trace roots the parts register; History moved to Tasks.
- Worker harness takes the grant as data and its caller's round validation; Session boundary moved to Task sessions; Agent harness to the root.
- Execution reads no Spec and launches no worker; Check execution owns the checks file format.
- Workflows: generic step output convention (contract.workflows.step-output), last step named by the script, own workflow_step/workflow_report tools; brownfield workflow and script are Method's.
- Coordination: kernel only, every other reach an optional integration; new `concorde task deliver` (refused with delivery_by_method where Method is installed).
- Issues: kernel only; Issue's Module checked against the registry only with the spec part.
- Distribution: shell and project MCP server host, part registration contract (chosen over Kernel because the spec part must depend on nothing and a registration is plain data the loader owns), installs any subset, records installed parts.

Decisions taken on the main agent's behalf (all in the decision log, entries 1-15): the module tree; registration contract in Distribution; Kernel contents; task deliver; no new scenarios (Delivery would refuse untested ones) and scenario ids kept; contract fences that tests compare kept at current versions so the configured checks pass (the code tasks bump them); trace_show/run_result stay Coordination's tools; requirements moved between Modules (listed in entry 11).

Review: spec_panel r-20261002T190724-spec_panel-89d5bab4 on root/Kernel/Worker harness/Method: changes_required, 40 blocking. 36 fixed or settled and resolved by this task (merge closes them). Decision-needed Issues I settled within the brief (please object if any is the developer's): I-fa8c61d6 (root grant promises cover grants Method computes), I-eddceec1 (part dependencies = package dependencies; meeting another part's format or Distribution's host promises is not a dependency), I-54f88b22 (build/protocol-manifest share Spec tooling's error-envelope exception), I-92f008bc (Kernel defines its own registered-schema dialect), I-7b5f86b6 (a transaction's caller excludes other writers by its records' lock), I-e553cef9 (Kernel's delivery convention covers marker/ancestry/verification only), I-f6190dbd (a standalone worker-harness caller must keep other writers out of the worktree).

Still open: pre-existing decision-needed I-5badf523 (brownfield cycle policy; recommend ordering strongly connected groups by outside dependencies) and I-d0783a18 (scaffold effects of a superseded survey; recommend requiring a fresh workspace); I-4d84ba09, I-28f9a76b (development.md, pre-existing); I-b3d59e10 (Kernel scenarios wait for the code task's tests). Recorded for the code tasks: I-26aa6017 (Workflows fences), I-9984951d (Method output fences), I-4c0a0969 (Tracing node kinds enum), I-42b2f22d (Distribution result fences), I-9669db1a (scenarios still in Operations/Spec core because tests name them). The code tasks also move the code each realization still binds at today's paths.

## Closed: merged, 2026-10-02T20:09:33Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit d40ca6b18aff292e076ffa41f6bf489b38207be7 into parts-split and closed it as merged. Nobody answers a report after that.
