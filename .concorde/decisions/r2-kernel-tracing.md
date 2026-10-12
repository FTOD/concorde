# Decision log: r2-kernel-tracing

Goal: Fix the critical, high and obvious-fix open Issues of Kernel and Tracing found by the complete project_review, the critical first (I-dc8c3bda)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 21 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T13:38:13Z

- **task-session** task session (task r2-kernel-tracing): `issue_decision_needed`
  Issue I-73955523379f501aa25485d0054f798f (decision-needed, high, module.tracing): the view contract (contract.tracing.view) defines one view object, and 'Reading traces' says the output is 'one JSON value as the view contract defines', but no Spec says what 'concorde trace list' prints for zero or several top nodes. Found: src/concorde/kernel/tracing/command.py listing() prints a JSON array of view objects (each with children empty), '[]' when nothing is listed; its tree format prints '(no traces)'. Existing callers and tests rely on that array.
  Not handled here (decision): Fixing the response shape of a command is an interface promise of Tracing; the Issue's tier is decision-needed, which a task session never settles.
  Options: A: specify the current behaviour: list prints a JSON array of view objects, one per listed top node in the listed order, each with children empty; [] when nothing is listed; add a two-node example. No code change.; B: wrap the list in an envelope object, e.g. {"nodes": [<view>...]}, with its own contract; changes the command's output and its callers.
  Recommendation: A: it matches the code and its callers, keeps one canonical entry shape, and distinguishes list (array) from show (object) and prune (its own object).

```json
{
  "level": "task-session",
  "actor": "task session (task r2-kernel-tracing)",
  "code": "issue_decision_needed",
  "detail": "Issue I-73955523379f501aa25485d0054f798f (decision-needed, high, module.tracing): the view contract (contract.tracing.view) defines one view object, and 'Reading traces' says the output is 'one JSON value as the view contract defines', but no Spec says what 'concorde trace list' prints for zero or several top nodes. Found: src/concorde/kernel/tracing/command.py listing() prints a JSON array of view objects (each with children empty), '[]' when nothing is listed; its tree format prints '(no traces)'. Existing callers and tests rely on that array.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Fixing the response shape of a command is an interface promise of Tracing; the Issue's tier is decision-needed, which a task session never settles."
  },
  "options": [
    "A: specify the current behaviour: list prints a JSON array of view objects, one per listed top node in the listed order, each with children empty; [] when nothing is listed; add a two-node example. No code change.",
    "B: wrap the list in an envelope object, e.g. {\"nodes\": [<view>...]}, with its own contract; changes the command's output and its callers."
  ],
  "recommendation": "A: it matches the code and its callers, keeps one canonical entry shape, and distinguishes list (array) from show (object) and prune (its own object).",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T13:38:22Z

- **task-session** task session (task r2-kernel-tracing): `issue_decision_needed`
  Issue I-f9b01a31bf235f6aa7601b41821f2bc5 (decision-needed, high, module.tracing): realization.tracing.library lists capabilities only; the Specs give no callable producer entry points, inputs, results or repeat behaviour. Found: the library is concorde.kernel.tracing with modules layout (paths), node (Node with start/update/finish, check, write, read, artifact, TraceError), kinds and roots (register, lookup, registered; KindError, RootError), locks (hold, handed_on, holder, acquire, release, wait_released, removing; LockBusy, LockGone), reader (view, locate, listing, run_alive, render; ReadError), retention (prune, configuration) and watch. Related: Kernel's I-6f307966 (preferred-fix, mine) asks the same of the Kernel library; I plan to fix it by naming each operation's import location and callable in the Kernel Library table.
  Not handled here (decision): Naming the producer API in the contract turns today's Python names into promises of Tracing that the current Specs do not make; the Issue's tier is decision-needed.
  Options: A: add a 'Library' section to the Tracing contracts like the Kernel's: one table row per producer operation with its import location (concorde.kernel.tracing.<module>), callable, inputs, result and refusal exception, plus duplicate-registration and repeated-write behaviour; add one producer's normal path (register kind and root, Node start/update/finish with warnings, take and hand on a lock) to module.md. Private helpers stay unnamed.; B: keep the contracts free of callable names; add only a producer walkthrough in module.md in terms of operations, leaving names to the code.; C: close as not actionable: the library has only Concorde's own parts as producers, which read the code.
  Recommendation: A, the same treatment as the Kernel library (I-6f307966), so a producer author needs no code and both libraries read alike.

```json
{
  "level": "task-session",
  "actor": "task session (task r2-kernel-tracing)",
  "code": "issue_decision_needed",
  "detail": "Issue I-f9b01a31bf235f6aa7601b41821f2bc5 (decision-needed, high, module.tracing): realization.tracing.library lists capabilities only; the Specs give no callable producer entry points, inputs, results or repeat behaviour. Found: the library is concorde.kernel.tracing with modules layout (paths), node (Node with start/update/finish, check, write, read, artifact, TraceError), kinds and roots (register, lookup, registered; KindError, RootError), locks (hold, handed_on, holder, acquire, release, wait_released, removing; LockBusy, LockGone), reader (view, locate, listing, run_alive, render; ReadError), retention (prune, configuration) and watch. Related: Kernel's I-6f307966 (preferred-fix, mine) asks the same of the Kernel library; I plan to fix it by naming each operation's import location and callable in the Kernel Library table.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Naming the producer API in the contract turns today's Python names into promises of Tracing that the current Specs do not make; the Issue's tier is decision-needed."
  },
  "options": [
    "A: add a 'Library' section to the Tracing contracts like the Kernel's: one table row per producer operation with its import location (concorde.kernel.tracing.<module>), callable, inputs, result and refusal exception, plus duplicate-registration and repeated-write behaviour; add one producer's normal path (register kind and root, Node start/update/finish with warnings, take and hand on a lock) to module.md. Private helpers stay unnamed.",
    "B: keep the contracts free of callable names; add only a producer walkthrough in module.md in terms of operations, leaving names to the code.",
    "C: close as not actionable: the library has only Concorde's own parts as producers, which read the code."
  ],
  "recommendation": "A, the same treatment as the Kernel library (I-6f307966), so a producer author needs no code and both libraries read alike.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:38:29Z

