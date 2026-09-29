# Decision log: tracing

Goal: Add the Tracing Module (traces, their uniform structure and metadata, the error chain) and reorganize Concorde's records into one folder per task with nested uniform traces, a history area for closed tasks and all locks under .concorde/locks, as agreed with the developer

## Brief from the main agent, 2026-09-29

The developer agreed the following design with the main agent and asked for it to be carried out
directly, Specs and implementation, without a Spec review round in between. Work it through to
delivery: first the Specs (new Module and every affected Module, glossary), committed as their own
steps, then the implementation, tests and docs, each verified step committed.

### Why

An inventory of observability found: no state history for tasks; Claude Code task sessions record
only their start; workflow steps record only a start time; runs have no per-step timing and no
exit code in the result; workers record cost per round but no tokens, overwrite earlier rounds'
stderr and write their record only at the end; nothing is aggregated upward; there is no CLI to
list or show runs (unbound runs are invisible); launch logs of the pi run view are not tied to
their run; nothing is ever cleaned up; credential copies (`auth.json`, `.credentials.json`) stay
in every worker run directory forever; records have no schema version (five key shapes of
`status.json` on disk). The organisation is also muddled: state, evidence, traces and runtime
inputs (grant, settings, credentials, home, tmp) sit side by side, `r-*` and `w-*` run directories
are flat siblings, locks sit inside record folders.

### Decisions of the developer

1. **A new Module, Tracing** (proposed id `module.tracing`, a child of the root, Spec under
   `specs/concorde/tracing/`). Tracing defines which information is combined and retained, and in
   what structure, so that it can be analysed later. It does **not** define how the information is
   produced: each producing Module (Tasks, Task session, Workflows, Execution, Workers, Checks, …)
   still produces its own content. Tracing is a capability; it owns the mechanism (structure,
   nesting and links, the uniform record, metadata dimensions, layout of current and history
   folders, retention, reading tools), not the level-specific content.
2. **The error chain belongs to Tracing** (move `concept.error-chain` from the root to
   `module.tracing`). Condition: the error chain stays an in-band, self-contained part of every
   result, which its receiver decides from; it is never replaced by a pointer into the traces. A
   link may carry the id of its trace node as an entry point for deeper analysis. Spec tooling
   keeps its own error types (earlier developer decision) — say so.
