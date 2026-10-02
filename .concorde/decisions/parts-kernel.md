# Decision log: parts-kernel

Goal: Give the kernel part its code: typed values, registered-schema dialect, file transactions, digests, workspace binding, workspace and merge locks, delivery-commit recognition and trace roots per the Kernel and Tracing Specs, and make every part except spec use the kernel for them

## Brief (main agent, 2026-10-03)

### Context

The developer decided (2026-10-03) to split Concorde into independently installable parts. On the
integration branch `parts-split` (the primary worktree is on it; this task merges there, never into
`main`): `parts-spec` rewrote the Specs, and `parts-layout` moved the code into one directory per
part (`src/concorde/<part>/`) and added `tests/concorde/development/test_part_dependencies.py`,
whose `KNOWN_EXCEPTIONS` lists every import that still breaks the part directions, grouped by the
code task that removes it; the test fails on a new violation and on a stale exception. This is the
**kernel** code task. Next come issues and worker harness, then execution, workflow, method,
coordination, distribution.

Read first: `specs/concorde/kernel/` (module, contracts, requirements) and
`specs/concorde/kernel/tracing/` (trace roots, node kinds, locks, retention), the root's "The
parts" and `req.concorde.part-dependencies`, and the decision logs of `parts-spec` and
`parts-layout` in `.concorde/decisions/`.

### What this task does

- **Kernel library code** in `src/concorde/kernel/` (bound by a new realization of `module.kernel`),
  as the Kernel's [Library](specs/concorde/kernel/contracts.md#library) table says: typed values with
  the Kernel's own registered-schema dialect and schema checking, file transactions, digests, the
  workspace binding reader and writer (`binding_unreadable`, `binding_invalid`, `binding_misplaced`),
  delivery-commit listing and verification, and the workspace lock and merge lock taken through
  Tracing's lock library. Refusals carry stable codes; the Kernel writes no error link and imports
  no part.
- **Every part except spec uses the kernel for these**: repoint every import whose target now lives
  in the kernel, whichever `KNOWN_EXCEPTIONS` group lists it (all of group `kernel`, and e.g.
  issues' merge lock and digest uses, coordination's binding and delivery-commit uses), and move the
  implementations out of their old homes (`execution/binding.py`, `method/delivery/commits.py`, the
  merge lock in `coordination/tasks/store.py`, ...) rather than leaving two. Spec core keeps its
  own copy of typed values, file transactions, schema checking and digests, unchanged and used only
  by the spec part (and by method, which may import spec); it must not import the kernel.
  Distribution's exceptions stay for the distribution task.