r2-kernel-tracing: early escalation of the task's two decision-needed Issues, as the task brief asks; I continue with the 19 others meanwhile.

1) I-73955523 (trace list JSON response). Options: A specify today's behaviour (a JSON array of view objects with children empty, [] when none, plus a two-node example; no code change); B an envelope object {"nodes": [...]}. Recommendation: A.

2) I-f9b01a31 (Tracing producer library interface). Options: A a 'Library' section in the Tracing contracts naming each producer operation's import location, callable, inputs, result and refusal exception, with duplicate-registration and repeated-write behaviour, plus one producer's normal path in module.md; B a walkthrough in operation terms only, no callable names; C close as not actionable. Recommendation: A, the same treatment I give the Kernel library for the preferred-fix I-6f307966.

Rendered chains:

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-08T13:38:47Z

Escalations 1-2 (main agent): 1 A — specify today's trace list output (a JSON array of view objects with children empty, [] when none) with a two-node example; no code change. 2 A — a Library section in Tracing's contracts naming each producer operation's import location, callable, inputs, result and refusal exception, with duplicate-registration and repeated-write behaviour, plus one producer's normal path in module.md; private helpers stay unnamed; no compatibility promise beyond the installed Concorde (rapid-iteration rule).

## Task session decisions (2026-10-08)

- **I-dc8c3bda (critical, preferred-fix).** Fix chosen: `apply_files` records a target before its
  write begins; `_restore` removes a never-created target with `missing_ok` and skips an existing
  target that still holds its original bytes. Chosen over a recovery journal because the window is
  inside one process and restoring an untouched target is then a no-op. Contract step 4 now says a
  write under way counts as written. Fault-injection test interrupts just after `os.replace`, for
  an existing and a new file (fails without the fix).
- **I-dff83b7b, I-f8d6c0ee (high, preferred-fix).** On `FileNotFoundError`, `os.path.lexists`
  tells a dangling symbolic link (refused `marker_unreadable` / `binding_unreadable`) from absence.
  The binding reader's `exists()` pre-check is gone, so every inspection failure is
  `binding_unreadable`. Library rows say a symbolic link to nothing cannot be read.
- **I-73072d05 (high, preferred-fix).** A `true` schema is checked as `{}`, so the kind, finite
  number and depth checks descend through every unconstrained subtree. Also added: a value of a
  Python type that is no JSON value, or an object key that is no string, is refused
  `invalid_field` (the contract's "a value is checked as JSON" needs it; full suite passed).
- **I-245d33dd, I-1866c4f1 (obvious-fix).** Done as the Issues suggest.
- **I-6f307966 (high, preferred-fix).** The Kernel Library table gained a `Call` column naming
  `<module>.<function>(args)` in `concorde.kernel`, plus conventions (Path arguments,
  `KernelError` fields, locks as context managers with `LockRefused`, `verify` callable). Same
  "no compatibility beyond the installed Concorde" wording the main agent gave for Tracing.
- **I-18cb21bb (high, preferred-fix).** The Purpose example reads the marker under the merge lock
  and refuses on a present or unreadable marker before any write; it also names the calls.
- **I-55156040 (obvious-fix).** New `req.kernel.marker-changed-under-lock`. Mechanical follow-on
  outside my Modules: `module.tasks`' `uses` of the Kernel now also relies on it (Tasks writes the
  marker), registry refreshed.
- **I-547aec77 (obvious-fix).** `.concorde/workspace.json` added to the kernel part's own
  `install.gitignore`; Coordination's identical entry left as is (Distribution deduplicates).
  Test composes the ignore rules of the kernel closure without Coordination.