3. **Structure**: levels above and below each other are **nested**; nodes at the same level may
   **reference** each other (e.g. a workflow step's input run, the runs a delivery bundle cites).
   Across the two halves the link goes **downward only**: Execution knows no task and only
   produces its own traces; the task links to its workspace's traces. Analysis goes from a task to
   its executions, never from an execution back to its task. The task→Execution link is at the
   **workspace** granularity (not per task-session round). Nesting is done by the parent giving
   the child its location before the child starts (no orphans), never by the child recording its
   parent's id.
   Logical hierarchy:
   ```
   task ─┬─ session ─ round
         ├─ merge ─ check
         └─ workspace (link; Execution below)
              ├─ workflow ─ step ─ run
              └─ run ─┬─ check
                      └─ worker run ─ round ─ check
   ```
   Runs a workflow step starts are nested under that step; runs started directly (by a task
   session or the main agent) sit under the workspace. The reading tool walks both.
4. **Uniform record, structured with metadata**: every node has a `trace.json`: uniform fields
   (id, kind, started_at, ended_at, status, usage {tokens in/out/cache, cost, turns, duration},
   error link, references to large artifacts by relative path and digest), analysis metadata
   dimensions (workspace, modules, Operation or execution command name, task type, worker id,
   backend, model, reasoning, commit, context identity, grant/brief digests, Concorde commit,
   Protocol version — each level declares which it provides), and the producer's own content as a
   typed value (`concept.typed-value`). The worker run record (`record.json`) and the workflow
   record (`record.json`) are folded into their `trace.json`. `status.json` (live progress files)
   and `result.json` (run result, read by workflow report and delivery) stay separate files in the
   same node folder; `trace.json` is written initially at start and finally at the end. Metadata
   records only facts Concorde observed itself, never worker claims. Large content (transcripts,
   event streams) is referenced, never copied. A derived query index is allowed but is never the
   source of truth. No absolute paths inside traces: only ids or paths relative to the trace root,
   because folders move.
5. **Layout: no separate `traces/` folder.** One folder per task holds everything of that task,
   state and traces alike; the organising axis is the task's lifecycle:
   ```
   .concorde/
   ├─ config.json specs.json workers.json protocol/ checks/ tools/ issues/   (unchanged)
   ├─ evidence/<task>/<n>.json      evidence bundle, still committed to Git (unchanged)
   ├─ locks/                        every lock, nothing else
   │  ├─ merge.lock  issues.lock
   │  ├─ tasks/<task>.lock  workspaces/<ws>.lock  workflows/<ws>.lock  runs/<run>.lock
   ├─ tasks/<task>/                 a current task
   │  ├─ task.json                  state (task record: only what commands need to act)
   │  ├─ trace.json                 task-level trace: start/end, outcome, metadata, state
   │  │                             transitions, escalations, link to workspace/
   │  ├─ decisions.md               decision log
   │  ├─ runtime/                   task session boundary config (not a trace; removed at close)
   │  ├─ sessions/<session>/        trace.json, status.json (live, pi), transcript.jsonl,
   │  │                             rounds/<n>/{trace.json,prompt.md,events.jsonl,stderr.log,supervisor.log}
   │  ├─ merges/<n>/                every merge attempt incl. conflicts and undone merges:
   │  │                             trace.json, checks/<check>/{trace.json,output.log}
   │  └─ workspace/                 Execution's root; the binding gives this location
   │     ├─ workflow/               trace.json (name, mode, client, args), answers/, reports/,
   │     │                          steps/<seq>-<key>/{trace.json, run/…}
   │     └─ runs/<run>/             trace.json, status.json, result.json, host.out,
   │                                readiness.json (validation/delivery), checks/<check>/…,
   │                                workers/<worker-run>/{trace.json,status.json,grant.json,
   │                                brief.md,transcript.jsonl,rounds/<n>/{trace.json,stderr.log,checks/…}}
   ├─ history/<task>/               a closed task, same structure; moved by renaming the task folder
   └─ unbound/<run>/                runs without a workspace, same structure as a run
   ```
   - State (task record, locks) is not a trace; the history parts now in the task record
     (session rounds, escalations, state transitions, merge attempts) move to the task's traces;
     which exact fields stay in `task.json` is yours to settle in the Spec.
   - **Locks are separate from records**: every lock under `.concorde/locks/`, never inside a
     task, workspace or run folder. A lock file holds only its current holder. The run lock is
     taken only by its runner and is deleted when the runner exits (a missing file means not
     running); workspace, workflow and task locks are contended, so they are removed only at task
     close while held; merge and issues locks are permanent. The pi run view must tell liveness
     from `locks/runs/<run>.lock` (today it reads `/proc/locks` by the run directory's inode).
   - The workspace binding gives Execution its trace location (`tasks/<task>/workspace/`) and the
     `.concorde` root (for `locks/workspaces/<ws>.lock` etc.); Execution never learns it is inside
     a task. Other preparers of a workspace choose the location themselves.
   - **Worker runtime inputs** (`control/`, `config/` with credential copies, `home/`, `tmp/`,
     `work/`) move to a private directory under `/tmp`, removed when the worker ends; the
     transcript (Claude `config/projects/…`, pi `config/sessions/…`) is moved into the worker
     trace first. Credentials must never persist in the records.
   - **pi launch logs** (`runs/launch-<ms>.log`) go away: the pi extension starts runs with
     `--detach`, so the runner writes `host.out` in the run folder; a failure before any run exists
     returns to the tool call directly.
   - stderr is kept per worker round (not overwritten).
6. **Close moves the task to history at once**, but only when the task has really ended: close
   takes the workspace lock (so no run is running and none can start), renames
   `tasks/<task>/` to `history/<task>/`, then releases. A merge already waits for runs; a failed or
   abandoned close first stops the workspace's running runs and a running pi task-session round.
   The write hook of a task session must refuse writes into a task folder that no longer exists.
   After close, a run in that workspace is refused because its binding's location is gone. History
   keys must be unique (check whether `task open` refuses reusing a name; if not, make keys unique).
   History is append-only; it is only removed whole (retention) or exported. The final
   `task.json` goes to history with the rest; `.concorde/tasks/` holds only current tasks.
7. **Evidence stays with the runs** that produce it (readiness, check results inside the run). The
   **evidence bundle stays committed to Git** under `.concorde/evidence/`: after retention removes
   local traces it is the only durable record, and it travels with the code. It must be readable
   on its own; its run ids are only an entry point while the local traces exist. The delivery
   run's trace references the bundle (commit and path); the bundle references runs by id.
8. **Reading tool**: a read-only `concorde` command (name it by the owning Module per the command
   naming rules) that shows any node and walks its tree from any level, with timing and cost
   rolled up, including unbound runs. `task show` and the pi run view read the new layout.

### Decisions of the main agent (recorded here, taken without the developer)

- One task rather than several: every part of this change touches the same layout and the same
  code paths (run store, binding, task store, pi run view), so parallel tasks would conflict.
- Retention defaults (the developer left the numbers open): history is kept without automatic
  removal by default; unbound runs are kept 7 days after they end and then removed. Both are
  configurable in `.concorde/config.json`. Removal is explicit or happens at a defined point you
  choose (e.g. on task open/close); never in a background daemon.
- Claude Code task sessions reporting their end through a Concorde command is **not** in scope
  (the workspace-level link was chosen); keep recording what the session entry records today.
- No backward compatibility (standing developer rule): no migration code for the old layout.
  Do not delete or rewrite existing records of the primary worktree either; old `.concorde/runs`
  and flat `.concorde/tasks/<id>.json` files simply stop being read. Mention in your report what
  is left on disk.
- **Bootstrapping hazard of this task itself**: this task was opened by the old code, so its own
  record, decision log and workspace binding are in the old layout, and the primary worktree's
  code (old) will merge it. Keep this task operable to delivery: when the branch's code switches to
  the new layout, adapt this task's own git-ignored binding by hand if needed so that
  `task-validation` and `delivery` from the task worktree still work, and log what you did. If the
  branch's `task escalate` can no longer read this old-layout record, message the main agent
  instead (SendMessage), which you do anyway. Never rewrite the primary worktree's existing
  records.
- **Overlap with the open task `owner-only-wake`** (another main session's task: an owner main
  session per run and task-session round, touching Main session, Tasks, Task session, headless
  sessions, e2e). Work the Tracing Spec and the Execution-side Modules (Execution, Workers,
  Workflows, Checks, Harness, Delivery, Validation, Operations) first. Before changing the
  Coordination Modules' Specs or code (Tasks, Task session, Main session incl. the pi run view),
  check once whether `owner-only-wake` has been merged into main (`git log main`); if it has, merge
  main into this task branch first; if not, message the main agent and wait for its answer.

### Left to the task session

Exact field lists, schema versions and contract names; the reading command's name and flags;
which task-record fields move to the task trace; glossary entries (new terms such as trace,
trace node — only those meeting the glossary criterion — and updates to run store, run record,
run directory, workflow record, workspace binding, run lock, workspace lock, progress files,
decision log, task record); Spec documents' structure; test strategy. Escalate anything that would
change a developer decision above.

## Task session, 2026-09-29: start and first decisions

- `owner-only-wake` is not merged into main yet (checked `git log main`); Tracing and the
  Execution-side Modules go first, as the brief says.
- The task's goal covers every Concorde record and lock, so a few files of Modules not named in the
  task are changed as its direct consequence: the Issues lock path (module.issues), the `.gitignore`
  entries, the install's active-run and open-task detection and the `trace` command route
  (module.distribution), and the end-to-end scripts that read run results (module.e2e). No promise
  of those Modules changes beyond where their records and locks lie.
- The error contract moves with the error chain: `contract.concorde.error` becomes
  `contract.tracing.error` in `specs/concorde/tracing/contracts.md` (schema unchanged, version 5);
  the root's `contracts.md` is removed. `src/concorde/errors.py` stays where it is (every Module
  imports it) and is bound by Tracing instead of the root. The Framework-wide error requirements stay
  in the root's requirements, since they promise what all Modules achieve together.
- A link carries its trace node as ordinary evidence of kind `trace` whose `ref` is the node's id
  (a run or worker run identity), which `concorde trace show` resolves; no field is added to the
  error contract.
- Retention is configured in a Tracing file of its own, `.concorde/tracing.json` (tracked,
  optional; defaults: history kept without removal, unbound runs removed 7 days after they end),
  not in `.concorde/config.json`: that file's closed schema belongs to Spec core, whose change would
  bump the configuration profile of every project. Removal happens at `task open` and `task close`
  and with `concorde trace prune`, never in a background process.
- The reading command is `concorde trace show|list|prune`, a Tracing command named by its owner.

## Task session: decisions in the Execution-side Specs (commit 3fd47923)

- Workspace binding version 2: `records` is replaced by `traces` (the absolute workspace folder,
  which must exist) and `concorde` (the absolute `.concorde` whose `locks/` holds the workspace's
  locks), so that Execution writes where it is told and derives only lock paths from Tracing's layout.
- A workflow step nests its run with a runner option `--trace-at <folder>` (inside the workspace
  folder only); a step's node is `workflow/steps/<n>-<key>/`, the key sanitized to `[a-z0-9.-]`,
  `<n>` counting every recorded step. The run keeps its `r-…` identity; `concorde trace` finds it by
  searching the workspace folder.
- The worker run record is the worker run's `trace.json`; its content keeps what is not a uniform
  field (task type, backend source, tools, transcript path, worker result, pending and deletion
  lists, round count), and each round is a node of its own (`concorde-worker-round-trace`) with its
  tokens, cost and turns as usage and its standard error as `stderr.log` (last 80,000 bytes).
- Run results keep absolute evidence paths (their caller opens them at once); trace records hold
  only relative paths and identities. The readiness's check log path becomes relative to the run's
  node (`checks/<check>/output.log`), readiness contract version 5; the run result contract becomes
  version 3 (saved in the run's node, `trace` evidence kind).
- The Harness's session boundary allows the task session's Bash to write its own task folder and
  `.concorde/locks/` of the primary worktree (instead of all of `.concorde/runs/` and
  `.concorde/tasks/`); the write hook refuses the decision log once the task folder has moved.
- The diagnostic timing sink refuses `.concorde/tasks`, `history`, `unbound` and `locks` instead of
  the old `.concorde/runs` and `.concorde/status`.

## 2026-09-29 — Main agent on the overlap with `owner-only-wake`

The task session asked whether to wait for `owner-only-wake` before changing the Coordination
Modules. That task was active, not delivered, with two commits touching mostly the pi run view
(`pi_extension.ts`, `pi_runs.ts`, their tests) and the Main session Spec, lightly the Task session
Spec and `tests/concorde/tasks/test_store.py`, and no `src/concorde/tasks/*.py`. Decision (ordering
of work, within the main agent's authority): do not wait; work Tracing and Execution first, then
Tasks and Task session, then Main session last; when starting Main session, merge main first if
`owner-only-wake` has merged, otherwise go ahead and resolve conflicts on a later `merge_conflict`.

## Main agent's answer on `owner-only-wake`, 2026-09-29 (decision of the main agent)

Go ahead without waiting. Order: (1) Tracing library and Execution-side code, (2) Tasks and Task
session Specs and code, (3) Main session last (its Spec, `pi_extension.ts`, `pi_runs.ts` and their
tests). When starting step 3, check once whether `owner-only-wake` merged into main: if so, merge
main into concorde/tracing first; if not, go ahead and resolve conflicts on a later `merge_conflict`.

## Task session: decisions in the Coordination Specs and code (commits e92c9310, 127c430a)

- Task record `task.json` (contract.tasks.record version 12, schema_version 2) keeps only id, goal,
  Modules, branch, worktree, base commit, stored state, merging and closed (with the history key).
  Escalations, state transitions and the closing move into the task's trace node
  (`contract.tasks.task-trace`); sessions and pi rounds become nodes `sessions/<id>/` and
  `rounds/<n>/` (`contract.task-session.session-trace`, `...round-trace`); merge attempts become
  `merges/<n>/` with `checks/<i>/output.log` (`contract.tasks.merge-trace`, `merge-check-trace`),
  replacing `<task>.merge.log`. Escalation numbers keep counting from 1, now in the task's trace.
- A Claude Code session node has status `unknown` (Concorde never observes its end); no Concorde
  command reports its end (out of scope, as the brief says).
- Every change of a task's record or trace holds the per-task lock `locks/tasks/<task>.lock`
  instead of the former global `.concorde/tasks/.lock`.
- Close: the move to the history is the close's last step, after the record update, the end of
  the task node and the decision-log append, so a refused close is finished by the same close as
  before; a failed move is `history_move_failed`. `runtime/` is removed with the move. History keys
  are `<task>` or `<task>.<n>` (n from 2); `task open` still refuses a name whose branch exists, so
  a clash needs the branch deleted first.
- Close `--completed`/`--failed` stops running runs by sending SIGTERM to the process that
  `/proc/locks` names as holding each run lock (translated into the caller's PID namespace, so no
  recorded pid is trusted), and stops a running pi round as `session --stop` does, then waits for
  the workspace lock as before.
- `task list` and `task show` also read the history; `task show` adds `sessions`, `escalations`
  and `folder`.
- The write hook (Claude Code and pi) refuses writes to the decision log once the task's folder
  has moved (it would otherwise recreate the folder).
- The pi run view starts runs with `--detach` and reads the announcement; while a launch is not
  announced yet, it discovers no runs, so a run is never reported twice.
- Dogfooding defect reports and end-to-end session logs stay under `.concorde/runs/defects/` and
  `.concorde/runs/e2e/`, which the installer still ignores; moving them is not part of this goal
  (they are not Execution's runs).
- The end-to-end scripts (module.e2e) read runs, rounds and workflow reports from the new layout.
- A delivery that finds its work already delivered (recovered) adds no `commit`/`bundle`
  references to its run node: those relations mean a commit and bundle the node itself created;
  its output still names the existing delivery commit.

## Task session: implementation (commit 449335f1) and delivery

- Implementation, tests and documents were done with four parallel helper agents on disjoint
  files; the full suite passes (772 passed, 4 live tests skipped), spec-validation has no finding,
  `build --check` passes, the docsite repository regressions pass.
- Spec core's typed-value checker treats `{"type": "object"}` as a closed object and does not know
  `"type": "number"`; the registered content schemas therefore spell open objects as
  `{"type": "object", "additionalProperties": {}}`, and the merge trace's `waited_seconds` is
  registered without a type (the contract says number). Spec core is outside this task; worth a
  follow-up so the typed-value checker follows JSON Schema.
- `tests/concorde/test_errors.py` moved from the root's check to a new check file
  `.concorde/checks/module.tracing.json` (`check.tracing.tests`).
- Bootstrapping: this task was opened by the old code, so its binding was version 1, which the
  branch's code refuses. I rewrote this worktree's Git-ignored `.concorde/workspace.json` by hand to
  version 2 with `concorde` = `/home/zhenyu/concorde/.concorde/runs/tracing-bootstrap` and `traces`
  = `.../tracing-bootstrap/tasks/tracing/workspace`, because this session's sandbox can write
  `.concorde/runs/` and `.concorde/tasks/` of the primary worktree but not `.concorde/locks/`.
  task-validation and delivery of this task are therefore traced there; the primary worktree's
  `.concorde/tasks/tracing.json` record and this decision log stay in the old layout.
- Found by reading this task's own trace: `concorde trace show` refused a workspace folder no task node holds (as another preparer's, or this task's bootstrapped one); the reader now shows such a folder as a workspace node, tested. Delivered again after that fix.
- Reported the delivery (d7839211) to concorde-04, since the task's main session
  "Observability across task workflow operation levels" is no longer reachable. concorde-04 says it
  is not this task's main agent, has passed the report to the developer and asks me to wait; on a
  take-over it will merge and ask me to merge main into concorde/tracing after a merge_conflict.

## Main agent concorde-04 (2026-09-29)

- The task session's delivery report reached concorde-04, not this task's main agent
  ("Observability across task workflow operation levels"), which no longer runs. The developer
  chose to have concorde-04 merge the task after `owner-only-wake`, then have the task session
  merge main into the task branch on a conflict, and clean up the old-layout leftovers in the
  primary through a task.
- Non-ok: `task merge tracing` ended `merge_conflict` in 10 paths (scripts/e2e/sessions.py, the
  Main session module.md and scenarios.md, the Task session scenarios.md, the e2e sessions
  module.md, src/concorde/distribution/install.py, pi_extension.ts, pi_runs.ts,
  tests/concorde/distribution/test_distribution.py, tests/concorde/e2e/test_sessions.py). The
  merge was aborted and the task is still delivered. concorde-04 asked the task session to merge
  main (9d75a622, owner-only-wake included) into concorde/tracing, resolve the conflicts, run
  task-validation and delivery again, and report.

## Merge of main (9d75a622) into concorde/tracing — 2026-09-29

Asked by the main agent after a merge_conflict with owner-only-wake. Conflicts in 10 files, resolved
in the merge commit 352884d5, keeping both sides' promises:

- **Round ownership moved into the session trace node.** owner-only-wake read a pi task session's
  owner from the `main` of the session entry in the old task record; tracing removed that list. The
  owner is now `content.data.main` of `.concorde/tasks/<task>/sessions/<id>/trace.json`
  (`roundOwner`/`recordedSession` in `pi_runs.ts`, `_pi_rounds` in `scripts/e2e/sessions.py`). The
  owner stays the session it was started for, whoever answers; the task-session, main-session and
  e2e/sessions Specs say "the `main` of the session's node".
- **A pi main session's owned runs stay in its pi session file** (OWNED_RUN_ENTRY/REPORTED_ENTRY),
  as owner-only-wake designed. They are not copied into trace nodes: a run's trace node describes
  the run, while ownership belongs to the main session that owns it, and pi already persists it with
  the session.
- **Run launch in `pi_extension.ts`**: I kept tracing's `--detach` launch and added main's
  `appendEntry(OWNED_RUN_ENTRY)`, and marked a run that had already finished as given. I kept
  tracing's `pendingLaunches === 0` guard on discovery beside main's comment that discovered runs
  wake nobody here.
- **`scripts/e2e/owners.py` and its test (new on main)** now use the tracing layout: runs come from
  `tasks/*/workspace/runs/r-*`, the workflow step run folders and `unbound/r-*`. The task record is
  `tasks/<task>/task.json`, and the locks are `locks/workspaces/<ws>.lock` and
  `locks/runs/<id>.lock`.
- **Tests from main that assumed the old records** now write session trace nodes:
  `test_pi_run_view` probe, `test_sessions` fake pi, `test_store` show test and the
  `test_distribution` imports.
- **Spec wording**: I reworded the session_supervisor_lost row of task-session/contracts.md to "the
  round is recorded by the next start, …" so that the verb "records" is no longer auto-linked as
  the term Task record (the CHK.term.unlinked warning).
- **Checks**: 786 passed and 4 skipped; spec-validation shows 0 errors and 0 warnings; build
  --check passes. The ruff E402 in scripts/concorde.py comes from main unchanged and was not
  touched.
- **Delivered again**: task-validation ready at 352884d5; delivery commit 74b9aff7 with the evidence
  bundle `.concorde/evidence/tracing/3.json`.

## Closed: merged, 2026-09-29T08:51:29Z