- **Tracing**: trace roots registered as data by the parts that keep them (Coordination: current
  tasks and history; Execution: unbound runs and lobby), with Tracing searching, listing and pruning
  only the roots it is given; History becomes Tasks' (Coordination's) as the Specs say; the node
  kind enum gains `delivery` and `delivery-check` (I-4c0a0969, I-b43c8352). Until the distribution
  task gives the parts registrations, the `trace` command receives the roots from whoever wires it
  today (Distribution's CLI, already an exception) — keep that wiring minimal and obvious for the
  distribution task to replace.
- **Scenarios and tests** for the Kernel's behavioural interfaces (I-b3d59e10): add the scenarios
  the Kernel's requirements need, each with a test carrying its `verifies` declaration.
- Remove every exception this task makes stale; add none (the test forbids it), except moving an
  entry to another group when its remaining reason belongs to another task.
- Rapid-iteration rule: no compatibility re-exports, shims or dual paths; refactor boldly. Keep
  record formats the Specs did not change byte-compatible, so the primary worktree's existing
  `.concorde/` records (tasks, history, Issues, locks) still read after the merge.

### Verification and delivery

`build --check`, `spec-validation`, the full suite (`.venv/bin/python -m pytest`), a smoke of
`task list`, `issues list`, `trace show <a history task>` and `trace prune --help`-level commands from
the task worktree; then `task-validation` and `delivery`, and report. The three Issues this task
resolves are on the task (`--resolves`); the merge closes them.

### Left to the task session

Module and function names inside `src/concorde/kernel/`, how the trace-root data is shaped in code,
the exact scenarios. Decide and record. Escalate only a conflict with the Specs that the code cannot
meet as written; if a Spec is wrong in a detail, fix the Spec in this task and record why.

## Task session decisions (2026-10-03)

1. **Kernel package layout.** `src/concorde/kernel/` stays a namespace package (no `__init__.py`)
   and gains, bound by a new realization `realization.kernel.library` of `module.kernel`:
   `refusal.py` (`KernelError`: stable `code`, the JSON pointer or path concerned, a message, and
   causes for `system_error`), `schema.py` (the registered dialect, schema admission and checking,
   typed values with registration and embedding, project paths, artifacts, canonical JSON, strict
   JSON decoding, digests), `files.py` (file transactions), `binding.py` (workspace binding reader
   and writer, finding the worktree a directory lies in), `delivery.py` (the delivery commit's
   message, listing and verification) and `locking.py` (workspace lock and merge lock through
   Tracing's lock library). Kernel tests go to `tests/concorde/kernel/`, bound by a realization
   `realization.kernel.tests`.
2. **Records checked against their own contract's schema.** The parts' code checks records whose
   contract defines their own representation (binding, run result, error link, trace node, ...)
   against schemas that need local `$defs` (the error link is recursive). The Kernel's checker
   therefore admits, for such a *contract schema* only, local `{"$ref": "#/$defs/<name>"}` and
   `$defs`; a *registered* schema still refuses them. No code outside the spec part uses `oneOf` or
   `allOf`, so the Kernel does not take them. Spec fix: Kernel contracts gain this rule and a
   "Check a record" row in the Library table (the Spec said the `$defs` dialect "belongs to the
   Spec tooling", which left the parts' own record checks with no owner).
3. **Delivery listing is oldest first**, not newest first as the Library row said: every caller
   (Coordination's derived state, `task show`'s `deliveries`, Method's `delivery`) reads the last
   delivery as the newest, Method's scenario says "oldest first", and `task show` keeps its output
   unchanged. Spec row fixed. Each listed commit carries `mismatches` (empty when it verifies), the
   shape `task show` already prints; a Git failure refuses with `git_failed`.
4. **Locks in the Library table.** Kernel contracts' Library gains rows for taking the workspace
   lock (`workspace_busy`, `workspace_retired`) and the merge lock (`merge_busy`) and reading their
   holders, since the brief and the Kernel entry place them in the Kernel's library. The merge
   lock's default wait (300 s) moves with it, so Issues no longer reads it from Tasks.
5. **Method keeps Spec core's copies** of schema checking, typed data paths and file transactions
   for its Spec-document work (method may import spec, per the brief); only its delivery commit
   code moves into the kernel. `method/delivery/commits.py` keeps Method's own output schema.
6. **Trace roots** are plain data (`kernel/tracing/roots.py`, `TraceRoot`) that a part registers
   with Tracing when its code loads, like typed value types: Coordination's Tasks registers
   current tasks and history, Execution registers unbound runs and lobby. Tracing's reader,
   listing and retention work only over the registered roots (or roots passed explicitly). Until
   the distribution task gives the parts registrations, Distribution's CLI loads Coordination's
   and Execution's modules (already-listed exceptions) before dispatching `concorde trace`, so their
   roots are registered; the project MCP server already loads them. A process that loaded only
   Execution therefore finds no task's runs by identity, which is right: Execution knows no task.
   The root folders' names and helpers (tasks, history, history key, a task's workspace folder;
   unbound, lobby) move out of Tracing's layout into Tasks and Execution. Coordination's retention
   at `task open`/`close` prunes the registered roots, as before.
7. **Installer run lookup.** Distribution's `active_runs` no longer uses the root folders: it finds
   the run folder of each held run lock by walking the `.concorde` directory, which needs no part.
   Distribution's import of `execution.binding` becomes `kernel.binding` (the same exception,
   relocated in the distribution group).
8. **Node kinds.** `contract.tracing.node` (version 4) and the code add `delivery` and
   `delivery-check` (I-4c0a0969, I-b43c8352).
9. **Distribution exceptions relocated, one added.** `distribution/project_mcp/tools.py` reads the
   binding through `kernel.binding` instead of `execution.binding` and catches the Kernel's
   refusal, so its distribution-group exception moved to `kernel.binding` and one entry
   `kernel.refusal` was added there: both are the same reliance as before (Distribution's MCP
   tools reading a binding) and go with the distribution task. `distribution/install.py` no longer
   imports `kernel.tracing.reader`; its gitignore list of trace folders is now its own constant
   `TRACES` (Tracing's layout no longer names the parts' roots). The whole `kernel` group (25),
   `issues/command.py -> coordination.tasks.store` (the merge lock's default wait moved to the
   Kernel) and `distribution/install.py -> kernel.tracing.reader` are gone; `kernel` left
   `CODE_TASKS`.
10. **Error text.** A Kernel refusal's message no longer starts with its JSON pointer (Spec core's
    `ContractError` did); every caller that showed the pointer now prints `field: message` itself.
    Busy-lock refusals keep each caller's own wording; Execution's `workspace_busy` now ends "one
    workspace does one thing at a time".
11. **Node lookup.** `locate` finds a top node by name in every registered root, then any node by
    identity below the given workspace folders, then below every registered root (a folder named
    after it, or a step's `run/` whose node has that identity, holding a `trace.json`, progress
    file or result). A run of another task is therefore found by identity only where Tasks'
    roots are registered, which the runner process alone does not do; its `input_not_admissible`
    refusal then says the run has no readable result instead of naming the task.
12. **Kernel scenarios** (I-b3d59e10): `specs/concorde/kernel/scenarios.md` with 12 scenarios
    (binding read, refused, copied; deliveries listed, merge unverified; registration repeated,
    dialect; typed embedded; transaction stale, restored, unrestored; busy lock refused) and a
    requirement `req.kernel.busy-lock-named`; each scenario verified by
    `tests/concorde/kernel/test_kernel.py`.

## Report 1 to the main agent (concorde-a2), 2026-10-02T21:14:07Z

parts-kernel delivered: delivery commit 7f53d6f1 on concorde/parts-kernel (step bdc9f688). Verified: build --check ok, spec-validation success with no findings, full suite 982 passed / 5 skipped, task-validation ready (no blocking), smoke from the task worktree of task list, issues list, trace show parts-layout, trace show of a run, worker run and unbound run by identity, trace list --history --unbound (254 nodes, as the old code lists) and trace prune --dry-run.

What changed: the Kernel library in src/concorde/kernel/ (refusal.py KernelError with stable codes; schema.py typed values, registered dialect, contract-schema checking with local $defs, digests, paths; files.py file transactions; binding.py; delivery.py; locking.py workspace and merge locks through Tracing's locks), bound by realization.kernel.library and tested by tests/concorde/kernel/. Every part but spec and Distribution uses it; execution/binding.py and method/delivery/commits.py are deleted, the merge lock and its 300 s default left Tasks. Tracing: trace roots are registered data (kernel/tracing/roots.py); Tasks registers current tasks and history, Execution unbound runs and lobby; the reader, listing and retention work only over registered roots; the root folders and the history key left Tracing's layout. contract.tracing.node v4 adds delivery and delivery-check.

Decisions taken on your behalf (all in the decision log, entries 1-12): (2) the Kernel checks the parts' own records against "contract schemas" = registered dialect + local $defs (the error link is recursive); Kernel contracts gain that rule and a "Check a record" row. (3) Spec fix: deliveries are listed oldest first, not newest first; every caller and Method's scenario already read them that way, and task show's output is unchanged. (4) Library table gains the workspace lock, merge lock and holder rows, plus "Find the worktree". (5) Method keeps Spec core's copies for its Spec-document work; only delivery commits moved. (6) Trace roots register when the part's code loads; until Distribution reads registrations, Distribution's CLI loads Tasks' and Execution's modules (existing exceptions) before `concorde trace`; a runner process alone therefore no longer finds another task's run by identity, so its input_not_admissible refusal says "no readable result" instead of naming the task. (7) Installer finds held runs' progress files by walking .concorde; its gitignore trace folders are its own TRACES constant. (9) Part-dependency exceptions: the whole kernel group (25), issues/command -> coordination.tasks.store and install -> kernel.tracing.reader removed; kernel left CODE_TASKS; in the distribution group project_mcp/tools.py's execution.binding entry moved to kernel.binding and one entry kernel.refusal was added (same reliance, Distribution reading a binding) - the only exception added. (10) Kernel refusal messages no longer prefix the JSON pointer; callers print field: message. (12) Kernel scenarios: 12 scenarios plus req.kernel.busy-lock-named, each verified by a test.

Issues resolved by this task (already on the task, the merge closes them): I-b3d59e10 (Kernel scenarios), I-4c0a0969 and I-b43c8352 (delivery/delivery-check node kinds). No escalations, nothing open.

## Closed: merged, 2026-10-02T21:14:28Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 7f53d6f15170474a00fe6194ca9ed7d86614d89d into parts-split and closed it as merged. Nobody answers a report after that.