- **I-736f5cd4, I-6833d3ae (obvious-fix).** `node.check` validates a non-null error against
  `ERROR_SCHEMA`, refuses an error on a status other than blocked/failed, and refuses an absolute
  reference target for every relation (commits are never absolute either). Full suite passed, so
  no producer wrote an incomplete link.
- **I-40cca21c (obvious-fix).** `parse_time` reads RFC 3339 with `Z` or any offset, converting
  to UTC; fractions beyond microseconds are cut. Non-UTC offsets are accepted (converted) rather
  than refused: more robust and harmless.
- **I-d4e9d288 (obvious-fix).** Artifact inspection moved inside the `OSError` boundary of
  `Node._write`; "Writing a node" says such a refusal is a failed write.
- **I-ad59b89e (obvious-fix).** `_streams` keeps every nonempty stream exactly; an empty stream
  is still omitted (nothing was captured).
- **I-73955523 (main agent: A).** "Reading traces" specifies per form: `show` one view, `list` a
  JSON array (`[]` when empty), `prune` its object, with a two-node example; tree form prints
  `(no traces)`. No code change.
- **I-f9b01a31 (main agent: A).** New "Library" section in Tracing contracts: one table row per
  producer operation (call, inputs, result, refusal exception), conventions, a check-node
  example, "no compatibility beyond the installed Concorde"; the entry's realization gives one
  producer's normal path. Error chain code (`concorde.kernel.errors`) included since Tracing owns it.
- **I-410982d5, I-a862637e (obvious-fix).** Requirements: written-at-start carries the
  best-effort qualification; new written-at-end; relative-paths keeps the retained-payload
  exception in its statement; roots-registered split into roots-searched, roots-listed,
  roots-pruned (no outside references to the old id); lock-handed-on now states the validity
  check with fallback; new lock-held-to-exit; history-unchanged names the closing exception in
  its statement. Kept `written-at-start` as the id other Modules link for best effort.
- **I-019e9f54, I-5152f108 (obvious-fix).** Entry text fixed as the Issues suggest.

## Report 2 to the main agent (Review流程), 2026-10-08T14:15:00Z

r2-kernel-tracing delivered: delivery commit 427e71c1d2308e122aa038a03d2d84ff756c6a4a on concorde/r2-kernel-tracing. All 21 Issues in the task's resolves are fixed; none turned out invalid, a duplicate or already fixed. task-validation was ready (28 checks passed, 0 blocking findings, 10 warnings, all in other Modules). The full suite passed on the final input: 1378 passed, 5 skipped.

Critical: I-dc8c3bda (preferred-fix). apply_files now records a target before its write begins. The restoration removes a target that was never created and skips one that still holds its original bytes. The contract's step 4 says the same. A new fault-injection test interrupts just after os.replace, for an existing file and for a new one; it fails without the fix.

High, preferred-fix, the fix I chose for each:
- I-dff83b7b and I-f8d6c0ee: os.path.lexists tells a dangling symbolic link (refused as marker_unreadable or binding_unreadable) from a missing file. The binding reader's unguarded exists() pre-check is gone.
- I-73072d05: a true schema is checked as {}, so the kind, finite-number and depth checks descend into every unconstrained subtree. Added: a Python value that is no JSON value, or an object key that is not a string, is refused as invalid_field. The full suite passed with that.
- I-6f307966: the Kernel Library table gained a Call column (<module>.<function>(args) in concorde.kernel), plus conventions for KernelError, LockRefused, locks as context managers and the verify callable. It promises no compatibility beyond the installed Concorde.
- I-18cb21bb: the Purpose example reads the marker under the merge lock and refuses before any write. It also names the calls.

High, decided by you as A:
- I-73955523: trace list prints a JSON array of view objects, [] when empty. Two-node example added; no code change.
- I-f9b01a31: new Library section in the Tracing contracts with a producer-path example, and the normal producer path in module.md.

High, obvious-fix: I-410982d5 and I-d4e9d288.

Obvious-fix, medium and low: I-019e9f54, I-1866c4f1, I-245d33dd, I-40cca21c, I-5152f108, I-547aec77, I-55156040, I-6833d3ae, I-736f5cd4, I-a862637e, I-ad59b89e.

Spec changes besides those:
- New requirements: req.kernel.marker-changed-under-lock, req.tracing.written-at-end, req.tracing.lock-held-to-exit.
- req.tracing.roots-registered is split into roots-searched, roots-listed and roots-pruned. No other Module referenced the old id.

Mechanical follow-ons outside my Modules:
- specs/concorde/coordination/tasks/module.md.json: Tasks, which writes the marker, now also relies on req.kernel.marker-changed-under-lock (one line). The registry was refreshed. r2-tasks may conflict on that line.
- The node contract is now enforced. A node's error must be a whole error link, carried only by a blocked or failed node, and a reference must never be an absolute path. No producer in the suite broke this.

Every decision is in the decision log. Nothing is open.

## Closed: merged, 2026-10-12T14:27:17Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 427e71c1d2308e122aa038a03d2d84ff756c6a4a into main and closed it as merged. Nobody answers a report after that.
